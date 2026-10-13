"""通过 vLLM V1 公开扩展接口在合法动作完成后仅生成 EOS。"""
from dataclasses import dataclass
import torch
from vllm.v1.sample.logits_processor.interface import LogitsProcessor, MoveDirectionality
from vllm.transformers_utils.tokenizer import get_tokenizer
from verl.experimental.process_checks.action_stop import action_complete

EXTRA_KEY = 'search_r1_action_stop_v1'


@dataclass
class RequestState:
    """只保留公开接口提供的当前输出列表与 EOS，不持有训练器状态。"""
    tokens: list
    eos: int
    complete: bool = False


class ActionBoundaryLogitsProcessor(LogitsProcessor):
    def __init__(self, vllm_config, device, is_pin_memory):
        """@brief 使用当前模型分词器构建逐请求的动作停止状态。
        @param vllm_config 原生模型配置，仅读取分词器身份。
        @param device 原生接口传入的设备，本实现不另建 GPU 张量。
        @param is_pin_memory 原生接口内存选项，本实现无需额外 pinned memory。
        @return 无。
        """
        model = vllm_config.model_config
        # 与原生引擎使用相同分词器；不重编码已经采样的 token。
        self.tokenizer = get_tokenizer(model.tokenizer, tokenizer_mode=model.tokenizer_mode,
            trust_remote_code=model.trust_remote_code, revision=model.tokenizer_revision)
        self.requests = {}

    def is_argmax_invariant(self):
        """@brief 声明 EOS 收尾会改变下一 token 的 argmax，贪心与采样均需调用。
        @return False。
        """
        return False

    def update_state(self, batch_update):
        """@brief 按公开批次更新协议处理请求移除、加入及位置变化。
        @param batch_update 批次变化对象，可为空；输出列表由引擎持续更新。
        @return 无。
        @raises ValueError 请求指定的 EOS 非法。
        """
        if batch_update is None:
            return
        # 官方约定顺序为 removed、added、moved；禁用请求也必须清除同槽旧状态。
        for index in batch_update.removed:
            self.requests.pop(index, None)
        for index, params, prompt_tokens, output_tokens in batch_update.added:
            self.requests.pop(index, None)
            extra = params.extra_args or {}
            if extra.get(EXTRA_KEY) is True:
                eos = extra.get('search_r1_action_eos')
                if isinstance(eos, bool) or not isinstance(eos, int) or eos < 0:
                    raise ValueError('Action boundary stop requires a valid EOS token')
                self.requests[index] = RequestState(output_tokens, eos)
        for old, new, direction in batch_update.moved:
            left = self.requests.pop(old, None)
            # 移动的是公开 batch 槽位，不能按请求排序猜测对应关系。
            if direction == MoveDirectionality.SWAP:
                right = self.requests.pop(new, None)
                if right is not None:
                    self.requests[old] = right
            else:
                self.requests.pop(new, None)
            if left is not None:
                self.requests[new] = left

    def apply(self, logits):
        """@brief 完整合法动作之前保持所有 logits 原值，之后只允许 EOS。
        @param logits 原生批次的二维词表 logits，原位处理并返回。
        @return 原 logits 张量；已生成的动作 token 与概率完全保留。
        @raises ValueError EOS 超出词表范围。
        @note 收尾 EOS 不属于消费动作，现有前缀提取及损失掩码会将其排除。
        """
        for index, state in self.requests.items():
            if not state.complete and state.tokens:
                # 只有刚生成的 token 含右括号才可能闭合标签，避免每步整段解码。
                last = self.tokenizer.decode(state.tokens[-1:], skip_special_tokens=True)
                if '>' in last:
                    text = self.tokenizer.decode(state.tokens, skip_special_tokens=True)
                    state.complete = action_complete(text)
            if state.complete:
                if state.eos >= logits.shape[-1]:
                    raise ValueError('Action stop EOS exceeds vocabulary')
                # 仅修改动作完成后的额外收尾位置，不修改正常动作采样分布。
                logits[index].fill_(-torch.inf)
                logits[index, state.eos] = 0
        return logits
