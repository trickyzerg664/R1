"""沐曦 vLLM 的进程内张量并行接口暂未接入旧 veRL。"""


def _unsupported(*args, **kwargs):
    raise NotImplementedError('MetaX vLLM adapter currently requires tensor_model_parallel_size=1')


initialize_parallel_state = _unsupported
get_tensor_model_parallel_world_size = _unsupported
get_tensor_model_parallel_group = _unsupported
get_tensor_model_parallel_src_rank = _unsupported
