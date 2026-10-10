"""第一阶段 CPU 回归：使用真实共用入口、损失和更新适配，不加载大模型。"""
import copy
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import torch
from omegaconf import OmegaConf
from tensordict import TensorDict

from verl import DataProto
from verl.trainer.ppo.ray_trainer import RayPPOTrainer, reduce_metrics
from verl.workers.actor.dp_actor import DataParallelPPOActor, forward_response_logits, token_statistics
from verl.experimental.difficulty.loss_safety import policy_loss, kl_loss, entropy_loss
from verl.experimental.stability.diagnostics import (
    token_diagnostics, score_gradient_diagnostics, sample_parameter_values,
    parameter_update_diagnostics, likelihood_change_diagnostics)
from verl.experimental.stability.generation_audit import token_alignment_report
from search_r1.llm_agent.generation import GenerationConfig, LLMGenerationManager
from test_generation_budget import CharTokenizer


class EvaluationEntryTests(unittest.TestCase):
    def trainer(self, before=False, resumed=False, reward=True, mode='train'):
        """@brief 创建只允许评价、禁止生成管理器及训练更新的入口夹具。
        @param before 训练前评价开关。
        @param resumed 是否模拟完整 checkpoint 恢复。
        @param reward 是否提供评价奖励函数。
        @param mode 难度控制器模式。
        @return 未初始化 GPU 的共用 RayPPOTrainer 实例。
        """
        trainer = object.__new__(RayPPOTrainer)
        trainer.config = OmegaConf.create({'trainer': {'val_only': True, 'val_before_train': before},
                                          'difficulty': {'resume': '/mock/step_42' if resumed else None,
                                                         'resume_mode': 'continue', 'mode': mode}})
        trainer.logger = MagicMock()
        trainer.val_reward_fn = object() if reward else None
        trainer._validate = MagicMock(return_value={'val/test': .5})
        trainer.actor_rollout_wg = MagicMock()
        trainer.train_dataloader = MagicMock()
        trainer.difficulty = (SimpleNamespace(completed_step=42, load_state_dict=MagicMock())
                              if resumed or mode == 'score' else None)
        return trainer

    def test_val_only_independent_of_before_flag(self):
        """@brief 两种训练前评价开关都必须评价一次并保持零训练更新。
        @return 无。
        """
        # 对关闭开关执行真实 fit；旧代码会访问缺失训练配置并继续训练。
        for before in (False, True):
            with self.subTest(before=before):
                trainer = self.trainer(before=before)
                with patch('verl.trainer.ppo.ray_trainer.GenerationConfig', side_effect=AssertionError('entered training')):
                    trainer.fit()
                trainer._validate.assert_called_once_with()
                trainer.actor_rollout_wg.update_actor.assert_not_called()
                trainer.train_dataloader.__iter__.assert_not_called()
                self.assertEqual(trainer.global_steps, 0)
                trainer.logger.log.assert_called_once_with(data={'val/test': .5}, step=0)

    def test_resumed_val_only_preserves_completed_step(self):
        """@brief 恢复状态不能绕过独立评价，也不能递增 global step。
        @return 无。
        """
        trainer = self.trainer(resumed=True)
        with patch('verl.experimental.difficulty.checkpoint.load_driver', return_value={'provenance': {}}), \
             patch('verl.experimental.difficulty.configuration.provenance_matches', return_value=True):
            trainer.fit()
        trainer.actor_rollout_wg.load_training_checkpoint.assert_called_once_with('/mock/step_42/actor')
        trainer._validate.assert_called_once_with()
        trainer.actor_rollout_wg.update_actor.assert_not_called()
        self.assertEqual(trainer.global_steps, 42)

    def test_missing_reward_fails_without_updates(self):
        """@brief 评价缺少奖励函数必须失败，不能静默进入训练。
        @return 无。
        """
        trainer = self.trainer(reward=False)
        with self.assertRaisesRegex(ValueError, 'val_reward_fn'):
            trainer.fit()
        trainer.actor_rollout_wg.update_actor.assert_not_called()
        trainer._validate.assert_not_called()

    def test_score_mode_conflict_fails_without_updates(self):
        """@brief 同时请求评分和评价必须明确报错。
        @return 无。
        """
        trainer = self.trainer(mode='score')
        with self.assertRaisesRegex(ValueError, 'conflicts'):
            trainer.fit()
        trainer.actor_rollout_wg.update_actor.assert_not_called()


