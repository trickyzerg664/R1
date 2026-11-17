# SFT：DeepSeek 搜索轨迹，host3 TITAN

更新日期：2026-11-17。分支：`sft`。代码基点固定为官方 Search-R1 `598e61bd1d36895726d28a8d06b3a15bed19f5d3`。

## 代码和运行位置

- 主机 `host3`，容器 `lzy_yolo11`，原目录 `/root/myprojects/R1/R1`。
- 本分支直接在原目录开发，不另建 worktree。确认分支名为 `sft`，数据及设备信息写在本文和配置中。
- 原工作区 9 个 RL 修改已经过 34 项 CPU 回归，并提交在 `data-difficulty` 的 `cb6551fc8faa2147562f99a44d5a669c54d1d15b`；本分支没有继承该提交或 fork main 的 `71e072a4`。
- 官方旧 PPO、GRPO、worker 和生成代码不因本次 SFT 修改。新增代码集中在 `search_sft/`，不依赖 Ray、vLLM、在线检索或 MetaX 运行库。

## 实现范围

| 文件 | 作用 |
|---|---|
| search_sft/prepare.py | 去重、已有知识保守筛选、评测排重、逐轮编译、分组与发布清单 |
| search_sft/protocol.py | 初始提示、工具文档格式、动作校验、structured 观察和 bounded 预算重放 |
| search_sft/data.py | 数据哈希校验、样本分组、保留真实尾批和零权重 dummy |
| search_sft/loss.py | 仅监督当前 assistant；按题权重、token CE 总和及真实全局 batch 归一化 |
| search_sft/train.py | Qwen 加载、ZeRO-3/FP16、累积、验证、日志和真实更新计数 |
| search_sft/checkpoint.py | 完整状态、随机数与 batch 游标恢复，滚动保留 |
| search_sft/export.py | 独立进程调用 DeepSpeed 官方转换器导出 HF safetensors 分片 |
| search_sft/preflight.py | 资源、依赖和历史 Base 文件身份检查 |
| configs/sft | 数据、预算、设备、训练参数和历史 Base 哈希 |
| scripts/sft/run_host3.sh | 显式选择阶段；默认仅做 preflight，不启动训练 |
| tests/sft | 因果性、长度、筛选、分组、loss/梯度、尾批和 CPU 恢复测试 |

不为这个实验改写官方旧 SFT 骨架。独立 Transformers + DeepSpeed 入口解决多轮监督和 TITAN 的分片/优化器卸载需求。Transformer 主干仍读取完整上下文，仅 LM head 限制在当前 target 所需的尾部位置。

## 数据与监督目标

教师文件：私有 HF `tr1ckyzerg/R1-sft`，提交 `a23313e8ef015b931abf5fa6c1704f14c4e1547d`，路径 `runs/b29ca10632104eae9b39963290fe9531/accepted.jsonl`。

SHA256：`d210492c2583c878f466869010a43dcb25b86161f58af5ad181c1d5197f62519`，原始 3,011 题。

已有文本审查：去重后 3,009 题；保守移出/隔离 1,147 题，剩余 1,862 题候选。草案 train 1,675 题/4,112 行，val 187 题/466 行，pilot 256 题/636 行（属于 train）。这些是学生分词及正式评测排重前的草案数量，不能用作最终训练规模。检索前答案提及包含候选猜测；题干选项和最终记忆用语隔离，不能称其全部为已证明的记忆作答。

每个真实 assistant 调用展开一行：此前可见的问题/历史/工具结果为输入，当前 `<think>…</think>` 和一个 search/answer 动作为监督目标。历史 token、工具反馈及 padding 不计损失。失败 history、gold 和未来 observation 不进入模型输入。动作闭标签终止，不凭空补 EOS。

按题等权：题 q 共 Nq 个监督 token，Q 题、M 行，行权重 `M/(Q*Nq)` 乘当前行 CE 总和；整体取 M 行平均后等于 Q 题各自的 token 平均。当前 target 的第一个 token 由 prompt 最后一个位置预测。上下文+目标总预算4096、target256、观察2048、最多10个assistant轮次；采用历史 bounded/structured 行为规范，需强制最终回答或无法完整重放的题移出。

