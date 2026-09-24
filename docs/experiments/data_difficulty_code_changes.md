# 第一批实验代码修改

> 当前进度与交接统一见[进度台账](data_difficulty_progress.md)；每次运行按[运行模板](runs/TEMPLATE.md)建档并在阶段节点同步。历史检查结果不代表当前运行状态。

分支：data-difficulty。按用户要求跳过小数据准备及检索服务验证，先修改代码。本轮未占用 GPU、未启动检索服务或训练。

## 实验模块设计规则

本实验遵循仓库根目录 [AGENTS.md](../../AGENTS.md)、[实验模块约束](../../verl/experimental/AGENTS.md) 和 [命令脚本约束](../../scripts/difficulty/AGENTS.md)。这些规则适用于后续全部新增及修改代码。

低耦合要求各模块通过明确的输入输出和少量接口协作；高内聚要求同一职责的逻辑集中维护。训练主循环只负责在适当时机调用实验接口。

| 职责 | 模块归属 | 接入限制 |
| --- | --- | --- |
| 题目身份、标签校验及难度配额采样 | `verl/experimental/difficulty/sampling.py` | 接收题目记录、标签和配置，不依赖训练器 |
| 四次 rollout 的评分编排与进度记录 | `verl/experimental/difficulty/scoring.py` | 通过回调复用生成与奖励流程，不复制推理实现 |
| 实验阶段切换与步骤协调 | `verl/experimental/difficulty/controller.py` | 组合实验模块，不持有训练器对象或访问其私有成员 |
| 随机状态、指纹和原子持久化 | `verl/experimental/difficulty/state.py` | 提供基础函数，不反向依赖实验控制器 |
| 分布式训练状态存取 | 独立 checkpoint 适配模块，待实现 | 与采样、评分算法分离，由 worker 调用 |
| 实验组入口及结果汇总 | `scripts/difficulty/` 和独立汇总模块，待实现 | 脚本仅处理参数和文件输入输出，计算逻辑留在实验模块 |

依赖方向为：命令入口／训练器适配 → 实验控制器 → 采样、评分、状态等基础模块。生成及奖励通过显式回调传入。共用训练代码中不得硬编码 A0/B0 等实验组、具体比例或本机路径。

每个修改的代码块添加中文注释，说明职责、修改原因或关键约束。交付时检查接口、依赖方向、默认行为兼容性和测试范围。

当前核心模块已接入训练、评分、刷新和恢复流程，17 个 CPU 测试通过。实际 GPU 联调未完成；下文第一批记录为历史范围，最新结果见本文件末尾及[核心运行说明](data_difficulty_core_usage.md)。

## 已完成

1. **GRPO 抽题分组**：检索路径在展开 n_agent 次之前，为每次抽题赋予独立 uid。同一道题被多次抽取、不同来源具有相同 index 时，不会合并成同一组。question_id/index 等原有字段继续保留。
2. **组大小检查**：按实际 n_agent 检查 GRPO 组大小，重排后组大小异常会在优势计算前失败。检索路径要求 rollout.n=1，防止与 n_agent 重复展开。
3. **评价尾批**：val DataLoader 不再丢弃最后不足 batch 的题目；评价输出 val/num_samples，并核对结果行数。
4. **极小批次补齐**：当 batch 比并行数小得多时，补齐足够行；去掉补齐行后仍返回 DataProto，保留非 tensor 字段和元数据。
5. **评价采样参数**：多轮活动批次及并行补齐保留 do_sample/validate 等 metadata，避免评价时丢失确定性解码设置。
6. **可配置 attention**：actor/reference 共享模型构建路径支持 flash_attention_2、eager、sdpa，默认保持 flash_attention_2。非 FA2 后端配合 use_remove_padding=true 时明确报错。

修改位置：ray_trainer.py、protocol.py、generation.py、fsdp_workers.py、utils/model.py、ppo_trainer.yaml。critic/reward-model 的独立 FA2 路径未纳入本轮修改；本实验 GRPO 不启用它们。

## CPU 验证