class NumericalTests(unittest.TestCase):
    def actor(self, enabled=False):
        """@brief 创建可检查真实 SGD 参数与缩放状态的 CPU actor。
        @param enabled 是否使用 CPU GradScaler。
        @return 未初始化分布式或 GPU 的 actor。
        """
        actor = object.__new__(DataParallelPPOActor)
        actor.actor_module = torch.nn.Linear(2, 1, bias=False)
        actor.actor_optimizer = torch.optim.SGD(actor.actor_module.parameters(), lr=.1)
        actor.config = OmegaConf.create({'grad_clip': 1.})
        actor.grad_scaler = torch.amp.GradScaler('cpu', enabled=enabled, init_scale=16.)
        return actor

    def test_nonfinite_without_scaler_refuses_step(self):
        """@brief 非缩放路径的 NaN 和 inf 梯度不得污染参数。
        @return 无。
        """
        # 分别覆盖 NaN 和 inf；快照检查权重未变及梯度已清理。
        for value in (float('nan'), float('inf')):
            with self.subTest(value=value):
                actor = self.actor()
                before = actor.actor_module.weight.detach().clone()
                actor.actor_module.weight.grad = torch.full_like(before, value)
                with self.assertRaises(FloatingPointError):
                    actor._optimizer_step()
                self.assertTrue(torch.equal(before, actor.actor_module.weight))
                self.assertIsNone(actor.actor_module.weight.grad)
                self.assertFalse(actor.actor_optimizer.state)

    def test_optimizer_step_failure_offloads_loaded_state(self):
        """@brief 更新异常仍卸回已加载的优化器状态，防止异常路径占据 GPU 显存。
        @return 无。
        """
        actor = self.actor()
        actor.optimizer_offload = True
        actor.actor_module.weight.grad = torch.ones_like(actor.actor_module.weight)
        with patch('verl.workers.actor.dp_actor.load_fsdp_optimizer') as load, \
             patch('verl.workers.actor.dp_actor.offload_fsdp_optimizer') as offload, \
             patch('torch.cuda.empty_cache'), patch('torch.cuda.current_device', return_value=0), \
             patch.object(actor.grad_scaler, 'step', side_effect=RuntimeError('simulated update error')):
            with self.assertRaisesRegex(RuntimeError, 'simulated'):
                actor._optimizer_step()
        load.assert_called_once()
        offload.assert_called_once()

    def test_scaled_nonfinite_skips_then_recovers(self):
        """@brief 缩放路径跳过异常更新、回退 scale，并允许下一次有限梯度恢复。
        @return 无。
        """
        actor = self.actor(enabled=True)
        actor.grad_scaler.scale(actor.actor_module.weight.sum()).backward()
        actor.actor_module.weight.grad.fill_(float('inf'))
        before = actor.actor_module.weight.detach().clone()
        _, updated = actor._optimizer_step()
        self.assertFalse(updated)
        self.assertTrue(torch.equal(before, actor.actor_module.weight))
        self.assertEqual(actor.grad_scaler.get_scale(), 8.)
        actor.grad_scaler.scale(actor.actor_module.weight.sum()).backward()
        _, updated = actor._optimizer_step()
        self.assertTrue(updated)
        self.assertFalse(torch.equal(before, actor.actor_module.weight))

    def test_finite_elements_with_overflowed_norm_skip(self):
        """@brief 范数求和溢出也必须跳步，不能依赖逐元素 inf 检查。
        @return 无。
        """
        actor = self.actor(enabled=True)
        actor.grad_scaler.scale(actor.actor_module.weight.sum()).backward()
        actor.actor_module.weight.grad.fill_(1e30)
        before = actor.actor_module.weight.detach().clone()
        norm, updated = actor._optimizer_step()
        self.assertFalse(torch.isfinite(norm))
        self.assertFalse(updated)
        self.assertTrue(torch.equal(before, actor.actor_module.weight))

    def test_masked_nan_is_excluded_from_gradient(self):
        """@brief 无效环境位置的 NaN 不得进入损失或参数梯度。
        @return 无。
        """
        current = torch.tensor([[-1., float('nan')]], requires_grad=True)
        mask = torch.tensor([[1., 0.]])
        pg = policy_loss(torch.tensor([[-1., float('nan')]]), current,
                         torch.tensor([[1., float('nan')]]), mask, .2)[0]
        kl = kl_loss(current, torch.tensor([[-1.2, float('nan')]]), mask)[0]
        entropy = entropy_loss(current.square(), mask)
        # 熵上游若已在无效位置计算 NaN，其导数也可能 NaN；单独验证入口叶张量筛选。
        leaf_entropy = torch.tensor([[.5, float('nan')]], requires_grad=True)
        total = pg + kl - entropy_loss(leaf_entropy, mask) * .001
        total.backward()
        self.assertTrue(torch.isfinite(total))
        self.assertTrue(torch.isfinite(current.grad).all())
        self.assertEqual(current.grad[0, 1].item(), 0.)
        self.assertEqual(leaf_entropy.grad[0, 1].item(), 0.)
        self.assertTrue(torch.isfinite(entropy))

    def test_extreme_ratios_and_zero_advantage_remain_finite(self):
        """@brief 极端概率比、正负及零优势的损失和梯度应保持有限。
        @return 无。
        """
        current = torch.tensor([[1000., -1000., 1000.]], requires_grad=True)
        loss = policy_loss(torch.zeros_like(current), current, torch.tensor([[1., -1., 0.]]),
                           torch.ones_like(current), .2)[0]
        loss.backward()
        self.assertTrue(torch.isfinite(loss))
        self.assertTrue(torch.isfinite(current.grad).all())

    def test_kl_cutoff_values_and_derivatives(self):
        """@brief KL 切换点两侧应沿用原值、原导数及连续切线。
        @return 无。
        """
        # 覆盖负差、零点、切换两侧和高端，避免只验证一个正常点。
        for delta in (-100., 0., 2.4999, 2.5, 2.5001, 100.):
            with self.subTest(delta=delta):
                current = torch.tensor([[-delta]], requires_grad=True)
                loss = kl_loss(current, torch.zeros_like(current), torch.ones_like(current))[0]
                gradient = torch.autograd.grad(loss, current)[0].item()
                expected_gradient = -np.expm1(min(delta, 2.5))
                self.assertAlmostEqual(gradient, expected_gradient, places=4)
                expected_value = (np.expm1(delta) - delta if delta <= 2.5 else
                                  np.expm1(2.5) - 2.5 + (delta - 2.5) * np.expm1(2.5))
                self.assertAlmostEqual(loss.item(), expected_value, delta=max(1e-5, abs(expected_value)*1e-6))

    def test_finite_input_subtraction_overflow_rejected(self):
        """@brief 单个输入有限而概率差溢出时应在指数前失败。
        @return 无。
        """
        current = torch.tensor([[3e38]])
        old = -current
        with self.assertRaises(FloatingPointError):
            policy_loss(old, current, torch.ones_like(current), torch.ones_like(current), .2)
        with self.assertRaises(FloatingPointError):
            kl_loss(old, current, torch.ones_like(current))

    def test_invalid_masks_and_bounds_rejected(self):
        """@brief 空掩码、非二值、错误形状和错误边界应明确报错。
        @return 无。
        """
        values = torch.ones(1, 2)
        # 空、软和可广播错误形状都应拒绝，防止训练掩码变义。
        for mask in (torch.zeros_like(values), torch.full_like(values, .5), torch.ones(1, 1)):
            with self.subTest(mask=mask.tolist()), self.assertRaises(ValueError):
                entropy_loss(values, mask)
        # 分开验证裁剪半径、指数边界及 KL 切换点的非法配置。
        for clip in (-.1, 1., float('nan')):
            with self.subTest(clip=clip), self.assertRaises(ValueError):
                policy_loss(values, values, values, values, clip)
        for bound in (0., 100., float('inf')):
            with self.subTest(bound=bound), self.assertRaises(ValueError):
                policy_loss(values, values, values, values, .2, bound)
        for cutoff in (0., 100., float('nan')):
            with self.subTest(cutoff=cutoff), self.assertRaises(ValueError):
                kl_loss(values, values, values, cutoff)

    def test_fp16_input_uses_fp32_losses(self):
        """@brief FP16 输入应在 FP32 计算损失，并保留有限反传。
        @return 无。
        """
        current = torch.tensor([[-2., -3.]], dtype=torch.float16, requires_grad=True)
        mask = torch.ones_like(current)
        total = policy_loss(current.detach(), current, mask, mask, .2)[0] + kl_loss(current, current.detach(), mask)[0]
        self.assertEqual(total.dtype, torch.float32)
        total.backward()
        self.assertTrue(torch.isfinite(current.grad).all())


