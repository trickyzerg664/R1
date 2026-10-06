"""CPU核验：展示、奖励不变、随机流、逐轮来源以及日志故障隔离。"""
from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
import io
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import torch
from verl.experimental.process_checks.protocol import TraceLedger, parse_action
from verl.trainer.main_ppo import RewardManager
from verl.utils.trajectory_logging import HumanTrajectoryLogger, display_text, render_trajectory
from tests.test_process_checks import execute
from tests.test_reward_boundary import Tokenizer, batch


def process_data(raw, target='Paris', final=False):
    """@brief 用真实账本构造同行过程报告，覆盖伪观察和缺答案。
    @param raw 模型原始输出字符串。
    @param target 标准答案字符串。
    @param final 是否只允许答案。
    @return 带真实过程身份的单轨迹DataProto。
    """
    # 来源和答案状态都由真实执行器产生，不直接伪造报告字段。
    ledger=TraceLedger(1)
    execute(ledger,[raw],final=final)
    data=batch(parse_action(raw)['consumed'],target)
    data.non_tensor_batch['process_checks']=np.array(ledger.reports(),dtype=object)
    data.non_tensor_batch['process_trace_uid']=np.array([ledger.rows[0]['trace_uid']],dtype=object)
    return data


def sample_record(report=None):
    """@brief 构造展示字典，采用已算出的分数而非模拟另一套评分器。
    @param report 可选真实过程报告。
    @return 普通日志输入字典。
    """
    # 该材料仅用于排版，数值来源验证另走真实RewardManager入口。
    return dict(prompt='问题：法国首都是哪里？',model_response='<think>先找证据。</think><answer>Paris</answer>',
                full_response='<information>环境文本</information><answer>Paris</answer>',
                scoring_text='<answer>Paris</answer>',target=['Paris'],data_source='nq',row=0,
                question_id='q1',uid='group1',meta={'trajectory_step':40},phase='train',batch_number=1,
                answer_mode='response_only_v1',original_em=1.,returned_reward=1.,format_score=0.,
                process_report=report,reward_gate=True,penalty=.1,apply_process_reward=True)


