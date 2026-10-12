"""验证融合概率算子的非连续标签布局及梯度。"""
import unittest
from unittest.mock import patch
import torch
from verl.utils import torch_functional as functional
from verl.workers.actor.dp_actor import token_statistics


class ProbabilityLayoutCPUTests(unittest.TestCase):
    def fused_reference(self, logits, labels):
        """@brief 模拟融合入口并验证连续布局，使用原生概率作为参考。
        @param logits 二维样本乘词表张量。
        @param labels 已展平的连续编号。
        @return 对应目标的原生对数概率。
        """
        self.assertTrue(labels.is_contiguous())
        return logits.log_softmax(-1).gather(-1, labels.unsqueeze(-1)).squeeze(-1)

    def test_flattened_tail_labels_are_contiguous(self):
        """@brief 多样本单 token 尾块必须复制 stride，不能依赖 reshape。
        @return 无。
        """
        logits = torch.randn(2, 3, 16, requires_grad=True)
        labels = torch.tensor([[1, 2, 3], [4, 5, 6]])[:, -1:]
        self.assertFalse(labels.reshape(-1).is_contiguous())
        # 只替换 GPU kernel 边界，生产展平/连续复制与 autograd 路径仍实际执行。
        with patch.object(functional, 'FLAH_ATTN_CROSS_ENTROPY_LOSS_AVAILABLE', True), \
             patch.object(functional, 'logprobs_from_logits_flash_attn', self.fused_reference):
            out = functional.logprobs_from_logits(logits[:, -1:], labels)
        ref = logits[:, -1:].log_softmax(-1).gather(-1, labels.unsqueeze(-1)).squeeze(-1)
        self.assertTrue(torch.allclose(out, ref))
        self.assertTrue(torch.allclose(torch.autograd.grad(out.sum(), logits, retain_graph=True)[0],
                                       torch.autograd.grad(ref.sum(), logits)[0]))



@unittest.skipUnless(torch.cuda.is_available(), 'GPU unavailable')
class ProbabilityLayoutGPUTests(unittest.TestCase):
    def test_real_kernel_tail_values_and_gradients(self):
        """@brief 实际融合 GPU kernel 的多样本单 token 尾块与原生概率/梯度一致。
        @return 无。
        """
        torch.manual_seed(42)
        # 同时覆盖尾块为 1、多 token、整块、单/多样本，以及非连续原始标签。
        for batch in (1, 2):
            for length in (32, 33, 34, 65):
                for recompute in (False, True):
                    with self.subTest(batch=batch, length=length, recompute=recompute):
                        full = torch.randn(batch, length + 2, 256, device='cuda', requires_grad=True)
                        labels = torch.randint(0, 256, (batch, length + 2), device='cuda')[:, 1:-1]
                        lp, entropy = token_statistics(full[:, 1:-1], labels,
                                                       chunk_size=32, recompute=recompute)
                        ref = full[:, 1:-1].log_softmax(-1).gather(-1, labels.unsqueeze(-1)).squeeze(-1)
                        grad = torch.autograd.grad(lp.sum(), full, retain_graph=True)[0]
                        expected = torch.autograd.grad(ref.sum(), full)[0]
                        self.assertLess((lp - ref).abs().max().item(), 2e-6)
                        self.assertLess((grad - expected).abs().max().item(), 2e-6)
                        self.assertTrue(torch.isfinite(entropy).all().item())
