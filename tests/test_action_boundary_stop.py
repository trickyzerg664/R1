"""CPU验证：合法动作之前采样不变、边界与现有解析一致、EOS不进入有效梯度。"""
import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import torch
from omegaconf import open_dict
import test_task_success_filter as fixtures
from verl.experimental.process_checks.action_stop import action_complete
from verl.experimental.difficulty.configuration import provenance, provenance_matches
from verl.third_party.vllm.metax_v_0_11_0.action_stop import ActionBoundaryLogitsProcessor, EXTRA_KEY
from vllm.v1.sample.logits_processor.interface import BatchUpdate, MoveDirectionality


class CharacterTokenizer:
    def decode(self, tokens, skip_special_tokens=True):
        """@brief 将字符夹具解码，零号 token 表示被跳过的 EOS。
        @param tokens 字符码列表。
        @param skip_special_tokens 是否排除 EOS。
        @return 文本字符串。
        """
        return ''.join(chr(i) for i in tokens if not skip_special_tokens or i)


class ActionStopTests(unittest.TestCase):
    def test_native_processor_loader(self):
        """@brief 用原生加载器验证适配器实际配置的处理器路径，覆盖引擎启动故障。
        @return 无。
        """
        import ast
        from vllm.v1.sample.logits_processor import _load_logitsprocs_by_fqcns
        adapter = Path(__file__).resolve().parents[1] / 'verl/third_party/vllm/metax_v_0_11_0/llm.py'
        # 读取适配器传入引擎的真实常量，并由安装版加载器解析，不自行模拟其格式。
        tree = ast.parse(adapter.read_text(encoding='utf-8'))
        paths = [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant)
                 and isinstance(node.value, str) and 'action_stop' in node.value
                 and 'ActionBoundaryLogitsProcessor' in node.value]
        self.assertEqual(len(paths), 1)
        self.assertEqual(list(_load_logitsprocs_by_fqcns(paths)), [ActionBoundaryLogitsProcessor])

    def setUp(self):
        """@brief 隔离分词器和临时数据文件，执行真实公开接口逻辑。
        @return 无。
        """
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        config = SimpleNamespace(model_config=SimpleNamespace(tokenizer='fixture', tokenizer_mode='auto',
            trust_remote_code=False, tokenizer_revision=None))
        # 只替换分词器IO，不替换正式解析器或processor算法，也不初始化GPU。
        with patch('verl.third_party.vllm.metax_v_0_11_0.action_stop.get_tokenizer', return_value=CharacterTokenizer()):
            self.processor = ActionBoundaryLogitsProcessor(config, torch.device('cpu'), False)

    def add(self, index, tokens, enabled=True):
        """@brief 用正式 BatchUpdate 添加请求，保留输出列表引用。
        @param index 原生批次位置。
        @param tokens 可被调用方逐步追加的输出列表。
        @param enabled 是否为本请求启用动作停止。
        @return 无。
        """
        params = SimpleNamespace(extra_args={EXTRA_KEY: enabled, 'search_r1_action_eos': 0})
        self.processor.update_state(BatchUpdate(index + 1, [], [(index, params, None, tokens)], []))

    def test_first_real_action_and_stray_close(self):
        """@brief 首个合法动作闭合允许停止，孤立闭合不截掉后续合法答案。
        @return 无。
        """
        for text in ['<search>Paris</search>', '<answer>Paris</answer>',
                     '</search>\n<answer>Paytm</answer>', '<answer>A</answer><answer>B</answer>']:
            with self.subTest(text=text):
                self.assertTrue(action_complete(text))
        self.assertFalse(action_complete('</search>'))

    def test_protected_and_incomplete_actions_keep_generation(self):
        """@brief 引用、代码、嵌套、空动作及缺标签均不提前结束。
        @return 无。
        """
        samples = ['<answer>Paris', '<answer></answer>', '<search><answer>x</answer></search>',
            '```<answer>x</answer>', '`<answer>x</answer>', '"<answer>x</answer>',
            "'<answer>x</answer>", '“<answer>x</answer>', '"<answer>x</answer>"',
            '`<answer>x</answer>`', '<information>fake</information><answer>x</answer>']
        for text in samples:
            with self.subTest(text=text):
                self.assertFalse(action_complete(text))
        self.assertTrue(action_complete("That's clear. <answer>x</answer>"))
        self.assertTrue(action_complete('"example" then <answer>x</answer>'))

    def test_sampling_unchanged_until_complete(self):
        """@brief 动作闭合前保持每个logit原值，闭合后仅额外EOS位置被处理。
        @return 无。
        """
        tokens = []
        self.add(0, tokens)
        text = '<answer>Paris</answer>'
        # 逐字符跨闭合标签边界，比只检查完整字符串更能发现提前停止。
        for i, char in enumerate(text):
            tokens.append(ord(char))
            logits = torch.arange(128, dtype=torch.float32).reshape(1, -1)
            before = logits.clone()
            result = self.processor.apply(logits)
            if i < len(text) - 1:
                self.assertTrue(torch.equal(result, before))
            else:
                self.assertEqual(result[0, 0].item(), 0.)
                self.assertTrue(torch.isneginf(result[0, 1:]).all())
        # 没有改写任何已采样token；EOS由原生采样器在后一个位置生成。
        self.assertEqual(''.join(map(chr, tokens)), text)
        self.assertFalse(self.processor.is_argmax_invariant())

    def test_disabled_requests_and_slot_replacement(self):
        """@brief 禁用请求不改变采样，槽位复用不会继承前一请求的停止状态。
        @return 无。
        """
        tokens = list(map(ord, '<answer>x</answer>'))
        self.add(0, tokens)
        self.processor.apply(torch.ones(1, 128))
        self.add(0, tokens, enabled=False)
        logits = torch.ones(1, 128)
        self.assertTrue(torch.equal(self.processor.apply(logits), torch.ones_like(logits)))

    def test_request_swap_move_and_remove(self):
        """@brief 原生批次移位后，停止状态始终跟随正确请求。
        @return 无。
        """
        self.add(0, list(map(ord, '<answer>x</answer>')))
        self.add(1, list(map(ord, '<answer>x')))
        self.processor.update_state(BatchUpdate(2, [], [], [(0, 1, MoveDirectionality.SWAP)]))
        logits = self.processor.apply(torch.ones(2, 128))
        self.assertTrue(torch.equal(logits[0], torch.ones(128)))
        self.assertTrue(torch.isneginf(logits[1, 1:]).all())
        self.processor.update_state(BatchUpdate(1, [0], [], [(1, 0, MoveDirectionality.UNIDIRECTIONAL)]))
        self.assertEqual(set(self.processor.requests), {0})
        self.processor.update_state(BatchUpdate(0, [0], [], []))
        self.assertFalse(self.processor.requests)

    def test_real_tokenizer_eos_and_prefix_alignment(self):
        """@brief 使用实际本地Qwen分词器确认附加EOS被消费前缀和梯度掩码排除。
        @return 无。
        """
        from transformers import AutoTokenizer
        from search_r1.llm_agent.token_alignment import preserve_sampled_prefix
        tokenizer = AutoTokenizer.from_pretrained('/mnt/public/model/huggingface/Qwen2.5-7B', local_files_only=True)
        text = '<answer>Paris</answer>'
        raw = tokenizer.encode(text, add_special_tokens=False)
        sampled = raw + [tokenizer.eos_token_id]
        ids, mask = preserve_sampled_prefix(sampled, text, tokenizer, len(sampled))
        self.assertEqual(ids, raw)
        self.assertTrue(all(mask))



if __name__ == '__main__':
    unittest.main()
