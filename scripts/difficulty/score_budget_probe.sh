#!/usr/bin/env bash
# [data-difficulty] 限时小池评分；只用正式来源抽取临时 P/D/T，不发布正式实验标签。
set -Eeuo pipefail

usage() {
  cat <<'USAGE'
用法：CUDA_VISIBLE_DEVICES=1,2 NCCL_P2P_DISABLE=1 bash scripts/difficulty/score_budget_probe.sh --run
可选：--minutes N（默认 40，最多 45） --data-root DIR --model DIR
      --output-dir DIR --retriever-url URL
无 --run 时仅预览；不会启动 GPU。需事先启动检索服务。
USAGE
}

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)"
data_root="${SEARCH_R1_ASSET_ROOT:-$repo_root/../../../data/search-r1}"
model=''
requested_output=''
retriever_url='http://127.0.0.1:8008/retrieve'
minutes=40
run=0
while (($#)); do
  case "$1" in
    --minutes|--data-root|--model|--output-dir|--retriever-url)
      (($# >= 2)) || { echo "缺少 $1 的值" >&2; exit 2; }
      case "$1" in
        --minutes) minutes="$2" ;;
        --data-root) data_root="$2" ;;
        --model) model="$2" ;;
        --output-dir) requested_output="$2" ;;
        --retriever-url) retriever_url="$2" ;;
      esac
      shift 2 ;;
    --run) run=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "未知参数：$1" >&2; usage >&2; exit 2 ;;
  esac
done
[[ "$minutes" =~ ^[0-9]+$ ]] && ((minutes >= 1 && minutes <= 45)) || {
  echo '--minutes 必须为 1–45 的整数' >&2; exit 2;
}
data_root="$(realpath -m -- "$data_root")"
model="$(realpath -m -- "${model:-$data_root/models/Qwen2.5-3B}")"
printf '代码：%s\n数据：%s\n模型：%s\n检索：%s\n评分时间上限：%s 分钟\n' \
  "$repo_root" "$data_root" "$model" "$retriever_url" "$minutes"
if ((!run)); then
  echo '仅预览；添加 --run 才会准备数据并启动 GPU。'
  exit 0
fi

# 设备和资产预检先于任何新产物；GPU 数从明确的可见设备推导。
[[ -n "${CUDA_VISIBLE_DEVICES:-}" && "$CUDA_VISIBLE_DEVICES" =~ ^[0-9]+(,[0-9]+)*$ ]] || {
  echo '请设置 CUDA_VISIBLE_DEVICES=1,2（或实际空闲 GPU 编号）' >&2; exit 2;
}
IFS=, read -ra gpu_ids <<< "$CUDA_VISIBLE_DEVICES"
export SEARCH_R1_N_GPUS="${#gpu_ids[@]}"
[[ -x "$repo_root/env/run.sh" && -f "$model/config.json" ]] || {
  echo '缺少项目环境或模型配置' >&2; exit 1;
}
for file in "$data_root/datasets/nq_hotpotqa_train/train.parquet" \
            "$data_root/datasets/nq_hotpotqa_train/test.parquet"; do
  [[ -s "$file" ]] || { echo "缺少数据：$file" >&2; exit 1; }
done
command -v timeout >/dev/null || { echo '缺少 GNU timeout' >&2; exit 1; }
export RAY_TMPDIR="${RAY_TMPDIR:-$HOME/r1ray}"
run_dir="$(realpath -m -- "${requested_output:-$data_root/runs/score-budget-$(date -u +%Y%m%d-%H%M%S)-$$}")"
# 显式输出路径也必须是空目录，避免重试覆盖旧标签和日志。
[[ ! -e "$run_dir" || -z "$(find "$run_dir" -mindepth 1 -maxdepth 1 -print -quit)" ]] || {
  echo "输出目录已有文件：$run_dir" >&2; exit 1;
}
mkdir -p "$run_dir" "$data_root/cache/train/hf" "$data_root/cache/train/tmp" "$RAY_TMPDIR"
git -C "$repo_root" rev-parse HEAD > "$run_dir/git-head.txt"
git -C "$repo_root" status --porcelain > "$run_dir/git-status.txt"
printf '运行目录：%s\n' "$run_dir"

