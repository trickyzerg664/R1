"""预分词数据与显式全局 batch：同题先分组，行可以随机训练。"""
from __future__ import annotations
import json
from pathlib import Path
import random
from .common import read_jsonl, sha256, tokenizer_identity


def load_release(directory, stage, model_path, allow_draft=False):
    root = Path(directory)
    manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    if not allow_draft and (manifest['status']!='final' or not manifest['evaluation_exclusions_complete']):
        raise ValueError('Training requires a final decontaminated release')
    if tokenizer_identity(model_path) != manifest['tokenizer_hashes']:
        raise ValueError('Tokenizer changed after data compilation')
    key = 'pilot' if stage == 'pilot' else 'train'
    def read(name):
        item = manifest['files'][name]
        path = root/item['path']
        if sha256(path) != item['sha256']:
            raise ValueError('Release data hash mismatch: '+name)
        return list(read_jsonl(path))
    train, val = read(key), read('val')
    if {r['question_id'] for r in train} & {r['question_id'] for r in val}:
        raise ValueError('Question crosses train/validation')
    return train, val, manifest


def global_batches(size, batch_size, seed):
    """尾批保留真实样本；不使用 DistributedSampler 的重复补齐。"""
    order = list(range(size))
    random.Random(seed).shuffle(order)
    return [order[i:i+batch_size] for i in range(0,size,batch_size)]


def micro_slots(indices, world_size):
    return [indices[i:i+world_size]+[None]*max(0,world_size-len(indices[i:i+world_size])) for i in range(0,len(indices),world_size)]


def model_batch(row, device, dummy_id=0):
    import torch
    ids = row['input_ids'] if row is not None else [dummy_id,dummy_id]
    inputs = torch.tensor([ids],dtype=torch.long,device=device)
    return {'input_ids':inputs, 'attention_mask':torch.ones_like(inputs),
            'position_ids':torch.arange(len(ids),device=device).unsqueeze(0), 'use_cache':False,
            'num_logits_to_keep':row['target_length']+1 if row is not None else 1}
