# 难度实验核心代码：运行与验收

更新：2026-09-24。核心流程已接入，18 个 CPU 测试通过；本机完整检索及双卡模型初始化通过，首批 rollout 因显存不足失败，完整 GPU 联调和正式实验未完成。迁移见[目标设备执行清单](data_difficulty_migration.md)，当前状态见[进度台账](data_difficulty_progress.md)。

## 已实现范围

- 冻结题池的稳定 ID、标签完整性校验、来源×H/M/E×k 配额采样及恢复。
- 同一检索／生成／奖励路径的四次随机评分，失败批次不计为零分，评分可从已完成前缀继续。
- 训练步骤边界刷新标签、独立训练／评分随机流，以及多轮活动筛选和 TP 收集中的逐轨迹种子对应。
- 固定 reference；actor 从完整 checkpoint 恢复模型、每 rank optimizer、scheduler、scaler、随机流、采样器和标签。完成清单含文件哈希。
- 绝对步骤停止条件、训练实际 k0–k4、有效组率、曝光、生成 token 和检索次数；JSONL 转 CSV；五档标签迁移计算。

入口为 `verl.trainer.main_ppo --config-name difficulty_grpo`，实验模块默认关闭，专用配置显式打开。职责和依赖规则见根目录及 `verl/experimental/AGENTS.md`。

## 前置条件

检索服务可通过仓库根目录的 `retrieval_launch.sh` 启动。它默认读取本机 `/root/data/search-r1/` 下的最终索引、语料和 e5 模型；迁移后设置 `SEARCH_R1_ASSET_ROOT=/path/to/assets`，或分别设置 `SEARCH_R1_INDEX_PATH`、`SEARCH_R1_CORPUS_PATH`、`SEARCH_R1_RETRIEVER_MODEL`。默认索引留在 CPU 内存；只有目标设备索引显存足够时才设置 `SEARCH_R1_FAISS_GPU=1`。当前服务的查询编码器仍要求 GPU。先在目标设备实测索引／语料加载的内存峰值，并确认 8000 端口服务可访问。

先冻结独立 train/dev 文件，执行去重、长度检查并记录清单哈希。本轮未生成这些文件。不要将下载的整个官方 test 文件反复用于开发集调参。

在目标设备完成检索服务和 5–10 步短流程验证后再运行 A/B。当前核心实现限定单节点、FSDP、vLLM、四条搜索轨迹、二值奖励及独立 KL loss。完整恢复要求相同 GPU 数、FSDP/TP 配置及 Torch/Transformers/vLLM 版本；支持在相同拓扑和环境的其他设备恢复，不支持跨拓扑重分片。

下面是命令模板，先把变量设为实际路径。专用配置固定 `max_turns=10`。GPU 数通过 `SEARCH_R1_N_GPUS` 显式提供，也可用命令行覆盖；当前设备选两卡，其他设备按实测资源配置。batch、长度和后端仍需在目标设备统一确认。

```bash
SEARCH_R1_N_GPUS=2  # 当前设备使用两卡；迁移后按目标设备修改
export SEARCH_R1_N_GPUS
MODEL=/path/to/Qwen2.5-3B
TRAIN=/path/to/frozen/train.parquet
DEV=/path/to/frozen/dev.parquet
RUNS=/path/to/runs
RETRIEVAL_ID=encoder_corpus_index_fixed_version_or_hash
RETRIEVER_URL=http://127.0.0.1:8000/retrieve

# 每组共享这些参数；RUNS 下各运行目录必须独占。
COMMON=(--config-name difficulty_grpo
  "actor_rollout_ref.model.path=$MODEL"
  "actor_rollout_ref.ref.model_path=$MODEL"
  "data.train_files=$TRAIN" "data.val_files=$DEV"
  "retriever.url=$RETRIEVER_URL" "difficulty.retrieval_id=$RETRIEVAL_ID")
```

本机 TITAN 需另加 `actor_rollout_ref.model.attn_implementation=eager`、`actor_rollout_ref.model.use_remove_padding=false`，并保持序列并行度 1；这仍不代表实际 vLLM/FSDP 显存和吞吐已验证。各对照组后端和 batch 必须一致。

## 初始评分与第一阶段

```bash
# 仅生成标签，不更新参数；仍初始化训练 worker，因此不是轻量 CPU 命令。
bash env/run.sh searchr1 python -m verl.trainer.main_ppo "${COMMON[@]}" \
  difficulty.mode=score "difficulty.output_dir=$RUNS/score-v0" \
  "difficulty.score_output=$RUNS/labels-v0.json"

# A0：相同来源边际下的自然采样，无需标签。
bash env/run.sh searchr1 python -m verl.trainer.main_ppo "${COMMON[@]}" \
  "difficulty.output_dir=$RUNS/A0-seed42"

# A2 示例；A1/A3/A4 分别用 [0.33,0.34,0.33]、[0.6,0.2,0.2]、[0.2,0.2,0.6]。
bash env/run.sh searchr1 python -m verl.trainer.main_ppo "${COMMON[@]}" \
  "difficulty.output_dir=$RUNS/A2-seed42" "difficulty.labels=$RUNS/labels-v0.json" \
  'difficulty.ratios=[0.2,0.6,0.2]'
```

