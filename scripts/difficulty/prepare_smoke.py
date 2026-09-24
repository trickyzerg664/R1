"""从已下载的原始训练 split 生成仅用于链路验收的小题集。"""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
from transformers import AutoTokenizer


def digest(path: Path) -> str:
    """流式记录输入/产物身份，避免读取整个 parquet 到额外字节缓存。"""
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--max-prompt-length', type=int, default=256)
    args = parser.parse_args()
    if args.max_prompt_length < 1:
        parser.error('--max-prompt-length 必须为正整数')
    data_root, output = args.data_root.resolve(), args.output_dir.resolve()
    source = data_root / 'datasets/nq_hotpotqa_train/train.parquet'
    model = data_root / 'models/Qwen2.5-3B'
    if not source.is_file() or not model.is_dir():
        parser.error('缺少原始训练 parquet 或 Qwen2.5-3B tokenizer')
    output.mkdir(parents=True, exist_ok=True)
    products = {name: output / f'{name}.parquet' for name in ('train', 'dev', 'score')}
    manifest_path = output / 'sample-manifest.json'
    # 已有完整烟测输入时保留原样；避免重试迁移时改写正在使用的小题集。
    if manifest_path.is_file() and all(path.is_file() for path in products.values()):
        print(f'烟测输入已存在，保持不变：{output}')
        return
    if manifest_path.exists() or any(path.exists() for path in products.values()):
        raise RuntimeError('烟测输出不完整；检查后使用新的 --output-dir 重新生成')

    tokenizer = AutoTokenizer.from_pretrained(str(model), local_files_only=True)
    frame = pd.read_parquet(source)
    chosen = {'train': [], 'dev': []}
    seen = set()
    # 固定来源顺序和每来源数量；仅验证调用链，不作为正式 P/D/T 或效果估计。
    for source_name in ('nq', 'hotpotqa'):
        subset = frame[frame['data_source'] == source_name]
        for _, row in subset.head(2000).iterrows():
            question_key = str(row['question']).strip().casefold()
            if question_key in seen:
                continue
            prompt = row['prompt'].tolist() if hasattr(row['prompt'], 'tolist') else row['prompt']
            rendered = (tokenizer.apply_chat_template(prompt, add_generation_prompt=True, tokenize=False)
                        if tokenizer.chat_template else prompt[0]['content'])
            if len(tokenizer(rendered)['input_ids']) > args.max_prompt_length:
                continue
            train_count = sum(item['data_source'] == source_name for item in chosen['train'])
            dev_count = sum(item['data_source'] == source_name for item in chosen['dev'])
            part = 'train' if train_count < 4 else 'dev'
            if part == 'dev' and dev_count >= 2:
                break
            chosen[part].append(row)
            seen.add(question_key)
    if len(chosen['train']) != 8 or len(chosen['dev']) != 4:
        raise RuntimeError('筛选后不足 8 训练题 / 4 开发题；请检查数据和长度设置')

    # parquet 和清单最后写入；中断后的部分产物必须人工检查，不当作已完成输入。
    for part, rows in chosen.items():
        pd.DataFrame(rows).to_parquet(products[part], index=False)
    pd.DataFrame(chosen['train'][:2]).to_parquet(products['score'], index=False)
    manifest = {
        'purpose': 'smoke-only',
        'source_sha256': digest(source),
        'max_prompt_length': args.max_prompt_length,
        'samples': {part: [{'data_source': str(row['data_source']), 'id': str(row['id']),
                            'question': str(row['question'])} for row in rows]
                    for part, rows in chosen.items()},
        'files_sha256': {name: digest(path) for name, path in products.items()},
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f'烟测输入已生成：{output}；train=8，dev=4，score=2')


if __name__ == '__main__':
    main()
