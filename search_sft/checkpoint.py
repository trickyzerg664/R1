"""只在 optimizer 边界保存，完整状态与 HF 导出各自独立。"""
from __future__ import annotations
import json
from pathlib import Path
import random
import re
import shutil
import numpy as np
import torch
import torch.distributed as dist
from .common import write_json


def rng_state():
    return {'python':random.getstate(), 'numpy':np.random.get_state(), 'torch':torch.get_rng_state(),
            'cuda':torch.cuda.get_rng_state() if torch.cuda.is_available() else None}


def restore_rng(state):
    random.setstate(state['python']); np.random.set_state(state['numpy']); torch.set_rng_state(state['torch'])
    if state['cuda'] is not None:
        torch.cuda.set_rng_state(state['cuda'])


def verify_signature(saved, current):
    if saved != current:
        raise ValueError('Resume code/config/data/model/stage/world_size identity mismatch')


def save(engine, directory, cursor, updates, signature):
    """先发布完成标记，再清理同一 run 的旧状态；所有 rank 均调用引擎保存。"""
    root = Path(directory).resolve()
    root.mkdir(parents=True,exist_ok=True)
    tag = f'step_{cursor:08d}'
    previous = json.loads((root/'latest.json').read_text())['tag'] if (root/'latest.json').is_file() else None
    error=[None]
    if dist.get_rank()==0 and (root/tag).exists():
        error[0]='Checkpoint tag already exists: '+tag
    dist.broadcast_object_list(error,src=0)
    if error[0]:raise ValueError(error[0])
    state = {'cursor':cursor, 'updates':updates, 'signature':signature}
    # 引擎会附加 ds_version/config 等字段，业务状态使用独立命名空间。
    ok = engine.save_checkpoint(str(root),tag=tag,client_state={'search_sft':state},save_latest=False)
    if ok is False:
        raise RuntimeError('DeepSpeed checkpoint save failed')
    torch.save(rng_state(),root/tag/f'rng_rank{dist.get_rank()}.pt')
    dist.barrier()
    if dist.get_rank()==0:
        write_json(root/tag/'complete.json',state)
        write_json(root/'latest.json',{'tag':tag})
        if previous and previous != tag:
            old = (root/previous).resolve()
            if not re.fullmatch(r'step_\d+',previous) or old.parent != root:
                raise ValueError('Invalid prior checkpoint path')
            shutil.rmtree(old)
    dist.barrier()
    return tag


def load(engine, directory, signature):
    root = Path(directory)
    tag = json.loads((root/'latest.json').read_text())['tag']
    if not re.fullmatch(r'step_\d+',tag):
        raise ValueError('Invalid checkpoint tag')
    complete = json.loads((root/tag/'complete.json').read_text())
    verify_signature(complete['signature'],signature)
    path,client = engine.load_checkpoint(str(root),tag=tag)
    state=client.get('search_sft') if client is not None else None
    if path is None or state != complete:
        raise ValueError('Incomplete/inconsistent checkpoint client state')
    # 引擎和模型初始化会消费随机数，因此随机状态最后恢复。
    restore_rng(torch.load(root/tag/f'rng_rank{dist.get_rank()}.pt',map_location='cpu',weights_only=False))
    return state
