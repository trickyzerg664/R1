"""[data-difficulty] 实验策略组合层；不导入或持有 Ray trainer/worker。"""
from collections import Counter, defaultdict
import json
from pathlib import Path
import numpy as np
from .sampling import DifficultyBatchSampler, load_labels, pool_hash, validate_labels
from .scoring import score_pool
from .state import atomic_json, capture_rng, fingerprint, restore_rng, trajectory_seed


class DifficultyExperiment:
    def __init__(self, rows, settings, batch_size, steps, seed, output_dir, provenance):
        """组合采样、评分与日志组件，不持有训练器或 worker 对象。
        settings 为解析后的普通字典；同一输出目录只能属于同一配置的任务。
        """
        self.rows, self.settings = rows, settings
        self.seed, self.output_dir = seed, Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.provenance = provenance
        self.label_payload = None
        labels = None
        if settings.get('labels'):
            self.label_payload, labels = load_labels(settings['labels'], rows)
        ratios = settings.get('ratios')
        if settings.get('mode') == 'score':
            ratios = None
        self.strategy = {key: settings.get(key) for key in ('ratios', 'refresh_steps', 'refresh_every', 'score_seed', 'score_batch_size')}
        self.lineage = settings.get('lineage', provenance['initial_model_id'])
        self.sampler = DifficultyBatchSampler(rows, batch_size, steps, seed, ratios, labels)
        self.completed_step = 0
        self.refresh_steps = set(settings.get('refresh_steps', []))
        self.refresh_every = int(settings.get('refresh_every', 0))
        self.initial_model_id = provenance['initial_model_id']
        self.train_seconds, self.score_seconds = 0., 0.
        self.imported_label_seconds = float(self.label_payload.get('seconds', 0.)) if self.label_payload and ratios is not None else 0.
        self.generated_tokens, self.score_tokens = 0, 0
        # 已有运行目录只能用于相同配置的断点重试；分支必须使用新目录。
        if (self.output_dir/'run.json').exists():
            previous = json.loads((self.output_dir/'run.json').read_text())
            if previous['settings'] != settings or previous['provenance'] != provenance:
                raise ValueError('Output directory already belongs to a different configuration; use a new directory')
        atomic_json(self.output_dir/'run.json', {'schema_version': 1, 'settings': settings,
                    'seed': seed, 'pool_hash': pool_hash(rows), 'provenance': provenance})

    def score(self, generate_and_score, output, step=0, version='initial'):
        # 只在明确的步骤边界评估，评分种子与训练抽样 RNG 分离。
        """评分只生成标签，不更新模型，训练 RNG 隔离由调用适配层负责。
        标签绑定父模型血缘、步骤及运行策略，防止同路径误用其他模型的评分。
        """
        context = {**self.provenance, 'step': step, 'version': version, 'lineage': self.lineage,
                   # 标签内容标识区分训练历史；不绑定本机目录，便于迁移评分断点。
                   'strategy': self.strategy,
                   'labels_id': fingerprint(self.label_payload) if self.label_payload else None}
        payload = score_pool(self.rows, generate_and_score, output, context,
                             self.settings.get('score_batch_size', 32), self.settings.get('score_seed', 1729))
        self.score_seconds += payload['seconds']
        self.score_tokens += sum(sum(r.get('generated_tokens', [])) for r in payload['records'])
        self.record({'event': 'score', 'step': step, 'seconds': payload['seconds'],
                     'tokens': sum(sum(r.get('generated_tokens', [])) for r in payload['records']),
                     'labels': str(output)})
        return payload

    def should_refresh(self, step):
        """判断已完成步骤是否为刷新边界。
        调用方排除最后一步，避免为已结束的训练执行无用刷新。
        """
        return step in self.refresh_steps or bool(self.refresh_every and step % self.refresh_every == 0)

    def refresh(self, payload):
        # 标签切换与采样配额状态一起生效，DataLoader 无预取队列。
        """完整验证新标签后切换采样桶，并保存当前标签供 checkpoint 使用。
        调用发生在步骤完成后、下一次 DataLoader 取数前。
        """
        labels = validate_labels(payload, self.rows)
        self.sampler.refresh(labels)
        self.label_payload = payload

    def attach_seeds(self, batch, step):
        # 数组属于逐轨迹字段，后续筛选、重排和并行分发时同步处理。
        """对已经展开成四条轨迹的生成批设置独立请求种子。
        训练位置使用绝对 step，恢复后不从零重新生成随机序列。
        """
        # [data-difficulty] DataProto 非张量字段必须为 object dtype，补齐和 Ray 分发会再次校验。
        batch.non_tensor_batch['rollout_seed'] = np.array(
            [trajectory_seed(self.seed, 'train', step, i) for i in range(len(batch))], dtype=object)
        batch.meta_info['recompute_log_prob'] = False
        return batch

    def metrics(self, batch):
        """按一次抽题 uid 聚合训练实际 k，区分历史桶与当前模型能力。
        有效组定义为 0<k<4；tokens 使用 info_mask 排除检索注入文字。
        """
        groups = defaultdict(list)
        for uid, score in zip(batch.non_tensor_batch['uid'], batch.batch['token_level_scores'].sum(-1).tolist()):
            if score not in (0., 1.):
                raise ValueError('Difficulty experiment requires binary correctness rewards')
            groups[str(uid)].append(score)
        if any(len(g) != 4 for g in groups.values()):
            raise ValueError('Difficulty group size must be four')
        counts = Counter(int(sum(g)) for g in groups.values())
        total = len(groups)
        metrics = {f'difficulty/k{k}': counts[k]/total for k in range(5)}
        metrics['difficulty/effective_fraction'] = sum(counts[k] for k in (1,2,3))/total
        metrics['difficulty/unique_questions'] = int((self.sampler.exposures > 0).sum())
        metrics['difficulty/max_exposure'] = int(self.sampler.exposures.max())
        width = batch.batch['responses'].shape[-1]
        mask = batch.batch.get('info_mask', batch.batch['attention_mask'])[:, -width:]
        metrics['difficulty/generated_tokens'] = int(mask.sum().item())
        metrics['difficulty/context_tokens'] = int(batch.batch['attention_mask'].sum().item())
        metrics['difficulty/search_queries'] = sum(batch.meta_info.get('valid_search_stats', []))
        return metrics

    def record(self, record):
        # JSONL 是后续汇总的唯一输入；每条均带 schema 与 seed。
        """追加带版本和种子的结构化事件，不静默覆盖重复步骤。
        重复步骤可能来自恢复尝试，结果分析必须按具体运行和 checkpoint 核对。
        """
        with (self.output_dir/'metrics.jsonl').open('a') as stream:
            stream.write(json.dumps({'schema_version': 1, 'seed': self.seed, **record}, default=float)+'\n')

    def after_step(self, step, metrics, elapsed):
        """在参数更新结束后推进已完成 step 并记录该步成本与标签版本。
        此时 sampler 消费位置必须与 step 相同，后续完整保存才能安全恢复。
        """
        self.completed_step = step
        self.train_seconds += elapsed
        self.generated_tokens += int(metrics.get('difficulty/generated_tokens', 0))
        self.record({'event': 'train', 'step': step, 'metrics': metrics,
                     'train_seconds': self.train_seconds, 'score_seconds': self.score_seconds,
                     'imported_label_seconds': self.imported_label_seconds,
                     'generated_tokens': self.generated_tokens, 'score_tokens': self.score_tokens,
                     'label_version': None if self.label_payload is None else self.label_payload['metadata']['context'].get('version')})

    def state_dict(self):
        """导出实验端状态；模型、optimizer 和 worker RNG 由 checkpoint 适配另行保存。
        这份 driver 状态单独存在不代表完整训练 checkpoint。
        """
        return {'schema_version': 1, 'strategy': self.strategy, 'completed_step': self.completed_step, 'sampler': self.sampler.state_dict(),
                'imported_label_seconds': self.imported_label_seconds,
                'labels': self.label_payload, 'provenance': self.provenance, 'rng': capture_rng(),
                'train_seconds': self.train_seconds, 'score_seconds': self.score_seconds,
                'generated_tokens': self.generated_tokens, 'score_tokens': self.score_tokens}

    def load_state_dict(self, state, branch=False, scoring=False):
        """验证题池与训练来源后恢复实验状态和 driver RNG。
        continue 保持策略不变；branch 保留父训练状态但采用显式新标签／比例；score 只恢复用于评估。
        """
        if state['schema_version'] != 1:
            raise ValueError('Unsupported difficulty checkpoint version')
        # 阶段二允许标签/比例变更，模型、参考模型、题池和训练关键参数必须保持一致。
        if state['provenance'] != self.provenance:
            raise ValueError('Resume provenance differs (reference/model/training/retrieval settings)')
        if not branch and not scoring and state['strategy'] != self.strategy:
            raise ValueError('Continue mode requires the same refresh and scoring strategy')
        if not branch or scoring:
            self.label_payload = state['labels']
            self.sampler.configure(state['strategy']['ratios'] if scoring else self.sampler.ratios,
                                   None if self.label_payload is None else validate_labels(self.label_payload, self.rows))
        self.sampler.load_state_dict(state['sampler'], branch=branch)
        self.completed_step = state['completed_step']
        if self.sampler.cursor != self.completed_step:
            raise ValueError('Sampler cursor and completed training step differ')
        # 分支重用旧标签不重复收费；新标签成本单列，历史训练及在线评分成本仍从父状态继承。
        if not branch or state['labels'] == self.label_payload:
            self.imported_label_seconds = state.get('imported_label_seconds', 0.)
        else:
            self.imported_label_seconds += state.get('imported_label_seconds', 0.)
        for key in ('train_seconds','score_seconds','generated_tokens','score_tokens'):
            setattr(self, key, state[key])
        restore_rng(state['rng'])
