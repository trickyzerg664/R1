"""验证原始 token 保留、人工边界掩码及融合算子的非连续标签。"""
import unittest
from unittest.mock import patch
import numpy as np
import torch
from verl import DataProto
from search_r1.llm_agent.token_alignment import preserve_sampled_prefix
from search_r1.llm_agent.generation import GenerationConfig, LLMGenerationManager
from verl.experimental.stability.generation_audit import token_alignment_report
from verl.utils import torch_functional as functional
from verl.workers.actor.dp_actor import token_statistics, response_loss_mask, DataParallelPPOActor
from omegaconf import OmegaConf
from tensordict import TensorDict
from test_generation_budget import CharTokenizer


class PieceTokenizer(CharTokenizer):
    """模拟同文字多种 token 表示及跨闭合边界的真实词表片段。"""
    pieces = {500: '>M', 501: '>\n\n', 502: '>TAIL', 503: '</answer>TAIL'}

    def encode(self, text, add_special_tokens=False):
        """@brief 规范编码会合并 >M，用于暴露整段重分词差异。
        @param text 待编码文本。
        @param add_special_tokens 是否附加特殊 token；测试保持关闭语义。
        @return 整数 token 列表。
        """
        # 只模拟一个已确认的 BPE 合并，其他文字沿用字符编号便于独立检查。
        ids, offset = [], 0
        while offset < len(text):
            if text.startswith('>M', offset):
                ids.append(500)
                offset += 2
            else:
                ids.append(ord(text[offset]))
                offset += 1
        return ids

    def decode(self, ids, **kwargs):
        """@brief 解码原始片段并忽略 pad，允许非规范 token 序列。
        @param ids 整数 token 序列。
        @param kwargs tokenizer 兼容参数，不改变此测试词表行为。
        @return 对应可见字符串。
        """
        # pad/EOS 沿用字符夹具的零编号；多字符 token 不会再拆分。
        return ''.join(self.pieces.get(int(i), chr(int(i))) for i in ids if int(i))


class TokenPreservationTests(unittest.TestCase):
    def test_noncanonical_answer_keeps_sampled_ids(self):
        """@brief 完整答案保留实际分开生成的 > 与 M，不能规范合并。
        @return 无。
        """
        tok = PieceTokenizer()
        text = '<answer>Minnie Driver</answer>'
        raw = [ord(c) for c in text]
        ids, mask = preserve_sampled_prefix(raw, text, tok)
        # 文本等价不够，必须逐编号一致，且真正生成的位置全部参与梯度。
        self.assertNotEqual(tok.encode(text), raw)
        self.assertEqual(ids, raw)
        self.assertEqual(mask, [1] * len(raw))

    def test_exact_boundary_drops_tail_without_reencoding(self):
        """@brief 恰好落在 token 边界的动作只删未执行尾部。
        @return 无。
        """
        tok = PieceTokenizer()
        text = '<answer>Minnie Driver</answer>'
        raw = [ord(c) for c in text + 'TAIL']
        ids, mask = preserve_sampled_prefix(raw, text, tok)
        # 前缀包含非规范 >、M 拆分，截断不得重新规范编码。
        self.assertEqual(ids, raw[:len(text)])
        self.assertEqual(mask, [1] * len(text))

    def test_crossing_token_rebuilds_only_masked_fragment(self):
        """@brief 跨闭合字符的 token 仅重建尾片段并排除梯度。
        @return 无。
        """
        tok = PieceTokenizer()
        prefix = '<answer>Minnie Driver</answer'
        raw = [ord(c) for c in prefix] + [502] + [ord(c) for c in 'ignored']
        ids, mask = preserve_sampled_prefix(raw, prefix + '>', tok)
        # 先前所有实际 token 不变，人工 > 置零，TAIL 不得进入上下文。
        self.assertEqual(ids[:-1], raw[:len(prefix)])
        self.assertEqual(ids[-1], ord('>'))
        self.assertEqual(mask, [1] * len(prefix) + [0])
        report = token_alignment_report(raw, ids, tok, 128, sampled_mask=mask)
        self.assertTrue(report['sampled_prefix_matches'])
        self.assertEqual(report['reconstructed_token_count'], 1)
        self.assertTrue(report['retokenized_prefix'])

    def test_multi_character_boundary_fragment_is_fully_masked(self):
        """@brief 一个 token 横跨整个结束标签时，人工多 token 片段全部屏蔽。
        @return 无。
        """
        tok = PieceTokenizer()
        prefix = '<answer>Minnie Driver'
        ids, mask = preserve_sampled_prefix([ord(c) for c in prefix] + [503], prefix + '</answer>', tok)
        # 所有新构造编号都属于边界，不因包含合法结束标签而获得训练权重。
        self.assertEqual(ids[:len(prefix)], [ord(c) for c in prefix])
        self.assertEqual(mask[len(prefix):], [0] * len('</answer>'))

    def test_native_length_and_eos_padding(self):
        """@brief pad 等于 EOS 时原生长度与尾部剔除都保持内容前缀。
        @return 无。
        """
        tok = PieceTokenizer()
        tok.eos_token_id = 0
        ids, mask = preserve_sampled_prefix([65, 0, 0], 'A', tok, 2)
        self.assertEqual((ids, mask), ([65], [1]))
        # 非法长度与非前缀消费显式拒绝，防止使用整段 encode 静默回退。
        with self.assertRaises(ValueError):
            preserve_sampled_prefix([65], 'A', tok, 2)
        with self.assertRaises(ValueError):
            preserve_sampled_prefix([65], 'B', tok)

    def test_unknown_and_length_text_keeps_original_tokens(self):
        """@brief 无合法动作的完整乱码或替换字符同样保留实际编号。
        @return 无。
        """
        tok = PieceTokenizer()
        raw = [ord('x'), 500, ord('\ufffd')]
        text = tok.decode(raw)
        ids, mask = preserve_sampled_prefix(raw, text, tok)
        self.assertEqual(ids, raw)
        self.assertEqual(mask, [1] * len(raw))

    def test_audit_rejects_unmasked_reconstructed_token(self):
        """@brief 不允许人工编号冒充实际生成 token 进入审计通过路径。
        @return 无。
        """
        tok = PieceTokenizer()
        with self.assertRaises(ValueError):
            token_alignment_report([62, 77], [500], tok, 8, sampled_mask=[1])
        with self.assertRaises(ValueError):
            token_alignment_report([65, 66], [65, 66], tok, 8, sampled_mask=[0, 1])


