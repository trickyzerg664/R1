"""在线筛选完整问题组：先生成评分，再补齐有效问题，不持有训练器或worker。"""
from collections import Counter, defaultdict
import copy
import math
import time
import numpy as np
import torch
import torch.nn.functional as F
from .eligibility import TASK_MIXED_VERSION, ANSWER_RANGE_MODE, ANSWER_RANGE_VERSION, task_success_labels


def mixed_groups(batch, group_size, seen=None, reward_mode='binary', variance_epsilon=1e-12,
                 eligibility='reward_variance'):
    """@brief 保留完整同题组；可选要求门控后任务成功与失败同时存在。
    @param batch 含 dynamic_rewards、uid、question_id 和可选成功报告的 DataProto。
    @param group_size 每个问题的完整轨迹数，必须为正整数。
    @param seen 已接受的问题 ID 集合，可为空，入选后原地更新。
    @param reward_mode binary 沿用零一奖励规则；finite 允许有限实数。
    @param variance_epsilon finite 模式的非负有限奖励方差容差。
    @param eligibility 原奖励方差、任务混合或 answer_correct_3_6 八次答对三至六次规则。
    @return 完整入选行索引组和含成功数、奖励方差及排除原因的组记录。
    @raises ValueError 配置、奖励、身份、完整性或成功标签不满足约束。
    """
    # 先校验模式，避免误拼写或缺少标签时退回奖励方差。
    if not isinstance(group_size, int) or group_size <= 0:
        raise ValueError('Group size must be a positive integer')
    if reward_mode not in ('binary', 'finite') or not math.isfinite(variance_epsilon) or variance_epsilon < 0:
        raise ValueError('Invalid group reward mode/variance threshold')
    if eligibility not in ('reward_variance', 'task_success_mixed', ANSWER_RANGE_MODE):
        raise ValueError('Unknown dynamic eligibility mode')
    # 新规则只定义G8，禁止把其他轨迹数静默套入固定正确次数范围。
    if eligibility == ANSWER_RANGE_MODE and group_size != 8:
        raise ValueError('answer_correct_3_6 requires exactly eight rollouts')
    scores = batch.batch['dynamic_rewards'].sum(-1).tolist()
    reports = batch.non_tensor_batch.get('process_checks')
    success = (task_success_labels(reports, batch.non_tensor_batch.get('process_trace_uid'), len(scores))
               if eligibility != 'reward_variance' else None)
    # uid 区分一次抽题实例；同题八条完整保留，question_id 控制重复曝光。
    groups = defaultdict(list)
    for i, uid in enumerate(batch.non_tensor_batch['uid']):
        groups[str(uid)].append(i)
    accepted, records = [], []
    seen = set() if seen is None else seen
    # 逐组先验证完整性和身份，再决定资格；排除组也保留可追溯原因。
    for uid, indices in groups.items():
        values = [scores[i] for i in indices]
        if len(indices) != group_size or any(not math.isfinite(v) for v in values):
            raise ValueError('Filtering requires complete groups and finite rewards')
        if reward_mode == 'binary' and any(v not in (0., 1.) for v in values):
            raise ValueError('Binary filtering requires 0/1 rewards')
        q = str(batch.non_tensor_batch['question_id'][indices[0]])
        if any(str(batch.non_tensor_batch['question_id'][i]) != q for i in indices):
            raise ValueError('Question identities differ inside group')
        # 资格筛选不改奖励值和优势公式；同分组仍保留原来的零信号排除条件。
        mean = sum(values) / group_size
        variance = sum((v - mean) ** 2 for v in values) / group_size
        k = int(sum(values)) if reward_mode == 'binary' else None
        reward_mixed = 0 < k < group_size if reward_mode == 'binary' else variance > variance_epsilon
        success_k = None if success is None else sum(success[i] for i in indices)
        answer_k = (sum(reports[i]['accepted_answer_em'] == 1. and reports[i]['protocol_gate']
                        for i in indices) if success is not None else None)
        reasons = []
        if not reward_mixed:
            reasons.append('no_reward_variance')
        if success_k == 0:
            reasons.append('no_task_success')
        elif success_k == group_size:
            reasons.append('all_task_success')
        # 答对次数与质量成功数分别记录；严重重复答对仍计原答案正确，但不能独占正信号。
        if eligibility == ANSWER_RANGE_MODE and not 3 <= answer_k <= 6:
            reasons.append('answer_correct_outside_3_6')
        if q in seen:
            reasons.append('duplicate_question')
        valid = not reasons
        source = str(batch.non_tensor_batch['data_source'][indices[0]]) if 'data_source' in batch.non_tensor_batch else 'unknown'
        # 原文本 EM 与执行器接受 EM 分开；旧报告缺分项时只记录未知。
        em_k = sum(float(reports[i]['original_em']) for i in indices) if reports is not None else k
        accepted_em_k = (sum(float(reports[i]['accepted_answer_em']) for i in indices)
                         if success is not None else None)
        records.append(dict(question_id=q, uid=uid, k=k, em_k=em_k, eligible=valid, source=source,
                            reward_mode=reward_mode, reward_mean=mean, reward_variance=variance,
                            eligibility=eligibility,
                            eligibility_version=(ANSWER_RANGE_VERSION if eligibility == ANSWER_RANGE_MODE else
                                                 TASK_MIXED_VERSION if success is not None else None),
                            answer_correct_k=answer_k,
                            task_success_k=success_k, accepted_answer_em_k=accepted_em_k,
                            rejection_reasons=reasons))
        if valid:
            accepted.append(indices)
            seen.add(q)
    return accepted, records


