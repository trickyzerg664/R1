"""Offline environment checks; does not download models or start services."""
import importlib
from importlib.metadata import version
import sys
from pathlib import Path

import torch

kind = sys.argv[1]
root = Path(__file__).resolve().parents[1]
assert Path(sys.prefix).resolve() == root / '.envs' / kind, sys.prefix
print('Python:', sys.version.split()[0], 'prefix:', sys.prefix)
print('torch:', torch.__version__, 'CUDA:', torch.version.cuda)
assert torch.cuda.is_available(), 'CUDA is unavailable'
for device in range(torch.cuda.device_count()):
    x = torch.ones((32, 32), device=f'cuda:{device}', dtype=torch.float16)
    assert (x @ x).sum().item() == 32768
    print('GPU:', device, torch.cuda.get_device_name(device),
          'capability:', torch.cuda.get_device_capability(device))

modules = ['transformers', 'datasets']
if kind == 'searchr1':
    modules += ['vllm', 'flash_attn', 'tensordict', 'ray', 'wandb', 'verl',
                'verl.trainer.main_ppo', 'verl.workers.fsdp_workers',
                'verl.third_party.vllm']
else:
    modules += ['faiss', 'fastapi', 'uvicorn', 'pyserini.search.lucene']
for name in modules:
    module = importlib.import_module(name)
    print('IMPORT OK:', name, version('vllm') if name == 'vllm' else getattr(module, '__version__', ''))
if kind == 'retriever':
    import faiss
    import numpy as np
    assert faiss.get_num_gpus() == torch.cuda.device_count()
    resources = faiss.StandardGpuResources()
    resources.setTempMemory(64 * 1024 * 1024)  # Small smoke check on a shared GPU.
    index = faiss.index_cpu_to_gpu(resources, 0, faiss.IndexFlatL2(4))
    vectors = np.eye(4, dtype=np.float32)
    index.add(vectors)
    distances, ids = index.search(vectors, 1)
    assert np.array_equal(ids[:, 0], np.arange(4))
    assert np.allclose(distances, 0)
    print('FAISS GPU add/search: OK')
else:
    # FP16 is supported here, but the training attention backend still requires FA2.
    supported = all(torch.cuda.get_device_capability(i)[0] >= 8
                    for i in range(torch.cuda.device_count()))
    print('FlashAttention-2 training hardware supported:', supported)
print('Environment checks passed:', kind)
