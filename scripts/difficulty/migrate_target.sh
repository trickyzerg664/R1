#!/usr/bin/env bash
# 目标机直接从 Git 仓库拉取实验代码，随后重建环境并下载固定版本资产。
set -Eeuo pipefail

usage() {
  cat <<'USAGE'
用法：
  bash migrate_target.sh [--repo /path/to/R1] [--data-root /path/to/search-r1] \
    [--repo-url https://github.com/trickyzerg664/R1.git] \
    [--branch data-difficulty] [--expected-commit 40位Git提交ID] \
    [--refresh-code] [--dry-run]

目标机直接从 Git 仓库克隆代码；不访问本机，也不需要连接本机 SSH。
无参数时，以脚本所在目录为根，使用 myprojects/R1/R1 和 data/search-r1。
随后创建训练/检索环境，下载并校验固定版本资产，运行环境与 CPU 检查。
不会自动启动检索服务、评分、训练或正式实验。
USAGE
}

# 以脚本实际所在目录为根，保持当前设备相对 /root 的代码与资产目录结构。
# 允许分别覆盖代码和数据目录；GPU 型号及卡数留给目标设备的实验配置。
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_url='https://github.com/trickyzerg664/R1.git'
branch='data-difficulty'
expected_commit=''
repo="$script_dir/myprojects/R1/R1"
data_root="$script_dir/data/search-r1"
dry_run=0
refresh_code=0
while (($#)); do
  case "$1" in
    --repo-url|--branch|--expected-commit|--repo|--data-root)
      (($# >= 2)) || { echo "缺少 $1 的值" >&2; exit 2; }
      case "$1" in
        --repo-url) repo_url="$2" ;;
        --branch) branch="$2" ;;
        --expected-commit) expected_commit="$2" ;;
        --repo) repo="$2" ;;
        --data-root) data_root="$2" ;;
      esac
      shift 2 ;;
    --dry-run) dry_run=1; shift ;;
    --refresh-code) refresh_code=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "未知参数：$1" >&2; usage >&2; exit 2 ;;
  esac
