"""在线筛选完整问题组：先生成评分，再补齐有效问题，不持有训练器或worker。"""
from collections import defaultdict
import copy
import math
import time
import numpy as np
import torch
import torch.nn.functional as F


def mixed_groups(batch, group_size, seen=None, reward_mode='binary', variance_epsilon=1e-12):
    """
    @brief 保留完整、有奖励差异且未重复的问题组，原二值模式保持默认。
    @param batch 含dynamic_rewards、uid和question_id的DataProto。
    @param group_size 每问题完整轨迹数。
    @param seen 已接受的问题ID集合，可为空。
    @param reward_mode binary沿用0/1正确数组规则；finite允许有限实数奖励。
    @param variance_epsilon 非负有限的组奖励方差容差。
    @return 接受行索引组及每个候选组的分项记录。
    @raises ValueError 模式/容差错误、组不完整、奖励非法或组身份不一致。
    """
    # 模式显式决定筛选，避免实数奖励被强转为历史正确数k。
    if not isinstance(group_size, int) or group_size <= 0:
        raise ValueError('Group size must be a positive integer')
    if reward_mode not in ('binary', 'finite') or not math.isfinite(variance_epsilon) or variance_epsilon < 0:
        raise ValueError('Invalid group reward mode/variance threshold')
    # uid区分抽题实例；question_id阻止同一更新批内重复问题，组内轨迹不能拆分。
    scores=batch.batch['dynamic_rewards'].sum(-1).tolist()
    groups=defaultdict(list)
    for i,uid in enumerate(batch.non_tensor_batch['uid']): groups[str(uid)].append(i)
    accepted=[]; records=[]; seen=set() if seen is None else seen
    for uid,indices in groups.items():
        values=[scores[i] for i in indices]
        # 残组和非有限数不能参与筛选；二值模式继续拒绝负奖励和非0/1数。
        if len(indices)!=group_size or any(not math.isfinite(v) for v in values):
            raise ValueError('Filtering requires complete groups and finite rewards')
        if reward_mode == 'binary' and any(v not in (0.,1.) for v in values):
            raise ValueError('Binary filtering requires 0/1 rewards')
        q=str(batch.non_tensor_batch['question_id'][indices[0]])
        if any(str(batch.non_tensor_batch['question_id'][i])!=q for i in indices):
            raise ValueError('Question identities differ inside group')
        # finite模式依组内方差筛选；同分组仍无GRPO信号，不能因均值为负强行入选。
        mean=sum(values)/group_size; variance=sum((v-mean)**2 for v in values)/group_size
        k=int(sum(values)) if reward_mode == 'binary' else None
        valid=(0<k<group_size if reward_mode == 'binary' else variance>variance_epsilon) and q not in seen
        source=str(batch.non_tensor_batch['data_source'][indices[0]]) if 'data_source' in batch.non_tensor_batch else 'unknown'
        # 原EM正确数与新训练奖励分别保存；缺原EM报告时不伪造正确数。
        reports=batch.non_tensor_batch.get('process_checks')
        em_k=sum(float(reports[i]['original_em']) for i in indices) if reports is not None else k
        records.append(dict(question_id=q,uid=uid,k=k,em_k=em_k,eligible=valid,source=source,
                            reward_mode=reward_mode,reward_mean=mean,reward_variance=variance))
        if valid:
            accepted.append(indices); seen.add(q)
    return accepted,records


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
    @brief 复用原补抽流程，按同一奖励入口选择二值或实数组筛选。
    @param loader 原问题DataLoader。
    @param controller 难度实验状态控制器。
    @param manager 共用检索生成管理器。
    @param reward_fn 奖励入口，可显式提供group_reward_mode。
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
    iterator=iter(loader); target=controller.sampler.batch_size; group_size=controller.group_size
    while controller.completed_step<total_steps:
        # 本段已训练问题不再入选，保证100步覆盖800个不同的有效问题。
        step=controller.completed_step+1; parts=[]; seen=set(controller.accepted_question_ids); candidates=0; started=time.monotonic()
        candidate_tokens=0; candidate_searches=0
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
            candidate.batch['dynamic_rewards']=reward_fn(candidate)
            # 关闭过程功能的原奖励函数不提供模式属性，继续沿用binary。
            accepted,records=mixed_groups(candidate,group_size,seen,
                                          reward_mode=getattr(reward_fn,'group_reward_mode','binary'))
            candidates+=len(records)
            controller.record({'event':'filter_candidates','step':step,'round':round_index,'groups':records,
                               'accepted_so_far':len(parts),'candidate_groups_so_far':candidates})
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
        for source in set(batch.non_tensor_batch['data_source']):
            batch.meta_info['dynamic_metrics']['dynamic/retained_source/'+str(source)]=sum(batch.non_tensor_batch['data_source']==source)/group_size
        yield batch

