"""显式safe_v1损失：只计算有效token，正常区域保持原公式，极端区域有限化。"""
import math
import torch


def valid_values(values,mask):
    # 先选择有效位置，避免无效位置的NaN在乘0后继续污染反传。
    selected=values[mask.bool()].float()
    if not selected.numel():raise ValueError('No model tokens in loss mask')
    if not torch.isfinite(selected).all():raise FloatingPointError('Nonfinite input on valid model token')
    return selected


def policy_loss(old_logprob,logprob,advantages,mask,cliprange,log_ratio_bound=5.):
    # 有限截取只在极端概率比启用；记录边界比例，不把异常静默隐藏在均值中。
    current=valid_values(logprob,mask); old=valid_values(old_logprob,mask); adv=valid_values(advantages,mask)
    delta=current-old; ratio=torch.exp(delta.clamp(-log_ratio_bound,log_ratio_bound))
    raw=-adv*ratio; clipped=-adv*ratio.clamp(1-cliprange,1+cliprange)
    loss=torch.maximum(raw,clipped).mean()
    diagnostics={'actor/log_ratio_abs_max':delta.detach().abs().max().item(),
                 'actor/log_ratio_bound_fraction':(delta.detach().abs()>log_ratio_bound).float().mean().item()}
    return loss,(clipped>raw).float().mean(),(-delta).mean(),diagnostics


def kl_loss(logprob,reference,mask,cutoff=2.5):
    # 指数只计算至cutoff；上段改为切线延续，保持非零纠偏梯度，防止先溢出再截断。
    current=valid_values(logprob,mask); ref=valid_values(reference,mask); delta=ref-current
    normal=torch.expm1(delta.clamp(max=cutoff))-delta
    linear=math.expm1(cutoff)-cutoff+(delta-cutoff)*math.expm1(cutoff)
    values=torch.where(delta>cutoff,linear,normal)
    return values.mean(),{'actor/reference_delta_abs_max':delta.detach().abs().max().item(),
        'actor/kl_linear_fraction':(delta.detach()>cutoff).float().mean().item()}


def entropy_loss(entropy,mask):
    return valid_values(entropy,mask).mean()

