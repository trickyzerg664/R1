"""一次性上传已完成语义复核文件；CPU运行，不创建定时任务或重新上传权重。"""
import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
import shutil
from pathlib import Path

CONTROL = Path('/mnt/public/code/lyk/lzy/maintenance/test1024-five-models-20261014')


def sha(path):
    """
    @brief 计算已冻结小型复核文件的内容身份。
    @param path 已存在普通文件的Path对象。
    @return 十六进制SHA256字符串。
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    """
    @brief 原子保存上传状态或验收回执。
    @param path 输出JSON的Path对象。
    @param value 可序列化字典。
    @return 无。
    @note 临时文件在同目录替换，不修改原始测试结果。
    """
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def main():
    """
    @brief 上传五模型复核及简短汇总，逐文件核验云端大小和哈希。
    @return 无。
    @raises RuntimeError 未完整复核、链接文件、云端文件不匹配或本地漂移时抛出。
    @note 复用已授权账号和上传SDK；独占上传锁，保留本地与云端原文件。
    """
    state_path = CONTROL / 'semantic-upload-status.json'
    # 与原始结果发布器共用锁，拒绝并发上传；退出自动释放，无重复守护进程。
    with (CONTROL / 'cloud.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            plan = json.loads((CONTROL / 'plan.json').read_text())
            run = Path(plan['evaluation'])
            review = run / 'semantic-review'
            summaries = json.loads((review / 'status.json').read_text())['models']
            # 不把未审完模型当作完成；题量固定且待审为零才允许发布。
            if len(summaries) != 5 or any(not s['review_complete'] or s['pending'] or s['n'] != 1024 for s in summaries):
                raise RuntimeError('存在未完整复核模型')
            snapshot = CONTROL / 'semantic-upload-snapshot'
            snapshot.mkdir(exist_ok=True)
            # 仅复制已完成复核目录和简短汇总，不遍历权重或原始大型轨迹。
            shutil.copytree(review, snapshot / 'semantic-review', dirs_exist_ok=True)
            shutil.copy2(run / 'TEST_RESULTS_SUMMARY.md', snapshot / 'TEST_RESULTS_SUMMARY.md')
            for summary in summaries:
                name = summary['model']
                shutil.copytree(run / name / 'T1024/llm-as-a-judge', snapshot / name / 'T1024/llm-as-a-judge', dirs_exist_ok=True)
            files = {}
            # 拒绝符号链接并保存逐文件身份，后续验收只认本次冻结字节。
            for path in sorted(snapshot.rglob('*')):
                if path.is_symlink():
                    raise RuntimeError('复核快照包含符号链接')
                if path.is_file():
                    files[str(path.relative_to(snapshot))] = {'bytes': path.stat().st_size, 'sha256': sha(path)}
            spec = importlib.util.spec_from_file_location('upload_helpers', '/mnt/public/code/lyk/lzy/maintenance/modelscope-upload-R1-mx/upload.py')
            helpers = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(helpers)
            # 现有认证函数同时校验账号与私有仓库，凭证不写入日志。
            api = helpers.checked_api()
            prefix = 'runs/' + run.name
            save(state_path, {'status': 'uploading', 'pid': os.getpid(), 'prefix': prefix, 'files': len(files)})
            api.upload_folder(plan['modelscope_repo'], 'model', str(snapshot), path_in_repo=prefix,
                              commit_message='T1024 five-model semantic judgments and readable summary',
                              max_workers=2, use_cache=True, tracker_path=CONTROL / 'semantic-upload-cache',
                              disable_tqdm=True, sync_remote_repo=False)
            remote = {item.path: item for item in api.list_repo_files(plan['modelscope_repo'], 'model', recursive=True)}
            # 上传返回成功不代替验收；云端缺哈希时下载对应文件复核。
            for name, expected in files.items():
                item = remote.get(prefix + '/' + name)
                if item is None or item.size != expected['bytes'] or sha(snapshot / name) != expected['sha256']:
                    raise RuntimeError('文件缺失、大小或本地身份变化：' + name)
                actual = helpers.remote_sha(item)
                if actual is None:
                    downloaded = api.download_file(plan['modelscope_repo'], 'model', prefix + '/' + name,
                                                   cache_dir=CONTROL / 'semantic-cloud-verify', force=True,
                                                   expected_sha256=expected['sha256'])
                    actual = sha(Path(downloaded))
                if actual != expected['sha256']:
                    raise RuntimeError('云端内容哈希不一致：' + name)
            receipt = {'status': 'completed', 'repo': plan['modelscope_repo'], 'prefix': prefix,
                       'verified': True, 'errors': [], 'files': files,
                       'bytes': sum(item['bytes'] for item in files.values()),
                       'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
            save(CONTROL / 'semantic-upload-verification.json', receipt)
            save(state_path, {k: v for k, v in receipt.items() if k != 'files'})
        except Exception as error:
            # 失败明确记录；保留快照与缓存，便于授权范围内续传，不删除云端文件。
            save(state_path, {'status': 'failed', 'error': str(error)[:800], 'pid': os.getpid()})
            raise


if __name__ == '__main__':
    main()
