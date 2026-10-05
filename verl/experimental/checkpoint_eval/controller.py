"""单次检查点曲线任务的资产准备、子进程生命周期和文档同步。"""
import datetime
import fcntl
import json
import os
import subprocess
import sys
import tarfile
import time
from pathlib import Path

from .core import label_flags, paired_compare, select_rows


def now():
    """
    @brief 返回用于状态与交接记录的UTC时间。
    @return 带时区的ISO时间字符串。
    """
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def prepare(repo, output, pool, historical, base, checkpoints, formal_config, seed, device):
    """
    @brief 在不生成回答的情况下冻结D256、风险清单、模型列表和配置。
    @param repo 项目代码根目录。
    @param output 本次唯一运行目录，已存在时拒绝覆盖。
    @param pool 冻结P/D/T目录；只读取D表和清单，T表不读取。
    @param historical 历史D32表。
    @param base 固定初始模型目录。
    @param checkpoints 父训练运行的检查点根目录。
    @param formal_config 父训练已解析的配置文件。
    @param seed 固定选题与统计种子。
    @param device 整个对照共同使用的物理GPU编号。
    @return 本次冻结配置文件路径。
    @raises ValueError 数据交叉、清单或标签无效时抛出。
    @raises FileExistsError 输出目录已存在时抛出。
    """
    import pandas as pd
    from .runtime import json_value
    from verl.experimental.difficulty.pool_preparation import normalize_question
    from verl.experimental.difficulty.state import atomic_json, file_hash
    output, repo, pool = Path(output), Path(repo), Path(pool)
    # 唯一run_id目录不可覆盖，失败尝试和已生成证据必须保留。
    if output.exists():
        raise FileExistsError('Run directory already exists; inspect it before resuming')
    frame, old = pd.read_parquet(pool / 'D.parquet'), pd.read_parquet(historical)
    rows = [{'question_id': str(row.question_id), 'source': str(row.data_source), 'question': str(row.question),
             'target': json.loads(json.dumps(row.reward_model['ground_truth']['target'], default=json_value))}
            for row in frame.itertuples()]
    selected = select_rows(rows, set(old.question_id), {'nq': 120, 'hotpotqa': 136}, seed)
    identities = [row['question_id'] for row in selected]
    manifest = json.loads((pool / 'manifest.json').read_text())
    forbidden = {row['question_id'] for split in ('P', 'T') for row in manifest['samples'][split]}
    # 利用冻结ID清单检查隔离，不读取封存T的题目或答案。
    if set(identities) & forbidden or set(identities) & set(old.question_id):
        raise ValueError('Evaluation selection overlaps P, T, or historical D32')
    normalized = [normalize_question(row['question']) for row in selected]
    # 原始大小写或标点差异不能制造两道不同的评价问题。
    if len(set(normalized)) != 256:
        raise ValueError('Duplicate normalized questions in D256')
    review = [{'question_id': row['question_id'], 'question': row['question'], 'target': row['target'],
               'flags': label_flags(row)} for row in selected]
    output.mkdir(parents=True)
    order = {identity: i for i, identity in enumerate(identities)}
    chosen = frame[frame.question_id.isin(identities)].copy()
    chosen['_order'] = chosen.question_id.map(order)
    chosen.sort_values('_order').drop(columns='_order').reset_index(drop=True).to_parquet(output / 'D256.parquet')
    models = [{'label': 'base', 'step': 0, 'path': str(base), 'checkpoint_root': None}]
    # 只登记实际保存且发布完整的权重，不虚构第50步检查点。
    for step in (20, 40, 60, 80, 100):
        root = Path(checkpoints) / f'step_{step}'
        # 发布标记缺失则停止准备，避免后面把加载失败当作性能下降。
        if not (root / 'COMPLETE.json').is_file():
            raise ValueError(f'Missing completed checkpoint: {root}')
        models.append({'label': f'step_{step}', 'step': step, 'path': str(root / 'actor'), 'checkpoint_root': str(root)})
    # 只冻结源码与原始数据指纹；不会复制大模型或碰封存T表。
    source_paths = sorted(set(list(repo.glob('verl/**/*.py')) + list(repo.glob('search_r1/**/*.py'))
                              + list(repo.glob('scripts/difficulty/*.py'))
                              + [repo / 'tests/test_checkpoint_eval.py', repo / 'env/metax/run.sh']))
    source_hashes = {str(path.relative_to(repo)): file_hash(path) for path in source_paths}
    # 独立快照包含未提交的新评价代码，Git HEAD本身不能完整描述本次实现。
    with tarfile.open(output / 'source-snapshot.tar.gz', 'w:gz') as archive:
        for path in source_paths:
            archive.add(path, arcname=str(path.relative_to(repo)))
    git_head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip()
    (output / 'git-status.txt').write_text(subprocess.check_output(['git', 'status', '--short'], cwd=repo, text=True))
    (output / 'git-diff.patch').write_bytes(subprocess.check_output(['git', 'diff'], cwd=repo))
    settings = {'schema_version': 1, 'created_utc': now(), 'repo': str(repo), 'output_dir': str(output),
                'seed': seed, 'device': str(device), 'batch_size': 8, 'formal_config': str(formal_config),
                'datasets': {'D256': str(output / 'D256.parquet'), 'D32': str(historical)},
                'models': models, 'label_risk_ids': [row['question_id'] for row in review if row['flags']],
                'source_hashes': source_hashes, 'git_head': git_head,
                'source_snapshot_sha256': file_hash(output / 'source-snapshot.tar.gz'),
                'asset_hashes': {str(path): file_hash(path) for path in (pool / 'D.parquet', pool / 'manifest.json',
                                                                     Path(historical), Path(formal_config), output / 'D256.parquet')},
                'protocol': {'single_trajectory': True, 'do_sample': False, 'temperature': 0,
                             'top_p': 1, 'top_k': -1, 'tensor_parallel_size': 1,
                             'topology': 'one identical physical GPU, eight prompts per inference batch',
                             'historical_topology': 'eight data-parallel GPU engines, one prompt per engine',
                             'historical_scores_mixed_into_new_curve': False,
                             'answer_mode': 'response_only_v1', 'labels_modified': False}}
    atomic_json(output / 'selection.json', {'seed': seed, 'quotas': {'nq': 120, 'hotpotqa': 136},
                                           'selected': selected, 'historical_ids_excluded': sorted(set(old.question_id)),
                                           'label_review': review, 'label_review_scope': '结构、时间指代和多部分答案风险初查；非256题全部外部事实核验',
                                           'near_duplicate_scope': '规范化完全重复及冻结ID交叉；语义近重复未全部人工验收'})
    atomic_json(output / 'config.json', settings)
    atomic_json(output / 'status.json', {'status': 'prepared', 'checked_utc': now(), 'completed_d256_models': 0,
                                        'target_models': 6, 'gpu_started': False})
    return output / 'config.json'


