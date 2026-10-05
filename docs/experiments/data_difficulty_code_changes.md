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

## 2026-09-24：目标设备迁移引导脚本

新增 `scripts/difficulty/migrate_target.sh`，职责仅为目标机准备：解析源机/目标目录、经 rsync 拉取含 dirty 修改的工作树、按锁文件重建环境、调用既有固定版本资产下载器、检查完整状态、运行两个环境检查和 18 项 CPU 测试；可选复制临时烟测输入。脚本不实现训练/评分算法，也不自动启动检索或 GPU 实验。每个步骤有中文注释，失败保留日志与最后阶段，重复运行可接续资产下载。验证：`bash -n`、`--help` 和 `--dry-run` 已通过；真实跨机器 SSH、环境安装与下载尚未执行。

迁移脚本补充幂等边界：首次要求空目标代码目录，代码复制中断可接续；已完成迁移的重复运行默认不覆盖目标机后续修改，需显式 `--refresh-code` 才重新拉取。缺少系统 uv 时复用已有引导环境。尚未进行真实跨机安装。

环境预检发现当前源机没有 rsync 可执行文件，且 22 端口未监听；目标迁移脚本改用 SSH/tar 流式复制源码与可选烟测切片，避免依赖源机 rsync。真实跨机执行仍需先具备可达的源机 SSH 服务或入口；未擅自开启服务。

迁移脚本进一步增加源端 SSH/目录/tar 预检；迁移说明的手工示例同步改成 SSH/tar，避免依赖当前源机不存在的 rsync。验证：待重跑语法、帮助、干运行和文档代码块检查；跨机网络未验证。

本轮脚本验证完成：`bash -n scripts/difficulty/migrate_target.sh`、`--help`、`--dry-run`、错误参数拒绝、迁移文档 9 个 bash 代码块语法检查及 `git diff --check` 均通过。还用当前无 SSH 监听的 localhost 做了失败路径实测，脚本退出非零并在独立日志中记录 `FAILED stage=拉取代码 exit=255`，没有开始下载/训练。真实跨设备传输、环境构建与资产下载仍未验证。

## 2026-09-24：目标机独立 Git 迁移

按用户要求取消源机 SSH/离线包方案，`scripts/difficulty/migrate_target.sh` 改为 HTTPS Git clone，支持分支、完整提交 ID 校验及干净工作树的快进更新；后续环境/资产检查不变。新增 `scripts/difficulty/prepare_smoke.py`，从目标机下载的原始 train split 确定性筛选 NQ/HotpotQA 训练 8、开发 4、评分 2 题，记录原始文件和产物哈希；已有完整小切片时不改写，部分产物时明确报错。所有新代码按职责划分并有中文注释。验证：本机实际生成并复用小切片，行数 8/4/2 正确；跨设备 Git clone、环境和资产下载待验证。

验证补充：`https://github.com/trickyzerg664/R1.git` 的 `data-difficulty` 分支实际可通过 HTTPS 克隆（当时远端提交 `459b8b41588446ed1e25f08e15a01cba4255477e`）；新脚本的帮助、干运行及 shell 语法通过。`prepare_smoke.py` 用本地真实 parquet/tokenizer 生成 train=8、dev=4、score=2，再次运行保留原产物；迁移文档命令块语法和相对链接检查通过。环境安装、资产重新下载及目标机 GPU 验收均未在本轮运行。

## 2026-09-24 12:22 UTC：迁移脚本无参数默认目录

修改 `scripts/difficulty/migrate_target.sh`：以脚本实际所在目录为共同根目录，默认代码为 `myprojects/R1/R1`、资产为 `data/search-r1`，沿用本机相对 `/root` 的布局；`--repo`、`--data-root` 仍可分别覆盖。修改了 `scripts/difficulty/README.md` 与 `docs/experiments/data_difficulty_migration.md` 的下载、运行和后续烟测路径。新增逻辑的中文注释说明了目录来源与可覆盖边界；未触及训练、评分和下载算法。

验证：`bash -n scripts/difficulty/migrate_target.sh`、`--help`、`git diff --check` 通过。把脚本复制到临时目录、切换到其他工作目录执行 `--dry-run`，输出为临时目录下的 `myprojects/R1/R1` 与 `data/search-r1`；单独指定 `--repo` 后数据目录仍为默认值，干运行没有创建目标目录。尚未在目标设备执行完整 Git 克隆、环境安装、资产下载或 GPU 验收；远端分支须包含此次修改，目标机通过 HTTPS 下载的脚本才会获得新默认值。

## 2026-09-26：目标机搜索训练旧策略 log probability 元数据修复

目标机 `train-smoke-20260926-112131` 通过 `NCCL_P2P_DISABLE=1` 完成两卡初始化、真实检索和 step 0 验证，但在 step 1 生成后调用 `ActorRolloutRefWorker.compute_log_prob` 时出现 `KeyError: micro_batch_size`。搜索路径直接调用该 worker 入口，绕过普通 `generate_sequences` 内的重算元数据设置；`dp_actor.compute_log_prob` 同时要求 `micro_batch_size`、`temperature` 和 `use_dynamic_bsz`，动态批量还要求 `max_token_len`。

修改 `verl/workers/fsdp_workers.py`：在 `compute_log_prob` 入口用 worker 已按数据并行卡数归一化的 rollout 配置补齐四个重算字段，并保留 tokenizer 字段。该入口同时服务普通调用，不改采样、评分、奖励及训练主循环。修改仅在源端仓库完成；目标机独立副本尚未同步，真实 GPU 重试未验证。

验证：`python3 -m py_compile verl/workers/fsdp_workers.py`、`git diff --check` 通过；`CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 bash env/run.sh searchr1 python -m unittest discover -s tests -p '*difficulty*.py' -q`，18 项通过。CPU 测试不覆盖真实 FSDP/vLLM worker 入口；下一步在目标机同步修复，用新 run_id 重试 5 步并检查完整 checkpoint。

## 2026-09-26：目标机搜索训练 actor 更新温度元数据修复

目标机 `train-smoke-20260926-114502` 已越过旧策略概率计算、奖励和优势计算，在 step 1 参数更新时，`dp_actor.update_policy` 因缺少 `temperature` 报错。上一修复仅在 `compute_log_prob` 的 worker 本地补齐元数据；它返回概率张量，训练 driver 的原始批次没有获得温度。

修改 `verl/workers/fsdp_workers.py` 的 FSDP `update_actor` 入口，从该 worker 的 rollout 配置设置训练批次温度，与正常生成路径读取的配置一致。保留 `dp_actor` 对温度存在性的检查；不改搜索、奖励或训练主循环。验证：`python3 -m py_compile verl/workers/fsdp_workers.py`、`git diff --check` 均通过；离线环境下运行 `CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 bash env/run.sh searchr1 python -m unittest discover -s tests -p '*difficulty*.py' -q`，18 项 CPU 测试通过。该测试集未覆盖真实 FSDP worker 的 GPU 更新入口；目标机 5 step、checkpoint 与恢复仍待验证，详见[运行记录](runs/train-smoke-20260926-114502.md)。

## 2026-09-27：正式 P/D/T 冻结与校验入口

新增 `verl/experimental/difficulty/pool_preparation.py`：从原始 train/test DataFrame 确定性构建互斥 P/D/T；NQ/HotpotQA 按训练来源比例分配目标数量，整个官方 test 的规范化问题均从 P/D 排除，题目经 tokenizer 实际渲染长度筛选后生成稳定 `question_id`。去重规则为 Unicode NFKC、casefold、去标点及空白合并；T 来自官方 test，D/P 来自 train。纯模块不依赖 Ray/GPU/路径。

新增 `scripts/difficulty/freeze_pool.py`：命令层读取原始 parquet 和固定 tokenizer，默认 P=10000、D=1000、T=2000，写 `P.parquet`、`D.parquet`、`T.parquet` 和最后发布的 `manifest.json`；记录原始/输出/tokenizer 文件 SHA-256、每题来源/原始 ID/问题哈希/token 长度。输出目录已有文件时拒绝覆盖；`--verify` 复查哈希、行序、来源和题目互斥。新增 `tests/test_difficulty_pool_preparation.py` 的两项 CPU 语义测试，检查跨 split 防泄漏、来源配额、超长过滤、输入行重排后的稳定性，以及不足容量/重叠拒绝。

验证：`python3 -m py_compile`、`git diff --check`、CLI `--help` 通过；离线环境下难度模块 CPU 测试 20 项通过。真实原始数据、固定 tokenizer 的小规模 CLI 端到端输出 P=20/D=10/T=10，随后独立 `--verify` 通过，产物位于 `/root/data/search-r1/runs/pdt-tool-validation-20260927-0200`，仅作工具验证，不是正式 P/D/T。默认大规模 P/D/T 尚未运行；目标机运行结果、最终模型/长度和零奖励修复均未验证。正式冻结必须等模型/tokenizer/长度确定，使用独立新目录。

## 2026-09-27：零奖励评分轨迹诊断

目标机复核仍显示两题八条轨迹全为 0；11 次检索观察超长警告，生成 token 分别为 `[82,114,150,150]` 和 `[150,104,114,113]`。`qa_em` 的 `Extracted answer` 日志随机以约 1/64 概率打印，因此日志中没有该行不能证明答案标签不存在。当前标签缺少原始响应，无法判断是没有闭合 `<answer>`、输出截断，还是答案与标准答案不符。

修改 `verl/experimental/difficulty/generation.py`：为 `score_batch` 加可选 `trace_chars`，沿用奖励器的有效响应 mask 解码每条已有轨迹，在记录中保存闭合答案标签状态、最后一个答案、标准答案和响应末尾。`verl/trainer/ppo/ray_trainer.py` 只传入诊断长度；`verl/experimental/difficulty/controller.py` 把非零诊断长度写入评分上下文，避免混用断点；`configuration.py` 将长度限制在 0–2000，`ppo_trainer.yaml` 默认 0，常规评分结果与 checkpoint 策略不变。新增 CPU 测试检查正常/未闭合标签、多标签最后答案和末尾截取。新诊断仍须在目标机跑真实 GPU 评分才能判定零奖励原因，不据此将正式实验标记为可开始。

验证：`python3 -m py_compile`、`git diff --check` 均通过；离线 `python -m unittest discover -s tests -p '*difficulty*.py' -q` 21 项通过。未在源机运行新 GPU 评分。

