#!/usr/bin/env bash
# [data-difficulty] 检索服务入口只负责路径与设备选项；索引读取和编码仍由原服务实现。
set -euo pipefail

# [data-difficulty] 资产根目录可在迁移设备上覆盖；默认值对应本机已校验资产。
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
asset_root="${SEARCH_R1_ASSET_ROOT:-/root/data/search-r1}"
index_file="${SEARCH_R1_INDEX_PATH:-$asset_root/retrieval/wiki18/e5_Flat.index}"
corpus_file="${SEARCH_R1_CORPUS_PATH:-$asset_root/retrieval/wiki18/wiki-18.jsonl}"
retriever_model="${SEARCH_R1_RETRIEVER_MODEL:-$asset_root/models/e5-base-v2}"

# [data-difficulty] 启动前检查最终索引、语料和编码器，不接受尚未合并的下载分片。
for input_file in "$index_file" "$corpus_file"; do
    if [[ ! -f "$input_file" ]]; then
        echo "Missing retrieval asset: $input_file" >&2
        exit 2
    fi
done
if [[ ! -d "$retriever_model" ]]; then
    echo "Missing retriever model: $retriever_model" >&2
    exit 2
fi

# [data-difficulty] 大索引的 GPU 克隆必须显式选择；CPU 索引仍需检索编码器使用 GPU。
faiss_args=()
case "${SEARCH_R1_FAISS_GPU:-0}" in
    0) ;;
    1) faiss_args=(--faiss_gpu) ;;
    *) echo 'SEARCH_R1_FAISS_GPU must be 0 or 1' >&2; exit 2 ;;
esac

# [data-difficulty] 大语料的 Arrow 缓存和临时文件写到数据卷，避免根分区耗尽。
cache_root="${SEARCH_R1_CACHE_ROOT:-$asset_root/cache/retriever}"
mkdir -p "$cache_root/hf" "$cache_root/datasets" "$cache_root/tmp"

# [data-difficulty] 参数统一组装；迁移机可使用已校验的独立检索环境。
server_args=(
    search_r1/search/retrieval_server.py
    --index_path "$index_file" --corpus_path "$corpus_file"
    --retriever_model "$retriever_model" --retriever_name e5 --topk 3
    "${faiss_args[@]}" "$@"
)
cache_env=(
    "HF_HOME=$cache_root/hf"
    "HF_DATASETS_CACHE=$cache_root/datasets"
    "XDG_CACHE_HOME=$cache_root"
    "TMPDIR=$cache_root/tmp"
)
if [[ -n "${SEARCH_R1_RETRIEVER_ENV:-}" ]]; then
    if [[ ! -x "$SEARCH_R1_RETRIEVER_ENV/bin/python" ]]; then
        echo "Missing retriever python: $SEARCH_R1_RETRIEVER_ENV/bin/python" >&2
        exit 2
    fi
    # 独立环境仅引入当前仓库代码及指定缓存，避免依赖不存在的旧 .envs 目录。
    cd "$project_dir"
    exec env "PYTHONPATH=$project_dir" "${cache_env[@]}" "$SEARCH_R1_RETRIEVER_ENV/bin/python" "${server_args[@]}"
fi

# 原有部署继续使用项目管理的 retriever 环境，保持默认行为。
exec bash "$project_dir/env/run.sh" retriever env "${cache_env[@]}" python "${server_args[@]}"