def publish(settings, state):
    """
    @brief 同步本次实测状态到运行记录和进度台账，保留人工分析及历史。
    @param settings 含repo和output_dir的冻结配置。
    @param state 由实际文件/进程确认的状态字典。
    @return 无。
    """
    from verl.experimental.difficulty.state import atomic_json
    root, repo = Path(settings['output_dir']), Path(settings['repo'])
    state = dict(state, checked_utc=now())
    atomic_json(root / 'status.json', state)
    record = repo / 'docs/experiments/runs' / f'{root.name}.md'
    # 必须先建档，再占用设备；自动区块不能替代人工登记配置与偏离。
    if not record.exists():
        raise ValueError('Run record must be registered before GPU start')
    marker = '\n## 自动评价进度'
    text = record.read_text().split(marker)[0]
    record.write_text(text + marker + '\n\n```json\n' + json.dumps(state, ensure_ascii=False, indent=2) + '\n```\n')
    ledger = repo / 'docs/experiments/data_difficulty_progress.md'
    begin, end = f'<!-- {root.name}-current -->', f'<!-- /{root.name}-current -->'
    block = begin + '\n\n检查点曲线：' + json.dumps(state, ensure_ascii=False) + '\n\n' + end
    current = ledger.read_text()
    # 仅替换当前run_id的自动区块，其他运行与历史结论保持不变。
    if begin in current:
        a, b = current.index(begin), current.index(end) + len(end)
        current = current[:a] + block + current[b:]
    else:
        current += '\n\n' + block + '\n'
    ledger.write_text(current)


