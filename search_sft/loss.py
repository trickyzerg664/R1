"""当前轮 token CE 总和；权重和全局归一化由训练循环显式给出。"""
import torch
import torch.nn.functional as F


def target_loss_sum(logits, row, chunk_size=32):
    if row is None:
        return logits.float().sum() * 0
    n = row['target_length']
    if n < 1 or logits.shape[1] != n + 1:
        raise ValueError('Need target_length+1 logits including the first prediction position')
    labels = torch.tensor(row['input_ids'][-n:],device=logits.device,dtype=torch.long)
    # 尾部 T+1 个 hidden 位置从 prompt 最后一个 token 开始；最后一个 logit 无目标。
    total = logits[0,0,0].float() * 0
    for start in range(0,n,chunk_size):
        end = min(start+chunk_size,n)
        total = total + F.cross_entropy(logits[0,start:end].float(), labels[start:end],reduction='sum')
    return total


def backward_loss(logits, row, actual_batch_size, world_size):
    if actual_batch_size < 1:
        raise ValueError('Empty optimizer batch')
    weight = row['row_weight'] if row is not None else 0.
    return target_loss_sum(logits,row) * weight * world_size / actual_batch_size