支持 draft 数据检查，正式 pilot/full 强制要求 final release、完整评测清单及匹配的模型/tokenizer 身份。评价集 JSONL 至少包含 question，建议包含 id/original_id；Parquet 可读取 question 或 prompt。清单示例（路径与哈希必须填实际值）：

```json
{
  "complete": false,
  "sets": [
    {"name": "D256", "path": "D256.jsonl", "sha256": "填写真实文件SHA256"}
  ]
}
```

正式清单默认要求 D1000、D256、T2000、T1024、T128、official_test 均有非空文件及正确 SHA256。导出 ID、规范化题目及高度相似题排除记录。历史 RL 训练池交集允许存在；当前未取得其完整清单，交集统计记“未核实”，不能记0。

## 训练和恢复

- 基座：与历史 RL 一致的 Qwen2.5-7B Base，身份和逐文件哈希见 `configs/sft/base_model_hashes.json`；不使用 Instruct 或 RL checkpoint 初始化。
- 全参数、epoch1、lr5e-6、AdamW、warmup5%、cosine、clip1.0、seed42。
- 默认2 GPU、每卡micro1、常规累积16，即全局32行；尾批按真实行数归一化，不重复样本补齐。
- FP16、DeepSpeed 动态缩放、CPU optimizer offload、SDPA、梯度检查点；关闭 BF16、FA2 和 packing/remove_padding。
- 手动控制 DeepSpeed 累积边界，关闭其重复 GAS 除法。overflow 跳步单独记录，不计入成功更新；调度器由引擎在成功更新时推进。
- 完整 checkpoint 记录模型/优化器/调度器/scale、每rank随机数、batch游标和代码/数据/config/拓扑身份。恢复要求相同world_size和阶段。
- 只滚动保留最近一份完整状态；新状态成功写入并标记完成后才清理旧状态，需预留两份状态峰值。导出在独立进程执行，保留最终 HF 权重；不默认保留四份7B完整状态。
- pilot 与 full 各自从 Base 和新 optimizer 开始，不在 pilot 后追加一轮。

## 环境与命令

独立环境拟采用 Python3.10、Torch2.4.0 CUDA12.1、Transformers4.47.1、DeepSpeed0.15.4。依赖文件为 `env/sft/requirements.in`；真实验收后才能生成已验证锁文件。不要安装整个 RL requirements，也不要改变原 RL 环境。

```bash
cd /root/myprojects/R1/R1
python3 -m venv .envs/sft
# CUDA_HOME 必须指向含 nvcc 和 cuRAND 开发库的工具链。
# 本机已在 .cache/sft-cuda 验证，可在安装 DeepSpeed 前显式设置：
export CUDA_HOME=/root/myprojects/R1/R1/.cache/sft-cuda
.envs/sft/bin/python -m pip install torch==2.4.0 --index-url https://download.pytorch.org/whl/cu121
.envs/sft/bin/python -m pip install -r env/sft/requirements.in
export R1_SFT_MODEL=/填写实际且符合历史哈希的Qwen2.5-7B路径
bash scripts/sft/run_host3.sh test
bash scripts/sft/run_host3.sh preflight --check-model
# 只作数据审查，不能用于正式训练：
bash scripts/sft/run_host3.sh prepare --draft --output data/sft/releases/deepseek-draft-v1
# 完整评价资产齐备后，发布独立 final 数据目录：
bash scripts/sft/run_host3.sh prepare
bash scripts/sft/run_host3.sh pilot --run-id deepseek-pilot-001
bash scripts/sft/run_host3.sh full --run-id deepseek-full-001
bash scripts/sft/run_host3.sh full --run-id deepseek-full-001 --resume
bash scripts/sft/run_host3.sh export --checkpoints runs/sft/deepseek-full-001/checkpoints --output runs/sft/deepseek-full-001/hf
```

以上训练命令有前置条件，不代表已经执行。验证阶段可使用明确标注为 synthetic smoke 的小模型和草案数据；不把其结果标为7B训练验收。

## 当前验收台账

2026-11-17：首次 CPU 回归18项通过（4.48s），使用原只读Torch2.4.0/Transformers4.47.1验证环境，pytest放入独立 `.cache/sft-test-deps`，没有改变原RL依赖。后续修改的最终回归结果另行追加。没有启动正式 SFT，真实7B全参资源仍待验收。

