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
        """
        @brief 初始化单卡推理引擎并登记初始权重可用于生成。
        @param actor_module 旧接口传入的训练模型，初始推理权重由本地目录加载。
        @param tokenizer 含本地模型路径及 pad/eos 标识的分词器。
        @param model_hf_config 含备用本地模型路径的模型配置。
        @param tensor_parallel_size 张量并行数，当前仅支持 1。
        @param dtype 原生引擎支持的推理精度。
        @param enforce_eager 是否禁用图捕获。
        @param gpu_memory_utilization 推理引擎显存预算比例。
        @param skip_tokenizer_init 是否跳过引擎内分词器初始化。
        @param max_model_len 引擎最大上下文长度。
        @param load_format 保留的旧加载接口参数。
        @return 无。
        @raises ValueError 并行数、本地路径或休眠配置无效时抛出。
        @note 后续权重同步和缓存失效均完成后才恢复生成资格。
        """
        # 当前实现按每个 rank 单卡运行，禁止悄悄采用不支持的并行路径。
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
        # 冷加载的权重和缓存一致；同步期间置为无效，任何失败都禁止继续生成。
        self._weights_ready = True

    def offload_model_weights(self):
        """支持休眠时释放推理显存；无休眠路径保留常驻权重。"""
        if not self._sleep_enabled:
            return
        if not self._sleeping:
            self.engine.sleep(level=2)
            self._sleeping = True

    def sync_model_weights(self, params, load_format='hf'):
        """
        @brief 同步完整训练权重并使上一版本的前缀 KV 缓存失效。
        @param params 完整 FSDP state_dict，张量经共享目录交给 worker。
        @param load_format 权重格式，当前只支持 hf。
        @return 无。
        @raises ValueError 格式、共享目录或张量集合无效时抛出。
        @raises RuntimeError 存在未完成请求、加载失败或缓存清空失败时抛出。
        @note 同步期间不得并发生成；失败后必须重新完成同步才允许生成。
        """
        if load_format != 'hf':
            raise ValueError(f'MetaX vLLM only supports full HF weights, got {load_format}')
        sync_dir = os.environ.get('VERL_METAX_WEIGHT_SYNC_DIR', '/dev/shm')
        if not Path(sync_dir).is_dir():
            raise ValueError(f'Weight sync directory does not exist: {sync_dir}')
        # 先关闭生成资格；拒绝在请求尚持有 KV 块时修改权重，避免重置静默失败。
        self._weights_ready = False
        if self.engine.llm_engine.has_unfinished_requests():
            raise RuntimeError('MetaX vLLM cannot sync weights with unfinished requests')
        # 临时目录只在同步期间存在；worker RPC 返回后才删除，防止读取到半成品。
        with tempfile.TemporaryDirectory(prefix='verl-metax-', dir=sync_dir) as temp_dir:
            weight_path = str(Path(temp_dir) / 'weights.safetensors')
            # 只导出训练张量，转到 CPU 且连续存储以供 worker 安全读取。
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
            # 加载失败时保留不可生成状态，不能把缓存重置误作完整同步成功。
            if not result or any(item['loaded'] == 0 for item in result):
                raise RuntimeError(f'MetaX vLLM did not load actor weights: {result}')
            if self._sleeping:
                self.engine.wake_up(tags=['kv_cache'])
                self._sleeping = False
            # 完整加载并唤醒 KV 后只重置一次；同权重多轮生成仍可复用前缀。
            # vLLM 0.11 V1 同步接口正常返回 None；非成功值或异常均视为失败。
            reset_result = self.engine.reset_prefix_cache()
            if reset_result is not None and reset_result is not True:
                raise RuntimeError('MetaX vLLM failed to reset prefix cache after weight sync')
            self._weights_ready = True

    def init_cache_engine(self):
        """vLLM 0.11 管理 KV cache；休眠路径的唤醒由 sync_model_weights 完成。"""

    def free_cache_engine(self):
        """旧 rollout 的此调用无需操作；外层 manager 按配置处理休眠。"""

    def generate(self, prompts, sampling_params, prompt_token_ids, use_tqdm=False):
        """
        @brief 仅使用已同步且缓存一致的权重生成旧接口的 token 和概率张量。
        @param prompts 旧接口保留的文本提示；实际使用 token 输入。
        @param sampling_params 原生引擎采样参数。
        @param prompt_token_ids 每条请求的非 padding token 列表。
        @param use_tqdm 是否显示原生生成进度。
        @return 二元组：右补齐的 token 整数张量及对应 logprob 浮点张量。
        @raises RuntimeError 引擎休眠、同步未完成或未返回生成结果时抛出。
        @note 同一权重版本内不清空前缀缓存，不改变采样和补齐语义。
        """
        if self._sleeping:
            raise RuntimeError('MetaX vLLM weights are sleeping; sync actor weights first')
        # 同步中断或缓存失败后拒绝旧/混合状态，不能依赖调用方一定退出。
        if not self._weights_ready:
            raise RuntimeError('MetaX vLLM weights and prefix cache are not ready; sync actor weights first')
        requests = [{'prompt_token_ids': ids} for ids in prompt_token_ids]
        outputs = self.engine.generate(requests, sampling_params=sampling_params, use_tqdm=use_tqdm)
        token_rows = []
        logprob_rows = []
        # 按原请求/候选顺序展开输出；缺少原生 logprob 时保持旧接口的零值回退。
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
        # 仅在真实 token 区域填值，右侧补齐与概率张量保持相同形状。
        for row, (tokens, probs) in enumerate(zip(token_rows, logprob_rows)):
            responses[row, :len(tokens)] = torch.tensor(tokens, dtype=torch.long)
            logprobs[row, :len(probs)] = torch.tensor(probs, dtype=torch.float32)
        return responses, logprobs
