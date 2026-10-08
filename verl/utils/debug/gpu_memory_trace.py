"""仅记录阶段显存与完整轨迹形状，不修改张量或随机流。"""
import json
import os
import time
import torch

def trace_gpu_memory(stage, enabled=False, batch=None, optimizer=None):
    """@brief 启用时记录本进程的显存和优化器状态设备。
    @param stage 阶段名称字符串。
    @param enabled 布尔开关，默认关闭且不访问GPU。
    @param batch 可选张量映射，仅读取完整上下文和回答形状。
    @param optimizer 可选优化器，只读已存在的状态。
    @return 无。
    @note Torch统计不含独立检索进程，须与驱动总显存时间线一起分析。
    """
    # 旧任务关闭诊断时不访问GPU；诊断不清缓存、不重置峰值。
    if not enabled:
        return
    state_bytes = {'cpu': 0, 'cuda': 0}
    if optimizer is not None:
        # 仅遍历已有状态，避免通过defaultdict访问创建空Adam状态。
        for state in optimizer.state.values():
            for value in state.values():
                if isinstance(value, torch.Tensor):
                    device = value.device.type
                    state_bytes[device] = state_bytes.get(device, 0) + value.numel() * value.element_size()
    shapes = {}
    if batch is not None:
        for key in ('input_ids', 'responses'):
            if key in batch:
                shapes[key] = list(batch[key].shape)
    print('[GPU_MEMORY] ' + json.dumps(dict(
        time_unix=time.time(), pid=os.getpid(), stage=stage,
        device=torch.cuda.current_device(), shapes=shapes,
        allocated_MiB=torch.cuda.memory_allocated() / 2**20,
        reserved_MiB=torch.cuda.memory_reserved() / 2**20,
        peak_allocated_MiB=torch.cuda.max_memory_allocated() / 2**20,
        optimizer_state_bytes=state_bytes,
    )), flush=True)

