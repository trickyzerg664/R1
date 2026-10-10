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
Single Process Actor
"""

import itertools
from contextlib import nullcontext
from verl.utils.activation_offload import cpu_activation_offload
import math
from typing import Iterable, Tuple

import torch
from torch import nn
from torch.utils.checkpoint import checkpoint
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
from torch.distributed.fsdp.sharded_grad_scaler import ShardedGradScaler

from verl import DataProto
from verl.utils.torch_dtypes import PrecisionType
from verl.utils.fsdp_utils import load_fsdp_optimizer, offload_fsdp_optimizer
from verl.utils.debug.gpu_memory_trace import trace_gpu_memory
from verl.trainer.ppo import core_algos
from verl.workers.actor import BasePPOActor
from verl.utils.py_functional import append_to_dict
from verl.utils.torch_functional import logprobs_from_logits, masked_mean
from verl.utils.ulysses import ulysses_pad_and_slice_inputs, gather_outpus_and_unpad
from verl.utils.seqlen_balancing import rearrange_micro_batches, get_reverse_idx
import verl.utils.torch_functional as verl_F

from flash_attn.bert_padding import pad_input, unpad_input, rearrange, index_first_axis

__all__ = ['DataParallelPPOActor']


def forward_response_logits(model, response_length, response_logits_only=False, **model_inputs):
    """@brief 提取回答 logits，显式省显存时使用模型实际支持的 LM head 截断参数。
    @param model 因果模型或 FSDP 包装，不能截断其输入上下文。
    @param response_length 回答 token 长度。
    @param response_logits_only 是否只计算回答加前一位置的 LM head。
    @param model_inputs 原始完整上下文、attention mask、position ids 等模型参数。
    @return 批次乘回答长度乘词表的 logits。
    @raises ValueError 显式开启优化但模型不支持已知截断接口。
    @note FSDP 使用公开 module 检查实际签名；默认关闭时不检查或改变调用。
    """
    if response_logits_only:
        # 新版 Qwen2 使用 logits_to_keep；旧拼写可能被 **kwargs 吞掉，显存优化静默失效。
        import inspect
        forward_model = model.module if isinstance(model, FSDP) else model
        parameters = inspect.signature(forward_model.forward).parameters
        key = next((name for name in ('logits_to_keep', 'num_logits_to_keep') if name in parameters), None)
        if key is None:
            raise ValueError('Model does not explicitly support response-only logits')
        # 多保留一个预测位置，但仍传入完整因果上下文。
        model_inputs[key] = response_length + 1
    return model(**model_inputs).logits[:, -response_length - 1:-1]


def token_statistics(logits, responses, recompute=False, chunk_size=0, compute_entropy=True):
    """回答概率和熵；显式分块降低词表中间量峰值，概率推理可不计算熵。"""
    def calculate(logits, responses):
        log_probs = logprobs_from_logits(logits, responses)
        entropy = verl_F.entropy_from_logits(logits) if compute_entropy else torch.zeros_like(log_probs)
        return log_probs, entropy

    def evaluate(logits, responses):
        # 每块独立重算，仅保留必要的logits；保持原公式及token顺序。
        if recompute and torch.is_grad_enabled():
            return checkpoint(calculate, logits, responses, use_reentrant=False)
        return calculate(logits, responses)

    if chunk_size < 0:
        raise ValueError('token_statistics_chunk_size must be nonnegative')
    if chunk_size == 0:
        return evaluate(logits, responses)
    # 词表维度不截断，只沿token维度分块；输出仍为完整回答长度。
    parts = [evaluate(logits[:, i:i+chunk_size], responses[:, i:i+chunk_size])
             for i in range(0, responses.shape[-1], chunk_size)]
    return tuple(torch.cat([p[j] for p in parts], dim=1) for j in range(2))


class DataParallelPPOActor(BasePPOActor):

    def __init__(
        self,
        config,
        actor_module: nn.Module,
        actor_optimizer: torch.optim.Optimizer = None,
    ):
        """When optimizer is None, it is Reference Policy"""
        super().__init__(config)
        self.actor_module = actor_module
        self.actor_optimizer = actor_optimizer
        self.optimizer_offload = bool(self.config.get('fsdp_config', {}).get('optimizer_offload', False)) and actor_optimizer is not None
        precision = self.config.get('fsdp_config', {}).get('mixed_precision') or {}
        self.compute_dtype = PrecisionType.to_dtype(precision.get('param_dtype', 'fp16'))
        scale_gradients = self.compute_dtype == torch.float16 and actor_optimizer is not None
        # 7B 的长轨迹在默认 65536 loss scale 下可连续溢出；允许实验配置降低初值，默认行为不变。
        init_scale = float(self.config.get('fsdp_config', {}).get('grad_scaler_init_scale', 65536.0))
        if not math.isfinite(init_scale) or init_scale <= 0:
            raise ValueError('grad_scaler_init_scale must be a finite positive number')
        if isinstance(actor_module, FSDP):
            self.grad_scaler = ShardedGradScaler(enabled=scale_gradients, init_scale=init_scale,
                                                process_group=actor_module.process_group)
        else:
            self.grad_scaler = torch.amp.GradScaler('cuda', enabled=scale_gradients, init_scale=init_scale)
        self.use_remove_padding = self.config.get('use_remove_padding', False)
        print(f'Actor use_remove_padding={self.use_remove_padding}')
        self.ulysses_sequence_parallel_size = self.config.ulysses_sequence_parallel_size
        self.use_ulysses_sp = self.ulysses_sequence_parallel_size > 1

        self.compute_entropy_from_logits = torch.compile(verl_F.entropy_from_logits, dynamic=True)

    def _forward_micro_batch(self, micro_batch, temperature) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns: 
            entropy: # (bs, response_len)
            log_probs: # (bs, response_len)
        """
        response_length = micro_batch['responses'].size(-1)
        with torch.autocast(device_type='cuda', dtype=self.compute_dtype):
            input_ids = micro_batch['input_ids']
            batch_size, seqlen = input_ids.shape
            attention_mask = micro_batch['attention_mask']
            position_ids = micro_batch['position_ids']

            if self.use_remove_padding:
                input_ids_rmpad, indices, *_ = unpad_input(input_ids.unsqueeze(-1),
                                                           attention_mask)  # input_ids_rmpad (total_nnz, ...)
                input_ids_rmpad = input_ids_rmpad.transpose(0, 1)  # (1, total_nnz)

                # unpad the position_ids to align the rotary
                position_ids_rmpad = index_first_axis(rearrange(position_ids.unsqueeze(-1), "b s ... -> (b s) ..."),
                                                      indices).transpose(0, 1)

                # for compute the log_prob
                input_ids_rmpad_rolled = torch.roll(input_ids_rmpad, shifts=-1, dims=1)  # (1, total_nnz)

                # pad and slice the inputs if sp > 1
                if self.use_ulysses_sp:
                    input_ids_rmpad, position_ids_rmpad, pad_size = ulysses_pad_and_slice_inputs(input_ids_rmpad, \
                                                                                                position_ids_rmpad, \
                                                                                                sp_size=self.ulysses_sequence_parallel_size)
                    input_ids_rmpad_rolled, _, _ = ulysses_pad_and_slice_inputs(input_ids_rmpad_rolled, None,
                                                                                self.ulysses_sequence_parallel_size)

                input_ids_rmpad_rolled = input_ids_rmpad_rolled.squeeze(0)  # ((total_nnz / sp) + pad)

                # only pass input_ids and position_ids to enable flash_attn_varlen
                output = self.actor_module(input_ids=input_ids_rmpad,
                                           attention_mask=None,
                                           position_ids=position_ids_rmpad,
                                           use_cache=False)  # prevent model thinks we are generating
                logits_rmpad = output.logits.squeeze(0).float()  # (total_nnz, vocab_size)

                logits_rmpad.div_(temperature)

                # compute entropy
                entropy_rmpad = self.compute_entropy_from_logits(logits_rmpad)  # ((total_nnz / sp) + pad)

                # if use_sp: ((total_nnz / sp) + pad) ; if not use_sp: (batch, seqlen)
                log_probs = logprobs_from_logits(logits=logits_rmpad, labels=input_ids_rmpad_rolled)

                # gather log_prob if sp > 1
                if self.use_ulysses_sp:
                    # gather and unpad for the ulysses sp
                    log_probs = gather_outpus_and_unpad(log_probs, gather_dim=0, unpad_dim=0, padding_size=pad_size)
                    entropy_rmpad = gather_outpus_and_unpad(entropy_rmpad,
                                                            gather_dim=0,
                                                            unpad_dim=0,
                                                            padding_size=pad_size)
                # pad back to (bsz, seqlen)
                full_entropy = pad_input(hidden_states=entropy_rmpad.unsqueeze(-1),
                                         indices=indices,
                                         batch=batch_size,
                                         seqlen=seqlen)
                full_log_probs = pad_input(hidden_states=log_probs.unsqueeze(-1),
                                           indices=indices,
                                           batch=batch_size,
                                           seqlen=seqlen)

                # only return response part:
                entropy = full_entropy.squeeze(-1)[:, -response_length - 1:-1]  # (bsz, response_length)
                log_probs = full_log_probs.squeeze(-1)[:, -response_length - 1:-1]  # (bsz, response_length)

            else:  # not using rmpad and no ulysses sp
                # [data-difficulty] 省显存路径必须显式开启；默认保留原有全段 logits 顺序以兼容旧评分前缀。
                if self.config.get('response_logits_only', False):
                    logits = forward_response_logits(
                        self.actor_module, response_length, True,
                        input_ids=input_ids, attention_mask=attention_mask,
                        position_ids=position_ids, use_cache=False).float()
                    logits.div_(temperature)
                else:
                    output = self.actor_module(input_ids=input_ids,
                                               attention_mask=attention_mask,
                                               position_ids=position_ids,
                                               use_cache=False)
                    logits = output.logits.float()
                    logits.div_(temperature)
                    logits = logits[:, -response_length - 1:-1]
                log_probs, entropy = token_statistics(
                    logits, micro_batch['responses'],
                    recompute=self.config.get('checkpoint_token_statistics', False),
                    chunk_size=self.config.get('token_statistics_chunk_size', 0),
                    # 概率推理只使用log_probs；开关显式启用时跳过未使用的熵。
                    compute_entropy=not (self.config.get('token_statistics_chunk_size', 0)
                                         and not torch.is_grad_enabled()))

            return entropy, log_probs

    def _optimizer_step(self):
        """@brief 按原精度裁剪梯度并更新Adam，可选记录状态显存。
        @return 梯度范数及是否实际完成更新的布尔值。
        @raises FloatingPointError 未启用缩放时梯度范数非有限，拒绝更新。
        @note 反传后才装入Adam状态，finally卸回CPU；全局非有限范数触发一致跳步。
        """
        trace_gpu_memory('optimizer_before_load', self.config.get('memory_diagnostics', False),
                         optimizer=self.actor_optimizer)
        assert self.config.grad_clip is not None
        self.grad_scaler.unscale_(self.actor_optimizer)

        if isinstance(self.actor_module, FSDP):
            grad_norm = self.actor_module.clip_grad_norm_(max_norm=self.config.grad_clip)
        else:
            grad_norm = torch.nn.utils.clip_grad_norm_(self.actor_module.parameters(), max_norm=self.config.grad_clip)
        # 非有限全局范数不得进入 Adam；FSDP 各 rank 使用相同全局范数作决定。
        # 即便单个梯度有限，范数求和也可能溢出，不能只依赖 GradScaler 的逐元素检查。
        if not torch.isfinite(grad_norm).item():
            self.actor_optimizer.zero_grad(set_to_none=True)
            if self.grad_scaler.is_enabled():
                # 公开 update API 同时回退缩放并清理本轮缓存，完全不调用 optimizer.step。
                self.grad_scaler.update(new_scale=self.grad_scaler.get_scale() * self.grad_scaler.get_backoff_factor())
                return grad_norm, False
            raise FloatingPointError('Nonfinite gradient norm; optimizer step refused')
        # 优化器状态只在反传完成后搬入 GPU，避免 Adam 状态与激活同时占用显存。
        optimizer_loaded = False
        if getattr(self, 'optimizer_offload', False) and torch.isfinite(grad_norm).item():
            torch.cuda.empty_cache()
            load_fsdp_optimizer(optimizer=self.actor_optimizer, device_id=torch.cuda.current_device())
            optimizer_loaded = True
        trace_gpu_memory('optimizer_before_step', self.config.get('memory_diagnostics', False),
                         optimizer=self.actor_optimizer)
        try:
            # GradScaler 在溢出时静默跳过 optimizer.step；缩放值回退是本 mini-batch 跳步的判据。
            previous_scale = self.grad_scaler.get_scale() if self.grad_scaler.is_enabled() else None
            self.grad_scaler.step(self.actor_optimizer)
            self.grad_scaler.update()
            updated = previous_scale is None or self.grad_scaler.get_scale() >= previous_scale
            return grad_norm, updated
        finally:
            if optimizer_loaded:
                offload_fsdp_optimizer(optimizer=self.actor_optimizer)
            trace_gpu_memory('optimizer_after_offload', self.config.get('memory_diagnostics', False),
                             optimizer=self.actor_optimizer)

    def compute_log_prob(self, data: DataProto) -> torch.Tensor:
        """Compute the log probability of the responses given input_ids, attention_mask and position_ids

        Args:
            data (DataProto): a DataProto containing keys

                ``input_ids``: tensor of shape [batch_size, sequence_length]. torch.int64. Note that input_ids is the
                concatenation of prompt and response. Note that ``sequence_length = prompt_length + response_length``.

                ``attention_mask``: tensor of shape [batch_size, sequence_length]. torch.int64.

                ``position_ids``: tensor of shape [batch_size, sequence_length]. torch.int64.

                ``responses``:  tensor of shape [batch_size, response_length]. torch.int64.

        Returns:
            torch.Tensor: the log_prob tensor
        """
        # set to eval
        self.actor_module.eval()

        micro_batch_size = data.meta_info['micro_batch_size']
        temperature = data.meta_info['temperature']  # temperature must be in the data.meta_info to avoid slient error
        use_dynamic_bsz = data.meta_info['use_dynamic_bsz']

        select_keys = ['responses', 'input_ids', 'attention_mask', 'position_ids']
        batch = data.select(batch_keys=select_keys).batch

        if use_dynamic_bsz:
            # split using dynamic bsz
            max_token_len = data.meta_info['max_token_len'] * self.ulysses_sequence_parallel_size
            micro_batches, indices = rearrange_micro_batches(batch=batch, max_token_len=max_token_len)
        else:
            micro_batches = batch.split(micro_batch_size)

        log_probs_lst = []
        for micro_batch in micro_batches:
            with torch.no_grad():
                _, log_probs = self._forward_micro_batch(micro_batch, temperature=temperature)
            log_probs_lst.append(log_probs)
        log_probs = torch.concat(log_probs_lst, dim=0)

        if use_dynamic_bsz:
            indices = list(itertools.chain.from_iterable(indices))
            assert len(indices) == log_probs.size(0), f"{len(indices)} vs. {log_probs.size()}"
            revert_indices = torch.tensor(get_reverse_idx(indices), dtype=torch.long)
            log_probs = log_probs[revert_indices]

        return log_probs

    def update_policy(self, data: DataProto):
        """@brief 原批次及梯度累积更新策略，可选将反传保存的同精度激活搬至CPU。
        @param data 完整DataProto，含完整上下文、回答、掩码、优势、旧及参考概率。
        @return 原指标及显式开启的只读稳定性诊断映射。
        @note 输出端分量梯度不代表完整参数梯度；固定轨迹探针额外前向，默认关闭。
        @raises FloatingPointError 损失非有限时拒绝反传。
        @raises ValueError 固定概率探针遇到非零 dropout 时拒绝执行。
        @note activation_offload默认关闭；开启不裁剪token或改变损失计算顺序。
        """
        # make sure we are in training mode
        self.actor_module.train()

        assert self.config.ppo_mini_batch_size % self.config.ppo_micro_batch_size == 0
        self.gradient_accumulation = self.config.ppo_mini_batch_size // self.config.ppo_micro_batch_size
        temperature = data.meta_info['temperature']  # temperature must be in the data.meta_info to avoid slient error

        select_keys = ['responses', 'input_ids', 'attention_mask', 'position_ids', 'old_log_probs', 'advantages']
        if self.config.state_masking:
            select_keys.append('loss_mask')
        if self.config.use_kl_loss:
            select_keys.append('ref_log_prob')
        batch = data.select(batch_keys=select_keys).batch

        # Split to make minibatch iterator for updating the actor
        # See PPO paper for details. https://arxiv.org/abs/1707.06347
        dataloader = batch.split(self.config.ppo_mini_batch_size)

        from verl.experimental.stability.diagnostics import (
            token_diagnostics, score_gradient_diagnostics, sample_parameter_values,
            parameter_update_diagnostics, likelihood_change_diagnostics)
        diagnostics_config = self.config.get('stability_diagnostics', {})
        diagnostics_enabled = bool(diagnostics_config.get('enabled', False))
        probe_enabled = diagnostics_enabled and bool(diagnostics_config.get('probe_after_update', False))
        if probe_enabled:
            # 前值来自训练前向、后值在 eval 读取；非零 dropout 会混入随机差异，不能作为概率位移证据。
            dropout_present = any(
                (isinstance(module, nn.Dropout) and module.p > 0)
                or float(getattr(module, 'attention_dropout', 0.) or 0.) > 0
                for module in self.actor_module.modules())
            if dropout_present:
                raise ValueError('Fixed likelihood probe requires zero dropout')
        metrics = {}
        for batch_idx, data in enumerate(dataloader):
            probe = None
            # split batch into micro_batches
            mini_batch = data
            if self.config.use_dynamic_bsz:
                max_token_len = self.config.ppo_max_token_len_per_gpu * self.ulysses_sequence_parallel_size
                micro_batches, _ = rearrange_micro_batches(batch=mini_batch, max_token_len=max_token_len)
            else:
                # split batch into micro_batches
                micro_batches = mini_batch.split(self.config.ppo_micro_batch_size)

            self.actor_optimizer.zero_grad()

            for micro_index, data in enumerate(micro_batches):
                data = data.cuda()  # actor device is cpu when using offload
                responses = data['responses']
                response_length = responses.size(1)
                attention_mask = data['attention_mask']
                response_mask = attention_mask[:, -response_length:]
                if self.config.state_masking:
                    response_mask = data['loss_mask']
                old_log_prob = data['old_log_probs']
                advantages = data['advantages']

                clip_ratio = self.config.clip_ratio
                entropy_coeff = self.config.entropy_coeff

                # 不改dtype或完整轨迹，仅搬移浮点反传张量；整数索引保留原设备和stride。
                # checkpoint重算和微批梯度累积顺序保持不变，关闭走旧路径。
                activation_context = (cpu_activation_offload(True)
                                      if self.config.get('activation_offload', False) else nullcontext())
                if micro_index in (0, len(micro_batches) - 1):
                    trace_gpu_memory('actor_micro_before', self.config.get('memory_diagnostics', False), data)
                with activation_context:
                    # all return: (bsz, response_length)
                    entropy, log_prob = self._forward_micro_batch(micro_batch=data, temperature=temperature)

                    safe_loss = self.config.get('loss_numerics', 'legacy') == 'safe_v1'
                    if safe_loss:
                        from verl.experimental.difficulty.loss_safety import policy_loss, kl_loss as safe_kl_loss, entropy_loss as safe_entropy_loss
                        pg_loss, pg_clipfrac, ppo_kl, safety_metrics = policy_loss(old_log_prob, log_prob, advantages, response_mask, clip_ratio)
                        append_to_dict(metrics, safety_metrics)
                    else:
                        pg_loss, pg_clipfrac, ppo_kl = core_algos.compute_policy_loss(old_log_prob=old_log_prob,
                                                                                  log_prob=log_prob,
                                                                                  advantages=advantages,
                                                                                  eos_mask=response_mask,
                                                                                  cliprange=clip_ratio)
                    # compute entropy loss from entropy
                    entropy_loss = safe_entropy_loss(entropy, response_mask) if safe_loss else verl_F.masked_mean(entropy, response_mask)

                    # compute policy loss
                    policy_loss = pg_loss - entropy_loss * entropy_coeff

                    if self.config.use_kl_loss:
                        ref_log_prob = data['ref_log_prob']
                        # compute kl loss
                        if safe_loss:
                            kl_loss, safety_metrics = safe_kl_loss(log_prob, ref_log_prob, response_mask)
                            append_to_dict(metrics, safety_metrics)
                        else:
                            kld = core_algos.kl_penalty(logprob=log_prob, ref_logprob=ref_log_prob,
                                                      kl_penalty=self.config.kl_loss_type)
                            kl_loss = masked_mean(kld, response_mask)

                        policy_loss = policy_loss + kl_loss * self.config.kl_loss_coef
                        # 保存全部微批，避免均值只有最后一条轨迹；不改变旧模式的实际损失。
                        append_to_dict(metrics, {'actor/kl_loss': kl_loss.detach().item(), 'actor/kl_coef': self.config.kl_loss_coef})

                    # 诊断默认关闭，开启时只观察原损失；分量梯度仅在每个 mini 的首微批计算。
                    if diagnostics_enabled:
                        append_to_dict(metrics, token_diagnostics(log_prob, old_log_prob, advantages, response_mask))
                        if micro_index == 0:
                            components = {'pg': pg_loss / self.gradient_accumulation,
                                          'entropy': -entropy_coeff * entropy_loss / self.gradient_accumulation}
                            if self.config.use_kl_loss:
                                components['kl'] = self.config.kl_loss_coef * kl_loss / self.gradient_accumulation
                            append_to_dict(metrics, score_gradient_diagnostics(components, log_prob, entropy))
                            if probe_enabled:
                                # 硬限制一条固定轨迹，复制以免后续微批释放或改写其存储。
                                probe = ({key: data[key][:1].detach().clone()
                                          for key in ('responses', 'input_ids', 'attention_mask', 'position_ids')},
                                         log_prob[:1].detach().clone(), response_mask[:1].detach().clone())
                    loss = policy_loss / self.gradient_accumulation
                    if safe_loss and not torch.isfinite(loss).all():
                        raise FloatingPointError('Nonfinite policy loss before backward')
                    self.grad_scaler.scale(loss).backward()

                if micro_index in (0, len(micro_batches) - 1):
                    trace_gpu_memory('actor_micro_after_backward', self.config.get('memory_diagnostics', False), data)

                data = {
                    'actor/entropy_loss': entropy_loss.detach().item(),
                    'actor/pg_loss': pg_loss.detach().item(),
                    'actor/pg_clipfrac': pg_clipfrac.detach().item(),
                    'actor/ppo_kl': ppo_kl.detach().item(),
                }
                append_to_dict(metrics, data)

            # 参数变化是固定少量本地样本；禁止为诊断复制完整参数。
            sample_limit = diagnostics_config.get('parameter_sample_size', 256)
            before_parameters = (sample_parameter_values(self.actor_module.parameters(), sample_limit)
                                 if diagnostics_enabled else None)
            grad_norm, updated = self._optimizer_step()
            if diagnostics_enabled:
                after_parameters = sample_parameter_values(self.actor_module.parameters(), sample_limit)
                append_to_dict(metrics, parameter_update_diagnostics(before_parameters, after_parameters))
            if probe is not None and updated:
                # 更新后使用相同 token、上下文和温度；暂时 eval 防止 dropout 给探针引入随机变化。
                was_training = self.actor_module.training
                try:
                    self.actor_module.eval()
                    with torch.no_grad():
                        _, after_log_prob = self._forward_micro_batch(probe[0], temperature)
                    append_to_dict(metrics, likelihood_change_diagnostics(probe[1], after_log_prob, probe[2]))
                finally:
                    self.actor_module.train(was_training)
            data = {'actor/grad_norm': grad_norm.detach().item(),
                    'actor/optimizer_step': int(updated),
                    'actor/grad_scaler_scale': self.grad_scaler.get_scale()}
            append_to_dict(metrics, data)
        # 旧 optimizer_step 是更新成功比例，不是更新次数；新增每 rank 的实际计数避免误读。
        attempts = len(metrics.get('actor/optimizer_step', []))
        updates = sum(metrics.get('actor/optimizer_step', []))
        append_to_dict(metrics, {'actor/optimizer_attempts_per_rank': attempts,
                                 'actor/optimizer_updates_per_rank': updates,
                                 'actor/optimizer_skips_per_rank': attempts - updates})
        self.actor_optimizer.zero_grad()
        return metrics