## 2026-09-27：避免检索反馈被当作模型答案

目标机轨迹诊断 `score-trace-20260927-051309` 把多条轨迹的答案提取为 `and`。代码核对表明无效动作反馈内含字面 `<answer> and </answer>`，而 `RewardManager` 原先把模型响应和环境观察一起交给严格 EM 提取器；诊断输出也沿用了混合文本。该伪答案本次仍得 0，但可能在标准答案恰为 `and` 时造成误奖，且不能用来判断模型是否有合法答案。

修改 `verl/trainer/main_ppo.py`：检索轨迹若有 `info_mask`，奖励器从有效响应中只保留模型生成 token，剔除检索观察后再与原 prompt 一起交给原 `qa_em`，保持原二值 EM 奖励规则、答案样例约束及奖励写回位置。没有 `info_mask` 的旧路径保持原行为。修改 `verl/experimental/difficulty/generation.py`：可选诊断沿用同一 `info_mask`，使摘要只显示模型文本。根据用户要求保留官方系统提示词及无效动作反馈原文；新增一项 CPU 回归，同时检查环境伪标签不得计奖、真正生成答案仍得奖。未改检索索引、模型权重或题池。

验证：`python3 -m py_compile`、`git diff --check` 通过；离线难度模块 CPU 测试 22 项通过。真实目标机评分、训练奖励和其它数据来源尚未在新代码上验证；此前全部零奖励运行不作为正式比较基线。此修复改变了评分输入文本，正式实验所有组必须在同一修复版本下重跑。

## 2026-09-27：一小时预算的小池评分入口

新增 `scripts/difficulty/score_budget_probe.sh`，只封装既有冻结题池与评分命令：默认从同源原始数据确定性生成临时 P20/D10/T10，初始 prompt 限 256 token，评分使用 `max_prompt_length=4096`、每轮生成 128、检索观察 256、四条轨迹、严格 EM、固定检索 ID。必须显式 `--run`，GPU 选择由 `CUDA_VISIBLE_DEVICES` 指定，数据根、模型、输出目录和检索地址可覆盖。准备最多 8 分钟、评分默认最多 40 分钟；每题 batch=1，限时停止后汇总 `labels.json.partial` 已持久化的前缀，并显示 K0–K4 与有效答案标签数。记录 Git 提交/工作区状态、完整日志与原始退出码。该小池不是正式 P/D/T，部分标签不能进入正式训练。

验证：`bash -n`、`--help`、无 `--run` 预览、非法时间参数和未指定 GPU 的拒绝路径通过；尚未在目标机运行 GPU/限时中断路径。脚本未改评分、采样、系统提示词或模型实现。

## 2026-09-27：四卡 7B 评分的空观察 dtype 修复

四卡 Qwen2.5-7B Base 已越过两卡的 FSDP→vLLM 权重同步 OOM，并完成首题多轮生成，但在 RewardManager 解码时收到 float token ID。源机用同族 Qwen tokenizer 复现：全部观察文本为空时返回形状 (4,0)、dtype float32 的张量；与整数 token ID 拼接会把整段响应上转为 float。

修改 search_r1/llm_agent/generation.py::_process_next_obs：将 tokenizer 的 input_ids 明确转为 long，保持空观察与非空观察的 token 类型一致。未改官方系统提示词、奖励判定、检索内容或实验开关；这是共用生成路径的类型修复。tests/test_difficulty_core.py 增加全部四条轨迹同轮结束的零宽空观察回归，验证拼接后仍为 long。

验证：源机 bash env/run.sh searchr1 python -m unittest discover -s tests -p test_difficulty_core.py，14 项通过；共享生成回归 tests/test_grpo_difficulty.py 7 项通过；git diff --check 和 py_compile 通过。目标机尚未同步和 GPU 复验；四卡评分的单次记录见 runs/score-7b-4gpu-20260927-091511-2460617.md。关键路径注释审查覆盖空观察类型约束、失败触发和下游拼接；无新增跨模块依赖或重复评分逻辑。

## 2026-09-28：7B actor 反向传播显存峰值与无效微批修复

目标机四卡 7B 短训练在 step 2 actor backward 申请 2.32 GiB 时 OOM：该 worker 自身约占 46.22 GiB。先前建议将全局 actor PPO micro batch 4→1 是错误的；FSDP worker 按四卡整除后变成 0，造成下一次短训练在首步 actor 更新入口除零。原全局 micro 4 已对应每卡 1 条，不能再靠降低它节省每卡反向传播峰值。

修改 `verl/workers/actor/dp_actor.py`：显式开启 `response_logits_only` 时，向 Transformers 4.47.1 的 Qwen2 模型传 `num_logits_to_keep=response_length+1`，让 LM head 只计算回答及前一个预测位置的词表 logits，并在截取后转 FP32。未开启时保留原有全段 logits、转 FP32、温度缩放和截取顺序；评分阶段不启用该选项，已有四卡评分前缀的配置与执行路径均不变。选项只用于 Qwen2 且要求 `use_remove_padding=false`；它不改变注意力主干计算或奖励规则，真实 GPU 显存节约幅度尚未验证。

修改 `verl/experimental/difficulty/configuration.py`：难度训练入口按数据并行卡数检查 actor 全局 mini/micro batch 的正值及整除性，在 7B 权重加载前拒绝微批归零和静默截断；可选回答段 logits 与去 padding 同开时直接报错。其他非难度实验入口不受本次校验影响。`tests/test_grpo_difficulty.py` 以微型 Qwen2 CPU 模型确认启用选项后 LM head 输入由 7 token 缩至 4 token，回答 logits 与 LM head 梯度仍与全段计算一致；`tests/test_difficulty_core.py` 确认四卡全局 micro=1 提前报清晰错误。

短流程重试建议四张空闲 A6000，训练部分全局 `actor_rollout_ref.actor.ppo_micro_batch_size=4`、`actor_rollout_ref.actor.ppo_mini_batch_size=8`，可将题目 batch 4→2，并用 `+actor_rollout_ref.actor.response_logits_only=true` 启用 Qwen2 末段 logits。batch 2 每步展开为 8 条轨迹，仍为完整的每题四轨迹；全局 mini 8、micro 4 在四卡上分别是每卡 2/1。降低题目 batch 未必能解决单条长轨迹的峰值，本次代码优化才直接针对全词表 logits。评分续跑须沿原四卡配置和原输出目录，不追加本训练专用选项。若用于正式 A0–A4，所有对照组须统一冻结这个新训练配置和新 checkpoint 指纹；不得接续旧配置训练 checkpoint。

验证：离线 CPU `python -m unittest tests.test_grpo_difficulty tests.test_difficulty_core -q`，23 项通过；`py_compile` 与 `git diff --check` 通过。目标机尚未同步此代码，真实四卡 7B 反向传播、有限梯度范数、step 5 checkpoint 和评分续跑均未在新路径验证。下一步同步代码，仅用新运行目录执行短训练并量测 GPU 峰值；若仍 OOM，再考虑缩短上下文或增加卡数，改变评分生成长度时应另开评分目录并重新打分。

审查补充（2026-09-28）：保持默认 actor/评分分支与提交前同一操作顺序，仅显式开关走末段 logits。CPU 测试扩为 24 项：双样本含左侧 padding 的回答 logits、整个 Qwen 模型梯度和 CPU BF16 结果与全段路径一致；去 padding 与新开关同时启用会在加载模型前拒绝。`num_logits_to_keep=response_length+1` 的多一个位置用于预测回答首 token。测试不能替代真实四卡 FP16/FSDP 显存和梯度检查；目标机尚未运行审查后版本。


## 2026-09-28：7B actor token 统计量反传重算（源端优化）

检查发现生成轮结束时 `vllm_rollout.py` 已调用 `free_cache_engine()`，FSDP/vLLM sharding manager 已卸载推理权重；无需重复添加清理逻辑。先前 `response_logits_only` 只减少 LM head 的词表投影范围，完整检索轨迹仍进入 Transformer，且回答段熵计算会在反传前保存较大的 softmax 中间量。

修改 `verl/workers/actor/dp_actor.py`：新增显式开关 `actor_rollout_ref.actor.checkpoint_token_statistics=true`。仅在非去 padding、具有梯度的 actor 前向中，对回答 token 的原有 log probability 和 entropy 公式使用 PyTorch 非重入 checkpoint；反传时重算统计量，减少前向保留的词表张量，不截断上下文、不改变损失公式或标签。默认关闭；评分和 `torch.no_grad()` 的旧路径仍直接计算。该选项可与 `response_logits_only=true` 一起用于新训练运行。`configuration.py` 在难度实验入口拒绝该开关与 `use_remove_padding=true` 同时启用，避免静默无效。未修改官方提示词、检索和奖励。

`tests/test_grpo_difficulty.py` 比较原路径与重算路径的损失、logits 梯度和微型 Qwen2 全模型梯度，并确认前向保存字节数下降；`tests/test_difficulty_core.py` 验证不兼容配置会提前报错。离线 CPU 命令 `CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 bash env/run.sh searchr1 python -m unittest tests.test_grpo_difficulty tests.test_difficulty_core -q`：27 项通过。CPU 测试使用项目已有 naive log probability 实现绕开 FlashAttention 的 GPU 限制；目标机 FlashAttention、FP16/FSDP 的显存峰值、有限梯度范数、5 步 checkpoint 尚未验证。完整 Transformer 轨迹仍参与反传，若单条轨迹过长仍可能 OOM。下一步目标机拉取新提交，在独立训练目录同时启用两个训练开关并复测；已有 9/20 题评分前缀保持原评分配置。

## 2026-09-29 13:06 UTC：沐曦迁移分支的 Ray GPU 注册

分支 `data-difficulty-muxi` 基于 `data-difficulty` 提交 `ab78b058692353190351206033d90f6c84978737`；独立检出目录为 `/mnt/public/code/lyk/lzy/R1-vllm-metax`。

- 修改 `verl/trainer/main_ppo.py`：本地单节点以 `trainer.n_gpus_per_node` 显式注册 Ray GPU，并校验 PyTorch 可见设备和 Ray 集群资源；外部集群由各节点显式声明资源。未启动正式训练。
- 编译检查与 `git diff --check` 通过。此前在主目录的同等 Ray 逻辑完成两卡（物理 4、5）及八卡 worker 实测；**本分支尚未重跑入口 GPU 测试**，不将旧结果记为本分支验证。
- vLLM 0.11.0 与沐曦插件、mcoplib 的组合仍在独立试验环境测试。生成和权重同步尚未接入本分支；原有 data-difficulty 算法流程未改。

