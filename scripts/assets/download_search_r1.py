"""Download pinned Search-R1 assets, verify them and prepare retrieval files.

Run with the project's searchr1 Python. All files/caches live on --root.
Re-running resumes Hub downloads and reuses verified artifacts.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import threading
import time
from urllib.parse import quote

# [data-difficulty] 固定仓库提交，确保各次实验使用同一批模型、语料和索引。
REPOS = [
    ('model', 'Qwen/Qwen2.5-3B', '3aab1f1954e9cc14eb9509a215f9e5ca08227a9b', 'models/Qwen2.5-3B'),
    ('model', 'intfloat/e5-base-v2', 'f52bf8ec8c7124536f0efb74aca902b2995e5bcd', 'models/e5-base-v2'),
    ('dataset', 'PeterJinGo/nq_hotpotqa_train', 'b7d80abfee334a7a91cb377544f09180d58b34f6', 'datasets/nq_hotpotqa_train'),
    ('dataset', 'PeterJinGo/wiki-18-e5-index', 'a4d31160a035f30764604f4827cd8f1d0315eb86', 'retrieval/wiki18'),
    ('dataset', 'PeterJinGo/wiki-18-corpus', '69c1c00ffe7c5554c68d8548355cb22e46aabc51', 'retrieval/wiki18'),
]


# [data-difficulty] 下载、校验和后处理的统一入口；所有缓存和临时文件写到数据卷。
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('/root/data/search-r1'))
    parser.add_argument('--workers', type=int, default=3)
    args = parser.parse_args()
    root = args.root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    for name in ('cache/huggingface', 'tmp', 'runs/asset-download'):
        (root / name).mkdir(parents=True, exist_ok=True)
    # [data-difficulty] 必须在导入 Hub 客户端前设置缓存目录，避免占满代码所在磁盘。
    os.environ.update(HF_HOME=str(root/'cache/huggingface'),
                      HF_HUB_CACHE=str(root/'cache/huggingface/hub'),
                      HF_DATASETS_CACHE=str(root/'cache/huggingface/datasets'),
                      TMPDIR=str(root/'tmp'), HF_HUB_DISABLE_XET='1',
                      HF_HUB_DOWNLOAD_TIMEOUT='120', HF_HUB_ETAG_TIMEOUT='60',
                      HF_HUB_DISABLE_PROGRESS_BARS='1')
    from huggingface_hub import HfApi, hf_hub_download
    import fcntl
    # [data-difficulty] 跨进程互斥，防止两个任务同时改写分段文件和状态。
    lock_file = (root/'runs/asset-download/download.lock').open('w')
    fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    status_path = root/'runs/asset-download/status.json'
    manifest_path = root/'asset-manifest.json'
    status = {'started_at': datetime.now(timezone.utc).isoformat(), 'phase': 'metadata', 'files': {}}
    state_lock = threading.Lock()

    # [data-difficulty] 临时文件写完再替换，避免读到半份 JSON；并发调用处还需持有 state_lock。
    def save():
        temporary = status_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(status, indent=2))
        temporary.replace(status_path)

    def log(message):
        print(datetime.now(timezone.utc).isoformat(), message, flush=True)

    # [data-difficulty] 流式计算完整文件哈希，不把数十 GB 的索引读入内存。
    def digest(path):
        h = hashlib.sha256()
        with path.open('rb') as f:
            for block in iter(lambda: f.read(8*1024*1024), b''):
                h.update(block)
        return h.hexdigest()

    save()
    api = HfApi()
    files = []
    # [data-difficulty] 以官方元信息取得文件大小和 SHA-256，镜像仅承担传输。
    for kind, repo, revision, subdir in REPOS:
        info = api.repo_info(repo, repo_type=kind, revision=revision, files_metadata=True, timeout=60)
        assert info.sha == revision
        for entry in info.siblings:
            name = entry.rfilename
            if name == '.gitattributes':
                continue
            if repo == 'intfloat/e5-base-v2' and (name.startswith(('onnx/', 'openvino/')) or name == 'pytorch_model.bin'):
                continue
            files.append(dict(repo_type=kind, repo=repo, revision=revision, name=name,
                              subdir=subdir, size=entry.size,
                              sha256=getattr(entry.lfs, 'sha256', None)))
    manifest_path.write_text(json.dumps({'repositories': REPOS, 'files': files}, indent=2))
    # [data-difficulty] 为原下载文件、索引拼接副本和语料解包保留空间。
    required = sum(f['size'] for f in files)
    if shutil.disk_usage(root).free < required*2 + 30*1024**3:
        raise RuntimeError('Insufficient headroom for downloads, assembled index and extracted corpus')
    log(f'Metadata ready: {len(files)} files; download bytes={required}')
    status['phase'] = 'downloading'
    save()

    # [data-difficulty] 大文件并发按字节段续传；最终仍由调用方检查整文件哈希。
    def ranged_download(item, target):
        import requests
        if target.exists() and target.stat().st_size == item['size']:
            return target
        target.parent.mkdir(parents=True, exist_ok=True)
        pieces = target.parent / ('.' + target.name + '.parts')
        pieces.mkdir(exist_ok=True)
        size = item['size']
        chunk_size = 32 * 1024 * 1024
        starts = list(range(0, size, chunk_size))
        prefix = 'datasets/' if item['repo_type'] == 'dataset' else ''
        base_url = ('https://hf-mirror.com/' + prefix + item['repo'] + '/resolve/'
                    + item['revision'] + '/' + quote(item['name']))
        key = str(target.relative_to(root))

        # [data-difficulty] 以字节偏移命名分段，重试从已写入的偏移继续。
        def part(start):
            end = min(start + chunk_size, size) - 1
            path = pieces / str(start)
            expected = end - start + 1
            if path.exists() and path.stat().st_size == expected:
                return expected
            for attempt in range(8):
                try:
                    # Distinct query prevents intermediate caches mixing byte ranges.
                    temporary = path.with_suffix('.partial')
                    offset = temporary.stat().st_size if temporary.exists() else 0
                    if offset == expected:
                        temporary.replace(path)
                        return expected
                    if offset > expected:
                        raise RuntimeError('Oversized partial range')
                    range_start = start + offset
                    url = base_url + f'?download=true&range={range_start}-{end}'
                    session = requests.Session()
                    # [data-difficulty] 使用已验证可达的镜像直连，不继承本机较慢的代理链路。
                    session.trust_env = False
                    with session.get(url, headers={'Range': f'bytes={range_start}-{end}'},
                                      stream=True, timeout=(30, 60)) as response:
                        response.raise_for_status()
                        # [data-difficulty] 严格核对范围，防止缓存返回错误分段后被拼入目标文件。
                        if response.status_code != 206 or response.headers.get('Content-Range') != f'bytes {range_start}-{end}/{size}':
                            raise RuntimeError('Invalid Content-Range')
                        with temporary.open('ab') as out:
                            for block in response.iter_content(1024*1024):
                                out.write(block)
                    if temporary.stat().st_size != expected:
                        raise RuntimeError('Incomplete range')
                    temporary.replace(path)
                    return expected
                except Exception as exc:
                    if attempt == 7:
                        raise RuntimeError(f'Range failed: {key} offset={start}: {type(exc).__name__}') from None
                    time.sleep(min(2*(attempt+1), 12))

        # [data-difficulty] 完成顺序可能不同；落盘拼接时仍按字节偏移排序。
        completed = 0
        with ThreadPoolExecutor(max_workers=8) as pool:
            for future in as_completed([pool.submit(part, start) for start in starts]):
                completed += future.result()
                with state_lock:
                    status['files'][key]['downloaded_bytes'] = completed
                    save()
        temporary = target.with_suffix(target.suffix + '.partial')
        with temporary.open('wb') as out:
            for start in starts:
                with (pieces/str(start)).open('rb') as src:
                    shutil.copyfileobj(src, out, 8*1024*1024)
        temporary.replace(target)
        return target

    # [data-difficulty] 大文件用分段传输，小文件用 Hub；两者统一校验并记录状态。
    def download(item):
        target = root/item['subdir']/item['name']
        key = str(target.relative_to(root))
        for attempt in range(1, 6):
            try:
                with state_lock:
                    status['files'][key] = {'state': 'downloading', 'bytes': item['size'], 'attempt': attempt}
                    save()
                if item['size'] >= 32*1024*1024:
                    path = ranged_download(item, target)
                else:
                    path = Path(hf_hub_download(repo_id=item['repo'], filename=item['name'],
                        repo_type=item['repo_type'], revision=item['revision'], local_dir=root/item['subdir']))
                if path.stat().st_size != item['size']:
                    raise RuntimeError(f'File size mismatch: {key}')
                with state_lock:
                    status['files'][key]['state'] = 'verifying'
                    save()
                actual = digest(path)
                if item['sha256'] and actual != item['sha256']:
                    raise RuntimeError(f'SHA256 mismatch: {key}; manual inspection required')
                with state_lock:
                    status['files'][key].update(state='verified', sha256=actual)
                    save()
                pieces = target.parent / ('.' + target.name + '.parts')
                if pieces.exists():
                    shutil.rmtree(pieces)  # Only this downloader's verified temporary chunks.
                log(f'VERIFIED {key} ({item["size"]} bytes)')
                return
            except Exception as exc:
                log(f'Attempt {attempt} failed for {key}: {type(exc).__name__}: {exc}')
                if 'mismatch' in str(exc) or attempt == 5:
                    with state_lock:
                        status['files'][key].update(state='failed', error=type(exc).__name__)
                        save()
                    raise
                time.sleep(min(5*attempt, 25))

    try:
        # Small assets finish first, leaving the large retrieval files last.
        small = [f for f in files if f['size'] < 10*1024**3]
        large = [f for f in files if f['size'] >= 10*1024**3]
        for batch in (small, large):
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                for future in as_completed([pool.submit(download, item) for item in batch]):
                    future.result()
        status['phase'] = 'preparing_retrieval'
        save()
        directory = root/'retrieval/wiki18'
        index_path = directory/'e5_Flat.index'
        # [data-difficulty] 上游索引按固定 aa→ab 顺序拆分，不能按下载完成顺序合并。
        parts = [directory/'part_aa', directory/'part_ab']
        total = sum(p.stat().st_size for p in parts)
        temporary = directory/'e5_Flat.index.partial'
        assembled_hash = hashlib.sha256()
        with temporary.open('wb') as out:
            for part in parts:
                with part.open('rb') as src:
                    for block in iter(lambda: src.read(8*1024*1024), b''):
                        out.write(block)
                        assembled_hash.update(block)
        assert temporary.stat().st_size == total
        temporary.replace(index_path)
        status['index'] = {'path': str(index_path), 'bytes': total, 'sha256': assembled_hash.hexdigest()}
        save()
        log('Index assembled')
        corpus_path = directory/'wiki-18.jsonl'
        temporary = directory/'wiki-18.jsonl.partial'
        corpus_hash = hashlib.sha256()
        rows = 0
        # [data-difficulty] 这里只去掉 gzip 层；上游还含 tar 层，随后由 finalize_assets 取出 JSONL。
        with gzip.open(directory/'wiki-18.jsonl.gz', 'rb') as src, temporary.open('wb') as out:
            for block in iter(lambda: src.read(8*1024*1024), b''):
                if shutil.disk_usage(root).free < 10*1024**3:
                    raise RuntimeError('Less than 10 GiB free during corpus extraction')
                out.write(block)
                rows += block.count(b'\n')
                corpus_hash.update(block)
        temporary.replace(corpus_path)
        status['corpus'] = {'path': str(corpus_path), 'bytes': corpus_path.stat().st_size,
                            'newline_count': rows, 'sha256': corpus_hash.hexdigest()}
        log(f'Corpus extracted; newline count={rows}')
        status['phase'] = 'validating_assets'
        save()
        # [data-difficulty] 解包及数据/模型结构校验都通过后，才将任务标为 complete。
        from finalize_search_r1 import finalize_assets
        validation, corpus = finalize_assets(root)
        status['validation'] = validation
        status['corpus'] = corpus
        status['phase'] = 'complete'
        status['completed_at'] = datetime.now(timezone.utc).isoformat()
        save()
        log('All downloads verified and retrieval files prepared')
    except BaseException as exc:
        status['phase'] = 'failed'
        status['error_type'] = type(exc).__name__
        save()
        raise


if __name__ == '__main__':
    main()
