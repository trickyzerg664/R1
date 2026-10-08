"""反传浮点激活CPU卸载；整数索引保留布局以兼容现有融合算子。"""
from contextlib import contextmanager
import torch

@contextmanager
def cpu_activation_offload(enabled=False):
    """@brief 开启时将GPU保存的浮点激活搬到固定页CPU内存，反传时恢复原dtype/device。
    @param enabled 布尔开关，默认关闭且不访问GPU或安装保存钩子。
    @return 无；返回上下文供原前向和反传使用。
    @raises RuntimeError CPU分配或设备搬移失败时抛出，不降精度重试。
    @note 整数和布尔索引保留原布局，避免改变现有Triton融合算子读取索引的行为。
    """
    # 默认路径无钩子，保持旧任务的保存张量与计算顺序。
    if not enabled:
        yield
        return
    def pack(tensor):
        """@brief 仅卸载GPU浮点张量，保存原设备与精度。
        @param tensor autograd要保存的张量，不修改原张量。
        @return 原设备与已脱离图的保存张量二元组。
        @note 整数索引保持原storage/stride；detach避免保存对象对计算图形成循环引用。
        """
        # 融合概率算子的整数labels可能是非连续view，搬移会改变stride。
        # 索引体积很小，保留原storage/stride同时避免改变现有前后向语义。
        if tensor.device.type != 'cuda' or not tensor.is_floating_point():
            return None, tensor.detach()
        host = torch.empty_like(tensor, device='cpu', pin_memory=True)
        # 阻塞D2H确保副本完整；原GPU张量后续释放或重用不会覆盖保存的激活。
        host.copy_(tensor.detach(), non_blocking=False)
        return tensor.device, host
    def unpack(saved):
        """@brief 反传使用保存张量时恢复到原GPU，不改dtype。
        @param saved pack返回的原设备及保存张量二元组。
        @return 原精度/设备上的张量。
        @note 固定页H2D在当前流排队，后续算子在同一流读取，避免全设备同步。
        """
        device, tensor = saved
        return tensor if device is None else tensor.to(device, non_blocking=True)
    # 仅保存张量生命周期变化，不改损失公式、微批、checkpoint重算或随机流。
    with torch.autograd.graph.saved_tensors_hooks(pack, unpack):
        yield

