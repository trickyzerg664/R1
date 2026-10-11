"""有界过程奖励CPU核验，使用真实解析/执行/评分入口。"""
from copy import deepcopy
import io
from contextlib import redirect_stdout
import unittest
import numpy as np
import torch
from verl.experimental.process_checks.protocol import TraceLedger
from verl.experimental.process_checks.reward import check_config, process_reward_components
from verl.experimental.process_checks.bounded_reward import bounded_reward
from verl.experimental.difficulty.configuration import provenance
from verl.trainer.main_ppo import RewardManager
from tests.test_process_checks import execute
from tests.test_trajectory_logging import sample_record
from tests.test_reward_boundary import Tokenizer, batch
from verl.utils.trajectory_logging import render_trajectory
from omegaconf import OmegaConf
from unittest.mock import patch
import tempfile
from pathlib import Path

CONFIG = dict(enabled=True,reward_gate=True,missing_answer_penalty=.1,
              reward_variant='bounded_invalid_v1',invalid_action_penalty=.02,process_penalty_cap=.12)

def report_with_retry(finish='stop', repeats=1, answer='Paris'):
    """@brief 经真实账本构造拒绝动作后正常回答，附程序原生终止夹具。
    @param finish 无效轮原生终止，stop/length/None。
    @param repeats 无效轮次数，正整数。
    @param answer 最终答案，None表示最终未作答。
    @return 真实程序报告，终止元数据为CPU夹具而非真实GPU结果。
    """
    ledger=TraceLedger(1)
    # 仅原生stop可计新增惩罚，最终正常回答不计入无效动作。
    for turn in range(repeats):execute(ledger,['<think>need evidence</think>'],turn=turn)
    if answer is not None:execute(ledger,['<answer>'+answer+'</answer>'],turn=repeats)
    report=ledger.reports()[0]
    report['token_diagnostics']=[dict(finish_reason=finish) for _ in range(repeats)]
    if answer is not None:report['token_diagnostics'].append(dict(finish_reason='stop'))
    return report