def take_rows(batch,indices):
    # TensorDict与非张量字段同步筛选；生成诊断的逐行元数据也同步筛选。
    from verl import DataProto
    ids=np.array(indices,dtype=int)
    meta=copy.deepcopy(batch.meta_info)
    for key in ('turns_stats','active_mask','valid_action_stats','valid_search_stats','generation_diagnostics'):
        if key in meta:meta[key]=[meta[key][i] for i in indices]
    return DataProto(batch=batch.batch[torch.tensor(indices)],
                     non_tensor_batch={k:v[ids] for k,v in batch.non_tensor_batch.items()},meta_info=meta)


def merge_groups(parts,pad_id):
    # 不同候选批有不同问题/回答宽度：问题左补齐、回答右补齐，禁止截取任何轨迹。
    from verl import DataProto
    pmax=max(p.batch['prompts'].shape[-1] for p in parts)
    rmax=max(p.batch['responses'].shape[-1] for p in parts)
    merged=[]
    row_meta=('turns_stats','active_mask','valid_action_stats','valid_search_stats','generation_diagnostics')
    for part in parts:
        pwidth=part.batch['prompts'].shape[-1]; rwidth=part.batch['responses'].shape[-1]
        tensors={}
        for key,value in part.batch.items():
            if key=='position_ids':continue
            padding=pad_id if key in ('input_ids','prompts','responses','responses_with_info_mask') else 0
            if key=='prompts':tensors[key]=F.pad(value,(pmax-pwidth,0),value=padding)
            elif value.shape[-1]==rwidth:tensors[key]=F.pad(value,(0,rmax-rwidth),value=padding)
            elif value.shape[-1]==pwidth+rwidth:
                tensors[key]=torch.cat((F.pad(value[:,:pwidth],(pmax-pwidth,0),value=padding),
                                        F.pad(value[:,pwidth:],(0,rmax-rwidth),value=padding)),dim=-1)
            else:raise ValueError('Unexpected dynamic batch field width: '+key)
        tensors['position_ids']=(tensors['attention_mask'].long().cumsum(-1)-1).clamp_min(0)
        merged.append(DataProto.from_dict(tensors,non_tensors=part.non_tensor_batch,meta_info=part.meta_info))
    result=DataProto.concat(merged)
    result.meta_info=copy.deepcopy(parts[0].meta_info)
    for key in row_meta:
        if all(key in p.meta_info for p in parts):result.meta_info[key]=sum((p.meta_info[key] for p in parts),[])
    return result


