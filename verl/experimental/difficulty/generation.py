"""[data-difficulty] 生成边界适配：复用现有多轮检索和奖励，不依赖训练器。"""
import copy
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


def score_batch(dataset, indices, seeds, manager, reward_fn, max_start_length):
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
    return [{'rewards': rs, 'generated_tokens': ts, 'search_queries': qs}
            for rs, ts, qs in zip(rewards, tokens, searches)]
