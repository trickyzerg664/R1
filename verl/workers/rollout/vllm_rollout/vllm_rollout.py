# Copyright 2024 Bytedance Ltd. and/or its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
The vllm_rollout that can be applied in different backend
When working with FSDP:
- Use DTensor weight loader (recommended) or HF weight loader
- Utilize state_dict from the FSDP to synchronize the weights among tp ranks in vLLM
When working with Megatron:
- Use Megatron weight loader
- During training, only the current pp stage holds the parameters
- Before inference, broadcast the parameters of the current pp rank to all other pp ranks (all pp ranks holds all the parameters)
- Bind the parameters to the inference engine
- Do inference in tp. pp is treated as additional dp
- After inference, all the parameters that doesn't belong to this pp rank is freed.
"""
from typing import List
from contextlib import contextmanager
from omegaconf import DictConfig
import torch
import numpy as np
import torch.distributed
from tensordict import TensorDict
from torch import nn

from verl import DataProto
from verl.utils.torch_functional import get_eos_mask, pad_sequence_to_length
from verl.workers.rollout.base import BaseRollout
from verl.third_party.vllm import LLM, vllm_version
from verl.third_party.vllm import parallel_state as vllm_ps
from vllm import SamplingParams

# TODO
# 1. support pp in vllm
# 2. passing tokenizer is not necessary? no encoding/decoding is happending here
# 3. simplify init logics


# NOTE(sgm): add for verl. We can optimize it by making the dataloader yield List[int] without padding.
def _pre_process_inputs(pad_token_id, prompt_token_ids: torch.Tensor) -> List[int]:
    # remove the left padding in the prompt token_id
    # pad_token_id = self.llm_engine.tokenizer.pad_token_id if self.llm_engine.tokenizer.pad_token_id is not None else self.llm_engine.tokenizer.eos_token_id
    non_pad_index = torch.nonzero(prompt_token_ids != pad_token_id, as_tuple=False)[0][0]
    token_ids = prompt_token_ids[non_pad_index:].tolist()
    return token_ids


class vLLMRollout(BaseRollout):

    def __init__(self, actor_module: nn.Module, config: DictConfig, tokenizer, model_hf_config, **kwargs):
        """
        @brief 构建复用训练模型的生成器，并把显式调度预算传入 MetaX 引擎。
        @param actor_module 支持 vLLM 的训练模型实例。
        @param config 生成、采样及执行资源配置，不减少待生成请求数。
        @param tokenizer 模型分词器及 pad/eos 标识。
        @param model_hf_config 模型上下文长度及加载配置。
        @param kwargs 可选 train_tp 等并行初始化参数。
        @return 无。
        @raises AssertionError 缓存模式、并行数或上下文长度不满足约束时抛出。
        @note 仅 MetaX 0.11 路径接收新调度预算，其余版本保留已有参数行为。
        """
        super().__init__()
        self.config = config
        # 缓存释放与图捕获不兼容，初始化时拒绝无效组合。
        assert not (not config.enforce_eager and config.free_cache_engine), \
            "disable CUDA graph (enforce_eager = False) if free cache engine"

        tensor_parallel_size = self.config.get('tensor_model_parallel_size', 1)
        assert tensor_parallel_size <= torch.distributed.get_world_size(), \
            "tensor parallel size should be less than or equal to the world size"

        # Megatron 仍复用原并行状态初始化；调度预算不改变进程拓扑。
        if kwargs.get('train_tp', None) is not None:
            # deployed with megatron
            import os
            os.environ['CUDA_TIMER_STREAM_KAFKA_ENABLE'] = '0'
            os.environ['MEGATRON_IMPORT_TIMERS'] = '0'
            train_tp = kwargs.get('train_tp', None)
            num_tp_per_train_tp = train_tp // tensor_parallel_size
            if vllm_version in ('0.4.2', '0.5.4', '0.6.3'):
                vllm_ps.initialize_parallel_state(tensor_model_parallel_size=tensor_parallel_size,
                                                  num_tp_per_train_tp=num_tp_per_train_tp)

        # 完整提示加响应长度必须受模型支持，不能为显存验证缩短上下文。
        assert model_hf_config.max_position_embeddings >= config.prompt_length + config.response_length, \
            "model context length should be greater than total sequence length"
        # 仅接通已验证支持此接口的 MetaX 路径；缺省值仍交给原生引擎。
        scheduler_kwargs = {}
        if vllm_version == '0.11.0':
            for key in ('max_num_batched_tokens', 'max_num_seqs', 'offload_weights_to_cpu'):
                if config.get(key) is not None:
                    scheduler_kwargs[key] = config.get(key)
        self.inference_engine = LLM(actor_module,
                                    tokenizer=tokenizer,
                                    model_hf_config=model_hf_config,
                                    tensor_parallel_size=tensor_parallel_size,
                                    dtype=config.dtype,
                                    enforce_eager=config.enforce_eager,
                                    gpu_memory_utilization=config.gpu_memory_utilization,
                                    skip_tokenizer_init=False,
                                    max_model_len=config.prompt_length + config.response_length,
                                    load_format=config.load_format,
                                    **scheduler_kwargs)

        # Offload vllm model to reduce peak memory usage
        self.inference_engine.offload_model_weights()

        kwargs = dict(
            n=1,
            logprobs=1,  # can be set to 0 and let actor to recompute
            max_tokens=config.response_length,
        )

        # we may detokenize the result all together later
        if vllm_version in ('0.4.2', '0.5.4', '0.6.3', '0.11.0'):
            # 沐曦路径只需要 token IDs；关闭额外解码以保持旧输出语义。
            kwargs['detokenize'] = False

        # supporting adding any sampling params from the config file
        # 仅采样器支持的键用于采样，调度预算不会改变温度或回答条数。
        for k in config.keys():
            if hasattr(SamplingParams(), str(k)):
                kwargs[k] = config.get(k)

        print(f"kwargs: {kwargs}")
        self.sampling_params = SamplingParams(**kwargs)

        self.pad_token_id = tokenizer.pad_token_id

    @contextmanager
    def update_sampling_params(self, **kwargs):
        # update sampling params
        old_sampling_params_args = {}
        if kwargs:
            for key, value in kwargs.items():
                if hasattr(self.sampling_params, key):
                    old_value = getattr(self.sampling_params, key)
                    old_sampling_params_args[key] = old_value
                    setattr(self.sampling_params, key, value)
        # [data-difficulty] 生成异常后也恢复采样参数，避免后续评分设置泄漏。
        try:
            yield
        finally:
            for key, value in old_sampling_params_args.items():
                setattr(self.sampling_params, key, value)

    @torch.no_grad()
    def generate_sequences(self, prompts: DataProto, **kwargs) -> DataProto:
        """@brief 复用原生成流程，可选传递 MetaX 原生终止元数据。
        @param prompts 原提示、mask、生成参数及可选只读审计开关。
        @param kwargs 原采样参数覆盖。
        @return 原生成 DataProto；开启且后端支持时含逐行终止信息。
        @raises ValueError 原生元数据数量与真实候选数量不匹配。
        @note 默认返回结构和采样参数不变，其他后端不伪造终止原因。
        """
        # rebuild vllm cache engine
        if self.config.free_cache_engine:
            self.inference_engine.init_cache_engine()

        idx = prompts.batch['input_ids']  # (bs, prompt_length)
        # left-padded attention_mask
        attention_mask = prompts.batch['attention_mask']
        position_ids = prompts.batch['position_ids']

        # used to construct attention_mask
        eos_token_id = prompts.meta_info['eos_token_id']

        batch_size = idx.size(0)

        idx_list = []
        # parse idx from torch.Tensor to List[List[str]]
        for i in range(batch_size):
            idx_list.append(_pre_process_inputs(self.pad_token_id, idx[i]))

        do_sample = prompts.meta_info.get('do_sample', True)
        if not do_sample:
            kwargs = {
                'best_of': 1,
                'top_p': 1.0,
                'top_k': -1,
                'min_p': 0.0,
                'temperature': 0,
                'n': 1  # if greedy, only 1 response
            }

        # users can customize different sampling_params at different run
        with self.update_sampling_params(**kwargs):
            # [data-difficulty] 每条请求独立 SamplingParams，四条轨迹不能共用同一 seed。
            from verl.experimental.difficulty.generation import request_sampling_params
            sampling_params = request_sampling_params(self.sampling_params, prompts.non_tensor_batch.get('rollout_seed'),
                                                       prompts.meta_info.get('sampling_round', 0), len(idx_list))
            # 审计选项属于适配层，不传入 SamplingParams；仅已支持的 MetaX 接口接收。
            metadata_options = ({'return_metadata': True}
                                if prompts.meta_info.get('record_rollout_metadata', False)
                                and vllm_version == '0.11.0' else {})
            output = self.inference_engine.generate(
                prompts=None,  # because we have already convert it to prompt token id
                sampling_params=sampling_params,
                prompt_token_ids=idx_list,
                use_tqdm=False, **metadata_options)

        # TODO(sgm): disable logprob when recompute_log_prob is enable
        # if n = 1: (bs, response_length) ; if n > 1: (bs * n, response_length)
        response = output[0].to(idx.device)
        log_probs = output[1].to(idx.device)

        if response.shape[1] < self.config.response_length:
            response = pad_sequence_to_length(response, self.config.response_length, self.pad_token_id)
            log_probs = pad_sequence_to_length(log_probs, self.config.response_length, self.pad_token_id)

        if self.config.n > 1 and do_sample:
            idx = idx.repeat_interleave(self.config.n, dim=0)
            attention_mask = attention_mask.repeat_interleave(self.config.n, dim=0)
            position_ids = position_ids.repeat_interleave(self.config.n, dim=0)
            batch_size = batch_size * self.config.n
        seq = torch.cat([idx, response], dim=-1)

        response_length = response.size(1)
        delta_position_id = torch.arange(1, response_length + 1, device=position_ids.device)
        delta_position_id = delta_position_id.unsqueeze(0).repeat(batch_size, 1)

        # TODO(sgm): fix position_ids on right_pad
        # prompt: left pad + response: right pad
        # attention_mask: [0,0,0,0,1,1,1,1, | 1,1,1,0,0,0,0,0]
        # position_ids:   [0,0,0,0,0,1,2,3, | 4,5,6,7,8,9,10,11]
        response_position_ids = position_ids[:, -1:] + delta_position_id
        position_ids = torch.cat([position_ids, response_position_ids], dim=-1)
        response_attention_mask = get_eos_mask(response_id=response, eos_token=eos_token_id, dtype=attention_mask.dtype)
        attention_mask = torch.cat((attention_mask, response_attention_mask), dim=-1)

        # all the tp ranks should contain the same data here. data in all ranks are valid
        batch = TensorDict(
            {
                'prompts': idx,
                'responses': response,
                'input_ids': seq,  # here input_ids become the whole sentences
                # 'old_log_probs': log_probs, # we will recompute old log prob with actor
                'attention_mask': attention_mask,
                'position_ids': position_ids
            },
            batch_size=batch_size)

        # free vllm cache engine
        if self.config.free_cache_engine:
            self.inference_engine.free_cache_engine()

        non_tensors = {}
        if len(output) > 2:
            if len(output[2]) != batch_size:
                raise ValueError('Rollout metadata candidate count differs')
            # 随行对象数组由 DataProto 分片/还原，避免批级元信息丢失候选身份。
            metadata = np.empty(batch_size, dtype=object)
            metadata[:] = output[2]
            non_tensors['rollout_metadata'] = metadata
        return DataProto(batch=batch, non_tensor_batch=non_tensors)
