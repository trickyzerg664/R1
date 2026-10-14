"""CPU真实Git仓库回归，验证快进同步与用户文件/索引保护。"""
import os
import subprocess
import tempfile
from pathlib import Path
from git_checkout_sync import sync_checkout


def git(repo, *arguments, data=None, environment=None):
    """
    @brief 在临时仓库执行真实Git命令，失败即终止回归。
    @param repo 临时仓库Path对象。
    @param arguments Git参数字符串序列。
    @param data 可选标准输入字符串。
    @param environment 可选进程环境字典。
    @return Git输出字符串。
    @raises subprocess.CalledProcessError 命令失败时抛出。
    """
    return subprocess.check_output(['git', '-C', str(repo), *arguments], input=data, env=environment, text=True).strip()


def main():
    """
    @brief 使用独立索引真实提交验证文件保留、暂存拒绝、分叉拒绝及未物化内容拒绝。
    @return 无。
    @note 仅CPU临时目录，无远程网络，无生产仓库写入。
    """
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        repo = root / 'repo'
        repo.mkdir()
        git(repo, 'init', '-b', 'experiment')
        git(repo, 'config', 'user.name', 'CPU test')
        git(repo, 'config', 'user.email', 'cpu@example.invalid')
        (repo / 'docs').mkdir()
        doc = repo / 'docs/record.md'
        doc.write_text('initial\n')
        git(repo, 'add', '.')
        git(repo, 'commit', '-m', 'initial')
        old = git(repo, 'rev-parse', 'HEAD')
        # 模拟独立发布器：真实生成文档并commit-tree，但当前分支仍停在旧SHA。
        doc.write_text('initial\npublished\n')
        extra = repo / 'docs/new.md'
        extra.write_text('new evidence\n')
        environment = dict(os.environ, GIT_INDEX_FILE=str(root / 'publisher.index'))
        git(repo, 'read-tree', old, environment=environment)
        git(repo, 'add', 'docs', environment=environment)
        tree = git(repo, 'write-tree', environment=environment)
        target = git(repo, 'commit-tree', tree, '-p', old, data='published\n')
        # 发布后又追加日志及未追踪记录，同步应保留原字节。
        with doc.open('a') as stream:
            stream.write('uncommitted append\n')
        scratch = repo / 'docs/scratch.md'
        scratch.write_text('local only\n')
        before = {p: p.read_bytes() for p in [doc, extra, scratch]}
        saved_index = os.environ.get('GIT_INDEX_FILE')
        os.environ['GIT_INDEX_FILE'] = str(root / 'publisher.index')
        try:
            receipt = sync_checkout(repo, 'experiment', target, root / 'audit')
        finally:
            if saved_index is None:
                os.environ.pop('GIT_INDEX_FILE', None)
            else:
                os.environ['GIT_INDEX_FILE'] = saved_index
        assert receipt['synced'] and git(repo, 'rev-parse', 'HEAD') == target
        assert all(p.read_bytes() == content for p, content in before.items())
        assert Path(receipt['backup'], 'index.before').exists()
        # 用户有暂存内容时必须保持主index不变，不允许mixed reset丢失暂存状态。
        git(repo, 'add', 'docs/scratch.md')
        index = (repo / '.git/index').read_bytes()
        assert sync_checkout(repo, 'experiment', target, root / 'audit')['reason'] == 'staged_changes_preserved'
        assert (repo / '.git/index').read_bytes() == index
        git(repo, 'reset', '--mixed', target)
        # 指向祖先不是快进；远端尚未进入工作区的修改也必须拒绝。
        assert sync_checkout(repo, 'experiment', old, root / 'audit')['reason'] == 'diverged_history_preserved'
        git(repo, 'reset', '--mixed', old)
        doc.write_text('independent local change\n')
        assert sync_checkout(repo, 'experiment', target, root / 'audit')['reason'] == 'remote_content_not_materialized'
        assert git(repo, 'rev-parse', 'HEAD') == old
    print('PASSED: real_git_fast_forward, default_index, all_file_bytes_preserved, backup, staged_guard, ancestor_guard, materialized_guard')


if __name__ == '__main__':
    main()