def repeat_check(settings, labels=('base', 'step_100')):
    """
    @brief 检查Base及末期D32复评一致性，并另报与历史输出的差异。
    @param settings 本次冻结配置。
    @param labels 本次需要检查的模型标识；Base完成即先验收，避免浪费后续计算。
    @return 本次重复一致性与历史比较记录。
    @raises ValueError 同协议重复评价不一致或ID集合改变时抛出。
    @note 历史八卡分发与本次单卡批处理不同，历史分数不拼入D256曲线。
    """
    from verl.experimental.difficulty.state import atomic_json
    root = Path(settings['output_dir'])
    historic_path = Path(settings['models'][-1]['checkpoint_root']).parents[1] / 'validation-answers.jsonl'
    historical = [json.loads(line) for line in historic_path.read_text().splitlines()]
    comparisons = {}
    # 初始和末期都验收重复性；历史输出只作协议核对，不补入新曲线。
    for label in labels:
        step = 0 if label == 'base' else 100
        a = json.loads((root / label / 'D32_a/result.json').read_text())['records']
        b = json.loads((root / label / 'D32_b/result.json').read_text())['records']
        keys = ('question_id', 'target', 'model_response', 'full_response', 'extracted_answer', 'reward')
        repeated = len(a) == len(b) == 32 and all(all(x[k] == y[k] for k in keys) for x, y in zip(a, b))
        old = {row['question_id']: row for row in historical if row['evaluation_step'] == step}
        # 同一历史集须具有相同ID，不能仅比较两个百分比。
        if set(old) != {row['question_id'] for row in a}:
            raise ValueError('Historical D32 IDs changed')
        comparisons[label] = {'repeat_exact': repeated, 'new_correct': sum(row['reward'] for row in a),
                              'historical_correct': sum(row['reward'] for row in old.values()),
                              'answer_changes_vs_historical': [row['question_id'] for row in a
                                                               if row['extracted_answer'] != old[row['question_id']]['extracted_answer']],
                              'model_response_changes_vs_historical': sum(row['model_response'] != old[row['question_id']]['model_response'] for row in a)}
    atomic_json(root / 'repeat-check.json', comparisons)
    # 重复性未通过时暂停曲线，不以固定seed代替实测复现。
    if not all(value['repeat_exact'] for value in comparisons.values()):
        raise ValueError('Greedy repeated D32 outputs differ; do not start D256 automatically')
    return comparisons


def assemble_curve(settings):
    """
    @brief 汇总六个完整模型的同题曲线，计算相邻及相对Base的探索性配对差值。
    @param settings 本次冻结配置及预先标记风险题ID。
    @return 不含大轨迹的曲线统计字典。
    @raises ValueError 任一模型未完成或标签不一致时抛出。
    """
    from verl.experimental.difficulty.state import atomic_json
    root = Path(settings['output_dir'])
    results = [json.loads((root / model['label'] / 'D256/result.json').read_text()) for model in settings['models']]
    # 六个完整结果到齐才发布曲线，部分模型仅作为进行中状态。
    if any(not result['complete'] or len(result['records']) != 256 for result in results):
        raise ValueError('Cannot summarize an incomplete six-model curve')
    curve = {'schema_version': 1, 'completed_utc': now(), 'protocol': settings['protocol'],
             'models': [{'label': result['model']['label'], 'step': result['model']['step'], 'summary': result['summary'],
                         'label_risk_excluded_summary': result['label_risk_excluded_summary'], 'cost': result['cost']} for result in results],
             'comparisons': [], 'selection_bias_note': '峰值和起始区间为开发集探索性结果，配对区间未作多重比较校正；不证明因果或总体最优。'}
    pairs = [(i - 1, i, 'adjacent') for i in range(1, 6)] + [(0, i, 'versus_base') for i in range(2, 6)]
    # 相邻比较定位区间；全部题与预先标记排除子集同时报告，不能事后挑标签。
    for before, after, kind in pairs:
        a, b = results[before], results[after]
        curve['comparisons'].append({'before': a['model']['label'], 'after': b['model']['label'], 'kind': kind,
                                     'all': paired_compare(a['records'], b['records']),
                                     'label_risk_excluded': paired_compare(a['records'], b['records'], settings['label_risk_ids'])})
    atomic_json(root / 'curve.json', curve)
    return curve