class DiagnosticTests(unittest.TestCase):
    def test_extrema_and_counts_aggregate_correctly(self):
        """@brief 跨微批和 worker 的极值取 max，计数取 sum，旧损失取均值。
        @return 无。
        """
        metrics = reduce_metrics({'actor/log_ratio_abs_max': [[1., 20.], [2., 3.]],
                                  'actor/reference_delta_abs_max': [2., 80.],
                                  'actor/stability/valid_tokens_sum': [10., 20.],
                                  'actor/stability/probe_log_prob_delta_abs_max': [1., 4.],
                                  'actor/pg_loss': [1., 3.]})
        self.assertEqual(metrics['actor/log_ratio_abs_max'], 20.)
        self.assertEqual(metrics['actor/reference_delta_abs_max'], 80.)
        self.assertEqual(metrics['actor/stability/valid_tokens_sum'], 30.)
        self.assertEqual(metrics['actor/stability/probe_log_prob_delta_abs_max'], 4.)
        self.assertEqual(metrics['actor/pg_loss'], 2.)

    def test_token_statistics_mask_and_advantage_groups(self):
        """@brief 诊断必须排除环境 NaN，并保留正负零优势的真实 token 数。
        @return 无。
        """
        current = torch.tensor([[.1, -.2, .3, float('nan')]])
        old = torch.zeros_like(current)
        metrics = token_diagnostics(current, old, torch.tensor([[1., -1., 0., float('nan')]]),
                                    torch.tensor([[1., 1., 1., 0.]]))
        self.assertEqual(metrics['actor/stability/valid_tokens_sum'], 3)
        for name in ('positive', 'negative', 'zero'):
            self.assertEqual(metrics['actor/stability/'+name+'_tokens_sum'], 1)
        self.assertAlmostEqual(metrics['actor/stability/log_ratio_sum'], .2, places=6)

    def test_score_diagnostics_do_not_change_backward(self):
        """@brief 分量输出端梯度诊断不得提前写入 .grad 或改变正式反传。
        @return 无。
        """
        log_prob = torch.tensor([[-1., -2.]], requires_grad=True)
        entropy = torch.tensor([[.4, .5]], requires_grad=True)
        components = {'pg': log_prob.sum(), 'kl': log_prob.square().mean()*.01,
                      'entropy': -entropy.mean()*.001}
        expected = torch.autograd.grad(sum(components.values()), (log_prob, entropy), retain_graph=True)
        report = score_gradient_diagnostics(components, log_prob, entropy)
        self.assertIsNone(log_prob.grad)
        self.assertIsNone(entropy.grad)
        self.assertAlmostEqual(report['actor/stability/score_gradient_pg_norm'], np.sqrt(2.))
        sum(components.values()).backward()
        self.assertTrue(torch.equal(log_prob.grad, expected[0]))
        self.assertTrue(torch.equal(entropy.grad, expected[1]))

    def test_bounded_parameter_samples(self):
        """@brief 参数探针有硬上限、独立存储，并报告真实样本变化。
        @return 无。
        """
        parameter = torch.nn.Parameter(torch.arange(10.).reshape(2, 5))
        before = sample_parameter_values([parameter], 3)
        with torch.no_grad():
            parameter.add_(1.)
        after = sample_parameter_values([parameter], 3)
        self.assertEqual(before.tolist(), [0., 1., 2.])
        self.assertEqual(before.numel(), 3)
        report = parameter_update_diagnostics(before, after)
        self.assertAlmostEqual(report['actor/stability/parameter_sample_delta_l2'], np.sqrt(3.), places=6)
        self.assertEqual(sample_parameter_values([], 3).numel(), 0)
        # 预算类型和取值均检查，布尔值不能作为整数预算漏过。
        for limit in (0, -1, True, 1.5):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                sample_parameter_values([parameter], limit)
        with self.assertRaises(ValueError):
            parameter_update_diagnostics(before, after[:1])

    def test_fixed_trajectory_probe_excludes_environment(self):
        """@brief 固定轨迹概率探针只比较模型 token，忽略环境 NaN。
        @return 无。
        """
        before = torch.tensor([[-1., -2., float('nan')]])
        after = torch.tensor([[-.9, -2.2, float('nan')]])
        report = likelihood_change_diagnostics(before, after, torch.tensor([[1., 1., 0.]]))
        self.assertEqual(report['actor/stability/probe_tokens_sum'], 2)
        self.assertAlmostEqual(report['actor/stability/probe_log_prob_delta_sum'], -.1, places=6)

    def test_diagnostic_invalid_inputs(self):
        """@brief 诊断错误形状、掩码和非有限值必须失败，避免写出误导指标。
        @return 无。
        """
        values = torch.ones(1, 2)
        # 诊断与损失遵循相同的有效集和二值掩码约束。
        for mask in (torch.zeros_like(values), torch.ones(1, 1), torch.full_like(values, .5)):
            with self.subTest(mask=mask.tolist()), self.assertRaises(ValueError):
                token_diagnostics(values, values, values, mask)
        with self.assertRaises(FloatingPointError):
            token_diagnostics(values*float('inf'), values, values, values)

    def run_actor_update(self, initial_state, enabled, probe, dropout=0.):
        """@brief 通过真实 update_policy 验证可选诊断对 CPU 小模型更新的兼容性。
        @param initial_state 固定小模型初始参数。
        @param enabled 稳定性诊断开关。
        @param probe 固定轨迹更新后前向开关。
        @param dropout 测试模型 dropout，默认零。
        @return 最终参数、指标及前向调用次数。
        @note 仅 CPU 单元测试小参数更新，不是远端训练实验或模型生成。
        """
        actor = object.__new__(DataParallelPPOActor)
        actor.actor_module = (torch.nn.Linear(2, 2) if dropout == 0 else
                              torch.nn.Sequential(torch.nn.Linear(2, 2), torch.nn.Dropout(dropout)))
        actor.actor_module.load_state_dict(initial_state)
        actor.actor_optimizer = torch.optim.SGD(actor.actor_module.parameters(), lr=.001)
        actor.grad_scaler = torch.amp.GradScaler('cpu', enabled=False)
        actor.config = OmegaConf.create(dict(ppo_mini_batch_size=2, ppo_micro_batch_size=1,
            use_dynamic_bsz=False, state_masking=True, use_kl_loss=True, clip_ratio=.2,
            entropy_coeff=.001, kl_loss_coef=.001, kl_loss_type='low_var_kl',
            loss_numerics='safe_v1', grad_clip=1.,
            stability_diagnostics=dict(enabled=enabled, probe_after_update=probe, parameter_sample_size=3)))
        calls = []
        def forward(micro_batch, temperature):
            """@brief 用 CPU 线性层替代 GPU 前向，保留可求导概率及熵。
            @param micro_batch 真实微批字段。
            @param temperature 与原更新入口相同的温度。
            @return 同形状熵和对数概率。
            """
            calls.append(actor.actor_module.training)
            log_prob = actor.actor_module(micro_batch['responses'].float()) / temperature
            return log_prob.square()*.1, log_prob
        actor._forward_micro_batch = forward
        responses = torch.ones(4, 2, dtype=torch.long)
        with torch.no_grad():
            old = actor.actor_module(responses.float())
        batch = DataProto.from_dict(dict(responses=responses, input_ids=torch.ones(4, 3, dtype=torch.long),
            attention_mask=torch.ones(4, 3, dtype=torch.long),
            position_ids=torch.arange(3).repeat(4, 1), old_log_probs=old,
            ref_log_prob=old-.1, advantages=torch.tensor([[1., 1.], [-1., -1.], [1., 1.], [-1., -1.]]),
            loss_mask=torch.ones(4, 2)), meta_info={'temperature': 1.})
        # 仅测试替换设备搬移；其余 loss、累积、裁剪、更新及诊断调用均执行生产代码。
        with patch.object(TensorDict, 'cuda', lambda self: self):
            metrics = actor.update_policy(batch)
        self.assertTrue(actor.actor_module.training)
        return copy.deepcopy(actor.actor_module.state_dict()), metrics, calls

    def test_fixed_probe_rejects_stochastic_dropout(self):
        """@brief 随机 dropout 不能被误记为策略概率变化，必须在任何更新前拒绝探针。
        @return 无。
        """
        initial = copy.deepcopy(torch.nn.Sequential(torch.nn.Linear(2, 2), torch.nn.Dropout(.2)).state_dict())
        with self.assertRaisesRegex(ValueError, 'zero dropout'):
            self.run_actor_update(initial, True, True, dropout=.2)

    def test_diagnostics_keep_restore_fingerprint(self):
        """@brief 默认关闭及开启只读诊断都兼容原 checkpoint 来源指纹。
        @return 无。
        """
        import tempfile
        from pathlib import Path
        from verl.experimental.difficulty.configuration import provenance
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory) / 'dataset'
            data.write_text('fixed CPU fixture')
            config = OmegaConf.load('verl/trainer/config/ppo_trainer.yaml')
            config.data.train_files = str(data)
            config.data.val_files = str(data)
            with patch('verl.experimental.difficulty.configuration.model_identity', return_value='fixed-reference'):
                baseline = provenance(config)
                del config.actor_rollout_ref.actor.stability_diagnostics
                self.assertEqual(provenance(config), baseline)
                config.actor_rollout_ref.actor.stability_diagnostics = dict(enabled=True,
                    probe_after_update=True, parameter_sample_size=512)
                config.data.record_token_diagnostics = True
                self.assertEqual(provenance(config), baseline)

    def test_real_update_diagnostics_disabled_enabled_equal(self):
        """@brief 诊断开关不改变小模型参数更新；只有显式探针增加前向。
        @return 无。
        """
        torch.manual_seed(42)
        initial = copy.deepcopy(torch.nn.Linear(2, 2).state_dict())
        base, base_metrics, base_calls = self.run_actor_update(initial, False, False)
        enabled, metrics, calls = self.run_actor_update(initial, True, False)
        probed, probe_metrics, probe_calls = self.run_actor_update(initial, True, True)
        # 每个参数逐元素一致，避免只看均值掩盖诊断造成的更新差异。
        for key in base:
            self.assertTrue(torch.equal(base[key], enabled[key]))
            self.assertTrue(torch.equal(base[key], probed[key]))
        self.assertEqual(base_metrics['actor/optimizer_attempts_per_rank'], [2])
        self.assertEqual(base_metrics['actor/optimizer_updates_per_rank'], [2])
        self.assertEqual(base_metrics['actor/optimizer_skips_per_rank'], [0])
        self.assertEqual(len(base_calls), 4)
        self.assertEqual(len(calls), 4)
        self.assertEqual(len(probe_calls), 6)
        self.assertEqual(probe_calls.count(False), 2)
        self.assertFalse(any(key.startswith('actor/stability/') for key in base_metrics))
        self.assertEqual(sum(metrics['actor/stability/valid_tokens_sum']), 8)
        self.assertEqual(sum(probe_metrics['actor/stability/probe_tokens_sum']), 4)


