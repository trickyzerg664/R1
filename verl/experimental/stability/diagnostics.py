"""只读、可关闭的稳定性诊断；不持有训练器或改变损失公式。"""
import numpy as np
import torch

MAX_METRICS = {'actor/log_ratio_abs_max', 'actor/reference_delta_abs_max'}


def reduce_metric(key, values):
    """@brief 聚合真实极值及可加计数，旧损失指标沿用均值。
    @param key 指标名称；稳定性指标以 actor/stability/ 开头。
    @param values 各微批、各 worker 返回的数值列表。
    @return 一个聚合数值。
    @note micro_p95 是微批分位数的均值，不能解释为全局 token 分位数。
    """
    # 原有 max 字段被平均会隐藏少数极端轨迹；仅改变显式极值及新增命名空间。
    if key in MAX_METRICS or (key.startswith('actor/stability/') and key.endswith('_max')):
        return np.max(values)
    # 新计数和对数概率总量可跨微批相加，后续均值须使用对应 token 总数。
    if key.startswith('actor/stability/') and key.endswith('_sum'):
        return np.sum(values)
    # 其他旧指标和微批分位数继续取均值，不冒充全局分位数。
    return np.mean(values)


def token_diagnostics(log_prob, old_log_prob, advantages, mask):
    """@brief 记录有效模型 token 的概率比、优势和样本权重。
    @param log_prob 当前对数概率，形状为批次乘回答长度。
    @param old_log_prob 相同 token 的旧策略对数概率。
    @param advantages 相同位置的 GRPO 优势。
    @param mask 二值模型 token 掩码，环境和 padding 为零。
    @return 可由 reduce_metric 汇总的标量字典。
    @raises FloatingPointError 有效 token 的概率差或优势非有限。
    @raises ValueError 张量形状不一致或掩码非二值、无有效 token。
    """
    # 禁止广播掩码或权重，否则诊断可能观察错误位置并给出误导结论。
    if not (log_prob.shape == old_log_prob.shape == advantages.shape == mask.shape):
        raise ValueError('Token diagnostics require matching shapes')
    if not torch.all((mask == 0) | (mask == 1)):
        raise ValueError('Token diagnostics require a binary mask')
    # 先筛选再计算，环境位置的 NaN 不进入诊断和分位数。
    keep = mask.bool()
    delta = (log_prob.detach()[keep].float() - old_log_prob.detach()[keep].float())
    adv = advantages.detach()[keep].float()
    # 空有效集和非有限中间量不输出伪造的零均值。
    if not delta.numel():
        raise ValueError('No model tokens in diagnostics')
    if not torch.isfinite(delta).all() or not torch.isfinite(adv).all():
        raise FloatingPointError('Nonfinite token diagnostic')
    prefix = 'actor/stability/'
    result = {prefix+'valid_tokens_sum': delta.numel(),
              prefix+'log_ratio_abs_max': delta.abs().max().item(),
              prefix+'log_ratio_micro_p50': torch.quantile(delta, .5).item(),
              prefix+'log_ratio_micro_p95': torch.quantile(delta, .95).item(),
              prefix+'advantage_abs_max': adv.abs().max().item(),
              prefix+'log_ratio_sum': delta.sum().item()}
    # 分组总量可计算 token 加权均值；优势正负只表明相对更新方向，不等同于动作有效性。
    for name, selected in [('positive', adv > 0), ('negative', adv < 0), ('zero', adv == 0)]:
        result[prefix+name+'_tokens_sum'] = selected.sum().item()
        result[prefix+name+'_log_ratio_sum'] = delta[selected].sum().item()
    return result