# 冻结工具自带 P/D/T 哈希与互斥校验；初始 prompt 选不超过 256 token 的题，避免起始 256 token 截断。
# 小池只用于诊断，不当作正式 10000/1000/2000 题池。
printf '准备 20 道评分题，最多等待 8 分钟……\n'
if ! timeout --signal=INT --kill-after=20s 8m \
  "$repo_root/env/run.sh" searchr1 env \
  HF_HOME="$data_root/cache/train/hf" TMPDIR="$data_root/cache/train/tmp" PYTHONUNBUFFERED=1 \
  python scripts/difficulty/freeze_pool.py \
  --data-root "$data_root" --output-dir "$run_dir/pool" --model "$model" \
  --p-size 20 --d-size 10 --t-size 10 --max-prompt-length 256 \
  > "$run_dir/freeze.log" 2>&1; then
  tail -n 35 "$run_dir/freeze.log"
  echo "准备题池未完成；日志：$run_dir/freeze.log" >&2
  exit 1
fi
tail -n 2 "$run_dir/freeze.log"

# 每题四轨迹，batch=1；score_pool 每完成一题就原子写入 .partial，可在时间上限后统计。
printf '开始评分，最多 %s 分钟；完整日志：%s/score.log\n' "$minutes" "$run_dir"
set +e
timeout --signal=INT --kill-after=30s "${minutes}m" \
  "$repo_root/env/run.sh" searchr1 env \
  HF_HOME="$data_root/cache/train/hf" TMPDIR="$data_root/cache/train/tmp" PYTHONUNBUFFERED=1 \
  python -m verl.trainer.main_ppo --config-name difficulty_grpo \
  "actor_rollout_ref.model.path=$model" "actor_rollout_ref.ref.model_path=$model" \
  "data.train_files=$run_dir/pool/P.parquet" "data.val_files=$run_dir/pool/D.parquet" \
  data.train_batch_size=2 data.val_batch_size=2 \
  data.max_prompt_length=4096 data.max_start_length=256 \
  data.max_response_length=128 data.max_obs_length=256 \
  actor_rollout_ref.actor.ppo_mini_batch_size=8 \
  actor_rollout_ref.actor.ppo_micro_batch_size=2 \
  actor_rollout_ref.ref.log_prob_micro_batch_size=2 \
  actor_rollout_ref.rollout.log_prob_micro_batch_size=2 \
  difficulty.mode=score difficulty.score_batch_size=1 difficulty.score_trace_chars=600 \
  "difficulty.output_dir=$run_dir/score" "difficulty.score_output=$run_dir/labels.json" \
  "retriever.url=$retriever_url" difficulty.retrieval_id=wiki18-e5-pinned \
  2>&1 | tee "$run_dir/score.log" | awk '
    /Started a local Ray instance/ { print "Ray 已启动"; fflush() }
    /ACTIVE_TRAJ_NUM:/ { batches++; print "完成轨迹批次：" batches; fflush() }
    /Traceback|Error executing job|out of memory/ { print "日志出现错误，详见 score.log"; fflush() }
  '
status=${PIPESTATUS[0]}
set -e
printf '%s\n' "$status" > "$run_dir/exit_code"
if ((status == 124 || status == 137)); then
  echo '达到评分时间上限；已完成题目保存在 labels.json.partial，可后续继续。'
elif ((status != 0)); then
  printf '评分异常退出（%s），最后日志：\n' "$status" >&2
  tail -n 35 "$run_dir/score.log" >&2
fi

# 允许正常完成或时间到达；只汇报已持久化题目，部分结果不当正式标签使用。
python3 - "$run_dir" <<'PY'
from collections import Counter
import json
from pathlib import Path
import sys

run = Path(sys.argv[1])
path = run / 'labels.json'
if not path.exists():
    path = run / 'labels.json.partial'
if not path.exists():
    print('尚无完成的评分题；查看日志：', run / 'score.log')
    raise SystemExit(0)
records = json.loads(path.read_text(encoding='utf-8'))['records']
k = Counter(int(row['k']) for row in records)
valid = sum(trace['has_answer_tag'] for row in records for trace in row.get('traces', []))
print(f'已完成 {len(records)}/20 题；k=0..4：{[k[i] for i in range(5)]}；有效答案格式 {valid}/{len(records) * 4} 条')
print('评分文件：', path)
PY
printf '退出码：%s；运行目录：%s\n' "$status" "$run_dir"
((status == 0 || status == 124 || status == 137)) || exit "$status"
