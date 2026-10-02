"""[data-difficulty] 生成边界适配：复用现有多轮检索和奖励，不依赖训练器。"""
import copy
import re
import numpy as np
from .state import trajectory_seed


def request_sampling_params(base, seeds, round_index, count):
    # 关闭实验时直接返回原参数对象，逐请求模式检查 TP 收集后的行数。
    """为每条请求复制采样参数并派生当前轮次的 seed。
    无 seed 时原样返回，保留未启用实验的行为；TP 收集后数量不匹配立即报错。
    """
    if seeds is None:
        return base
    if len(seeds) != count:
        raise ValueError('Sampling seeds and requests have different lengths')
    result = []
    for seed in seeds:
        params = copy.copy(base)
        params.seed = trajectory_seed(int(seed), int(round_index))
        result.append(params)
    return result


def response_trace(response, ground_truth, limit):
    # 诊断评分轨迹时记录闭合答案标签、标准答案和回答末尾，不改变奖励计算。
    matches = re.findall(r'<answer>(.*?)</answer>', response, re.DOTALL)
    target = ground_truth['target']
    if isinstance(target, np.ndarray):
        target = target.tolist()
    if not isinstance(target, (list, tuple)):
        target = [target]
    return {'has_answer_tag': bool(matches), 'last_answer': matches[-1].strip() if matches else None,
            'target': [str(answer) for answer in target], 'response_tail': response[-limit:]}


def score_batch(dataset, indices, seeds, manager, reward_fn, max_start_length, trace_chars=0):
    # 评分与训练共享 dataset、LLMGenerationManager 和 RewardManager，只禁用参数更新。
    """将题目展开为四条完整检索轨迹，调用训练共用的生成和奖励组件。
    返回每题四个奖励、生成 token 数和检索次数，不计算梯度或复用旧训练回答。
    基础设施异常直接传播给 score_pool，当前批次不会被写成四个错误答案。
    """
    from verl import DataProto
    from verl.utils.dataset.rl_dataset import collate_fn
    batch = DataProto.from_single_dict(collate_fn([dataset[i] for i in indices]))
    batch = batch.repeat(repeat_times=4, interleave=True)
    generation = batch.pop(batch_keys=['input_ids', 'attention_mask', 'position_ids'])
    # DataProto 的非张量字段约定为 object 数组，生成批次也必须满足同一约束。
    generation.non_tensor_batch['rollout_seed'] = np.asarray(seeds, dtype=object).reshape(-1)
    generation.meta_info.update(do_sample=True, recompute_log_prob=False)
    output = manager.run_llm_loop(generation, generation.batch['input_ids'][:, -max_start_length:].clone().long())
    batch = batch.union(output)
    rewards = reward_fn(batch).sum(-1).reshape(-1, 4).tolist()
    width = batch.batch['responses'].shape[-1]
    tokens = batch.batch['info_mask'][:, -width:].sum(-1).reshape(-1, 4).tolist()
    searches = np.asarray(batch.meta_info['valid_search_stats']).reshape(-1, 4).tolist()
    records = [{'rewards': rs, 'generated_tokens': ts, 'search_queries': qs}
               for rs, ts, qs in zip(rewards, tokens, searches)]
    if 'generation_diagnostics' in batch.meta_info:
        # 每题仍对应四条完整轨迹；诊断字段不参与奖励和难度标签计算。
        details = batch.meta_info['generation_diagnostics']
        if len(details) != len(batch):
            raise ValueError('Generation diagnostics and trajectories differ')
        for record, start in zip(records, range(0, len(details), 4)):
            record['diagnostics'] = details[start:start+4]
    if trace_chars:
        # 沿用 RewardManager 的有效响应长度，避免将 padding 当作模型输出。
        traces = []
        for i in range(len(batch)):
            item = batch[i]
            prompt_length = item.batch['prompts'].shape[-1]
            response_length = int(item.batch['attention_mask'][prompt_length:].sum().item())
            # 诊断与奖励器都排除检索观察，避免把反馈里的示例标签误认为模型作答。
            model_mask = item.batch['info_mask'][prompt_length:prompt_length + response_length].bool()
            response_ids = item.batch['responses'][:response_length][model_mask]
            response = manager.tokenizer.decode(response_ids, skip_special_tokens=True)
            traces.append(response_trace(response, item.non_tensor_batch['reward_model']['ground_truth'], trace_chars))
        for record, start in zip(records, range(0, len(traces), 4)):
            record['traces'] = traces[start:start + 4]
    return records