## 2026-09-29 13:25 UTC：沐曦 vLLM 0.11 接口封装初稿

新增 `verl/third_party/vllm/metax_v_0_11_0/`：`llm.py` 将生成输出转为旧 rollout 的张量格式，并以 level-2 休眠释放推理显存；`worker.py` 通过 vLLM 的 worker 扩展从本机 safetensors 文件读取完整权重，RPC 只传路径；`parallel_state.py` 对未支持的 TP>1 明确失败。输入限制为本地模型目录、完整 HF state_dict 和每 worker 单卡。

验证：新增模块 `compileall` 通过；此前在隔离试验环境，Qwen2.5-3B 单卡生成、休眠/唤醒、独立 worker 扩展更新并恢复一项层归一化权重通过。**本分支模块尚未与旧 veRL 调用路径联调，也未验证完整 FSDP 权重或训练**。下一步接入版本选择、rollout 和 FSDP manager 后重跑。

## 2026-09-29 13:26 UTC：沐曦适配接入旧 veRL 调用路径

- 修改 `verl/third_party/vllm/__init__.py`：仅当 vLLM 主包为 0.11.0 且同版本沐曦插件存在时选用新封装；0.3.1–0.6.3 路径保留。
- 修改 `verl/workers/rollout/vllm_rollout/vllm_rollout.py`：0.11.0 也以 token ID 作为输出，不额外解码；data-difficulty 的逐请求 seed 逻辑保留。
- 新增 `verl/workers/sharding_manager/metax_vllm.py`，修改 `verl/workers/fsdp_workers.py`：仅沐曦路径使用完整 CPU FSDP state_dict 和单卡 manager，其余版本沿用旧 manager。TP>1 当前明确不支持。
- Python 编译检查、`git diff --check` 通过。新增调用路径尚未完成实际旧 veRL/FSDP 联调，不能视为训练可用。

## 2026-09-29 13:37 UTC：FSDP 完整权重导出配置调整

沐曦实机小型 Qwen 测试在 `FullStateDictConfig(offload_to_cpu=True)` 的 `module.state_dict()` 阶段超过两分钟且未写出同步文件，已终止该测试；尚不能判定完整 FSDP 路径可用。将 `metax_vllm.py` 改为 `offload_to_cpu=False`，由同步层逐张量复制到 CPU，再重试。该调整可能提高短时 GPU 峰值，7B 多卡尚未验证。

## 2026-09-29 13:51 UTC：沐曦 vLLM/FSDP 单卡联调与限制

`verl/third_party/vllm/metax_v_0_11_0/llm.py` 修正 pad token ID 为 0 时错误回退到 eos 的情况。独立 Qwen2.5-3B 测试已验证新封装的完整权重加载和生成。两层小 Qwen2 与 FSDP、vLLM 同卡联调中，默认多进程引擎启动停滞；`VLLM_ENABLE_V1_MULTIPROCESSING=0` 时权重同步、生成、休眠成功，但 Python 退出时 MetaX torch allocator 抛 `Trying to free a pointer not allocated here`，退出码 134。显式清理 vLLM/FSDP 对象后仍复现。参见 [兼容性运行记录](runs/metax-vllm-compat-20260929-1330.md)。

代码目前仅实现 TP=1、完整 HF 权重同步；未验证正式训练、7B 多卡、checkpoint 恢复。当前插件 wheel 针对 MACA 3.3，目标机为 MACA 3.7，需使用匹配版本重新构建或选取对应 wheel 并解决生命周期异常。此前编译与 `git diff --check` 通过；本次改动后的检查结果另记。

适配器与 manager 的注释已改为通用 worker 说法；进程模式由 vLLM 运行配置决定。此文字修改后执行编译和差异检查，不代表运行故障已解决。
## 2026-09-30：沐曦纯净 venv 与睡眠模式复测

新建 `/mnt/public/code/lyk/lzy/envs/vllm-metax-clean33`，不继承系统包，统一安装 MACA 3.3 的 torch、Triton、FlashAttention、FlashInfer、vLLM 0.11、vllm-metax 和 mcoplib；`pip check` 通过，关键模块都从该 venv 加载。新增环境启动脚本 `/mnt/public/code/lyk/lzy/envs/maca-3.3.0.15/run-clean33.sh`，不复用其他 venv 的 PYTHONPATH；已运行 `vllm_metax_init` 和 `mcoplib_init`。后一初始化为 Qwen2 注册必需的 `silu_and_mul` 等算子。

Qwen2.5-3B 普通推理输出 `1+1等于2。` 且退出码 0。tiny-Qwen2 仅启用睡眠模式、未调用 `sleep()` 时生成 4 token 后退出码 139；faulthandler 指向进程退出时垃圾回收。保留 allocator C 回调引用的最小试验仍为 139，已恢复原插件源码。训练、评分、FSDP 和恢复均未运行。详细日志与后续验收见 [单次记录](runs/metax-clean33-20260930.md)。此环境方案目前只通过普通推理，不代表完整训练可用。

### 2026-09-30 02:56 UTC：MetaX 无休眠兼容路径

- 修改 `verl/third_party/vllm/metax_v_0_11_0/llm.py`：默认关闭会在退出时段错误的 vLLM sleep allocator；`VERL_METAX_ENABLE_SLEEP_MODE` 仅接受 `0/1`，仅显式 `1` 才调用 sleep/wake。关闭时权重和 KV cache 常驻，FSDP 同步仍通过 safetensors/RPC 执行。
- 修改 `verl/workers/sharding_manager/metax_vllm.py` 注释，明确常驻模式的显存生命周期。新 venv 安装 `tensordict==0.6.2`，因为仓库通用依赖的 `<0.6` 与 MetaX Torch 2.6 不能共同导入；当前通过 PYTHONPATH 使用项目，没有将旧 CUDA 环境的 requirements 直接安装到 MetaX venv。
- 验证：`run-clean33.sh .../smoke_fsdp_cleanup.py` 与 `.../smoke_fsdp_train_no_sleep.py` 均退出码 0；后者完成一次优化器更新、二次权重同步和生成。日志见 [本次记录](runs/metax-clean33-20260930.md)。正式 3B/7B 训练、保存、恢复及多卡内存仍未验证，不能据此启动 A0–A4。

### 2026-09-30 03:11 UTC：MetaX 可复现入口与 Ray 临时路径

- 新增 `env/metax/run.sh` 和 `env/metax/README.md`：以仓库位置推导隔离 MACA 3.3 SDK、venv 和库路径；使用 `env -i` 排除系统 MACA 3.7 与其他 Python 包；保留明确指定的 GPU/检索变量。Ray 临时目录默认 `/tmp/r1ray33`，避免 UNIX socket 路径长度错误及共享卷 96% 使用率告警。
- 验证：`bash -n env/metax/run.sh`、训练入口导入、Hydra `difficulty_grpo --cfg job`、Ray GPU worker 均退出码 0。真实 Qwen2.5-3B 的 FSDP→vLLM 权重同步和生成退出码 0；详情及残余风险见 [单次记录](runs/metax-clean33-20260930.md)。正式训练、checkpoint、恢复和多卡仍未验证。

### 2026-09-30 06:45 UTC：迁移机本地训练数据入口

- `scripts/data_process/qa_search_train_merge.py` 新增 `--raw_root`，从已下载 NQ/HotpotQA JSONL 读取共同字段并沿用原 prompt/reward 映射；不填时保留原线上数据行为。创建指定输出目录。
- `scripts/difficulty/prepare_smoke.py` 新增可选 `--model`，允许复用目标机已校验的 Qwen2.5-3B tokenizer；默认目录不变。
- 已验证 Python 编译与 `git diff --check`；实际 parquet 生成、训练和恢复尚未运行，见 [本轮记录](runs/metax-training-readiness-20260930-1445.md)。

### 2026-09-30 06:58 UTC：检索启动脚本适配独立环境

- `retrieval_launch.sh` 新增 `SEARCH_R1_RETRIEVER_ENV` 分支，直接使用已校验的独立 Python 环境，并统一传递索引、语料、模型和缓存参数；不设置时仍走原项目环境。命令使用数组，避免空格及可选参数错位。
- `bash -n` 与 `git diff --check` 通过；检索进程已启动但仍在装载，服务请求尚未验证。数据预处理 169615 行及烟测 8/4/2 题和哈希验证通过，见 [本轮记录](runs/metax-training-readiness-20260930-1445.md)。

### 2026-09-30 07:15 UTC：检索接口普通请求返回值

- `search_r1/search/retrieval_server.py` 根据 `return_scores` 分支接收底层结果；默认 `false` 只接文档列表，`true` 接文档和分数，修复默认请求 HTTP 500。
- 修复后重启已校验检索环境，真实 POST 返回 3 个文档且退出码 0；两卡 MCCL all-reduce 和评分 Hydra 配置解析也通过。评分与训练尚未启动，见 [本轮记录](runs/metax-training-readiness-20260930-1445.md)。

### 2026-09-30 07:34 UTC：Ray 本地 CPU 注册上限

- `verl/trainer/main_ppo.py` 在本地单节点 Ray 初始化时读取可选 `SEARCH_R1_RAY_CPUS`，正整数才生效；未设置时保持原行为。`env/metax/run.sh` 将此变量穿过隔离环境；烟测脚本指定 8 核。目的是避免 144 核节点预启动过多 worker 导致 agent 30 秒内未就绪。
- Python 编译、`bash -n` 与 `git diff --check` 通过；受影响训练重试尚未完成，不能把评分成功视为参数更新成功。首次失败日志和评分结果见 [本轮记录](runs/metax-training-readiness-20260930-1445.md)。

### 2026-09-30 07:45 UTC：Ray GPU actor 冷启动等待

- `verl/single_controller/ray/base.py` 将首个 GPU actor 注册的固定 120 秒等待改为可选 `SEARCH_R1_RAY_ACTOR_START_TIMEOUT`，默认仍 120 秒；检查变量为正整数。`env/metax/run.sh` 转发此变量，本次烟测设为 600 秒。
- Python 编译、`bash -n`、`git diff --check` 通过。第三次训练尚未运行；第二次失败退出码 1、训练 0 step，详见 [本轮记录](runs/metax-training-readiness-20260930-1445.md)。

