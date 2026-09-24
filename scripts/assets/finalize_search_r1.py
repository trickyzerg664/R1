"""Normalize the upstream tar-wrapped corpus and validate downloaded assets."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tarfile


# [data-difficulty] 可独立重跑后处理，无需重新下载已通过哈希校验的原始资产。
def finalize_assets(root):
    import pyarrow.parquet as pq
    from transformers import AutoConfig, AutoTokenizer
    from safetensors import safe_open
    corpus_path = root/'retrieval/wiki18/wiki-18.jsonl'
    corpus_hash = hashlib.sha256()
    rows = 0
    # [data-difficulty] 文件扩展名不代表实际格式；识别上游 gzip 解压后的 tar 容器。
    if tarfile.is_tarfile(corpus_path):
        # [data-difficulty] 只读取唯一普通 JSONL 成员，写到固定路径，不采用归档内的目录名。
        with tarfile.open(corpus_path, 'r:') as archive:
            members = [m for m in archive.getmembers() if m.isfile() and m.name.endswith('.jsonl')]
            if len(members) != 1:
                raise ValueError('Expected exactly one regular JSONL corpus member')
            member = members[0]
            temporary = corpus_path.with_suffix('.jsonl.extracted.partial')
            with archive.extractfile(member) as src, temporary.open('wb') as dst:
                for block in iter(lambda: src.read(8*1024*1024), b''):
                    dst.write(block)
                    rows += block.count(b'\n')
                    corpus_hash.update(block)
            if temporary.stat().st_size != member.size:
                raise ValueError('Extracted corpus size mismatch')
        # [data-difficulty] 仅替换本脚本生成的 tar 中间文件，保留下载的原始 .gz。
        temporary.replace(corpus_path)
    else:
        with corpus_path.open('rb') as src:
            for block in iter(lambda: src.read(8*1024*1024), b''):
                rows += block.count(b'\n')
                corpus_hash.update(block)
    corpus = {'path': str(corpus_path), 'bytes': corpus_path.stat().st_size,
              'newline_count': rows, 'sha256': corpus_hash.hexdigest()}
    validation = {'datasets': {}, 'models': {}}
    # [data-difficulty] 按批统计真实行数和来源分布，避免把上游标称规模当作本地验证结果。
    for split in ('train', 'test'):
        path = root/'datasets/nq_hotpotqa_train'/f'{split}.parquet'
        parquet = pq.ParquetFile(path)
        counts = Counter()
        for batch in parquet.iter_batches(columns=['data_source']):
            counts.update(batch.column(0).to_pylist())
        validation['datasets'][split] = {'rows': parquet.metadata.num_rows,
            'by_source': dict(counts), 'columns': parquet.schema_arrow.names}
        assert sum(counts.values()) == parquet.metadata.num_rows
    # [data-difficulty] 离线解析配置、tokenizer 和权重头部；该检查不等价于完整模型 GPU 前向。
    for name in ('Qwen2.5-3B', 'e5-base-v2'):
        directory = root/'models'/name
        config = AutoConfig.from_pretrained(str(directory), local_files_only=True)
        tokenizer = AutoTokenizer.from_pretrained(str(directory), local_files_only=True)
        index = directory/'model.safetensors.index.json'
        tensors = {}
        for path in sorted(directory.glob('*.safetensors')):
            with safe_open(str(path), framework='pt', device='cpu') as model_file:
                for key in model_file.keys():
                    tensors[key] = path.name
        if index.exists():
            assert tensors == json.loads(index.read_text())['weight_map']
        validation['models'][name] = {'model_type': config.model_type,
            'tokenizer_class': type(tokenizer).__name__, 'tensor_count': len(tensors)}
    # [data-difficulty] 确认取出的是可读 JSONL，并包含检索服务要求的 id/contents 字段。
    with corpus_path.open(encoding='utf-8') as src:
        first = json.loads(src.readline())
    assert 'contents' in first and 'id' in first
    validation['corpus_first_record_keys'] = list(first)
    validation['corpus'] = corpus
    (root/'asset-validation.json').write_text(json.dumps(validation, indent=2))
    return validation, corpus


# [data-difficulty] 独立恢复入口只接受原始资产已校验、索引已合并的任务。
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('/root/data/search-r1'))
    args = parser.parse_args()
    root = args.root.resolve()
    import fcntl
    lock = (root/'runs/asset-download/download.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    status_path = root/'runs/asset-download/status.json'
    status = json.loads(status_path.read_text())
    if len(status.get('files', {})) != 26 or not all(v['state'] == 'verified' for v in status['files'].values()):
        raise RuntimeError('All 26 downloads must be verified before finalizing')
    index = root/'retrieval/wiki18/e5_Flat.index'
    assert index.stat().st_size == status['index']['bytes']

    # [data-difficulty] 原子更新状态，校验失败时保留可诊断的失败类型。
    def save():
        temporary = status_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(status, indent=2))
        temporary.replace(status_path)

    status['phase'] = 'validating_assets'
    status.pop('error_type', None)
    save()
    try:
        validation, corpus = finalize_assets(root)
        status.update(validation=validation, corpus=corpus, phase='complete',
                      completed_at=datetime.now(timezone.utc).isoformat())
        save()
        print(json.dumps(validation, indent=2), flush=True)
        print('All assets prepared and validated', flush=True)
    except BaseException as exc:
        status.update(phase='failed', error_type=type(exc).__name__)
        save()
        raise


if __name__ == '__main__':
    main()
