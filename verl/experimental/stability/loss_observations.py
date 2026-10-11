"""损失展示统计只读模块；复用既有mask和聚合，不参与梯度计算。"""
def loss_observations(total_loss, entropy, mask):
    """@brief 记录实际损失分量和有效模型token熵总量，所有张量均只读。
    @param total_loss 包含原系数、尚未除梯度累积次数的实际总损失。
    @param entropy 模型token熵矩阵。
    @param mask 与entropy同形状的原模型有效token掩码。
    @return 可跨微批汇总的Python标量字典，不保留计算图。
    @note 微批均值对应现有优化目标；token加权熵只用于观察。
    """
    # 只选择真实模型token，排除环境与padding；float32求和降低展示统计误差。
    selected = entropy.detach().float()[mask.bool()]
    result = {'actor/total_loss': total_loss.detach().item(),
              'actor/observations/entropy_sum': selected.sum().item(),
              'actor/observations/model_tokens_sum': selected.numel(),
              'actor/observations/micro_batches_sum': 1}
    return result
