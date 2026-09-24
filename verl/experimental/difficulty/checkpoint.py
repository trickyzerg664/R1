"""[data-difficulty] 完整本地 checkpoint 的写入协议，独立于 Ray 和训练器。"""
import json
from pathlib import Path
import torch
from .state import atomic_json, atomic_torch_save, file_hash, capture_rng, restore_rng


def read_checkpoint(path):
    # 完成标记含文件哈希；未完成或损坏的 checkpoint 不允许用于分支或续训。
    """验证完成标记和逐文件哈希后读取元数据。
    检查会读取完整权重，耗时随模型大小增加；不能只看目录名判断 checkpoint 可用。
    """
    path = Path(path)
    marker = path / 'COMPLETE.json'
    if not marker.is_file():
        raise ValueError(f'Incomplete checkpoint: {path}')
    manifest = json.loads(marker.read_text())
    if manifest.get('schema_version') != 1:
        raise ValueError('Unsupported checkpoint schema')
    if not {'driver.pt', 'metadata.json'}.issubset(manifest['files']):
        raise ValueError('Checkpoint manifest is missing required state files')
    for name, digest in manifest['files'].items():
        target = path / name
        if not target.resolve().is_relative_to(path.resolve()) or not target.is_file() or file_hash(target) != digest:
            raise ValueError(f'Checkpoint integrity failure: {name}')
    return json.loads((path / 'metadata.json').read_text())


def save_checkpoint(path, driver_state, metadata, save_actor):
    # worker 回调同步完成后再发布标记；已有完整结果不可覆盖，失败目录可以重试。
    """先同步保存全部 actor/rank 状态，再提交 driver 和最后的完成标记。
    完整目录禁止覆盖；未完成目录可重试，但任务必须独占该输出位置。
    """
    path = Path(path)
    if (path / 'COMPLETE.json').exists():
        raise FileExistsError(f'Checkpoint already complete: {path}')
    path.mkdir(parents=True, exist_ok=True)
    save_actor(str(path / 'actor'))
    atomic_torch_save(path / 'driver.pt', driver_state)
    atomic_json(path / 'metadata.json', {'schema_version': 1, **metadata})
    files = {str(p.relative_to(path)): file_hash(p) for p in sorted(path.rglob('*')) if p.is_file()}
    atomic_json(path / 'COMPLETE.json', {'schema_version': 1, 'files': files})


def load_driver(path):
    # 此入口仅接受本项目自有、已校验的 checkpoint；torch 格式包含 RNG 等 Python 对象。
    """读取本项目生成的可信完整 checkpoint，包含无法用纯权重模式表示的 RNG 对象。
    此接口不接受来源不明的 pickle 文件；模型及各 rank 状态由对应适配恢复。
    """
    read_checkpoint(path)
    return torch.load(Path(path) / 'driver.pt', map_location='cpu', weights_only=False)


def runtime_state(sharding_manager=None):
    # rollout 的 CUDA 随机流由 sharding manager 管理，必须与训练随机流一起保存。
    """保存训练随机流以及 vLLM sharding manager 的生成随机流。
    评分前后的快照恢复使分桶调用不会改变随后训练的随机位置。
    """
    state = {'rng': capture_rng(), 'rollout': {}}
    if sharding_manager is not None:
        for key in ('torch_random_states', 'gen_random_states'):
            value = getattr(sharding_manager, key, None)
            state['rollout'][key] = value.clone().cpu() if value is not None else None
    return state


def restore_runtime(state, sharding_manager=None):
    """将随机流快照还原到对应 driver 或 worker，不能跨 rank 互换。
    """
    restore_rng(state['rng'])
    if sharding_manager is not None:
        for key, value in state['rollout'].items():
            setattr(sharding_manager, key, value)


def save_rank_state(path, rank, world_size, optimizer, scheduler, scaler, runtime):
    # 采用同拓扑的 rank 本地 optimizer 分片；恢复前由元数据校验 world size 和全部训练配置。
    """保存当前 rank 的 optimizer 分片、scheduler、scaler 及随机流。
    仅支持同节点数量、GPU 数与 FSDP 包装配置恢复，不实现跨拓扑重分片。
    """
    atomic_torch_save(Path(path) / f'rank_{rank}.pt', {
        'schema_version': 1, 'rank': rank, 'world_size': world_size,
        'optimizer': optimizer.state_dict(), 'scheduler': scheduler.state_dict(),
        'scaler': scaler.state_dict(), 'runtime': runtime})


def load_rank_state(path, rank, world_size, optimizer, scheduler, scaler):
    """在模型权重已加载后补回该 rank 的训练状态。
    先核对 rank 和 world size，配置来源另外由 driver 校验；恢复后不能再次 warmup。
    """
    state = torch.load(Path(path) / f'rank_{rank}.pt', map_location='cpu', weights_only=False)
    if state['schema_version'] != 1 or state['rank'] != rank or state['world_size'] != world_size:
        raise ValueError('Rank checkpoint requires identical distributed topology')
    optimizer.load_state_dict(state['optimizer'])
    scheduler.load_state_dict(state['scheduler'])
    scaler.load_state_dict(state['scaler'])
    return state['runtime']
