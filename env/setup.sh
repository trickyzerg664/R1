#!/usr/bin/env bash
# Recreate the two environments in this checkout; no conda init/global pip.
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"
export UV_CACHE_DIR="$project_dir/.cache/uv"
export UV_PYTHON_INSTALL_DIR="$project_dir/.tools/python"
export MAMBA_ROOT_PREFIX="$project_dir/.cache/mamba"
export PYTHONNOUSERSITE=1
unset PYTHONHOME PYTHONPATH
mkdir -p .tools .envs .cache
command -v uv >/dev/null || { echo 'uv is required on PATH' >&2; exit 1; }
if [ ! -x .tools/bin/micromamba ]; then
    curl -fL --retry 3 https://micro.mamba.pm/api/micromamba/linux-64/2.9.0 -o .tools/micromamba.tar.bz2
    tar -xjf .tools/micromamba.tar.bz2 -C .tools bin/micromamba
fi
if [ ! -x .envs/searchr1/bin/python ]; then
    uv venv --python 3.9 --seed .envs/searchr1
fi
if [ -f env/searchr1.lock.txt ]; then
    uv pip install --python .envs/searchr1/bin/python -r env/searchr1.lock.txt
else
    uv pip install --python .envs/searchr1/bin/python -r env/searchr1.in
fi
flash_wheel='flash_attn-2.7.4.post1+cu12torch2.4cxx11abiFALSE-cp39-cp39-linux_x86_64.whl'
if [ ! -f ".tools/$flash_wheel" ]; then
    curl -fL --retry 3 'https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.4.post1/flash_attn-2.7.4.post1%2Bcu12torch2.4cxx11abiFALSE-cp39-cp39-linux_x86_64.whl' -o ".tools/$flash_wheel"
fi
if [ -f env/flash-attn.sha256 ]; then sha256sum -c env/flash-attn.sha256; fi
uv pip install --python .envs/searchr1/bin/python --no-deps ".tools/$flash_wheel"
if [ ! -x .envs/retriever/bin/python ]; then
    if [ -f env/retriever.conda-explicit.txt ]; then
        .tools/bin/micromamba create -y -p "$PWD/.envs/retriever" -f env/retriever.conda-explicit.txt
    else
        .tools/bin/micromamba create -y -p "$PWD/.envs/retriever" --override-channels \
            -c pytorch -c nvidia -c conda-forge python=3.10 pip pytorch=2.4.0 \
            torchvision=0.19.0 torchaudio=2.4.0 pytorch-cuda=12.1 faiss-gpu=1.8.0 \
            'numpy<2' 'mkl<2025' openjdk=21
    fi
fi
if [ -f env/retriever.pip.lock.txt ]; then
    uv pip install --python .envs/retriever/bin/python -r env/retriever.pip.lock.txt
else
    uv pip install --python .envs/retriever/bin/python -r env/retriever.in
fi
printf '\nEnvironments installed. Validate using:\n  env/run.sh searchr1 python env/check.py searchr1\n  env/run.sh retriever python env/check.py retriever\n'
