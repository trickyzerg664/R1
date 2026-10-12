"""重复奖励及G8三至六次正确筛选回归；真实协议、评分、GRPO路径，无模型加载。"""
import copy
import io
from contextlib import redirect_stdout
import unittest
from unittest.mock import patch
import numpy as np
import torch
from verl.experimental.process_checks.protocol import TraceLedger
from verl.experimental.process_checks.reward import check_config
from verl.experimental.process_checks.repetition import (
    repetition_config, repeated_coverage, inspect_turn, QUALITY_SUCCESS_VERSION, REPETITION_VERSION)
from verl.experimental.difficulty.eligibility import normalize_dynamic_filter, task_success_labels
from verl.experimental.difficulty.dynamic_filter import mixed_groups, training_batches
from verl.experimental.difficulty.configuration import prepare_config, provenance
from verl.trainer.main_ppo import RewardManager
from verl.trainer.ppo.core_algos import compute_grpo_outcome_advantage
from tests.test_process_checks import execute
from tests.test_reward_boundary import batch
from tests.test_generation_budget import CharTokenizer
from tests.test_task_success_filter import group_batch, TaskManager
import tests.test_task_success_filter as task_helpers
from tests.test_dynamic_filter import Worker
from verl.utils.dataset.rl_dataset import collate_fn
from torch.utils.data import DataLoader
from tests.test_dynamic_filter import Dataset

CONFIG = dict(enabled=True, reward_gate=True, missing_answer_penalty=.1,
              reward_variant='bounded_invalid_v1', invalid_action_penalty=.02,
              process_penalty_cap=.12, repetition=dict(enabled=True))


def reward_data(prefix='', tail='', observation=''):
    """@brief 构造两轮真实协议报告与评分文本，尾部及工具内容独立保存。
    @param prefix 答案之前的模型消费内容，可含重复。
    @param tail 最终答案后的未执行内容。
    @param observation 合法工具观察内容，独立于模型消费事件。
    @return 带同行过程身份的完整 DataProto。
    """
    ledger = TraceLedger(1)
    # 首轮可缺动作模拟长度截断；所有奖励来自实际接受的末轮答案。
    if observation:
        execute(ledger, ['<search>capital</search>'], result=observation)
        body = '<search>capital</search>'
    else:
        execute(ledger, [prefix or '<think>Reason once.</think>'])
        body = prefix or '<think>Reason once.</think>'
    execute(ledger, ['<answer>Paris</answer>' + tail], turn=1)
    report = ledger.reports()[0]
    report['token_diagnostics'] = [dict(finish_reason='length'), dict(finish_reason='stop')]
    data = batch(body + '<answer>Paris</answer>', environment=observation)
    data.non_tensor_batch['process_checks'] = np.array([report], dtype=object)
    data.non_tensor_batch['process_trace_uid'] = np.array([report['trace_uid']], dtype=object)
    return data


