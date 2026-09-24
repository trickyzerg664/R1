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

# [data-difficulty] 使用项目管理的 retriever 环境；在其环境初始化后覆盖大型缓存位置。
exec bash "$project_dir/env/run.sh" retriever env \
    HF_HOME="$cache_root/hf" HF_DATASETS_CACHE="$cache_root/datasets" \
    XDG_CACHE_HOME="$cache_root" TMPDIR="$cache_root/tmp" python search_r1/search/retrieval_server.py \
    --index_path "$index_file" --corpus_path "$corpus_file" \
    --retriever_model "$retriever_model" --retriever_name e5 --topk 3 \
    "${faiss_args[@]}" "$@"
