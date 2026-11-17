#!/usr/bin/env bash
# 显式指定阶段；不隐式串行启动 pilot/full，也不读取旧 RL 环境。
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$root"
python_bin="${SFT_PYTHON:-$root/.envs/sft/bin/python}"
export PATH="$(dirname -- "$python_bin"):$PATH"
if [ -z "${CUDA_HOME:-}" ] && [ -x "$root/.cache/sft-cuda/bin/nvcc" ]; then
  export CUDA_HOME="$root/.cache/sft-cuda"
fi
export PYTHONNOUSERSITE=1
export PYTHONPATH="$root"
export TOKENIZERS_PARALLELISM=false
config="${SFT_CONFIG:-configs/sft/deepseek.yaml}"
stage="${1:-preflight}"
if [ "$#" -gt 0 ]; then shift; fi
case "$stage" in
  preflight|prepare|export)
    exec "$python_bin" -m "search_sft.$stage" --config "$config" "$@" ;;
  pilot|full|smoke)
    exec "$python_bin" -m torch.distributed.run --standalone --nproc_per_node=2 \
      -m search_sft.train --config "$config" --stage "$stage" "$@" ;;
  test)
    exec "$python_bin" -m pytest tests/sft -q "$@" ;;
  *) printf 'Usage: %s {preflight|prepare|pilot|full|smoke|export|test} [args]\n' "$0" >&2; exit 2 ;;
esac