class TrajectoryLoggingTests(unittest.TestCase):
    def test_rewards_rng_and_input_unchanged(self):
        """@brief 日志开关不得改变真实奖励、Python随机状态或原始输入张量。
        @return 无。
        """
        # 同一批分别关闭/开启日志，检查旧模式、纯EM及过程门控三条真实路径。
        cases=[('legacy',None,batch('<answer>Paris</answer>')),
               ('response_only_v1',None,batch('<answer>Rome</answer>')),
               ('response_only_v1',dict(enabled=True,reward_gate=True,missing_answer_penalty=.1),
                process_data('<information>fake</information><answer>Paris</answer>')),
               ('response_only_v1',dict(enabled=True,reward_gate=True,missing_answer_penalty=.1),
                process_data('<search>capital</search>',final=True))]
        for mode,config,source in cases:
            baseline,logged=deepcopy(source),deepcopy(source)
            before={k:v.clone() for k,v in logged.batch.items()}
            random.seed(123);expected=RewardManager(Tokenizer(),0,answer_mode=mode,process_checks=config)(baseline)
            state=random.getstate()
            random.seed(123)
            with redirect_stdout(io.StringIO()):
                actual=RewardManager(Tokenizer(),0,answer_mode=mode,process_checks=config,
                    trajectory_logging={'enabled':True})(logged)
            self.assertTrue(torch.equal(expected,actual))
            self.assertEqual(state,random.getstate())
            for key,value in before.items():self.assertTrue(torch.equal(value,logged.batch[key]))
            self.assertEqual(baseline.non_tensor_batch.get('process_checks',[]).tolist() if config else [],
                             logged.non_tensor_batch.get('process_checks',[]).tolist() if config else [])

    def test_forged_observation_reward_explained(self):
        """@brief 正确答案的伪观察应明确展示原EM1、门控失败和实际0分。
        @return 无。
        """
        # 经真实评分入口获取分项，不能用假字段掩盖候选与返回奖励的区别。
        # 真实奖励入口应将伪观察的原EM1门控为0，并展示同一结论。
        output=io.StringIO();data=process_data('<information>fake</information><answer>Paris</answer>')
        with redirect_stdout(output):
            result=RewardManager(Tokenizer(),0,answer_mode='response_only_v1',
                process_checks=dict(enabled=True,reward_gate=True,missing_answer_penalty=.1),
                trajectory_logging={'enabled':True})(data)
        text=output.getvalue()
        self.assertIn('原始答案分（EM规则）=1',text)
        self.assertIn('来源 / 动作门控：失败',text)
        self.assertIn('模型冒充工具观察',text)
        self.assertIn('候选过程奖励=0 = 1 × 0 - 0.1 × 0',text)
        self.assertIn('本次实际返回规则奖励=0',text)
        self.assertEqual(result.sum().item(),0.)

    def test_validation_keeps_original_score(self):
        """@brief 验证日志应区分候选过程0分与实际返回原EM1。
        @return 无。
        """
        # 验证保持原EM，日志必须同时说明候选0分和实际1分。
        data=process_data('<information>fake</information><answer>Paris</answer>');output=io.StringIO()
        with redirect_stdout(output):
            score=RewardManager(Tokenizer(),0,answer_mode='response_only_v1',apply_process_reward=False,
                process_checks=dict(enabled=True,reward_gate=True,missing_answer_penalty=.1),
                trajectory_logging={'enabled':True})(data)
        self.assertEqual(score.sum().item(),1.)
        self.assertIn('阶段=validation',output.getvalue())
        self.assertIn('候选过程奖励=0',output.getvalue())
        self.assertIn('保留原始答案分',output.getvalue())
        self.assertIn('本次实际返回规则奖励=1',output.getvalue())

    def test_missing_answer_negative_reward(self):
        """@brief 未作答惩罚必须按浮点分项展示，不被格式化成0。
        @return 无。
        """
        # 最终轮未接受答案时，真实浮点负奖励及展示值必须一致。
        data=process_data('<search>capital</search>',final=True);output=io.StringIO()
        with redirect_stdout(output):
            score=RewardManager(Tokenizer(),0,answer_mode='response_only_v1',
                process_checks=dict(enabled=True,reward_gate=True,missing_answer_penalty=.1),
                trajectory_logging={'enabled':True})(data)
        self.assertAlmostEqual(score.sum().item(),-.1,places=6)
        self.assertIn('无答案=1',output.getvalue())
        self.assertIn('本次实际返回规则奖励=-0.1',output.getvalue())

    def test_real_turns_visible_evidence_and_tail(self):
        """@brief 展示真实搜索、可见结果与未执行尾部，不能混入不可见证据。
        @return 无。
        """
        ledger=TraceLedger(1)
        execute(ledger,['<think>先搜索。</think><search>capital France</search>'],
                result='Doc 1(Title: City) Paris is a city. HIDDEN')
        # 实际裁剪后的可见观察替代完整工具返回，后续日志只展示模型看见的内容。
        ledger.observe_visible(['<information>Doc 1(Title: City) Paris is a city.</information>'],0)
        execute(ledger,['<answer>Paris</answer><search>unused</search>'],turn=1)
        report=ledger.reports()[0]
        report.update(accepted_answer_em=1.,protocol_reward=1.,original_em=1.,returned_reward=1.)
        record=sample_record(report);before=deepcopy(record);text=render_trajectory(record)
        self.assertIn('[第 1 轮',text);self.assertIn('[第 2 轮',text)
        self.assertIn('[真实工具调用]',text);self.assertIn('capital France',text)
        self.assertNotIn('HIDDEN',text);self.assertIn('未执行尾部',text)
        self.assertEqual(record,before)
        # 反复展示不应倍增标签空行，奖励块与推理段之间必须保留清楚边界。
        self.assertIn('不计入奖励。\n\n[答案与奖励判定]',text)
        tags='<think>first\nsecond</think><answer>Paris</answer>'
        self.assertEqual(display_text(display_text(tags,500),500),display_text(tags,500))

    def test_newlines_controls_and_length_budget(self):
        """@brief 真实换行保留、字面量转义不误改，长文本不能吞掉奖励总结。
        @return 无。
        """
        # 终端控制字符只在显示副本中去除，字面量反斜线n保留原样。
        shown=display_text('第一行\r\n第二行\\n字面量\x1b[31m红色\x00',200)
        self.assertIn('第一行\n第二行\\n字面量',shown)
        self.assertNotIn('\x1b',shown);self.assertNotIn('\x00',shown)
        record=sample_record();record.update(prompt='问'*30000,model_response='想'*30000,full_response='答'*30000)
        text=render_trajectory(record,2000)
        self.assertLessEqual(len(text),2000)
        self.assertIn('展示截断',text);self.assertIn('[答案与奖励判定]',text)
        self.assertIn('本次实际返回规则奖励=1',text)
        # 奖励总结自身很长时也遵守总预算，实际返回分和结束边界不能丢失。
        report={'trace_uid':'trace','events':[],'calls':[],'protocol_valid':True,'missing_answer':False,
                'reasons':[],'answer':'x'*10000,'accepted_answer_em':1.,'protocol_reward':1.}
        record.update(process_report=report,target=['x'*10000],scoring_text='<answer>'+'x'*10000+'</answer>')
        text=render_trajectory(record,2000)
        self.assertLessEqual(len(text),2000)
        self.assertIn('本次实际返回规则奖励=1',text);self.assertIn('[轨迹结束]',text)

    def test_deterministic_limits_and_batch_frequency(self):
        """@brief 每来源样例和批次频率独立限制，不消费随机数。
        @return 无。
        """
        # 第1和3批展示，第2批跳过；每来源独立限额，随机状态不变。
        logger=HumanTrajectoryLogger(dict(enabled=True,console_samples_per_source=1,every_n_batches=2))
        output=io.StringIO();state=random.getstate()
        with redirect_stdout(output):
            logger.begin_batch();logger.emit('nq',sample_record());logger.emit('nq',sample_record())
            logger.emit('hotpotqa',sample_record());logger.begin_batch();logger.emit('nq',sample_record())
            logger.begin_batch();logger.emit('nq',sample_record())
        self.assertEqual(output.getvalue().count('[轨迹开始]'),3)
        self.assertEqual(state,random.getstate())

    def test_file_all_rows_and_console_failure_independent(self):
        """@brief 控制台失败不能中断文件输出，文件可配置选中批次全量轨迹。
        @return 无。
        """
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'human.log';logger=HumanTrajectoryLogger(dict(enabled=True,file_path=str(path)))
            logger.begin_batch()
            # 模拟真实输出接口抛错，另一目的地仍须保留两条完整日志。
            with patch('builtins.print',side_effect=OSError('stdout unavailable')):
                logger.emit('nq',sample_record());logger.emit('nq',sample_record())
            self.assertEqual(path.read_text().count('[轨迹开始]'),2)
            self.assertTrue(logger.warned)

    def test_reward_survives_file_and_formatter_failures(self):
        """@brief 文件写入或展示格式化异常时，真实奖励仍正常返回。
        @return 无。
        """
        # 文件路径指向目录或格式化器抛错，都只能丢失展示而不能改变奖励。
        with tempfile.TemporaryDirectory() as tmp:
            reward=RewardManager(Tokenizer(),0,answer_mode='response_only_v1',
                trajectory_logging=dict(enabled=True,file_path=tmp,console_samples_per_source=0))
            with redirect_stderr(io.StringIO()):
                self.assertEqual(reward(batch('<answer>Paris</answer>')).sum().item(),1.)
            self.assertTrue(reward.human_logger.warned)
        reward=RewardManager(Tokenizer(),0,answer_mode='response_only_v1',trajectory_logging={'enabled':True})
        with patch('verl.utils.trajectory_logging.render_trajectory',side_effect=ValueError('format failure')), redirect_stderr(io.StringIO()):
            self.assertEqual(reward(batch('<answer>Paris</answer>')).sum().item(),1.)

    def test_display_decode_failure_preserves_reward(self):
        """@brief 仅展示用的额外解码失败时，真实奖励仍返回。
        @return 无。
        """
        class DisplayFailTokenizer(Tokenizer):
            def decode(self, ids, **kwargs):
                """@brief 仅拒绝单独初始提示的展示解码，保留原评分解码。
                @param ids 输入字符token序列。
                @param kwargs 兼容分词器额外参数。
                @return 原字符解码文本。
                @raises ValueError 仅展示提示的额外解码请求。
                """
                # 原评分解码为提示加回答及模型回答，只有新增展示单独解码提示。
                if len(ids)==len(batch('<answer>Paris</answer>').batch['prompts'][0]):
                    raise ValueError('display decode failure')
                return super().decode(ids,**kwargs)
        # 仅额外展示解码失败，已完成的EM评分仍须正常返回并限量提示。
        reward=RewardManager(DisplayFailTokenizer(),0,answer_mode='response_only_v1',trajectory_logging={'enabled':True})
        with redirect_stderr(io.StringIO()):
            self.assertEqual(reward(batch('<answer>Paris</answer>')).sum().item(),1.)
        self.assertTrue(reward.human_logger.warned)

    def test_invalid_configuration_rejected(self):
        """@brief 非法展示配置启动时失败，避免隐式真值或无界预算。
        @return 无。
        """
        # 非法真值、负限额、零频率与空路径均在启动时显式拒绝。
        for config in [dict(enabled='False'),dict(every_n_batches=0),dict(console_samples_per_source=-1),
                       dict(max_chars_per_trajectory=100),dict(file_path='')]:
            with self.subTest(config=config),self.assertRaises(ValueError):HumanTrajectoryLogger(config)


if __name__=='__main__':
    unittest.main()