### 2026-09-30 08:43 UTC：MetaX 修复后的实际训练验收

- 本轮代码修复后的 Qwen2.5-3B 双卡评分（2 题 × 4 轨迹）、真实训练 step_1、从 step_1 继续到 step_2 均退出码 0。step_1/step_2 的 `COMPLETE.json` 与全部文件哈希经项目 `read_checkpoint` 检验通过。
- `SEARCH_R1_RAY_CPUS=8` 和 `SEARCH_R1_RAY_ACTOR_START_TIMEOUT=600` 消除本机 144 worker 启动压力和 actor 120 秒冷启动超时；默认行为仍兼容未设置变量的旧环境。无休眠 vLLM 路径显存约 46 GiB/卡，GPU5/6 均在进程退出后释放。正式 P/D/T、7B 和长期稳定性仍未验证，详情见 [本轮记录](runs/metax-training-readiness-20260930-1445.md)。

### 2026-09-30 09:17 UTC：7B 八卡正式题池的留出数据入口

- `scripts/data_process/qa_search_train_merge.py` 增加可选 `--split test`；本地 FlashRAG 资产的 NQ test 与 HotpotQA 标注 dev 统一映射为留出 `test.parquet`，训练默认行为保持不变。两个来源仍只保留共同问答字段并沿用原 prompt/reward 生成。
- `python3 -m py_compile` 与 `git diff --check` 通过；实际 test parquet、P/D/T 冻结、7B 八卡训练与恢复尚未验证，见[本轮记录](runs/metax-7b8-readiness-20260930-1717.md)。

### 2026-09-30 10:12 UTC：MetaX 7B 八卡权重同步峰值显存

- `verl/workers/sharding_manager/metax_vllm.py` 将 FSDP 全量权重导出改为 `offload_to_cpu=True, rank0_only=False`；八个 TP=1 rank 都保留各自完整 CPU state_dict，继续通过既有共享内存 safetensors 同步各自 vLLM。目的是避免 GPU 上额外克隆约 7B 全量权重。
- 首次 0.25 vLLM 显存配额因 KV cache 预算 -3.74 GiB 失败；0.40 配额使八卡 KV cache 各约 5.81 GiB / 108k tokens，但第一次 `state_dict()` 在 GPU 50 GiB PyTorch + vLLM 常驻下 OOM，并伴随同步层 `mcMemcpyAsync` invalid argument，退出码 1。CPU 导出尚待真实评分重试验证；需同时检查是否重现旧环境小模型 CPU offload 停滞。静态编译与差异检查后再运行。

### 2026-09-30 13:54 UTC：MetaX 多轮生成权重同步复用

- `verl/workers/sharding_manager/metax_vllm.py` 在无休眠模式下只同步尚未同步的 actor 权重；公开 `invalidate_weights()`，同步成功才标记可复用。启用 sleep 后仍每次重新同步，避免读取已释放的权重。
- `verl/workers/fsdp_workers.py` 在 actor 更新成功后调用可选失效接口，使下一训练 step 或评分使用新权重；非 MetaX manager 无该接口时保持旧行为。`tests/test_metax_sync_cache.py` 覆盖连续两次生成仅导出一次、参数更新后重导出、sleep/失败后重新导出。
- Python 编译、`git diff --check`、隔离 MACA 3.3 环境的 2 个 CPU 单元测试均通过。当前进行中的 `train1` 进程在修改前已加载旧模块，不能作为该优化的 GPU 验证；下一次独立运行须核对权重版本、同步次数、训练更新和耗时。

### 2026-09-30 14:01 UTC：mx 检索超时按实测覆盖

- 代码中的检索默认读取超时仍是 120 秒；本次失败请求服务端耗时 148.53 秒后返回 200，故八卡 7B 重试脚本 `run-7b8-cache.sh` 单次覆盖 `retriever.timeout=600`。没有把异常请求伪装成空结果；超过 600 秒仍中断并保留日志。
- `bash -n` 通过；真实训练重试正在运行，超时覆盖的有效性和正式吞吐尚未证实。具体退出码见[运行记录](runs/metax-7b8-readiness-20260930-1717.md)。

### 2026-09-30 14:48 UTC：FP16 溢出不再伪报训练成功

- `verl/workers/actor/dp_actor.py` 将 `ShardedGradScaler` 初始值开放为 `fsdp_config.grad_scaler_init_scale`（默认仍 65536，值须为正且有限）；每个 mini batch 对比 scaler 更新前后倍率，输出 `actor/optimizer_step`，以辨别数值溢出导致的 `optimizer.step()` 跳过。
- `verl/workers/fsdp_workers.py` 在 actor 更新后检查实际优化器步数；若全部跳过，在学习率调度器和权重同步失效之前报错，避免生成误导性 checkpoint。`tests/test_actor_scaler_step.py` 覆盖正常步和降 scale 跳步；2 个 CPU 测试、编译与 `git diff --check` 通过。
- 触发证据：`train-cache1` 的 `actor/grad_norm=inf`、optimizer state 条目为 0、scaler 65536→16384，而训练却退出码 0。独立 `train-scale1` 使用初始 scale 1024 验证实际八卡更新中；通过前不得进入正式实验。

### 2026-09-30 16:16 UTC：Adam 状态延后至反传后装载

- `verl/workers/fsdp_workers.py` 不再在 `update_actor` 前提前把 CPU optimizer state 装入 GPU；`verl/workers/actor/dp_actor.py` 在每个 mini batch 的 backward、GradScaler unscale 和梯度裁剪后，仅有限梯度才按需装载，执行 `optimizer.step` 后立即卸载。异常路径也卸载，避免下一 mini batch 再遇到状态与激活叠加；仅 `fsdp_config.optimizer_offload=true` 生效，默认 false 不变。
- 触发证据：原 FP16 + ref offload + vLLM 0.32 的第 1 步真实更新并生成 Adam 状态；下一次从完整 checkpoint 恢复时，原 worker 在反传前先装入 Adam 状态，GPU0 于 2.32 GiB 申请处 OOM。`tests/test_actor_scaler_step.py` 增加状态装载/卸载时序测试；3 个 CPU 测试、Python 编译和 `git diff --check` 通过。新逻辑八卡验收中。

### 2026-09-30 16:31 UTC：允许仅改变 optimizer 内存放置的恢复

- `verl/experimental/difficulty/configuration.py` 的父 checkpoint provenance 不匹配时，仅额外以反转 `actor.fsdp_config.optimizer_offload` 的配置再计算一次指纹；它完全匹配父指纹才允许恢复，且立即恢复当前配置值。保存的新 checkpoint 仍记录本次真实配置指纹。这样可从旧 `false` 状态切换到 CPU offload，其他模型、数据、reference、随机种子、后端及学习率设置仍不得改变。
- `tests/test_difficulty_core.py` 的恢复测试增加 optimizer 放置变化可用、原 seed 不同仍拒绝的断言。单测、编译与 `git diff --check` 通过；真实 7B 八卡续训结果待 `resume-opt-offload2` 验收。

### 2026-09-30 16:49 UTC：恢复状态使用同一限定兼容判断

- resume-opt-offload2 通过前置 prepare_config 校验后，controller 的 load_state_dict 仍按旧指纹拒绝。configuration.py 提取 provenance_matches，ray_trainer.py 在装载状态时验证它，然后只传入已验证父指纹；controller.py 默认保持严格比较。这样仅 optimizer_offload 内存放置可以变更，其他训练来源约束不变。
- 两项定向恢复测试、Python 编译及 git diff --check 通过。resume-opt-offload3 八卡验收中；第 2 步有效更新和 checkpoint 未经完成验证前，不宣称 OOM 已解决。

### 2026-10-01 00:27 UTC：Adam 延迟装载八卡连续验证

- 代码未新增修改。当前可选 optimizer CPU offload 时序在第 2 步单步恢复及第 3、4 步连续恢复中通过；三步 grad_norm 均有限，actor/optimizer_step 均为 1，完整 checkpoint 均生成且进程退出码 0。此前第 2 步反向传播 OOM 已不再复现；本结论仅针对当前八卡参数。


## 2026-10-01T01:45:11+00:00：检索长度诊断编排

新增运行产物目录中的 workflow.py 与 base-score.sh 副本，用于512重复/1024/2048同题评分、原样转发检索返回并记录完整证据、按题比较奖励和难度桶。通用生成、检索服务、奖励、训练主循环未修改。职责集中于运行编排和诊断记录，复用 score_pool/load_labels 与现有评分入口。

验证：py_compile通过；2048 Hydra配置解析通过；代理与后端真实响应JSON完全一致；tokenizer padding_side=right；同题比较和按题统计CPU检查通过。512评分已启动，GPU三组完整结果尚未验证；原20步训练保持暂停。证据见 runs/metax-obs-length-20261001-0938.md 和 /mnt/public/code/lyk/lzy/runs/metax-obs-length-20261001-0938/proxy-verification.json。


## 2026-10-01T03:53:58+00:00：新生成协议接入

新增context_budget.py、tests/test_generation_budget.py；修改generation.py、ray_trainer.py两处GenerationConfig参数、difficulty/generation.py诊断记录，修复test_difficulty_core.py模拟fit的临时资产/provenance夹具。structured保持未超限token原样，超限保留标签并分配文档内容；bounded把结束提示和最后答案纳入4096总预算，问题与完整历史始终保留，禁止静默丢弃生成token。模块不依赖Ray/GPU/本机路径，默认legacy兼容，训练器仅转交配置。

本次8项生成CPU测试通过；核心17项首次1错误系旧测试缺路径，已补夹具复验中。尚未验证GPU/吞吐/训练显存。关键逻辑注释已覆盖公共接口、协议开关、预算边界、诊断与失败路径；注释覆盖按逻辑单元检查，不以行数计。详细运行记录 runs/metax-protocol-pilot-20261001-1155.md。


## 2026-10-01T04:02:12+00:00：新生成协议验收与执行

