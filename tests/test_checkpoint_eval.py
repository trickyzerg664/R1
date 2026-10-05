"""CPU边界验收：选题隔离、续跑前缀、标签风险和配对统计的真实约束。"""
import unittest
from unittest.mock import Mock, call
from verl.experimental.checkpoint_eval.runtime import ObservedRollout
from verl.experimental.checkpoint_eval.core import label_flags, paired_compare, process_features, select_rows, summarize, validate_prefix


class CheckpointEvaluationTests(unittest.TestCase):
    """不模拟GPU成功；只验收能够独立判断的CPU算法边界。"""

    def test_cache_reset_before_unmodified_delegation(self):
        """@brief 验证每轮先清空缓存，再原样委托生成且返回原对象。\n@return 无。"""
        events = Mock()
        events.reset.return_value = True
        engine = Mock()
        events.attach_mock(engine.generate_sequences, 'generate')
        prompts = object()
        wrapper = ObservedRollout(engine, None, events.reset)
        result = wrapper.generate_sequences(prompts)
        self.assertIs(result, engine.generate_sequences.return_value)
        self.assertEqual(events.mock_calls, [call.reset(), call.generate(prompts)])

    def test_cache_failure_prevents_generation(self):
        """@brief 缓存清空失败必须停止，不能将不同比较条件下的输出计入曲线。\n@return 无。"""
        engine = Mock()
        wrapper = ObservedRollout(engine, None, Mock(return_value=False))
        # 基础设施前置条件失败时，没有生成请求，也没有已完成答案。
        with self.assertRaises(RuntimeError):
            wrapper.generate_sequences(object())
        engine.generate_sequences.assert_not_called()

    def row(self, identity, reward, source='nq', text='<answer>x</answer>'):
        """
        @brief 构造不含模型依赖的标准评价记录。
        @param identity 测试题ID。
        @param reward 二值正确性。
        @param source 测试来源。
        @param text 模型生成的标签文本。
        @return 单题记录。
        """
        return {'question_id': identity, 'reward': reward, 'target': ['x'], 'data_source': source,
                'extracted_answer': 'x', 'features': process_features(text), 'actual_search_queries': 2}

    def test_selection_stable_and_disjoint(self):
        """@brief 验证原始顺序改变不影响选择，排除题与来源配额正确。\n@return 无。"""
        rows = [{'question_id': str(i), 'source': 'nq' if i < 5 else 'hotpotqa'} for i in range(10)]
        a = select_rows(rows, {'0', '5'}, {'nq': 2, 'hotpotqa': 3}, 42)
        b = select_rows(list(reversed(rows)), {'0', '5'}, {'nq': 2, 'hotpotqa': 3}, 42)
        self.assertEqual(a, b)
        self.assertFalse({'0', '5'} & {x['question_id'] for x in a})
        self.assertEqual([x['source'] for x in a].count('hotpotqa'), 3)

    def test_selection_rejects_duplicates_and_shortage(self):
        """@brief 验证重复ID和不足配额不能默默生成缩小题集。\n@return 无。"""
        rows = [{'question_id': 'x', 'source': 'nq'}]
        # 重复ID必须拒绝，不能将重复题用于填满来源配额。
        with self.assertRaises(ValueError):
            select_rows(rows * 2, set(), {'nq': 1}, 42)
        # 剩余题数不足时必须失败，不能静默缩小开发集。
        with self.assertRaises(ValueError):
            select_rows(rows, set(), {'nq': 2}, 42)

    def test_resume_prefix_rejects_gap_duplicate_and_nonbinary(self):
        """@brief 验证缺题、乱序、重复题或异常奖励不能通过续跑验收。\n@return 无。"""
        validate_prefix([self.row('a', 1)], ['a', 'b'])
        # 分别构造乱序、重复和非二值奖励，任何一种都不能恢复。
        for records in ([self.row('b', 0)], [self.row('a', 1)] * 2, [self.row('a', 2)]):
            # 每个坏前缀都独立触发校验异常。
            with self.assertRaises(ValueError):
                validate_prefix(records, ['a', 'b'])

    def test_process_diagnostics_do_not_count_fake_information_as_search(self):
        """@brief 区分虚构information、嵌套答案和重复查询，诊断不改变答案奖励。\n@return 无。"""
        value = process_features('<think><information>x</information><search>A  B</search><search>a b</search><answer>x</answer>')
        self.assertTrue(value['model_information'])
        self.assertTrue(value['format_anomaly'])
        self.assertTrue(value['nested_answer'])
        self.assertEqual(value['exact_repeat_queries'], 1)
        self.assertEqual(value['search_tag_count'], 2)

    def test_label_risks_frozen_before_outputs(self):
        """@brief 验证结构风险不读取模型输出，空标签不能进入开发集。\n@return 无。"""
        self.assertTrue(label_flags({'question': 'Who invented this and when?', 'target': ['A', '1817']}))
        self.assertTrue(label_flags({'question': 'What is the most recent movie?', 'target': ['A']}))
        self.assertFalse(label_flags({'question': 'Who won Wimbledon in 2017?', 'target': ['A']}))
        # 结构风险筛查不能容忍完全没有可接受答案的题目。
        with self.assertRaises(ValueError):
            label_flags({'question': 'Q', 'target': []})

    def test_summary_preserves_actual_cost_and_risk_denominator(self):
        """@brief 验证风险排除的分母、来源分组和真实调用成本按实际记录计算。\n@return 无。"""
        rows = [self.row('a', 1), self.row('b', 0, 'hotpotqa')]
        self.assertEqual(summarize(rows)['actual_search_queries'], 4)
        subset = summarize(rows, ['b'])
        self.assertEqual((subset['n'], subset['correct'], subset['em']), (1, 1, 1.))

    def test_pairing_rejects_changed_gold_and_missing_ids(self):
        """@brief 验证配对统计拒绝改标签和漏题，避免比较不可比评价。\n@return 无。"""
        a, b = [self.row('a', 0)], [self.row('a', 1)]
        b[0]['target'] = ['different']
        # 同ID改标注会改变正确率定义，必须拒绝配对。
        with self.assertRaises(ValueError):
            paired_compare(a, b)
        # 后模型少题不能只用交集计算，避免丢失失败问题。
        with self.assertRaises(ValueError):
            paired_compare(a, [])

    def test_paired_changes_and_reproducible_bootstrap(self):
        """@brief 验证同题改善/退步与配对区间可复现，零变化对应p=1。\n@return 无。"""
        a = [self.row('a', 0), self.row('b', 1), self.row('c', 1)]
        b = [self.row('a', 1), self.row('b', 0), self.row('c', 1)]
        result = paired_compare(a, b, draws=200)
        self.assertEqual((result['improves'], result['regresses'], result['delta']), (1, 1, 0.))
        self.assertEqual(result, paired_compare(a, b, draws=200))
        self.assertEqual(paired_compare(a, a, draws=200)['mcnemar_p_uncorrected'], 1.)


# 直接执行只运行CPU验收，不初始化GPU评价入口。
if __name__ == '__main__':
    unittest.main()