默认 200 个更新步骤，每 50 步评价、100 步保存，最后一步总会保存。每个步骤恰好消费一个题目批，再展开四条训练轨迹。评分轨迹不用于训练。

## 第二阶段与续训

先按开发集冻结 r* 和父 checkpoint。假设父 step=200，完整目录形如 `A2-seed42/checkpoints/step_200`；不能只提供其内部 `actor/` 权重目录。

```bash
PARENT="$RUNS/A2-seed42/checkpoints/step_200"

# 同一 C1 重新评分，产生 B1/B3 共享的 v1；不更新模型。
bash env/run.sh searchr1 python -m verl.trainer.main_ppo "${COMMON[@]}" \
  difficulty.mode=score "difficulty.resume=$PARENT" \
  "difficulty.output_dir=$RUNS/score-v1" "difficulty.score_output=$RUNS/labels-v1.json"

# B3：明确 branch，恢复完整父状态，仅切换标签和比例；最终绝对步数为 500。
bash env/run.sh searchr1 python -m verl.trainer.main_ppo "${COMMON[@]}" \
  "difficulty.resume=$PARENT" difficulty.resume_mode=branch difficulty.additional_steps=300 \
  "difficulty.labels=$RUNS/labels-v1.json" 'difficulty.ratios=[0.1,0.8,0.1]' \
  "difficulty.output_dir=$RUNS/B3-seed42"
```

B0：v0+r*；B1：v1+r*；B2：v0+[0.1,0.8,0.1]；B3：v1+[0.1,0.8,0.1]。四组必须使用同一父完整状态和初始 reference。r* 为实际冻结结果，不预设一定是 A2。

普通中断续训使用 `resume_mode=continue`，保留原始比例、刷新及评分设置；checkpoint 中的当前标签优先于初始 labels 文件。每次恢复使用新的输出目录，日志不会覆盖前一次尝试。追加预算或绝对停止步数须明确设置，warmup 不重启。

周期刷新可设置 `difficulty.refresh_steps=[300,400]`（绝对步骤），或 `difficulty.refresh_every=100`。结束步不再刷新。B4 的刷新计划必须在运行前锁定，不能看到结果后随意变更。

## 产物与检查

| 产物 | 含义 |
| --- | --- |
| `run.json` | 解析后的实验设置、题池与训练来源标识 |
| `metrics.jsonl` | 配置、训练、评分、checkpoint 和最终评价事件 |
| `labels_step_N.json` | 该训练分支在 N 步的刷新标签 |
| `*.json.partial` | 已完成评分前缀，不能作为完整训练标签输入 |
| `checkpoints/step_N/actor/` | 模型、tokenizer 及每 rank 训练状态 |
| `driver.pt`、`metadata.json`、`COMPLETE.json` | driver 状态、恢复元数据和完整性清单 |

```bash
bash env/run.sh searchr1 python scripts/difficulty/summarize.py \
  --metrics "$RUNS/A2-seed42/metrics.jsonl" --output "$RUNS/A2-seed42/metrics.csv"
```

`reporting.migration(old_payload, new_payload, rows)` 返回 5×5 计数和行比例。当前提供核心汇总数据，完整绘图、bootstrap 报告及自动实验矩阵调度不属于本次核心实现。代码快照（含未跟踪源码）、实际命令、日志和设备检查仍须按[运行模板](runs/TEMPLATE.md)登记。

成本记录区分训练步骤耗时、在线评分耗时、导入标签的已记录耗时。失败批次、服务端独立运行、checkpoint I/O 和设备利用率的完整成本需要运行日志及外部监测补充，不能将现有字段直接称为端到端 GPU 小时。模型内容校验会读取权重文件，首次启动和恢复可能有明显磁盘扫描耗时。

## 验证边界

```bash
CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
bash env/run.sh searchr1 python -m unittest discover -s tests -p '*difficulty*.py' -v
```

18 个测试通过，包含真实 `fit` 的模拟 worker 接入：精确三步更新、步骤一刷新、完整 driver 保存、从第一步恢复到第三步、评分模式不新增更新。CPU AdamW 验证恢复后的下一次参数更新与连续更新完全相同；不据此承诺分布式 FP16 或 vLLM 位级一致。

仍须在目标 GPU 检查真实 FSDP optimizer 分片恢复、FP16 scaler 溢出路径、vLLM 逐请求种子及 TP 收集、模型显存、检索服务。正式实验尚未启动。
