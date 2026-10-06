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
    """
    @brief 共用生成评分入口做四轨迹难度打标，原EM标签与过程奖励分别保存。
    @param dataset 原训练问题数据集。
    @param indices 本批问题索引列表。
    @param seeds 每题四个轨迹种子。
    @param manager 原LLMGenerationManager。
    @param reward_fn 共用RewardManager，过程开启时返回同行分项报告。
    @param max_start_length 原初始问题窗口参数。
    @param trace_chars 有限轨迹尾部保存长度，0表示不保存。
    @return 每题四个原EM、生成成本及可选过程奖励记录列表。
    @raises Exception 基础设施或来源错误传播，失败批次不写成错误答案。
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
    # 打标不是参数更新；记录独立阶段，负奖励不能进入要求0/1的难度标签。
    batch.meta_info['process_reward_phase'] = 'difficulty_score'
    process_rewards = reward_fn(batch).sum(-1).reshape(-1, 4).tolist()
    reports = batch.non_tensor_batch.get('process_checks')
    rewards = (np.asarray([r['original_em'] for r in reports]).reshape(-1, 4).tolist()
               if reports is not None else process_rewards)
    width = batch.batch['responses'].shape[-1]
    tokens = batch.batch['info_mask'][:, -width:].sum(-1).reshape(-1, 4).tolist()
    searches = np.asarray(batch.meta_info['valid_search_stats']).reshape(-1, 4).tolist()
    records = [{'rewards': rs, 'generated_tokens': ts, 'search_queries': qs}
               for rs, ts, qs in zip(rewards, tokens, searches)]
    # 正确数仍由原EM生成，候选过程奖励及来源诊断旁列，不改变历史标签结构。
    if reports is not None:
        for record, start, values in zip(records, range(0, len(reports), 4), process_rewards):
            record['process_rewards'] = values
            record['process_checks'] = reports[start:start+4].tolist()
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
