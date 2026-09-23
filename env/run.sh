#!/usr/bin/env bash
# Execute in a child process so the calling shell's environment is untouched.
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
kind="${1:-}"
case "$kind" in searchr1|retriever) shift ;; *) echo "Usage: $0 {searchr1|retriever} COMMAND [ARGS...]" >&2; exit 2 ;; esac
if [ "$#" -eq 0 ]; then set -- bash --noprofile --norc; fi
prefix="$project_dir/.envs/$kind"
[ -x "$prefix/bin/python" ] || { echo "Environment missing: $prefix" >&2; exit 1; }
unset PYTHONPATH PYTHONHOME
export PYTHONNOUSERSITE=1
export PIP_REQUIRE_VIRTUALENV=true
export UV_CACHE_DIR="$project_dir/.cache/uv"
export PIP_CACHE_DIR="$project_dir/.cache/pip"
export HF_HOME="$project_dir/.cache/huggingface"
export XDG_CACHE_HOME="$project_dir/.cache"
export TORCH_HOME="$project_dir/.cache/torch"
export TRITON_CACHE_DIR="$project_dir/.cache/triton/$kind"
export TORCH_EXTENSIONS_DIR="$project_dir/.cache/torch_extensions/$kind"
export NUMBA_CACHE_DIR="$project_dir/.cache/numba/$kind"
export WANDB_DIR="$project_dir/.cache/wandb"
export WANDB_CACHE_DIR="$project_dir/.cache/wandb/cache"
export RAY_TMPDIR="$project_dir/.cache/ray"
export MAMBA_ROOT_PREFIX="$project_dir/.cache/mamba"
mkdir -p "$WANDB_DIR" "$RAY_TMPDIR"
cd "$project_dir"
if [ "$kind" = searchr1 ]; then
    export VIRTUAL_ENV="$prefix"
    export PATH="$prefix/bin:$PATH"
    export VLLM_ATTENTION_BACKEND=XFORMERS
    exec "$@"
else
    unset VIRTUAL_ENV
    # PIP_REQUIRE_VIRTUALENV does not recognize conda prefixes; pip is explicit.
    unset PIP_REQUIRE_VIRTUALENV
    export JAVA_HOME="$prefix/lib/jvm"
    exec "$project_dir/.tools/bin/micromamba" run -p "$prefix" "$@"
fi
