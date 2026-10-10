"""FP16 动态缩放回退必须标记被跳过的 optimizer 更新。"""

import unittest
from omegaconf import OmegaConf
from unittest.mock import patch

import torch

from verl.workers.actor.dp_actor import DataParallelPPOActor


class FakeScaler:
    def __init__(self, next_scale):
        self.current_scale = 1024.0
        self.next_scale = next_scale
        self.optimizer_calls = 0

    def is_enabled(self):
        return True

    def get_scale(self):
        return self.current_scale

    def unscale_(self, optimizer):
        pass

    def step(self, optimizer):
        if self.next_scale >= self.current_scale:
            self.optimizer_calls += 1
            optimizer.step()

    def update(self):
        self.current_scale = self.next_scale


class ScalerStepTest(unittest.TestCase):
    def make_actor(self, next_scale):
        """@brief 构造具有真实配置接口的 CPU 缩放回退测试演员。
        @param next_scale 下一次更新后的模拟 scale。
        @return 仅有 CPU 小参数的 actor 夹具。
        """
        actor = object.__new__(DataParallelPPOActor)
        actor.actor_module = torch.nn.Linear(2, 1)
        actor.actor_optimizer = torch.optim.SGD(actor.actor_module.parameters(), lr=0.1)
        # 使用真实配置接口，避免夹具在执行被测逻辑前因 .get 不存在而失败。
        actor.config = OmegaConf.create({'grad_clip': 1.0})
        actor.grad_scaler = FakeScaler(next_scale)
        actor.actor_module.weight.grad = torch.ones_like(actor.actor_module.weight)
        return actor

    def test_backoff_marks_step_skipped(self):
        actor = self.make_actor(512.0)
        _, updated = actor._optimizer_step()
        self.assertFalse(updated)
        self.assertEqual(actor.grad_scaler.optimizer_calls, 0)

    def test_constant_scale_marks_update(self):
        actor = self.make_actor(1024.0)
        _, updated = actor._optimizer_step()
        self.assertTrue(updated)
        self.assertEqual(actor.grad_scaler.optimizer_calls, 1)

    def test_optimizer_state_is_loaded_only_for_the_step(self):
        actor = self.make_actor(1024.0)
        actor.optimizer_offload = True
        events = []
        with patch('verl.workers.actor.dp_actor.load_fsdp_optimizer', side_effect=lambda **kwargs: events.append('load')), \
             patch('verl.workers.actor.dp_actor.offload_fsdp_optimizer', side_effect=lambda **kwargs: events.append('offload')), \
             patch('torch.cuda.empty_cache'), patch('torch.cuda.current_device', return_value=0):
            _, updated = actor._optimizer_step()
        self.assertTrue(updated)
        self.assertEqual(events, ['load', 'offload'])


if __name__ == '__main__':
    unittest.main()
