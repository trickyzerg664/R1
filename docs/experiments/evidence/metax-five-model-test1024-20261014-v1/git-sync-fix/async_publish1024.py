"""独立逐模型文档/Git或魔搭工作器，不获取推理锁，不等待模型中的文档任务。"""
import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from git_checkout_sync import sync_checkout

CONTROL = Path('/mnt/public/code/lyk/lzy/maintenance/test1024-five-models-20261014')


def atomic(path, value):
    """@brief 原子保存发布工作器自己的状态。@param path 输出路径。@param value JSON数据。@return 无。"""
    path = Path(path)
    temporary = path.with_name(path.name + '.publisher.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def sha(path):
    """@brief 分块计算日志内容身份。@param path 文件路径。@return SHA256。"""
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def load_results(plan, upto):
    """@brief 读取已完成且身份匹配的模型前缀。
    @param plan 冻结计划。
    @param upto 当前发布模型的顺序索引。
    @return 完整结果字典。
    @raises RuntimeError 结果漂移、缺题或问题顺序不一致。
    """
    results, identities = {}, None
    for index, label in enumerate(plan['model_order'][:upto + 1]):
        event = json.loads((CONTROL / 'queue' / (f'{index:02d}-' + label + '.json')).read_text())
        path = Path(event['result'])
        if sha(path) != event['result_sha256']:
            raise RuntimeError('Completed model result changed')
        result = json.loads(path.read_text())
        ids = [row['question_id'] for row in result['records']]
        # 发布只认完整冻结1024题，不拼接另一模型或重复题。
        if not result['complete'] or len(ids) != plan['expected_count'] or len(set(ids)) != len(ids):
            raise RuntimeError('Incomplete result')
        if identities is not None and ids != identities:
            raise RuntimeError('Unpaired question order')
        identities, results[label] = ids, result
    return results


def git_publish(plan, index, label):
    """@brief 更新已完成模型的文档并立即提交用户指定分支。
    @param plan 冻结计划。
    @param index 当前模型顺序。
    @param label 当前完整模型名称。
    @return Git已验证提交回执，附带检出工作区同步及恢复备份状态。
    @raises RuntimeError 身份、分支或远程SHA不一致。
    @note 独立index，保留工作树；网络等待不会进入推理进程。主索引已暂存或需内容合并时不自动覆盖。
    """
    results = load_results(plan, index)
    repo, evaluation = Path(plan['repository']), Path(plan['evaluation'])
    relative = Path('docs/experiments/evidence') / evaluation.name
    evidence = repo / relative
    evidence.mkdir(parents=True, exist_ok=True)
    folder = evidence / label
    folder.mkdir(exist_ok=True)
    (folder / 'answers.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in results[label]['records']))
    for name in ['console.log', 'model-verification.json']:
        shutil.copy2(evaluation / label / name, folder / name)
    for name in ['settings.json', 'formal-config.yaml']:
        shutil.copy2(evaluation / name, evidence / name)
    # 从完整结果生成累计表，未运行模型不填预测分数。
    summary = {'completed_models': list(results), 'model_order': plan['model_order'], 'dataset_sha256': plan['dataset_sha256'],
               'n': plan['expected_count'], 'models': {name: {'summary': result['summary'], 'cost': result['cost']} for name, result in results.items()}}
    lines = ['# T1024五模型对比', '', '固定NQ335+HotpotQA689，原128题完整保留；greedy单轨迹、10轮、256生成/2048观察/4096上下文，同一检索和action-stop。', '',
             '| 模型 | 正确题数 | EM | NQ EM | HotpotQA EM | 未作答 | 检索次数 | 实测推理分钟 |', '|---|---:|---:|---:|---:|---:|---:|---:|']
    for name, result in results.items():
        value = result['summary']
        lines.append(f"| {name} | {int(value['correct'])}/1024 | {value['em']:.2%} | {value['sources']['nq']['em']:.2%} | {value['sources']['hotpotqa']['em']:.2%} | {value['missing_answer']} | {value['actual_search_queries']} | {result['cost']['total_seconds']/60:.2f} |")
    lines.extend(['', '未完成模型：' + '、'.join(plan['model_order'][index + 1:]), '', '原始EM按冻结标签计算；T128语义复核为独立已提交报告，不覆盖本次1024题金标准。', '',
                  '更新UTC：' + datetime.datetime.now(datetime.timezone.utc).isoformat(), ''])
    atomic(evidence / 'comparison.json', summary)
    (evidence / 'comparison.md').write_text('\n'.join(lines))
    run_doc = repo / ('docs/experiments/runs/' + evaluation.name + '.md')
    with run_doc.open('a') as stream:
        stream.write('\n\n' + datetime.datetime.now(datetime.timezone.utc).isoformat() + ' 模型完整结束：' + label + '\n\n' + '\n'.join(lines) + '\n')
    with (repo / 'docs/experiments/data_difficulty_progress.md').open('a') as stream:
        stream.write('\n\n' + datetime.datetime.now(datetime.timezone.utc).isoformat() + ' T1024完成模型' + label + '，独立文档Git工作器立即发布；推理已顺序启动下一模型，不等待此网络操作。\n')
    environment = dict(os.environ, GIT_INDEX_FILE=str(CONTROL / 'git.index'), GIT_AUTHOR_NAME='trickyzerg', GIT_AUTHOR_EMAIL='3261677617@qq.com',
                       GIT_COMMITTER_NAME='trickyzerg', GIT_COMMITTER_EMAIL='3261677617@qq.com',
                       GIT_SSH_COMMAND='ssh -o BatchMode=yes -o ConnectTimeout=20 -o ServerAliveInterval=15 -o ServerAliveCountMax=3')
    # 每次以指定分支最新远程头为父提交；只添加本实验路径，禁止强推或切换分支。
    head = subprocess.check_output(['git', '-C', str(repo), 'ls-remote', plan['git_remote'], 'refs/heads/' + plan['git_branch']], env=environment, text=True).split()[0]
    subprocess.run(['git', '-C', str(repo), 'fetch', plan['git_remote'], head], env=environment, check=True)
    subprocess.run(['git', '-C', str(repo), 'read-tree', head], env=environment, check=True)
    subprocess.run(['git', '-C', str(repo), 'add', '-f', '--', str(relative), *plan['git_extra_paths']], env=environment, check=True)
    tree = subprocess.check_output(['git', '-C', str(repo), 'write-tree'], env=environment, text=True).strip()
    commit = subprocess.check_output(['git', '-C', str(repo), 'commit-tree', tree, '-p', head], input='docs: T1024 ' + label + ' 完整结果\n', env=environment, text=True).strip()
    author = subprocess.check_output(['git', '-C', str(repo), 'show', '-s', '--format=%an <%ae>|%cn <%ce>', commit], text=True).strip()
    # 作者及提交者独立验收，不能受全局Codex配置影响。
    if author != 'trickyzerg <3261677617@qq.com>|trickyzerg <3261677617@qq.com>':
        raise RuntimeError('Wrong Git identity')
    subprocess.run(['git', '-C', str(repo), 'push', plan['git_remote'], commit + ':refs/heads/' + plan['git_branch']], env=environment, check=True)
    remote = subprocess.check_output(['git', '-C', str(repo), 'ls-remote', plan['git_remote'], 'refs/heads/' + plan['git_branch']], env=environment, text=True).split()[0]
    if remote != commit:
        raise RuntimeError('Remote commit differs')
    # 已验证远端后推进当前检出分支；未提交文件保持原文，避免独立提交导致HEAD长期落后。
    checkout = sync_checkout(repo, plan['git_branch'], commit, CONTROL / 'git-checkout-sync')
    return {'model': label, 'commit': commit, 'branch': plan['git_branch'], 'author': author, 'remote_verified': True,
            'local_checkout_sync': checkout}


def cloud_publish(plan, index, label):
    """@brief 上传一个已完成模型的完整日志并逐文件验收。
    @param plan 冻结计划。
    @param index 模型顺序。
    @param label 已完成模型名称。
    @return 云端文件验收回执。
    @raises RuntimeError 文件漂移、大小或哈希不匹配。
    @note 只上传已结束模型子目录，另一模型的活动日志不会被快照或锁定。
    """
    load_results(plan, index)
    spec = importlib.util.spec_from_file_location('upload_helpers', '/mnt/public/code/lyk/lzy/maintenance/modelscope-upload-R1-mx/upload.py')
    archive = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(archive)
    api = archive.checked_api()
    root = Path(plan['evaluation']) / label
    prefix = 'runs/' + Path(plan['evaluation']).name + '/' + label
    metadata_files = {}
    if index == 0:
        # 数据和协议快照独立归档；只复制冻结静态文件，不触碰其他模型活动日志。
        metadata = CONTROL / 'cloud-metadata'
        metadata.mkdir(exist_ok=True)
        for source in [Path(plan['settings']), Path(plan['dataset']), Path(plan['evaluation']) / 'formal-config.yaml',
                       CONTROL / 'preflight.json', CONTROL / 'plan.json', CONTROL / 'execution-plan.md']:
            shutil.copy2(source, metadata / source.name)
        metadata_prefix = 'runs/' + Path(plan['evaluation']).name + '/metadata'
        metadata_files = {metadata_prefix + '/' + file.name: {'sha256': sha(file), 'bytes': file.stat().st_size} for file in metadata.iterdir() if file.is_file()}
        api.upload_folder(plan['modelscope_repo'], 'model', str(metadata), path_in_repo=metadata_prefix, commit_message='T1024 frozen metadata',
                          max_workers=2, use_cache=True, tracker_path=CONTROL / 'cloud-metadata-cache', disable_tqdm=True, sync_remote_repo=False)
    files = {str(path.relative_to(root)): {'sha256': sha(path), 'bytes': path.stat().st_size} for path in root.rglob('*') if path.is_file()}
    api.upload_folder(plan['modelscope_repo'], 'model', str(root), path_in_repo=prefix, commit_message='T1024 complete ' + label,
                      max_workers=2, use_cache=True, tracker_path=CONTROL / ('cloud-cache-' + label), disable_tqdm=True, sync_remote_repo=False)
    remote = {item.path: item for item in api.list_repo_files(plan['modelscope_repo'], 'model', recursive=True)}
    for name, value in files.items():
        # 完成事件之后文件必须稳定；上传成功返回不能代替哈希验收。
        item = remote.get(prefix + '/' + name)
        if item is None or item.size != value['bytes'] or sha(root / name) != value['sha256']:
            raise RuntimeError('Cloud size mismatch or local file drift')
        actual = archive.remote_sha(item)
        if actual is None and value['bytes'] <= 1024 * 1024:
            downloaded = api.download_file(plan['modelscope_repo'], 'model', prefix + '/' + name,
                                          cache_dir=CONTROL / 'cloud-verify', force=True, expected_sha256=value['sha256'])
            actual = sha(downloaded)
        if actual != value['sha256']:
            raise RuntimeError('Cloud hash mismatch: ' + name)
    for name, value in metadata_files.items():
        # 第一模型同时验收完整静态测试身份，不能仅验收模型输出而漏掉协议。
        item = remote.get(name)
        actual = archive.remote_sha(item) if item is not None else None
        if actual is None and item is not None and value['bytes'] <= 1024 * 1024:
            downloaded = api.download_file(plan['modelscope_repo'], 'model', name, cache_dir=CONTROL / 'cloud-verify', force=True, expected_sha256=value['sha256'])
            actual = sha(downloaded)
        if item is None or item.size != value['bytes'] or actual != value['sha256']:
            raise RuntimeError('Cloud metadata verification failed: ' + name)
    return {'model': label, 'files': files, 'metadata_files': metadata_files, 'prefix': prefix, 'verified': True, 'errors': []}


def main(kind):
    """@brief 独立消费不可变完成事件并续接已确认发布前缀。
    @param kind git或cloud，分别在对应CPU环境启动。
    @return 无。
    @raises RuntimeError 连续发布失败时保留队列和已验收回执。
    @note 网络重试只阻塞当前发布工作器，推理及另一工作器均继续。
    """
    plan = json.loads((CONTROL / 'plan.json').read_text())
    state_path = CONTROL / (kind + '-status.json')
    receipt_dir = CONTROL / (kind + '-receipts')
    completed = []
    with (CONTROL / (kind + '.lock')).open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if kind == 'git':
            # 用户要求先启动测试；此初始化文档发生在推理子进程已启动之后。
            repo, evaluation = Path(plan['repository']), Path(plan['evaluation'])
            document = (CONTROL / 'execution-plan.md').read_text()
            (repo / 'docs/experiments/test1024_five_model_execution_20261014.md').write_text(document)
            run_doc = repo / ('docs/experiments/runs/' + evaluation.name + '.md')
            if not run_doc.exists():
                run_doc.write_text(document)
            with (repo / 'docs/experiments/data_difficulty_code_changes.md').open('a') as stream:
                stream.write('\n\n' + datetime.datetime.now(datetime.timezone.utc).isoformat() + ' 五模型T1024维护模块：prepare_test1024.py、test1024_eval.py、workflow1024.py、async_publish1024.py。共享生成、评分、身份和完整批次续跑算法保持原样；CPU原始行保留、128题包含、1024身份唯一、五分词器全部实际提示一致验收已通过，GPU正式测试已由独立进程启动。逐模型文档Git与云端不持有推理锁，网络重试不阻塞下一模型。\n')
        for index, label in enumerate(plan['model_order']):
            receipt = receipt_dir / (label + '.json')
            if receipt.exists():
                # 已验收模型跳过，恢复不会重复提交或上传。
                completed.append(label)
                continue
            event_path = CONTROL / 'queue' / (f'{index:02d}-' + label + '.json')
            atomic(state_path, {'status': 'waiting', 'pid': os.getpid(), 'current_model': label, 'completed_models': completed})
            while not event_path.exists():
                time.sleep(1)
            for attempt in range(1, 7):
                try:
                    atomic(state_path, {'status': 'publishing', 'pid': os.getpid(), 'current_model': label, 'completed_models': completed, 'attempt': attempt})
                    value = git_publish(plan, index, label) if kind == 'git' else cloud_publish(plan, index, label)
                    value['checked_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    atomic(receipt, value)
                    completed.append(label)
                    break
                except Exception as error:
                    # 保留失败与重试台账，不能把网络失败当作模型答错。
                    atomic(state_path, {'status': 'failed' if attempt == 6 else 'retrying', 'pid': os.getpid(), 'current_model': label,
                                        'completed_models': completed, 'attempt': attempt, 'error': str(error)[:800]})
                    if attempt == 6:
                        raise
                    time.sleep(min(20 * attempt, 120))
        atomic(state_path, {'status': 'completed', 'pid': os.getpid(), 'completed_models': completed})


if __name__ == '__main__':
    main(sys.argv[1])
