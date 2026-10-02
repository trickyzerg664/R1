"""在线筛选完整问题组：先生成评分，再补齐有效问题，不持有训练器或worker。"""
from collections import defaultdict
import copy
import time
import numpy as np
import torch
import torch.nn.functional as F


def mixed_groups(batch, group_size, seen=None):
    # uid区分抽题实例；question_id阻止同一更新批内重复问题，组内轨迹不能拆分。
    scores=batch.batch['dynamic_rewards'].sum(-1).tolist()
    groups=defaultdict(list)
    for i,uid in enumerate(batch.non_tensor_batch['uid']): groups[str(uid)].append(i)
    accepted=[]; records=[]; seen=set() if seen is None else seen
    for uid,indices in groups.items():
        values=[scores[i] for i in indices]
        if len(indices)!=group_size or any(v not in (0.,1.) for v in values):
            raise ValueError('Filtering requires complete groups and binary rewards')
        q=str(batch.non_tensor_batch['question_id'][indices[0]])
        if any(str(batch.non_tensor_batch['question_id'][i])!=q for i in indices):
            raise ValueError('Question identities differ inside group')
        k=int(sum(values)); valid=0<k<group_size and q not in seen
        source=str(batch.non_tensor_batch['data_source'][indices[0]]) if 'data_source' in batch.non_tensor_batch else 'unknown'
        records.append(dict(question_id=q,uid=uid,k=k,eligible=valid,source=source))
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
            accepted,records=mixed_groups(candidate,group_size,seen)
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

