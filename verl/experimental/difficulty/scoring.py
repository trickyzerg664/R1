"""[data-difficulty] 可续跑的四轨迹评分；生成和奖励通过窄回调复用训练实现。"""
import json
import time
from pathlib import Path
from .sampling import bucket, pool_hash, validate_labels
from .state import atomic_json, trajectory_seed


def score_pool(rows, generate_and_score, output, context, batch_size=32, seed=42):
    """回调接收题目行号及每题四个种子，返回按题排列的奖励/成本记录。"""
    if not rows:
        raise ValueError('Cannot score an empty pool')
    if batch_size < 1:
        raise ValueError('score batch size must be positive')
    output = Path(output)
    partial = output.with_suffix(output.suffix + '.partial')
    metadata = {'schema_version': 1, 'pool_hash': pool_hash(rows), 'group_size': 4,
                'seed': int(seed), 'batch_size': batch_size, 'context': context}
    # 文件绑定模型、题池、检索和采样配置；续跑时不能混入另一版本的轨迹。
    records, seconds = [], 0.
    existing = output if output.exists() else partial
    if existing.exists():
        previous = json.loads(existing.read_text())
        if previous['metadata'] != metadata:
            raise ValueError('Existing score file has incompatible provenance')
        records, seconds = previous['records'], previous.get('seconds', 0.)
        if [r['question_id'] for r in records] != [r['question_id'] for r in rows[:len(records)]]:
            raise ValueError('Invalid scoring resume order')
        # 已完成前缀同样验证来源、奖励和标签，损坏文件不能继续扩写。
        prefix = rows[:len(records)]
        validate_labels({'metadata': {**metadata, 'pool_hash': pool_hash(prefix)}, 'records': records}, prefix)
        if output.exists():
            if len(records) != len(rows):
                raise ValueError('Completed label file is incomplete')
            return previous
    for start in range(len(records), len(rows), batch_size):
        indices = list(range(start, min(start+batch_size, len(rows))))
        seeds = [[trajectory_seed(seed, rows[i]['question_id'], j) for j in range(4)] for i in indices]
        started = time.monotonic()
        generated = generate_and_score(indices, seeds)
        if len(generated) != len(indices):
            raise ValueError('Scorer returned an incorrect question count')
        new_records = []
        for i, rs, values in zip(indices, seeds, generated):
            rewards = values['rewards']
            if len(rewards) != 4 or any(r not in (0,1) for r in rewards):
                raise ValueError('Difficulty scoring requires four binary correctness rewards')
            k = int(sum(rewards))
            new_records.append({**values, 'question_id': rows[i]['question_id'], 'source': rows[i]['source'],
                                'k': k, 'bucket': bucket(k), 'seeds': rs})
        records.extend(new_records)
        seconds += time.monotonic()-started
        # 按已完成批次原子持久化，失败批次不留下半份标签。
        atomic_json(partial, {'metadata': metadata, 'records': records, 'seconds': seconds})
    payload = {'metadata': metadata, 'records': records, 'seconds': seconds}
    atomic_json(output, payload)
    if partial.exists():
        partial.unlink()
    return payload
