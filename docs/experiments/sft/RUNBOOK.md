# SFT 执行手册

先读PLAN和HANDOFF；以下命令在host3的lzy_yolo11容器中执行。命令存在不代表前置条件已完成，也不代表获得了正式训练启动指令。

## 0. 接手先检查

```bash
cd /root/myprojects/R1/R1
git branch --show-current
git status --short
git log -3 --oneline
ps -ef | grep 'search_sft' | grep -v grep
nvidia-smi
df -h . /root/data
free -h
cat .cache/sft-base-download-20261118/status.json
```

预期分支sft。Git有未提交修改先读diff，不覆盖他人修改。存在同任务进程时先观察实际进度，不并发启动相同下载或run。status中的pid需和进程命令行一起检查；文件中的downloading/running可能是异常退出后遗留状态。

## 1. Base 下载与确认

只下载公开 `Qwen/Qwen2.5-7B` 固定快照，不能换Coder/Instruct。当前目标 `.cache/models/Qwen2.5-7B`；哈希依据 `configs/sft/base_model_hashes.json`。

若确认没有同任务下载进程，使用可断点续传命令：

```bash
PYTHONNOUSERSITE=1 .cache/sft-smoke-env/bin/python -m search_sft.download_base \
  --endpoint https://hf-mirror.com \
  --job-dir .cache/sft-base-download-20261118
```

该缓存环境是已验证的准备/小模型环境，不是正式隔离训练环境。直连huggingface.co在本机曾超时；hf-mirror.com实测可达。下载公开模型显式不使用私人HF token。无论走哪一来源，四个分片LFS摘要和全部11个本地核心文件SHA256必须匹配历史RL记录。

下载日志/状态入口是job-dir/status.json；large partial在目标目录的 `.cache/huggingface/download/*.incomplete`。只有phase=complete、11个verified_files齐全且无errors，才能登记Base准备完成；metadata_verified和文件存在不能替代完整校验。不要手工伪造完成标志或修改expected哈希迁就其它模型。

## 2. 正式环境与资源

准备代码/原始资产不会自动启动训练。创建独立正式环境时：

```bash
python3 -m venv .envs/sft
export CUDA_HOME=/root/myprojects/R1/R1/.cache/sft-cuda
.envs/sft/bin/python -m pip install torch==2.4.0 --index-url https://download.pytorch.org/whl/cu121
.envs/sft/bin/python -m pip install -r env/sft/requirements.in
bash scripts/sft/run_host3.sh test
bash scripts/sft/run_host3.sh preflight --check-model --output .cache/sft-preflight.json
```

当前工具链nvcc12.1.105、cuRAND开发库10.3.2.106位于SFT缓存；CPUAdam已经在小模型验证环境编译过。新环境仍需确认ninja可执行文件可见、CPUAdam可加载。启动脚本会把所选Python的bin加入PATH；不要修改原 `.envs/searchr1`。

正式环境通过后记录python/pip版本和 `pip freeze` 到运行产物，再确定已验证lock，不能将requirements.in称为已验证完整环境。

CPU内存预算仍有缺口，需要先确认可用资源与卸载方案。当前CPUAdam配置按7B估算基本113.5GiB，默认余量170.2GiB；小模型成功不能证明真实7B可跑。若改NVMe卸载，先更新磁盘预算和验收配置，不能直接套用CPU卸载的215.6GiB总输出预算。

## 3. 正式数据发布

现有raw在 `data/sft/raw/accepted.jsonl`，已核验SHA。draft在 `data/sft/releases/deepseek-draft-20261117-v1`。不要把draft的status手工改成final。

取得历史冻结D1000/D256/T2000/T1024/T128和官方test的实际题单后，准备 `data/sft/evaluation/manifest.json`。每个set需要name、path、sha256；相对path以manifest目录解析。JSONL每行至少有question，可带id/original_id；Parquet可用question或prompt列。

```json
{
  "complete": false,
  "sets": [
    {"name": "D256", "path": "D256.jsonl", "sha256": "真实文件SHA256"}
  ]
}
```

