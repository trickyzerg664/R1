"""任务成功筛选 CPU 回归：真实奖励入口、完整组、旧模式与恢复身份。"""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import torch
from torch.utils.data import DataLoader
from omegaconf import OmegaConf
from verl import DataProto
from verl.experimental.process_checks.protocol import TraceLedger
from verl.experimental.process_checks.reward import (
    TASK_SUCCESS_VERSION, process_reward_components, process_score)
from verl.experimental.difficulty.eligibility import normalize_dynamic_filter
from verl.experimental.difficulty.dynamic_filter import mixed_groups, training_batches, take_rows
from verl.experimental.difficulty.configuration import prepare_config, provenance
from verl.experimental.difficulty.controller import DifficultyExperiment
from verl.trainer.main_ppo import RewardManager
from verl.trainer.ppo.ray_trainer import repeat_search_batch
from verl.trainer.ppo.core_algos import compute_grpo_outcome_advantage
from verl.utils.dataset.rl_dataset import collate_fn
from search_r1.llm_agent.context_budget import pad_token_rows
from tests.test_process_checks import execute
from tests.test_generation_budget import CharTokenizer
from tests.test_reward_boundary import batch as answer_batch
from tests.test_dynamic_filter import Dataset, Worker

ROOT = Path(__file__).resolve().parents[1]


def group_batch(rewards, successes, original=None, accepted=None, gates=None):
    """@brief 构造同行绑定的完整组，分别控制奖励、成功与两种 EM 口径。
    @param rewards 逐轨迹训练奖励列表。
    @param successes 显式布尔任务成功列表。
    @param original 可选原文本 EM 列表，缺省采用成功值。
    @param accepted 可选实际接受答案 EM 列表，缺省采用成功值。
    @param gates 可选布尔协议门控列表，缺省全部合法。
    @return 含版本化报告与独立轨迹身份的 DataProto。
    """
    n = len(rewards)
    original = list(map(float, successes)) if original is None else original
    accepted = list(map(float, successes)) if accepted is None else accepted
    gates = [True] * n if gates is None else gates
    # 模拟记录来自共用评分分量；身份与组 uid 独立，缺答案与错答分别表示。
    reports = [dict(trace_uid=f't:{i}', original_em=original[i], accepted_answer_em=accepted[i],
                    answered=rewards[i] >= 0, protocol_gate=gates[i], task_success=successes[i],
                    task_success_version=TASK_SUCCESS_VERSION)
               for i in range(n)]
    return DataProto.from_dict(
        {'dynamic_rewards': torch.tensor(rewards, dtype=torch.float32)[:, None]},
        non_tensors={'uid': np.array(['u'] * n), 'question_id': np.array(['q'] * n),
                     'process_trace_uid': np.array([r['trace_uid'] for r in reports]),
                     'process_checks': np.array(reports, dtype=object)})


def gated_reward(apply=True):
    """@brief 复用真实奖励管理器，区分训练门控与开发评价。
    @param apply 是否将过程门控和缺答案惩罚应用到训练奖励。
    @return 正式 RewardManager，模型和 GPU 均不加载。
    """
    return RewardManager(CharTokenizer(), 0, answer_mode='response_only_v1',
                         process_checks={'enabled': True, 'reward_gate': True,
                                         'missing_answer_penalty': .1},
                         apply_process_reward=apply,
                         trajectory_logging={'enabled': False})


