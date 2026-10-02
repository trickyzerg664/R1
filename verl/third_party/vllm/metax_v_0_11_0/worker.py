"""vLLM worker 扩展：从本机 safetensors 文件接收训练后的模型权重。"""

from safetensors import safe_open


class MetaxWeightUpdateExtension:
    def load_weights_from_safetensors(self, path: str) -> dict:
        """在推理 worker 内载入参数；RPC 只传路径，不序列化 GPU 张量或函数。"""
        model = self.model_runner.model
        with safe_open(path, framework='pt', device='cpu') as handle:
            names = list(handle.keys())
            loaded = model.load_weights((name, handle.get_tensor(name)) for name in names)
        return {'loaded': len(loaded), 'total': len(names)}