class BoundaryWorker:
    """经真实 DataProto 补齐生成两轮，保留活动行与原生长度。"""
    def __init__(self, tok):
        """@brief 保存测试 tokenizer 及每轮实际输入。
        @param tok 片段 tokenizer 测试夹具。
        @return 无。
        """
        self.tok, self.inputs, self.calls = tok, [], 0

    def generate_sequences(self, batch):
        """@brief 首轮返回跨边界搜索，次轮返回非规范分词答案。
        @param batch 已按 GPU 数补齐的 DataProto。
        @return token 矩阵和同序原生长度元数据。
        """
        self.inputs.append(batch.batch['input_ids'].clone())
        self.calls += 1
        # 故意在 search 结束字符之后同 token 携带换行，后续未执行文字必须删除。
        ids = ([ord(c) for c in '<search>q</search'] + [501] + [ord(c) for c in 'unexecuted']
               if self.calls == 1 else [ord(c) for c in '<answer>Minnie Driver</answer>'])
        metadata = np.empty(len(batch), dtype=object)
        metadata[:] = [dict(finish_reason='stop', raw_token_count=len(ids))] * len(batch)
        return DataProto.from_dict({'responses': torch.tensor(ids).repeat(len(batch), 1)},
                                   non_tensors={'rollout_metadata': metadata})