class RepetitionTests(unittest.TestCase):
    def inspect(self, text, settings=None, initial=False):
        """@brief 使用共用字符 tokenizer 检验结构规则，不加载模型。
        @param text 一轮模型文字。
        @param settings 可选阈值更新。
        @param initial 提示是否已打开 think。
        @return 检测报告。
        """
        return inspect_turn(text, lambda s: CharTokenizer().encode(s, add_special_tokens=False),
                            repetition_config(settings), initial)

    def score(self, data, apply=True, enabled=True):
        """@brief 调用正式奖励入口，分别测试训练、验证和关闭兼容。
        @param data 真实过程 DataProto。
        @param apply 是否应用过程奖励。
        @param enabled 是否启用新重复规则。
        @return 总奖励及已写回的报告。
        """
        config = copy.deepcopy(CONFIG)
        config['repetition']['enabled'] = enabled
        with redirect_stdout(io.StringIO()):
            value = RewardManager(CharTokenizer(), 0, answer_mode='response_only_v1',
                process_checks=config, apply_process_reward=apply,
                trajectory_logging={'enabled':False})(data).sum().item()
        return value, data.non_tensor_batch['process_checks'][0]

    def test_ngram_nonoverlap_union_and_first_occurrence(self):
        """@brief 独立位置 oracle 校验首份豁免、三次不触发、跨n去重与界限。
        @return 无。
        """
        # 用唯一分隔符隔离四份，只有完全相同的四token片段可命中。
        tokens = []
        for i in range(4):
            tokens.extend([1,2,3,4,100+i])
        self.assertEqual(repeated_coverage(tokens), 12/20)
        self.assertEqual(repeated_coverage([1,2,3,4]*3), 0.)
        self.assertLessEqual(repeated_coverage([1]*256), 1.)
        self.assertEqual(repeated_coverage([]), 0.)

    def test_short_tag_loop_and_unclosed_single(self):
        """@brief 标签循环突破正文最短限制，单次未闭合及合法分段不罚。
        @return 无。
        """
        for text in ('<think>'*4, '<think></think>'*2,
                     '<think>x<think>x<think>x<think>x'):
            self.assertEqual(self.inspect(text)['level'], 'severe')
        for text in ('<think>Reason once', '<think>Reason once.</think><answer>Paris</answer>',
                     '<think>A.</think><think>B.</think>'):
            self.assertEqual(self.inspect(text)['level'], 'normal')
        self.assertEqual(self.inspect('<think>Again')['level'], 'normal')
        self.assertEqual(self.inspect('<think>Again', initial=True)['level'], 'mild')

    def test_literal_tags_and_long_legitimate_reasoning(self):
        """@brief 引用和代码标签不算结构循环，正常长文本不误罚。
        @return 无。
        """
        for text in ('```<think><think><think><think>```',
                     '`<think><think><think><think>`',
                     '"<think><think><think><think>"',
                     '> <think><think><think><think>'):
            self.assertEqual(self.inspect(text)['duplicate_think_opens'], 0)
            self.assertLess(self.inspect(text)['tag_run'], 4)
        # 每个字符只出现一次，独立验证最短长度以上也不会自动触发。
        self.assertEqual(self.inspect(''.join(chr(0x4e00+i) for i in range(128)))['level'], 'normal')

    def test_mild_and_severe_ratio_boundaries(self):
        """@brief 固定token oracle 检查比例边界、软罚与重度门控。
        @return 无。
        """
        settings = repetition_config({})
        # 隔离比例计算检查边界，算法的实际重复位置由另一测试独立验证。
        for ratio, level, cost in ((.149,'normal',0.),(.275,'mild',.05),(.4,'severe',.12)):
            with patch('verl.experimental.process_checks.repetition.repeated_coverage', return_value=ratio):
                report = inspect_turn('unique', lambda s:list(range(100)), settings)
            self.assertEqual(report['level'], level)
            self.assertAlmostEqual(report['penalty'], cost)

    def test_real_reward_severe_correct_wrong_missing_and_validation(self):
        """@brief 真正答对的重复轨迹训练为-.12，验证原EM保持1，关闭规则仍为1。
        @return 无。
        """
        for text in ('lm '*256, '<think>'*8, '千方百计索'*100):
            data = reward_data(text)
            before = copy.deepcopy(data.non_tensor_batch['process_checks'][0]['events'])
            value, report = self.score(data)
            self.assertAlmostEqual(value, -.12, places=6)
            self.assertEqual(report['original_em'], 1.)
            self.assertEqual(report['accepted_answer_em'], 1.)
            self.assertFalse(report['task_success'])
            self.assertEqual(report['task_success_version'], QUALITY_SUCCESS_VERSION)
            self.assertEqual(report['events'], before)
            self.assertEqual(task_success_labels([report],[report['trace_uid']],1), [False])
            self.assertEqual(self.score(reward_data(text), apply=False)[0], 1.)
            self.assertEqual(self.score(reward_data(text), enabled=False)[0], 1.)
        # 错答与缺答案仍保持非正奖励，总成本不得超过原上限。
        for answer in ('Rome', ''):
            ledger = TraceLedger(1)
            execute(ledger, ['lm '*256])
            execute(ledger, ['<answer>'+answer+'</answer>'], turn=1)
            data = batch('lm '*256 + '<answer>'+answer+'</answer>')
            report = ledger.reports()[0]
            data.non_tensor_batch['process_checks'] = np.array([report], dtype=object)
            data.non_tensor_batch['process_trace_uid'] = np.array([report['trace_uid']], dtype=object)
            value, report = self.score(data)
            self.assertAlmostEqual(value, -.12, places=6)

    def test_observation_tail_and_per_turn_exclusion(self):
        """@brief 工具观察和未执行尾部重复不罚，合法多轮think不累计为循环。
        @return 无。
        """
        for data in (reward_data(tail='<think>'*100+'lm '*256),
                     reward_data(observation='lm '*256+'<think>'*100)):
            value, report = self.score(data)
            self.assertEqual(value, 1.)
            self.assertEqual(report['repetition_level'], 'normal')
        ledger = TraceLedger(1)
        for turn in range(5):
            execute(ledger, ['<think>A new query.</think><search>query</search>'], turn=turn)
        execute(ledger, ['<think>Now answer.</think><answer>Paris</answer>'], turn=5)
        report = ledger.reports()[0]
        data = batch(''.join(e['consumed'] for e in report['events']))
        data.non_tensor_batch['process_checks'] = np.array([report], dtype=object)
        data.non_tensor_batch['process_trace_uid'] = np.array([report['trace_uid']], dtype=object)
        self.assertEqual(self.score(data)[0], 1.)

    def test_config_validation_and_quality_label_tampering(self):
        """@brief 非法配置、伪造质量门控与错版标签均立即拒绝。
        @return 无。
        """
        for update in ({'enabled':'false'}, {'mild_ratio':.5}, {'severe_ratio':float('nan')},
                       {'tag_run':True}, {'min_tokens':0}, {'typo':1}, {'severe_penalty':0}):
            with self.assertRaises(ValueError):repetition_config(update)
        with self.assertRaises(ValueError):check_config(dict(CONFIG,reward_variant='legacy',invalid_action_penalty=0.))
        _, report = self.score(reward_data('<think>'*4))
        for key, value in (('quality_gate',True),('task_success',True),('repetition_version','bad'),
                           ('task_success_version','task_success_v1')):
            changed = dict(report, **{key:value})
            with self.assertRaises(ValueError):task_success_labels([changed],[changed['trace_uid']],1)

    def test_g8_range_all_nine_counts_and_severe_advantages(self):
        """@brief 穷举0–8次答对，仅3–6入选，重度正确轨迹为负GRPO优势。
        @return 无。
        """
        for k in range(9):
            data = group_batch([1.]*k+[0.]*(8-k),[True]*k+[False]*(8-k))
            groups, records = mixed_groups(data,8,reward_mode='finite',eligibility='answer_correct_3_6')
            self.assertEqual(bool(groups), 3 <= k <= 6)
            self.assertEqual(records[0]['answer_correct_k'], k)
            if groups:self.assertEqual(groups,[list(range(8))])
        data = group_batch([.88]*3+[-.12]+[0.]*4,[True]*3+[False]*5,
                           accepted=[1.]*4+[0.]*4)
        report = data.non_tensor_batch['process_checks'][3]
        report.update(answered=True, quality_gate=False, repetition_level='severe',
                      repetition_version=REPETITION_VERSION, task_success_version=QUALITY_SUCCESS_VERSION)
        groups, records = mixed_groups(data,8,reward_mode='finite',eligibility='answer_correct_3_6')
        self.assertEqual(len(groups),1)
        self.assertEqual(records[0]['answer_correct_k'],4)
        self.assertEqual(records[0]['task_success_k'],3)
        advantage, _ = compute_grpo_outcome_advantage(data.batch['dynamic_rewards'],
                          torch.ones_like(data.batch['dynamic_rewards']),['u']*8)
        self.assertLess(advantage[3].item(),0.)
        self.assertTrue(torch.all(advantage[:3]>0))
        # 答对次数满足但没有质量成功者，排除整组防止全劣质相对正奖。
        for i in range(3):
            data.non_tensor_batch['process_checks'][i].update(task_success=False,quality_gate=False,
                repetition_level='severe',repetition_version=REPETITION_VERSION,
                task_success_version=QUALITY_SUCCESS_VERSION)
        self.assertEqual(mixed_groups(data,8,reward_mode='finite',eligibility='answer_correct_3_6')[0],[])

    def test_g8_shape_identity_and_duplicate_question(self):
        """@brief 非G8、不完整组、重复身份、重复问题和缺报告不能回退旧筛选。
        @return 无。
        """
        data = group_batch([1.]*4+[0.]*4,[True]*4+[False]*4)
        with self.assertRaises(ValueError):mixed_groups(data,4,reward_mode='finite',eligibility='answer_correct_3_6')
        self.assertEqual(mixed_groups(data,8,seen={'q'},reward_mode='finite',eligibility='answer_correct_3_6')[0],[])
        for key in ('process_checks','process_trace_uid'):
            changed=copy.deepcopy(data);changed.non_tensor_batch.pop(key)
            with self.assertRaises(ValueError):mixed_groups(changed,8,reward_mode='finite',eligibility='answer_correct_3_6')
        self.assertNotEqual(normalize_dynamic_filter({'enabled':True,'eligibility':'task_success_mixed'}),
                            normalize_dynamic_filter({'enabled':True,'eligibility':'answer_correct_3_6'}))


