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
                 eligibility='reward_variance', fallback_counts=()):
    """@brief 保留完整同题组；可选要求门控后任务成功与失败同时存在。
    @param batch 含 dynamic_rewards、uid、question_id 和可选成功报告的 DataProto。
    @param group_size 每个问题的完整轨迹数，必须为正整数。
    @param seen 已接受的问题 ID 集合，可为空，入选后原地更新。
    @param reward_mode binary 沿用零一奖励规则；finite 允许有限实数。
    @param variance_epsilon finite 模式的非负有限奖励方差容差。
    @param eligibility 原奖励方差、任务混合或 answer_correct_3_6 八次答对三至六次规则。
    @param fallback_counts 补入时允许的正确次数，仅支持 7 和 8；默认不放宽资格。
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
    # 备用资格仍要求完整轨迹、有限奖励和非零奖励方差。
    if any(k not in (7, 8) for k in fallback_counts) or (fallback_counts and eligibility != ANSWER_RANGE_MODE):
        raise ValueError('Fallback requires answer_correct_3_6 and counts 7/8')
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
        # 备用8次正确组只允许靠真实奖励差异提供信号，原策略仍排除全成功组。
        elif success_k == group_size and answer_k not in fallback_counts:
            reasons.append('all_task_success')
        # 答对次数与质量成功数分别记录；严重重复答对仍计原答案正确，但不能独占正信号。
        if eligibility == ANSWER_RANGE_MODE and not (3 <= answer_k <= 6 or answer_k in fallback_counts):
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
    @param max_rounds 默认硬上限；恢复模式下表示每次尝试补齐的轮数间隔。
    @return 按原规则产出完整DataProto批次的迭代器。
    @raises ValueError 组或奖励非法。
    @raises RuntimeError 默认策略在耗尽后失败，不执行不完整批次的更新。
    """
    # 只有凑齐完整有效批才yield并更新参数；候选消费与训练步数分别保存，禁止小批降级。
    from verl import DataProto
    # 新模式在生成前检查标签能力，评价或旧奖励入口不能静默退回原筛选。
    eligibility = getattr(controller, 'dynamic_eligibility', 'reward_variance')
    if eligibility != 'reward_variance' and getattr(reward_fn, 'task_success_enabled', False) is not True:
        raise ValueError('task_success_mixed requires gated training reward with success labels')
    iterator=iter(loader); target=controller.sampler.batch_size; group_size=controller.group_size
    recovery = controller.settings.get('dynamic_filter', {}).get('on_exhaustion') == 'refill_7_8_v1'
    while controller.completed_step<total_steps:
        # 本段已训练问题不再入选，保证100步覆盖800个不同的有效问题。
        step=controller.completed_step+1; parts=[]; seen=set(controller.accepted_question_ids); candidates=0; started=time.monotonic()
        # 恢复模式可能无限补抽；题池剩余独立问题不足时立即拒绝，避免无法完成的循环。
        if recovery and len(controller.rows) - len(seen) < target:
            raise ValueError('Insufficient untrained questions for a complete dynamic batch')
        candidate_tokens=0; candidate_searches=0
        rejection_counts = Counter()
        # 同一更新期间权重不变，缓存真实备用轨迹；每轮优先接纳 3–6 组。
        reserves = {}; fallback_used = Counter(); fallback_selected = []; round_index = -1
        while len(parts) < target:
            round_index += 1
            if not recovery and round_index >= max_rounds:
                break
            try:
                candidate_dict = next(iterator)
            except StopIteration:
                if not recovery:
                    raise
                # 扩展候选预算，不重置随机流、曝光记录或已完成的训练步骤。
                controller.extend_candidate_budget(max_rounds)
                iterator = iter(loader)
                candidate_dict = next(iterator)
            candidate=DataProto.from_single_dict(candidate_dict)
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
            if recovery and len(parts) < target:
                # 正常组先入选后删除其旧备用，避免占用有限缓存容量或重复入选。
                reserves = {q: item for q, item in reserves.items() if q not in seen}
                # 备用组仍执行原奖励及方差校验；全对同分组不会产生学习信号。
                backup, backup_records = mixed_groups(candidate, group_size, set(seen),
                    reward_mode=getattr(reward_fn, 'group_reward_mode', 'binary'),
                    eligibility=eligibility, fallback_counts=(7, 8))
                by_uid = {record['uid']: record for record in backup_records}
                for indices in backup:
                    record = by_uid[str(candidate.non_tensor_batch['uid'][indices[0]])]
                    q, k = record['question_id'], record['answer_correct_k']
                    if k not in (7, 8) or q in seen:
                        continue
                    # 同题后出现的七次组也应优先；同优先级保留首次真实轨迹以保证确定性。
                    if q in reserves:
                        if k < reserves[q][0]:
                            reserves[q] = (k, take_rows(candidate, indices))
                        continue
                    if len(reserves) >= target:
                        # 容量已满时，允许新出现的 7 次正确组替换优先级较低的 8 次组。
                        replaceable = next((key for key, value in reserves.items() if value[0] > k), None)
                        if replaceable is None:
                            continue
                        del reserves[replaceable]
                    reserves[q] = (k, take_rows(candidate, indices))
                if (round_index + 1) % max_rounds == 0:
                    # 达到补齐边界时先接纳 7 次组，再接纳有奖励方差的 8 次组。
                    for q, (k, reserved) in sorted(reserves.items(), key=lambda item: item[1][0]):
                        if len(parts) == target:
                            break
                        if q not in seen:
                            parts.append(reserved); seen.add(q); fallback_used[k] += 1
                            # 记录备用实际入选身份，便于与原候选审计逐组对齐。
                            fallback_selected.append({'question_id': q, 'answer_correct_k': k,
                                'uid': str(reserved.non_tensor_batch['uid'][0]),
                                'candidate_round': reserved.meta_info['trajectory_candidate_round']})
                    reserves.clear()
                    controller.record({'event': 'filter_recovery', 'step': step,
                        'rounds': round_index + 1, 'retained': len(parts), 'target': target,
                        'fallback_counts': dict(fallback_used), 'selected': list(fallback_selected),
                        'continued': len(parts) < target})
                    print(f'[筛选恢复] step={step} rounds={round_index+1} retained={len(parts)}/{target} fallback={dict(fallback_used)}', flush=True)
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
        # 独立记录实际备用组数量，避免将新策略结果混报为严格 3–6 筛选。
        if recovery:
            batch.meta_info['dynamic_metrics'].update({
                'dynamic/fallback_k7_groups': fallback_used[7],
                'dynamic/fallback_k8_groups': fallback_used[8],
                'dynamic/extended_rounds': max(0, round_index + 1 - max_rounds)})
        for reason, count in rejection_counts.items():
            batch.meta_info['dynamic_metrics']['dynamic/rejected_' + reason + '_groups'] = count
        for source in set(batch.non_tensor_batch['data_source']):
            batch.meta_info['dynamic_metrics']['dynamic/retained_source/'+str(source)]=sum(batch.non_tensor_batch['data_source']==source)/group_size
        yield batch

