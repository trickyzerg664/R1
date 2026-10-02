"""检索观察裁剪与上下文预算；独立于Ray、GPU和训练器。"""
import re
import torch


def observation_ids(text, tokenizer, limit):
    """未超限时逐token保持原文，超限时保留标签及尽可能多的文档标题。"""
    if limit < 0:
        raise ValueError('Observation token budget must be nonnegative')
    original = tokenizer.encode(text, add_special_tokens=False)
    if len(original) <= limit:
        return original, False
    opening, closing = '\n\n<information>', '</information>\n\n'
    if not (text.startswith(opening) and text.endswith(closing)):
        # 无效动作反馈也受剩余预算限制，但不伪造检索标签。
        return original[:limit], True
    prefix = tokenizer.encode(opening, add_special_tokens=False)
    suffix = tokenizer.encode('\n[retrieval truncated]' + closing, add_special_tokens=False)
    available = limit - len(prefix) - len(suffix)
    if available < 0:
        raise ValueError('Budget cannot contain retrieval tags and truncation notice')
    inner = text[len(opening):-len(closing)]
    documents = re.split(r'(?m)(?=^Doc \d+\(Title:)', inner)
    documents = [doc for doc in documents if doc]
    parts = []
    for doc in documents:
        marker = doc.find(') ')
        header, body = (doc[:marker+2], doc[marker+2:]) if marker >= 0 else ('', doc)
        parts.append((tokenizer.encode(header, add_special_tokens=False),
                      tokenizer.encode(body, add_special_tokens=False)))
    headers = sum(len(header) for header, _ in parts)
    if parts and headers <= available:
        # 各文档正文均分预算；短文档剩余份额继续分给长文档，不跨文档复制内容。
        counts = [0] * len(parts)
        remaining = available - headers
        while remaining and any(count < len(body) for count, (_, body) in zip(counts, parts)):
            for i, (_, body) in enumerate(parts):
                if remaining and counts[i] < len(body):
                    counts[i] += 1
                    remaining -= 1
        content = []
        for (header, body), count in zip(parts, counts):
            content.extend(header)
            content.extend(body[:count])
    else:
        # 极小预算无法容纳全部标题时，保留内容前缀；标签完整性始终优先。
        content = tokenizer.encode(inner, add_special_tokens=False)[:available]
    ids = prefix + content + suffix
    assert len(ids) <= limit
    return ids, True


def pad_token_rows(rows, pad_id, padding_side='right'):
    """明确创建long类型，包括全空观察，避免浮点token污染后续拼接。"""
    width = max((len(row) for row in rows), default=0)
    result = torch.full((len(rows), width), pad_id, dtype=torch.long)
    for i, row in enumerate(rows):
        if row:
            start = width - len(row) if padding_side == 'left' else 0
            result[i, start:start+len(row)] = torch.tensor(row, dtype=torch.long)
    return result


class ContextBudget:
    """每条轨迹保留原问题和完整生成历史，预算不足时只允许最后一次回答。"""
    def __init__(self, prefix_ids, pad_id, limit, response_limit, tokenizer):
        self.pad_id, self.limit = pad_id, int(limit)
        self.response_limit = int(response_limit)
        self.prefix_lengths = (prefix_ids != pad_id).sum(-1).cpu()
        self.reminder = tokenizer.encode(
            '\nSearch/context budget exhausted. Give your final answer now inside <answer> and </answer>. Do not search again.\n',
            add_special_tokens=False)
        # 最后回答、结束提示与重新分词的小幅长度变化预留空间；不能悄悄截掉模型答案。
        self.reserve = self.response_limit + len(self.reminder) + 16
        empty = '\n\n<information></information>\n\n'
        self.minimum_observation = len(tokenizer.encode(empty, add_special_tokens=False)) + 24
        if self.response_limit < 1 or bool((self.prefix_lengths + self.reserve >= self.limit).any()):
            raise ValueError('Question leaves insufficient budget for a complete final answer')

    def lengths(self, ids):
        return (ids != self.pad_id).sum(-1).cpu()

    def final_mask(self, responses):
        """继续一轮搜索所需空间不足时终结，保留最终回答预算。"""
        remaining = self.limit - self.prefix_lengths - self.lengths(responses)
        return remaining < self.reserve + self.response_limit + self.minimum_observation

    def observation_limits(self, responses, new_response, active_mask=None):
        """新检索反馈只能消费最终回答预留空间以外的token。"""
        remaining = self.limit - self.prefix_lengths - self.lengths(responses) - self.lengths(new_response) - self.reserve
        eligible = torch.ones_like(remaining, dtype=torch.bool) if active_mask is None else active_mask.cpu().bool()
        if bool(((remaining < 0) & eligible).any()):
            raise ValueError('Generated response exceeds reserved context budget')
        return remaining.clamp_min(0).tolist()

    def validate(self, responses):
        """训练/奖励轨迹与生成输入使用同一完整历史；超预算立即报错。"""
        if bool((self.prefix_lengths + self.lengths(responses) > self.limit).any()):
            raise ValueError('Complete trajectory exceeds context limit')

