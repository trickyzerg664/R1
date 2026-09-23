"""Small offline CUDA checks for PPO FP16 updates and overflow handling."""
import math
from pathlib import Path
import tempfile
import unittest

from omegaconf import OmegaConf
from transformers.modeling_outputs import CausalLMOutput
import torch
from torch import nn
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP, MixedPrecision
from torch.distributed.fsdp.sharded_grad_scaler import ShardedGradScaler

from verl import DataProto
from verl.workers.actor.dp_actor import DataParallelPPOActor
from verl.workers.critic.dp_critic import DataParallelPPOCritic

ROOT = Path(__file__).resolve().parents[1]


class TinyModel(nn.Module):
    def __init__(self, outputs):
        super().__init__()
        self.embedding = nn.Embedding(16, 8)
        self.projection = nn.Linear(8, outputs)
        self.output_dtype = None

    def forward(self, input_ids, **kwargs):
        logits = self.projection(self.embedding(input_ids))
        self.output_dtype = logits.dtype
        return CausalLMOutput(logits=logits)


@unittest.skipUnless(torch.cuda.is_available(), 'CUDA required')
class FP16UpdateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        torch.distributed.init_process_group(
            'gloo', init_method='file://' + cls.temp.name + '/rendezvous', rank=0, world_size=1)

    @classmethod
    def tearDownClass(cls):
        torch.distributed.destroy_process_group()
        cls.temp.cleanup()

    def test_actor_and_critic_updates(self):
        config = OmegaConf.load(ROOT / 'verl/trainer/config/ppo_trainer.yaml')
        for role in ('actor', 'critic'):
            for sharded in (False, True):
                with self.subTest(role=role, fsdp=sharded):
                    self.check_update(config, role, sharded)

    def check_update(self, config, role, sharded):
        torch.manual_seed(0)
        model = TinyModel(16 if role == 'actor' else 1).cuda()
        module = model
        if sharded:
            module = FSDP(model, device_id=torch.cuda.current_device(),
                          mixed_precision=MixedPrecision(param_dtype=torch.float16,
                                                         reduce_dtype=torch.float32,
                                                         buffer_dtype=torch.float32))
        optimizer = torch.optim.SGD(module.parameters(), lr=0.01)
        if role == 'actor':
            cfg = config.actor_rollout_ref.actor.copy()
            cfg.ppo_mini_batch_size, cfg.ppo_micro_batch_size = 2, 1
            worker = DataParallelPPOActor(cfg, module, optimizer)
        else:
            cfg = OmegaConf.create(OmegaConf.to_container(config.critic, resolve=True))
            cfg.ppo_mini_batch_size, cfg.ppo_micro_batch_size = 2, 1
            worker = DataParallelPPOCritic(cfg, module, optimizer)
        self.assertEqual(worker.compute_dtype, torch.float16)
        self.assertTrue(worker.grad_scaler.is_enabled())
        self.assertEqual(isinstance(worker.grad_scaler, ShardedGradScaler), sharded)

        ids = torch.tensor([[1, 2, 3, 4], [2, 3, 4, 5]], device='cuda')
        tensors = dict(input_ids=ids, responses=ids[:, -2:].clone(),
                       attention_mask=torch.ones_like(ids),
                       position_ids=torch.arange(4, device='cuda').expand(2, -1))
        with torch.no_grad():
            if role == 'actor':
                _, old_log_probs = worker._forward_micro_batch(tensors, 1.0)
                self.assertEqual(old_log_probs.dtype, torch.float32)
                tensors.update(old_log_probs=old_log_probs, advantages=torch.full((2, 2), 0.01, device='cuda'))
            else:
                values = worker._forward_micro_batch(tensors)
                self.assertEqual(values.dtype, torch.float32)
                tensors.update(values=values, returns=values + 0.01)
        data = DataProto.from_dict(tensors=tensors, meta_info={'temperature': 1.0})
        before = [p.detach().clone() for p in module.parameters()]
        metrics = worker.update_policy(data) if role == 'actor' else worker.update_critic(data)
        self.assertEqual(model.output_dtype, torch.float16)
        self.assertTrue(any(not torch.equal(a, b) for a, b in zip(before, module.parameters())))
        self.assertTrue(all(p.dtype == torch.float32 and torch.isfinite(p).all() for p in module.parameters()))
        self.assertTrue(all(math.isfinite(v) for values in metrics.values() for v in values))

        # An overflowing step must not corrupt weights; the next finite step must recover.
        for overflow in (True, False):
            optimizer.zero_grad()
            loss = sum(p.square().sum() for p in module.parameters()) * 0.001
            worker.grad_scaler.scale(loss).backward()
            if overflow:
                next(module.parameters()).grad.fill_(float('inf'))
            before = [p.detach().clone() for p in module.parameters()]
            scale = worker.grad_scaler.get_scale()
            worker._optimizer_step()
            changed = any(not torch.equal(a, b) for a, b in zip(before, module.parameters()))
            self.assertEqual(changed, not overflow)
            if overflow:
                self.assertLess(worker.grad_scaler.get_scale(), scale)
        optimizer.zero_grad()


if __name__ == '__main__':
    unittest.main()