class ConfigurationTests(unittest.TestCase):
    """继承既有配置/恢复夹具，新增入口指纹及完整补抽验证。"""
    setUp = task_helpers.TaskSuccessTests.setUp
    config = task_helpers.TaskSuccessTests.config
    controller = task_helpers.TaskSuccessTests.controller

    def test_new_config_and_restore_fingerprint(self):
        """@brief 新资格与重复各自改变指纹，显式关闭保持旧指纹。
        @return 无。
        """
        with patch('verl.experimental.difficulty.configuration.model_identity', return_value='fixture'):
            config = self.config();prepare_config(config);old=provenance(config)
            config.difficulty.dynamic_filter.eligibility='answer_correct_3_6'
            prepare_config(config);new=provenance(config)
            self.assertNotEqual(old['training'],new['training'])
            config.process_checks.repetition={'enabled':False}
            self.assertEqual(new,provenance(config))
            config.process_checks.reward_variant='bounded_invalid_v1'
            config.process_checks.invalid_action_penalty=.02
            before=provenance(config)
            config.process_checks.repetition={'enabled':True}
            self.assertNotEqual(before['training'],provenance(config)['training'])
            config.actor_rollout_ref.rollout.n_agent=4
            with self.assertRaisesRegex(ValueError,'exactly eight'):prepare_config(config)

    def test_changed_eligibility_rejects_resume_even_branch(self):
        """@brief 旧成功混合状态不能冒充3–6筛选续训，分支也必须拒绝。
        @return 无。
        """
        old = self.controller(name='old-mode')
        state = old.state_dict()
        current = self.controller(name='range-mode',mode='answer_correct_3_6')
        # 来源相同也不能绕过显式资格版本边界。
        for branch in (False,True):
            with self.assertRaisesRegex(ValueError,'eligibility differs'):
                current.load_state_dict(state,branch=branch,compatible_provenance=old.provenance)

    def test_real_complete_batch_with_new_filter_and_rewards(self):
        """@brief 完整补抽复用生产循环，8题各8轨迹且答对4次，质量标签同行绑定。
        @return 无。
        """
        controller = self.controller(mode='answer_correct_3_6')
        reward = RewardManager(CharTokenizer(),0,answer_mode='response_only_v1',process_checks=CONFIG,
                               trajectory_logging={'enabled':False})
        loader = DataLoader(Dataset(),batch_sampler=controller.sampler,collate_fn=collate_fn)
        # 共用repeat入口沿用原同题展开，循环独立生成不加载模型。
        from verl.trainer.ppo.ray_trainer import repeat_search_batch
        manager = TaskManager()
        with redirect_stdout(io.StringIO()):
            data = next(training_batches(loader,controller,manager,reward,repeat_search_batch,Worker(),0,1,4))
        self.assertEqual(len(data),64)
        records = data.non_tensor_batch['process_checks']
        self.assertEqual(sum(r['task_success'] for r in records),32)
        self.assertTrue(all(r['repetition_level']=='normal' for r in records))
        # 实际训练汇总复用原EM口径，新质量字段必须独立出现。
        data.batch['token_level_scores'] = data.batch['dynamic_rewards']
        metrics = controller.metrics(data)
        self.assertEqual(metrics['quality/severe_repetition_fraction'],0.)
        self.assertEqual(metrics['quality/task_success_fraction'],.5)
        self.assertEqual(metrics['difficulty/k4'],1.)


if __name__ == '__main__':
    unittest.main()
