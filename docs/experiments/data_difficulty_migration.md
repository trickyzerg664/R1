# data-difficulty：迁移到其他设备的执行清单

更新：2026-09-24。实验代码分支为 `data-difficulty`；目标机运行时通过 `git rev-parse HEAD` 记录实际提交。正式 P/D/T 尚未冻结，本机烟测评分为 0 题、训练为 0 step。目标机先接续短流程验收，不能把本机失败运行标为完成。运行历史见[本机烟测记录](runs/gpu-smoke-20260924-1022.md)。

以下示例假设 Linux/x86_64、目标设备可访问同版本 CUDA 依赖。把 `user@host`、`/work/R1`、`/data/search-r1` 换成真实地址；目标机的数据卷路径尽量短。不同机器的 GPU 型号、显存、卡数、驱动和可用磁盘须重新实测。

## 1. 在目标设备一键准备

目标设备只需通过 HTTPS 访问 GitHub 和上游资产源，**无需连接本机 SSH**。脚本参数、重试行为和日志位置见[使用 README](../../scripts/difficulty/README.md)。目标机需要 Linux/x86_64、NVIDIA 驱动、`git`、`curl`、`python3`（含 venv）、`tar`；下载可能较久，建议在 `tmux` 会话中运行。

```bash
# 全部命令在目标设备执行；先取得轻量引导脚本。
curl -fL https://raw.githubusercontent.com/trickyzerg664/R1/data-difficulty/scripts/difficulty/migrate_target.sh \
  -o /tmp/r1-migrate-target.sh
bash /tmp/r1-migrate-target.sh \
  --repo /work/R1 --data-root /data/search-r1 --dry-run
bash /tmp/r1-migrate-target.sh \
  --repo /work/R1 --data-root /data/search-r1
```

脚本从 GitHub 的 `data-difficulty` 分支克隆代码，下载固定 revision 的 Qwen2.5-3B、e5-base-v2、原始问答 parquet、FAISS 索引与语料，重建两个环境，生成目标机自己的小规模烟测切片，并执行环境及 CPU 检查。当前分支的核心实验代码在 Git；若上述 `curl` 返回 404，应先确认迁移脚本所在提交已推送。需要锁定代码时传入 `--expected-commit` 指定完整 40 位提交 ID。运行日志保存于目标数据目录的 `runs/migration-<UTC时间>-<pid>/`；`events.tsv` 最后为 `COMPLETE` 才说明准备通过。脚本不启动检索或 GPU 实验。

## 2. 资产与烟测输入

下载器以仓库内固定 revision 获取官方模型、数据、索引分片和压缩语料，验证后拼接索引、提取 JSONL。最终可直接运行的资产约为：Qwen2.5-3B 5.8 GiB、e5-base-v2 419 MiB、索引 61 GiB、JSONL 14 GiB、问答数据 407 MiB；下载原件及缓存还需额外空间。只有 `runs/asset-download/status.json` 的 `phase=complete` 才算资产完成。

脚本在下载后执行 [`prepare_smoke.py`](../../scripts/difficulty/prepare_smoke.py)，从原始 train split 生成 `runs/smoke-input/score.parquet`（2 题）、`train.parquet`（8 题）、`dev.parquet`（4 题）及记录来源哈希的清单。它们只用于链路验收，不是已冻结的正式 P/D/T。本机没有需经设备迁移的正式实验 checkpoint；将来跨设备续训须传完整 `checkpoints/step_N/`（含 actor、rank 状态、`driver.pt`、`metadata.json`、`COMPLETE.json`），并保持同样 GPU 拓扑及环境版本。

## 3. 重建并检查目标机环境

`.envs` 和 `.tools` 属于本机环境，不复制；在目标机从锁文件重建。`env/setup.sh` 需要 `uv`、`curl` 和网络；目标机若无法访问依赖源，先准备相同版本的 wheel/conda 包。该脚本为项目当前 CUDA 12.x、PyTorch 2.4、vLLM 0.6.3 和 FlashAttention 2.7.4 依赖组合；按目标 GPU 驱动、架构检查兼容性，不直接复制本机 Python 环境。

```bash
cd /work/R1
bash env/setup.sh
bash env/run.sh searchr1 python env/check.py searchr1
bash env/run.sh retriever python env/check.py retriever
nvidia-smi
CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  bash env/run.sh searchr1 python -m unittest discover -s tests -p '*difficulty*.py' -q
```

环境检查与 CPU 测试通过后，仍需真实模型/FSDP/vLLM 验收。当前实验协议固定 `max_turns=10`、每题四条轨迹；GPU 数通过 `SEARCH_R1_N_GPUS` 指定。若要与本机两卡设置及后续同父 checkpoint 直接比较，目标机先用两张卡。跨 GPU 数、FSDP/TP 拓扑或 Torch/Transformers/vLLM 版本，不按“继续训练”处理，应从共同初始模型重新建组或先实现并验证状态重分片。

## 4. 启动完整检索服务并验收

完整索引默认在 CPU，曾在本机占用约 62 GiB RSS；查询编码器仍占用 GPU。目标机需要为语料加载、Arrow 缓存及训练进程保留充足内存。若目标机显存充足且决定把索引放 GPU，才设置 `SEARCH_R1_FAISS_GPU=1`；此改变应记入运行记录并保持所有对照组一致。

