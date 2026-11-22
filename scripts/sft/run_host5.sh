#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$root"
source scripts/sft/host5_env.sh
config="${SFT_CONFIG:-configs/sft/deepseek_host5.yaml}"
stage="${1:-preflight}"
if [ "$#" -gt 0 ]; then shift; fi
case "$stage" in
  preflight|prepare|export)
    exec "$SFT_PYTHON" -m "search_sft.$stage" --config "$config" "$@" ;;
  pilot|full|smoke)
    exec "$SFT_PYTHON" -m torch.distributed.run --standalone --nproc_per_node=1 \
      -m search_sft.train --config "$config" --stage "$stage" "$@" ;;
  test) exec "$SFT_PYTHON" -m pytest tests/sft -q "$@" ;;
  *) printf 'Usage: %s {preflight|prepare|pilot|full|smoke|export|test} [args]\n' "$0" >&2; exit 2 ;;
esac
