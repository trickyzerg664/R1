"""CPU核验：真实生成/评分/筛选入口及可核查推理边界，不启动Ray或GPU。"""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
import torch
from verl import DataProto
from verl.protocol import pad_dataproto_to_divisor, unpad_dataproto
from verl.experimental.process_checks.protocol import TraceLedger, parse_action, validate_report
from verl.experimental.process_checks.reasoning import documents, review_reasoning, search_diagnostic
from verl.experimental.process_checks.reward import check_config, process_score, append_reports
from verl.experimental.difficulty.dynamic_filter import mixed_groups, take_rows, merge_groups
from verl.trainer.main_ppo import RewardManager
from search_r1.llm_agent.generation import LLMGenerationManager, GenerationConfig
from search_r1.llm_agent.context_budget import pad_token_rows
from tests.test_generation_budget import CharTokenizer
from tests.test_reward_boundary import batch


def execute(ledger, texts, turn=0, final=False, result='Doc 1(Title: A) Paris is a city.'):
    """
    @brief 经真实账本执行测试输出，同时记录模型实际可见观察。
    @param ledger 待检验的轨迹账本。
    @param texts 全批次原始输出，None表示已结束轨迹。
    @param turn 全局轮次。
    @param final 是否为禁止搜索的最终轮。
    @param result 模拟真实工具接口返回的内容，可为空检索结果。
    @return 工具接口收到的查询列表。
    """
    # 原始后处理与执行分别调用同一解析器，检查批次活动行对应关系。
    queries = []
    def search(items):
        """
        @brief 记录实际检索请求并返回等长工具结果。
        @param items 查询字符串列表。
        @return 等长观察字符串列表。
        """
        queries.extend(items)
        return [result for _ in items]
    active = [t is not None for t in texts]
    consumed = [parse_action(t)['consumed'] if t is not None else '' for t in texts]
    obs, _, _, _ = ledger.execute(consumed, active, [final]*len(texts), search, turn,
                                   [t for t in texts if t is not None])
    ledger.observe_visible(obs, turn)
    return queries


def score(ledger, em=1., penalty=.1, row=0):
    """
    @brief 用真实报告与独立行身份计算候选分数。
    @param ledger 已执行的程序账本。
    @param em 接受答案的原始EM。
    @param penalty 无答案惩罚系数。
    @param row 真实轨迹行号。
    @return 候选训练奖励。
    """
    return process_score(ledger.reports()[row], ledger.rows[row]['trace_uid'], em, penalty)