class TaskManager:
    """只模拟模型返回，动作账本、真实奖励和完整补抽仍复用生产入口。"""

    def __init__(self, all_wrong=False):
        """@brief 建立可重复的候选生成夹具，不启动真实模型。
        @param all_wrong 是否使所有候选均无正确答案。
        @return 无。
        """
        self.config = type('Config', (), {'max_start_length': 2})()
        self.all_wrong, self.calls = all_wrong, 0

    def run_llm_loop(self, gen_batch, initial_input_ids):
        """@brief 返回全错差异组、全对组与混合组，账本由真实执行器生成。
        @param gen_batch 经过正式采样器展开并绑定种子的候选 DataProto。
        @param initial_input_ids 共用入口提供的问题 token，夹具保留完整 prompts。
        @return 含模型响应、完整 mask 和真实过程报告的 DataProto。
        """
        self.calls += 1
        texts = []
        for i in range(len(gen_batch)):
            group = i // 8
            correct = not self.all_wrong and (group == 1 or (group > 1 and i % 8 < 4))
            # 首组七条错答与一条缺答案，复现原 finite 筛选的错误入选通道。
            texts.append('<answer></answer>' if group == 0 and i % 8 == 7 else
                         '<answer>yes</answer>' if correct else '<answer>no</answer>')
        ledger = TraceLedger(len(texts))
        execute(ledger, texts, final=True)
        reports = ledger.reports()
        responses = pad_token_rows([CharTokenizer().encode(text) for text in texts], 0)
        prompts = gen_batch.batch['input_ids']
        attention = torch.cat((gen_batch.batch['attention_mask'], (responses != 0).long()), -1)
        return DataProto.from_dict(
            {'prompts': prompts, 'responses': responses, 'responses_with_info_mask': responses,
             'input_ids': torch.cat((prompts, responses), -1), 'attention_mask': attention,
             'info_mask': attention, 'position_ids': (attention.cumsum(-1) - 1).clamp_min(0)},
            non_tensors={'process_checks': np.array(reports, dtype=object),
                         'process_trace_uid': np.array([r['trace_uid'] for r in reports])},
            meta_info={'active_mask': [not r['answered'] for r in reports],
                       'valid_search_stats': [0] * len(texts)})


