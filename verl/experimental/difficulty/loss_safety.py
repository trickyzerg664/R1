"""显式 safe_v1 损失：正常区域保持原公式，非有限输入及中间量显式失败。"""
import math
import torch


def valid_values(values, mask):
    """@brief 只取有效模型 token，并以 FP32 验证数值。
    @param values 与掩码同形状的概率、优势或熵。
    @param mask 二值模型 token 掩码。
    @return 非空、有限的一维 FP32 张量，保留梯度。
    @raises ValueError 形状不一致、掩码非二值或没有模型 token。
    @raises FloatingPointError 有效 token 输入非有限。
    """
    # 不接受隐式广播和软掩码，确保环境 token 永远没有训练权重。
    if values.shape != mask.shape or not torch.all((mask == 0) | (mask == 1)):
        raise ValueError('Loss requires matching shapes and binary mask')
    # 先筛选，避免环境位置的 NaN 乘零后仍污染反传。
    selected = values[mask.bool()].float()
    # 空有效集和非有限有效输入必须在反传前失败，不能静默归零。
    if not selected.numel():
        raise ValueError('No model tokens in loss mask')
    if not torch.isfinite(selected).all():
        raise FloatingPointError('Nonfinite input on valid model token')
    return selected


def policy_loss(old_logprob, logprob, advantages, mask, cliprange, log_ratio_bound=5.):
    """@brief 计算原 GRPO 裁剪损失，并保护极端概率比。
    @param old_logprob 有效 token 的旧策略对数概率矩阵。
    @param logprob 同 token 的当前对数概率矩阵。
    @param advantages 同形状相对优势矩阵。
    @param mask 二值模型 token 掩码。
    @param cliprange PPO 风格比值裁剪半径，有限且位于零到一之间。
    @param log_ratio_bound 额外指数安全边界，有限、正数且不大于八十。
    @return 损失、裁剪比例、旧减新对数概率均值及安全指标。
    @raises ValueError 裁剪边界或张量掩码无效。
    @raises FloatingPointError 有效输入或相减后的概率差非有限。
    @note 正常区公式不变；安全边界命中必须单独记录。
    """
    # 配置检查不改当前合法超参数，防止非法边界改变损失方向或让 exp 溢出。
    if not math.isfinite(cliprange) or not 0 <= cliprange < 1:
        raise ValueError('cliprange must be finite in [0, 1)')
    if not math.isfinite(log_ratio_bound) or not 0 < log_ratio_bound <= 80:
        raise ValueError('log_ratio_bound must be finite in (0, 80]')
    current = valid_values(logprob, mask)
    old = valid_values(old_logprob, mask)
    adv = valid_values(advantages, mask)
    delta = current - old
    # 有限输入相减仍可能溢出；拒绝把溢出后的 inf 当作正常裁剪样本。
    if not torch.isfinite(delta).all():
        raise FloatingPointError('Nonfinite log ratio before clipping')
    ratio = torch.exp(delta.clamp(-log_ratio_bound, log_ratio_bound))
    raw = -adv * ratio
    clipped = -adv * ratio.clamp(1 - cliprange, 1 + cliprange)
    loss = torch.maximum(raw, clipped).mean()
    diagnostics = {'actor/log_ratio_abs_max': delta.detach().abs().max().item(),
                   'actor/log_ratio_bound_fraction': (delta.detach().abs() > log_ratio_bound).float().mean().item()}
    return loss, (clipped > raw).float().mean(), (-delta).mean(), diagnostics


def kl_loss(logprob, reference, mask, cutoff=2.5):
    """@brief 计算安全参考 KL 估计，指数高端沿用切线延续。
    @param logprob 当前对数概率矩阵。
    @param reference 固定 reference 对数概率矩阵。
    @param mask 二值模型 token 掩码。
    @param cutoff 指数切换点，有限、正数且不大于二十。
    @return 安全 KL 均值及参考概率差诊断。
    @raises ValueError 切换点或张量掩码无效。
    @raises FloatingPointError 有效输入或相减后的参考差非有限。
    @note 切线延续是安全 surrogate；高端不能解释为精确 KL。
    """
    # 切换点须处于 FP32 安全指数范围，不接受 NaN 或无穷大配置。
    if not math.isfinite(cutoff) or not 0 < cutoff <= 20:
        raise ValueError('KL cutoff must be finite in (0, 20]')
    current = valid_values(logprob, mask)
    ref = valid_values(reference, mask)
    delta = ref - current
    # 单个输入有限不能保证相减有限；参考差溢出时拒绝构造 KL。
    if not torch.isfinite(delta).all():
        raise FloatingPointError('Nonfinite reference delta')
    # 指数仅到 cutoff，高端切线保持非零纠偏梯度及值、导数连续。
    normal = torch.expm1(delta.clamp(max=cutoff)) - delta
    linear = math.expm1(cutoff) - cutoff + (delta - cutoff) * math.expm1(cutoff)
    values = torch.where(delta > cutoff, linear, normal)
    return values.mean(), {'actor/reference_delta_abs_max': delta.detach().abs().max().item(),
                           'actor/kl_linear_fraction': (delta.detach() > cutoff).float().mean().item()}


def entropy_loss(entropy, mask):
    """@brief 计算有效模型 token 的原熵均值。
    @param entropy token 熵矩阵。
    @param mask 二值模型 token 掩码。
    @return 保留梯度的 FP32 熵均值。
    @raises ValueError 形状或掩码无效。
    @raises FloatingPointError 有效熵非有限。
    """
    return valid_values(entropy, mask).mean()