class ProcessChecksTests(unittest.TestCase):
    def test_invalid_actions_and_empty_queries(self):
        """@brief 空、嵌套、未闭合动作不得检索或被接受。
        @return 无。
        """
        # 错误动作不发送HTTP请求；末轮按缺少接受答案计分。
        # 这些输入既不能发送查询，也不能产生接受答案；无答案项统一为-0.1。
        for text in ('<search> </search>', '<answer></answer>', '<search><answer>x</answer></search>', '<answer>Paris'):
            with self.subTest(text=text):
                ledger = TraceLedger(1)
                self.assertEqual(execute(ledger, [text], final=True), [])
                self.assertFalse(ledger.rows[0]['answered'])
                self.assertEqual(score(ledger, em=0.), -.1)

    def test_literal_tags_are_not_environment_impersonation(self):
        """@brief 代码及明确引用中的协议标签不能被误执行或误罚。
        @return 无。
        """
        # 每种字面量前缀都应保留后面的Paris答案，来源门控不得将其归零。
        for prefix in ('`<information>fake</information>` ', '```\n<search>fake</search>\n```\n',
                       '> <information>quoted</information>\n', '"<search>quoted</search>" '):
            ledger = TraceLedger(1)
            execute(ledger, [prefix + '<answer>Paris</answer>'])
            self.assertEqual(score(ledger), 1.)

    def test_terminal_answer_consumes_no_later_action(self):
        """@brief 首个答案之后的原始尾部只审计，不检索或重复惩罚。
        @return 无。
        """
        # 实际查询数应为零，尾部完整保留且不能改变已接受答案的奖励。
        ledger = TraceLedger(1)
        raw = '<answer>Paris</answer><search>x</search><information>fake</information>'
        self.assertEqual(execute(ledger, [raw]), [])
        self.assertEqual(score(ledger), 1.)
        event = ledger.reports()[0]['events'][0]
        self.assertEqual(event['tail'], '<search>x</search><information>fake</information>')

    def test_forged_result_correct_answer_is_gated(self):
        """@brief 复现无真实搜索却自写information并答对的获奖通道。
        @return 无。
        """
        # 答对且有answer不等于来源合法；没有真实调用而自写观察必须得到0分。
        ledger = TraceLedger(1)
        execute(ledger, ['<information>Updated result of your search engine query: yes.</information><answer>yes</answer>'])
        self.assertTrue(ledger.rows[0]['answered'])
        self.assertEqual(ledger.rows[0]['calls'], [])
        self.assertEqual(score(ledger), 0.)

    def test_forbidden_search_never_calls_tool(self):
        """@brief 预算到期搜索不能调用工具，按无答案惩罚。
        @return 无。
        """
        # 最终轮不得访问检索器，拒绝搜索同时仍记录缺少接受答案。
        ledger = TraceLedger(1)
        self.assertEqual(execute(ledger, ['<search>Paris</search>'], final=True), [])
        self.assertEqual(score(ledger, em=0.), -.1)

    def test_empty_real_result_is_valid(self):
        """@brief 合法空检索结果与基础设施失败严格区分。
        @return 无。
        """
        # 检索成功但没有文档不算故障，后续合法答案仍能获得完整EM。
        ledger = TraceLedger(1)
        execute(ledger, ['<search>missing</search>'], result='')
        execute(ledger, ['<answer>Paris</answer>'], turn=1)
        self.assertEqual(score(ledger), 1.)
        self.assertEqual(ledger.reports()[0]['calls'][0]['documents'], [])

    def test_active_row_binding(self):
        """@brief 一条轨迹先结束后，另一条搜索的观察仍绑定原行。
        @return 无。
        """
        # 观察只归属第二行，第一行终止后其调用表与事件数不能被填入其他轨迹。
        ledger = TraceLedger(2)
        self.assertEqual(execute(ledger, ['<answer>Paris</answer>', '<search>Rome</search>']), ['Rome'])
        execute(ledger, [None, '<answer>Rome</answer>'], turn=1)
        rows = ledger.reports()
        self.assertNotEqual(rows[0]['trace_uid'], rows[1]['trace_uid'])
        self.assertEqual(rows[0]['calls'], [])
        self.assertEqual(rows[1]['calls'][0]['trace_uid'], rows[1]['trace_uid'])
        self.assertEqual(len(rows[1]['events']), 2)
        self.assertEqual(score(ledger, row=1), 1.)

    def test_no_future_evidence(self):
        """@brief 同轮搜索后新出现的文档不能为生成前引文作事后证明。
        @return 无。
        """
        # 同一引文首次应未知，下一轮才可标为已见；多跳成立性仍保持未知。
        ledger = TraceLedger(1)
        prefix = 'Doc 1 says "Paris is a city." Therefore the location is established. '
        execute(ledger, [prefix + '<search>Paris</search>'])
        execute(ledger, [prefix + '<answer>Paris</answer>'], turn=1)
        events = ledger.reports()[0]['events']
        self.assertEqual(events[0]['reasoning']['quote_checks'][0]['status'], 'unverified')
        self.assertEqual(events[1]['reasoning']['quote_checks'][0]['status'], 'exact_present')
        self.assertEqual(events[1]['reasoning']['multi_hop_checks'][0]['status'], 'unknown')

    def test_truncated_evidence_not_full_return(self):
        """@brief 不可见工具正文不算引文支持，引用文档包含调用身份。
        @return 无。
        """
        # 工具全文有该句但模型未见，所以引文状态只能未知，不能借全文作证明。
        ledger = TraceLedger(1)
        execute(ledger, ['<search>q</search>'], result='Doc 1(Title: A) hidden sentence is here.')
        ledger.observe_visible(['<information>Doc 1(Title: A) shown sentence</information>'], 0)
        execute(ledger, ['Doc 1 says "hidden sentence is here." <answer>Paris</answer>'], turn=1)
        report = ledger.reports()[0]
        self.assertEqual(report['events'][1]['reasoning']['quote_checks'][0]['status'], 'unverified')
        refs = report['events'][1]['reasoning']['citation_checks'][0]['references']
        self.assertEqual(refs[0]['call_id'], report['calls'][0]['call_id'])
        self.assertEqual(score(ledger), 1.)

    def test_repeated_query_and_new_evidence_separated(self):
        """@brief 重复查询返回新文档不判冗余，重复也不会直接扣分。
        @return 无。
        """
        # 重复但有新正文只标重复，不标冗余；同正文重复则给诊断候选。
        old = documents('Doc 1(Title: A) old body', 'old')
        previous = [dict(query='a b c', documents=old)]
        same = search_diagnostic(' A B C ', old, previous)
        new = search_diagnostic('a b c', documents('Doc 1(Title: B) new body', 'new'), previous)
        self.assertTrue(same['redundant_search_candidate'])
        self.assertTrue(new['repeated_query'])
        self.assertEqual(new['new_documents'], 1)
        self.assertFalse(new['redundant_search_candidate'])

    def test_semantics_conflict_and_hops_remain_unknown(self):
        """@brief 字面引文不替代语义判定，数值冲突与多跳只给复核候选。
        @return 无。
        """
        # 数字不一致只给冲突候选，关键词连贯不代表事实或推理已核实。
        evidence = documents('Doc 1(Title: A) The population was 100.\nDoc 2(Title: B) The population was 200.', 'c')
        reviewed = review_reasoning('Therefore the population is correct.', evidence)
        self.assertEqual(reviewed['semantic_review_status'], 'requires_review')
        self.assertEqual(reviewed['multi_hop_checks'][0]['status'], 'unknown')
        self.assertEqual(reviewed['conflict_candidates'][0]['status'], 'unknown')

    def test_infrastructure_exception_is_not_model_penalty(self):
        """@brief 检索异常传播并保留账本，失败批次不能变成模型负分。
        @return 无。
        """
        # 服务错误必须向上抛出并保存error身份；失败批次评分要拒绝。
        def fail(queries):
            """
            @brief 模拟检索基础设施不可用。
            @param queries 当前实际查询列表。
            @return 无。
            @raises OSError 模拟连接失败。
            """
            raise OSError('unavailable')
        ledger = TraceLedger(1)
        with self.assertRaises(OSError):
            ledger.execute(['<search>q</search>'], [True], [False], fail, 0)
        self.assertEqual(ledger.reports()[0]['calls'][0]['status'], 'error')
        with self.assertRaises(ValueError):
            score(ledger, em=0.)

    def test_result_count_mismatch_stops_batch(self):
        """@brief 工具返回数量错配不得评分或绑定其他行结果。
        @return 无。
        """
        # 一个请求收到零条返回属于接口故障，不得补成模型的空检索或负奖励。
        ledger = TraceLedger(1)
        def empty(queries):
            """
            @brief 模拟检索接口返回数量错误。
            @param queries 当前查询列表。
            @return 空列表，与实际调用数量不符。
            """
            return []
        with self.assertRaises(ValueError):
            ledger.execute(['<search>q</search>'], [True], [False], empty, 0)
        with self.assertRaises(ValueError):
            score(ledger, em=0.)

    def test_parse_mismatch_stops_batch(self):
        """@brief 后处理与执行消费边界不同必须显式停止。
        @return 无。
        """
        # 原始Paris与消费Rome不一致时必须停止，不能为任一答案发奖。
        ledger = TraceLedger(1)
        with self.assertRaises(ValueError):
            ledger.execute(['<answer>Rome</answer>'], [True], [False], None, 0, ['<answer>Paris</answer>'])

    def test_report_tampering_and_uid_mismatch(self):
        """@brief 同行身份、调用参数及可见证据篡改均被拒绝。
        @return 无。
        """
        # 分别改变查询、可见正文、原返回后评分要失败；换行身份也要失败。
        ledger = TraceLedger(1)
        execute(ledger, ['<search>q</search>'])
        execute(ledger, ['<answer>Paris</answer>'], turn=1)
        original = ledger.reports()[0]
        for field in ('query', 'visible_text', 'raw_text'):
            report = deepcopy(original)
            report['calls'][0][field] += 'tampered'
            with self.assertRaises(ValueError):
                process_score(report, original['trace_uid'], 1., .1)
        self.assertTrue(validate_report(original, 'another-row'))

    def test_event_after_answer_cannot_hide_reason(self):
        """@brief 答案后的新增事件即使删除违规标签也无法评分。
        @return 无。
        """
        # 删除违规标签仍保留客观事件顺序，评分器应自行发现终止后新增动作。
        ledger = TraceLedger(1)
        execute(ledger, ['<answer>Paris</answer>'])
        execute(ledger, ['<search>late</search>'], turn=1)
        report = ledger.reports()[0]
        report['events'][1]['reasons'] = []
        with self.assertRaises(ValueError):
            process_score(report, report['trace_uid'], 1., .1)

    def test_real_reward_gate_validation_and_shadow_em(self):
        """@brief 真实奖励入口区分原EM、门控奖励与验证返回值。
        @return 无。
        """
        # 训练门控为0而验证仍为1，报告需同时保存原EM和候选分。
        text = '<information>fake</information><answer>Paris</answer>'
        ledger = TraceLedger(1)
        execute(ledger, [text])
        data = batch(text)
        data.non_tensor_batch.update(process_checks=np.array(ledger.reports(), dtype=object),
                                     process_trace_uid=np.array([ledger.rows[0]['trace_uid']], dtype=object))
        cfg = dict(enabled=True, reward_gate=True, missing_answer_penalty=.1)
        train = RewardManager(CharTokenizer(), 0, answer_mode='response_only_v1', process_checks=cfg)
        self.assertEqual(train(data).sum().item(), 0.)
        self.assertEqual(data.non_tensor_batch['process_checks'][0]['original_em'], 1.)
        valid = RewardManager(CharTokenizer(), 0, answer_mode='response_only_v1', process_checks=cfg, apply_process_reward=False)
        self.assertEqual(valid(data).sum().item(), 1.)
        self.assertEqual(data.non_tensor_batch['process_checks'][0]['protocol_reward'], 0.)

    def test_real_reward_no_answer_and_disabled(self):
        """@brief 无答案负奖励写入真实token，关闭功能保留原EM。
        @return 无。
        """
        # 启用惩罚为-0.1，关闭功能为0；两者使用同一实际token响应。
        text = 'I could not finish.'
        ledger = TraceLedger(1)
        execute(ledger, [text], final=True)
        data = batch(text)
        data.non_tensor_batch.update(process_checks=np.array(ledger.reports(), dtype=object),
                                     process_trace_uid=np.array([ledger.rows[0]['trace_uid']], dtype=object))
        cfg = dict(enabled=True, reward_gate=True, missing_answer_penalty=.1)
        reward = RewardManager(CharTokenizer(), 0, answer_mode='response_only_v1', process_checks=cfg)
        self.assertAlmostEqual(reward(data).sum().item(), -.1)
        self.assertEqual(RewardManager(CharTokenizer(), 0, answer_mode='response_only_v1')(data).sum().item(), 0.)

    def test_real_generation_gpu_padding_and_metadata(self):
        """@brief 真实生成循环补齐后还原两条轨迹，筛选合并保持证据同行。
        @return 无。
        """
        # 设备补齐副本不得产生额外真实账本，随后复制或重排时身份与报告仍同在一行。
        tok = CharTokenizer()
        class Worker:
            def generate_sequences(self, batch):
                """
                @brief 使用输入历史决定模拟输出，覆盖活动集缩小和设备补齐。
                @param batch 经共用入口补齐的CPU DataProto。
                @return 生成响应DataProto。
                """
                replies = ['<answer>Paris</answer>' if text.startswith('FIRST') or '<information>' in text
                           else '<search>capital</search>' for text in tok.batch_decode(batch.batch['input_ids'])]
                return DataProto.from_dict({'responses': pad_token_rows([tok.encode(t) for t in replies], 0)})
        class Manager(LLMGenerationManager):
            def batch_search(self, queries):
                """
                @brief 按真实批次调用提供固定检索内容。
                @param queries 实际发送的查询列表。
                @return 等长结果列表。
                """
                return ['Doc 1(Title: A) Paris is a city.' for _ in queries]
        config = GenerationConfig(2, 64, 900, 128, 250, 3, observation_truncation='structured',
                                  context_policy='bounded', process_checks_enabled=True)
        manager = Manager(tok, Worker(), config)
        ids = pad_token_rows([tok.encode('FIRST'), tok.encode('SECOND')], 0, 'left')
        mask = (ids != 0).long()
        data = DataProto.from_dict({'input_ids': ids, 'attention_mask': mask, 'position_ids': (mask.cumsum(-1)-1)*mask})
        generated = manager.run_llm_loop(data, ids)
        self.assertEqual(len(generated.non_tensor_batch['process_checks']), 2)
        self.assertEqual(len(generated.non_tensor_batch['process_checks'][0]['calls']), 0)
        self.assertEqual(len(generated.non_tensor_batch['process_checks'][1]['calls']), 1)
        # 使用真实DataProto补齐、重复、重排、筛选及合并实现检验行级元数据。
        padded, count = pad_dataproto_to_divisor(generated, 3)
        restored = unpad_dataproto(padded, count)
        restored.reorder(torch.tensor([1, 0]))
        merged = merge_groups([take_rows(restored, [0]), take_rows(restored, [1])], 0)
        # 原DataProto.repeat不展开批级统计；真实流程先展开问题再生成，单独核查报告复制。
        repeated = merged.repeat(2, interleave=True)
        repeated.reorder(torch.tensor([3, 0, 2, 1]))
        for report, uid in zip(repeated.non_tensor_batch['process_checks'], repeated.non_tensor_batch['process_trace_uid']):
            self.assertEqual(validate_report(report, uid), [])
        self.assertEqual(score_from_report(generated.non_tensor_batch['process_checks'][1]), 1.)
        # 覆盖独立最终轮路径：未搜索的末轮search被拒绝，不能误报为合法停止。
        config.max_turns = 0
        terminal = manager.run_llm_loop(data, ids)
        report = terminal.non_tensor_batch['process_checks'][1]
        self.assertEqual(report['calls'], [])
        self.assertTrue(report['missing_answer'])
        self.assertEqual(process_score(report, report['trace_uid'], 0., .1), -.1)

    def test_finite_group_filter_and_constant_groups(self):
        """@brief 实数模式只保留有差异的完整组，二值模式原规则保持。
        @return 无。
        """
        # 全错但奖励有差异可保留，全同分负组丢弃；NaN和残组必须拒绝。
        def group(values):
            """
            @brief 构造完整同题组供真实筛选入口验收。
            @param values 每轨迹有限奖励列表。
            @return DataProto组。
            """
            n = len(values)
            return DataProto.from_dict({'dynamic_rewards': torch.tensor(values).reshape(n, 1)},
                                       non_tensors={'uid': np.array(['u']*n), 'question_id': np.array(['q']*n)})
        self.assertEqual(mixed_groups(group([0., -.1]), 2, reward_mode='finite')[0], [[0, 1]])
        self.assertEqual(mixed_groups(group([-.1, -.1]), 2, reward_mode='finite')[0], [])
        self.assertEqual(mixed_groups(group([0., 0.]), 2, reward_mode='finite')[0], [])
        self.assertEqual(mixed_groups(group([1., 0.]), 2)[0], [[0, 1]])
        with self.assertRaises(ValueError): mixed_groups(group([0., -.1]), 2)
        with self.assertRaises(ValueError): mixed_groups(group([0., float('nan')]), 2, reward_mode='finite')
        with self.assertRaises(ValueError): mixed_groups(group([0., 1.]), 3)

    def test_configuration_fails_before_reward_changes(self):
        """@brief 不完整开关、非法惩罚及旧上下文配置拒绝启用。
        @return 无。
        """
        # 各类错误开关都应在评分或生成前失败，防止以字符串真值误启用。
        for cfg in ({'reward_gate': True}, {'enabled': True, 'missing_answer_penalty': .1},
                    {'enabled': 'false'}, {'missing_answer_penalty': float('nan')}, {'missing_answer_penalty': -.1}):
            with self.assertRaises(ValueError): check_config(cfg)
        with self.assertRaises(ValueError):
            LLMGenerationManager(CharTokenizer(), None, GenerationConfig(2, 64, 900, 128, 250, 1, process_checks_enabled=True))
        with self.assertRaises(ValueError):
            RewardManager(CharTokenizer(), 0, process_checks={'enabled': True})

    def test_difficulty_metrics_keep_original_em(self):
        """@brief 真实难度统计入口接受负奖励，原正确数与方差分别汇报。
        @return 无。
        """
        # 原正确率全部为0但过程奖励组有差异，这两种有效组比例不得混记。
        from types import SimpleNamespace
        from verl.experimental.difficulty.controller import DifficultyExperiment
        controller = SimpleNamespace(group_size=2, sampler=SimpleNamespace(exposures=np.array([1, 1])))
        reports = np.array([dict(original_em=0., protocol_valid=True, missing_answer=False),
                            dict(original_em=0., protocol_valid=True, missing_answer=True)], dtype=object)
        data = DataProto.from_dict({'token_level_scores': torch.tensor([[0.], [-.1]]),
                                    'responses': torch.ones(2, 1, dtype=torch.long),
                                    'attention_mask': torch.ones(2, 2, dtype=torch.long)},
                                   non_tensors={'uid': np.array(['u', 'u']), 'process_checks': reports})
        metrics = DifficultyExperiment.metrics(controller, data)
        self.assertEqual(metrics['difficulty/k0'], 1.)
        self.assertEqual(metrics['difficulty/effective_fraction'], 0.)
        self.assertEqual(metrics['process/effective_fraction'], 1.)
        self.assertAlmostEqual(metrics['process/reward_mean'], -.05)
        self.assertEqual(metrics['process/missing_answer_fraction'], .5)

    def test_process_protocol_enters_resume_fingerprint(self):
        """@brief 关闭检查保持旧指纹；解析或奖励改变拒绝混用，审计路径可迁移。
        @return 无。
        """
        # 关闭保持旧来源身份，协议和惩罚变化产生新指纹，单改保存地址不产生新身份。
        from unittest.mock import patch
        from omegaconf import OmegaConf
        from verl.experimental.difficulty.configuration import provenance
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'dataset'
            path.write_text('test data')
            config = OmegaConf.load('verl/trainer/config/ppo_trainer.yaml')
            config.data.train_files = str(path)
            config.data.val_files = str(path)
            # 仅隔离模型大文件身份IO；真正配置解析和指纹计算不替换。
            with patch('verl.experimental.difficulty.configuration.model_identity', return_value='fixed-reference'):
                disabled = provenance(config)
                del config.process_checks
                self.assertEqual(provenance(config), disabled)
                config.process_checks = dict(enabled=True, reward_gate=False, missing_answer_penalty=0., audit_path=None)
                audited = provenance(config)
                self.assertNotEqual(audited['training'], disabled['training'])
                config.process_checks.audit_path = 'different-location.jsonl'
                self.assertEqual(provenance(config), audited)
                config.process_checks.reward_gate = True
                gated = provenance(config)
                self.assertNotEqual(gated['training'], audited['training'])
                config.process_checks.missing_answer_penalty = .1
                self.assertNotEqual(provenance(config)['training'], gated['training'])

    def test_scoring_labels_remain_binary_with_penalty(self):
        """@brief 真实难度打标入口保存四个原EM，负奖励与来源报告旁列。
        @return 无。
        """
        from verl.experimental.difficulty.generation import score_batch
        tok = CharTokenizer()
        class SearchWorker:
            def generate_sequences(self, batch):
                """
                @brief 模拟最终轮仍尝试搜索，核查打标中的无答案负奖励。
                @param batch 原生成接口CPU批次。
                @return 固定搜索输出DataProto。
                """
                return DataProto.from_dict({'responses': pad_token_rows([tok.encode('<search>q</search>')]*len(batch), 0)})
        ids = torch.tensor(tok.encode('QUESTION'))
        dataset = [dict(input_ids=ids, attention_mask=torch.ones_like(ids), position_ids=torch.arange(len(ids)),
                        question_id='q', data_source='nq', reward_model={'ground_truth': {'target': ['Paris']}})]
        cfg = GenerationConfig(0, 64, 900, 128, 250, 1, observation_truncation='structured',
                               context_policy='bounded', process_checks_enabled=True)
        manager = LLMGenerationManager(tok, SearchWorker(), cfg)
        reward = RewardManager(tok, 0, answer_mode='response_only_v1',
                               process_checks=dict(enabled=True, reward_gate=True, missing_answer_penalty=.1))
        records = score_batch(dataset, [0], [[1, 2, 3, 4]], manager, reward, 64)
        # 四个原EM均为0，过程奖励为-0.1；标签不能因负奖励被拒绝或强转成正确数。
        self.assertEqual(records[0]['rewards'], [0.]*4)
        self.assertTrue(all(abs(r+.1) < 1e-6 for r in records[0]['process_rewards']))
        self.assertTrue(all(r['missing_answer'] for r in records[0]['process_checks']))

    def test_contraction_does_not_hide_action(self):
        """@brief 英文缩写的撇号不能跨越实际答案标签形成伪引用。
        @return 无。
        """
        raw = "I don't need a search. <answer>Paris</answer> That's the answer."
        ledger = TraceLedger(1)
        execute(ledger, [raw])
        # 答案之前与尾部各有一个撇号，仍须在第一个闭合answer处消费并结束。
        self.assertTrue(ledger.rows[0]['answered'])
        self.assertEqual(score(ledger), 1.)
        self.assertEqual(ledger.reports()[0]['events'][0]['tail'], " That's the answer.")
        # 单轮在search结束即停止时也会遇到两个缩写，不能漏掉实际查询。
        searching = TraceLedger(1)
        raw_search = "I don't know. <search>What's the capital of France?</search>"
        self.assertEqual(execute(searching, [raw_search]), ["What's the capital of France?"])
        # 真正成对引号内的缩写仍属字面量，不应把引用中的information判为伪造。
        literal = "'<information>don't execute this</information>' <answer>Paris</answer>"
        quoted = TraceLedger(1)
        execute(quoted, [literal])
        self.assertEqual(score(quoted), 1.)

    def test_real_fit_keeps_fractional_reward_and_advantages(self):
        """@brief 真实fit控制流不能把负小数奖励截成整数或丢掉GRPO优势。
        @return 无。
        """
        from types import SimpleNamespace
        from unittest.mock import Mock, patch
        from omegaconf import OmegaConf
        from verl.trainer.ppo.ray_trainer import RayPPOTrainer
        config = OmegaConf.load('verl/trainer/config/ppo_trainer.yaml')
        config.algorithm.adv_estimator = 'grpo'
        config.actor_rollout_ref.actor.use_kl_loss = True
        config.actor_rollout_ref.rollout.n_agent = 2
        config.trainer.n_gpus_per_node = 1
        config.trainer.save_freq = config.trainer.test_freq = -1
        tensors = {'prompts': torch.ones(4, 2), 'responses': torch.ones(4, 1),
                   'input_ids': torch.ones(4, 3), 'attention_mask': torch.ones(4, 3),
                   'info_mask': torch.ones(4, 3), 'position_ids': torch.zeros(4, 3),
                   'old_log_probs': torch.full((4, 1), -.25),
                   'dynamic_rewards': torch.tensor([[0.], [-.1], [0.], [-.1]])}
        data = DataProto.from_dict(tensors, non_tensors={'uid': np.array(['a', 'a', 'b', 'b'])},
                                  meta_info={'dynamic_timing': {'gen': 0., 'step': 0.}})
        trainer = RayPPOTrainer.__new__(RayPPOTrainer)
        trainer.config = config
        trainer.tokenizer = CharTokenizer()
        trainer.total_training_steps = 1
        trainer.logger = SimpleNamespace(log=Mock())
        trainer.val_reward_fn = None
        # 筛选阶段已经评分，本次更新必须消费同行候选分，不能再算一次掩盖截断。
        trainer.reward_fn = Mock(side_effect=AssertionError('Candidate rewards must not be recomputed'))
        trainer.train_dataloader = []
        trainer.use_reference_policy = trainer.use_critic = trainer.use_rm = False
        trainer.difficulty = SimpleNamespace(dynamic=True, max_candidate_rounds=1,
                                             metrics=Mock(return_value={}), after_step=Mock())
        trainer.actor_rollout_wg = SimpleNamespace(update_actor=Mock(return_value=DataProto(meta_info={'metrics': {}})))
        # 只替换候选批获取和GPU worker；真实fit、dtype处理、优势与损失掩码完整执行。
        with patch('verl.experimental.difficulty.dynamic_filter.training_batches', return_value=iter([data])), \
             patch.object(trainer, '_balance_batch'), patch.object(trainer, '_save_difficulty'):
            trainer.fit()
        # 验收实际进入actor的数据：奖励保留-0.1，概率保留小数，token为整数，优势符号按组排序。
        captured = trainer.actor_rollout_wg.update_actor.call_args.args[0]
        torch.testing.assert_close(captured.batch['token_level_scores'].sum(-1), torch.tensor([0., -.1, 0., -.1]))
        torch.testing.assert_close(captured.batch['old_log_probs'], torch.full((4, 1), -.25))
        self.assertEqual(captured.batch['input_ids'].dtype, torch.long)
        self.assertTrue(bool((captured.batch['advantages'][[0, 2]] > 0).all()))
        self.assertTrue(bool((captured.batch['advantages'][[1, 3]] < 0).all()))

    def test_jsonl_audit_preserves_originals(self):
        """@brief 审计阶段和原始模型尾部以JSONL完整保存。
        @return 无。
        """
        # JSONL需保留generation阶段及原始尾部，供后续复核消费边界。
        ledger = TraceLedger(1)
        execute(ledger, ['<answer>Paris</answer>trailing'])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'audit.jsonl'
            append_reports(path, ledger.reports(), 'generation')
            rows = [json.loads(t) for t in path.read_text(encoding='utf-8').splitlines()]
            self.assertEqual(rows[0]['phase'], 'generation')
            self.assertTrue(rows[0]['report']['events'][0]['raw'].endswith('trailing'))


def score_from_report(report):
    """
    @brief 验证真实生成入口产生的报告可以直接评分。
    @param report 原生成报告。
    @return 接受答案EM为1时的候选奖励。
    """
    return process_score(report, report['trace_uid'], 1., .1)


if __name__ == '__main__':
    unittest.main()