class ForwardInterfaceTests(unittest.TestCase):
    def test_explicit_legacy_signature_supported(self):
        """@brief 明确提供旧参数的模型继续兼容，不依赖 Transformers 版本猜测。
        @return 无。
        """
        class LegacyModel(torch.nn.Module):
            def forward(self, input_ids, num_logits_to_keep=0):
                """@brief 使用显式旧接口裁 LM head 输入的 CPU 替身。
                @param input_ids 完整上下文。
                @param num_logits_to_keep 最后保留的预测位置数。
                @return 简单可核对 logits 对象。
                """
                values = input_ids.float().unsqueeze(-1)
                return SimpleNamespace(logits=values[:, -num_logits_to_keep:] if num_logits_to_keep else values)
        ids = torch.tensor([[1, 2, 3, 4]])
        model = LegacyModel()
        full = forward_response_logits(model, 2, False, input_ids=ids)
        limited = forward_response_logits(model, 2, True, input_ids=ids)
        self.assertTrue(torch.equal(full, limited))

    def test_fsdp_public_module_signature_path(self):
        """@brief FSDP 公开 module 分支使用实际模型签名，CPU 替身不初始化分布式。
        @return 无。
        """
        class Model(torch.nn.Module):
            def forward(self, input_ids, logits_to_keep=0):
                """@brief 当前截断接口的 CPU 替身。
                @param input_ids 完整上下文。
                @param logits_to_keep 保留位置数。
                @return 简单 logits 对象。
                """
                return SimpleNamespace(logits=input_ids[:, -logits_to_keep:].float().unsqueeze(-1))
        class Wrapper(torch.nn.Module):
            def __init__(self):
                """@brief 模拟 FSDP 的公开包装接口。
                @return 无。
                """
                super().__init__()
                self.module = Model()
            def forward(self, **kwargs):
                """@brief 原参数委托到实际模型，不裁上下文。
                @param kwargs 完整模型参数。
                @return 模型输出。
                """
                return self.module(**kwargs)
        with patch('verl.workers.actor.dp_actor.FSDP', Wrapper):
            result = forward_response_logits(Wrapper(), 2, True, input_ids=torch.tensor([[1, 2, 3, 4]]))
        self.assertEqual(result.squeeze().tolist(), [2., 3.])

    def test_unknown_signature_fails_before_forward(self):
        """@brief 不支持接口时明确拒绝，避免优化选项被静默吞掉。
        @return 无。
        """
        class Unknown(torch.nn.Module):
            def forward(self, **kwargs):
                """@brief 不声明截断选项的模型替身。
                @param kwargs 原输入，本测试不允许进入实际前向。
                @return 无。
                @raises AssertionError 如果接口保护失效。
                """
                raise AssertionError('Forward must not execute')
        with self.assertRaises(ValueError):
            forward_response_logits(Unknown(), 2, True, input_ids=torch.ones(1, 4))

    def test_chunked_statistics_values_and_gradients_equal(self):
        """@brief CPU 参考后端验证分块和重算的概率、熵及梯度保持一致。
        @return 无。
        @note 真实 flash-attn 融合算子仅支持 GPU，此测试不替代 GPU 算子验收。
        """
        def cpu_log_probs(logits, responses):
            """@brief 复用原公式提供 GPU 融合算子的 CPU 参考。
            @param logits 批次乘 token 长度乘词表的 logits。
            @param responses 同 token 位置的整数标签。
            @return token 对数概率矩阵，保留梯度。
            """
            return torch.log_softmax(logits, dim=-1).gather(-1, responses.unsqueeze(-1)).squeeze(-1)
        torch.manual_seed(13)
        logits = torch.randn(2, 7, 16, requires_grad=True)
        responses = torch.randint(0, 16, (2, 7))
        # 只替换 CPU 无法执行的 GPU 算子边界，分块、checkpoint 和熵执行生产实现。
        with patch('verl.workers.actor.dp_actor.logprobs_from_logits', cpu_log_probs):
            baseline = token_statistics(logits, responses)
            expected = torch.autograd.grad(sum(value.sum() for value in baseline), logits)[0]
            # 包含单 token 块、非整除尾块及大于长度的块。
            for chunk in (1, 3, 32):
                trial = logits.detach().clone().requires_grad_(True)
                output = token_statistics(trial, responses, recompute=True, chunk_size=chunk)
                for before, after in zip(baseline, output):
                    torch.testing.assert_close(before, after)
                gradient = torch.autograd.grad(sum(value.sum() for value in output), trial)[0]
                torch.testing.assert_close(gradient, expected)


