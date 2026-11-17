"""配置、文件身份和问题规范化，共用逻辑不加载 GPU。"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import string


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def normalize(text):
    text = str(text).lower().translate(str.maketrans('', '', string.punctuation))
    return ' '.join(re.sub(r'\b(a|an|the)\b', ' ', text).split())


def contains(answer, text):
    key = normalize(answer)
    return bool(key) and (' ' + key + ' ') in (' ' + normalize(text) + ' ')


def read_jsonl(path):
    with Path(path).open(encoding='utf-8-sig') as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def write_jsonl(path, rows):
    with Path(path).open('w', encoding='utf-8') as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + '\n')


def load_config(path):
    import yaml
    config = yaml.safe_load(Path(path).read_text(encoding='utf-8'))
    config['_config_path'] = str(Path(path).resolve())
    return config


def configured_path(value):
    expanded = os.path.expanduser(os.path.expandvars(str(value or '')))
    if not expanded or '$' in expanded:
        raise ValueError('Required path is unset: ' + str(value))
    return Path(expanded).resolve()


def tokenizer_identity(path):
    """分词器文件变化必须生成新数据版本，不能继续使用旧 token 清单。"""
    root = Path(path)
    names = ['tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json', 'vocab.json', 'merges.txt']
    hashes = {name: sha256(root / name) for name in names if (root / name).is_file()}
    if not hashes:
        raise ValueError('No local tokenizer files: ' + str(root))
    return hashes