done
for path in "$repo" "$data_root"; do
  [[ "$path" = /* && "$path" =~ ^[A-Za-z0-9_./-]+$ ]] || {
    echo "路径必须是无空格的绝对路径：$path" >&2; exit 2;
  }
done
[[ "$repo" != "$data_root" && "$repo" != "$data_root"/* && "$data_root" != "$repo"/* ]] || {
  echo '代码目录和数据目录不能互相包含' >&2; exit 2;
}
[[ "$branch" =~ ^[A-Za-z0-9._/-]+$ && "$branch" != -* ]] || {
  echo 'Git 分支名称不合法' >&2; exit 2;
}
[[ -z "$expected_commit" || "$expected_commit" =~ ^[0-9a-fA-F]{40}$ ]] || {
  echo '--expected-commit 必须是完整的 40 位 Git 提交 ID' >&2; exit 2;
}
[[ "$repo_url" = https://* || "$repo_url" = http://* ]] || {
  echo '仓库地址需使用 HTTP(S)；目标机不需要 Git SSH 密钥' >&2; exit 2;
}

# 干运行只展示目标路径和动作，不连接网络、创建目录或下载。
if ((dry_run)); then
  printf 'Git 仓库：%s\n分支：%s\n期望提交：%s\n目标代码：%s\n目标资产：%s\n' \
    "$repo_url" "$branch" "${expected_commit:-未指定，使用分支当前 HEAD}" "$repo" "$data_root"
  printf '步骤：Git 克隆/快进 → 安装 uv（若缺）→ env/setup.sh → 下载/校验资产 → 生成烟测输入 → 双环境检查 → 18 项 CPU 测试。\n'
  exit 0
fi

command -v git >/dev/null || { echo '缺少 git' >&2; exit 1; }
command -v python3 >/dev/null || { echo '缺少 python3' >&2; exit 1; }
command -v curl >/dev/null || { echo '缺少 curl' >&2; exit 1; }
command -v tar >/dev/null || { echo '缺少 tar' >&2; exit 1; }
command -v nvidia-smi >/dev/null || { echo '缺少 nvidia-smi；先安装并验证 NVIDIA 驱动' >&2; exit 1; }

# 每次尝试独立存放日志；失败时保留最后阶段和退出码，便于接续。
run_id="migration-$(date -u +%Y%m%d-%H%M%S)-$$"
run_dir="$data_root/runs/$run_id"
mkdir -p "$run_dir"
exec > >(tee -a "$run_dir/bootstrap.log") 2>&1
stage='预检'
record() { printf '%s\t%s\n' "$(date -u +%FT%TZ)" "$1" | tee -a "$run_dir/events.tsv"; }
on_exit() {
  local code=$?
  trap - EXIT
  if ((code == 0)); then record 'COMPLETE'; else record "FAILED stage=$stage exit=$code"; fi
  printf '运行记录：%s\n' "$run_dir"
  exit "$code"
}
trap on_exit EXIT
record "START repo_url=$repo_url branch=$branch repo=$repo data_root=$data_root"
printf 'GPU：\n'
nvidia-smi -L
df -h "$data_root"

# 首次只克隆到空目录；重复运行默认保留现有源码，显式刷新也只接受干净工作树快进。
stage='拉取 Git 代码'
record "$stage"
if [[ -d "$repo/.git" ]]; then
  [[ "$(git -C "$repo" config --get remote.origin.url)" = "$repo_url" ]] || {
    echo '目标代码目录的 origin 与指定仓库不同' >&2; exit 1;
  }
  [[ "$(git -C "$repo" branch --show-current)" = "$branch" ]] || {
    echo '目标代码目录的当前分支与指定分支不同' >&2; exit 1;
  }
  if ((refresh_code)); then
    [[ -z "$(git -C "$repo" status --porcelain)" ]] || {
      echo '目标工作树有未提交修改；拒绝自动更新' >&2; exit 1;
    }
    git -C "$repo" pull --ff-only origin "$branch"
  else
    echo '代码目录已有 Git 仓库；本次保留现有提交。需要快进时传入 --refresh-code。'
  fi
else
  [[ ! -e "$repo" || -z "$(find "$repo" -mindepth 1 -maxdepth 1 -print -quit)" ]] || {
    echo '目标代码目录非空且不是目标 Git 仓库；请使用空目录' >&2; exit 1;
  }
  git clone --branch "$branch" --single-branch "$repo_url" "$repo"
fi
actual_commit="$(git -C "$repo" rev-parse HEAD)"
if [[ -n "$expected_commit" && "$actual_commit" != "$expected_commit" ]]; then
  echo "Git 提交不符：期望 $expected_commit，实际 $actual_commit" >&2
  exit 1
fi
[[ -f "$repo/env/setup.sh" && -f "$repo/scripts/assets/download_search_r1.py" ]] || {
  echo '克隆代码缺少环境或资产脚本' >&2; exit 1;
}
printf '%s\n' "$actual_commit" > "$run_dir/git-head.txt"
git -C "$repo" status --short > "$run_dir/git-status.txt"
echo "使用提交：$actual_commit"

# env/setup.sh 依赖 uv；缺失时在目标代码目录创建独立的小型引导环境。
stage='准备 uv'
record "$stage"
if ! command -v uv >/dev/null; then
  if [[ ! -x "$repo/.tools/bootstrap-uv/bin/uv" ]]; then
    python3 -m venv "$repo/.tools/bootstrap-uv"
    "$repo/.tools/bootstrap-uv/bin/python" -m pip install 'uv==0.12.15'
  fi
  export PATH="$repo/.tools/bootstrap-uv/bin:$PATH"
fi
uv --version

# 安装仓库锁定的训练环境和检索环境，失败即停止并保留日志。
stage='重建 Python 环境'
record "$stage"
(
  cd "$repo"
  bash env/setup.sh
)

# 完整状态且最终文件大小匹配时跳过下载；其他情况交给固定 revision 下载器续传。
assets_complete() {
  python3 - "$data_root" <<'PY'
import json
import sys
from pathlib import Path
root = Path(sys.argv[1])
try:
    status = json.loads((root/'runs/asset-download/status.json').read_text())
    assert status['phase'] == 'complete'
    for key, info in [('retrieval/wiki18/e5_Flat.index', status['index']),
                      ('retrieval/wiki18/wiki-18.jsonl', status['corpus'])]:
        assert (root/key).stat().st_size == info['bytes']
    for key in ('models/Qwen2.5-3B/config.json', 'models/e5-base-v2/config.json',
                'datasets/nq_hotpotqa_train/train.parquet',
                'datasets/nq_hotpotqa_train/test.parquet'):
        assert (root/key).is_file()
except (OSError, KeyError, AssertionError, ValueError):
    sys.exit(1)
PY
}
stage='下载和校验资产'
record "$stage"
if assets_complete; then
  echo '检测到已完成且文件大小匹配的资产，跳过重复下载。'
else
  (
    cd "$repo"
    bash env/run.sh searchr1 python -u scripts/assets/download_search_r1.py --root "$data_root"
  )
  assets_complete || { echo '资产状态不是 complete 或最终文件不完整' >&2; exit 1; }
fi

# 本机烟测切片未进入 Git；目标机从已下载原始数据重新生成相同规模的小题集。
stage='准备烟测输入'
record "$stage"
(
  cd "$repo"
  bash env/run.sh searchr1 python scripts/difficulty/prepare_smoke.py \
    --data-root "$data_root" --output-dir "$data_root/runs/smoke-input"
)

# 环境检查使用真实 GPU；CPU 回归屏蔽 GPU 和网络，不能替代完整烟测。
stage='环境与 CPU 检查'
record "$stage"
(
  cd "$repo"
  bash env/run.sh searchr1 python env/check.py searchr1
  bash env/run.sh retriever python env/check.py retriever
  CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
    HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
    bash env/run.sh searchr1 python -m unittest discover -s tests -p '*difficulty*.py' -q
  git diff --check
)

# 告知后续验收入口，不自动占用 GPU 启动评分或训练。
record '准备完成；GPU 评分/训练/恢复尚未验证'
printf '\n下一步：按 %s/docs/experiments/data_difficulty_migration.md 启动真实检索服务和新烟测。\n' "$repo"
printf '设置 SEARCH_R1_ASSET_ROOT=%s，Ray 使用数据卷上的短 RAY_TMPDIR。\n' "$data_root"