8项新增CPU测试及17项核心回归全部通过，编译和差异检查通过。新增运行编排protocol_pilot.py，复用既有评分、训练、来源指纹和checkpoint哈希校验；固定64题评估、按预先规则判断128/256、批量一致性测试、新256题和20step有限训练依次执行。默认旧协议保持兼容，旧标签不与新标签混用。GPU完整评分、吞吐、反传与20step尚未验证。详细标准与命令见[runs/metax-protocol-pilot-20261001-1155.md](runs/metax-protocol-pilot-20261001-1155.md)。


## 2026-10-01T04:07:14+00:00：输出问题补齐检查

发现数据集问题固定补齐4096位置，而actor当前use_remove_padding=false；新协议现仅删除所有样本共同的左侧补齐，保留每条完整原问题，减少训练无效位置。生成测试加入补至900窗口的输入和输出宽度断言，8项重跑中。此前17项核心回归已通过；本次GPU尚未启动。配置预检、已知奖励汇总和配对比较检查通过，见preflight-verification.json。


2026-10-01T04:08:16+00:00：移除共同问题补齐后的8项生成测试再次全部通过（21.739秒）；编译、git diff --check通过。17项核心回归已通过，配置预检通过。GPU尚未验收，开始启动有限阶段控制器。


2026-10-01T10:25:19+00:00：独立评分原外层3小时预算不足，在240/256题时退出124，18:14触发SIGTERM，GPU已释放，训练0step。保留240题及原失败历史，以metax-protocol-resume-20261001-1822原样续评剩16题；先备份并校验原前缀、数据、源码与配置，完整256题且旧240记录逐字段一致才独立训练20step。续评1小时、训练6小时上限，以覆盖实测成本，不更改模型生成参数或评分种子。新编排protocol_resume.py语法检查通过，实际恢复及训练未验证。


2026-10-01T10:28:31+00:00：续跑1822在GPU启动前的配置比较失败，原因是父控制器环境没有SEARCH_R1_N_GPUS，而原bash入口才导出卡数。已将比较改为不提前计算环境插值的配置声明比较，同一bash入口和源码已核验；两个实际配置CPU比较通过，编译通过。1822的错误、日志及240题备份保留；新尝试metax-protocol-resume-20261001-1828，评分参数和原240题不变。


2026-10-01T13:47:19.205906+00:00：静态分析与CPU最小复现完成，未加载模型、未启动GPU、未修改冻结数据及生产评分代码。确认奖励提取会读取提示示例，但D32无Beijing目标；确认D32印度总统题标准答案错误；确认嵌套答案标签提取异常。160次抽题159题，68个有对有错组，平均每步3.4题。学习率预热20周期覆盖全部训练，第1周期学习率0；此前20次真实参数更新表述更正为20周期优化器未跳过、19周期学习率非零。9题完整日志不足以定位净丢分4题，下降原因未最终确认。原D32复跑与D128扩大评价暂不执行，下一步优先奖励提取修复方案和CPU测试。详情 validation/static-decline-audit-20261001.md。


2026-10-01T13:57:38.977575+00:00：正式准备代码已接入显式response_only_v1、逐题评价记录及恢复指纹。准备脚本末尾记录哈希时使用了错误根路径，首次退出1；代码修改和备份完整，已修正记录步骤，未重放修改。CPU测试待执行，GPU未启动。


2026-10-01T13:59:39.410620+00:00：16项新奖励CPU测试通过；新增已有生成诊断计数汇总和独立评价编号，不新增模型计算。进一步回归和配置预检待完成。


2026-10-01T14:13:23.342068+00:00：正式准备完成：新奖励response_only_v1、逐题完整评价记录、恢复来源版本隔离及已有生成诊断汇总已接入；默认legacy兼容。42项CPU测试通过，配置/数据隔离/来源/源码快照/编译/差异检查通过。控制台tqdm训练进度条和每分钟台账同步已准备，无GPU启动。首段100步、P10000池、800次抽题、4回答、预热10步、保存20步/评价50步；时间估算11至13小时、上限14小时，未遍历全池。详细依据validation/formal-preparation-20261001.md。


2026-10-01T14:17:41.805798+00:00：用户授权启动正式首段100步；源码259文件及P/D32哈希通过，未发现已有训练。控制器PID1119753、子进程PID1119774存活，Ray main_task已输出实际配置。已完成训练0/100步、完整检查点0；处于初始化，初始开发评价和实际GPU更新尚未完成。控制台进度条0%，动态日志/mnt/public/code/lyk/lzy/runs/metax-formal-preparation-20261001/controller-console.log，纯训练日志/mnt/public/code/lyk/lzy/runs/metax-formal-stage1-20261001-v2/console.log。检索PID155243保留。本地临时目录为空，清理0个。


2026-10-02T03:57:59.127473+00:00：静态GRPO原因分析a2完成、CPU退出0、GPU0。800组K0至K4=382/115/100/125/78，57.5%全同组正确性优势为0但KL/熵仍更新。原函数复现：low_var_kl在差值3/10时截10且梯度0；FP32差值100时损失10而梯度NaN；被屏蔽位置仍可污染梯度；全零优势PPO遇指数溢出也NaN。rank0缩放512/64/64/64/16与6次跳过吻合。实现风险已确认，缺真实逐token差值不能直接认定6次异常根因。增加8条可改善混合概率，但固定轨迹预算减少问题覆盖，当前难度模块固定4条需接口/标签版本变更。优先数值修复CPU测试再决定下一段，未改生产代码或启动实验。详细validation/grpo-static-causes-20261002.md。


2026-10-02T04:18:54.984862+00:00：梯度异常静态原因核查完成，CPU退出0，GPU0，生产代码未改。第一次异常发生第12步，早于末段漂移；FP32损失经过FP16反传，在scale1024的CPU样例产生Inf，64/16有限，证明半精度反传放大路径可发生。此前原损失指数/屏蔽数值风险仍成立，但真实逐token差值未保存，6次根因未定位。新发现KL日志在微批循环内覆盖，只记录每卡末微批，因此此前KL均值仅为日志子集，不能视为整周期全部轨迹的KL均值。后续优先数值边界与完整异常记录CPU修复，再调整轨迹数量；不启动新实验。详细validation/gradient-causes-20261002.md。


2026-10-02T04:40:16.867492+00:00：用户授权每题8轨迹+动态筛选。新增dynamic_filter.py与loss_safety.py；controller/configuration/训练器接入在线补抽，目标8有效问题、上限8候选批，不足停止；候选消费与训练步数分离恢复。safe_v1显式开启安全损失，KL指数段切线延续保留约束梯度，PPO极端概率比有限化，先选择有效token。KL日志改为保留全部微批，记录scaler。默认关闭兼容旧四轨迹；G8仅在线动态训练、拒绝旧标签刷新。编译通过，CPU集成验证进行中，GPU未启动。


## 八轨迹动态筛选准备 2026-10-02T04:54:25.527797+00:00

- 用户授权G8+动态筛选，P10000/D32保持冻结，T不使用。新训练从Qwen2.5-7B Base初始权重开始，reference固定初始权重；与旧四轨迹末轮不直接续接。
- 100训练周期，每周期8道新的有效问题，每题8轨迹，保留64轨迹；总目标800不同有效问题、6400保留轨迹。候选每批8问题，最多8候选批，凑不齐停止，不以不足批次更新。全对/全错只丢弃本次生成组，不从原题池永久删除；动态筛选改变训练题目分布，不能据此声称总体正确率提高。
- 实现分工：dynamic_filter负责补抽、整组筛选、跨批补齐、成本统计；controller负责种子、候选游标、跨周期题目去重、状态恢复；trainer仅适配批次；loss_safety负责显式safe_v1数值计算，dp_actor调用。关闭功能保持四轨迹兼容。旧四轨迹标签和刷新拒绝与G8在线训练混用。
- 训练mini/micro=32/8，全局64轨迹仍为2次小批更新，微批保持每卡1条；lr=1e-6/warmup10，scaler初始16，FP16计算/FP32主权重，优化器CPU卸载，reference CPU卸载，vLLM预算0.32，8×C500。上下文4096、单轮生成256、观察2048、最多10轮，原检索服务保持。
- safe_v1先选有效token再计算；PPO对数概率比截至±5；KL在差值2.5以上改切线延续，保持非零约束梯度，防止指数溢出。极端区域公式发生变化，已显式版本化。实际FP16反传仍待GPU验证；记录每周期scaler和全部微批KL。记录的微批差值最大值由现有日志汇总器求平均，不能当作全局最大值。
- 58项CPU测试通过：difficulty_core17、generation_budget8、reward_boundary17、actor_scaler3、新增动态/安全损失13。新测试包含真实DataLoader/controller/展开接口、模拟生成和worker，验证补抽、分组、去重、长度补齐、状态恢复及损失正常区兼容/极端区有限性。GPU完整联调尚未通过。
- 新控制器计划每分钟记录进度，实时进度条；所有历史周期中出现非有限梯度或optimizer_step不等于1立即停本训练进程组。保存每20步、D32评估每50步及初始/结束。D32已知一题标注错误保留，分析时同时报告剔除该题的31题结果。48小时是停止上限，耗时尚未实测；候选抽满停止或数值异常均保留记录，不自动重启。
- 产物：/mnt/public/code/lyk/lzy/runs/metax-dynamic-preparation-20261002；运行目标：/mnt/public/code/lyk/lzy/runs/metax-dynamic-g8-20261002-v1。配置/快照/冻结数据哈希核对进行中；GPU尚未启动。恢复保存候选游标与已训练题目ID，CPU通过，GPU恢复未验证。
- 注释检查范围：模块职责、混合组判断、补抽上限、跨批padding、成本统计、随机流、跨步去重、恢复边界、旧模式兼容、有效token筛选、指数边界、异常路径，关键逻辑均有中文说明。


## 按功能整理提交 2026-10-02T05:14:49+00:00

本次仅整理现有未提交改动，工作区代码哈希保持不变，未重启训练或启动GPU实验。
提交分为MetaX运行环境及FP16稳定性、检索与本地数据准备、生成长度控制、奖励边界与逐题评价、八轨迹动态筛选及恢复状态五批。新增Markdown不提交，仅纳入原有文档更新。
本次CPU复验60项通过：difficulty_core17、generation_budget8、reward_boundary17、actor_scaler_step3、dynamic_filter13、metax_sync_cache2；命令均为CUDA_VISIBLE_DEVICES= bash env/metax/run.sh -m unittest discover -s tests -p test_<名称>.py。Shell语法与git diff --check通过。各中间提交未分别重跑测试，GPU运行结果沿用既有记录，本次不新增GPU验证结论。
首次直接调用env/metax/run.sh因缺少可执行权限失败，改用bash调用；首个连续测试SSH会话在输出25项通过后无后续结果，已停止该会话，后四组独立复验通过。


