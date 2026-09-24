"""[data-difficulty] 无预取的可恢复配额采样，支持固定来源边际和五档标签。"""
from collections import defaultdict
import copy
import json
from pathlib import Path
import numpy as np
from .state import fingerprint


def bucket(k):
    """将四次正确数量映射为 H/M/E：0、1–2、3–4。
    k=3 与 k=4 虽同属 E，优势是否非零不同，因此始终保留原始五档标签。
    """
    if k not in range(5):
        raise ValueError('Correct count must be in 0..4')
    return 'H' if k == 0 else 'M' if k < 3 else 'E'


def pool_rows(dataframe):
    # question_id 跨刷新保持稳定；输入缺 ID 时由来源、原始 ID 和问题共同生成。
    """从冻结的数据表提取永久题目身份、来源和问题／答案内容指纹。
    返回顺序与 dataset 行号一致；不能在标签生成后重新排序或替换题池。
    """
    rows = []
    for _, row in dataframe.iterrows():
        source = str(row['data_source'])
        prompt = row['prompt'].tolist() if hasattr(row['prompt'], 'tolist') else row['prompt']
        identity = row.get('question_id')
        if not isinstance(identity, str) or not identity:
            identity = fingerprint([source, str(row.get('id', '')), prompt])
        rows.append({'question_id': identity, 'source': source, 'prompt_hash': fingerprint(prompt),
                     'answer_hash': fingerprint(row['reward_model']['ground_truth'])})
    if len({r['question_id'] for r in rows}) != len(rows):
        raise ValueError('Candidate pool question_id values must be unique')
    return rows


def pool_hash(rows):
    """将题池内容及排列顺序一起纳入身份校验。
    相同题目集合但不同排列也拒绝直接复用行号状态，防止采样错题。
    """
    return fingerprint(rows)


def load_labels(path, rows):
    """读取完整标签并返回原始元数据和按 question_id 索引的记录。
    磁盘文件与在线刷新共用 validate_labels，不接受仅部分题目已评分的文件。
    """
    payload = json.loads(Path(path).read_text())
    return payload, validate_labels(payload, rows)


def validate_labels(payload, rows):
    # 磁盘加载与运行时刷新共用完整性约束，避免非法标签绕过文件入口。
    """校验版本、固定题池、唯一覆盖、来源、四条二值奖励和桶的一致性。
    返回 ID 索引；任何检查失败都不能把部分结果应用到 sampler。
    """
    if payload['metadata'].get('schema_version') != 1 or payload['metadata'].get('group_size') != 4:
        raise ValueError('Unsupported labels schema or group size')
    if payload['metadata']['pool_hash'] != pool_hash(rows):
        raise ValueError('Labels belong to a different candidate pool')
    records = payload['records']
    by_id = {r['question_id']: r for r in records}
    if len(by_id) != len(records) or set(by_id) != {r['question_id'] for r in rows}:
        raise ValueError('Labels must cover every candidate exactly once')
    for row in rows:
        record = by_id[row['question_id']]
        if record['source'] != row['source'] or bucket(record['k']) != record['bucket']:
            raise ValueError('Inconsistent source or difficulty label')
        rewards = record['rewards']
        if len(rewards) != 4 or any(r not in (0, 1) for r in rewards) or sum(rewards) != record['k']:
            raise ValueError('Each label must contain four binary rewards')
    return by_id


