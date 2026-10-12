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
from verl.utils.trajectory_logging import HumanTrajectoryLogger, display_text, render_trajectory, render_search_result
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
        self.assertLess(text.index('[连续轨迹结束]'),text.index('[答案与奖励判定]'))
        tags='<think>first\nsecond</think><answer>Paris</answer>'
        self.assertEqual(display_text(display_text(tags,500),500),display_text(tags,500))

    def test_newlines_controls_and_auxiliary_budget(self):
        """@brief 清理控制字符，旧预算只限制诊断，完整生成与奖励均保留。
        @return 无。
        """
        shown = display_text('第一行\r\n第二行\\n字面量\x1b[31m红色\x00', 200)
        self.assertIn('第一行\n第二行\\n字面量', shown)
        self.assertNotIn('\x1b', shown); self.assertNotIn('\x00', shown)
        record = sample_record(); history = '想' * 30000 + '<answer>FINAL_ANSWER</answer>'
        record.update(prompt='问' * 30000, model_response=history, full_response=history)
        text = render_trajectory(record, 2000)
        # 提示可以缩略，连续模型轨迹不得被旧2000预算截掉。
        self.assertIn(display_text(history, None), text)
        self.assertIn('展示截断', text); self.assertIn('[答案与奖励判定]', text)
        self.assertIn('本次实际返回规则奖励=1', text); self.assertIn('[轨迹结束]', text)

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

    def test_continuous_long_model_output_and_deferred_diagnostics(self):
        """@brief 多轮超长模型输出必须完整，诊断和未消费尾部只能出现在轨迹之后。
        @return 无。
        """
        ledger = TraceLedger(1)
        first = '<think>THINK_A' + '甲' * 16000 + 'END_A</think><search>first query</search>'
        second = '<think>THINK_B' + '乙' * 16000 + 'END_B</think><answer>Paris</answer>'
        execute(ledger, [first], result='Doc 1(Title: A) ' + '证据' * 10000)
        execute(ledger, [second + '<search>UNCONSUMED_TAIL</search>'], turn=1)
        report = ledger.reports()[0]
        report.update(accepted_answer_em=1., protocol_reward=1., original_em=1., returned_reward=1.)
        record = sample_record(report); before = deepcopy(record)
        text = render_trajectory(record, 2000, 400)
        # 用每轮完整格式化文本校验，不能只检查首尾哨兵而遗漏中间思考。
        self.assertIn(display_text(first, None), text)
        self.assertIn(display_text(second, None), text)
        chain = text.split('[连续轨迹：', 1)[1].split('[连续轨迹结束]', 1)[0]
        self.assertLess(chain.index('END_A'), chain.index('搜索结果省略'))
        self.assertLess(chain.index('搜索结果省略'), chain.index('THINK_B'))
        self.assertNotIn('实际执行=', chain); self.assertNotIn('UNCONSUMED_TAIL', chain)
        self.assertGreater(text.index('UNCONSUMED_TAIL'), text.index('[答案与奖励判定]'))
        self.assertIn('[过程诊断：不属于模型输出]', text); self.assertEqual(record, before)

    def test_search_abbreviation_boundaries_and_full_option(self):
        """@brief 搜索正文只缩略真实观察，保留首尾、信息标签及准确省略数量。
        @return 无。
        """
        source = '<information>HEAD' + 'x' * 1000 + 'TAIL</information>'
        shown = render_search_result(source, 200)
        # 正文1008字符，保留200，省略说明的字符不占正文预算。
        self.assertIn('省略 808 字符', shown)
        self.assertTrue(shown.startswith('<information>\nHEAD'))
        self.assertTrue(shown.endswith('TAIL\n</information>'))
        self.assertEqual(render_search_result(source, 0), display_text(source, None))
        self.assertEqual(render_search_result('<information>short</information>', 200),
                         display_text('<information>short</information>', None))
        for limit in (-1, 1, 199, True, '200'):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                render_search_result(source, limit)

    def test_model_information_tag_never_abbreviated(self):
        """@brief 模型自己写的伪观察即使很长也应完整展示，不能当工具返回省略。
        @return 无。
        """
        raw = '<information>MODEL_FAKE' + 'z' * 18000 + '</information><answer>Paris</answer>'
        ledger = TraceLedger(1); execute(ledger, [raw])
        report = ledger.reports()[0]
        report.update(accepted_answer_em=1., protocol_reward=0., original_em=1., returned_reward=0.)
        text = render_trajectory(sample_record(report), 2000, 200)
        # 保留错误生成本身用于退化分析；没有真实call_id便不会缩略。
        self.assertIn(display_text(raw, None), text); self.assertNotIn('搜索结果省略', text)

    def test_no_ledger_history_displayed_once(self):
        """@brief 无账本时完整历史只输出一次，缺失历史则回退到模型输出。
        @return 无。
        """
        record = sample_record()
        history = '<think>ONLY_ONCE' + 'h' * 20000 + '</think><answer>Paris</answer>'
        record.update(model_response=history, full_response=history)
        text = render_trajectory(record, 2000, 200)
        self.assertEqual(text.count('ONLY_ONCE'), 1); self.assertIn(display_text(history, None), text)
        # 无来源身份时不可缩略information，避免把模型文本误当工具结果。
        record['full_response'] = '<information>' + 'ENV_UNKNOWN' * 300 + '</information>' + history
        self.assertIn(display_text(record['full_response'], None), render_trajectory(record, 2000))
        for missing in (None, ''):
            record['full_response'] = missing
            self.assertIn(display_text(history, None), render_trajectory(record, 2000))

    def test_unanswered_trace_not_fabricated(self):
        """@brief 缺答案轨迹连续保留真实输出，明确结束状态且不补造答案。
        @return 无。
        """
        ledger = TraceLedger(1); execute(ledger, ['<think>still thinking</think>'], final=True)
        report = ledger.reports()[0]
        report.update(accepted_answer_em=0., protocol_reward=-.1, original_em=0., returned_reward=-.1)
        record = sample_record(report); record.update(original_em=0., returned_reward=-.1, scoring_text='')
        text = render_trajectory(record)
        chain = text.split('[连续轨迹：', 1)[1].split('[连续轨迹结束]', 1)[0]
        self.assertIn('still thinking', chain); self.assertIn('未接受最终回答', chain)
        self.assertNotIn('<answer>', chain); self.assertIn('本次实际返回规则奖励=-0.1', text)

    def test_console_and_file_each_receive_complete_single_block(self):
        """@brief 控制台和文件得到同一完整块，模型长输出不受旧预算限制。
        @return 无。
        """
        record = sample_record(); history = '<think>' + 'q' * 15000 + '</think><answer>Paris</answer>'
        record.update(full_response=history, model_response=history)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'trajectory.log'
            logger = HumanTrajectoryLogger(dict(enabled=True, file_path=str(path),
                max_chars_per_trajectory=2000, search_result_max_chars=0))
            logger.begin_batch(); output = io.StringIO()
            # 本条仅一次print，避免logger自身逐轮打印穿插其他轨迹。
            with patch('builtins.print', wraps=print) as printer, redirect_stdout(output):
                logger.emit('nq', record)
            self.assertEqual(printer.call_count, 1)
            self.assertEqual(output.getvalue(), path.read_text())
            self.assertIn(display_text(history, None), output.getvalue())

    def test_tag_whitespace_layout_matches_previous_output(self):
        """@brief 验证普通和交错空白排版与旧输出完全一致。
        @return 无。
        """
        import re
        # 旧正则仅用于短字符串兼容性对照，避免测试本身触发长空白回溯。
        pattern = r'[ \t]*\n*[ \t]*(</?(?:think|search|answer|information)>)[ \t]*\n*[ \t]*'
        spaces = ['', ' ', '\t', '\n', ' \n ', '\n \n', ' \n \n ', '\u00a0']
        for left in spaces:
            for right in spaces:
                # 覆盖相邻标签、标签间正文、所有控制标签及未闭合标签。
                for core in ['<think></think>', '<answer>Paris</answer>',
                             '<search>x</search><information>y</information>',
                             '<think>text<answer']:
                    raw = 'HEAD' + left + core + right + 'TAIL'
                    expected = re.sub(pattern, r'\n\1\n', raw).strip()
                    with self.subTest(left=left, right=right, core=core):
                        self.assertEqual(display_text(raw, None), expected)

    def test_long_whitespace_formatting_timeout(self):
        """@brief 在有超时保护的子进程中核验长空白和完整尾部轨迹不会卡死。
        @return 无。
        @note 超时只终止本测试子进程，不影响训练或测试主进程。
        """
        import subprocess
        import sys
        # 子进程防止将来的性能回归挂住整套测试；无需GPU或真实模型生成。
        script = r"""
from copy import deepcopy
import time
from verl.utils.trajectory_logging import display_text, render_trajectory
# 从依赖导入后计时，避免把冷启动误判为日志性能退化。
started = time.perf_counter()
# 覆盖此次30336空白，以及更大输入、交错换行和无法闭合的标签。
assert display_text(' ' * 30336, 800) == ''
assert display_text(' ' * 100000, None) == ''
assert display_text((' \t\n' * 40000) + 'END', None).endswith('END')
assert display_text('HEAD' + (' ' * 100000) + '<answer', None).endswith('<answer')
assert display_text(' ' * 100000 + '<answer>Paris</answer>' + ' ' * 100000, None) == '<answer>\nParis\n</answer>'
# 完整展示报告只用于日志测试，不模拟评分或运行真实模型。
report = dict(trace_uid='render-test', calls=[], answered=True, protocol_valid=True,
              missing_answer=False, reasons=[], answer='Paris', accepted_answer_em=1.,
              protocol_reward=1., events=[dict(turn=0, consumed='<answer>Paris</answer>',
              tail=' ' * 30336, accepted=True, executed='answer')])
record = dict(prompt='question', model_response='<answer>Paris</answer>',
              full_response='<answer>Paris</answer>', scoring_text='<answer>Paris</answer>',
              target=['Paris'], data_source='nq', row=0, question_id='q', uid='g',
              meta={'trajectory_step':1}, phase='train', batch_number=1,
              answer_mode='response_only_v1', original_em=1., returned_reward=1.,
              format_score=0., process_report=report, reward_gate=True, penalty=.1,
              apply_process_reward=True)
# 验证原输入、奖励说明和完整结束标记，防止修复用截断掩盖问题。
before = deepcopy(record)
text = render_trajectory(record)
assert record == before
assert '<answer>\nParis\n</answer>' in text
assert '本次实际返回规则奖励=1' in text and '[轨迹结束]' in text
# 长空白和完整轨迹排版合计限5秒；总进程另有冷启动超时保护。
assert time.perf_counter() - started < 5.0
print('long-whitespace-ok')
"""
        # 总预算含依赖冷启动，实际格式化另限5秒；超时只终止测试子进程。
        result = subprocess.run([sys.executable, '-c', script], cwd=Path(__file__).resolve().parents[1],
                                capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('long-whitespace-ok', result.stdout)

    def test_invalid_configuration_rejected(self):
        """@brief 非法展示配置启动时失败，避免隐式真值或无界预算。
        @return 无。
        """
        # 非法真值、负限额、零频率与空路径均在启动时显式拒绝。
        for config in [dict(enabled='False'),dict(every_n_batches=0),dict(console_samples_per_source=-1),
                       dict(max_chars_per_trajectory=100),dict(file_path=''),
                       dict(search_result_max_chars=199),dict(search_result_max_chars=-1),
                       dict(search_result_max_chars=True),dict(search_result_max_chars='1000')]:
            with self.subTest(config=config),self.assertRaises(ValueError):HumanTrajectoryLogger(config)


if __name__=='__main__':
    unittest.main()
