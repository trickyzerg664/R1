"""生成 token 审计只观察原流程，不改变消费边界、EOS 或重分词。"""


def token_alignment_report(raw_ids, processed_ids, tokenizer, max_tokens, backend=None):
    """@brief 对比实际生成和进入训练的 token 前缀及终止证据。
    @param raw_ids 单条生成 token 列表，允许右侧 padding。
    @param processed_ids 单条消费文本重分词后的 token 列表。
    @param tokenizer 实际分词器，提供 decode、pad_token_id 和可选 eos_token_id。
    @param max_tokens 本轮实际 token 上限。
    @param backend 可选原生终止信息，不将推断结果写成原生 finish_reason。
    @return 可 JSON 序列化的原始/消费 token、概率来源、边界及终止报告。
    @note 允许合法动作之后存在未消费尾部；不把尾部删除等同于重分词错误。
    """
    raw, processed = list(map(int, raw_ids)), list(map(int, processed_ids))
    # 仅移除右补齐，保留内部特殊 token；pad 与 eos 相同的后端需要原生长度。
    native = dict(backend or {})
    native_length = native.get('raw_token_count')
    if native_length is not None:
        raw = raw[:native_length]
    else:
        while raw and raw[-1] == tokenizer.pad_token_id:
            raw.pop()
    while processed and processed[-1] == tokenizer.pad_token_id:
        processed.pop()
    raw_text = tokenizer.decode(raw, skip_special_tokens=True)
    processed_text = tokenizer.decode(processed, skip_special_tokens=True)
    # 前缀一致允许删掉未执行尾部；文本相同但 token 前缀不同才提示重分词歧义。
    token_prefix = raw[:len(processed)] == processed
    text_prefix = raw_text.startswith(processed_text)
    eos = getattr(tokenizer, 'eos_token_id', None)
    eos_ids = set(eos if isinstance(eos, (list, tuple)) else [eos]) if eos is not None else set()
    eos_observed = bool(eos_ids.intersection(raw))
    return dict(raw_token_ids=raw, processed_token_ids=processed,
                raw_token_count=len(raw), processed_token_count=len(processed),
                token_prefix_matches=token_prefix, text_prefix_matches=text_prefix,
                retokenized_prefix=bool(text_prefix and not token_prefix),
                eos_observed=eos_observed,
                eos_removed=bool(eos_observed and not eos_ids.intersection(processed)),
                token_limit_reached=len(raw) >= max_tokens,
                finish_reason=native.get('finish_reason'), stop_reason=native.get('stop_reason'),
                termination_evidence='eos_observed' if eos_observed else
                    'token_limit_reached' if len(raw) >= max_tokens else 'unknown',
                sampled_logprobs_available=bool(native.get('logprobs_available', False)),
                sampled_token_logprobs=native.get('sampled_token_logprobs'))