class GenerationMaskTests(unittest.TestCase):
    def test_full_loop_keeps_context_and_masks_boundary(self):
        """@brief 两轮真实生成拼接保留非规范答案，人工边界与观察都没有训练权重。
        @return 无。
        """
        tok = PieceTokenizer()
        worker = BoundaryWorker(tok)
        cfg = GenerationConfig(2, 8, 512, 128, 128, 4, observation_truncation='structured',
                               context_policy='bounded', process_checks_enabled=True,
                               record_token_diagnostics=True)
        manager = LLMGenerationManager(tok, worker, cfg)
        manager.batch_search = self.search
        prefix = torch.tensor([[ord('Q')]])
        batch = DataProto.from_dict(dict(input_ids=prefix, attention_mask=torch.ones_like(prefix),
                                        position_ids=torch.zeros_like(prefix)))
        out = manager.run_llm_loop(batch, prefix)
        # 人工闭合字符仍在下轮输入和完整训练历史中，其梯度掩码必须为零。
        boundary = len('<search>q</search>') - 1
        self.assertEqual(out.batch['responses'][0, boundary].item(), ord('>'))
        self.assertEqual(out.batch['info_mask'][0, prefix.shape[1] + boundary].item(), 0)
        self.assertEqual(out.batch['sampled_loss_mask'][0, boundary].item(), 0)
        # 独立掩码只排人工位置，真实观察继续由原工具开关控制。
        self.assertTrue(bool((out.batch['sampled_loss_mask'] >
                              out.batch['info_mask'][:, -out.batch['responses'].shape[1]:]).any()))
        self.assertTrue(tok.decode(worker.inputs[1][0]).startswith('Q<search>q</search>'))
        self.assertNotIn('unexecuted', tok.decode(out.batch['responses'][0]))
        report = out.non_tensor_batch['process_checks'][0]
        self.assertTrue(report['answered'])
        self.assertEqual(report['token_diagnostics'][0]['reconstructed_token_count'], 1)
        self.assertTrue(all(t['sampled_prefix_matches'] for t in report['token_diagnostics']))
        # 答案中的 >、M 仍为两个原始编号，不被合并 token 500 替换。
        answer = [ord(c) for c in '<answer>Minnie Driver</answer>']
        self.assertEqual(out.batch['responses'][0, -len(answer):].tolist(), answer)
        self.assertEqual(out.batch['info_mask'][0, -len(answer):].tolist(), [1] * len(answer))

    def search(self, queries):
        """@brief 提供真实观察格式，检验环境反馈掩码。
        @param queries 本轮查询列表。
        @return 每个查询对应的固定文档字符串。
        """
        return ['Doc 1(Title: A) document'] * len(queries)

    def test_default_disabled_protocol_still_preserves_sampled_ids(self):
        """@brief 默认协议路径同样修复非规范分词，保留原消费文字。
        @return 无。
        """
        tok = PieceTokenizer()
        manager = LLMGenerationManager(tok, None, GenerationConfig(1, 8, 512, 128, 128, 1))
        text = '<answer>Minnie Driver</answer>'
        raw = torch.tensor([[ord(c) for c in text + 'TAIL']])
        ids, texts = manager._postprocess_responses(raw)
        self.assertEqual(texts, [text])
        self.assertEqual(ids[0].tolist(), [ord(c) for c in text])


class IndependentBoundaryMaskTests(unittest.TestCase):
    def test_artificial_mask_applies_with_both_state_modes(self):
        """@brief 工具观察开关两种取值都屏蔽人工 token，真实观察语义不变。
        @return 无。
        """
        data = dict(responses=torch.ones(1, 3), attention_mask=torch.ones(1, 4),
                    loss_mask=torch.tensor([[1., 0., 1.]]),
                    sampled_loss_mask=torch.tensor([[1, 1, 0]]))
        # 中间位置是观察、末位是人工；关闭观察屏蔽仅允许中间位置恢复训练。
        self.assertEqual(response_loss_mask(data, False).tolist(), [[1., 1., 0.]])
        self.assertEqual(response_loss_mask(data, True).tolist(), [[1., 0., 0.]])
        del data['sampled_loss_mask']
        self.assertEqual(response_loss_mask(data, False).tolist(), [[1., 1., 1.]])
        data['sampled_loss_mask'] = torch.tensor([[1., .5, 0.]])
        with self.assertRaises(ValueError):
            response_loss_mask(data, False)

    def test_dynamic_merge_zero_pads_boundary_mask(self):
        """@brief 不同长度入选组补齐时人工边界掩码填零并保持逐行身份。
        @return 无。
        """
        from verl.experimental.difficulty.dynamic_filter import merge_groups
        parts = []
        for length in (3, 5):
            parts.append(DataProto.from_dict(dict(prompts=torch.tensor([[7]]),
                responses=torch.ones(1, length, dtype=torch.long),
                input_ids=torch.ones(1, length + 1, dtype=torch.long),
                attention_mask=torch.ones(1, length + 1, dtype=torch.long),
                position_ids=torch.arange(length + 1).unsqueeze(0),
                sampled_loss_mask=torch.tensor([[1] * (length - 1) + [0]]))))
        # 非零 pad_id 不能污染二值掩码，新增字段走共用零补齐分支。
        result = merge_groups(parts, 151643)
        self.assertEqual(result.batch['sampled_loss_mask'].tolist(), [[1, 1, 0, 0, 0], [1, 1, 1, 1, 0]])

    def test_utf8_partial_decode_uses_safe_fallback(self):
        """@brief 字节中间 decode 长度不单调时保留已完成字符前缀。
        @return 无。
        """
        class ByteTokenizer(PieceTokenizer):
            def decode(self, ids, **kwargs):
                """@brief 模拟 UTF8 未完成时临时替换字符，完成后恢复真实字符。
                @param ids token 编号列表。
                @param kwargs 兼容解码参数。
                @return 对应的完整或临时可见文本。
                """
                ids = list(map(int, ids))
                if ids[:2] == [700, 701]:
                    return '汉' + super().decode(ids[2:], **kwargs)
                if ids and ids[0] == 700:
                    return '\ufffd\ufffd'
                return super().decode(ids, **kwargs)
        # 二分遇到临时长字符串时必须回退，不能把汉字拆成重新编码的人工内容。
        ids, mask = preserve_sampled_prefix([700, 701, 502], '汉>', ByteTokenizer())
        self.assertEqual(ids, [700, 701, ord('>')])
        self.assertEqual(mask, [1, 1, 0])


