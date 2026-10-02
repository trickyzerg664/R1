#!/usr/bin/env bash
# 在独立 MACA 3.3 SDK 和纯净 venv 中运行本仓库的 Python 入口。
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
workspace="$(dirname "$repo")"
sdk="${METAX_SDK_ROOT:-$workspace/envs/maca-3.3.0.15/sdk-root/opt/maca-3.3.0}"
venv="${METAX_VENV_ROOT:-$workspace/envs/vllm-metax-clean33}"
lib_overrides="${METAX_LIB_OVERRIDES:-$workspace/envs/maca-3.3.0.15/lib-overrides}"
cache="${METAX_CACHE_ROOT:-$workspace/cache/maca-clean33}"
ray_tmpdir="${RAY_TMPDIR:-/tmp/r1ray33}"

if [[ ! -x "$venv/bin/python" || ! -d "$sdk/lib" || ! -d "$lib_overrides" ]]; then
  echo "MetaX SDK、venv 或覆盖库不存在；请设置 METAX_SDK_ROOT/METAX_VENV_ROOT/METAX_LIB_OVERRIDES" >&2
  exit 2
fi
mkdir -p "$ray_tmpdir"

# 隔离系统 MACA 3.7 和其他 venv，仅传递训练任务明确需要的环境变量。
forward=()
for name in CUDA_VISIBLE_DEVICES SEARCH_R1_N_GPUS SEARCH_R1_RAY_CPUS SEARCH_R1_RAY_ACTOR_START_TIMEOUT SEARCH_R1_ASSET_ROOT SEARCH_R1_CACHE_ROOT SEARCH_R1_FAISS_GPU HF_HUB_OFFLINE TRANSFORMERS_OFFLINE VERL_METAX_WEIGHT_SYNC_DIR VERL_METAX_ENABLE_SLEEP_MODE; do
  if [[ -v $name ]]; then
    forward+=("$name=${!name}")
  fi
done

base=(
  "HOME=${HOME:-/root}"
  "PATH=$venv/bin:$sdk/bin:$sdk/mxgpu_llvm/bin:$sdk/tools/cu-bridge/bin:/usr/bin:/bin"
  "LD_LIBRARY_PATH=$lib_overrides:$sdk/lib:$sdk/mxgpu_llvm/lib:$sdk/ompi/lib:/opt/mxdriver/lib"
  "MACA_PATH=$sdk"
  "CUCC_PATH=$sdk/tools/cu-bridge"
  "PYTHONPATH=$repo"
  "PYTHONNOUSERSITE=1"
  "VLLM_ENABLE_V1_MULTIPROCESSING=0"
  "VLLM_WORKER_MULTIPROC_METHOD=spawn"
  "HF_HOME=$cache/huggingface"
  "XDG_CACHE_HOME=$cache/xdg"
  "RAY_TMPDIR=$ray_tmpdir"
)
exec env -i "${base[@]}" "${forward[@]}" "$venv/bin/python" "$@"