def score_gradient_diagnostics(components, log_prob, entropy):
    """@brief 计算已加权损失在概率和熵输出端的梯度范数。
    @param components 标量损失分量映射，已包含系数及梯度累积除数。
    @param log_prob 可求导的模型对数概率张量。
    @param entropy 可求导的 token 熵张量。
    @return 每个分量在输出端的梯度 L2 范数。
    @note 不计算完整参数梯度；不写入参数 .grad，保留图供正式反传。
    """
    # 常数分量或不可导输出记零，不为观测另行构造模型图。
    inputs = [value for value in (log_prob, entropy) if value.requires_grad]
    result = {}
    # autograd 只回溯到指定输出，避免为诊断重复完整模型反传或触发 FSDP 参数同步。
    for name, component in components.items():
        gradients = (torch.autograd.grad(component, inputs, retain_graph=True, allow_unused=True)
                     if inputs and component.requires_grad else [])
        squares = sum(g.detach().float().square().sum().item() for g in gradients if g is not None)
        result['actor/stability/score_gradient_'+name+'_norm'] = squares ** .5
    return result


def sample_parameter_values(parameters, limit=256):
    """@brief 以固定遍历顺序复制少量本地参数作更新前后探针。
    @param parameters 当前本地参数迭代器，兼容 FSDP 分片。
    @param limit 最多复制的参数元素数，必须为正整数。
    @return 一维 FP32 CPU 样本，不持有模型或计算图。
    @raises ValueError limit 不是正整数。
    @note 该样本不能代表完整模型的参数变化范数。
    """
    # 提前拒绝浮点、布尔或非正预算；采样大小必须可预测且有界。
    if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
        raise ValueError('Parameter sample size must be a positive integer')
    parts, remaining = [], limit
    # 总样本数有硬上限，防止诊断额外复制整个 7B 参数。
    for parameter in parameters:
        count = min(parameter.numel(), remaining)
        if count:
            parts.append(parameter.detach().reshape(-1)[:count].float().cpu().clone())
            remaining -= count
        if remaining == 0:
            break
    return torch.cat(parts) if parts else torch.empty(0)


def parameter_update_diagnostics(before, after):
    """@brief 比较相同本地参数样本的实际变化。
    @param before 更新前一维 CPU 样本。
    @param after 相同位置的更新后样本。
    @return 样本元素数、绝对及相对 L2 变化。
    @raises ValueError 样本形状不一致。
    @note 各 worker 指标取均值；不冒充完整模型的全局更新量。
    """
    # 前后位置必须一一对应，不能把长度变化误记为参数更新。
    if before.shape != after.shape:
        raise ValueError('Parameter sample shapes differ')
    # 零范数保护仅用于报告相对变化，不干预更新。
    difference = torch.linalg.vector_norm(after - before).item()
    norm = torch.linalg.vector_norm(before).item()
    return {'actor/stability/parameter_sample_count': before.numel(),
            'actor/stability/parameter_sample_delta_l2': difference,
            'actor/stability/parameter_sample_relative_delta': difference / max(norm, 1e-12)}


def likelihood_change_diagnostics(before, after, mask):
    """@brief 对更新前后相同固定轨迹报告 token 对数概率变化。
    @param before 更新前对数概率。
    @param after 更新后同 token、同上下文、同温度的对数概率。
    @param mask 二值有效模型 token 掩码。
    @return 固定轨迹 token 数、对数概率总变化及微批平均变化。
    @raises ValueError 形状不匹配、掩码非二值或无有效 token。
    @raises FloatingPointError 有效 token 概率差非有限。
    @note 这是轨迹探针；不能直接判定 LLDS 或合法动作概率变化。
    """
    metrics = token_diagnostics(after, before, torch.zeros_like(after), mask)
    count = metrics['actor/stability/valid_tokens_sum']
    total = metrics['actor/stability/log_ratio_sum']
    return {'actor/stability/probe_tokens_sum': count,
            'actor/stability/probe_log_prob_delta_sum': total,
            'actor/stability/probe_log_prob_delta_micro_mean': total / count,
            'actor/stability/probe_log_prob_delta_abs_max': metrics['actor/stability/log_ratio_abs_max']}
