"""CPU逐题记录：保留原指标和回答证据，不修改标准答案或奖励。"""
import datetime
import json
import hashlib
from pathlib import Path
from .qa_em import extract_solution, em_check


def make_record(prompt, response, full_response, ground_truth, source, reward, mode, step, call, question_id, row):
    # legacy影子指标只作可比性诊断，不能进入新训练奖励。
    legacy_answer = extract_solution(prompt + response)
    return dict(schema_version=1, checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                evaluation_step=step, reward_call=call, row=row, question_id=question_id if question_id is not None else hashlib.sha256(prompt.encode()).hexdigest(),
                data_source=source, prompt=prompt, model_response=response, full_response=full_response,
                target=ground_truth['target'], answer_mode=mode,
                extracted_answer=extract_solution(response if mode != 'legacy' else prompt+response, mode),
                reward=float(reward), legacy_reward=float(em_check(legacy_answer, ground_truth['target'])) if legacy_answer is not None else 0.)


def append_records(path, rows):
    # 序列化整批后写入；完整文本不截取，支持numpy标准答案但拒绝未知对象。
    def encode(value):
        if hasattr(value, 'tolist'):
            return value.tolist()
        raise TypeError(f'Unsupported audit value: {type(value)}')
    text = ''.join(json.dumps(row, ensure_ascii=False, default=encode)+'\n' for row in rows)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('a') as stream:
        stream.write(text)