class TokenAuditTests(unittest.TestCase):
    def test_consumed_prefix_is_allowed(self):
        """@brief 删掉合法动作之后的未消费尾部不能误报重分词。
        @return 无。
        """
        tok = CharTokenizer()
        report = token_alignment_report(tok.encode('<answer>x</answer>tail'),
                                        tok.encode('<answer>x</answer>'), tok, 64)
        self.assertTrue(report['token_prefix_matches'])
        self.assertFalse(report['retokenized_prefix'])
        self.assertIsNone(report['finish_reason'])

    def test_native_finish_and_eos_preserved_in_report(self):
        """@brief 原生长度处理 pad 等于 EOS 情况，并保留真实 stop 信息。
        @return 无。
        """
        tok = CharTokenizer()
        tok.eos_token_id = 0
        report = token_alignment_report([65, 0, 0], [65, 0], tok, 8,
                                        dict(raw_token_count=2, finish_reason='stop', stop_reason=0))
        self.assertTrue(report['eos_observed'])
        self.assertTrue(report['eos_removed'])
        self.assertEqual(report['raw_token_ids'], [65, 0])
        self.assertEqual(report['finish_reason'], 'stop')
        self.assertEqual(report['stop_reason'], 0)
        self.assertFalse(report['sampled_logprobs_available'])

    def test_noncanonical_tokens_detected_without_rewrite(self):
        """@brief 同文本不同 token 前缀必须记录，不在审计中修补。
        @return 无。
        """
        tok = SimpleNamespace(pad_token_id=0, eos_token_id=None,
                              decode=lambda ids, **kwargs: ''.join({1:'a', 2:'b', 3:'ab'}[i] for i in ids))
        raw, processed = [1, 2], [3]
        report = token_alignment_report(raw, processed, tok, 2)
        self.assertTrue(report['retokenized_prefix'])
        self.assertTrue(report['token_limit_reached'])
        self.assertEqual(raw, [1, 2])
        self.assertEqual(processed, [3])

    def test_active_rows_and_padding_keep_identity(self):
        """@brief token 审计随活动行还原，不把补齐行或非活动行计入。
        @return 无。
        """
        tok = CharTokenizer()
        config = GenerationConfig(1, 8, 128, 16, 32, 1, record_token_diagnostics=True)
        manager = LLMGenerationManager(tok, None, config)
        output = DataProto.from_dict({'responses': torch.tensor([[65, 0], [66, 0]])},
            non_tensors={'rollout_metadata': np.array([{'finish_reason':'stop'}, {'finish_reason':'length'}],
                                                     dtype=object)})
        diagnostics = [{}, {}, {}]
        manager._record_token_alignment(output, torch.tensor([[65], [66]]),
                                        torch.tensor([True, False, True]), diagnostics)
        self.assertEqual(diagnostics[0]['token_turns'][0]['raw_token_ids'], [65])
        self.assertEqual(diagnostics[1], {})
        self.assertEqual(diagnostics[2]['token_turns'][0]['finish_reason'], 'length')
        with self.assertRaises(ValueError):
            manager._record_token_alignment(output, torch.tensor([[65]]),
                                            torch.tensor([True, False, True]), diagnostics)

    def test_disabled_audit_does_not_decode(self):
        """@brief 默认关闭的审计不得访问 token 或引入额外记录。
        @return 无。
        """
        manager = LLMGenerationManager(CharTokenizer(), None, GenerationConfig(1, 8, 128, 16, 32, 1))
        manager._record_token_alignment(None, None, None, None)

    def test_full_loop_audit_keeps_model_and_environment_masks(self):
        """@brief 完整共用生成循环的审计开关不改变 token、来源 mask 或动作消费。
        @return 无。
        """
        from verl.protocol import pad_dataproto_to_divisor, unpad_dataproto
        tok = CharTokenizer()
        class Worker:
            def __init__(self):
                """@brief 每次生成调用使用独立轮次，先搜索后回答。
                @return 无。
                """
                self.calls = 0
            def generate_sequences(self, batch):
                """@brief 返回固定完整答案，仍执行真实 GPU 行补齐与还原。
                @param batch 已补齐提示批次。
                @return 每行相同答案及可核对的原生终止元数据。
                """
                self.calls += 1
                # 两轮真实环境文本提供 mask 验证，不能只用没有观察的单轮答案。
                text = '<search>q</search>' if self.calls == 1 else '<answer>yes</answer>'
                ids = torch.tensor(tok.encode(text)).repeat(len(batch), 1)
                native = np.empty(len(batch), dtype=object)
                native[:] = [dict(finish_reason='stop', raw_token_count=ids.shape[-1])] * len(batch)
                return DataProto.from_dict({'responses': ids}, non_tensors={'rollout_metadata': native})
        prefix = torch.tensor([[65, 66]])
        batch = DataProto.from_dict(dict(input_ids=prefix, attention_mask=torch.ones_like(prefix),
                                        position_ids=torch.tensor([[0, 1]])))
        outputs = []
        # 同样两轮搜索/回答，仅改变审计开关，逐字段比较训练与观察掩码。
        for audit in (False, True):
            config = GenerationConfig(2, 2, 512, 64, 128, 4,
                observation_truncation='structured', context_policy='bounded',
                process_checks_enabled=True, record_token_diagnostics=audit)
            manager = LLMGenerationManager(tok, Worker(), config)
            manager.batch_search = MagicMock(side_effect=lambda queries: ['document'] * len(queries))
            outputs.append(manager.run_llm_loop(batch, prefix))
        for key in outputs[0].batch.keys():
            self.assertTrue(torch.equal(outputs[0].batch[key], outputs[1].batch[key]))
        self.assertTrue(bool((outputs[1].batch['attention_mask'] > outputs[1].batch['info_mask']).any()))
        report = outputs[1].non_tensor_batch['process_checks'][0]
        self.assertEqual(len(report['token_diagnostics']), 2)
        self.assertEqual(report['token_diagnostics'][0]['finish_reason'], 'stop')
        padded, count = pad_dataproto_to_divisor(outputs[1], 4)
        restored = unpad_dataproto(padded, count)
        self.assertEqual(restored.non_tensor_batch['process_checks'][0], report)
        self.assertNotIn('token_diagnostics', outputs[0].non_tensor_batch['process_checks'][0])

    def test_metax_metadata_opt_in_preserves_tokens_and_probabilities(self):
        """@brief 使用原生完成对象夹具验证元数据开关保持旧 token 和概率逐元素一致。
        @return 无。
        """
        import runpy
        import types
        from pathlib import Path
        # 复用已有 MetaX CPU 测试的导入隔离，不导入原生 GPU 引擎或启动后端。
        native = types.ModuleType('vllm')
        native.LLM = MagicMock()
        path = Path(__file__).resolve().parents[1] / 'verl/third_party/vllm/metax_v_0_11_0/llm.py'
        with patch.dict('sys.modules', {'vllm': native}):
            adapter_type = runpy.run_path(str(path))['LLM']
        adapter = object.__new__(adapter_type)
        adapter._sleeping = False
        adapter._weights_ready = True
        adapter._restore_cpu_weights = MagicMock()
        adapter.pad_token_id = 0
        completion = SimpleNamespace(token_ids=[1, 2], logprobs=[{1:SimpleNamespace(logprob=-.1)},
            {2:SimpleNamespace(logprob=-.2)}], finish_reason='stop', stop_reason=2)
        missing = SimpleNamespace(token_ids=[3], logprobs=None, finish_reason='length', stop_reason=None)
        adapter.engine = SimpleNamespace(generate=MagicMock(return_value=[SimpleNamespace(outputs=[completion, missing])]))
        legacy = adapter.generate(None, object(), [[1]])
        audited = adapter.generate(None, object(), [[1]], return_metadata=True)
        self.assertEqual(len(legacy), 2)
        self.assertTrue(torch.equal(legacy[0], audited[0]))
        self.assertTrue(torch.equal(legacy[1], audited[1]))
        self.assertEqual(audited[2][0]['finish_reason'], 'stop')
        self.assertTrue(audited[2][0]['logprobs_available'])
        self.assertEqual(audited[2][0]['sampled_token_logprobs'], [-.1, -.2])
        self.assertFalse(audited[2][1]['logprobs_available'])
        self.assertIsNone(audited[2][1]['sampled_token_logprobs'])