class FinalMaskIntegrationTests(unittest.TestCase):
    def test_left_padded_audit_keeps_active_row_identity(self):
        """@brief 不同长度活动行左补齐后，原始前缀审计仍逐行一致。
        @return 无。
        """
        from search_r1.llm_agent.context_budget import pad_token_rows
        tok = PieceTokenizer()
        tok.padding_side = 'left'
        manager = LLMGenerationManager(tok, None, GenerationConfig(1, 8, 512, 128, 128, 1,
                                         record_token_diagnostics=True))
        texts = ['<answer>Minnie Driver</answer>', '<answer>x</answer>']
        rows = [[ord(c) for c in text] for text in texts]
        raw = pad_token_rows(rows, 0, 'right')
        native = np.empty(2, dtype=object)
        native[:] = [dict(raw_token_count=len(row), finish_reason='stop') for row in rows]
        output = DataProto.from_dict({'responses': raw}, non_tensors={'rollout_metadata': native})
        ids, consumed, sampled = manager._postprocess_responses(raw, True, native)
        diagnostics = [{}, {}]
        manager._record_token_alignment(output, ids, torch.tensor([True, True]), diagnostics, sampled)
        # 短行的左 pad 不能被计入原始生成前缀或人工边界数量。
        for index, row in enumerate(rows):
            report = diagnostics[index]['token_turns'][0]
            self.assertEqual(report['processed_token_ids'], row)
            self.assertTrue(report['sampled_prefix_matches'])
            self.assertEqual(report['reconstructed_token_count'], 0)
        self.assertEqual(consumed, texts)

    def forward(self, micro_batch, temperature):
        """@brief 使用实际线性参数生成可求导概率及熵，保留正式更新入口。
        @param micro_batch 正式筛选后的微批张量。
        @param temperature 本次固定温度。
        @return 熵和对数概率矩阵。
        """
        log_prob = self.actor.actor_module(micro_batch['responses'].float()) / temperature
        return log_prob.square() * .1, log_prob

    def cpu_identity(self):
        """@brief 仅替换测试 TensorDict 的设备搬移，不改损失或梯度。
        @return 原 TensorDict。
        """
        return self

    def test_actual_update_never_trains_artificial_output(self):
        """@brief 正式 update_policy 在两种观察开关下都不更新人工输出对应参数。
        @return 无。
        """
        for state_masking in (False, True):
            torch.manual_seed(42)
            actor = object.__new__(DataParallelPPOActor)
            actor.actor_module = torch.nn.Linear(2, 2)
            actor.actor_optimizer = torch.optim.SGD(actor.actor_module.parameters(), lr=.001)
            actor.grad_scaler = torch.amp.GradScaler('cpu', enabled=False)
            actor.config = OmegaConf.create(dict(ppo_mini_batch_size=2, ppo_micro_batch_size=1,
                use_dynamic_bsz=False, state_masking=state_masking, use_kl_loss=True,
                clip_ratio=.2, entropy_coeff=.001, kl_loss_coef=.001, kl_loss_type='low_var_kl',
                loss_numerics='safe_v1', grad_clip=1., stability_diagnostics={'enabled':False}))
            self.actor = actor
            actor._forward_micro_batch = self.forward
            responses = torch.ones(2, 2, dtype=torch.long)
            with torch.no_grad():
                old = actor.actor_module(responses.float())
            original_weight = actor.actor_module.weight.detach().clone()
            original_bias = actor.actor_module.bias.detach().clone()
            batch = DataProto.from_dict(dict(responses=responses,
                input_ids=torch.ones(2, 3, dtype=torch.long), attention_mask=torch.ones(2, 3),
                position_ids=torch.arange(3).repeat(2, 1), old_log_probs=old,
                ref_log_prob=old-.1, advantages=torch.tensor([[1.,100000.],[1.,100000.]]),
                loss_mask=torch.ones(2, 2), sampled_loss_mask=torch.tensor([[1,0],[1,0]])),
                meta_info={'temperature':1.})
            # 人工输出具有极大正优势，若掩码丢失会明显污染第二输出行；只替换设备搬移。
            with patch.object(TensorDict, 'cuda', FinalMaskIntegrationTests.cpu_identity):
                actor.update_policy(batch)
            self.assertTrue(torch.equal(actor.actor_module.weight[1], original_weight[1]))
            self.assertTrue(torch.equal(actor.actor_module.bias[1], original_bias[1]))
            self.assertFalse(torch.equal(actor.actor_module.weight[0], original_weight[0]))