## 动态G8显存失败与修复 2026-10-02T05:36:10.232175+00:00
- v1退出1、0/100更新、无检查点。初始开发评价完成后，第1周期3批候选24问题/192轨迹，已保留8混合题64轨迹；失败在reference compute_ref_log_prob -> token_statistics -> entropy_from_logits，额外分配2.23GiB，剩余显存约0.3至0.7GiB。显存48GiB左右为PyTorch已分配，加预留及其他占用耗尽64GiB。
- 推理概率路径原来计算未使用熵，参考模型也未开启response_logits_only；跨候选批统一长度扩大词表中间量峰值。逐token分块256并省去推理熵；reference启用回答范围logits，actor训练仍计算所需熵；轨迹数、有效问题数不减少。
- 生产改动集中dp_actor.token_statistics及其调用，默认chunk_size=0保留旧行为；修改前备份runs/metax-dynamic-memory-fix-20261002/dp_actor.before.py。CPU原公式/分块值及梯度、重算、跳过熵与块宽验证进行中；GPU尚未重启。
- 首次独立CPU测试抽取函数未提供FlashAttention可用性变量，测试脚本退出1，生产修改已保留；补齐CPU参考分支后复验。此项是测试环境错误，尚不能宣称修复验证通过。
- git当前HEAD b00d68c，另一任务已整理提交，未回退其修改；新修复暂未提交。v1原日志与状态保留，不自动续接无检查点的失败运行。


2026-10-02T05:37:26.438780+00:00：CPU显存修复核对退出0：完整/分块概率和熵输出一致，完整/分块梯度一致，checkpoint重算一致，推理省略熵仍得到相同概率；17token按4分块的实际熵调用最大块宽4，关闭熵后调用0。GPU显存尚未验证。记录runs/metax-dynamic-memory-fix-20261002/tests.log，配置v2准备进行中。


2026-10-02T05:39:17.191367+00:00：修复版本v2开始启动，控制器PID 1339606；实际0/100，checkpoint0。v1失败记录保留。当前数值/3项scaler CPU验证通过，GPU验证待完成；块256、参考回答logits开关已核对，正式配置数据源码预检通过。


## 答案元数据维度修复 2026-10-02T08:20:17.789341+00:00

- 已实现：`verl/utils/dataset/rl_dataset.py::collate_fn` 将每题非张量元数据保存为一维对象数组，避免等长列表自动升维。复用共用入口，兼容普通训练与动态筛选，不改变答案内容、张量堆叠、评分或采样规则。
- 新增 `tests/test_rl_dataset_collate.py`，覆盖固定/不同答案数量、Parquet数组对象保留、标量/字典/对话/张量兼容性以及跨候选批实际合并。
- 修复前4项测试复现失败，合并路径出现同一ValueError；修复后的测试正在运行。GPU重跑未启动；v3停在1/100步，无完整检查点。


### 答案维度修复验证完成 2026-10-02T08:24:32.986587+00:00

- CPU回归51项全部通过：新增整理/跨批合并4项、动态筛选与安全损失13项、实验核心17项、奖励边界17项。修复前新增测试复现同一数组拼接ValueError，修复后通过。
- 验证命令：`CUDA_VISIBLE_DEVICES= bash env/metax/run.sh /mnt/public/code/lyk/lzy/runs/metax-collate-fix-20261002/run_cpu_tests.py`；证据：`runs/metax-collate-fix-20261002/tests.log`、`verification.json`、修改源码快照与差异。`git diff --check`通过。
- 共用入口保持张量堆叠、标量和字典值兼容；列表/数组/对话统一按题保存。未改模型生成、奖励、题池、采样规则或无限时启动器。
- v3仍为失败状态：完成1/100步、无完整检查点；本次没有启动GPU训练。下次启动须重新冻结源码哈希，使用新运行目录从初始权重开始。GPU完整联调未验证。


2026-10-02T08:31:28.807594+00:00：用户要求重启，v4已从初始权重启动；控制器PID1365003，实测0/100步，checkpoint0。修复后51项CPU测试通过，本次源码/冻结数据哈希预检通过，无总时间上限；GPU完整联调待验证。运行记录：[v4](runs/metax-dynamic-g8-20261002-v4.md)，快照SHA256：ed2eafa53d86cd71b553fb04056df4a335033e24e762e9d21c450f483a802b5f。


## 2026-10-03T19:03:09+08:00 提交前CPU复验与开发基准整理

- 负责人Codex；按用户要求整理现有未提交修复。实现集中于`rl_dataset.py::collate_fn`和`dp_actor.py::token_statistics`及其调用；新增`tests/test_rl_dataset_collate.py`。前者保持每题元数据为一维对象数组，后者沿回答token分块并在概率推理时跳过未使用熵。默认分块0保持旧计算路径；无新增实验开关或训练参数改动。
- 本轮CPU复验51项通过：整理/跨批合并4、动态筛选13、实验核心17、奖励边界17。命令：`CUDA_VISIBLE_DEVICES= bash env/metax/run.sh /mnt/public/code/lyk/lzy/runs/metax-collate-fix-20261002/run_cpu_tests.py`，退出码0。
- 独立生产函数CPU核对通过：完整/分块概率、熵和梯度一致，checkpoint重算一致，跳过熵后概率一致；17token按4分块最大块宽4，关闭熵无熵调用。命令：`CUDA_VISIBLE_DEVICES= bash env/metax/run.sh /mnt/public/code/lyk/lzy/runs/metax-dynamic-memory-fix-20261002/test_token_statistics.py`，退出码0。
- 三个代码/测试文件SHA256与v4冻结源码一致。当前职责、默认兼容性和关键中文注释已检查；未接入SFT。本轮没有运行GPU验证，完整GPU恢复和SFT链路仍未验收；正在运行的v4代码、配置及进程保持原状。
- 验证证据补充保存至`/mnt/public/code/lyk/lzy/runs/metax-collate-fix-20261002/commit-validation-20261003.json`。提交前执行`git diff --check`；下步整理运行记录/验证产物的忽略规则，保留核心方案与交接文档。


## 2026-10-03T19:04:45+08:00 文档版本管理整理

- 负责人Codex；代码修复已提交为`93a6f348de8ecfebeeee7ba476dba68611bc0305`，可作为SFT增量开发的已提交代码基准。51项CPU回归及独立token分块数值/梯度验证本轮通过；未新增GPU实验或SFT实现。
- `.gitignore`由整目录忽略收窄为单次运行记录和验证产物；核心方案、步骤、就绪/实现/进度台账、AGENTS、SFT设计/范围评估、MetaX说明及运行记录README/TEMPLATE继续版本管理。
- 18个已跟踪运行/验证产物从索引移除，其中17份旧运行Markdown在本轮操作前已经不存在；现存文件仅停止跟踪，逐文件哈希确认内容保留。当前v4记录及验证报告保持原路径、仅在本地留存。没有删除本轮任何运行产物。
- `git check-ignore --no-index`已分别验证核心文档可跟踪、v4记录与验证报告被忽略。`git diff --check`和暂存差异检查作为提交验收；下一步可基于整理后的分支HEAD建立独立SFT开发分支，尚未执行。
- v4控制器仍会自动更新进度台账中的状态块；提交代表当时的文档快照，后续自动更新产生的台账差异不属于未提交代码。


## 2026-10-03T19:44:19+08:00 中文注释控制规则更新

- 负责人Codex；按用户要求更新仓库`AGENTS.md`及`docs/experiments/AGENTS.md`。所有新增代码添加中文注释；新增或修改函数必须使用`@brief`、逐参数`@param`、`@return`及适用的`@raises`/`@note`，关键逻辑必须就近解释。
- 覆盖率沿用逻辑单元口径，由至少40%提高为至少50%；公式、范围、有效说明定义及检查清单已明确。函数和关键逻辑完整标注为独立强制项，不能用总体比例代替。历史40%审查保留为当时记录，不改写为本次验收。
- 本轮仅修改控制文档并同步实现记录/进度台账，未补齐历史源码注释，未修改训练代码、配置或进程。代码覆盖率不适用，未运行CPU/GPU测试；验收为控制条款一致性与`git diff --check`。下一次代码变更按新规则登记覆盖清单后提交。


## 2026-10-03T20:26:17+08:00 SFT冷启动代码实施计划（未实施）

- 负责人Codex；本轮完成SFT入口、batch换算、mask移位、FP16/scaler、逐轮生成/检索接口及保存/恢复的静态核查。技术计划见[sft_cold_start_implementation_plan.md](sft_cold_start_implementation_plan.md)，代码基准为`7a9789a306aa4231665cbed3ad0d03457839d1c1`；未创建SFT开发分支。
- 拟定职责：独立cold_start模块负责数据manifest/轨迹转换/报告；通用SFTDataset、sampler、loss及checkpoint工具负责数据/梯度/状态；旧SFT trainer只保留适配。生成器通过默认关闭的trace sink记录真实输入和检索，RL入口沿用现有实现。
- 关键约定：labels按目标token位置定义并使用[1:]移位；每题全部目标token均值后按题平均；跨卡汇总真实样本分母，微批分子累加；global batch32/micro8在8卡对应每卡4/1。尾批零权重占位，真实样本不丢不复制；后缀logits按实际context/右padding位置对齐。
- 精度方案：FP32主权重、FP16计算、FP32通信/缓冲、ShardedGradScaler初值16；优化器状态卸载单独验收，梯度累积初版关闭FSDP原生CPU参数卸载。保存完整训练状态与HF导出，C3加载HF权重并新建全部RL状态/reference。
- 实施顺序A–F及CPU/GPU/导出/恢复/单条检索EM验收详见技术计划。细化范围估算22–27个代码/配置/测试文件、2600–4300行，文档另计；此前14–20文件估算为粗估，本版增加追踪、尾批、恢复和统一评价细节。
- 当前仅更新计划及相关文档，没有修改训练源码/配置、制作演示、运行新CPU/GPU测试或启动实验；注释覆盖率不适用。现有v4不在本次操作范围。PyTorch2.6官方FSDP与AMP文档已核对；首次只读SSH审批超时，重试成功，未造成代码变更。
- 下一步先实施A的数据/损失/sampler及CPU验收，再接入B追踪采集、C训练、D恢复导出、E接续评价、F256题先导；全部新增/修改函数与关键逻辑按中文标签和逻辑单元≥50%规则检查。方案数值为计划，不构成SFT能力或实验收益的验收结论。