def run(settings):
    """
    @brief 独占本次运行和指定GPU的评价锁，顺序执行复评检查及六模型曲线。
    @param settings 完整且已登记的冻结运行配置。
    @return 无。
    @raises Exception 子进程失败、源码变化或重复性验收失败时停止并保留产物。
    @note 不杀其他任务或检索服务；失败后仅能在相同配置和源码下显式续跑。
    """
    from verl.experimental.difficulty.state import atomic_json, file_hash
    root, repo = Path(settings['output_dir']), Path(settings['repo'])
    # 文件锁只约束本入口拥有的评价任务，绝不终止其他进程以抢占设备。
    with (root / 'run.lock').open('a') as lock, (root.parent / f'.checkpoint-eval-gpu-{settings["device"]}.lock').open('a') as gpu_lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(gpu_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # 所有对照都由同一冻结代码和题集生成，禁止中途悄悄变更评价定义。
        for name, expected in settings['source_hashes'].items():
            if file_hash(repo / name) != expected:
                raise ValueError('Frozen source changed: ' + name)
        # 数据与原协议同样校验内容，文件路径没变不能代替一致性检查。
        for path, expected in settings['asset_hashes'].items():
            if file_hash(path) != expected:
                raise ValueError('Frozen asset changed: ' + path)
        atomic_json(root / 'controller-process.json', {'pid': os.getpid(), 'started_utc': now(), 'argv': sys.argv})
        tasks = [('base', ['D32_a', 'D32_b']), ('step_100', ['D32_a', 'D32_b'])]
        tasks.extend((model['label'], ['D256']) for model in settings['models'])
        child = None
        # 子进程失败或被打断时保留结果，并只结束本控制器拥有的子进程。
        try:
            for index, (label, phases) in enumerate(tasks):
                # 完整阶段可跳过；续跑不会重复写已提交的题，也不把失败批次计为错误答案。
                if all((root / label / phase / 'result.json').exists() for phase in phases):
                    # 跳过已完成阶段仍需核验D32复评，不能靠旧完成文件绕过验收。
                    if index <= 1:
                        repeat_check(settings, ('base',) if index == 0 else ('base', 'step_100'))
                    continue
                # 进入第一个D256模型前，两种权重的D32重复性必须先通过。
                if index == 2:
                    repeat_check(settings)
                env = dict(os.environ, CUDA_VISIBLE_DEVICES=settings['device'], SEARCH_R1_N_GPUS='1',
                           HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
                command = ['bash', 'env/metax/run.sh', '-u', '-m', 'verl.experimental.checkpoint_eval.runtime',
                           '--config', str(root / 'config.json'), '--model', label, '--phases', *phases]
                log = root / f'{index:02d}-{label}-{phases[0]}.log'
                # 保存精确启动命令、时间及日志，独立检索服务不受评价进程退出影响。
                with log.open('a') as stream:
                    child = subprocess.Popen(command, cwd=repo, env=env, stdout=stream, stderr=subprocess.STDOUT)
                    atomic_json(root / 'child-process.json', {'pid': child.pid, 'started_utc': now(), 'argv': command, 'log': str(log)})
                    # 状态只读已落盘批次，不能把估计题数当作已完成结果。
                    while child.poll() is None:
                        phase_state = {}
                        # 复评两个阶段分别展示，不用总数掩盖某一轮尚未完成。
                        for phase in phases:
                            status_path = root / label / phase / 'status.json'
                            if status_path.exists():
                                phase_state[phase] = json.loads(status_path.read_text())
                        completed = sum((root / model['label'] / 'D256/result.json').exists() for model in settings['models'])
                        publish(settings, {'status': 'running', 'model': label, 'phases': phase_state, 'child_pid': child.pid,
                                           'completed_d256_models': completed, 'target_models': 6, 'log': str(log)})
                        time.sleep(20)
                    # 任何非零退出停止后续模型，防止服务故障污染曲线。
                    if child.returncode:
                        raise RuntimeError(f'Evaluation child exited {child.returncode}: {log}')
                # 末期复评结束后立即验收，失败时不再加载其他模型。
                if index <= 1:
                    repeat_check(settings, ('base',) if index == 0 else ('base', 'step_100'))
            curve = assemble_curve(settings)
            publish(settings, {'status': 'completed', 'completed_d256_models': 6, 'target_models': 6,
                               'curve': str(root / 'curve.json'), 'models': curve['models']})
        except BaseException as error:
            # 只处理已由本控制器创建且仍存活的子进程，避免续跑时遗留并行写者。
            if child is not None and child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()
            publish(settings, {'status': 'failed_or_interrupted', 'error': repr(error),
                               'completed_d256_models': sum((root / m['label'] / 'D256/result.json').exists() for m in settings['models']),
                               'target_models': 6})
            raise
