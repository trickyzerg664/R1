"""沐曦 vLLM 0.11 与 FSDP 的单卡权重同步。"""

import torch
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
from torch.distributed.fsdp.api import FullStateDictConfig, StateDictType

from verl.workers.sharding_manager.base import BaseShardingManager


class MetaxFSDPVLLMShardingManager(BaseShardingManager):
    """每个 FSDP rank 各自运行 TP=1 的 vLLM，输入输出无需跨 rank 广播。"""

    def __init__(self, module: FSDP, inference_engine):
        self.module = module
        self.inference_engine = inference_engine
        # 多轮生成会重复进入 manager；仅 actor 参数更新后才需要重新导出 7B 权重。
        self._weights_synced = False
        # vLLM 从共享内存读取完整 HF 权重；FSDP 直接导出到 CPU，避免 7B 全量权重在 GPU 上额外克隆导致峰值溢出。
        # TP=1 时每个 rank 都要同步各自的推理引擎，因此不能使用 rank0_only。
        FSDP.set_state_dict_type(
            module,
            state_dict_type=StateDictType.FULL_STATE_DICT,
            state_dict_config=FullStateDictConfig(offload_to_cpu=True, rank0_only=False),
        )

    def invalidate_weights(self):
        """actor 更新或恢复参数后使下次生成重新同步完整权重。"""
        self._weights_synced = False

    def __enter__(self):
        if not self._weights_synced:
            params = self.module.state_dict()
            try:
                self.inference_engine.sync_model_weights(params, load_format='hf')
                # 同步成功后才复用；失败重试时必须重新导出。
                self._weights_synced = True
            finally:
                del params
                torch.cuda.empty_cache()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # 无休眠模式让 vLLM 权重常驻；休眠模式释放权重后，下次必须重新同步。
        self.inference_engine.offload_model_weights()
        if self.inference_engine._sleep_enabled:
            self.invalidate_weights()
        self.module.train()
        torch.cuda.empty_cache()
        return False
