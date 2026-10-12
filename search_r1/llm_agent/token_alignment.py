"""保留实际采样前缀；仅重建无法在原 token 边界截断的片段。"""


def preserve_sampled_prefix(raw_ids, consumed, tokenizer, raw_token_count=None):
    """@brief 保留原始 token 前缀，并为人工边界返回零训练掩码。
    @param raw_ids 单条原始生成编号列表，可包含右侧补齐。
    @param consumed 协议实际消费的文本前缀。
    @param tokenizer 实际 tokenizer，提供 decode、encode 与 pad/eos 标识。
    @param raw_token_count 可选原生长度，用于区分生成内容与右侧补齐。
    @return 处理后的编号列表与同长度零一列表；一表示实际采样 token。
    @raises ValueError 原生长度、消费前缀或重建文本不符合约束。
    @note 不重编码完整文本；人工片段只作上下文，不接受策略梯度。
    """
    raw = list(map(int, raw_ids))
    # 原生长度优先，避免 pad 与 EOS 相同时把补齐误当成实际输出。
    if raw_token_count is not None:
        if not isinstance(raw_token_count, int) or not 0 <= raw_token_count <= len(raw):
            raise ValueError('Invalid native response length')
        raw = raw[:raw_token_count]
    eos = getattr(tokenizer, 'eos_token_id', None)
    terminal = set(eos if isinstance(eos, (list, tuple)) else [eos])
    terminal.add(getattr(tokenizer, 'pad_token_id', None))
    # 沿用既有消费语义：尾部 EOS/补齐不进入下一轮上下文；内部 token 保持原样。
    while raw and raw[-1] in terminal:
        raw.pop()
    text = tokenizer.decode(raw, skip_special_tokens=True)
    # 消费文字必须来自实际生成前缀；错误边界立即失败，不能退回整段编码。
    if not text.startswith(consumed):
        raise ValueError('Consumed text is not a sampled prefix')
    # 空消费不构造人工 token，也不将未执行原始尾部加入训练。
    if not consumed:
        return [], []
    # 完整消费直接返回原编号，包括非规范 BPE 拆分与真实替换字符。
    if text == consumed:
        return raw, [1] * len(raw)

    # 常见 ASCII 动作边界用二分定位；任何不满足文本前缀关系的情况改用完整扫描。
    lo, hi = 0, len(raw)
    while lo < hi:
        mid = (lo + hi) // 2
        prefix = tokenizer.decode(raw[:mid], skip_special_tokens=True)
        if len(prefix) < len(consumed):
            lo = mid + 1
        else:
            hi = mid
    end = lo
    before = tokenizer.decode(raw[:max(0, end - 1)], skip_special_tokens=True)
    through = tokenizer.decode(raw[:end], skip_special_tokens=True)
    if through == consumed:
        return raw[:end], [1] * end
    if through.startswith(consumed) and consumed.startswith(before):
        safe_count, safe_text = max(0, end - 1), before
    else:
        # UTF-8 字节的中间 decode 可能出现临时替换字符，不能据此丢掉正确前缀。
        safe_count, safe_text = 0, ''
        for count in range(1, len(raw) + 1):
            prefix = tokenizer.decode(raw[:count], skip_special_tokens=True)
            if prefix == consumed:
                return raw[:count], [1] * count
            if prefix.startswith(consumed):
                break
            if consumed.startswith(prefix):
                safe_count, safe_text = count, prefix
        else:
            raise ValueError('Cannot locate sampled action boundary')
    # 跨 token 的字符边界只重建剩余片段，保留此前所有实际采样编号。
    fragment = tokenizer.encode(consumed[len(safe_text):], add_special_tokens=False)
    result = raw[:safe_count] + list(map(int, fragment))
    if tokenizer.decode(result, skip_special_tokens=True) != consumed:
        raise ValueError('Reconstructed boundary changes consumed text')
    return result, [1] * safe_count + [0] * len(fragment)
