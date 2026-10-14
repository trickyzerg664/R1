"""同步独立发布器与当前检出分支，保留工作区文件及未提交记录。"""
import datetime
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path


def sync_checkout(repo, branch, target, audit_root):
    """
    @brief 将已在工作区生成的文档提交快进到当前分支和主索引，保留文件内容。
    @param repo Git仓库Path或路径字符串。
    @param branch 允许同步的当前分支名字符串。
    @param target 已验证远程提交SHA字符串。
    @param audit_root 仓库外审计和恢复快照目录Path或路径字符串。
    @return 含synced、旧新SHA、备份位置或跳过原因的字典。
    @raises RuntimeError Git执行失败或文件保护校验失败时抛出。
    @note 暂存内容、分叉、代码更新或尚未进入工作区的远程内容均不自动处理。
    """
    repo, audit_root = Path(repo), Path(audit_root)
    environment = dict(os.environ)
    # 发布器使用独立index；同步操作必须明确使用检出工作区的主index。
    environment.pop('GIT_INDEX_FILE', None)
    command = ['git', '-C', str(repo)]
    current_branch = subprocess.check_output(command + ['branch', '--show-current'], env=environment, text=True).strip()
    old = subprocess.check_output(command + ['rev-parse', 'HEAD'], env=environment, text=True).strip()
    if current_branch != branch:
        return {'synced': False, 'reason': 'different_checked_out_branch', 'head': old}
    # 已暂存用户内容不能被mixed reset改变；不允许通过同步覆盖另一条提交历史。
    if subprocess.run(command + ['diff', '--cached', '--quiet'], env=environment).returncode:
        return {'synced': False, 'reason': 'staged_changes_preserved', 'head': old}
    if subprocess.run(command + ['merge-base', '--is-ancestor', old, target], env=environment).returncode:
        return {'synced': False, 'reason': 'diverged_history_preserved', 'head': old}
    changed = subprocess.check_output(command + ['diff', '--name-only', '-z', old, target], env=environment).decode().split('\0')
    changed = [name for name in changed if name]
    # 仅处理发布器已物化的文档；真正新增远端代码或需要内容合并时保留现场。
    if any(not name.startswith('docs/') for name in changed):
        return {'synced': False, 'reason': 'non_document_updates_require_merge', 'head': old}
    for name in changed:
        local = repo / name
        remote = subprocess.run(command + ['show', target + ':' + name], env=environment, capture_output=True)
        if remote.returncode or not local.is_file() or not local.read_bytes().startswith(remote.stdout):
            return {'synced': False, 'reason': 'remote_content_not_materialized', 'path': name, 'head': old}
    dirty = subprocess.check_output(command + ['ls-files', '--modified', '--others', '--exclude-standard', '-z'], env=environment).decode().split('\0')
    paths = sorted(set(changed + [name for name in dirty if name]))
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    backup = audit_root / stamp
    backup.mkdir(parents=True, mode=0o700)
    before = {}
    # 保存主索引及所有受影响文件，支持恢复旧指针/暂存状态；不复制或修改GPU运行目录。
    git_dir = Path(subprocess.check_output(command + ['rev-parse', '--absolute-git-dir'], env=environment, text=True).strip())
    if (git_dir / 'index').exists():
        shutil.copy2(git_dir / 'index', backup / 'index.before')
    for name in paths:
        source = repo / name
        if source.is_file():
            destination = backup / 'files' / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            before[name] = hashlib.sha256(destination.read_bytes()).hexdigest()
    receipt = {'old_head': old, 'target': target, 'branch': branch, 'backup': str(backup), 'before_sha256': before}
    (backup / 'before.json').write_text(json.dumps(receipt, indent=2) + '\n')
    # mixed只更新分支/主索引，工作树文件不写入；禁止hard reset或强推。
    subprocess.run(command + ['reset', '--mixed', target], env=environment, check=True, capture_output=True)
    exact, appended, drift = [], [], []
    for name, expected in before.items():
        path = repo / name
        data = path.read_bytes() if path.is_file() else b''
        if hashlib.sha256(data).hexdigest() == expected:
            exact.append(name)
        elif data.startswith((backup / 'files' / name).read_bytes()):
            # 并行实验台账可追加新日志；完整原前缀保留时不误报为丢失。
            appended.append(name)
        else:
            drift.append(name)
    if drift:
        receipt.update(synced=False, reason='concurrent_file_change_needs_review', drift=drift)
    else:
        receipt.update(synced=True, preserved_files=len(exact), appended_files=appended)
    (backup / 'after.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt
