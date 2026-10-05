"""CPU 回归：同步完成前不能生成，新权重不能复用旧版本前缀。"""

import runpy
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, call, patch

import torch
from safetensors import safe_open


class MetaxWeightCacheInvalidationTests(unittest.TestCase):
    """替换原生 GPU 引擎，执行真实适配器及 safetensors 导出逻辑。"""

    def setUp(self):
        """
        @brief 创建隔离的原生引擎替身与真实适配器实例。
        @return 无。
        @note 不导入原生 vLLM 或创建 GPU，上下文目录在每条测试后清理。
        """
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.env = patch.dict('os.environ', {
            'VERL_METAX_WEIGHT_SYNC_DIR': self.directory.name,
            'VERL_METAX_ENABLE_SLEEP_MODE': '0',
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.engine = Mock()
        self.engine.llm_engine.has_unfinished_requests.return_value = False
        self.engine.collective_rpc.return_value = [{'loaded': 1, 'total': 1}]
        self.engine.reset_prefix_cache.return_value = None
        # 仅替换导入边界；被测方法与磁盘导出逻辑来自真实生产源码。
        native = types.ModuleType('vllm')
        native.LLM = Mock(return_value=self.engine)
        path = Path(__file__).resolve().parents[1] / 'verl/third_party/vllm/metax_v_0_11_0/llm.py'
        with patch.dict('sys.modules', {'vllm': native}):
            adapter_type = runpy.run_path(str(path))['LLM']
        tokenizer = types.SimpleNamespace(name_or_path=self.directory.name, pad_token_id=0, eos_token_id=2)
        self.adapter = adapter_type(None, tokenizer, None, 1, 'float16', True, .32, False, 256, 'hf')
        self.params = {'weight': torch.tensor([1.0])}

    def configure_output(self):
        """
        @brief 配置包含真实 token/logprob 形状的原生输出替身。
        @return 无。
        """
        completion = types.SimpleNamespace(token_ids=[7, 8], logprobs=[{7: types.SimpleNamespace(logprob=-.5)}, {}])
        self.engine.generate.return_value = [types.SimpleNamespace(outputs=[completion])]

    def assert_generation_blocked(self):
        """
        @brief 验证失败状态不会把请求转交给原生引擎。
        @return 无。
        """
        with self.assertRaisesRegex(RuntimeError, 'not ready'):
            self.adapter.generate(None, object(), [[3]])
        self.engine.generate.assert_not_called()

    def test_new_weights_invalidate_old_prefix_before_generation(self):
        """
        @brief 用可复用前缀的状态机复现旧缓存问题，验证更新后读取新状态。
        @return 无。
        """
        state = {'weight': 1, 'prefix': 1}

        def load_weights(method, args):
            """
            @brief 从实际导出文件更新替身权重，故意保留旧前缀。
            @param method RPC 方法名。
            @param args 含临时权重文件路径的二元接口参数。
            @return 模拟 worker 的已加载数量列表。
            """
            self.assertEqual(method, 'load_weights_from_safetensors')
            # 只更新权重，不清除旧 prefix，确保生产方法必须完成失效步骤。
            with safe_open(args[0], framework='pt', device='cpu') as handle:
                state['weight'] = int(handle.get_tensor('weight').item())
            return [{'loaded': 1, 'total': 1}]

        def reset_prefix():
            """@brief 清除旧状态，模拟 V1 正常返回 None 的同步接口。
            @return 无。
            """
            state['prefix'] = None

        self.engine.collective_rpc.side_effect = load_weights
        self.engine.reset_prefix_cache.side_effect = reset_prefix
        self.adapter.sync_model_weights({'weight': torch.tensor([2.0])})
        # 缺陷版仍保留 prefix=1；修复后下一次前缀计算应来自 weight=2。
        prefix_used_next = state['weight'] if state['prefix'] is None else state['prefix']
        self.assertEqual(prefix_used_next, 2)
        self.engine.reset_prefix_cache.assert_called_once_with()
        self.assertTrue(self.adapter._weights_ready)

    def test_reset_after_load_accepts_v1_none_and_boolean_success(self):
        """@brief 验证公开接口兼容 None/True，且先加载后重置。
        @return 无。
        """
        events = Mock()
        events.attach_mock(self.engine.collective_rpc, 'load')
        events.attach_mock(self.engine.reset_prefix_cache, 'reset')
        # 当前 V1 返回 None，其他引擎返回 True，两种成功语义都需保持。
        for result in (None, True):
            with self.subTest(result=result):
                events.reset_mock()
                self.engine.reset_prefix_cache.return_value = result
                self.adapter.sync_model_weights(self.params)
                self.assertEqual([entry[0] for entry in events.mock_calls], ['load', 'reset'])
                self.assertTrue(self.adapter._weights_ready)

    def test_sleep_wakes_kv_before_reset(self):
        """@brief 验证休眠路径先唤醒权重、加载、唤醒 KV，再重置。
        @return 无。
        """
        self.adapter._sleeping = True
        events = Mock()
        events.attach_mock(self.engine.wake_up, 'wake')
        events.attach_mock(self.engine.collective_rpc, 'load')
        events.attach_mock(self.engine.reset_prefix_cache, 'reset')
        self.adapter.sync_model_weights(self.params)
        self.assertEqual([entry[0] for entry in events.mock_calls], ['wake', 'load', 'wake', 'reset'])
        self.assertEqual(self.engine.wake_up.call_args_list, [call(tags=['weights']), call(tags=['kv_cache'])])
        self.assertFalse(self.adapter._sleeping)

    def test_reset_failure_or_exception_blocks_generation(self):
        """@brief 清缓存返回 False 或抛异常时都不能继续生成。
        @return 无。
        """
        # 逐个覆盖正常失败返回和异常传播，均需关闭生成资格。
        for failure in (False, RuntimeError('reset interrupted')):
            with self.subTest(failure=str(failure)):
                self.engine.reset_prefix_cache.side_effect = failure if isinstance(failure, Exception) else None
                self.engine.reset_prefix_cache.return_value = failure
                with self.assertRaises(RuntimeError):
                    self.adapter.sync_model_weights(self.params)
                self.assert_generation_blocked()

    def test_load_failure_never_marks_cache_ready(self):
        """@brief 加载为空、零权重或异常时不能重置并放行不完整状态。
        @return 无。
        """
        # 空加载、零参数加载和中断分别模拟，不允许任何一种放行。
        for failure in ([], [{'loaded': 0}], RuntimeError('load interrupted')):
            with self.subTest(failure=str(failure)):
                self.engine.collective_rpc.side_effect = failure if isinstance(failure, Exception) else None
                self.engine.collective_rpc.return_value = failure
                with self.assertRaises(RuntimeError):
                    self.adapter.sync_model_weights(self.params)
                self.engine.reset_prefix_cache.assert_not_called()
                self.assert_generation_blocked()

    def test_active_requests_reject_update_before_any_weight_mutation(self):
        """@brief 请求仍持有缓存时拒绝同步，避免原生 V1 隐藏的重置失败。
        @return 无。
        """
        # 活动请求持有的旧块不得跨权重更新，因此在 RPC 之前拒绝。
        self.engine.llm_engine.has_unfinished_requests.return_value = True
        with self.assertRaisesRegex(RuntimeError, 'unfinished requests'):
            self.adapter.sync_model_weights(self.params)
        self.engine.collective_rpc.assert_not_called()
        self.engine.reset_prefix_cache.assert_not_called()
        self.assert_generation_blocked()

    def test_successful_retry_restores_generation(self):
        """@brief 失败后必须重新同步并成功失效缓存才恢复生成。
        @return 无。
        """
        self.engine.reset_prefix_cache.return_value = False
        with self.assertRaises(RuntimeError):
            self.adapter.sync_model_weights(self.params)
        self.assert_generation_blocked()
        # 新的一次完整成功同步才能恢复，不允许只清掉异常标志放行。
        self.engine.reset_prefix_cache.return_value = None
        self.adapter.sync_model_weights(self.params)
        self.configure_output()
        tokens, probabilities = self.adapter.generate(None, object(), [[3]])
        self.assertEqual(tokens.tolist(), [[7, 8]])
        self.assertEqual(probabilities.tolist(), [[-.5, 0]])

    def test_same_weight_generation_preserves_cache_and_padding_semantics(self):
        """@brief 同权重生成保留前缀缓存，pad=0 和 token/logprob 转换不变。
        @return 无。
        """
        self.adapter.sync_model_weights(self.params)
        self.configure_output()
        short = types.SimpleNamespace(token_ids=[9], logprobs=[])
        self.engine.generate.return_value.append(types.SimpleNamespace(outputs=[short]))
        for _ in range(2):
            tokens, probabilities = self.adapter.generate(None, object(), [[3], [4]])
            self.assertEqual(tokens.tolist(), [[7, 8], [9, 0]])
            self.assertEqual(probabilities.tolist(), [[-.5, 0], [0, 0]])
        # 两次同权重生成不重复清空缓存；仅权重同步时重置一次。
        self.engine.reset_prefix_cache.assert_called_once_with()


# 可直接运行或通过 unittest discover；本文件不启动原生 GPU 引擎。
if __name__ == '__main__':
    unittest.main()