```bash
CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 bash env/run.sh searchr1 python -m unittest discover   -s tests -p 'test_grpo_difficulty.py' -v
```

7 个测试通过，覆盖：

- 同题重复抽取、组重排及 0/1/2/3/4 次正确的优势符号；
- 错误合组时拒绝计算；
- 1/2/3/4/5/9 条样本按 8 路补齐后正确恢复；
- 检索与非检索评价对 1/3/5/9 条样本完整计分；
- 活动批次从 3→2→1→0 的多轮生成始终保留评价参数；
- 禁止不兼容的 attention/去 padding 组合；
- 本地保存的小型随机 Qwen2 模型在 CPU 上分别使用 eager、sdpa 加载并完成前向和反向，有效 token 输出一致。

测试中的小模型和模拟批次用于回归验证，不是正式实验数据或完整模型训练结果。

## 后续运行配置

本机 TITAN 路径先使用以下配置覆盖，待 GPU 空闲后验证：

```text
algorithm.adv_estimator=grpo
do_search=true
actor_rollout_ref.rollout.n_agent=4
actor_rollout_ref.rollout.n=1
actor_rollout_ref.model.attn_implementation=eager
actor_rollout_ref.model.use_remove_padding=false
actor_rollout_ref.actor.ulysses_sequence_parallel_size=1
actor_rollout_ref.actor.use_kl_loss=true
```

这是需要加入实际训练入口的配置片段，未替用户启动训练。模型/数据路径、GPU 数、batch 和 micro batch、长度、检索地址仍需按实验环境完整设置。兼容 FA2 的设备可保留原后端，但各对照组必须一致。

尚待完成：真实模型多 GPU FSDP/vLLM 联调、检索服务验证、难度标签工具与 sampler、完整 checkpoint 恢复及固定 reference。当前 CPU 测试通过不代表本机全量训练已通过。

## 2026-09-24：进度同步与交接规范

本次只修改文档：仓库及实验文档目录的 AGENTS.md、新增进度台账和单次运行模板，并在方案、步骤、条件检查及本记录中增加统一入口。已登记资产校验完成、基础修复的既有测试结果，以及实验模块初稿尚未接入的实际状态。

每次改代码后更新本记录和进度台账，记录修改文件、行为、测试命令及结果、未验证项和下一步；每次跑实验后更新单次运行记录和台账。失败或中断也必须同步。不得把计划进度、历史测试结果或代码文件存在当作本次运行成功的证据。

验证：`git diff --check` 通过；本次新增文档入口及相对 Markdown 链接检查通过。未重新运行代码测试，未启动实验。下一步仍为完成独立实验模块的训练接入、完整状态恢复和相关测试。

## 2026-09-24：核心实现进行中

已接入独立难度控制器、来源×难度采样器、离线四轨迹评分和步骤边界刷新；新增 checkpoint、配置及生成适配模块。训练侧增加绝对停止步数、固定 reference、逐轨迹/轮次种子传递、完整状态 RPC。检索错误明确失败，不记成零分。当前正在编写并运行回归测试，尚不能据此声称 GPU 联调通过。

checkpoint 当前范围为单节点、同 GPU 数、同 FSDP/TP 配置的本地完整恢复，保存每 rank optimizer、scheduler、scaler 和随机状态；跨拓扑迁移不在本次核心实现范围内。实验关闭时新控制器不启用。

## 2026-09-24：核心代码接入完成，GPU 验收待执行

实现入口与命令见[核心运行说明](data_difficulty_core_usage.md)。新增 `configuration.py`、`generation.py`、`checkpoint.py`、`reporting.py` 并完善 sampler、scorer、controller 和 state；新增专用 Hydra 配置与 CSV 汇总命令。训练器只负责窄接口适配，worker 只负责分布式状态存取。默认配置关闭实验功能。

共用代码修改包括：main 入口前置配置检查，trainer 的采样/评分/刷新/保存与恢复调用和步骤边界，generation 的逐轨迹种子及检索错误检查，vLLM 的逐请求 SamplingParams，TP 非张量字段收集，以及 FSDP 的固定 reference、绝对 warmup 和完整训练状态 RPC。