## 2026-10-05T04:18:48.636571+00:00 检查点曲线独立入口

新增verl/experimental/checkpoint_eval下core/runtime/controller及scripts/difficulty/checkpoint_curve.py、tests/test_checkpoint_eval.py；未修改训练器、生成器或奖励实现。core负责选题/诊断/配对统计，runtime复用原生成/检索/奖励，controller负责资产/状态/子进程与文档同步，CLI仅参数适配。8项CPU边界验收、语法和diff检查通过；真实GPU尚未测。函数与控制逻辑清单见/mnt/public/code/lyk/lzy/runs/metax-checkpoint-curve-d256-20261005-v1/cpu-verification.json：32+89=121项，中文覆盖121/121；所有函数接口标签通过。最后补注释AST相同；GPU效果、完整训练恢复和真实finish_reason未验证。


## 2026-10-05T04:35:23.192396+00:00 阶段A重复性修复

v1 Base D32两轮同15/32但文本/检索轨迹不一致，D256未启动，已停止并保留证据。v2冻结同一256题/15题风险清单；独立ObservedRollout每轮调用原生公开缓存清空接口，控制器Base完成立即验收。新增2项缓存调用顺序/失败停止测试，10项CPU验收、语法和diff检查通过；中文接口34项、逻辑覆盖123/126，见/mnt/public/code/lyk/lzy/runs/metax-checkpoint-curve-d256-20261005-v2/cpu-verification.json。训练/奖励共享实现未改，未启动RL/SFT；GPU重复一致性待实测。详见runs/metax-checkpoint-curve-d256-20261005-v2.md。


## 2026-10-05T04:48:48.121904+00:00 有限评价后处理

负责人Codex /root；启动单次结果后处理PID1620336，不重启失败任务或执行训练。六模型完整D256且重复门槛通过才输出diagnostic.json并追加原最终评估报告第6节及本run记录。区分首次数值下降与两组负配对区间；输出所有相邻节点、全部对→错题ID及过程特征，开发峰值为事后探索、未多重比较校正，不断言因果。代码产物/mnt/public/code/lyk/lzy/runs/metax-checkpoint-curve-d256-20261005-v2/finish_report.py，SHA256 3e6c6446423fc22f0a0ad56f56ff797204b0e238ffe76ed0adbe170492af047b；语法检查通过，真实结果尚未生成。单一main函数中文接口完备；各结果校验、等待/失败分支、统计和写入逻辑均就近中文说明。此前冻结的评价源码/题集不改。


## 2026-10-05T04:54:15.707640+00:00 后处理边界验收通过

负责人Codex /root。独立临时合成结果CPU验收退出0：失败不写完整报告、同题下降区间、全部32道合成转错索引、峰值及防重复覆盖；没有把合成指标当作真实GPU结果。证据/mnt/public/code/lyk/lzy/runs/metax-checkpoint-curve-d256-20261005-v2/report-boundary-verification.json，代码函数中文接口2项、逻辑说明覆盖16/22=72.73%，清单/源码哈希已保存。关键等待、数据校验、下降判定、逐题索引及历史写入逻辑有中文说明；只读模型仍在复评，未启动训练。


## HF离线复评异常，暂停D256

step100第一轮D32实测0/32，32题均无答案，57次真实搜索，78290生成token，32次强制结束，349次长度命中；总585.34秒（生成510.04、检索73.53）。与训练内15/32不符，不作为真实退化结论。第二轮首批输出一致，但未等全轮，控制器SIGINT仅停止所属任务；D256仍0/1536，后处理和本机同步按失败处理。已冻结异常前后两题实际输入到loading-probe/inputs.json，有限单卡探针比较冷HF加载batch2/batch1、Base初始化后原训练RPC加载以及保留/清空前缀缓存。只读权重/已保存输入，未启动训练，未改原HF配置或共享加载器；探针目前未验收。源码probe.py语法通过，接口与关键加载/重置/记录逻辑有中文说明。负责人Codex /root。


### 5.2 新发现：训练权重更新后前缀缓存未失效（2026-10-05T05:13:28.316548+00:00）

D256在开始前暂停，step100冷缓存D32实际0/32且32题无答案，与训练内15/32不符。有限探针已确认：Base引擎先生成固定上下文、通过原MetaxWeightUpdateExtension公开RPC加载step100全部7份HF分片，同一权重与相同输入保留旧KV时产出正常答案/搜索，公开reset_prefix_cache后转为calling重复且命中长度上限；直接HF冷加载（batch2和batch1）也出现重复。英国国籍上下文保留旧KV输出<answer> English </answer>并停止，清空后重复calling至256token。证据/mnt/public/code/lyk/lzy/runs/metax-checkpoint-curve-d256-20261005-v2/loading-probe/cache-update-finding.json、rpc-retained-prefix.json、rpc-cleared-prefix.json、rpc-load.json及cold-*.json。

静态代码核对：worker.load_weights_from_safetensors仅model.load_weights，LLM.sync_model_weights未调用reset_prefix_cache；权重dirty标记会触发重新导出，但不清前缀KV。因此历史D32应视为可能混入旧权重KV的指标，不能用15→18→15直接推断真实参数退化起点。尚未完整重放历史，不能量化各次污染，也不能据2题断言全部训练无效或reward hacking因果。先用冷缓存评价实际保存权重定位首次下降/循环区间，原训练已结束且未改源码或重启；后续训练须另验收权重更新后的缓存失效。没有把0/32当作HF文件损坏证明，完整COMPLETE哈希仍一致。


## 2026-10-05T05:14:38.754797+00:00 机制核查后按冻结协议继续

已证明相同HF权重通过原训练RPC加载、清空前缀后也重复，不能将0/32简单归因于HF导出文件损坏。历史带旧KV分数不作复评正确率门槛；继续v2相同冻结代码/数据/权重/每轮清缓存协议，从已完成批次接续step100第二轮。先验收冷缓存重复，再执行D256六模型曲线。旧中断状态/进程/报告状态保存为*-before-resume-1.json，日志追加；没有修改模型或训练源码，后处理同时恢复。负责人Codex /root。


## 2026-10-05T05:17:51.150767+00:00 已保存节点小探针

GPU1实测无进程（859MiB为设备基础占用），顺序运行Base/20/40/60/80/100的同2个初始输入及同2个搜索后输入、batch1/每次空缓存；各节点独立进程，物理GPU1一致。仅比较原始生成循环症状，不计算完整题EM，不混入GPU0的D256曲线。产物loading-probe/curve-probe，各阶段退出码/实际状态独立保存；源代码及驱动哈希已保存，语法通过，GPU全节点未验收。新增/修改函数接口及关键循环/失败/文件锁有中文说明。负责人Codex /root。


### 5.3 保存节点小探针结果（2026-10-05T05:26:24.412226+00:00）

Base/20/40/60/80/100六节点全部退出0；同一GPU1、batch1、每次空前缀缓存、同2个初始及2个真实搜索后上下文（共24次单条原始生成）。该冰雨上下文step60输出<answer>Freezing rain</answer>并停止；step80在相同输入下输出连续<search>标签至256token，最大同token三元组重复70次；step100转为calla lilies重复，国籍上下文calling重复248次。严重循环的这个样本在保存节点上首次见于step80，能定位到60→80区间；step40已有部分长输出命中256上限，但这不等同严重循环。另一国籍上下文step80仍能给出English，症状并非所有题同时出现。

这是固定上下文机制探针，不是完整检索单轨迹EM；不能将60–80称作整体准确率退化的确定起点或step60最优。完整GPU0 D32重复门槛已通过：Base两轮15/32、step100两轮0/32且全部输出/奖励逐题一致，六模型D256已开始。实际总体/来源/256及241题配对曲线完成后由有限后处理自动追加第6节，当前还未完成。证据/mnt/public/code/lyk/lzy/runs/metax-checkpoint-curve-d256-20261005-v2/loading-probe/curve-probe-summary.json、各节点cold-*.json及/mnt/public/code/lyk/lzy/runs/metax-checkpoint-curve-d256-20261005-v2/repeat-check.json。未修训练源码或启动RL/SFT；训练内旧分数受已确认的权重更新后KV残留缺陷影响，需要先以冷缓存曲线为准。

小探针中文接口3项，逻辑说明覆盖14/19=73.68%，完整清单curve-source-verification.json；真实6节点退出均0，不称完整EM验证。


## 2026-10-05 MetaX 权重更新后的前缀缓存失效修复（验证待执行）

用户明确授权修复。源码范围：verl/third_party/vllm/metax_v_0_11_0/llm.py；新增 tests/test_metax_weight_cache_invalidation.py。
完整权重加载并唤醒 KV 后调用公开 reset_prefix_cache；兼容当前 V1 正常返回 None 和布尔 True，其他返回或异常停止。同步前拒绝未完成请求，生成资格只有完整同步和缓存失效完成后恢复，失败后不能继续生成。同权重多轮生成保留缓存；worker、训练损失、奖励和已完成权重均未修改。
补丁/原始文件证据 runs/metax-prefix-cache-fix-20261005-v1。CPU 回归、语法/diff 验收和真实 GPU 热更新/冷加载对照尚未执行，下一步按阶段单独记录。
现有 GPU0 D256 评价保持运行；本修复不重启它、不改其冻结协议。CPU 模拟不能代替 GPU 验收。


## 2026-10-05 前缀缓存修复 CPU 验收

真实适配器与既有 manager 共10项 CPU 回归通过（新8项+既有2项）；命令 CUDA_VISIBLE_DEVICES= bash env/metax/run.sh -m unittest discover -s tests -p test_metax*.py -v。覆盖旧前缀失效、加载/唤醒/重置顺序、V1 None/True兼容、失败拒绝生成、活动请求拒绝更新、成功重试、同权重缓存及原补齐语义。修改源码/新测试/探针语法与 git diff --check 通过。证据 runs/metax-prefix-cache-fix-20261005-v1/cpu-verification.json；GPU固定输入对照仍待执行，未运行训练、未停止现有评价。