这是格式示例，不是可发布完整清单。全部默认required_evaluation_sets齐备、非空、身份正确并完成人工/近重复复核后，才能声明complete。原始train/test已在 `/root/data/search-r1/datasets/nq_hotpotqa_train`，历史正式D/T不能仅凭原始split或随机seed推断。

使用新的release目录，已有release不覆盖：

```bash
# 缺少完整评价资产时，只能做检查草案：
bash scripts/sft/run_host3.sh prepare --draft --output data/sft/releases/新的草案版本
# 完成前置检查后，发布配置中指定的独立final目录：
bash scripts/sft/run_host3.sh prepare
```

检查manifest中的status、evaluation_exclusions_complete、tokenizer_hashes、protocol、files/statistics、筛选数量和问题互斥。当前草案1814/1632/182/256及122/20名义更新数不是发布承诺。P10000交集报告和语义证据复核需要另行完成并记入记录。

## 4. 真实7B资源验收

当前仅有20,768参数合成模型的双卡验证，真实7B资源测试尚未完成。`tests/sft/make_smoke.py` 生成的是随机小模型，不能拿它冒充7B验收。

接手者应先解决CPU预算，再在独立scratch配置和合成输入上形成真实7B资源短跑方案：使用已核验的7B Base、计划精度/卸载、最长上下文，至少2次成功optimizer更新、有限梯度与真实参数变化、峰值记录，以及完整保存→新进程恢复→导出冷加载。此处尚没有宣称验收通过的一键7B命令。

程序 `--stage smoke` 可用于明确标注的合成资源测试，允许draft并跳过正式Base门禁，因此应先独立核验Base；输出必须标为smoke，不进入效果表。`--stop-after-batches`仅支持smoke，用于新进程恢复测试。

资源验收状态写HANDOFF和单次记录。失败保留日志，不自动降低模型规模或更换训练方法。

## 5. pilot 与 full

只有正式环境、模型、final数据和7B资源验收通过，且用户授权启动真实数据实验后执行。每次选择唯一run_id，先复制runs/TEMPLATE.md填记录；不要复用示例ID覆盖产物。

```bash
# run_id须改为本次唯一标识；输出根以configs/sft/deepseek.yaml为准。
bash scripts/sft/run_host3.sh pilot --run-id 本次唯一pilot标识
# pilot验收后，full独立从Base开始：
bash scripts/sft/run_host3.sh full --run-id 本次唯一full标识
```

训练日志含batch、actual_updates、overflow_skipped、actual_batch_rows等。不能把batch数当成真实参数更新数。进度同时记录已持久化checkpoint游标，不把尚未保存的进度写成可恢复。

训练结束后，从run/checkpoints导出到run/hf：

```bash
bash scripts/sft/run_host3.sh export \
  --checkpoints /root/data/search-r1/sft-runs/本次run/checkpoints \
  --output /root/data/search-r1/sft-runs/本次run/hf
```

导出会启动新进程冷加载、检查tokenizer编码一致和有限logits。通过后再登记export_verified。pilot验收且HF/日志/评价归档后按PLAN保留策略处理其完整优化状态；勿触碰其它实验产物。

## 6. 恢复、评价与交接

```bash
bash scripts/sft/run_host3.sh full --run-id 原full标识 --resume
```

先确认无同run进程，latest.json指向的checkpoint有complete.json及各rank文件。恢复要求相同数据、代码、config、world_size、阶段；源代码或配置变化应新建run或先明确迁移规则，不能直接绕过签名校验。

评价在独立冻结工作区加载Base/RL60/RL80/SFT四组，按PLAN统一设置。复用已有Wiki/E5/索引/Arrow缓存，不在SFT期间同时加载60GiB索引。正式评价前做固定查询和模型回归。用户尚未指定该评价工作区的最终路径，需在建立时登记，不假定本分支已有完整统一评价入口。

每次结束或交接：更新HANDOFF中的代码、状态、日志/产物、阻塞、下一条可执行步骤；更新真实run记录。只有实际检查过的进程、模型或checkpoint才能写“已验证”。