class BoundedRewardTests(unittest.TestCase):
    def components(self, report, em=1., config=None):
        """@brief 在原可信门控后调用新奖励模块，复用既有成功标签。
        @param report 真实CPU报告。
        @param em 接受答案EM，0或1。
        @param config 可选过程配置。
        @return 有界奖励分量。
        """
        config=check_config(config or CONFIG)
        base=process_reward_components(report,report['trace_uid'],em,.1)
        return bounded_reward(report,base,config)

    def test_complete_invalid_retry_soft_penalty(self):
        """@brief 完整无效动作后答对只扣.02，成功标签保持true。
        @return 无。
        """
        report=report_with_retry();before=deepcopy(report);result=self.components(report)
        self.assertEqual(result['protocol_reward'],1.)
        self.assertAlmostEqual(result['training_reward'],.98)
        self.assertEqual(result['invalid_action_count'],1)
        self.assertTrue(result['task_success']);self.assertEqual(report,before)

    def test_length_unknown_and_normal_answer_not_penalized(self):
        """@brief 长度截断、未知终止和正常完成答案均免新增惩罚。
        @return 无。
        """
        for finish in ('length',None,'abort'):
            result=self.components(report_with_retry(finish))
            self.assertEqual(result['training_reward'],1.)
            self.assertEqual(result['invalid_action_count'],0)
        self.assertEqual(self.components(report_with_retry(repeats=0))['training_reward'],1.)

    def test_counts_and_total_cost_bounded(self):
        """@brief 多次明确无效动作成本最多.04，缺答案合计成本最多.12。
        @return 无。
        """
        result=self.components(report_with_retry(repeats=5))
        self.assertAlmostEqual(result['training_reward'],.96)
        missing=self.components(report_with_retry(repeats=5,answer=None),em=0.)
        self.assertAlmostEqual(missing['training_reward'],-.12)

    def test_unknown_metadata_and_identity_mismatch(self):
        """@brief 无元数据不猜测违规，事件数或原来源身份错误必须失败。
        @return 无。
        """
        report=report_with_retry();del report['token_diagnostics']
        self.assertEqual(self.components(report)['training_reward'],1.)
        report['token_diagnostics']=[]
        with self.assertRaisesRegex(ValueError,'Termination records'):self.components(report)
        report=report_with_retry()
        with self.assertRaises(ValueError):process_reward_components(report,'wrong_uid',1.,.1)

    def test_legacy_exact_compatibility_and_invalid_config(self):
        """@brief 未启用新奖励时原字典和值不变，非法系数和门控显式拒绝。
        @return 无。
        """
        report=report_with_retry();base=process_reward_components(report,report['trace_uid'],1.,.1)
        self.assertEqual(bounded_reward(report,base,check_config(dict(enabled=True,reward_gate=True,missing_answer_penalty=.1))),base)
        for update in (dict(reward_variant='typo'),dict(invalid_action_penalty=-.02),
                       dict(process_penalty_cap=.2),dict(reward_gate=False),
                       dict(invalid_action_penalty=float('nan'))):
            with self.subTest(update=update),self.assertRaises(ValueError):check_config(dict(CONFIG,**update))

    def test_real_training_and_validation_rewards(self):
        """@brief 真实RewardManager训练返回.98，验证保持原EM1，日志明确新旧奖励。
        @return 无。
        """
        report=report_with_retry();data=batch('<answer>Paris</answer>')
        data.non_tensor_batch['process_checks']=np.array([report],dtype=object)
        data.non_tensor_batch['process_trace_uid']=np.array([report['trace_uid']],dtype=object)
        output=io.StringIO()
        with redirect_stdout(output):
            training=RewardManager(Tokenizer(),0,answer_mode='response_only_v1',process_checks=CONFIG,
                                   trajectory_logging={'enabled':True})(deepcopy(data))
            validation=RewardManager(Tokenizer(),0,answer_mode='response_only_v1',process_checks=CONFIG,
                                     apply_process_reward=False)(deepcopy(data))
        self.assertAlmostEqual(training.sum().item(),.98,places=6)
        self.assertEqual(validation.sum().item(),1.)
        self.assertIn('训练候选奖励=0.98',output.getvalue())

    def test_group_advantage_signs_under_worst_costs(self):
        """@brief G8成功/失败混合组，在.12成本边界下成功优势正、失败优势负。
        @return 无。
        """
        for k in range(1,8):
            values=torch.tensor([.88]*k+[0.]*(8-k));advantages=(values-values.mean())/(values.std()+1e-6)
            self.assertTrue(torch.all(advantages[:k]>0));self.assertTrue(torch.all(advantages[k:]<0))

    def test_normal_search_retry_and_unconsumed_tail_cost_zero(self):
        """@brief 合法多轮检索与答案后未消费尾部均免新增软罚。
        @return 无。
        """
        ledger=TraceLedger(1)
        # 正常探索允许多次搜索；本轮不启用循环惩罚。
        execute(ledger,['<search>query</search>'])
        execute(ledger,['<search>query</search>'],turn=1)
        execute(ledger,['<answer>Paris</answer><search>unused tail</search>'],turn=2)
        report=ledger.reports()[0]
        report['token_diagnostics']=[dict(finish_reason='stop') for _ in report['events']]
        result=self.components(report)
        self.assertEqual(result['training_reward'],1.)
        self.assertEqual(result['invalid_action_count'],0)

    def test_hard_gate_failure_stays_task_failure(self):
        """@brief 空动作后的正确答案不能绕过原严重违规门控。
        @return 无。
        """
        ledger=TraceLedger(1);execute(ledger,['<search> </search>'])
        execute(ledger,['<answer>Paris</answer>'],turn=1)
        report=ledger.reports()[0]
        report['token_diagnostics']=[dict(finish_reason='stop') for _ in report['events']]
        result=self.components(report)
        self.assertFalse(result['task_success'])
        self.assertAlmostEqual(result['training_reward'],-.02)

    def test_reward_variant_enters_restore_fingerprint(self):
        """@brief 新奖励规则改变恢复身份，旧缺省字段保持原指纹。
        @return 无。
        """
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'data';path.write_text('fixed')
            config=OmegaConf.load('verl/trainer/config/ppo_trainer.yaml')
            config.data.train_files=str(path);config.data.val_files=str(path)
            config.process_checks=dict(enabled=True,reward_gate=True,missing_answer_penalty=.1)
            with patch('verl.experimental.difficulty.configuration.model_identity',return_value='same'):
                base=provenance(config)
                config.process_checks=CONFIG
                self.assertNotEqual(base,provenance(config))