验证命令：

```bash
CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 bash env/run.sh searchr1 python -m unittest discover -s tests -p '*difficulty*.py' -v
```

结果：当时 17 个 CPU 测试通过；本次复审后为 18 个。日志已保存到 `docs/experiments/validation/core_cpu_2026-09-24.txt`。专用配置 `--cfg job` 和 CSV CLI `--help` 检查通过，Python 编译检查及 `git diff --check` 通过。没有启动正式训练、检索服务或 GPU 联调；这些测试不覆盖真实分布式分片恢复及 FP16 溢出。

### 注释覆盖审查（按关键逻辑单元，不按行数）

本轮选取下列 12 个核心单元逐项检查，均有中文注释或接口文档，覆盖高于用户提出的 40% 下限。该清单用于说明检查范围，不以增加注释数量为目标。

| 关键单元 | 注释说明内容 |
| --- | --- |
| 题池身份与标签校验 | 永久 ID、顺序绑定、四个奖励、刷新完整性 |
| 来源及难度配额 | 累计舍入补偿、容量不足、桶内 k 分布 |
| 采样器恢复 | 已消费位置、曝光、branch 的欠额重置 |
| 可续跑评分 | partial 前缀、模型血缘、失败不记零分 |
| 逐轨迹生成 | 独立 seed、活动筛选、轮次和 TP 对齐 |
| 实验控制 | 模块组合、步骤边界、评分 RNG 隔离 |
| 配置与来源 | 允许变更字段、reference 固定、环境一致性 |
| 完整 checkpoint | 完成清单、模型及 driver/rank 状态边界 |
| worker 恢复 | 同拓扑限制、optimizer 设备、scaler 和 scheduler |
| 随机状态及原子写入 | 不同随机流、完整文件可见性、单写者限制 |
| 训练停止及评价 | 完成目标步骤再结束、仅评分不更新参数 |
| 汇总与迁移矩阵 | 同题池配对、空行、重复尝试不静默覆盖 |

下一步：保持正式 GPU 运行暂缓；待恢复运行安排后，在目标设备完成 5–10 步模型／检索／FSDP／vLLM 联调及连续与恢复对照，再进入初始分桶和 A/B 实验。数据切分工具、完整绘图统计和自动矩阵调度仍是外围待办。


最终入口检查发现当前环境已有同名 `scripts` 包，`python -m scripts.difficulty.summarize` 无法定位本项目脚本；已将文档改为直接执行 `python scripts/difficulty/summarize.py`，`--help` 检查通过。评分断点身份改为模型血缘、策略和标签内容，避免绑定本机输出路径，支持迁移目录后继续评分。

最终修改后重跑同一 CPU 测试集：17 个全部通过，归档日志已更新。CSV 汇总使用一条临时模拟指标完成实际导出，字段和值校验通过；该记录是工具验证，不是正式实验结果。`git diff --check` 再次通过。

## 2026-09-24：运行前代码复审与修复

发现训练与评分逐轨迹 `rollout_seed` 先被写成 `int64` 数组，而 `DataProto` 非张量字段必须是 `object` 数组。真实补齐和分发会再次调用一致性检查，可能在首批 rollout 时失败。已统一改为 `object`，并增加经过 `DataProto.check_consistency()`、补齐／还原及训练／评分模拟入口的回归测试。测试由 17 项增至 18 项，全部 CPU 通过；归档日志见 `validation/core_cpu_2026-09-24.txt`。该测试依然不替代实际 Ray/FSDP/vLLM 联调。

检索启动脚本原有占位索引路径并强制 GPU 克隆大索引，无法直接使用已下载资产。现支持可配置资产根目录、单项路径及显式 `SEARCH_R1_FAISS_GPU` 开关；缺文件时先报错。`bash -n retrieval_launch.sh` 和缺资产错误路径验证通过，未加载真实检索服务。脚本选择 CPU 索引时，现有检索编码器仍使用 GPU；目标机器的内存和显存需求需在短流程实测。

