"""将 vLLM 0.11.0 的推理和权重更新接口接入旧 veRL rollout。"""

import os
import tempfile
from pathlib import Path

import torch
from safetensors.torch import save_file
from vllm import LLM as NativeLLM


class LLM:
    """保留旧 rollout 的窄接口；只支持每个 FSDP rank 使用一张沐曦卡。"""

    def __init__(self, actor_module, tokenizer, model_hf_config,
                 tensor_parallel_size, dtype, enforce_eager,
                 gpu_memory_utilization, skip_tokenizer_init,
                 max_model_len, load_format):
        if tensor_parallel_size != 1:
            raise ValueError('MetaX vLLM adapter currently requires tensor_model_parallel_size=1')
        model_path = getattr(tokenizer, 'name_or_path', None) or getattr(model_hf_config, '_name_or_path', None)
        if not model_path or not Path(model_path).is_dir():
            raise ValueError(f'MetaX vLLM needs a local model directory: {model_path}')
        # pad id 可以是 0；仅在未定义时才回退到 eos。
        self.pad_token_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
        # 当前 MetaX allocator 在启用 sleep 后退出时崩溃；仅显式设为 1 才启用休眠。
        sleep_mode = os.environ.get('VERL_METAX_ENABLE_SLEEP_MODE', '0')
        if sleep_mode not in ('0', '1'):
            raise ValueError('VERL_METAX_ENABLE_SLEEP_MODE must be 0 or 1')
        self._sleep_enabled = sleep_mode == '1'
        self.engine = NativeLLM(
            model=model_path,
            tokenizer=model_path,
            tensor_parallel_size=1,
            dtype=dtype,
            enforce_eager=enforce_eager,
            gpu_memory_utilization=gpu_memory_utilization,
            skip_tokenizer_init=skip_tokenizer_init,
            max_model_len=max_model_len,
            enable_sleep_mode=self._sleep_enabled,
            worker_extension_cls='verl.third_party.vllm.metax_v_0_11_0.worker.MetaxWeightUpdateExtension',
        )
        self._sleeping = False

    def offload_model_weights(self):
        """支持休眠时释放推理显存；无休眠路径保留常驻权重。"""
        if not self._sleep_enabled:
            return
        if not self._sleeping:
            self.engine.sleep(level=2)
            self._sleeping = True

    def sync_model_weights(self, params, load_format='hf'):
        """把完整 FSDP state_dict 经本机共享内存交给 vLLM worker。"""
        if load_format != 'hf':
            raise ValueError(f'MetaX vLLM only supports full HF weights, got {load_format}')
        sync_dir = os.environ.get('VERL_METAX_WEIGHT_SYNC_DIR', '/dev/shm')
        if not Path(sync_dir).is_dir():
            raise ValueError(f'Weight sync directory does not exist: {sync_dir}')
        # 临时目录只在同步期间存在；worker RPC 返回后才删除，防止读取到半成品。
        with tempfile.TemporaryDirectory(prefix='verl-metax-', dir=sync_dir) as temp_dir:
            weight_path = str(Path(temp_dir) / 'weights.safetensors')
            tensors = {
                name: value.detach().cpu().contiguous()
                for name, value in params.items()
                if isinstance(value, torch.Tensor)
            }
            if not tensors:
                raise ValueError('FSDP returned no tensors for MetaX weight sync')
            save_file(tensors, weight_path)
            del tensors
            if self._sleeping:
                self.engine.wake_up(tags=['weights'])
            result = self.engine.collective_rpc('load_weights_from_safetensors', args=(weight_path,))
            if not result or any(item['loaded'] == 0 for item in result):
                raise RuntimeError(f'MetaX vLLM did not load actor weights: {result}')
            if self._sleeping:
                self.engine.wake_up(tags=['kv_cache'])
                self._sleeping = False

    def init_cache_engine(self):
        """vLLM 0.11 管理 KV cache；休眠路径的唤醒由 sync_model_weights 完成。"""

    def free_cache_engine(self):
        """旧 rollout 的此调用无需操作；外层 manager 按配置处理休眠。"""

    def generate(self, prompts, sampling_params, prompt_token_ids, use_tqdm=False):
        """把新 RequestOutput 转为旧 rollout 需要的 (token_ids, logprobs)。"""
        if self._sleeping:
            raise RuntimeError('MetaX vLLM weights are sleeping; sync actor weights first')
        requests = [{'prompt_token_ids': ids} for ids in prompt_token_ids]
        outputs = self.engine.generate(requests, sampling_params=sampling_params, use_tqdm=use_tqdm)
        token_rows = []
        logprob_rows = []
        for request in outputs:
            for completion in request.outputs:
                token_ids = list(completion.token_ids)
                token_rows.append(token_ids)
                steps = completion.logprobs or []
                logprob_rows.append([
                    float(steps[i][token_id].logprob)
                    if i < len(steps) and token_id in steps[i] else 0.0
                    for i, token_id in enumerate(token_ids)
                ])
        if not token_rows:
            raise RuntimeError('MetaX vLLM returned no completions')
        width = max(map(len, token_rows))
        responses = torch.full((len(token_rows), width), self.pad_token_id, dtype=torch.long)
        logprobs = torch.zeros((len(token_rows), width), dtype=torch.float32)
        for row, (tokens, probs) in enumerate(zip(token_rows, logprob_rows)):
            responses[row, :len(tokens)] = torch.tensor(tokens, dtype=torch.long)
            logprobs[row, :len(probs)] = torch.tensor(probs, dtype=torch.float32)
        return responses, logprobs