真实数据已校验同步到 `data/sft/raw/accepted.jsonl`（73,835,966 bytes）。缓存3B中的四个分词文件经逐文件SHA256核对，与历史7B的tokenizer完全相同；只复制这些分词文件至 `data/sft/tokenizer-qwen25-7b` 作数据检查，不使用3B权重。

学生分词及协议重放额外移出32题target超256、16题需预算强制收尾。实际draft `data/sft/releases/deepseek-draft-20261117-v1` 剩1,814题：train1,632题/3,897行/243,299监督token，val182题/440行/27,847监督token，pilot256题/615行/37,956监督token。正式评价清单尚未齐备，此draft不能用于正式pilot/full。发布时记录编译代码文件哈希；该草案生成于代码提交前。

双卡合成验证使用 `.cache/sft-smoke-env`：Python3.10，固定TF4.47.1/DeepSpeed0.15.4，继承只读系统Torch2.4.0。该验证环境不等同于最终全新隔离训练环境，未生成正式requirements.lock。原容器无CUDA编译器；最小编译工具安装在 `.cache/sft-cuda`，nvcc12.1.105，独立于系统和原RL环境。DeepSpeedCPUAdam还要求ninja在PATH，启动器已自动加入所选Python的bin目录。

首次合成尝试 `continuous1` 因ninja不在PATH失败，日志 `.cache/sft-validation-20261117/continuous.log` 保留；修正后使用新的 `continuous2/interrupted2`，双卡保存/恢复/冷加载仍在验证，结果以最终追加记录为准。合成fixture和日志均位于缓存目录，不作为7B实验结果。

两张TITAN RTX均为24GB。部署检查时GPU已有其它占用，CPU可用约105GiB，项目所在盘可用约215GiB，仅代表当时快照。完整7B训练需额外核实加载、优化状态、保存及导出峰值；不足时报告具体缺口，不自动降为3B/LoRA。

统一效果评价在独立冻结的评价工作区执行，Base/RL60/RL80/SFT共享prompt、检索、停止规则和response_only_v1判分。当前分支不开展新的RL训练或移植MetaX rollout。

## 最终代码验收（2026-11-17）

上述中间状态由本节更新。新增21项CPU回归全部通过（4.63s），命令：

```bash
CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
PYTHONPATH="$PWD:$PWD/.cache/sft-test-deps" \
.envs/searchr1/bin/python -m pytest tests/sft -q
```

双卡真实进程验收使用20,768参数随机Qwen2模型、35条合成训练行及3条合成验证行，明确属于程序smoke。配置为ZeRO-3、FP16、SDPA、CPU优化器卸载、micro1、global32；运行包含32行完整batch和3行尾批，两次成功优化器更新。

- `continuous4` 连续运行2个batch；`interrupted4` 在第1个batch完整保存后退出，再由新进程恢复至第2个batch。
- 两组导出权重逐tensor比较：最大绝对差0；相对FP16舍入后的初始权重，27个参数tensor确有更新。
- 两组HF导出均在新进程中冷加载成功，固定文本的tokenizer编码一致，前向logits有限。
- 最终代码使用 `search_sft` checkpoint命名空间，正确处理DeepSpeed返回的额外元数据；CPU恢复测试同步覆盖额外引擎字段。
- 结果证据：`.cache/sft-validation-20261117/comparison.json`、`continuous-v4.log`、`interrupt-v4.log`、`resume-v4.log`、`export-continuous4-v4.log`、`export-interrupted4-v4.log`；产物在 `.cache/sft-fixture-20261117/runs/`。
- 前期失败日志保留：首次ninja PATH、第二次cuRAND开发链接库、第三次checkpoint返回状态适配；对应 continuous.log、continuous-v2.log、resume-v3.log。修正均已在v4完整流程验证。

SDK修复仅在SFT缓存：nvcc12.1.105、cuRAND及开发库10.3.2.106；CPUAdam已实际编译加载。验证环境继承只读系统Torch，尚不能据此宣布正式全新隔离环境或7B全参资源验收完成。

真实DeepSeek草案中，保留的1,814题没有观察裁剪标记；最终评价排重、数据来源及证据可见性复核仍未全部完成，status保持draft。当前尚缺符合历史哈希的完整7B基座和全部评价题单，未启动真实数据pilot/full。实际数据清单和测试摘要另见 `sft_validation_20261117.json`。