复审仍留待目标设备验证：真实 FSDP 分片 optimizer 恢复、FP16 scaler 溢出、vLLM 逐请求种子及 TP 收集、全量索引和语料加载、checkpoint I/O 容量。固定训练池／开发集清单尚未生成，正式实验仍未开始。

## 2026-09-24：两卡与 10 轮配置对齐

专用实验配置显式设置 `max_turns=10`，避免继承值与方案不一致。当前设备的两卡选择通过必填 `SEARCH_R1_N_GPUS=2` 传入配置解析，保留 `trainer.n_gpus_per_node` 命令行覆盖；没有将 GPU 型号、显存或本机路径写入核心算法。研究方案、执行步骤及运行说明同步更新。正式运行仍须实测 3B 模型在两张卡上的显存与吞吐，不能把参数解析成功当作 GPU 可运行。

配置解析验证：`SEARCH_R1_N_GPUS=2` 得到整数 2、`max_turns=10`；环境变量设为 4 时得到整数 4；不设置环境变量但通过命令行覆盖卡数为 2 时解析成功。`git diff --check` 通过。本次未重跑代码测试，也未启动 GPU 任务；此前 18 个 CPU 测试只覆盖修改前的核心逻辑，本次配置变化通过解析检查验证。

## 2026-09-24：真实检索烟测前缓存修复

当前根分区仅约 59 GiB 可用，而真实 wiki 语料的 Arrow 预处理可能产生大缓存。检索启动脚本新增可配置 `SEARCH_R1_CACHE_ROOT`，通过项目 retriever 环境启动后把 Hugging Face、datasets 和临时目录定向到资产所在卷。脚本语法与缺文件错误路径检查通过，真实服务启动及请求结果待本次烟测登记。该修改有中文注释，不改变检索算法或评分协议。

## 2026-09-24：真实评分导入故障修复

首次 GPU 评分在 Ray 任务导入阶段失败；`verl/single_controller/ray/base.py` 的 actor 存活查询引入完整 state API，间接加载 dashboard，在当前 Ray/uvloop 组合下要求主线程已有事件循环。改为调用 Ray 自带的轻量 actor 表查询，保留按 actor ID 获取状态并判断 `ALIVE` 的行为。修改块有中文注释。验证：待进行导入测试和真实评分重试；尚不能算模型推理通过。

Ray/uvloop 导入复验：`bash env/run.sh searchr1 python -c` 设置 uvloop policy 后导入 `RayWorkerGroup` 成功；`git diff --check` 通过。真实评分重试已启动，仍需检查模型和标签。

## 2026-09-24：Ray 临时目录可配置

实际评分重试中，Ray 报告项目所在卷使用率超过 95%，对象溢写可能失败。`env/run.sh` 现在保留外部设置的 `RAY_TMPDIR`，默认仍使用项目缓存；本机后续烟测将指向数据卷。已给修改处添加中文注释。验证：待脚本语法与环境传递检查；当前正在运行的评分仍使用原目录，不能视为已修复其运行环境。

`bash -n env/run.sh`、指定 `RAY_TMPDIR` 后读取环境值、`git diff --check` 均通过；未对正在运行的评分进程应用新目录。

轻量 Ray actor 验证首次失败：`ray._private.state.actors` 返回的字段为大写 `State`，原实现读取小写 `state` 导致误判。已修正 `verl/single_controller/ray/base.py` 的存活判断，添加中文注释。待重新执行真实 Ray actor 查询。

CPU 测试首次重跑时缺少 `SEARCH_R1_N_GPUS` 环境变量，一项配置血缘测试报错（17 项通过、1 项错误）。`tests/test_difficulty_core.py` 现在显式覆盖虚拟 world size=2，以验证协议而不依赖执行设备的 GPU 配置；修改处有中文注释。待复验。

轻量 Ray actor 实例复验通过：uvloop policy 下，`RayWorkerGroup._is_worker_alive` 对实际 `ALIVE` actor 返回真。随后完整 18 项难度模块 CPU 测试通过，日志 `/root/data/search-r1/runs/gpu-smoke-20260924-1022/cpu-tests.log`；`git diff --check` 通过。GPU 评分、训练和恢复仍未验收。
