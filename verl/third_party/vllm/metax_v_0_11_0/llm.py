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
                 max_model_len, load_format, max_num_batched_tokens=None,
                 max_num_seqs=None, offload_weights_to_cpu=False, action_stop=False):
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
        @param max_num_batched_tokens 每次调度的 token 上限，None 保留原生默认。
        @param max_num_seqs 同时调度的序列数上限，None 保留原生默认。
        @param offload_weights_to_cpu 生成调用间是否卸载推理权重到CPU，默认关闭。
        @param action_stop 是否仅在合法完整动作后用 EOS 结束本轮，默认关闭。
        @return 无。
        @raises ValueError 并行数、本地路径、休眠配置或调度预算无效时抛出。
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
        # 两种卸载机制不能混用，缺省仍保持历史常驻行为。
        if not isinstance(offload_weights_to_cpu, bool) or (self._sleep_enabled and offload_weights_to_cpu):
            raise ValueError('CPU weight offload requires a boolean option and disabled sleep mode')
        self._cpu_offload_enabled = offload_weights_to_cpu
        self._cpu_offloaded = False
        # 限制执行时并发，不裁剪排队请求；未配置时保持原生默认行为。
        scheduler_kwargs = {}
        for key, value in (('max_num_batched_tokens', max_num_batched_tokens),
                           ('max_num_seqs', max_num_seqs)):
            if value is not None:
                if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                    raise ValueError(f'{key} must be a positive integer')
                scheduler_kwargs[key] = value
        # 使用 V1 公开 processor 接口，不修改原生引擎或绕过正式解析器。
        if not isinstance(action_stop, bool):
            raise ValueError('action_stop must be boolean')
        if action_stop:
            scheduler_kwargs['logits_processors'] = [
                'verl.third_party.vllm.metax_v_0_11_0.action_stop:ActionBoundaryLogitsProcessor']
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
            **scheduler_kwargs,
        )
        self._sleeping = False
        # 冷加载的权重和缓存一致；同步期间置为无效，任何失败都禁止继续生成。
        self._weights_ready = True

    def offload_model_weights(self):
        """@brief 按显式配置卸载推理权重，为概率重算和训练释放GPU空间。
        @return 无。
        @raises RuntimeError 仍有未完成请求或CPU卸载RPC未全部成功时抛出。
        @note 默认不卸载；CPU模式保留同权重的KV缓存，禁止与sleep混用。
        """
        if self._cpu_offload_enabled:
            # 无请求时才搬移；重复退出不反复复制已经在CPU的权重。
            if not self._cpu_offloaded:
                if self.engine.llm_engine.has_unfinished_requests():
                    raise RuntimeError('Cannot offload weights with unfinished requests')
                result = self.engine.collective_rpc('offload_weights_to_cpu')
                if not result or any(item is not True for item in result):
                    self._weights_ready = False
                    raise RuntimeError('CPU weight offload RPC failed')
                self._cpu_offloaded = True
            return
        if not self._sleep_enabled:
            return
        # 历史sleep路径仅在已有显式环境开关下执行，保持旧行为。
        if not self._sleeping:
            self.engine.sleep(level=2)
            self._sleeping = True

    def _restore_cpu_weights(self):
        """@brief 在生成或同步之前恢复CPU上的推理权重并校验全部worker。
        @return 无。
        @raises RuntimeError 恢复RPC失败时抛出，并禁止继续生成。
        @note 同版本恢复不重置前缀缓存；失败状态只能通过完整同步解除。
        """
        if self._cpu_offloaded:
            result = self.engine.collective_rpc('restore_weights_from_cpu')
            # 仅全部成功才宣布GPU权重可用，部分恢复失败不得继续生成。
            if not result or any(item is not True for item in result):
                self._weights_ready = False
                raise RuntimeError('CPU weight restore RPC failed')
            self._cpu_offloaded = False

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
            # CPU卸载后先恢复设备，再加载新版本；之后沿用原缓存失效保护。
            self._restore_cpu_weights()
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

    def generate(self, prompts, sampling_params, prompt_token_ids, use_tqdm=False, return_metadata=False):
        """
        @brief 仅使用已同步且缓存一致的权重生成旧接口的 token 和概率张量。
        @param prompts 旧接口保留的文本提示；实际使用 token 输入。
        @param sampling_params 原生引擎采样参数。
        @param prompt_token_ids 每条请求的非 padding token 列表。
        @param use_tqdm 是否显示原生生成进度。
        @param return_metadata 是否追加原生终止及概率来源信息，默认关闭。
        @return 默认 token/logprob 二元组；开启诊断时追加逐候选元数据列表。
        @raises RuntimeError 引擎休眠、同步未完成或未返回生成结果时抛出。
        @note 同一权重版本内不清空前缀缓存，不改变采样和补齐语义。
        """
        if self._sleeping:
            raise RuntimeError('MetaX vLLM weights are sleeping; sync actor weights first')
        # 同步中断或缓存失败后拒绝旧/混合状态，不能依赖调用方一定退出。
        if not self._weights_ready:
            raise RuntimeError('MetaX vLLM weights and prefix cache are not ready; sync actor weights first')
        # 同版本设备恢复只搬移权重，不复用旧版本或重置已验证一致的KV。
        self._restore_cpu_weights()
        requests = [{'prompt_token_ids': ids} for ids in prompt_token_ids]
        outputs = self.engine.generate(requests, sampling_params=sampling_params, use_tqdm=use_tqdm)
        token_rows = []
        logprob_rows = []
        metadata = []
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
                if return_metadata:
                    # 概率缺失时旧接口仍回退零值，但审计明确区分真实原生概率和回退。
                    available = len(steps) == len(token_ids) and all(
                        token_id in steps[i] for i, token_id in enumerate(token_ids))
                    metadata.append(dict(finish_reason=getattr(completion, 'finish_reason', None),
                                         stop_reason=getattr(completion, 'stop_reason', None),
                                         raw_token_count=len(token_ids), logprobs_available=available,
                                         sampled_token_logprobs=logprob_rows[-1] if available else None))
        if not token_rows:
            raise RuntimeError('MetaX vLLM returned no completions')
        width = max(map(len, token_rows))
        responses = torch.full((len(token_rows), width), self.pad_token_id, dtype=torch.long)
        logprobs = torch.zeros((len(token_rows), width), dtype=torch.float32)
        # 仅在真实 token 区域填值，右侧补齐与概率张量保持相同形状。
        for row, (tokens, probs) in enumerate(zip(token_rows, logprob_rows)):
            responses[row, :len(tokens)] = torch.tensor(tokens, dtype=torch.long)
            logprobs[row, :len(probs)] = torch.tensor(probs, dtype=torch.float32)
        return (responses, logprobs, metadata) if return_metadata else (responses, logprobs)
