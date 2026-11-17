"""纯离线协议重放：以冻结行为为依据，避免依赖另一实验分支。"""
from __future__ import annotations
import re

PROMPT = ('Answer the given question. '
          'You must conduct reasoning inside <think> and </think> first every time you get new information. '
          'After reasoning, if you find you lack some knowledge, you can call a search engine by <search> query </search> '
          'and it will return the top searched results between <information> and </information>. '
          'You can search as many times as your want. '
          'If you find no further external knowledge needed, you can directly provide the answer inside <answer> and </answer>, '
          'without detailed illustrations. For example, <answer> Beijing </answer>. Question: {question}\n')
REMINDER = '\nSearch/context budget exhausted. Give your final answer now inside <answer> and </answer>. Do not search again.\n'
ACTION = re.compile(r'\s*<think>(.*?)</think>\s*<(search|answer)>(.*?)</\2>\s*', re.S)


class ReplayError(ValueError):
    pass


def reasoning(text):
    match = re.search(r'<think>(.*?)</think>', text, re.S)
    return match[1] if match else ''


def assistant_target(turn):
    """仅消费真实 content；不将原生 reasoning 字段与 content 擅自拼接。"""
    message = turn['response']['choices'][0]['message']
    if message.get('reasoning_content') or message.get('reasoning'):
        raise ReplayError('native_reasoning_not_supported')
    text = message.get('content') or ''
    match = ACTION.fullmatch(text)
    if not match:
        raise ReplayError('invalid_assistant_format')
    if re.search(r'</?(?:search|answer|information)>', match[1]) or '<information>' in text:
        raise ReplayError('action_or_observation_inside_reasoning')
    action, value = match[2], match[3].strip()
    if not value or (action, value) != (turn.get('action'), str(turn.get('value', '')).strip()):
        raise ReplayError('recorded_action_mismatch')
    # 环境在动作闭标签处停下；其后的空白不作为新的模型目标。
    end = text.rfind('</' + action + '>') + len('</' + action + '>')
    return text[:end], action, value


def initial_ids(question, tokenizer, prompt=PROMPT):
    text = prompt.format(question=question.strip())
    if getattr(tokenizer, 'chat_template', None):
        text = tokenizer.apply_chat_template([{'role': 'user', 'content': text}], add_generation_prompt=True, tokenize=False)
    return tokenizer.encode(text, add_special_tokens=False)


def observation_text(documents):
    if not documents:
        raise ReplayError('search_without_observation')
    passages = []
    for i, item in enumerate(documents, 1):
        contents = item['document']['contents']
        title, _, body = contents.partition('\n')
        passages.append(f'Doc {i}(Title: {title}) {body}\n')
    return '\n\n<information>' + ''.join(passages).strip() + '</information>\n\n'


def observation_ids(text, tokenizer, limit):
    """保留完整工具标签；超限时先保留文档标题，再均分正文预算。"""
    ids = tokenizer.encode(text, add_special_tokens=False)
    if len(ids) <= limit:
        return ids, False
    opening, closing = '\n\n<information>', '</information>\n\n'
    prefix = tokenizer.encode(opening, add_special_tokens=False)
    suffix = tokenizer.encode('\n[retrieval truncated]' + closing, add_special_tokens=False)
    available = limit - len(prefix) - len(suffix)
    if available < 0:
        raise ReplayError('insufficient_observation_budget')
    inner = text[len(opening):-len(closing)]
    documents = [x for x in re.split(r'(?m)(?=^Doc \d+\(Title:)', inner) if x]
    parts = []
    for doc in documents:
        marker = doc.find(') ')
        header, body = (doc[:marker+2], doc[marker+2:]) if marker >= 0 else ('', doc)
        parts.append((tokenizer.encode(header, add_special_tokens=False), tokenizer.encode(body, add_special_tokens=False)))
    if sum(len(h) for h, _ in parts) <= available and parts:
        counts = [0] * len(parts)
        remaining = available - sum(len(h) for h, _ in parts)
        while remaining and any(c < len(b) for c, (_, b) in zip(counts, parts)):
            for i, (_, body) in enumerate(parts):
                if remaining and counts[i] < len(body):
                    counts[i] += 1
                    remaining -= 1
        content = []
        for (header, body), count in zip(parts, counts):
            content.extend(header + body[:count])
    else:
        content = tokenizer.encode(inner, add_special_tokens=False)[:available]
    return prefix + content + suffix, True


def compile_trajectory(row, tokenizer, limits, prompt=PROMPT):
    """每轮只监督当前 assistant；未来观察不会进入之前轮次的输入。"""
    if row.get('status') != 'accepted':
        raise ReplayError('not_accepted')
    turns = row['turns']
    if not turns or len(turns) > limits['max_turns']:
        raise ReplayError('turn_budget')
    context = initial_ids(row['question'], tokenizer, prompt)
    reserve = limits['max_target_tokens'] + len(tokenizer.encode(REMINDER, add_special_tokens=False)) + 16
    minimum_observation = len(tokenizer.encode('\n\n<information></information>\n\n', add_special_tokens=False)) + 24
    if len(context) + reserve >= limits['max_total_tokens']:
        raise ReplayError('initial_prompt_budget')
    samples = []
    for i, turn in enumerate(turns):
        if limits['max_total_tokens'] - len(context) < reserve + limits['max_target_tokens'] + minimum_observation:
            raise ReplayError('forced_final_required')
        text, action, _ = assistant_target(turn)
        target = tokenizer.encode(text, add_special_tokens=False)
        if not target or len(target) > limits['max_target_tokens']:
            raise ReplayError('target_budget')
        if len(context) + len(target) > limits['max_total_tokens']:
            raise ReplayError('trajectory_budget')
        samples.append({'sample_id':f'{row["id"]}:{i}', 'question_id':row['id'], 'source':row['source'],
                        'turn_index':i, 'input_ids':context + target, 'prompt_length':len(context),
                        'target_length':len(target), 'observation_truncated':False})
        context = context + target
        if action == 'answer':
            if i != len(turns) - 1:
                raise ReplayError('answer_before_last_turn')
        else:
            if i == len(turns) - 1:
                raise ReplayError('missing_final_answer')
            budget = min(limits['max_observation_tokens'], limits['max_total_tokens'] - len(context) - reserve)
            observation, truncated = observation_ids(observation_text(turn.get('observation')), tokenizer, budget)
            samples[-1]['observation_truncated'] = truncated
            context = context + observation
    return samples