```bash
export SEARCH_R1_ASSET_ROOT=/data/search-r1
export SEARCH_R1_CACHE_ROOT=/data/search-r1/cache/retriever
export SEARCH_R1_FAISS_GPU=0
# 在 tmux/screen 的单独会话执行，等待索引和语料完全加载：
bash retrieval_launch.sh 2>&1 | tee /data/search-r1/runs/retriever.log
```

另一个终端执行真实请求，确认得到文档，而非只确认端口开放：

```bash
curl -fsS -X POST http://127.0.0.1:8000/retrieve \
  -H 'Content-Type: application/json' \
  -d '{"queries":["Who wrote Hamlet?"],"topk":3,"return_scores":false}'
```

如果训练与检索分处两台机器，令 `retriever.url` 指向训练机可访问的检索服务器地址，明确绑定/防火墙设置；`difficulty.retrieval_id` 保持同一套编码器、索引、语料的固定身份。换了检索内容就不能继续当作同一实验。

## 5. 在目标机重跑短流程

先建新的 run_id 和输出目录，记录设备、代码快照、资产哈希、完整命令及日志。不要复用本机失败的 `score-run`；不同配置共用输出目录会被控制器拒绝。Ray 临时目录要位于空闲较多的数据卷且路径短，否则可能出现 UNIX socket 超长或对象溢写失败。

```bash
cd /work/R1
export SEARCH_R1_N_GPUS=2                  # 按目标机及实验对照设计确认
export RAY_TMPDIR=/data/r1ray              # 短路径，须在 env/run.sh 前设置
DATA=/data/search-r1
RUN_ID=smoke-target-001
RUN="$DATA/runs/$RUN_ID"
mkdir -p "$RUN" "$DATA/cache/train/hf" "$DATA/cache/train/tmp"
MODEL="$DATA/models/Qwen2.5-3B"
SCORE="$DATA/runs/smoke-input/score.parquet"  # 脚本在目标机生成的两题输入
DEV="$DATA/runs/smoke-input/dev.parquet"

bash env/run.sh searchr1 env \
  HF_HOME="$DATA/cache/train/hf" TMPDIR="$DATA/cache/train/tmp" \
  python -m verl.trainer.main_ppo --config-name difficulty_grpo \
  "actor_rollout_ref.model.path=$MODEL" \
  "actor_rollout_ref.ref.model_path=$MODEL" \
  "data.train_files=$SCORE" "data.val_files=$DEV" \
  data.train_batch_size=2 data.val_batch_size=2 \
  difficulty.mode=score difficulty.score_batch_size=1 \
  "difficulty.output_dir=$RUN/score" \
  "difficulty.score_output=$RUN/labels-v0.json" \
  retriever.url=http://127.0.0.1:8000/retrieve \
  difficulty.retrieval_id=wiki18-e5-pinned \
  data.max_prompt_length=256 data.max_start_length=128 \
  data.max_response_length=64 data.max_obs_length=128 \
  actor_rollout_ref.actor.ppo_mini_batch_size=8 \
  actor_rollout_ref.actor.ppo_micro_batch_size=2 \
  actor_rollout_ref.ref.log_prob_micro_batch_size=2 \
  actor_rollout_ref.rollout.log_prob_micro_batch_size=2 \
  2>&1 | tee "$RUN/score.log"
```

此模板是功能烟测，batch/长度不是正式实验配置。显存较紧时按目标机实测降低 `actor_rollout_ref.rollout.gpu_memory_utilization`，并考虑 `actor_rollout_ref.actor.fsdp_config.param_offload=true`、`actor_rollout_ref.ref.fsdp_config.param_offload=true`、`actor_rollout_ref.actor.fsdp_config.optimizer_offload=true`；本机 `0.20` 加 offload 的组合**尚未通过 rollout 验收**。不支持 FlashAttention 2 的卡另加 `actor_rollout_ref.model.attn_implementation=eager` 和 `actor_rollout_ref.model.use_remove_padding=false`，并检查 vLLM 后端实际运行。每次改变配置都用新输出目录，不能把失败批次计为答错。

验收顺序：确认两题各四条有效评分轨迹和完整标签文件；再用同一硬件配置运行 5–10 个真实更新步骤，检查 0/1 奖励、有限 loss/梯度；最后保存完整 checkpoint，并从它恢复，验证 global step、optimizer、scheduler、scaler、sampler、reference 及下一步训练。用至少 20 step 测量时间和显存后，再锁定正式组的共同 batch/后端。每个检查结果写入新 `runs/<run_id>.md` 和 [进度台账](data_difficulty_progress.md)。

## 6. 进入正式实验

先从原始 train/test 冻结独立 P/D/T 和稳定 ID/哈希；本机只有临时小切片，不能替代。按 [执行步骤](data_difficulty_steps.md)先做 C0 对 P 的四次评分生成 v0，再做 A0–A4；第一阶段选定共同父完整 checkpoint 后，对同一 P 重新评分生成 v1，再做 B0–B3。所有组统一 10 轮上限、同一检索身份、模型起点和硬件配置。只有短流程评分、训练更新、完整保存与恢复都通过，才启动 200 step 正式对照。
