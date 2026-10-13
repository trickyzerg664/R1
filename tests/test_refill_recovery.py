"""动态筛选恢复的 CPU 回归：复用真实采样、筛选与恢复入口。"""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch
from torch.utils.data import DataLoader
from omegaconf import OmegaConf, open_dict

from test_dynamic_filter import Dataset, Manager, Worker
import test_task_success_filter as existing_tests
from verl.experimental.difficulty.controller import DifficultyExperiment
from verl.experimental.difficulty.dynamic_filter import training_batches, mixed_groups
from verl.experimental.difficulty.eligibility import normalize_dynamic_filter
from verl.experimental.difficulty.configuration import provenance, provenance_matches
from verl.experimental.process_checks.reward import TASK_SUCCESS_VERSION
from verl.trainer.ppo.ray_trainer import repeat_search_batch
from verl.utils.dataset.rl_dataset import collate_fn


class PatternManager(Manager):
    def __init__(self, counts):
        """@brief 模拟每轮每组的正确次数，保留真实 DataProto 结构。
        @param counts 每轮的正确次数；可为统一整数或逐组整数列表。
        @return 无。
        """
        super().__init__()
        self.counts = counts

    def run_llm_loop(self, gen_batch, initial_input_ids):
        """@brief 生成完整 G8 组，并按指定模式设置模拟答案。
        @param gen_batch 已按八条展开的候选输入。
        @param initial_input_ids 原生成接口的提示 token。
        @return 与输入行对应的模拟生成 DataProto。
        """
        result = super().run_llm_loop(gen_batch, initial_input_ids)
        pattern = self.counts[min(self.calls - 1, len(self.counts) - 1)]
        # 逐组模式用于复现相同题目在不同轮次表现不同的缓存边界。
        for i in range(len(result)):
            k = pattern if isinstance(pattern, int) else pattern[i // 8]
            result.batch['responses'][i, 0] = 1 if i % 8 < k else 2
        return result


class ReportsReward:
    task_success_enabled = True
    group_reward_mode = 'finite'

    def __init__(self, vary=False):
        """@brief 设置全对组是否具有真实模拟奖励差异。
        @param vary 是否对每组第一条正确轨迹施加轻微过程惩罚。
        @return 无。
        """
        self.vary = vary

    def __call__(self, batch):
        """@brief 创建逐轨迹绑定的成功报告及有限奖励。
        @param batch 包含完整 G8 组的候选 DataProto。
        @return 与 responses 同形状的 token 奖励张量。
        """
        scores = torch.zeros_like(batch.batch['responses'], dtype=torch.float32)
        reports, uids = [], []
        # 成功标签始终与真实模拟答案一致，过程罚分不伪造失败标签。
        for i in range(len(batch)):
            correct = bool(batch.batch['responses'][i, 0] == 1)
            uid = f"{batch.meta_info['trajectory_candidate_round']}:{i}"
            uids.append(uid)
            reports.append(dict(trace_uid=uid, task_success_version=TASK_SUCCESS_VERSION,
                protocol_gate=True, task_success=correct, accepted_answer_em=float(correct),
                original_em=float(correct), answered=True))
            scores[i, -1] = float(correct) - (0.02 if self.vary and correct and i % 8 == 0 else 0.)
        batch.non_tensor_batch['process_checks'] = np.array(reports, dtype=object)
        batch.non_tensor_batch['process_trace_uid'] = np.array(uids, dtype=object)
        return scores


class RefillRecoveryTests(unittest.TestCase):
    def setUp(self):
        """@brief 创建独立临时目录和一百题 CPU 题池。
        @return 无。
        """
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        self.rows = [dict(question_id=f'q{i}', source='nq') for i in range(100)]

    def controller(self, name='a', recovery=True, authorized=True, rounds=1):
        """@brief 创建与生产相同的实验控制器。
        @param name 临时输出子目录名。
        @param recovery 是否启用耗尽补入策略。
        @param authorized 是否允许从旧策略显式适配恢复。
        @param rounds 每次尝试补齐的候选轮数间隔。
        @return DifficultyExperiment 控制器。
        """
        dynamic = dict(enabled=True, max_rounds=rounds, eligibility='answer_correct_3_6')
        if recovery:
            dynamic['on_exhaustion'] = 'refill_7_8_v1'
        settings = dict(mode='train', group_size=8, dynamic_filter=dynamic, labels=None, ratios=None)
        if authorized:
            settings['resume_sampling_adaptation'] = 'refill_7_8_v1'
        return DifficultyExperiment(self.rows, settings, 8, 1, 42, self.path / name,
                                    {'initial_model_id': 'test'})

    def stream(self, controller, counts, vary=False, fixed_rows=False):
        """@brief 构造真实筛选入口与可控制的候选流。
        @param controller 当前实验控制器。
        @param counts 每轮的正确次数模式。
        @param vary 是否启用模拟过程罚分。
        @param fixed_rows 是否在各轮复用同八道题，用于缓存优先级边界。
        @return 筛选生成器和用于计数的 Worker。
        """
        loader = DataLoader(Dataset(), batch_sampler=controller.sampler,
                            num_workers=0, collate_fn=collate_fn)
        # 缓存边界隔离为固定题目输入；恢复回归仍消费真实采样器。
        if fixed_rows:
            candidate = collate_fn([Dataset()[i] for i in range(8)])
            loader = [copy.deepcopy(candidate) for _ in counts]
        worker = Worker()
        stream = training_batches(loader, controller, PatternManager(counts), ReportsReward(vary),
            repeat_search_batch, worker, 0, 1, controller.max_candidate_rounds)
        return stream, worker

    def test_seven_correct_fills_at_soft_limit(self):
        """@brief 达到软边界后补入完整七次正确组，保留奖励原值。
        @return 无。
        """
        stream, worker = self.stream(self.controller(), [7])
        batch = next(stream)
        self.assertEqual(len(batch), 64)
        self.assertEqual(batch.meta_info['dynamic_metrics']['dynamic/fallback_k7_groups'], 8)
        self.assertEqual(batch.batch['dynamic_rewards'].sum().item(), 56)
        self.assertEqual(worker.calls, 1)

    def test_eight_with_variance_is_usable(self):
        """@brief 全对组仅在实际奖励存在方差时可补入。
        @return 无。
        """
        stream, worker = self.stream(self.controller(), [8], vary=True)
        batch = next(stream)
        self.assertEqual(batch.meta_info['dynamic_metrics']['dynamic/fallback_k8_groups'], 8)
        self.assertEqual(len(batch), 64)
        self.assertEqual(worker.calls, 1)

    def test_eight_identical_continues_and_extends_loader(self):
        """@brief 全对同分组被拒绝，候选预算耗尽后继续抽取真实合格组。
        @return 无。
        """
        controller = self.controller()
        stream, _ = self.stream(controller, [8, 4])
        batch = next(stream)
        self.assertEqual(controller.sampler.cursor, 2)
        self.assertEqual(controller.completed_step, 0)
        self.assertEqual(batch.meta_info['dynamic_metrics']['dynamic/extended_rounds'], 1)
        self.assertEqual(batch.meta_info['dynamic_metrics']['dynamic/fallback_k8_groups'], 0)

    def test_normal_groups_are_preferred(self):
        """@brief 三至六次组足够时，不接纳备用组或额外补抽。
        @return 无。
        """
        controller = self.controller()
        stream, _ = self.stream(controller, [4])
        batch = next(stream)
        self.assertEqual(batch.meta_info['dynamic_metrics']['dynamic/fallback_k7_groups'], 0)
        self.assertEqual(controller.sampler.cursor, 1)

    def test_same_question_seven_replaces_reserved_eight(self):
        """@brief 同一道题后生成七次正确组时，替换旧的八次备用组。
        @return 无。
        """
        stream, _ = self.stream(self.controller(rounds=2), [8, 7], vary=True, fixed_rows=True)
        batch = next(stream)
        self.assertEqual(batch.meta_info['dynamic_metrics']['dynamic/fallback_k7_groups'], 8)
        self.assertEqual(batch.meta_info['dynamic_metrics']['dynamic/fallback_k8_groups'], 0)
        self.assertEqual({int(row.sum()) for row in (batch.batch['responses'][:, :1] == 1).reshape(8, 8)}, {7})

    def test_normal_group_removes_its_stale_reserve(self):
        """@brief 优先接纳正常组后清除其旧缓存，为其他七次组保留容量。
        @return 无。
        """
        stream, _ = self.stream(self.controller(rounds=2), [7, [4] * 4 + [7] * 4], fixed_rows=True)
        batch = next(stream)
        self.assertEqual(batch.meta_info['dynamic_metrics']['dynamic/fallback_k7_groups'], 4)
        self.assertEqual(len(set(batch.non_tensor_batch['question_id'])), 8)

    def test_fallback_keeps_global_duplicate_exclusion(self):
        """@brief 已训练题即使满足备用条件也不能再次入选。
        @return 无。
        """
        stream, _ = self.stream(self.controller(), [7], fixed_rows=True)
        batch = next(stream)
        groups, _ = mixed_groups(batch, 8, {'q0'}, reward_mode='finite',
            eligibility='answer_correct_3_6', fallback_counts=(7, 8))
        self.assertEqual(len(groups), 7)
        self.assertNotIn('q0', {batch.non_tensor_batch['question_id'][indices[0]] for indices in groups})

    def test_extended_checkpoint_replays_sampler(self):
        """@brief 恢复扩展后的候选游标、曝光和随机流，下一批与原采样器一致。
        @return 无。
        """
        controller = self.controller()
        stream, _ = self.stream(controller, [0, 4])
        batch = next(stream)
        controller.after_step(1, {}, 0., accepted_question_ids=batch.meta_info['dynamic_question_ids'])
        restored = self.controller('b')
        restored.load_state_dict(controller.state_dict())
        self.assertEqual(restored.sampler.cursor, 2)
        self.assertEqual(restored.accepted_question_ids, controller.accepted_question_ids)
        controller.extend_candidate_budget(1)
        self.assertEqual(next(iter(controller.sampler)), next(iter(restored.sampler)))

    def test_insufficient_unused_pool_fails_before_generation(self):
        """@brief 剩余独立题目不足以补齐时，在生成和概率重算之前拒绝。
        @return 无。
        """
        controller = self.controller()
        controller.accepted_question_ids = {f'q{i}' for i in range(96)}
        stream, worker = self.stream(controller, [7])
        with self.assertRaisesRegex(ValueError, 'Insufficient untrained questions'):
            next(stream)
        self.assertEqual(controller.sampler.cursor, 0)
        self.assertEqual(worker.calls, 0)

    def test_candidate_extension_requires_positive_integer(self):
        """@brief 非整数候选预算不得改变游标、预算或曝光记录。
        @return 无。
        """
        controller = self.controller()
        before = controller.sampler.steps
        # bool 是 Python int 子类，但不能作为正式候选预算。
        for rounds in [0, -1, 1.5, True, None]:
            with self.subTest(rounds=rounds), self.assertRaises(ValueError):
                controller.extend_candidate_budget(rounds)
        self.assertEqual(controller.sampler.steps, before)
        self.assertEqual(controller.sampler.cursor, 0)

    def test_old_state_requires_explicit_adaptation(self):
        """@brief 从严格策略恢复到补入策略时，必须显式声明适配。
        @return 无。
        """
        controller = self.controller(recovery=False)
        stream, _ = self.stream(controller, [4])
        batch = next(stream)
        controller.after_step(1, {}, 0., accepted_question_ids=batch.meta_info['dynamic_question_ids'])
        state = controller.state_dict()
        self.controller('allowed').load_state_dict(state)
        with self.assertRaises(ValueError):
            self.controller('denied', authorized=False).load_state_dict(state)

    def test_unrelated_strategy_change_still_rejected(self):
        """@brief 恢复白名单不能放宽评分种子等不相关策略字段。
        @return 无。
        """
        controller = self.controller(recovery=False)
        stream, _ = self.stream(controller, [4])
        batch = next(stream)
        controller.after_step(1, {}, 0., accepted_question_ids=batch.meta_info['dynamic_question_ids'])
        state = controller.state_dict()
        state['strategy']['score_seed'] = 999
        with self.assertRaises(ValueError):
            self.controller('reject').load_state_dict(state)

    def test_default_identity_and_invalid_policy(self):
        """@brief 默认策略身份保持不变，错误恢复组合在生成前拒绝。
        @return 无。
        """
        self.assertEqual(normalize_dynamic_filter(dict(enabled=True, on_exhaustion='error')), dict(enabled=True))
        with self.assertRaises(ValueError):
            normalize_dynamic_filter(dict(enabled=True, on_exhaustion='refill_7_8_v1'))

    def test_provenance_adaptation_preserves_config_and_other_constraints(self):
        """@brief 实际来源计算只放宽授权字段，原配置及学习率约束保持不变。
        @return 无。
        """
        config = existing_tests.TaskSuccessTests.config(self)
        config.difficulty.dynamic_filter.eligibility = 'answer_correct_3_6'
        # 仅隔离大模型身份读取，来源指纹算法和小数据文件哈希均保持真实。
        with patch('verl.experimental.difficulty.configuration.model_identity', return_value='fixture'):
            parent = provenance(config)
            changed = copy.deepcopy(config)
            with open_dict(changed):
                changed.difficulty.dynamic_filter.on_exhaustion = 'refill_7_8_v1'
                changed.difficulty.resume_sampling_adaptation = 'refill_7_8_v1'
            before = OmegaConf.to_container(changed, resolve=True)
            self.assertTrue(provenance_matches(changed, parent))
            self.assertEqual(OmegaConf.to_container(changed, resolve=True), before)
            changed.actor_rollout_ref.actor.optim.lr *= 2
            self.assertFalse(provenance_matches(changed, parent))
            changed.actor_rollout_ref.actor.optim.lr /= 2
            changed.difficulty.resume_sampling_adaptation = None
            self.assertFalse(provenance_matches(changed, parent))


if __name__ == '__main__':
    unittest.main()