def training_batches(loader,controller,manager,reward_fn,repeat_fn,worker,pad_id,total_steps,max_rounds):
    """
    @brief 复用完整组补抽流程，按显式资格模式筛选，不改奖励或优势。
    @param loader 原问题DataLoader。
    @param controller 提供组大小、资格模式、采样器及记录接口的实验控制器。
    @param manager 共用检索生成管理器。
    @param reward_fn 共用奖励入口；新模式要求 task_success_enabled 为真。
    @param repeat_fn 原问题轨迹展开函数。
    @param worker 原actor概率计算worker。
    @param pad_id 原补齐token。
    @param total_steps 完成更新周期上限。
    @param max_rounds 每周期候选补抽上限。
    @return 按原规则产出完整DataProto批次的迭代器。
    @raises ValueError 组或奖励非法。
    @raises RuntimeError 候选耗尽，禁止部分更新。
    """
    # 只有凑齐完整有效批才yield并更新参数；候选消费与训练步数分别保存，禁止小批降级。
    from verl import DataProto
    # 新模式在生成前检查标签能力，评价或旧奖励入口不能静默退回原筛选。
    eligibility = getattr(controller, 'dynamic_eligibility', 'reward_variance')
    if eligibility != 'reward_variance' and getattr(reward_fn, 'task_success_enabled', False) is not True:
        raise ValueError('task_success_mixed requires gated training reward with success labels')
    iterator=iter(loader); target=controller.sampler.batch_size; group_size=controller.group_size
    while controller.completed_step<total_steps:
        # 本段已训练问题不再入选，保证100步覆盖800个不同的有效问题。
        step=controller.completed_step+1; parts=[]; seen=set(controller.accepted_question_ids); candidates=0; started=time.monotonic()
        candidate_tokens=0; candidate_searches=0
        rejection_counts = Counter()
        for round_index in range(max_rounds):
            candidate=DataProto.from_single_dict(next(iterator))
            candidate=repeat_fn(candidate,group_size)
            gen=candidate.pop(batch_keys=['input_ids','attention_mask','position_ids'])
            controller.attach_seeds(gen,step,candidate_round=round_index)
            generated=manager.run_llm_loop(gen_batch=gen,initial_input_ids=gen.batch['input_ids'][:,-manager.config.max_start_length:].clone().long())
            candidate=candidate.union(generated)
            width=candidate.batch['responses'].shape[-1]
            candidate_tokens+=int(candidate.batch['info_mask'][:,-width:].sum())
            candidate_searches+=sum(candidate.meta_info.get('valid_search_stats',[]))
            # 仅给展示标注更新步数和候选轮次，不改变身份、奖励或随机种子。
            candidate.meta_info.update(trajectory_step=step, trajectory_candidate_round=round_index,
                                       trajectory_phase='train_candidates')
            candidate.batch['dynamic_rewards']=reward_fn(candidate)
            # 关闭过程功能的原奖励函数不提供模式属性，继续沿用binary。
            accepted,records=mixed_groups(candidate,group_size,seen,
                                          reward_mode=getattr(reward_fn,'group_reward_mode','binary'),
                                          eligibility=eligibility)
            # 排除原因按候选组记录，可同时命中多个原因，不冒充互斥比例。
            for record in records:
                rejection_counts.update(record['rejection_reasons'])
            candidates+=len(records)
            controller.record({'event':'filter_candidates','step':step,'round':round_index,'groups':records,
                               'accepted_so_far':len(parts),'candidate_groups_so_far':candidates,
                               'eligibility':eligibility})
            print(f'[动态筛选] step={step} round={round_index+1}/{max_rounds} candidates={candidates} mixed={len(accepted)} retained={min(target,len(parts)+len(accepted))}/{target}',flush=True)
            for indices in accepted:
                if len(parts)<target:parts.append(take_rows(candidate,indices))
            if len(parts)==target:break
        if len(parts)!=target:
            controller.record({'event':'filter_exhausted','step':step,'retained':len(parts),'target':target,'candidates':candidates})
            raise RuntimeError('Dynamic filtering round limit reached; no partial optimizer update')
        batch=merge_groups(parts,pad_id)
        batch.meta_info['dynamic_question_ids']=sorted(set(str(q) for q in batch.non_tensor_batch['question_id']))
        gen_elapsed=time.monotonic()-started
        batch=batch.union(worker.compute_log_prob(batch))
        elapsed=time.monotonic()-started
        batch.meta_info['dynamic_timing']={'step':elapsed,'gen':gen_elapsed,'rollout_logprob':elapsed-gen_elapsed}
        batch.meta_info['dynamic_metrics']={'dynamic/candidate_groups':candidates,'dynamic/retained_groups':target,
            'dynamic/retained_fraction':target/candidates,'dynamic/rounds':round_index+1,
            'dynamic/candidate_trajectories':candidates*group_size,'dynamic/retained_trajectories':target*group_size,
            'dynamic/candidate_generated_tokens':candidate_tokens,'dynamic/candidate_search_queries':candidate_searches}
        for reason, count in rejection_counts.items():
            batch.meta_info['dynamic_metrics']['dynamic/rejected_' + reason + '_groups'] = count
        for source in set(batch.non_tensor_batch['data_source']):
            batch.meta_info['dynamic_metrics']['dynamic/retained_source/'+str(source)]=sum(batch.non_tensor_batch['data_source']==source)/group_size
        yield batch