class DifficultyBatchSampler:
    """[data-difficulty] 每批次先分配来源配额，再分配难度和五档内部配额。"""
    def __init__(self, rows, batch_size, steps, seed, ratios=None, labels=None):
        """创建按来源分层的固定步数采样器，steps 是绝对目标步数。
        题池是唯一且不可变的；每批无重复，跨批允许重复以维持计划配额。
        """
        if not rows or len({row['question_id'] for row in rows}) != len(rows):
            raise ValueError('Candidate pool must be nonempty with unique IDs')
        if batch_size < 1 or steps < 1:
            raise ValueError('batch_size and steps must be positive')
        self.rows, self.batch_size, self.steps = rows, batch_size, steps
        self.pool_hash = pool_hash(rows)
        self.rng = np.random.default_rng(seed)
        self.cursor = 0
        self.exposures = np.zeros(len(rows), dtype=np.int64)
        self.debts = {}
        self.sources = sorted({r['source'] for r in rows})
        self.source_indices = {s: [i for i,r in enumerate(rows) if r['source'] == s] for s in self.sources}
        self.configure(ratios, labels)

    def configure(self, ratios, labels):
        # 刷新只改变标签和配额，不改变题池成员、永久 ID 或已发生的曝光。
        """建立来源×难度×正确数量的候选索引，不修改历史曝光和消费位置。
        ratios=None 表示各来源内部自然采样；正配额的桶为空时必须修改实验设计。
        """
        if ratios is not None:
            ratios = list(map(float, ratios))
            if len(ratios) != 3 or any(x < 0 for x in ratios) or not np.isclose(sum(ratios), 1):
                raise ValueError('H/M/E ratios must be nonnegative and sum to 1')
            if labels is None:
                raise ValueError('Difficulty quotas require labels')
        if labels is not None and set(labels) != {r['question_id'] for r in self.rows}:
            raise ValueError('Labels must exactly match the candidate pool')
        self.ratios, self.labels = ratios, labels
        self.cells = defaultdict(list)
        if labels is not None:
            for i, row in enumerate(self.rows):
                record = labels[row['question_id']]
                if record['source'] != row['source']:
                    raise ValueError('Label source differs from candidate source')
                k = record['k']
                self.cells[(row['source'], bucket(k), k)].append(i)
            for source in self.sources:
                for b, ratio in zip(('H','M','E'), ratios or (0,0,0)):
                    if ratio > 0 and not any(self.cells[(source,b,k)] for k in range(5)):
                        raise ValueError(f'Empty required bucket: {source}/{b}')
        self.policy = fingerprint({'ratios': ratios, 'labels': labels})

    def _allocate(self, key, weights, total, capacities):
        # 最大余数配额加累计误差补偿；不静默跨来源/难度补齐样本。
        """用累计欠额补偿整数配额舍入误差，同时约束桶容量。
        同权重的优先顺序固定，随机性仅发生在桶内选题，便于复现配额与排查偏差。
        """
        weights = np.asarray(weights, dtype=float)
        capacities = np.asarray(capacities, dtype=int)
        if weights.sum() <= 0 or total > capacities[weights > 0].sum():
            raise ValueError(f'Insufficient candidates for quota {key}')
        debt = np.array(self.debts.get(key, [0.] * len(weights)))
        desired = total * weights / weights.sum() + debt
        counts = np.zeros(len(weights), dtype=int)
        for _ in range(total):
            valid = (weights > 0) & (counts < capacities)
            priority = np.where(valid, desired-counts, -np.inf)
            if not valid.any():
                raise ValueError(f'Quota cannot be filled: {key}')
            counts[np.argmax(priority)] += 1
        self.debts[key] = (desired-counts).tolist()
        return counts

    def __iter__(self):
        """每次迭代生成一个完整题目批，并在交给训练器前推进消费位置。
        必须使用 num_workers=0；只有该批训练完成后才允许保存对应 checkpoint。
        """
        while self.cursor < self.steps:
            # 无 worker 预取时，yield 前推进的位置正好对应当前已取出的训练批。
            counts = self._allocate('source', [len(self.source_indices[s]) for s in self.sources],
                                    self.batch_size, [len(self.source_indices[s]) for s in self.sources])
            chosen = []
            for source, count in zip(self.sources, counts):
                if not count:
                    continue
                if self.ratios is None:
                    chosen.extend(self.rng.choice(self.source_indices[source], count, replace=False).tolist())
                    continue
                available = [sum(len(self.cells[(source,b,k)]) for k in range(5)) for b in ('H','M','E')]
                # 正权重桶容量必须容纳理论上界，避免容量截断悄悄改变配比。
                for b, weight, capacity in zip(('H','M','E'), self.ratios, available):
                    if weight and capacity < int(np.ceil(count*weight)):
                        raise ValueError(f'Insufficient bucket capacity: {source}/{b}')
                bc = self._allocate(source+'/bucket', self.ratios, count, available)
                for b, n in zip(('H','M','E'), bc):
                    if not n:
                        continue
                    sizes = [len(self.cells[(source,b,k)]) for k in range(5)]
                    kc = self._allocate(source+'/'+b, sizes, n, sizes)
                    for k, nk in enumerate(kc):
                        if nk:
                            chosen.extend(self.rng.choice(self.cells[(source,b,k)], nk, replace=False).tolist())
            self.rng.shuffle(chosen)
            self.exposures[chosen] += 1
            self.cursor += 1
            yield chosen

    def __len__(self):
        """返回剩余批数，恢复后不会把父训练已完成的步骤重新计入预算。
        """
        return max(0, self.steps-self.cursor)

    def state_dict(self):
        """导出 RNG、配额欠额、曝光次数和已消费批数的独立快照。
        策略指纹绑定标签与比例，防止普通续训时意外切换策略。
        """
        return {'pool_hash': self.pool_hash, 'policy': self.policy, 'batch_size': self.batch_size,
                'cursor': self.cursor, 'rng': copy.deepcopy(self.rng.bit_generator.state),
                'exposures': self.exposures.tolist(), 'debts': copy.deepcopy(self.debts)}

    def load_state_dict(self, state, branch=False):
        """普通继续要求原策略相同，branch 才允许显式变更标签或比例。
        策略变更时清空旧配额欠额，保留父随机位置与历史曝光，避免旧桶欠额污染新策略。
        """
        if state['pool_hash'] != self.pool_hash or state['batch_size'] != self.batch_size:
            raise ValueError('Resume requires the same pool and batch size')
        if not branch and state['policy'] != self.policy:
            raise ValueError('Continue mode requires the same labels and ratios; use branch mode explicitly')
        self.cursor = state['cursor']
        if self.cursor < 0 or self.cursor > self.steps:
            raise ValueError('Resume step exceeds configured training steps')
        self.rng.bit_generator.state = state['rng']
        self.exposures = np.asarray(state['exposures'], dtype=np.int64)
        if self.exposures.shape != (len(self.rows),) or (self.exposures < 0).any() or self.exposures.sum() != self.cursor*self.batch_size:
            raise ValueError('Invalid sampler exposure state')
        self.debts = {} if branch and state['policy'] != self.policy else copy.deepcopy(state['debts'])

    def refresh(self, labels):
        """在训练步骤边界替换标签并清空旧桶的配额欠额。
        不改变训练候选池、模型、优化器或永久题目身份。
        """
        self.configure(self.ratios, labels)
        self.debts = {}