class ProbabilityLayoutCPUTests(unittest.TestCase):
    def fused_reference(self, logits, labels):
        """@brief 模拟融合入口并验证连续布局，使用原生概率作为参考。
        @param logits 二维样本乘词表张量。
        @param labels 已展平的连续编号。
        @return 对应目标的原生对数概率。
        """
        self.assertTrue(labels.is_contiguous())
        return logits.log_softmax(-1).gather(-1, labels.unsqueeze(-1)).squeeze(-1)

    def test_flattened_tail_labels_are_contiguous(self):
        """@brief 多样本单 token 尾块必须复制 stride，不能依赖 reshape。
        @return 无。
        """
        logits = torch.randn(2, 3, 16, requires_grad=True)
        labels = torch.tensor([[1, 2, 3], [4, 5, 6]])[:, -1:]
        self.assertFalse(labels.reshape(-1).is_contiguous())
        # 只替换 GPU kernel 边界，生产展平/连续复制与 autograd 路径仍实际执行。
        with patch.object(functional, 'FLAH_ATTN_CROSS_ENTROPY_LOSS_AVAILABLE', True), \
             patch.object(functional, 'logprobs_from_logits_flash_attn', self.fused_reference):
            out = functional.logprobs_from_logits(logits[:, -1:], labels)
        ref = logits[:, -1:].log_softmax(-1).gather(-1, labels.unsqueeze(-1)).squeeze(-1)
        self.assertTrue(torch.allclose(out, ref))
        self.assertTrue(torch.allclose(torch.autograd.grad(out.sum(), logits, retain_graph=True)[0],
                                       torch.autograd.grad(ref.sum(), logits)[0]))


@unittest.skipUnless(torch.cuda.is_available(), 'GPU unavailable')
class ProbabilityLayoutGPUTests(unittest.TestCase):
    def test_real_kernel_tail_values_and_gradients(self):
        """@brief 实际融合 GPU kernel 的多样本单 token 尾块与原生概率/梯度一致。
        @return 无。
        """
        torch.manual_seed(42)
        # 同时覆盖尾块为 1、多 token、整块、单/多样本，以及非连续原始标签。
        for batch in (1, 2):
            for length in (32, 33, 34, 65):
                for recompute in (False, True):
                    with self.subTest(batch=batch, length=length, recompute=recompute):
                        full = torch.randn(batch, length + 2, 256, device='cuda', requires_grad=True)
                        labels = torch.randint(0, 256, (batch, length + 2), device='cuda')[:, 1:-1]
                        lp, entropy = token_statistics(full[:, 1:-1], labels,
                                                       chunk_size=32, recompute=recompute)
                        ref = full[:, 1:-1].log_softmax(-1).gather(-1, labels.unsqueeze(-1)).squeeze(-1)
                        grad = torch.autograd.grad(lp.sum(), full, retain_graph=True)[0]
                        expected = torch.autograd.grad(ref.sum(), full)[0]
                        self.assertLess((lp - ref).abs().max().item(), 2e-6)
                        self.assertLess((grad - expected).abs().max().item(), 2e-6)
                        self.assertTrue(torch.isfinite(entropy).all().item())
