"""vLLM worker 扩展：从本机 safetensors 文件接收训练后的模型权重。"""

from safetensors import safe_open
import torch


class MetaxWeightUpdateExtension:
    def load_weights_from_safetensors(self, path: str) -> dict:
        """在推理 worker 内载入参数；RPC 只传路径，不序列化 GPU 张量或函数。"""
        model = self.model_runner.model
        with safe_open(path, framework='pt', device='cpu') as handle:
            names = list(handle.keys())
            loaded = model.load_weights((name, handle.get_tensor(name)) for name in names)
        return {'loaded': len(loaded), 'total': len(names)}

    def offload_weights_to_cpu(self):
        """@brief 将推理参数和缓冲区无损移至CPU，释放GPU权重空间。
        @return True，搬移及同步完成后返回。
        @note 仅用于无未完成请求的串行阶段；不修改KV缓存或参数精度。
        """
        # 不采用当前MetaX退出时不稳定的sleep allocator；复用Module设备搬移。
        self.model_runner.model.to('cpu')
        torch.cuda.synchronize(self.device)
        torch.cuda.empty_cache()
        return True

    def restore_weights_from_cpu(self):
        """@brief 在下一次生成或同步前恢复同精度推理权重到worker GPU。
        @return True，搬移及同步完成后返回。
        @note 不改变权重版本和KV前缀语义，调用者必须先确认RPC成功。
        """
        # 只改变设备，不执行初始化、量化或dtype转换。
        self.model_runner.model.to(self.device)
        torch.cuda.synchronize(self.device)
        return True
