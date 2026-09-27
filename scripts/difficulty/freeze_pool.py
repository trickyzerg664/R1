"""冻结并校验 Search-R1 正式 P/D/T；运行前须确定最终 tokenizer 和 prompt 长度。"""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
from transformers import AutoTokenizer
from verl.experimental.difficulty.pool_preparation import freeze_splits, validate_splits


def digest(path):
    """流式计算文件哈希，清单可在目标机独立复验。"""
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def verify(root, data_root, model):
    """验证输入身份、tokenizer 身份、产物哈希及分组互斥；不重新抽题。"""
    manifest = json.loads((root / 'manifest.json').read_text())
    if manifest.get('schema_version') != 1:
        raise ValueError('Unsupported split manifest schema')
    for name, expected in manifest['input_sha256'].items():
        if digest(data_root / 'datasets/nq_hotpotqa_train' / name) != expected:
            raise ValueError(f'Input changed: {name}')
    for name, expected in manifest['tokenizer_sha256'].items():
        if digest(model / name) != expected:
            raise ValueError(f'Tokenizer changed: {name}')
    frames = {}
    for part in ('P', 'D', 'T'):
        path = root / f'{part}.parquet'
        if digest(path) != manifest['output_sha256'][path.name]:
            raise ValueError(f'Output changed: {path.name}')
        frames[part] = pd.read_parquet(path)
        entries = manifest['samples'][part]
        if list(frames[part]['question_id']) != [entry['question_id'] for entry in entries]:
            raise ValueError(f'Manifest row order differs: {part}')
    validate_splits(frames, manifest['sizes'])
    print('P/D/T 校验通过：' + ', '.join(f'{part}={len(frames[part])}' for part in ('P', 'D', 'T')))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--model', type=Path, help='默认 data-root/models/Qwen2.5-3B')
    parser.add_argument('--p-size', type=int, default=10000)
    parser.add_argument('--d-size', type=int, default=1000)
    parser.add_argument('--t-size', type=int, default=2000)
    parser.add_argument('--max-prompt-length', type=int, default=256)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    data_root = args.data_root.resolve()
    model = (args.model or data_root / 'models/Qwen2.5-3B').resolve()
    output = args.output_dir.resolve()
    if args.verify:
        verify(output, data_root, model)
        return
    if output.exists() and any(output.iterdir()):
        parser.error('输出目录已有文件；请用 --verify 检查，或为新配置选择新目录')
    paths = {name: data_root / 'datasets/nq_hotpotqa_train' / name for name in ('train.parquet', 'test.parquet')}
    tokenizer_files = {name: model / name for name in ('tokenizer_config.json', 'tokenizer.json', 'vocab.json', 'merges.txt')
                       if (model / name).is_file()}
    if not all(path.is_file() for path in paths.values()) or not tokenizer_files:
        parser.error('缺少原始 parquet 或 tokenizer 文件')
    sizes = {'P': args.p_size, 'D': args.d_size, 'T': args.t_size}
    tokenizer = AutoTokenizer.from_pretrained(str(model), local_files_only=True)

    def token_length(prompt):
        # 与 RLHFDataset 的 chat template 和 add_generation_prompt 保持一致。
        chat = prompt.tolist() if hasattr(prompt, 'tolist') else prompt
        rendered = (tokenizer.apply_chat_template(chat, add_generation_prompt=True, tokenize=False)
                    if tokenizer.chat_template else chat[0]['content'])
        return len(tokenizer(rendered)['input_ids'])

    train, test = (pd.read_parquet(paths[name]) for name in ('train.parquet', 'test.parquet'))
    frames, manifest = freeze_splits(train, test, sizes, token_length, args.max_prompt_length, args.seed)
    manifest['input_sha256'] = {name: digest(path) for name, path in paths.items()}
    manifest['tokenizer_sha256'] = {name: digest(path) for name, path in tokenizer_files.items()}
    output.mkdir(parents=True, exist_ok=True)
    manifest['output_sha256'] = {}
    # manifest 最后原子发布；中断留下的部分输出不能被当作正式冻结数据。
    for part in ('P', 'D', 'T'):
        path = output / f'{part}.parquet'
        temporary = output / f'{part}.parquet.partial'
        frames[part].to_parquet(temporary, index=False)
        temporary.replace(path)
        manifest['output_sha256'][path.name] = digest(path)
    temporary = output / 'manifest.json.partial'
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    temporary.replace(output / 'manifest.json')
    verify(output, data_root, model)
    print(f'正式题池已冻结：{output}')


if __name__ == '__main__':
    main()
