"""[data-difficulty] 统一随机状态、文件指纹和原子写入。"""
import hashlib
import json
import random
from pathlib import Path
import numpy as np
import torch


def _json_value(value):
    # 数据表中的 numpy 数组转换为 JSON 值；其他不支持类型必须显式处理。
    if hasattr(value, 'tolist'):
        return value.tolist()
    raise TypeError(f'Unsupported fingerprint value: {type(value).__name__}')


def fingerprint(value):
    # 固定序列化方式，避免 Python hash 的进程随机性。
    """生成稳定内容标识，用于题池、标签及配置的跨进程一致性检查。
    不使用 Python hash；无法规范序列化的值会报错，不采用含地址的对象字符串。
    """
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, default=_json_value).encode()).hexdigest()


def file_hash(path):
    """分块计算实际文件内容哈希，内存占用不随模型文件大小增加。
    调用方负责只在初始化或 checkpoint 发布时执行，避免每步扫描权重。
    """
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def atomic_json(path, value):
    """先写同目录临时文件，再替换目标，读者只能看到完整的前一版或后一版。
    这保证单写者的可见性；不提供跨进程锁，运行目录必须由单个任务独占。
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2))
    temporary.replace(path)


def atomic_torch_save(path, value):
    """用同目录替换方式提交包含张量的训练状态。
    单个文件写完不代表整个 checkpoint 完成，仍须等待 COMPLETE 清单。
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    torch.save(value, temporary)
    temporary.replace(path)


def seed_all(seed):
    """初始化 Python、NumPy、Torch 及可用 CUDA 随机流。
    只在实验入口或 worker 初始化调用，不能在每个训练步骤重复重置。
    """
    random.seed(seed)
    np.random.seed(seed % 2**32)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def capture_rng():
    """保存 driver 或当前 worker 的随机状态供完整续训和评分隔离使用。
    采样器自己的 numpy Generator 与 vLLM 独立流由各自模块另外保存。
    """
    state = {'python': random.getstate(), 'numpy': np.random.get_state(), 'torch': torch.get_rng_state()}
    if torch.cuda.is_available():
        state['cuda'] = torch.cuda.get_rng_state_all()
    return state


def restore_rng(state):
    """恢复对应进程的随机状态，不改变种子派生规则或模型参数。
    含 CUDA 状态的 checkpoint 要求相同设备拓扑；CPU 单测只验证 CPU 路径。
    """
    random.setstate(state['python'])
    np.random.set_state(state['numpy'])
    torch.set_rng_state(state['torch'])
    if 'cuda' in state and torch.cuda.is_available():
        torch.cuda.set_rng_state_all(state['cuda'])


def trajectory_seed(seed, *parts):
    # 每条轨迹有独立种子；同题四次 rollout 不共享同一随机流，回答文本仍可能相同。
    """由主种子、题目或训练位置、轨迹序号和生成轮次派生请求种子。
    独立种子保证采样机会独立，不保证四个回答文本必然不同。
    """
    return int(fingerprint([int(seed), *parts])[:8], 16) % (2**31 - 1)


def model_identity(path):
    # 对本地模型文件计算内容指纹；只在实验初始化时执行，避免每一步重复扫描。
    """对本地模型、配置及 tokenizer 内容生成标识，不依赖目录名称。
    远程仓库需预先固定版本并下载；跨设备路径可以变化，内容必须一致。
    """
    path = Path(path)
    if not path.is_dir():
        raise ValueError('Difficulty experiments require a pinned local model directory')
    names = sorted(p for p in path.iterdir() if p.is_file() and
                   (p.suffix in ('.json', '.safetensors', '.bin') or p.name in ('merges.txt', 'vocab.txt')))
    if not names:
        raise ValueError(f'No model files found: {path}')
    return fingerprint([(p.name, file_hash(p)) for p in names])