class TaskSuccessTests(unittest.TestCase):
    def setUp(self):
        """@brief 为配置、恢复和补抽测试建立独立 CPU 目录。
        @return 无。
        """
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)

    def controller(self, name='new', mode='task_success_mixed'):
        """@brief 构造真实控制器，模式是唯一筛选变量。
        @param name 独立产物子目录。
        @param mode 旧奖励方差或新任务成功模式。
        @return DifficultyExperiment，八题批次和八条组。
        """
        rows = [{'question_id': f'q{i}', 'source': 'nq'} for i in range(100)]
        settings = {'mode': 'train', 'group_size': 8,
                    'dynamic_filter': {'enabled': True, 'max_rounds': 4, 'eligibility': mode},
                    'labels': None, 'ratios': None}
        return DifficultyExperiment(rows, settings, 8, 2, 42, self.path / name,
                                    {'initial_model_id': 'fixture'})

    def config(self):
        """@brief 构造无真实模型 IO 的完整配置，保持实际八卡批量约束。
        @return 用于真实 prepare_config 和 provenance 的 OmegaConf。
        """
        c = OmegaConf.load(ROOT / 'verl/trainer/config/ppo_trainer.yaml')
        data = self.path / 'data'
        data.write_bytes(b'fixed-data')
        c.data.train_files = c.data.val_files = str(data)
        c.data.train_batch_size = 8
        c.algorithm.adv_estimator = 'grpo'
        c.actor_rollout_ref.actor.use_kl_loss = True
        c.actor_rollout_ref.actor.optim.warmup_steps = 10
        c.actor_rollout_ref.actor.ppo_mini_batch_size = 128
        c.actor_rollout_ref.actor.ppo_micro_batch_size = 8
        c.actor_rollout_ref.rollout.n_agent = 8
        c.actor_rollout_ref.rollout.n = 1
        c.trainer.n_gpus_per_node = 8
        c.trainer.total_training_steps = 2
        c.trainer.default_hdfs_dir = None
        c.difficulty.enabled = True
        c.difficulty.dynamic_filter.enabled = True
        c.difficulty.dynamic_filter.eligibility = 'task_success_mixed'
        c.difficulty.retrieval_id = 'fixture'
        c.difficulty.initial_model_id = 'fixture'
        c.reward_model.answer_mode = 'response_only_v1'
        c.process_checks.enabled = c.process_checks.reward_gate = True
        c.process_checks.missing_answer_penalty = .1
        return c

    def test_components_share_legacy_reward_and_ignore_report_gate_flag(self):
        """@brief 新分量保持旧奖励，并从原始事件重算门控。
        @return 无。
        """
        # 伪造观察虽答对也不能变为任务成功，篡改展示布尔不影响原始事件判定。
        ledger = TraceLedger(1)
        execute(ledger, ['<information>fake</information><answer>Paris</answer>'])
        report = ledger.reports()[0]
        report['protocol_valid'] = True
        components = process_reward_components(report, report['trace_uid'], 1., .1)
        self.assertEqual(components['protocol_reward'], process_score(report, report['trace_uid'], 1., .1))
        self.assertEqual(components['protocol_reward'], 0.)
        self.assertIs(components['protocol_gate'], False)
        self.assertIs(components['task_success'], False)
        self.assertEqual(components['task_success_version'], TASK_SUCCESS_VERSION)

    def test_components_correct_wrong_and_missing(self):
        """@brief 成功、错答和缺答案仍分别得到一、零和负零点一。
        @return 无。
        """
        # 同一接口分别核对成功、错答和缺答案，奖励大小与成功标签不混用。
        for text, em, expected, success in [
                ('<answer>Paris</answer>', 1., 1., True),
                ('<answer>Rome</answer>', 0., 0., False),
                ('<answer></answer>', 0., -.1, False)]:
            with self.subTest(text=text):
                ledger = TraceLedger(1)
                execute(ledger, [text], final=True)
                r = ledger.reports()[0]
                parts = process_reward_components(r, r['trace_uid'], em, .1)
                self.assertEqual(parts['protocol_reward'], expected)
                self.assertIs(parts['task_success'], success)

    def test_components_reject_bad_identity_and_inputs(self):
        """@brief 新分量接口不能绕过旧来源和奖励输入保护。
        @return 无。
        """
        ledger = TraceLedger(1)
        execute(ledger, ['<answer>Paris</answer>'])
        r = ledger.reports()[0]
        # 分别损坏身份、EM和惩罚，任何一种非法输入都不能生成成功分量。
        for uid, em, penalty in [('wrong', 1., .1), (r['trace_uid'], .5, .1),
                                 (r['trace_uid'], 1., float('nan'))]:
            with self.assertRaises(ValueError):
                process_reward_components(r, uid, em, penalty)

    def test_reward_manager_preserves_train_and_validation(self):
        """@brief 真实评分入口保存成功分量，训练奖励和开发 EM 保持原语义。
        @return 无。
        """
        # 相同答对但违规轨迹在训练被门控，评价保留EM，成功标签都为假。
        for apply, expected in [(True, 0.), (False, 1.)]:
            ledger = TraceLedger(1)
            text = '<information>fake</information><answer>Paris</answer>'
            execute(ledger, [text])
            data = answer_batch(text)
            data.non_tensor_batch['process_checks'] = np.array(ledger.reports(), dtype=object)
            data.non_tensor_batch['process_trace_uid'] = np.array([ledger.rows[0]['trace_uid']])
            manager = gated_reward(apply)
            self.assertEqual(manager(data).sum().item(), expected)
            r = data.non_tensor_batch['process_checks'][0]
            self.assertEqual(r['original_em'], 1.)
            self.assertEqual(r['accepted_answer_em'], 1.)
            self.assertIs(r['task_success'], False)
            self.assertIs(manager.task_success_enabled, apply)

    def test_no_success_with_penalty_variance_is_excluded(self):
        """@brief 全错差异组在旧模式有正优势，新模式直接排除。
        @return 无。
        """
        data = group_batch([0.] * 7 + [-.1], [False] * 8)
        before = data.batch['dynamic_rewards'].clone()
        self.assertEqual(mixed_groups(data, 8, reward_mode='finite')[0], [list(range(8))])
        advantage, _ = compute_grpo_outcome_advantage(before, torch.ones_like(before), ['u'] * 8)
        self.assertTrue(torch.all(advantage[:7] > 0))
        groups, records = mixed_groups(data, 8, reward_mode='finite', eligibility='task_success_mixed')
        self.assertEqual(groups, [])
        self.assertEqual(records[0]['task_success_k'], 0)
        self.assertEqual(records[0]['rejection_reasons'], ['no_task_success'])
        torch.testing.assert_close(data.batch['dynamic_rewards'], before)

    def test_mixed_success_keeps_complete_group_and_rewards(self):
        """@brief 成功失败混合组完整保留，奖励矩阵不被筛选器改写。
        @return 无。
        """
        data = group_batch([1.] + [0.] * 6 + [-.1], [True] + [False] * 7)
        before = data.batch['dynamic_rewards'].clone()
        groups, records = mixed_groups(data, 8, reward_mode='finite', eligibility='task_success_mixed')
        self.assertEqual(groups, [list(range(8))])
        self.assertEqual(records[0]['task_success_k'], 1)
        self.assertEqual(records[0]['accepted_answer_em_k'], 1.)
        self.assertEqual(records[0]['rejection_reasons'], [])
        torch.testing.assert_close(data.batch['dynamic_rewards'], before)

    def test_all_success_is_excluded(self):
        """@brief 全成功组没有相对任务信号，保持排除。
        @return 无。
        """
        groups, records = mixed_groups(group_batch([1.] * 8, [True] * 8), 8,
                                        reward_mode='finite', eligibility='task_success_mixed')
        self.assertEqual(groups, [])
        self.assertIn('all_task_success', records[0]['rejection_reasons'])

    def test_original_em_does_not_substitute_task_success(self):
        """@brief 原文本正确与门控后成功独立，筛选只读取后者。
        @return 无。
        """
        # 门控失败的正确答案与缺答案不能凑成成功组。
        failed = group_batch([0.] * 7 + [-.1], [False] * 8, original=[1.] * 7 + [0.],
                             accepted=[1.] * 7 + [0.], gates=[False] * 7 + [True])
        self.assertEqual(mixed_groups(failed, 8, reward_mode='finite', eligibility='task_success_mixed')[0], [])
        # 反向口径差异也不能把实际成功误当成原文本全错组排除。
        mixed = group_batch([1.] + [0.] * 7, [True] + [False] * 7, original=[0.] * 8)
        groups, records = mixed_groups(mixed, 8, reward_mode='finite', eligibility='task_success_mixed')
        self.assertEqual(len(groups), 1)
        self.assertEqual(records[0]['em_k'], 0.)
        self.assertEqual(records[0]['task_success_k'], 1)

    def test_missing_labels_do_not_fallback(self):
        """@brief 新模式缺标签或独立身份时失败，旧模式仍接受历史报告。
        @return 无。
        """
        # 分别删除来源报告或独立身份，确认旧模式兼容与新模式严格失败可共存。
        for remove in ('process_checks', 'process_trace_uid'):
            data = group_batch([1.] + [0.] * 7, [True] + [False] * 7)
            data.non_tensor_batch.pop(remove)
            self.assertEqual(len(mixed_groups(data, 8, reward_mode='finite')[0]), 1)
            with self.assertRaisesRegex(ValueError, 'row-bound'):
                mixed_groups(data, 8, reward_mode='finite', eligibility='task_success_mixed')

    def test_bad_labels_fail_before_filtering(self):
        """@brief 拒绝字符串标记、版本缺失、分量矛盾、非法 EM 与同行错配。
        @return 无。
        """
        # 每次只污染一个标签字段，避免另一条错误提前抛出掩盖被测保护。
        for key, value in [('task_success', 'false'), ('protocol_gate', 1),
                           ('task_success_version', 'future'), ('accepted_answer_em', .5),
                           ('answered', False), ('trace_uid', 'other'), ('task_success', False)]:
            with self.subTest(key=key, value=value):
                data = group_batch([1.] + [0.] * 7, [True] + [False] * 7)
                data.non_tensor_batch['process_checks'][0][key] = value
                with self.assertRaises(ValueError):
                    mixed_groups(data, 8, reward_mode='finite', eligibility='task_success_mixed')

    def test_duplicate_trace_identity_fails(self):
        """@brief 复制轨迹身份不能冒充同题独立的八次 rollout。
        @return 无。
        """
        data = group_batch([1.] + [0.] * 7, [True] + [False] * 7)
        data.non_tensor_batch['process_trace_uid'][1] = data.non_tensor_batch['process_trace_uid'][0]
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            mixed_groups(data, 8, reward_mode='finite', eligibility='task_success_mixed')

    def test_nonfinite_rewards_and_incomplete_groups_fail(self):
        """@brief 成功标签不能绕过奖励有限性与完整八条组约束。
        @return 无。
        """
        # 成功标签合法时仍需拒绝每一种非有限奖励，不能因新资格放宽原数值约束。
        for value in [float('nan'), float('inf'), float('-inf')]:
            data = group_batch([1.] + [0.] * 7, [True] + [False] * 7)
            data.batch['dynamic_rewards'][0, 0] = value
            with self.assertRaisesRegex(ValueError, 'finite rewards'):
                mixed_groups(data, 8, reward_mode='finite', eligibility='task_success_mixed')
        data = group_batch([1.] + [0.] * 7, [True] + [False] * 7)
        with self.assertRaisesRegex(ValueError, 'complete groups'):
            mixed_groups(take_rows(data, list(range(7))), 8,
                         reward_mode='finite', eligibility='task_success_mixed')

    def test_question_identity_and_seen_are_enforced(self):
        """@brief 新模式保留同题身份检查和已接受问题去重。
        @return 无。
        """
        data = group_batch([1.] + [0.] * 7, [True] + [False] * 7)
        groups, records = mixed_groups(data, 8, seen={'q'}, reward_mode='finite',
                                        eligibility='task_success_mixed')
        self.assertEqual(groups, [])
        self.assertIn('duplicate_question', records[0]['rejection_reasons'])
        data.non_tensor_batch['question_id'][1] = 'other'
        with self.assertRaisesRegex(ValueError, 'Question identities'):
            mixed_groups(data, 8, reward_mode='finite', eligibility='task_success_mixed')

    def test_reward_variance_threshold_is_preserved(self):
        """@brief 成功混合也不能绕过用户已有的有限奖励方差阈值。
        @return 无。
        """
        data = group_batch([1.] + [0.] * 7, [True] + [False] * 7)
        groups, records = mixed_groups(data, 8, reward_mode='finite', variance_epsilon=1.,
                                        eligibility='task_success_mixed')
        self.assertEqual(groups, [])
        self.assertEqual(records[0]['rejection_reasons'], ['no_reward_variance'])

    def test_reordered_groups_keep_row_bound_success(self):
        """@brief 完整组重排后成功标签与独立轨迹身份同步，筛选不串组。
        @return 无。
        """
        a = group_batch([0.] * 7 + [-.1], [False] * 8)
        b = group_batch([1.] + [0.] * 7, [True] + [False] * 7)
        b.non_tensor_batch['uid'][:] = 'v'
        b.non_tensor_batch['question_id'][:] = 'r'
        b.non_tensor_batch['process_trace_uid'] = np.array([f'b:{i}' for i in range(8)])
        for i, report in enumerate(b.non_tensor_batch['process_checks']):
            report['trace_uid'] = f'b:{i}'
        merged = DataProto.concat([a, b])
        merged.reorder(torch.tensor([i for pair in zip(range(8), range(8, 16)) for i in pair]))
        groups, records = mixed_groups(merged, 8, reward_mode='finite', eligibility='task_success_mixed')
        self.assertEqual(groups, [list(range(1, 16, 2))])
        self.assertEqual([r['task_success_k'] for r in records], [0, 1])
        self.assertEqual(merged.non_tensor_batch['question_id'][groups[0]].tolist(), ['r'] * 8)

    def test_legacy_normalization_preserves_settings(self):
        """@brief 缺省与显式旧模式得到相同字典，调用者原设置不被修改。
        @return 无。
        """
        old = {'enabled': True, 'max_rounds': 16}
        explicit = {**old, 'eligibility': 'reward_variance'}
        self.assertEqual(normalize_dynamic_filter(explicit), old)
        self.assertIn('eligibility', explicit)
        self.assertEqual(normalize_dynamic_filter({'enabled': False, 'eligibility': 'reward_variance'}),
                         {'enabled': False})

    def test_unknown_modes_and_versions_are_rejected(self):
        """@brief 模式拼写、规则版本和未启用组合不得静默沿用旧行为。
        @return 无。
        """
        # 拼写、开启条件和两个模式的版本约束逐项验收，失败不能回退到旧规则。
        for settings in [{'enabled': True, 'eligibility': 'typo'},
                         {'enabled': False, 'eligibility': 'task_success_mixed'},
                         {'enabled': True, 'eligibility': 'task_success_mixed', 'eligibility_version': 'future'},
                         {'enabled': True, 'eligibility': 'reward_variance', 'eligibility_version': 'future'}]:
            with self.assertRaises(ValueError):
                normalize_dynamic_filter(settings)
        with self.assertRaises(ValueError):
            mixed_groups(group_batch([1., 0.], [True, False]), 2, eligibility='typo')

    def test_fingerprint_legacy_compatibility_and_new_mode_difference(self):
        """@brief 新字段缺省兼容旧指纹，启用资格规则会改变训练身份。
        @return 无。
        """
        c = self.config()
        c.difficulty.dynamic_filter.eligibility = 'reward_variance'
        with patch('verl.experimental.difficulty.configuration.model_identity', return_value='fixture'):
            explicit = provenance(c)
            del c.difficulty.dynamic_filter.eligibility
            self.assertEqual(provenance(c), explicit)
            c.difficulty.dynamic_filter.eligibility = 'task_success_mixed'
            changed = provenance(c)
            self.assertNotEqual(changed['training'], explicit['training'])
            # 审计地址仍不影响训练身份，规则版本由规范化入口固定。
            c.process_checks.audit_path = 'another-path'
            self.assertEqual(provenance(c), changed)

    def test_prepare_config_accepts_gated_training_and_keeps_hyperparameters(self):
        """@brief 合法配置通过前置检查，资格修复不更改奖励及学习率裁剪。
        @return 无。
        """
        c = self.config()
        before = OmegaConf.to_container(c.actor_rollout_ref.actor)
        process = OmegaConf.to_container(c.process_checks)
        with patch('verl.experimental.difficulty.configuration.model_identity', return_value='fixture'):
            prepare_config(c)
        self.assertEqual(OmegaConf.to_container(c.actor_rollout_ref.actor), before)
        self.assertEqual(OmegaConf.to_container(c.process_checks), process)
        self.assertEqual(c.difficulty.group_size, 8)

    def test_prepare_config_rejects_inactive_or_ungated_mode(self):
        """@brief 新模式在生成前拒绝关闭实验、关闭动态、无门控或旧答案评分。
        @return 无。
        """
        # 逐次只关闭一个前提，拒绝必须发生在模型身份IO和worker构建之前。
        for field in ['difficulty', 'dynamic', 'process', 'gate', 'answer']:
            with self.subTest(field=field):
                c = self.config()
                if field == 'difficulty':
                    c.difficulty.enabled = False
                elif field == 'dynamic':
                    c.difficulty.dynamic_filter.enabled = False
                elif field == 'process':
                    c.process_checks.enabled = c.process_checks.reward_gate = False
                    c.process_checks.missing_answer_penalty = 0.
                elif field == 'gate':
                    c.process_checks.reward_gate = False
                    c.process_checks.missing_answer_penalty = 0.
                else:
                    c.reward_model.answer_mode = 'legacy'
                with self.assertRaisesRegex(ValueError, 'task_success_mixed'):
                    prepare_config(c)

    def test_legacy_output_directory_accepts_explicit_default(self):
        """@brief 已有旧运行目录可接受新增缺省配置，不产生策略误失配。
        @return 无。
        """
        legacy = self.controller('old', 'reward_variance')
        settings = copy.deepcopy(legacy.settings)
        settings['dynamic_filter']['eligibility'] = 'reward_variance'
        again = DifficultyExperiment(legacy.rows, settings, 8, 2, 42, legacy.output_dir, legacy.provenance)
        self.assertEqual(again.strategy, legacy.strategy)
        self.assertNotIn('eligibility', again.settings['dynamic_filter'])
        self.assertEqual(again.dynamic_eligibility, 'reward_variance')

    def test_same_mode_state_restores_and_changed_mode_rejects_branches(self):
        """@brief 同版本恢复成功，资格变化在 branch 和兼容来源路径仍被拒绝。
        @return 无。
        """
        current = self.controller()
        state = current.state_dict()
        restored = self.controller('restored')
        restored.load_state_dict(state)
        self.assertEqual(restored.strategy, current.strategy)
        old = self.controller('old', 'reward_variance')
        old_state = old.state_dict()
        # 两种恢复类型都不能切换资格规则，即使调用方提供兼容来源也必须拒绝。
        for branch in [False, True]:
            with self.assertRaisesRegex(ValueError, 'eligibility differs'):
                current.load_state_dict(old_state, branch=branch, compatible_provenance=old.provenance)
            with self.assertRaisesRegex(ValueError, 'eligibility differs'):
                old.load_state_dict(state, branch=branch)
        bad = copy.deepcopy(state)
        bad['strategy']['dynamic_filter']['eligibility_version'] = 'future'
        with self.assertRaisesRegex(ValueError, 'version'):
            restored.load_state_dict(bad)

    def test_complete_refill_real_reward_and_checkpoint_replay(self):
        """@brief 共用补抽和真实奖励仅保留成功混合组，完整状态可恢复。
        @return 无。
        """
        c, manager, worker = self.controller(), TaskManager(), Worker()
        loader = DataLoader(Dataset(), batch_sampler=c.sampler, num_workers=0, collate_fn=collate_fn)
        stream = training_batches(loader, c, manager, gated_reward(), repeat_search_batch, worker, 0, 2, 4)
        result = next(stream)
        self.assertEqual(len(result), 64)
        self.assertEqual(worker.calls, 1)
        self.assertEqual(manager.calls, 2)
        self.assertEqual(len(result.meta_info['dynamic_question_ids']), 8)
        for indices in mixed_groups(result, 8, reward_mode='finite', eligibility='task_success_mixed')[0]:
            labels = [result.non_tensor_batch['process_checks'][i]['task_success'] for i in indices]
            self.assertGreater(sum(labels), 0)
            self.assertLess(sum(labels), 8)
        self.assertEqual(result.meta_info['dynamic_metrics']['dynamic/rejected_no_task_success_groups'], 2)
        self.assertEqual(result.meta_info['dynamic_metrics']['dynamic/rejected_all_task_success_groups'], 2)
        events = [json.loads(line) for line in (c.output_dir / 'metrics.jsonl').read_text().splitlines()]
        self.assertEqual(events[0]['eligibility'], 'task_success_mixed')
        self.assertIn('no_task_success', events[0]['groups'][0]['rejection_reasons'])
        c.after_step(1, {}, 0., accepted_question_ids=result.meta_info['dynamic_question_ids'])
        restored = self.controller('restored')
        restored.load_state_dict(c.state_dict())
        self.assertEqual(next(iter(restored.sampler)), next(iter(c.sampler)))
        self.assertEqual(restored.accepted_question_ids, c.accepted_question_ids)

    def test_refill_exhaustion_has_no_partial_update(self):
        """@brief 全错差异组在新模式耗尽补抽，不计算训练概率或推进步数。
        @return 无。
        """
        c, manager, worker = self.controller(), TaskManager(all_wrong=True), Worker()
        loader = DataLoader(Dataset(), batch_sampler=c.sampler, num_workers=0, collate_fn=collate_fn)
        with self.assertRaisesRegex(RuntimeError, 'no partial optimizer update'):
            next(training_batches(loader, c, manager, gated_reward(), repeat_search_batch, worker, 0, 2, 2))
        self.assertEqual(c.completed_step, 0)
        self.assertEqual(worker.calls, 0)
        self.assertEqual(c.accepted_question_ids, set())
        events = [json.loads(line) for line in (c.output_dir / 'metrics.jsonl').read_text().splitlines()]
        self.assertEqual(events[-1]['event'], 'filter_exhausted')

    def test_validation_reward_rejected_before_generation(self):
        """@brief 纯评价奖励不能作为新筛选训练入口，拒绝发生在生成前。
        @return 无。
        """
        c, manager, worker = self.controller(), TaskManager(), Worker()
        loader = DataLoader(Dataset(), batch_sampler=c.sampler, num_workers=0, collate_fn=collate_fn)
        with self.assertRaisesRegex(ValueError, 'gated training reward'):
            next(training_batches(loader, c, manager, gated_reward(False), repeat_search_batch, worker, 0, 2, 2))
        self.assertEqual(manager.calls, 0)
        self.assertEqual(worker.calls, 0)


    def test_new_mode_supports_binary_reward_without_penalty(self):
        """@brief 无缺答案惩罚时仍按成功混合筛选，二值奖励保护保持。
        @return 无。
        """
        # 资格模式与奖励类型正交，不能只支持负奖励的历史配置。
        data = group_batch([1.] + [0.] * 7, [True] + [False] * 7)
        groups, _ = mixed_groups(data, 8, reward_mode='binary', eligibility='task_success_mixed')
        self.assertEqual(groups, [list(range(8))])

    def test_gpu_padding_must_be_removed_before_task_filter(self):
        """@brief 补齐复制行不冒充独立轨迹，去补齐后报告和成功标签原样保留。
        @return 无。
        """
        from verl.protocol import pad_dataproto_to_divisor, unpad_dataproto
        data = group_batch([1.] + [0.] * 7, [True] + [False] * 7)
        padded, count = pad_dataproto_to_divisor(data, 16)
        # 未移除的 GPU 复制行必须拒绝，实际训练流程先去补齐再进入筛选。
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            mixed_groups(padded, 8, reward_mode='finite', eligibility='task_success_mixed')
        restored = unpad_dataproto(padded, count)
        self.assertEqual(mixed_groups(restored, 8, reward_mode='finite',
                                      eligibility='task_success_mixed')[0], [list(range(8))])
        self.assertEqual(restored.non_tensor_batch['process_checks'].tolist(),
                         data.non_tensor_batch['process_checks'].tolist())

    def test_checkpoint_config_rejects_new_eligibility_in_continue_and_branch(self):
        """@brief 实际入口指纹检查拒绝将旧资格 checkpoint 作为新模式续训。
        @return 无。
        """
        parent = self.path / 'parent'
        parent.mkdir()
        (parent / 'COMPLETE.json').write_text('{}')
        # 只隔离模型大文件身份和 checkpoint 元数据 IO，指纹与配置检查保持真实。
        with patch('verl.experimental.difficulty.configuration.model_identity', return_value='fixture'):
            old = self.config()
            old.difficulty.dynamic_filter.eligibility = 'reward_variance'
            prepare_config(old)
            origin = provenance(old)
            meta = {'initial_model_id': 'fixture', 'step': 0, 'provenance': origin}
            # 完整配置只改变资格与恢复类型，确保失败来自训练指纹变化。
            for mode in ['continue', 'branch']:
                new = copy.deepcopy(old)
                new.difficulty.dynamic_filter.eligibility = 'task_success_mixed'
                new.difficulty.resume = str(parent)
                new.difficulty.resume_mode = mode
                with patch('verl.experimental.difficulty.configuration.read_checkpoint', return_value=meta):
                    with self.assertRaisesRegex(ValueError, 'Parent reference/model/training/retrieval provenance'):
                        prepare_config(new)


if __name__ == '__main__':
    unittest.main()
