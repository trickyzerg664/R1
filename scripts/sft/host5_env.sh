#!/usr/bin/env bash
# Source inside host5/lzy. Historical host3 launchers remain unchanged.
export R1_HOST5_ROOT=/root/myprojects/R1/R1
export SFT_PYTHON="$R1_HOST5_ROOT/.cache/sft-smoke-env/bin/python"
export CUDA_VISIBLE_DEVICES=0
export CUDA_HOME="$R1_HOST5_ROOT/.cache/sft-cuda"
export PATH="$(dirname "$SFT_PYTHON"):$CUDA_HOME/bin:$PATH"
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export TOKENIZERS_PARALLELISM=false
export PYTHONPATH="$R1_HOST5_ROOT/.cache/sft-test-deps:$R1_HOST5_ROOT"
export TORCH_EXTENSIONS_DIR="$R1_HOST5_ROOT/.cache/torch_extensions_host5"
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export MAX_JOBS=2
export CPATH="$R1_HOST5_ROOT/.cache/sft-libaio-20261118/sysroot/usr/include${CPATH:+:$CPATH}"
export LIBRARY_PATH="$R1_HOST5_ROOT/.cache/host5-link-libs:$R1_HOST5_ROOT/.cache/sft-libaio-20261118/sysroot/usr/lib/x86_64-linux-gnu${LIBRARY_PATH:+:$LIBRARY_PATH}"
export LD_LIBRARY_PATH="$R1_HOST5_ROOT/.cache/host5-link-libs:$R1_HOST5_ROOT/.cache/sft-libaio-20261118/sysroot/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
