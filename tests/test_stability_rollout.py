"""CPU 回归：执行真实 rollout 适配，原生引擎仅替换导入边界。"""
import runpy
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import torch
from omegaconf import OmegaConf
from verl import DataProto


class RolloutMetadataTests(unittest.TestCase):
    def rollout(self, n=1, version='0.11.0', mismatch=False):
        """@brief 隔离原生 GPU 导入并构造可执行真实生成适配的 CPU 夹具。
        @param n 每条提示候选数。
        @param version 后端版本，用于检测审计接口支持边界。
        @param mismatch 是否返回数量错误的原生元数据。
        @return rollout 实例及可检查的原生生成 Mock。
        """
        third_party = types.ModuleType('verl.third_party.vllm')
        third_party.LLM = object
        third_party.vllm_version = version
        third_party.parallel_state = object()
        native = types.ModuleType('vllm')
        native.SamplingParams = object
        path = Path(__file__).resolve().parents[1] / 'verl/workers/rollout/vllm_rollout/vllm_rollout.py'
        # 隔离导入原生运行时，被测方法仍直接来自生产文件。
        with patch.dict('sys.modules', {'verl.third_party.vllm': third_party, 'vllm': native}):
            adapter_type = runpy.run_path(str(path))['vLLMRollout']
        rollout = object.__new__(adapter_type)
        rollout.config = OmegaConf.create({'free_cache_engine': False, 'response_length': 4, 'n': n})
        rollout.pad_token_id = 0
        rollout.sampling_params = types.SimpleNamespace()
        def generate(**kwargs):
            """@brief 返回可核对候选顺序的原生 token、概率及可选元数据。
            @param kwargs 实际生成适配传入的参数。
            @return 与真实原生接口同结构的二元组或三元组。
            """
            count = len(kwargs['prompt_token_ids']) * n
            response = torch.tensor([[7, 2]]).repeat(count, 1)
            probabilities = torch.tensor([[-.1, -.2]]).repeat(count, 1)
            if kwargs.get('return_metadata', False):
                metadata = [dict(finish_reason='stop', raw_token_count=2, candidate=i) for i in range(count)]
                return response, probabilities, metadata[:-1] if mismatch else metadata
            return response, probabilities
        engine = MagicMock()
        engine.generate.side_effect = generate
        rollout.inference_engine = engine
        return rollout, engine

    def prompts(self, audit):
        """@brief 构造两个真实提示并显式声明 EOS 和审计开关。
        @param audit 是否请求终止元数据。
        @return CPU DataProto。
        """
        ids = torch.tensor([[0, 5, 6], [0, 8, 9]])
        return DataProto.from_dict(dict(input_ids=ids, attention_mask=(ids != 0).long(),
            position_ids=torch.tensor([[0, 0, 1], [0, 0, 1]])),
            meta_info={'eos_token_id': 2, 'record_rollout_metadata': audit})

    def test_default_and_audited_outputs_equal(self):
        """@brief 元数据开关不改变实际 rollout token、概率掩码或位置编码。
        @return 无。
        """
        rollout, engine = self.rollout()
        legacy = rollout.generate_sequences(self.prompts(False))
        audited = rollout.generate_sequences(self.prompts(True))
        # 比较所有张量字段，覆盖 EOS 掩码、位置及提示重复规则。
        for key in legacy.batch.keys():
            self.assertTrue(torch.equal(legacy.batch[key], audited.batch[key]))
        self.assertNotIn('rollout_metadata', legacy.non_tensor_batch)
        self.assertEqual(audited.non_tensor_batch['rollout_metadata'][1]['candidate'], 1)
        self.assertTrue(engine.generate.call_args.kwargs['return_metadata'])
        self.assertEqual(audited.batch['responses'].tolist(), [[7, 2, 0, 0], [7, 2, 0, 0]])

    def test_multiple_candidates_preserve_metadata_order(self):
        """@brief 多候选展开后的元数据必须对应真实候选数量和顺序。
        @return 无。
        """
        rollout, _ = self.rollout(n=2)
        output = rollout.generate_sequences(self.prompts(True))
        self.assertEqual(len(output), 4)
        self.assertEqual([row['candidate'] for row in output.non_tensor_batch['rollout_metadata']], [0, 1, 2, 3])
        self.assertEqual(output.batch['prompts'][:, -1].tolist(), [6, 6, 9, 9])

    def test_malformed_metadata_rejected(self):
        """@brief 元数据数量错误时失败，防止污染后续轨迹身份。
        @return 无。
        """
        rollout, _ = self.rollout(mismatch=True)
        with self.assertRaisesRegex(ValueError, 'candidate count'):
            rollout.generate_sequences(self.prompts(True))

    def test_unsupported_backend_keeps_legacy_interface(self):
        """@brief 未支持的后端不接收新参数或伪造原生终止原因。
        @return 无。
        """
        rollout, engine = self.rollout(version='0.6.3')
        output = rollout.generate_sequences(self.prompts(True))
        self.assertNotIn('return_metadata', engine.generate.call_args.kwargs)
        self.assertNotIn('rollout_metadata', output.non_tensor_batch)