## 2026-10-05 MetaX 前缀缓存修复验收完成

用户授权的权重更新缓存缺陷已修复。10项CPU回归通过，隔离原源码的同一旧缓存回归按预期失败；语法和git diff --check通过。真实GPU1以Base暖缓存后经修复的生产适配器完整同步step100，同4个固定输入与同GPU独立冷加载输出全部逐token一致；同步日志确认Successfully reset prefix cache，失败日志未见。所有输出仍命中256长度上限，这反映step100在此协议下已有行为异常，修复不恢复模型能力。GPU0既有D256曲线继续运行，未启动新RL/SFT。

验证产物 runs/metax-prefix-cache-fix-20261005-v1/verification.json、sync-result.json、cold-result.json、cpu-verification.json、regression-before.log、fix.patch。CPU补充说明仅改注释，AST相同；没有重复训练或改写原指标。真实休眠GPU路径与多卡FSDP新训练未运行，休眠顺序由CPU覆盖。

中文说明验收：19个新增/修改函数的@brief/@param/@return全部通过，关键逻辑说明逐项检查；逻辑单元44/44=100%，清单见comment-verification.json。
- 函数职责 __init__：有中文说明。
- 函数职责 sync_model_weights：有中文说明。
- 函数职责 generate：有中文说明。
- 函数职责 setUp：有中文说明。
- 函数职责 configure_output：有中文说明。
- 函数职责 assert_generation_blocked：有中文说明。
- 函数职责 test_new_weights_invalidate_old_prefix_before_generation：有中文说明。
- 函数职责 test_reset_after_load_accepts_v1_none_and_boolean_success：有中文说明。
- 函数职责 test_sleep_wakes_kv_before_reset：有中文说明。
- 函数职责 test_reset_failure_or_exception_blocks_generation：有中文说明。
- 函数职责 test_load_failure_never_marks_cache_ready：有中文说明。
- 函数职责 test_active_requests_reject_update_before_any_weight_mutation：有中文说明。
- 函数职责 test_successful_retry_restores_generation：有中文说明。
- 函数职责 test_same_weight_generation_preserves_cache_and_padding_semantics：有中文说明。
- 函数职责 load_weights：有中文说明。
- 函数职责 reset_prefix：有中文说明。
- 函数职责 generate_native：有中文说明。
- 函数职责 generate_adapter：有中文说明。
- 函数职责 main：有中文说明。
- 冷加载的权重和缓存一致：有中文说明。
- 先关闭生成资格：有中文说明。
- 临时目录只在同步期间存在：有中文说明。
- 只导出训练张量：有中文说明。
- 加载失败时保留不可生成状态：有中文说明。
- 完整加载并唤醒 KV 后只重置一次：有中文说明。
- V1 同步接口正常返回 None：有中文说明。
- 同步中断或缓存失败后拒绝：有中文说明。
- 按原请求/候选顺序展开输出：有中文说明。
- 仅在真实 token 区域填值：有中文说明。
- 仅替换导入边界：有中文说明。
- 只更新权重，不清除旧 prefix：有中文说明。
- 缺陷版仍保留 prefix=1：有中文说明。
- 当前 V1 返回 None：有中文说明。
- 逐个覆盖正常失败返回：有中文说明。
- 空加载、零参数加载和中断：有中文说明。
- 活动请求持有的旧块：有中文说明。
- 新的一次完整成功同步：有中文说明。
- 两次同权重生成不重复清空缓存：有中文说明。
- 每轮单请求：有中文说明。
- 单条请求没有右侧 padding：有中文说明。
- 使用真实训练适配器从 Base 初始化：有中文说明。
- 交给修复后的完整同步方法：有中文说明。
- 同设备和相同精度/长度配置：有中文说明。
- 仅运行有限输入探针：有中文说明。


## 2026-10-05 sft-mx 分支创建前的已有改动验收

用户要求先提交未提交改动，再以 data-difficulty-muxi（经用户确认的实际分支名）创建 sft-mx。已有修改包含检查点评价、KV 缓存失效修复及历史实验文档，本节未新增训练算法。
实际命令：`bash env/metax/run.sh -m unittest tests.test_checkpoint_eval tests.test_metax_weight_cache_invalidation tests.test_metax_sync_cache -v`，20 项 CPU 测试全部通过（2026-10-05 14:52 +08:00），修改的 Python 文件 AST 解析通过；提交前执行 git diff --check。系统 Python 与 searchr1-metax 环境未安装 pytest，首次入口检查未运行测试，随后使用项目既有 unittest/MetaX 入口完成验收，未安装新依赖。
本轮没有 GPU 训练/新增 GPU 验证。此前 KV 修复 GPU 验收与检查点曲线结果保持各自记录；本次 CPU 通过不代替它们。代码注释清单沿用本次待提交代码对应的既有检查记录，此处只新增文档，新增代码覆盖不适用。


## 2026-10-05 sft-mx 数据方案登记（2026-10-05T15:02:50.261273+08:00，Codex）

用户已确认实际基础分支 data-difficulty-muxi。创建前将全部当时未提交改动提交为 28da7731b9f4b37bc5fa7007acfbac9101748876（16 文件；包括检查点评价与 KV 缓存修复）。20 项既有 CPU 测试、AST 与 diff 检查通过；本节新增范围仅为文档，未新增代码测试，注释覆盖不适用。沿用仓库近期提交身份通过单次 git -c 提交，没有改全局配置、推送或启动训练。

新分支 sft-mx 位于 /mnt/public/code/lyk/lzy/R1-sft-mx；原 R1-vllm-metax 工作区保留既有评价进程，其后续自动进度更新与本分支分离。详细设计见 [sft-mx 训练数据设计](sft_mx_data_design.md)。完成的是设计与只读来源审计，尚未采集/发布 SFT 演示、修复 SFT 入口或训练。

原始 train/test 哈希匹配既有 manifest。169615 行原训练数据在排除 P/D/T 问题哈希、所有官方 test 问题并全局规范化去重后剩 158551 道（NQ 73982 / HotpotQA 84569），尚未做 tokenizer 长度及近重复复核。审计只读官方 test 的 question 列，未读 T.parquet 或测试答案，未用 GPU。

数据执行顺序：先冻结来源/长度分层的候选与独立 S_val，再补可选真实逐轮 trace 和边界验收，执行 64 题教师探针（30/34，每题最多8次），合格 S256（120/136）与 S1000（467/533）嵌套。S_val 目标128题（60/68），只作预测损失诊断；主开发指标仍为同协议完整检索 EM。候选预算、行为覆盖、证据审核、逐轮 Parquet、按题 token 平均损失、发布/恢复约束和验收均见设计。数量为计划，合格率/样本行数/收益待实测。

当前结论以冷缓存评价为准；历史 v4 的训练内 D32 已确认存在旧 KV 影响，不能直接用作新 C2。同一修复协议下重建 C2/C3，旧曲线保留历史。旧训练 actor KL 已开启（0.001），首轮保持 RL 研究参数；过程奖励如变更须统一版本，不能把缓存或奖励修复归因于 SFT。25周期先导仅判断早期方向，后期稳定性另覆盖60/80/100节点。

下一步及验收：实现候选准备与真实调用追踪，验证隔离、模型/工具来源、后处理目标、观察裁剪、首末 token 与未来信息边界；64题探针全部拟保留轨迹人工复核。现有 SFTDataset/精度/导出恢复未实现，须按技术计划独立验收后启动 S256。


## 2026-10-05 SFT全流程规划更新（2026-10-05T20:08:44.549149+08:00，Codex）

用户要求规划数据准备、关键训练修改到启动的全部流程。最新版见 [sft-mx执行计划](sft_mx_execution_plan.md)，数据设计同步更新为强教师优先、Base为对照。此前Base自生成主方案保留为历史设计，当前以最新版为准；教师具体型号、接口与采样版本须先经64题质量/成本探针冻结。强教师与学生tokenizer分离，输出经学生后处理与协议重放生成学生context/target，不能直接复制教师token或私有提示。

本轮只读静态核对当前HEAD7229965和安装环境，工作区检查时干净。确认SFTDataset缺失、PEFT未安装、BF16/FlashAttention写死、全局batch原地修改、旧mask边界/归一化待修、尾批丢弃、仅HF保存及无完整恢复；torch2.6.0+metax3.3.0.2、transformers4.57.1、tensordict0.6.2。安装版Qwen前向参数为logits_to_keep，旧num_logits_to_keep描述已纠正。没有导入/启动训练模型，未运行新CPU/GPU测试，代码注释覆盖不适用。此前20项回归只适用于已提交KV/检查点评价代码。

执行顺序A配置/题集→B教师桥接与trace→C64题探针/审核→D逐轮数据发布→E训练代码→FCPU/小模型GPU/7B实际短跑/保存恢复验收→GS256一轮启动及D256评价；之后S1000从Base独立一轮，再新C2/C3 RL。拟先导4卡global32/每卡micro1/累积8，或冻结8卡/累积4并重验对应拓扑；GPU按启动时实际空闲分配，保留既有服务与任务。SFT不需要在线检索。启动和CPU/GPU调用均尚未执行，拟新增CLI与脚本不能当作已有入口。

已完成为计划与文档；候选冻结、正式教师采集、SFTDataset/loss/trainer/恢复/导出、实际训练均待实现。下一步实施候选/schema与教师窄接口，按功能分批提交及边界验收；每个真实实验单独登记run_id、状态、产物与失败记录。学习率/长度/规模/时长是计划，实际展开M和合格率未知，训练步数按ceil(M/32)计算。T保持封存，既有v4指标污染问题保留历史，奖励/KL参数未改。


## 流程说明表达要求更新（2026-10-05T20:21:50.259071+08:00，Codex）

按用户明确要求更新根控制文档AGENTS.md，在“沟通与表达”中增加“流程和方案说明”：先用常用词说明全流程，再按顺序说明动作、目的和结果；禁止堆砌术语和实现细节，必要术语简单解释；技术细节后置，使用具体例子，区分已完成与计划。子目录继承根规则。本次仅修改控制文档和记录，未改训练代码、未运行代码测试或启动实验；代码注释覆盖不适用。提交前检查文档差异及git diff --check。
