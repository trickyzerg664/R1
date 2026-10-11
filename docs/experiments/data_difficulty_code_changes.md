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


## 2026-10-05T12:56:28.212687+00:00 独立CPU回溯审计脚本

新增运行产物/mnt/public/code/lyk/lzy/runs/metax-dynamic-g8-20261002-v4/retrospective-audit-20261005/audit.py，未修改共享训练、生成、奖励源码。职责集中于已有日志解析、窗口统计、同题退化特征及来源校验；复用原qa_em评分，冻结源码快照与当前评分函数哈希一致。原输入以符号链接引用，未复制大日志到远程、不读取T。
实际执行python3 /mnt/public/code/lyk/lzy/runs/metax-dynamic-g8-20261002-v4/retrospective-audit-20261005/audit.py；退出0，3项解析边界检查通过，100步唯一连续指标、256同题结果、有限指标与来源哈希检查通过，本机/mx windows、261条样本计数、98题配对与早期获奖样本一致。未跑GPU、未启动RL/SFT，没有把历史10项CPU/4条GPU结果当本脚本验收。
6个函数clean_console、parse_debug、protocol_features、summarize_window、boundary_checks、main均具备中文@brief/逐参数@param/@return与适用约束说明。逻辑单元清单/接口与关键逻辑核查在comment-verification.json：38/44=86.36%，6个未覆盖项为非关键机械处理；关键字段校验、解析拒绝、样本归属、分母限制、配对、早期题组关联与来源校验均有就近中文说明。AST解析通过；源码SHA256见verification.json。
未验证：完整历史生成概率/KV命中无法恢复；无真实新训练的因果证据。同步最终报告、原v4和检查点曲线运行记录、计划/步骤与进度；不新建Markdown报告。


## 2026-10-06 过程检查实现验收

负责人Codex /root。run_id=metax-process-checks-20261006-v1；仓库/mnt/public/code/lyk/lzy/R1-vllm-metax，分支data-difficulty-muxi（此前确认的实际难度分支）；HEAD 28da7731b9f4b37bc5fa7007acfbac9101748876。修改在远程工作区，未提交。

最终90项CPU测试全部通过，包括25项新过程检查测试。首次70项中1项失败：测试复制已生成批次后使用了未展开的旧批级统计；按真实流水线先筛选合并、再独立验证报告复制修正。中间89项和24项边界复验通过；失败及成功日志全部保留。部署编排转义错误未造成部分源码写入，随后已改为直接SSH修复。本机本轮暂存711327字节已删除。

实际命令：`CUDA_VISIBLE_DEVICES="" bash env/metax/run.sh -m unittest tests.test_process_checks tests.test_generation_budget tests.test_reward_boundary tests.test_dynamic_filter tests.test_checkpoint_eval tests.test_difficulty_core -v`。AST与git diff --check通过。未启动实际RL/SFT训练、GPU调用或新检查点评价；测试训练循环使用CPU替代worker。真实模型/检索服务联调、长期稳定性与改善正确率效果未验证；历史KV验收不代替本模块GPU验收。

验收时间2026-10-06T05:45:15.596608+00:00；注释接口64项全部通过，语义逻辑单元覆盖147/185=79.46%，关键漏项0。证据目录/mnt/public/code/lyk/lzy/runs/metax-process-checks-20261006-v1。
共用解析器只执行首个未保护的闭合非空动作；空/嵌套动作、超预算搜索、消费区域伪造information和答案后新增事件得到检查。代码和明确引用内标签受保护，未消费尾部只审计。真实轨迹/工具调用身份由程序分配，绑定轮次、查询、原返回和实际裁剪分词后的可见结果。报告和独立轨迹身份作为DataProto非张量同行字段，随补齐、筛选和重排传递。合法空检索不罚；工具服务故障及错配向上抛出，失败批次不当作模型负奖励。

推理诊断记录明确引文与已见正文匹配、文档引用、重复/近重复查询和新增可见文档。仅使用本轮生成前已见证据；事实支持、多跳成立性和数值冲突保持unknown/待复核，不直接扣分。字面重合不证明推理正确。

奖励为R=接受答案EM乘协议合法门控减beta乘无接受答案标记。EM复用qa_em规则；训练可写入新分，验证继续返回原EM。原EM、接受答案EM、协议奖励和返回奖励旁列。beta>0时完整问题组按有限实数组内方差筛选，全同分负组仍丢弃；原正确数统计及四轨迹难度标签继续使用原EM，负奖励另列。打标审计使用difficulty_score阶段。GRPO损失、KL、优化器、学习率和SFT未改。新过程版本/奖励参数进入恢复指纹，关闭保持历史指纹，审计路径不进入身份。

修改文件：

- `search_r1/llm_agent/generation.py`
- `tests/test_process_checks.py`
- `verl/experimental/difficulty/dynamic_filter.py`
- `verl/experimental/process_checks/protocol.py`
- `verl/experimental/process_checks/reasoning.py`
- `verl/experimental/process_checks/reward.py`
- `verl/experimental/process_checks/__init__.py`
- `verl/trainer/main_ppo.py`
- `verl/trainer/config/ppo_trainer.yaml`
- `verl/trainer/ppo/ray_trainer.py`
- `verl/experimental/difficulty/configuration.py`
- `verl/experimental/difficulty/controller.py`
- `verl/experimental/difficulty/generation.py`

默认功能关闭，保持既有运行行为。仅启用检查/审计时支持以下显式配置；这只是配置说明，本轮未启动运行。

```text
data.context_policy=bounded
data.observation_truncation=structured
reward_model.answer_mode=response_only_v1
process_checks.enabled=true
process_checks.reward_gate=false
process_checks.missing_answer_penalty=0.0
process_checks.audit_path=/mnt/public/code/lyk/lzy/runs/<new_run_id>/process-checks.jsonl
```

训练门控设`process_checks.reward_gate=true`；R0的beta=0，R1设`process_checks.missing_answer_penalty=0.1`。开启审计已改变动作解析，因此R0/R1必须固定相同新解析和其他条件。开启新协议后不能混用旧训练状态的恢复指纹，应从同一已确认父模型初始化独立实验。历史1536条输出缺完整工具账本，不伪造调用身份重评分。下一步先在独立run_id保存真实生成来源，检查误判及未知语义，再决定是否接入裁判或进行正式对照；不以长时间训练验收实现。

接口与逻辑覆盖按新增/修改职责检查，未改旧逻辑不计入分母。函数说明不自动覆盖内部控制逻辑；非关键机械字段组合和测试样例装配未单独注释。未按注释行数计算。完整源码位置及清单另见comment-verification.json。

接口清单：

- `search_r1/llm_agent/generation.py:LLMGenerationManager.__init__`：中文@brief、逐参数@param、@return通过。
- `search_r1/llm_agent/generation.py:LLMGenerationManager._postprocess_responses`：中文@brief、逐参数@param、@return通过。
- `search_r1/llm_agent/generation.py:LLMGenerationManager.run_llm_loop`：中文@brief、逐参数@param、@return通过。
- `search_r1/llm_agent/generation.py:LLMGenerationManager.execute_predictions`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:execute`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:execute.search`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:score`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_invalid_actions_and_empty_queries`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_literal_tags_are_not_environment_impersonation`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_terminal_answer_consumes_no_later_action`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_forged_result_correct_answer_is_gated`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_forbidden_search_never_calls_tool`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_empty_real_result_is_valid`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_active_row_binding`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_no_future_evidence`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_truncated_evidence_not_full_return`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_repeated_query_and_new_evidence_separated`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_semantics_conflict_and_hops_remain_unknown`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_infrastructure_exception_is_not_model_penalty`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_infrastructure_exception_is_not_model_penalty.fail`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_result_count_mismatch_stops_batch`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_result_count_mismatch_stops_batch.empty`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_parse_mismatch_stops_batch`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_report_tampering_and_uid_mismatch`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_event_after_answer_cannot_hide_reason`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_real_reward_gate_validation_and_shadow_em`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_real_reward_no_answer_and_disabled`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_real_generation_gpu_padding_and_metadata`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_real_generation_gpu_padding_and_metadata.Worker.generate_sequences`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_real_generation_gpu_padding_and_metadata.Manager.batch_search`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_finite_group_filter_and_constant_groups`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_finite_group_filter_and_constant_groups.group`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_configuration_fails_before_reward_changes`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_difficulty_metrics_keep_original_em`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_process_protocol_enters_resume_fingerprint`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_scoring_labels_remain_binary_with_penalty`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_scoring_labels_remain_binary_with_penalty.SearchWorker.generate_sequences`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_jsonl_audit_preserves_originals`：中文@brief、逐参数@param、@return通过。
- `tests/test_process_checks.py:score_from_report`：中文@brief、逐参数@param、@return通过。
- `verl/experimental/difficulty/dynamic_filter.py:mixed_groups`：中文@brief、逐参数@param、@return通过。
- `verl/experimental/difficulty/dynamic_filter.py:training_batches`：中文@brief、逐参数@param、@return通过。
- `verl/experimental/process_checks/protocol.py:digest`：中文@brief、逐参数@param、@return通过。
- `verl/experimental/process_checks/protocol.py:protected_text`：中文@brief、逐参数@param、@return通过。
- `verl/experimental/process_checks/protocol.py:parse_action`：中文@brief、逐参数@param、@return通过。
- `verl/experimental/process_checks/protocol.py:TraceLedger.__init__`：中文@brief、逐参数@param、@return通过。
- `verl/experimental/process_checks/protocol.py:TraceLedger.execute`：中文@brief、逐参数@param、@return通过。
- `verl/experimental/process_checks/protocol.py:TraceLedger.observe_visible`：中文@brief、逐参数@param、@return通过。
- `verl/experimental/process_checks/protocol.py:TraceLedger.reports`：中文@brief、逐参数@param、@return通过。
- `verl/experimental/process_checks/protocol.py:validate_report`：中文@brief、逐参数@param、@return通过。
- `verl/experimental/process_checks/reasoning.py:normalized`：中文@brief、逐参数@param、@return通过。
- `verl/experimental/process_checks/reasoning.py:documents`：中文@brief、逐参数@param、@return通过。
- `verl/experimental/process_checks/reasoning.py:review_reasoning`：中文@brief、逐参数@param、@return通过。
- `verl/experimental/process_checks/reasoning.py:search_diagnostic`：中文@brief、逐参数@param、@return通过。
- `verl/experimental/process_checks/reward.py:check_config`：中文@brief、逐参数@param、@return通过。
- `verl/experimental/process_checks/reward.py:process_score`：中文@brief、逐参数@param、@return通过。
- `verl/experimental/process_checks/reward.py:append_reports`：中文@brief、逐参数@param、@return通过。
- `verl/trainer/main_ppo.py:RewardManager.__init__`：中文@brief、逐参数@param、@return通过。
- `verl/trainer/main_ppo.py:RewardManager.__call__`：中文@brief、逐参数@param、@return通过。
- `verl/trainer/main_ppo.py:main_task`：中文@brief、逐参数@param、@return通过。
- `verl/trainer/ppo/ray_trainer.py:RayPPOTrainer._validate`：中文@brief、逐参数@param、@return通过。
- `verl/trainer/ppo/ray_trainer.py:RayPPOTrainer.fit`：中文@brief、逐参数@param、@return通过。
- `verl/experimental/difficulty/configuration.py:provenance`：中文@brief、逐参数@param、@return通过。
- `verl/experimental/difficulty/controller.py:DifficultyExperiment.metrics`：中文@brief、逐参数@param、@return通过。
- `verl/experimental/difficulty/generation.py:score_batch`：中文@brief、逐参数@param、@return通过。

逻辑单元完整清单：

- `protocol.py:digest`：文本哈希与来源证明边界（有说明）
- `protocol.py:protected_text`：代码块与行内代码保护（有说明）；引用行保护（有说明）；含协议标签引号保护（有说明）；等长替换保持位置（有说明）；字符列表物化（非关键未单注）
- `protocol.py:parse_action`：原始类型拒绝（有说明）；首个未保护动作定位与闭合边界（有说明）；嵌套动作拒绝（有说明）；空白动作拒绝（有说明）；未闭合或无动作反馈（有说明）；仅消费区域信息角色识别（有说明）；动作接受与来源门控分离（有说明）；初始局部变量容器（非关键未单注）
- `protocol.py:TraceLedger.__init__`：真实轨迹数量校验（有说明）；程序轨迹身份分配（有说明）
- `protocol.py:TraceLedger.execute`：整批行数及轮次校验（有说明）；活动行原始输出对应（有说明）；原始消费尾部事件保存（有说明）；解析边界不一致停止（有说明）；答案后事件拒绝（有说明）；闭合非空答案接受（有说明）；程序调用身份与请求绑定（有说明）；末轮搜索禁止及错误动作反馈（有说明）；多余原始行拒绝（有说明）；等长字符串返回与合法空结果（有说明）；基础设施故障传播与错误调用保留（有说明）；程序工具结果原文与观察绑定（有说明）；输出标记列表初始化（非关键未单注）
- `protocol.py:TraceLedger.observe_visible`：观察全批次行数一致（有说明）；当前轮成功调用附着真实可见正文（有说明）
- `protocol.py:TraceLedger.reports`：成功调用按历史顺序计算搜索诊断（有说明）；推理仅使用生成前已经可见的证据（有说明）；共用动作边界定位推理前缀（有说明）；版本无答案及客观事件重验（有说明）；协议合法性与未知语义分离（有说明）；报告深拷贝（非关键未单注）
- `protocol.py:validate_report`：版本与同行轨迹身份核对（有说明）；调用身份唯一（有说明）；答案后客观事件拒绝（有说明）；原始文字重算动作与消费（有说明）；接受动作与真实执行一致（有说明）；答案内容重建（有说明）；同轮同查询调用与末轮禁止（有说明）；接受搜索与返回账本一一对应（有说明）；轮次有序唯一（有说明）；全局答案状态一致（有说明）；原始工具结果哈希校验（有说明）；可见正文哈希与文档校验（有说明）；故障调用状态不得评分（有说明）；原因去重返回（非关键未单注）
- `reasoning.py:normalized`：空白大小写归一化不替代EM（有说明）
- `reasoning.py:documents`：文档编号绑定真实调用（有说明）；可见正文边界和内容指纹（有说明）；文档记录字段组合（非关键未单注）
- `reasoning.py:review_reasoning`：实际动作边界之外推理文字（有说明）；明确引文逐字对照已见正文（有说明）；文档编号定位实际调用候选（有说明）；有限断言待复核而非语义放行（有说明）；多跳断言未知（有说明）；数值冲突只列待复核候选（有说明）；诊断返回字段组合（非关键未单注）
- `reasoning.py:search_diagnostic`：准确重复查询记录（有说明）；近重复至少三词及交并比阈值（有说明）；可见内容指纹计算新增文档（有说明）；重复且无新证据才列冗余候选（有说明）；查询词集合物化（非关键未单注）
- `reward.py:check_config`：默认关闭与空审计路径（有说明）；拒绝字符串开关真值（有说明）；非负有限惩罚（有说明）；启用检查与门控前置约束（有说明）；配置映射复制（非关键未单注）
- `reward.py:process_score`：重验身份和故障拒绝（有说明）；接受答案EM及惩罚范围（有说明）；无答案EM不得非零（有说明）；从原事件重新计算硬违规（有说明）；EM门控及无答案公式（有说明）
- `reward.py:append_reports`：空路径不写盘（有说明）；整批UTF8 JSONL追加及失败传播（有说明）；目标路径对象物化（非关键未单注）
- `dynamic_filter.py:mixed_groups`：模式及组数范围（有说明）；完整组有限奖励与二值兼容（有说明）；问题身份与去重（有说明）；实数组方差有效性（有说明）；原EM与新奖励分项（有说明）；统计记录字段组合（非关键未单注）
- `dynamic_filter.py:training_batches`：奖励入口显式决定二值或实数筛选（有说明）
- `controller.py:metrics`：原正确数用原EM（有说明）；有限实数奖励合法性（有说明）；组奖励方差有效率单列（有说明）；来源合法与无答案比例单列（有说明）
- `configuration.py:provenance`：开启协议版本及奖励参数进入恢复指纹（有说明）；关闭保持历史指纹及审计路径迁移（有说明）
- `generation.py:GenerationConfig`：过程开关默认关闭（有说明）
- `generation.py:LLMGenerationManager.__init__`：来源检查完整历史前置约束（有说明）
- `generation.py:LLMGenerationManager._postprocess_responses`：共用解析消费边界与关闭兼容（有说明）
- `generation.py:LLMGenerationManager.run_llm_loop`：本次调用独立真实轨迹账本（有说明）；普通轮原始输出及轮次传入（有说明）；只统计实际接受答案（有说明）；实际裁剪分词观察入账（有说明）；最终轮搜索禁止与答案接受（有说明）；报告同行非张量身份传递及审计（有说明）；对象数组物化（非关键未单注）
- `generation.py:LLMGenerationManager.execute_predictions`：显式活动与最终掩码委托（有说明）；工具故障审计与传播（有说明）；关闭保留旧执行器（有说明）
- `main_ppo.py:RewardManager.__init__`：过程配置与奖励筛选模式（有说明）；新协议要求回答边界且零格式分（有说明）
- `main_ppo.py:RewardManager.__call__`：外部RM绕过拒绝（有说明）；同行报告与独立身份要求（有说明）；仅真实接受答案EM计算（有说明）；原EM与候选训练奖励分项（有说明）；验证返回原EM与审计兼容（有说明）；空响应不得写padding奖励（有说明）；完整批次分阶段保存（有说明）；审计记录字段组合（非关键未单注）；评分调用方阶段标记传递（有说明）
- `main_ppo.py:main_task`：仅检索任务启用过程检查（有说明）；训练与验证显式共用检查配置（有说明）
- `ray_trainer.py:_validate`：验证生成传入相同来源协议（有说明）
- `ray_trainer.py:fit`：训练生成显式过程检查配置（有说明）
- `ppo_trainer.yaml:process_checks`：配置默认关闭并分开审计和奖励（有说明）
- `test_process_checks.py:execute`：经真实账本执行测试输出，同时记录模型实际可见观察。（有说明）
- `test_process_checks.py:score`：用真实报告与独立行身份计算候选分数。（有说明）
- `test_process_checks.py:score_from_report`：验证真实生成入口产生的报告可以直接评分。（有说明）
- `test_process_checks.py:search`：记录实际检索请求并返回等长工具结果。（有说明）
- `test_process_checks.py:test_invalid_actions_and_empty_queries`：@brief 空、嵌套、未闭合动作不得检索或被接受。（有说明）；样例材料及CPU批次装配（非关键未单注）
- `test_process_checks.py:test_literal_tags_are_not_environment_impersonation`：@brief 代码及明确引用中的协议标签不能被误执行或误罚。（有说明）；样例材料及CPU批次装配（非关键未单注）
- `test_process_checks.py:test_terminal_answer_consumes_no_later_action`：@brief 首个答案之后的原始尾部只审计，不检索或重复惩罚。（有说明）；样例材料及CPU批次装配（非关键未单注）
- `test_process_checks.py:test_forged_result_correct_answer_is_gated`：@brief 复现无真实搜索却自写information并答对的获奖通道。（有说明）；样例材料及CPU批次装配（非关键未单注）
- `test_process_checks.py:test_forbidden_search_never_calls_tool`：@brief 预算到期搜索不能调用工具，按无答案惩罚。（有说明）；样例材料及CPU批次装配（非关键未单注）
- `test_process_checks.py:test_empty_real_result_is_valid`：@brief 合法空检索结果与基础设施失败严格区分。（有说明）；样例材料及CPU批次装配（非关键未单注）
- `test_process_checks.py:test_active_row_binding`：@brief 一条轨迹先结束后，另一条搜索的观察仍绑定原行。（有说明）；样例材料及CPU批次装配（非关键未单注）
- `test_process_checks.py:test_no_future_evidence`：@brief 同轮搜索后新出现的文档不能为生成前引文作事后证明。（有说明）；样例材料及CPU批次装配（非关键未单注）
- `test_process_checks.py:test_truncated_evidence_not_full_return`：@brief 不可见工具正文不算引文支持，引用文档包含调用身份。（有说明）；样例材料及CPU批次装配（非关键未单注）
- `test_process_checks.py:test_repeated_query_and_new_evidence_separated`：@brief 重复查询返回新文档不判冗余，重复也不会直接扣分。（有说明）；样例材料及CPU批次装配（非关键未单注）
- `test_process_checks.py:test_semantics_conflict_and_hops_remain_unknown`：@brief 字面引文不替代语义判定，数值冲突与多跳只给复核候选。（有说明）；样例材料及CPU批次装配（非关键未单注）
- `test_process_checks.py:test_infrastructure_exception_is_not_model_penalty`：@brief 检索异常传播并保留账本，失败批次不能变成模型负分。（有说明）；样例材料及CPU批次装配（非关键未单注）
- `test_process_checks.py:test_result_count_mismatch_stops_batch`：@brief 工具返回数量错配不得评分或绑定其他行结果。（有说明）；样例材料及CPU批次装配（非关键未单注）
- `test_process_checks.py:test_parse_mismatch_stops_batch`：@brief 后处理与执行消费边界不同必须显式停止。（有说明）；样例材料及CPU批次装配（非关键未单注）
- `test_process_checks.py:test_report_tampering_and_uid_mismatch`：@brief 同行身份、调用参数及可见证据篡改均被拒绝。（有说明）；样例材料及CPU批次装配（非关键未单注）
- `test_process_checks.py:test_event_after_answer_cannot_hide_reason`：@brief 答案后的新增事件即使删除违规标签也无法评分。（有说明）；样例材料及CPU批次装配（非关键未单注）
- `test_process_checks.py:test_real_reward_gate_validation_and_shadow_em`：@brief 真实奖励入口区分原EM、门控奖励与验证返回值。（有说明）；样例材料及CPU批次装配（非关键未单注）
- `test_process_checks.py:test_real_reward_no_answer_and_disabled`：@brief 无答案负奖励写入真实token，关闭功能保留原EM。（有说明）；样例材料及CPU批次装配（非关键未单注）
- `test_process_checks.py:test_real_generation_gpu_padding_and_metadata`：使用真实DataProto补齐、重复、重排、筛选及合并实现检验行级元数据。（有说明）；样例材料及CPU批次装配（非关键未单注）
- `test_process_checks.py:test_finite_group_filter_and_constant_groups`：@brief 实数模式只保留有差异的完整组，二值模式原规则保持。（有说明）；样例材料及CPU批次装配（非关键未单注）
- `test_process_checks.py:test_configuration_fails_before_reward_changes`：@brief 不完整开关、非法惩罚及旧上下文配置拒绝启用。（有说明）；样例材料及CPU批次装配（非关键未单注）
- `test_process_checks.py:test_difficulty_metrics_keep_original_em`：@brief 真实难度统计入口接受负奖励，原正确数与方差分别汇报。（有说明）；样例材料及CPU批次装配（非关键未单注）
- `test_process_checks.py:test_process_protocol_enters_resume_fingerprint`：仅隔离模型大文件身份IO；真正配置解析和指纹计算不替换。（有说明）；样例材料及CPU批次装配（非关键未单注）
- `test_process_checks.py:test_jsonl_audit_preserves_originals`：@brief 审计阶段和原始模型尾部以JSONL完整保存。（有说明）；样例材料及CPU批次装配（非关键未单注）
- `test_process_checks.py:fail`：模拟检索基础设施不可用。（有说明）
- `test_process_checks.py:empty`：模拟检索接口返回数量错误。（有说明）
- `test_process_checks.py:group`：构造完整同题组供真实筛选入口验收。（有说明）
- `test_process_checks.py:generate_sequences`：使用输入历史决定模拟输出，覆盖活动集缩小和设备补齐。（有说明）
- `test_process_checks.py:batch_search`：按真实批次调用提供固定检索内容。（有说明）
- `difficulty/generation.py:score_batch`：打标与训练审计阶段区分（有说明）；四轨迹原EM二值标签与负奖励分开（有说明）；同行过程证据和奖励旁列保存（有说明）
- `test_process_checks.py:test_scoring_labels_remain_binary_with_penalty`：真实打标原EM为0且候选奖励为-0.1（有说明）；样例材料及CPU批次装配（非关键未单注）
- `test_process_checks.py:SearchWorker.generate_sequences`：按CPU批次返回固定最终搜索动作（有说明）


## 2026-10-06 静态检查修复

负责人Codex /root；验收时间2026-10-06T14:22:00.765715+08:00；run_id=metax-process-checks-static-20261006-v1。

本轮静态检查发现并修复两个会影响过程奖励的bug，均先由CPU用例复现失败：

- P1：RayPPOTrainer.fit原来将除old_log_probs外的所有批次张量long化，dynamic_rewards中-0.1被截成0，随后.float()无法恢复。修复为保留old_log_probs和dynamic_rewards浮点值，仅沿用token/掩码整数转换；真实fit至GRPO优势及actor接口的CPU回归确认负奖励、小数概率和优势符号正确。
- P1：protected_text把don't/What's/That's里的两个撇号识别为成对引用，跨越search/answer起始标签，导致合法动作丢失。单引号只在词边界外开闭，允许明确引用内部缩写及转义，保留代码/引用中的协议标签保护；覆盖单轮search即停和答案未消费尾部两种路径。

修复后92项相关CPU回归全部通过（新增2项），以及最终2项针对性复验；11份相关Python源码AST解析通过，git diff --check通过。本轮代码变更仅protocol.py、ray_trainer.py和test_process_checks.py；其余此前代码/文档改动保留。分支data-difficulty-muxi，HEAD 28da773；未提交，默认新过程开关关闭。真实GPU/长期效果未验证，推理事实及多跳依然unknown，不能据本次CPU通过宣布消除所有捏造推理。

证据目录/mnt/public/code/lyk/lzy/runs/metax-process-checks-static-20261006-v1；本轮4个函数中文@brief/逐参数@param/@return通过，逻辑单元覆盖10/14=71.43%，关键逻辑漏项0。

接口清单：

- `verl/experimental/process_checks/protocol.py:protected_text`：接口通过。
- `verl/trainer/ppo/ray_trainer.py:RayPPOTrainer.fit`：接口通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_contraction_does_not_hide_action`：接口通过。
- `tests/test_process_checks.py:ProcessChecksTests.test_real_fit_keeps_fractional_reward_and_advantages`：接口通过。

逻辑单元完整清单：

- protected_text：缩写撇号与单引号词边界（有说明）
- protected_text：明确引用内缩写及反斜线转义保护（有说明）
- fit：候选奖励保留浮点且旧概率保留浮点（有说明）
- test_contraction_does_not_hide_action：缩写跨答案的测试材料构造（非关键机械装配未单注）
- test_contraction_does_not_hide_action：实际接受答案及未消费尾部奖励断言（有说明）
- test_contraction_does_not_hide_action：单轮搜索的缩写不遮蔽查询（有说明）
- test_contraction_does_not_hide_action：引用字面量样例构造（非关键机械装配未单注）
- test_contraction_does_not_hide_action：明确引用不被误门控（有说明）
- test_real_fit_keeps_fractional_reward_and_advantages：CPU配置和材料装配（非关键机械装配未单注）
- test_real_fit_keeps_fractional_reward_and_advantages：完整同题组字段与替代对象装配（非关键机械装配未单注）
- test_real_fit_keeps_fractional_reward_and_advantages：禁止候选奖励重复计算（有说明）
- test_real_fit_keeps_fractional_reward_and_advantages：保留真实fit和优势控制流仅替换GPU边界（有说明）
- test_real_fit_keeps_fractional_reward_and_advantages：浮点奖励概率与整数token断言（有说明）
- test_real_fit_keeps_fractional_reward_and_advantages：优势正负符号断言（有说明）


## 可读训练轨迹日志实现中

负责人Codex /root；检查时间2026-10-06T06:39:21.179584+00:00。既有18份过程检查及静态修复文件已提交f2132a1，提交后工作区干净；Git提交身份复用既有作者，仅本次命令指定，未改全局配置。新增独立只读展示模块、奖励入口窄适配、候选轮次/普通训练步数标注以及展示配置；真实换行、模型/环境分离、真实可见工具结果、未执行尾部、原EM/候选过程分/实际返回分分别展示。默认每评分批次每来源1条，12000字符上限，额外文本文件默认关闭。日志失败隔离，评分随机抽取保留；奖励算法、优化器、采样和来源审计策略未改。新增CPU回归待执行，实际GPU训练未启动，当前不能宣称联调通过。


## 可读训练轨迹日志验收完成

负责人Codex /root；检查时间2026-10-06T06:48:21.001614+00:00；run_id=metax-readable-logs-20261006-v1。

本次只调整训练/验证/打标共用评分入口的可读展示。独立模块`verl/utils/trajectory_logging.py`只接受已有结果，不持有训练器，不重新生成或评分。`RewardManager`只保留窄适配；训练器和动态筛选只增加展示用步数/候选轮次。候选阶段使用独立`trajectory_phase`，保留原`process_reward_phase`及来源审计语义。旧EM随机调试仅抑制打印，仍消耗同一次random.randint；关闭日志保持既有直接调用及旧打印。新日志不自动启用过程门控。

展示问题、按轮次模型原文、实际接受动作、真实调用ID/查询、仅模型可见检索结果、未执行尾部、原答案分、接受答案EM、违规原因码、门控公式、候选过程分与实际返回分。语义支持和多跳仍待复核，不加入额外奖励；规则分不冒称KL调整后奖励、GRPO优势或损失。账本关闭时展示模型输出与环境历史，并明确来源未验证，不伪造轮次。真实换行和段落边界已人工检查；标签排版幂等，终端控制字符仅在显示副本过滤，字面量反斜线n不误转换。

默认`trajectory_logging.enabled=true`，每评分批次每来源前1条，`every_n_batches=1`，每条总预算12000字符。`file_path=null`默认不额外写文件；显式配置远程运行目录里的文件路径后，`file_samples_per_source=0`记录选中批次全部轨迹，仍受单条字符预算。完整原文需另启用既有来源审计JSONL；展示截断不改原token和报告。需要关闭时设置`trajectory_logging.enabled=false`。日志格式化、额外解码、控制台和可选文件输出异常分别隔离，至多提示一次，评分和主流程继续；原来源校验和必需审计错误仍按原规则处理。同步文件追加会有I/O开销，默认不开启，实际GPU吞吐未测。

本次新增`verl/utils/trajectory_logging.py`、`tests/test_trajectory_logging.py`；修改`verl/trainer/main_ppo.py`、`verl/utils/reward_score/qa_em.py`、`verl/trainer/ppo/ray_trainer.py`、`verl/experimental/difficulty/dynamic_filter.py`、`verl/trainer/config/ppo_trainer.yaml`。已有代码先提交为`f2132a1`（18文件），随后才开始日志改动；没有push。日志改动保留远程工作区以便查看diff，未创建本机源码缓存。

验证：首轮102项CPU通过；收紧预算并新增展示解码失败后103项相关CPU回归全部通过；人工样例发现重复空行和奖励标题粘连，修复后11项日志CPU针对性回归通过，补充幂等、块边界和长答案预算断言。注释补齐已验证AST等价；最终截断提示仅调整文字，语法检查通过，不把CPU材料当作真实模型训练。27个新增/修改函数接口中文@brief/@param/@return通过；7份源码AST与YAML检查和git diff --check通过。新训练0步、新GPU调用0次；真实GPU检索联调及吞吐尚未验证。下一次实际运行使用本日志，不为验收日志单独启动训练。

注释验收：27函数接口通过；独立逻辑单元82/86=95.35%，关键漏项0。未覆盖项为非关键机械装配：render_trajectory:初始提示材料排版、HumanTrajectoryLogger.__init__:独立计数初值装配、RewardManager.__call__:展示字典字段机械装配、process_data:DataProto同行材料装配。完整清单如下：

- verl/utils/trajectory_logging.py:display_text职责：有有效中文说明。
- verl/utils/trajectory_logging.py:render_trajectory职责：有有效中文说明。
- verl/utils/trajectory_logging.py:__init__职责：有有效中文说明。
- verl/utils/trajectory_logging.py:begin_batch职责：有有效中文说明。
- verl/utils/trajectory_logging.py:selected职责：有有效中文说明。
- verl/utils/trajectory_logging.py:warn职责：有有效中文说明。
- verl/utils/trajectory_logging.py:emit职责：有有效中文说明。
- tests/test_trajectory_logging.py:process_data职责：有有效中文说明。
- tests/test_trajectory_logging.py:sample_record职责：有有效中文说明。
- tests/test_trajectory_logging.py:test_rewards_rng_and_input_unchanged职责：有有效中文说明。
- tests/test_trajectory_logging.py:test_forged_observation_reward_explained职责：有有效中文说明。
- tests/test_trajectory_logging.py:test_validation_keeps_original_score职责：有有效中文说明。
- tests/test_trajectory_logging.py:test_missing_answer_negative_reward职责：有有效中文说明。
- tests/test_trajectory_logging.py:test_real_turns_visible_evidence_and_tail职责：有有效中文说明。
- tests/test_trajectory_logging.py:test_newlines_controls_and_length_budget职责：有有效中文说明。
- tests/test_trajectory_logging.py:test_deterministic_limits_and_batch_frequency职责：有有效中文说明。
- tests/test_trajectory_logging.py:test_file_all_rows_and_console_failure_independent职责：有有效中文说明。
- tests/test_trajectory_logging.py:test_reward_survives_file_and_formatter_failures职责：有有效中文说明。
- tests/test_trajectory_logging.py:test_display_decode_failure_preserves_reward职责：有有效中文说明。
- tests/test_trajectory_logging.py:test_invalid_configuration_rejected职责：有有效中文说明。
- tests/test_trajectory_logging.py:decode职责：有有效中文说明。
- verl/trainer/main_ppo.py:main_task职责：有有效中文说明。
- verl/trainer/main_ppo.py:__init__职责：有有效中文说明。
- verl/trainer/main_ppo.py:__call__职责：有有效中文说明。
- verl/utils/reward_score/qa_em.py:compute_score_em职责：有有效中文说明。
- verl/trainer/ppo/ray_trainer.py:fit职责：有有效中文说明。
- verl/experimental/difficulty/dynamic_filter.py:training_batches职责：有有效中文说明。
- display_text:统一CR换行与终端控制字符过滤：有有效中文说明。
- display_text:控制标签换行且重复渲染幂等：有有效中文说明。
- display_text:字符预算与显式截断：有有效中文说明。
- render_trajectory:最小预算校验：有有效中文说明。
- render_trajectory:同行身份、阶段、候选轮次展示：有有效中文说明。
- render_trajectory:初始提示材料排版：非关键机械装配，未单注。
- render_trajectory:调用表和按轮次模型输出：有有效中文说明。
- render_trajectory:接受动作与违规原文位置：有有效中文说明。
- render_trajectory:真实工具身份及仅可见结果：有有效中文说明。
- render_trajectory:未执行尾部单独标记：有有效中文说明。
- render_trajectory:沿用引用诊断不新增语义奖惩：有有效中文说明。
- render_trajectory:关闭账本的模型和环境历史分离：有有效中文说明。
- render_trajectory:共用答案提取且不再评分：有有效中文说明。
- render_trajectory:原分、接受EM和门控公式解释：有有效中文说明。
- render_trajectory:训练候选与验证实际返回策略：有有效中文说明。
- render_trajectory:规则分与后续KL优势损失区分：有有效中文说明。
- render_trajectory:长总结预算及最终分保留：有有效中文说明。
- render_trajectory:整条总预算与明确块间空行：有有效中文说明。
- HumanTrajectoryLogger.__init__:布尔和整数类型校验：有有效中文说明。
- HumanTrajectoryLogger.__init__:限额、频率与字符预算校验：有有效中文说明。
- HumanTrajectoryLogger.__init__:文件路径类型与空串拒绝：有有效中文说明。
- HumanTrajectoryLogger.__init__:独立计数初值装配：非关键机械装配，未单注。
- HumanTrajectoryLogger.begin_batch:只读展示计数重置：有有效中文说明。
- HumanTrajectoryLogger.selected:关闭与确定性批次频率：有有效中文说明。
- HumanTrajectoryLogger.selected:按来源独立控制台和文件限额：有有效中文说明。
- HumanTrajectoryLogger.warn:一次警告及警告失败隔离：有有效中文说明。
- HumanTrajectoryLogger.emit:先消费展示名额：有有效中文说明。
- HumanTrajectoryLogger.emit:格式化异常隔离：有有效中文说明。
- HumanTrajectoryLogger.emit:控制台失败隔离：有有效中文说明。
- HumanTrajectoryLogger.emit:UTF8文件追加及失败独立隔离：有有效中文说明。
- RewardManager.__init__:独立展示对象初始化：有有效中文说明。
- RewardManager.__call__:评分批次展示计数：有有效中文说明。
- RewardManager.__call__:关闭旧打印但保留随机评分调用：有有效中文说明。
- RewardManager.__call__:只在展示行额外解码：有有效中文说明。
- RewardManager.__call__:展示字典字段机械装配：非关键机械装配，未单注。
- RewardManager.__call__:展示故障捕获及关闭后的旧打印兼容：有有效中文说明。
- main_task:训练和验证同配置且独立计数：有有效中文说明。
- RayPPOTrainer.fit:普通训练日志绝对步数标注：有有效中文说明。
- training_batches:候选步数轮次与独立日志阶段标注：有有效中文说明。
- compute_score_em:同一次随机数消耗及仅抑制旧打印：有有效中文说明。
- compute_score_em:原奖励分支保持：有有效中文说明。
- ppo_trainer.yaml:默认有限样例和可选文件配置：有有效中文说明。
- process_data:真实执行器生成来源身份：有有效中文说明。
- process_data:DataProto同行材料装配：非关键机械装配，未单注。
- sample_record:只用于展示的固定字段装配：有有效中文说明。
- test_rewards_rng_and_input_unchanged:真实入口多模式奖励随机流与张量比较：有有效中文说明。
- test_forged_observation_reward_explained:原EM1与门控实际0对照：有有效中文说明。
- test_validation_keeps_original_score:验证保留原EM及候选分并列：有有效中文说明。
- test_missing_answer_negative_reward:缺答案真实浮点负分展示：有有效中文说明。
- test_real_turns_visible_evidence_and_tail:按真实工具返回裁剪可见证据：有有效中文说明。
- test_real_turns_visible_evidence_and_tail:原记录不变、块间空行与幂等：有有效中文说明。
- test_newlines_controls_and_length_budget:真实换行及字面量转义边界：有有效中文说明。
- test_newlines_controls_and_length_budget:长正文和长奖励总结总预算：有有效中文说明。
- test_deterministic_limits_and_batch_frequency:批次频率与来源限额无随机消耗：有有效中文说明。
- test_file_all_rows_and_console_failure_independent:一个目的地失败不妨碍另一个：有有效中文说明。
- test_reward_survives_file_and_formatter_failures:文件及格式化失败仍返回奖励：有有效中文说明。
- DisplayFailTokenizer.decode:仅展示解码失败的条件边界：有有效中文说明。
- test_display_decode_failure_preserves_reward:额外解码失败隔离：有有效中文说明。
- test_invalid_configuration_rejected:非法开关限额频率路径拒绝：有有效中文说明。

证据目录：/mnt/public/code/lyk/lzy/runs/metax-readable-logs-20261006-v1。


## 2026-10-06T07:08:01.330646+00:00 最小必要真实联调完成

负责人Codex /root；run_id=metax-process-preflight-20261006-v1。

训练核心未修改；在远程独立目录组合已验证共享接口联调。脚本语法、5函数中文接口通过；逻辑注释覆盖27/28，清单见comment-verification.json。全部8条/30调用已复核，实际GPU零参数更新；通过技术接线不表示语义奖惩已实现。真实产物与源码哈希见manifest.json，原始审计/可读日志保存在同运行目录，无本机缓存。

- save:职责与原子输出：有效中文说明。
- freeze:职责与拒绝覆盖：有效中文说明。
- freeze:来源/哈希选题：有效中文说明。
- freeze:标签校验：有效中文说明。
- freeze:原数据与独立种子固定：有效中文说明。
- summarize_rewards:职责：有效中文说明。
- summarize_rewards:同一批三种共享评分：有效中文说明。
- summarize_rewards:浮点与有限奖励：有效中文说明。
- summarize_rewards:完整组筛选/真实GRPO：有效中文说明。
- summarize_rewards:有限优势/原模型token提取：有效中文说明。
- summarize_rewards:同行报告保存：有效中文说明。
- main:职责：有效中文说明。
- main:prepare与GPU分离：有效中文说明。
- main:只读模型和原配置：有效中文说明。
- main:分词器一致性：有效中文说明。
- main:冻结题集匹配：有效中文说明。
- main:原同题展开和独立种子：有效中文说明。
- main:仅推理通信组：有效中文说明。
- main:共用冷加载和检索配置：有效中文说明。
- main:真实事件与阶段保存：有效中文说明。
- main:轨迹数/唯一ID校验：有效中文说明。
- main:最终结果字段装配：非关键字段装配，未单注。
- main:仅本任务资源释放：有效中文说明。
- supervisor:职责：有效中文说明。
- supervisor:新进程组隔离：有效中文说明。
- supervisor:1200秒预算：有效中文说明。
- supervisor:超时TERM/KILL：有效中文说明。
- supervisor:真实退出记录：有效中文说明。

## 2026-10-06T07:38:50.183654+00:00 用户授权单组40步正式实验

负责人Codex /root；run_id=metax-process-r1-40-20261006-v1。用户明确同意先只跑带无答案惩罚的一组，并要求直接进行40步；本节取代此前R0/R1各25步或分阶段延长的启动方案。仅运行R1，不启动R0、SFT或额外诊断训练。
从旧v4的step40 actor权重冷初始化；固定reference为Qwen2.5-7B Base，优化器、随机流、采样器重新初始化，新global step从0到40。旧优化器/协议指纹不恢复，新40步不能直接当作旧训练的绝对step80。
P候选10000题，每步保留8道新有效题×8轨迹=64；40步目标320道本运行内不同题、2560条入选轨迹。动态有限实数组方差筛选，最多8候选轮/步，候选量与入选量分别记账；新题可与父模型历史训练题重合。
开启process_checks.enabled/reward_gate，beta=0.1；奖励=接受答案EM×协议合法−0.1×无接受答案。保持原GRPO、lr=1e-6/warmup10、KL=0.001、mini/micro=32/8、温度1/top_p0.95、轮次10、上下文4096/单轮256/观察2048和已修KV失效。
D64从已有冻结D256按来源30NQ+34Hotpot及固定哈希选取，0/5/10/15/20/25/30/35/40评价；原主流程结束会再评价一次D64，单独标轮次不混合。10/20/30/40保存完整状态，结束后同新协议val_only零更新复核D256。T仅检查manifest隔离ID，不读封存题或答案。
资源8×MetaX C500，原GPU7检索服务保留；磁盘实测剩余3.3T，参考完整检查点86G，计划4个约344G，仅估算。所有小脚本、配置、源码/dirty快照、审计、可读日志和模型留远程/mnt/public/code/lyk/lzy/runs/metax-process-r1-40-20261006-v1，本机不落盘。
初始状态：准备完成，CPU父推理完整性、分词器同Base、P/D隔离、Hydra train配置解析通过；训练0/40步、完整新checkpoint无，GPU尚未启动。注释接口12函数全部通过，逻辑单元48/50=96.00%，关键遗漏0；清单见comment-verification.json。本次仅新增运行目录脚本，未修改训练主流程；此前103项CPU及一题真实联调保留其原范围，不代替新多卡训练验收。
监管器每60秒同步实测状态；非有限梯度/优化器跳过或基础设施错误停止并保留现场，答案率/正确率异常先记录，无任意改奖励或自动重启。整套策略效果可评价，无独立R0无法分离beta贡献；事实和多跳语义仍未知/人工审查。

## 2026-10-06T07:45:35.311086+00:00 启动监管字段修正及attempt2

负责人Codex /root；run_id=metax-process-r1-40-20261006-v1。启动后只读接口复核发现答案审计只有evaluation_step/reward_call，监管器误读evaluation_round，故在参数更新0步、GPU训练worker未加载时主动停止attempt1（所属训练进程退出-6）。原日志及进程身份保留于attempts/1，GPU除原检索服务外均已释放。
修正仅运行目录supervisor.py：按evaluation_step累计评价记录数，保留reward_call批次身份，不虚构评价轮次。训练/奖励/生成源码及预算均未改，代码已提交889e5c2。CPU使用真实make_record接口复现旧KeyError并验证修正后初始/重复评价记录读取，退出0；check-only退出0，无GPU生成、无更新。
新增测试check函数中文接口完整；函数职责、真实schema旧失败回归、临时路径隔离、初始读取与重复计数5个逻辑单元全部有中文说明；原监管读取计数单元说明同步。此小范围5/5、全部合并53/55=96.36%，关键遗漏0。完整清单与源码保存在运行目录。下一步attempt2重新启动相同冻结40步，保留父权重、数据、随机种子及所有奖励设置。


## 2026-10-07T16:43:46.141852+08:00 40步完成与最终评价启动故障恢复

负责人Codex /root；训练40/40步完成，320道不同题、2560条入选轨迹；40步D64两次分别29/64=45.3125%，均无答案0，128条为同64题重复评价。step40完整检查点已由read_checkpoint全文件校验，checkpoint-verification.json于16:00:07北京时间确认。训练退出后最终D256在Ray初始化失败，AF_UNIX临时路径超过107字节，模型加载/答题/更新均尚未开始；失败状态与日志归档attempts/final-D256-1。八卡除原检索服务外已空闲。新增仅运行目录recover_final.py独占恢复原val_only命令，唯一环境变更RAY_TMPDIR=/tmp/r1d256r2，奖励、数据、种子、模型及冻结源码不变，不重新训练。AST通过，真实Ray路径校验CPU复现旧路径失败并确认短路径通过，GPU调用0；恢复尚待启动。恢复脚本1函数中文接口及全部关键分支有说明，逻辑单元10/10覆盖：职责、双锁、重复任务、GPU占用、checkpoint证据、旧答案防重、短路径与原命令、进度、完整/零更新验收、异常收尾；关键遗漏0。未运行新的训练代码测试。本次故障与能力评价分别记账，最终D256结果待完成。


## 2026-10-07T13:08:40.376007+00:00 模型选择控制脚本CPU验收

运行目录selection.py、test_selection.py与复用final_eval.py完成AST检查，17函数@brief/逐参数@param/@return齐全；关键流程仅新增独立控制层，未修改训练/生成/评分实现。4项CPU检查通过：题数/身份/顺序/奖励边界、配置允许路径与拒绝温度漂移、同题标签配对、实际Ray短路径长度。GPU调用0、参数更新0；推理权重/配置冻结仍待prepare完成。注释逻辑单元53/57=92.98%，非关键未单注项['来源汇总', '配对差值', '检索可达', '进程身份']，关键遗漏0；清单在运行目录comment-verification.json。证据cpu-check.log。


## 2026-10-07T13:12:10.938975+00:00 同协议验证启动

run_id=metax-process-selection-d256-20261007-v1；两模型实际推理文件/分词器、D256身份与配置一致性CPU检查通过，两份Hydra配置解析退出0；监管PID2084524，身份见launcher-process.json。按父模型→step30顺序执行各256题val_only，新参数更新0；step40复用115/256。实际已完成题数由status.json确认，不将预算512当已完成。运行日志parent/console.log、step30/console.log，监管每30秒同步进度，单模型75分钟限额含加载。启动时原检索服务保留，训练源码未改。


## 2026-10-07T16:08:04.224314+00:00 扩大实验脚本与必要CPU验证

run_id=metax-process-r1-100-b32-20261008-v1；新增远程运行目录prepare.py、supervisor.py、final_eval.py、test_expansion.py，复用原正式入口、模型验证、奖励与筛选实现，没有修改生产训练源码。预算100新步×32题×8回答；mini128/micro8、D256每20步/最终冷评价、候选补抽上限16。新增监管完整D256保护：26以上缺答案或两次不同step正确数<=80暂停所属训练；完整轮次必须256唯一题，同一步重复不算两次。继承新40 actor、新优化器/RNG/采样器，严格恢复指纹未绕过。

本次实跑必要既有CPU回归48项通过（process_checks/dynamic_filter/metax_weight_cache_invalidation），新扩大入口及保护检查6项通过：真实32×8补抽/组及同行元数据、同配置恢复、部分/重复评价、同step重复保护、缺答案边界、49历史来源、两条标签敏感性。后两项复现未解决边界，不能宣称误罚已修复。生产parse与reward不变。prepare退出0并完成模型全文件/数据隔离/tokenizer/配置/源快照校验，监管check-only退出0；GPU正式联调尚未启动。

中文注释检查范围为上述四脚本，函数逐项AST确认@brief/@param/@return，关键逻辑按职责、分支、循环、状态切换核对；逻辑单元清单、每文件覆盖与遗漏见/mnt/public/code/lyk/lzy/runs/metax-process-r1-100-b32-20261008-v1/comment-verification.json。总计71/71=100%，缺少函数说明0、关键逻辑遗漏0；函数说明与关键注释独立核查。配置冻结/control-hashes与manifest保留源码版本及dirty快照；新脚本只管单次实验监管，不另写奖励、生成或采样算法。Hydra解析尚待完成，下一步通过后启动已授权扩大实验，T未读。


## 2026-10-08T03:09:14.187776+00:00 独立GPU检索基准脚本

范围：运行目录benchmark.py，无生产源码修改。职责：固定查询编码、分块分片精确搜索、CPU/GPU比较、耗时与显存统计；输入真实查询及原索引，输出results.json/npz，不接入训练器。函数六项：save、shard_search、search、compare、main及脚本异常入口（入口非函数）；五个显式函数与main共六？实际函数由AST核查，以代码为准。函数@brief/@param/@return全部通过；数值/并行/显存/公平性/异常约束就近中文说明。逻辑单元清单：原子记录、分块内积、块内top3、块间合并、CPU同步传回、并发分片、全局候选合并、排序/集合核对、匹配分数误差、关闭TF32、设备数保护、复用Encoder、固定嵌入、CPU索引加载、内存视图、小样比较保护、均匀分片、GPU同步计时、显存峰值复位、CPU线程比较、大批量设置选择、GPU热身、三次计时、比较与持久化、显存汇总、未联合验证标记、异常留痕。共27单元；覆盖其中23（其余设备数保护/CPU索引加载/显存汇总/未联合标记无单独邻近说明），23/27=85.19%。重要算法/显存/公平性分支说明完整，尚待实跑结果。未修改评分/采样/恢复，相关CPU测试不适用；小样真实GPU核对由基准执行，不能代替完整索引或联合训练。


## 2026-10-08T03:14:54.507146+00:00 显存约束与检查更正

用户再次确认每题rollout8条及原实验配置不降低。题组32、n_agent8、训练100步、mini128、生成长度/最大轮数/采样/奖励/学习率保持。candidate_train_memory.yaml仅执行层候选：actor/ref/rollout微批量4、KV显存预算0.24、调度单批token4096，使用累积维持有效批量；不得缩短响应或减少8条轨迹。未覆盖原冻结train.yaml、未换线上URL、未重启训练。联合目标驱动峰值<=56GiB/卡（留8GiB），尚未实测联合模型。

基准仅补中文注释，AST与执行快照benchmark.executed.py一致，执行hash=9fb1403d8f03ceff400d14630b26de6a4286cae749ba9a216ae869d9804577c7。实际5个函数（save/shard_search/search/compare/main），之前6个的记录计数错误；函数标签检查通过。沿用原27逻辑单元口径，补设备保护/CPU加载/距离保护/显存统计/联合边界/异常路径说明后27/27覆盖，关键注释与函数文档完整。未改生产代码。第一次记录更新因系统python缺yaml在import阶段失败，无部分修改；改用现有retriever环境完成，无安装新包。


## 2026-10-08T03:30:11.377807+00:00 完整索引GPU基准阶段完成与候选预算修订

results.json completed。CPU原160线程32/128查询98.330/239.362秒；CPU已测最快8线程39.740/127.686秒。八卡FP32、块262144对应32/128/256查询热身后三次中位0.019024/0.042849/0.074476秒；32和128查询top3编号及顺序100%一致，匹配分数最大误差1.073e-6；完整256查询CPU核对追加进行中（CPU独立，无GPU或训练）。CPU每设置计时一次、GPU三次，固定同嵌入、同全量索引，不混一次性加载；启动CPU加载92.289秒/GPU复制25.364秒。检索进程GPU分配峰值最高9.024GiB、缓存预留9.801GiB（包含两种块大小）；不含独立E5服务/驱动，不等于联合训练峰值。基准PID已退出、GPU已释放，线上仍CPU服务PID155243，正式训练未恢复。

原启动日志在gpu_memory_utilization=0.32时KV仅0.72–0.79GiB，不能未经联合profile就将预算压到0.24。候选修订为0.30（取代准备阶段0.24），配合调度token8192→4096及三项微批量8→4；32×8、mini128、总100步、上下文/响应长度/最大轮数、采样、奖励、学习率全部不变。候选尚未联合实跑，不宣称不会OOM；上线后必须索引先常驻并稳定，再profile模型/生成/更新，驱动峰值<=56GiB/卡；KV至少覆盖原4352上下文，不靠缩短上下文通过。

validate256.py仅独立CPU比较，复用benchmark.compare，不改线上。无新增函数，关键逻辑单元5项（固定线程/完整索引与嵌入/两种GPU结果比较/持久化证据/失败保护）均有中文就近说明，5/5覆盖；未更改评分/采样/恢复，CPU控制回归不适用。


## 2026-10-08T03:32:17.793156+00:00 最终选择验证与停止状态

推荐块262144：完整256真实查询CPU8线程228.475秒，GPU三次中位0.074476秒；全256的top3编号及顺序100%一致，最大匹配分数误差1.073e-6。32/128分别39.740/127.686→0.019024/0.042849秒，搜索核心约2089/2980/3068倍；不将此倍率当整步训练或HTTP检索服务倍率。固定同一E5嵌入/完整21015324×768索引，FP32，非近似索引。大块1048576在256条中的241/243行出现2条第三名候选差异，精确查询一致率254/256，整体校验脚本assert退出1，已保留validation256.log/json/npz，排除该块而不覆盖失败。差异见assessment.json，不据此声称所有GPU配置等价。小块256/256通过，推荐选项已验证。

OOM边界：检索单独分配峰值9.024GiB/预留9.801GiB（整轮两种块的上界），不含独立E5服务和驱动；原训练约33GiB仅瞬时采样。联合训练模型、KV/反向/优化器与索引峰值未验证，不能保证OOM已解决。candidate配置仅micro8→4、调度token8192→4096、rollout预算0.32→0.30；8条rollout、32题、mini128、100新步及实验参数不变。未改生产训练/检索源代码及原冻结配置，线上仍CPU服务，训练停在7步且本轮无checkpoint、未重启、未进入最终评价；GPU基准和CPU核对均结束、临时GPU占用释放。后续接入必须独立配置/启动记录，索引先稳定加载，再联合profile并验收每卡至少8GiB余量及4352上下文，不依靠减少轨迹或响应长度通过。报告和结构化证据在run目录，台账同步完成。


## 2026-10-08T03:45:36.319200+00:00 GPU检索迁移开始

用户授权迁移服务、初步验证及配置调整。run_id=metax-gpu-retrieval-migration-20261008-v1；新增gpu_flat_index.py常驻8卡FP32分片、262144行块、256查询计算批量，复用原Encoder/语料读取/响应格式；retrieval_server.py显式torch_gpu后端、默认CPU兼容、线程输入设备修复、请求串行、每进程18%显存上限、health/host/port。只改检索职责，不改训练评分采样算法。旧CPU PID155243暂保留，先8001候选HTTP核对后切8000；正式训练不恢复。联合验证计划独立运行原100步配置并在首个完整32×8训练步后人工监管停止，覆盖反向/优化器；该独立临时更新不计入正式100步、不替代父step40，样本/奖励/长度/温度等不变。准备阶段尚无API或联合GPU验收。源码前版备份和git-diff在run目录，基准与失配历史保留。


## 2026-10-08T03:48:23.843751+00:00 CPU控制检查通过、候选服务启动

CPU测试5项通过：跨分片候选/编号、负分数与并列、非法输入、CPU默认、L2拒绝；两个生产文件语法解析通过。候选GPU服务PID2131772，127.0.0.1:8001，全8卡，FP32、262144行块、256查询调度、进程每卡18%预算。原CPU8000及其启动环境/命令已备份rollback.json，真实32查询HTTP基线正在独立采集。GPU/API及联合训练尚未验收，正式训练停止。


## 2026-10-08T04:30:00.497066+00:00 配置准备及联合验证验收条件

正式就绪配置 /mnt/public/code/lyk/lzy/runs/metax-process-r1-100-b32-gpu-20261008-v1/train.yaml，未启动；独立joint-smoke/train.yaml同100步预算，监管首完整训练步后停止。执行层仅actor/ref/rollout微批量4、调度4096tokens、vLLM0.30；32题×8回答、mini128、100步、生成长度/轮数/温度/top_p、GRPO/EM/门控/beta/学习率保持原值。仅新产物路径/实验名及GPU实现retrieval_id另记，不绕过旧恢复指纹；从既有step40 actor冷起点，旧7步未持久化不冒称可恢复。

验收：原8000 health GPU且逐文档协议一致；首步实际32完整有效组/256轨迹、actor optimizer_step=1、有限损失/梯度，驱动每卡峰值<=56GiB留8GiB；全过程原响应/上下文4352不缩短。只停止验证创建的新进程组，检索常驻。若KV初始化失败或显存越界，只调整执行层预算再验证，不降低8条/32题。

源码职责集中gpu_flat_index.py，服务只适配索引与设备、请求锁、可选配置。中文注释检查：核心9单元（输入/距离保护、显式设备、FP32、均匀分片、分块内积、局部候选、八卡并发、合并、计算批量/空输入边界）及服务6单元（默认CPU兼容、编码设备、预算验证/设置、E5卡选择、请求锁、健康统计）、监管7单元（独立路径、禁止重复训练、身份记录、驱动采样/峰值、完整指标、预算/OOM/超时、所属组停止）共22职责单元；各有函数/就近中文说明22/22=100%，函数标签逐AST通过source-manifest记录。已有函数未改变的内部池化/格式化不计新增逻辑。CPU5项通过；API已通过；完整联合GPU尚未完成，不以CPU结果替代。


## 2026-10-08T04:37:22.220967+00:00 缓存环境修复重启

首次8000环境漏HF_DATASETS_CACHE导致重建同一语料，已核对FD中builder.lock/临时Arrow；未有联合训练启动。该进程及ready gate已停止，保留失败日志和临时缓存，不删除原数据。补原cache/retriever-metax/datasets与TMPDIR；DenseRetriever先load_corpus后CUDA初始化（新增顺序单元有就近中文说明，编码/文档/索引不变）。第一次重启脚本dict重复CUDA_VISIBLE_DEVICES参数在构造环境阶段失败，未创建新进程；改用update修复。新GPU PID2137145，原8000；gate2137146等待health后启动独立首步。默认CPU兼容检查待重跑。


## 2026-10-08T04:46:49.519107+00:00 约束修正、实际训练环境配置检查通过

两次联合启动在模型加载前因全局micro4不是8卡倍数退出，未更新参数；两次失败JSON及原console备份保留。actor/ref/rollout微批量恢复原8，worker分别除以8为每卡1条。配置检查先在retriever环境缺OmegaConf未执行保护函数，已改原env/metax/run.sh真实训练SDK环境执行，两份prepare_config CONFIG PASSED；不安装新包。32×8、mini128、100步及生成/采样/奖励不变，最终执行层仅max_num_batched_tokens4096、vLLM预算0.30。GPU原8000已就绪，attempt3联合监管PID2139245启动，首完整更新后停止，正式GPU100步仍prepared。此前micro4候选撤销，旧冻结实验未改。


## 2026-10-08T04:51:28.502860+00:00 冷启动顺序修复后控制回归

CPU关联5项再次全部通过，生产两个文件语法解析通过；最终源码sha256/完整diff与新模块快照保存在迁移run。语料加载移到GPU上下文前，新增1顺序单元有就近中文说明；原22职责单元加此项为23/23覆盖，函数中文标签检查沿用且未新增无说明函数。原8000 GPU服务已就绪，独立joint attempt3进行中；正式100步未启动。此前缺requests/OmegaConf、缓存环境遗漏、微批量整除错误及修复均记录，不能写为一次全部通过。


## 2026-10-08T04:59:56.482023+00:00 联合第三次失败及调度预算修复

第三次联合验证在vLLM缓存初始化退出：KV可用-0.56GiB，驱动峰值最高36.159GiB，未发生物理64GiB OOM、未生成或更新；失败JSON及console.attempt3-kv-failed.log已归档。发现旧rollout和MetaX窄接口均未传递配置max_num_batched_tokens/max_num_seqs，因此此前4096候选未生效。现仅MetaX0.11显式传递两项预算，原生缺省/其他版本行为保留，配置改为4352 tokens（覆盖完整上下文）/64并发序列/0.30预算；请求全部排队生成、不减少32题×8条、mini128、micro8、100步、响应/上下文/轮数或采样奖励学习率。正式训练未启动。新的CPU检查与首完整联合更新尚待验证。

函数职责仍集中在rollout适配和MetaX构造器，无实验名/机器路径进入共用代码。新增调度传递、缺省兼容、正整数保护3逻辑单元均有就近中文说明；两处修改构造函数参数说明齐全。原23单元加3为26/26覆盖，构造函数既有缓存/并行/上下文/采样保护补中文说明。不用之前检索CPU5项结果证明新适配器通过。


## 2026-10-08T05:02:16.581408+00:00 CPU预算测试依赖隔离修复

新增预算接口CPU测试首次1通过/2依赖导入异常：Mock sys.modules前未预载torch，隔离恢复后重复导入扩展发生docstring异常；未触发真实GPU或训练，不属于生产预算失败。测试调整为预加载torch/safetensors后仅隔离vllm，失败日志保留scheduler-tests.import-isolation-failed.log；准备重跑。测试新增职责（隔离、缺省/显式、非法值、两层及版本传递）4/4单元具中文说明，所有测试函数@brief/@return齐全；无评分/采样/恢复变更。


## 2026-10-08T05:04:43.889580+00:00 调度预算CPU通过及联合attempt4启动

预算接口CPU3项、既有权重缓存CPU8项通过；训练两份prepare_config保护检查通过。原8000 health ready/search_backend=torch_gpu；先前启动前检查错误使用backend字段KeyError，未创建训练，已修正。新监管PID2144933，32题×8条、micro8、mini128、100步预算，4352调度tokens/64并发/vLLM0.30，驱动56GiB保护；完成首个真实更新后停止。正式100步未启动，联合GPU验收待实测。


## 2026-10-08T05:06:53.457155+00:00 复现与回退配置归档

新增运行目录gpu-service-config.json完整冻结GPU启动参数及原HF_DATASETS_CACHE/TMPDIR/SDK环境；start_retrieval.py --backend gpu/cpu以exec前台启动，端口8000已占用时拒绝，不停止未知服务、不创建重复训练。CPU回退复用原rollback.json。脚本4逻辑单元（目录隔离、端口保护、环境复用、exec生命周期）均有中文就近说明4/4；无新增函数。脚本仅语法检查及端口保护待检，未重启目前线上服务。联合attempt4进行中，正式训练未启动。


## 2026-10-08T05:08:02.573358+00:00 冻结指纹保护及联合attempt5

attempt4在创建难度控制器时拒绝复用不同配置的旧输出目录，未加载训练GPU模型、未更新参数；保护有效，失败JSON/console已归档。调度参数改变后改用独立joint-smoke-attempt5目录，不放宽或绕过指纹保护，监管PID2146691。配置仍32×8/micro8/mini128/100步，4352tokens/64并发/0.30；仅产物目录变化。正式训练未启动，联合完整首步待实测。监管仅新增尝试目录隔离1注释单元，旧7单元加1为8/8；未改采样和状态恢复算法。


## 2026-10-08T05:26:05.671859+00:00 联合attempt5显存保护及推理权重CPU卸载实现

第三轮筛选已得到32组/256轨迹，但进入epoch0训练计算阶段驱动峰值63.534GiB，超过56GiB保护；监管停止，train事件为空，未完成更新，不能记GPU联合通过。失败JSON归档，独立attempt5全部日志保留，正式训练未启动。低KV预算不能释放常驻14.27GiB推理权重。新增显式offload_weights_to_cpu执行层开关（默认false），复用原offload_model_weights接口：无未完成请求时worker将同dtype参数/缓冲区搬至CPU，下一生成/新权重同步前恢复GPU；同版本KV保留，新版本仍完整load及reset。禁与既有sleep同时启用，不使用已知退出不稳定的sleep allocator。worker仅增加设备搬移RPC，算法/采样/奖励及全部轨迹不改。新增函数中文@brief/@return/异常约束完整、关键状态/RPC失败就近说明。新的CPU控制检查、GPU输出往返一致性和完整首步尚未验证，不能沿用之前CPU8项证明新卸载路径通过。


## 2026-10-08T05:29:26.528484+00:00 CPU卸载控制回归通过及单卡真实往返开始

新增卸载状态CPU3项通过，原权重缓存CPU8项在修改后再次通过；cpu-weight-offload-tests.log/cache-regression.after-offload.log。单卡GPU完整父step40模型往返验证已启动，固定贪心2条查询，要求token/logprob完全相同及实际释放>12GiB；当前尚未完成，不能记通过。单卡检查只验证设备搬移，之后仍须32×8完整联合更新。新增测试职责和关键状态说明齐全；脚本函数main含@brief/@return/@raises/@note，不将固定测试路径写入生产模块。正式训练仍未启动。


## 2026-10-08T05:30:24.373752+00:00 单卡往返KV预算失败及修订

单卡检查0.30在原生KV初始化退出：可用0.22GiB小于4352上下文需0.23GiB，尚未执行卸载，不属于CPU搬移失败。失败日志gpu-weight-roundtrip.kv-budget-failed.log保留；独立单卡检查预算改为0.32，不改上下文/输出/模型精度，准备重跑。此前联合0.30八卡可用0.41GiB有真实证据；正式与联合就绪预算暂不变，CPU卸载验收仍待GPU。正式训练未启动。


## 2026-10-08T05:32:47.994175+00:00 完整模型CPU/GPU往返通过及联合attempt6

单卡完整父step40/FP16/4352上下文真实往返通过：2条贪心查询token及logprob完全相同，释放14.271617GiB，卸载5.511秒，恢复加生成2.476秒。此为执行资源验证，不代替联合训练。检索服务始终保留。就绪正式及新joint-smoke-attempt6配置启用offload_weights_to_cpu=true，并恢复原vLLM0.32预算，配合已接通4352tokens/64并发，以释放推理常驻权重同时避免0.30仅够1.47倍最长上下文的缓存拥塞。32题×8条、micro8、mini128、100步、精度/响应/上下文/轮数/采样/奖励/学习率不改。新监管PID2155031首完整更新后停止，56GiB保护，正式100步未启动。失败KV单卡尝试保留，不称所有尝试一次通过。


## 2026-10-08T05:36:28.187739+00:00 最终函数说明及配置CPU检查

五个生产文件逐函数AST比较冻结前版，所有本次新增/修改函数均有中文@brief/@return及每个显式参数@param，语法解析全部通过，source-manifest.final.json/各源文件.final.py/git-diff.final.patch已刷新。最终两份配置保护通过，调度接口CPU3项在卸载改动后重跑通过；卸载CPU3项、既有缓存CPU8项已通过。真实单卡CPU/GPU往返2查询完全一致且释放14.27GiB；完整联合attempt6仍running，尚未有train验收。


## 2026-10-08T05:39:28.152991+00:00 卸载新版本同步CPU检查补充

新增CPU检查先恢复设备、加载新权重、重置旧KV的顺序；首次3通过/1因替身reset_prefix_cache默认Mock对象未模拟V1成功None而失败，生产保护正常拒绝。已保存mock-reset-failed.log并修正替身，准备重跑。没有修改生产代码或当前运行配置。联合attempt6正常推进，已确认原上下文KV、权重同步和初次卸载，驱动初始化峰值36.9GiB，完整更新待完成。


## 2026-10-08T05:41:39.530758+00:00 联合attempt6首轮候选完成

真实日志首轮32候选题保留14/32有效组，仍在补抽，尚无train事件，不计参数更新。当前驱动峰值36.909GiB（索引/E5/生成全部计入），反向及优化器峰值待确认。卸载CPU最终4项全部通过，包括卸载后新版本恢复GPU→加载→重置KV顺序，cpu-weight-offload-tests.final.log；测试替身错误日志保留。正式100步未启动，GPU8000继续提供服务。


## 2026-10-08T05:54:46.034469+00:00 GPU检索迁移最终验收完成

GPU原8000服务PID2137145 ready，21015324向量/8卡，训练后256真实查询逐文档再次100%一致，HTTP 0.156929秒。独立joint-smoke-attempt6完整train step1已完成：32有效题组/256保留轨迹，候选96题/768轨迹/3轮，全部数值指标有限、梯度范数2.942259、optimizer_step均值1.0，无OOM；驱动八卡峰值48.182–48.807GiB、最小15.193GiB余量，56GiB保护未触发。训练耗时524.600秒（生成405.236/参考17.075/更新82.319），对原首步5103.252秒9.728倍、旧7步中位4847.835秒9.241倍；仅单步初步证据，不外推稳定100步。监管在train事件后主动停止，停止阶段退出码-6保留，当前ps/mx-smi无训练或验证worker，仅检索常驻；独立更新没有保存checkpoint、不计正式100步。正式100步prepared未启动，原7步没有checkpoint，可用起点仍父step40。最终配置仅4352调度token/64序列/CPU推理权重卸载，vLLM0.32与三项micro8保留原值；原32×8/mini128/100步及精度、上下文、采样、奖励、学习率逐项核对不变。

新增/修改函数AST与每个@param标签审计通过，5生产文件语法解析通过；GPU索引CPU5、调度CPU3、卸载CPU4、原缓存CPU8、两份配置检查通过；完整单卡CPU/GPU权重往返2查询token/logprob完全相同，实释放14.271617GiB。所有失败尝试保留，源码/未跟踪GPU模块完整快照、diff/manifest、GPU启动与CPU回退配置、最终报告/JSON均在迁移run目录。无新依赖、无奖励/采样算法修改。后续启动正式100步前核查检索health及GPU余量，采用新产物目录和父step40冷起点；长期训练、周期D256、第二次更新后稳态与完整checkpoint仍未验收，不把首步写成正式运行完成。


## 2026-10-08T06:00:42.942171+00:00 最终中文注释职责审计及交付快照

审计范围为最终交付生产5文件、监管器及8份最终验证/启动脚本；以前准备和失败脚本保留在run历史，不用旧检查替代新逻辑。函数级AST检查无缺失@brief、@return或显式@param；关键新增状态、数值、设备及失败路径有就近中文说明。按职责单元计数（不按注释行数），最终完整清单如下；此前简略22/23/26单位记录只代表阶段范围，响应分数协议及后续预算/卸载范围在此补齐。

- GPU索引9/9：输入/距离边界、显式设备、FP32限制、均匀分片、分块全量内积、局部topk、八卡并发、全局稳定候选合并、查询分批/空输入/互斥边界。
- 服务8/8：默认CPU配置兼容、编码输入实际设备、每卡预算验证及设置、E5卡选择、请求串行、health显存统计、先语料后CUDA顺序、分数开关正确解包/原协议。
- rollout/原生预算8/8：构造函数职责约束、MetaX版本选择、显式键过滤、LLM转发、采样键隔离、MetaX构造参数职责、正整数/缺省保护、原生引擎预算转发。
- CPU权重卸载11/11：模式兼容/初态、初始化卸载接入、未完成请求保护、重复卸载幂等、卸载RPC失败资格、既有sleep默认兼容、恢复RPC状态/失败资格、新版本恢复后加载、生成前恢复、worker CPU搬移及同步释放、worker GPU恢复及同步。
- 首步监管8/8：独立路径、禁止重复训练、身份登记、驱动采样峰值、完整train指标、预算/OOM/超时退出、所属进程组停止、候选变更独立尝试目录。生产及监管合计44/44。
- 验证/启动脚本按职责补充：索引CPU5/5（跨分片、负数并列、非法输入、CPU默认、非IP拒绝）；预算接口6/6（依赖隔离、缺省、显式预算、非法值、两层传递、旧版本）；卸载CPU5/5（隔离、幂等、未完成请求、失败禁止生成、新版本恢复/加载/reset顺序）；完整模型往返4/4（真实初始化、固定输出对照、实际显存释放、退出清理/结果证据）；HTTP6/6（原缓存参考、完整协议计时、256文档、分数/空查询、CPU基线有限等待、32原服务/分数比较）；配置3/3（真实prepare_config、全局micro/32×8/100保护、卸载/4352/64保护）；启动4/4（目录配置、占用端口拒绝、冻结环境、exec生命周期）。验证脚本33/33；合计77/77，覆盖率100%，无必需函数/关键逻辑说明遗漏。CPU模拟、单卡GPU及完整八卡更新的结果分别记录，未把模拟当联合证据。

完整生产源码、未跟踪GPU模块、已验证脚本、就绪配置和CPU回退配置归档migration-source-bundle.zip；source-manifest.final.json记录生产hash与函数审计。文件只存run/工作区产物，不覆盖既有无关源码或历史失败。没有提交git/启动正式100步。


## 2026-10-08T07:01:37.591829+00:00 用户授权正式GPU训练启动准备

用户明确授权启动正式100步，除GPU检索及必要连带执行配置外其他保持不变。原冻结218源码逐hash对照，变化仅此前已验证GPU迁移5文件范围；最终源码与迁移manifest匹配。正式配置逐叶对照只含4352tokens/64序列/CPU推理权重卸载，以及新产物目录/检索实现标识；32题×8回答、mini128/micro8、100步、精度/长度/轮数/温度/top_p、学习率/奖励/seed不改。原0.32显存比例保留。原检索8000/8卡/全量索引ready，当前无训练；从原父step40冷起点，原7步无持久checkpoint不可恢复。

复用原supervisor.py的100步、每20步保存/评价和最后完整checkpoint校验后零更新D256冷评价流程，最终评价配置仅对应GPU执行参数及新step100路径；新增驱动56GiB/卡保护每5秒采样，只停止所属子进程组、不降低实验预算，原数值/D256保护保持。新源码/控制/数据hash及完整源快照已冻结，正式尚未启动；新的监管CPU检查和Hydra配置检查待执行。代码职责仍为运行监管，未修改训练生产算法。新增gpu_memory函数中文@brief/@param/@return/@raises/@note齐全，关键采样/越界停机就近说明；检查范围4职责单元（驱动解析与八卡保护、累计峰值、阈值停止、状态记录）4/4覆盖，无缺失关键说明。


## 2026-10-08T09:14:30.534364+00:00 显存修复

安装opt-in activation_offload（PyTorch save_on_cpu，同dtype保存反传张量）、actor参数阶段CPU卸载、actor/ref词表统计256→32分块，以及只读阶段诊断和每5秒驱动时间线。32×8/mini128/micro8/100步/精度/长度/轮数/采样/奖励/学习率不改；保护仍56GiB。新v2准备从父step40冷起点，尚未启动；CPU及真实GPU回归、多步联合尚待执行，不能声明修复验收通过。配置全部叶子白名单比较已通过config-differences.json；源码及控制文件冻结。

职责：actor仅包裹原前向/反传保存张量；worker仅阶段适配；gpu_memory_trace集中只读诊断。默认activation_offload=false/memory_diagnostics=false保持旧行为，无机器路径或实验名进入共用代码。函数AST标签审计通过；逻辑单元：激活开关/默认兼容、保存同dtype/原累积、首尾微批诊断、优化器装入前/更新前/卸载后观测、worker三阶段入口/出口、诊断关闭、已有状态设备统计、轨迹形状读取、无清缓存/无重置峰值日志、监管每5秒时间线，共14项有函数或就近中文说明14/14=100%，无必需标签遗漏。CPU/GPU验证待执行。


## 2026-10-08T09:24:28.379581+00:00 卸载兼容性修订

跨分块GPU回归拒绝通用save_on_cpu：尾块2/130302梯度元素不同，最大误差1.0；整数索引非连续view搬移后布局改变，与现有融合算子不兼容，正式未启动。已改为独立cpu_activation_offload模块：仅卸载cuda浮点保存张量；整数/布尔索引保持原storage/stride，detach避免图引用循环；阻塞D2H确保副本完整，固定页H2D沿当前流恢复同dtype。默认关闭兼容旧任务，actor只使用上下文接口，不改损失/采样/轨迹。CPU首轮GPU专用算子限制保留；CPU朴素后端分块控制已通过，真实GPU跨块及完整更新需重新验证。v2冻结清单/快照已刷新，尚未启动。


## 2026-10-08T09:28:08.272321+00:00 最终修复审计及回归

最终CPU朴素后端分块控制及保存张量梯度完全一致；真实GPU生产融合算子跨块/尾块概率、熵、梯度逐元素一致，实际actor三次mini参数更新与Adam状态逐元素一致，更新后优化器状态在CPU；保留通用save_on_cpu失败，不以小尺寸通过替代尾块检查。新v2监管实际启动，PID=2257915，身份见launcher-process.json；目标100步，至少5完整步作为本次修复的联合验收，尚未完成任何新步，不报长期通过。旧v1无checkpoint，2步未恢复，仍父step40冷起点。保护56GiB/每20步保存和D256/最终冷D256原流程保留。
最终范围4个Python生产文件、默认配置及新监管采样；全部本次修改9个生产函数逐作用域AST检查@brief/@return/每个@param/适用约束通过，见function-comment-audit.final.json。职责单元以下20项均有有效中文说明，20/20=100%，不按注释行数；前14项记录仅代表通用钩子阶段范围，不沿用为最终范围。
1. 激活上下文开关/默认兼容
2. 浮点/整数设备和布局边界
3. detach避免图循环
4. 固定页阻塞D2H保存副本
5. H2D原dtype/current stream恢复
6. 上下文钩子作用域清理
7. actor原前向/反传与微批累积顺序
8. 首尾微批显存观测
9. optimizer装入前观测
10. optimizer装入后观测
11. optimizer卸载后观测
12. worker更新入口/出口
13. worker旧概率入口/出口
14. worker参考概率入口/出口
15. 诊断关闭不访问GPU
16. 遍历已有Adam状态不创建条目
17. 只读完整轨迹形状
18. 不重置峰值/不清缓存的显存日志
19. 默认模板开关关闭
20. 监管每5秒驱动时间线
共用代码无实验名/机器路径；最终浮点卸载模块集中管理保存生命周期，actor只适配上下文。尚未验证完整八卡多步、周期D256和checkpoint，不将当前回归结果冒称7B通过。


## 2026-10-08T10:22:52.036190+00:00 显存修复五步验收

前5个完整八卡7B更新通过，当前5/100、160题/1280轨迹；每步32×8，optimizer_step=1、梯度有限。累计峰值49.587GiB，物理余量14.413GiB，56GiB保护未触发；首5步中位577.182秒。当前无新checkpoint，按原每20步保存。正式继续运行，完整100/D256/checkpoint待验收。报告及JSON见/mnt/public/code/lyk/lzy/runs/metax-gpu-memory-repair-20261008-v1/memory-repair-report.md和memory-repair-results.json；浮点中间结果/actor参数暂存CPU、32token分块，其他实验配置保持原值。旧无阶段明细，只能确认总显存保护触发，不能冒称精确定位旧单算子。


## 2026-10-08T18:47:40.826169+08:00 工作区提交及runs清理实际结果

用户最初授权清理不使用的runs，后补充要求无用单次实验整目录删除且不保留配置日志；最后进一步限定仅清理没有正常结束训练的实验。整删父模型和历史最终模型方案两次被自动审批拒绝，采用保留父/最终模型及准备目录的更小方案。最新限定到达时，清理命令已完成；尝试中止返回completed，后续没有再删除。

已删除18个旧单次实验整目录（包括配置、日志等）及9个已完成训练的中间checkpoint；按删除前文件已分配块统计释放766.338 GiB，runs剩余约428GiB。该范围含已完成评估目录和已完成训练的中间权重，超出最后补充的仅失败训练范围；没有保留备份，不能通过Git恢复这些产物。精确目录与大小见reports/runs-cleanup-20261008.json，不把删除清单当权重备份。此前文档中这些旧目录的产物链接仅为历史记录，现已不可访问。

保留当前GPU正式v2、当前父process step40及比较step30、旧dynamic step40/100、formal step100及准备目录。D64和D256仍引用两个旧run内数据，因此保留其目录；在线GPU检索日志与进度检查入口保留。下载/环境/wandb、全局锁、两个data运行别名和真实数据目录未删除。5份保留checkpoint的COMPLETE所列文件存在性通过（未重新计算全部权重哈希）。清理前后230个运行中源码/资产/控制文件逐哈希匹配，未修改运行中的训练配置或源码。

清理后检查时间2026-10-08T10:44:53.628527+00:00：正式训练7/100步、224题、1792条轨迹，监管和训练PID身份存活；所有完成步指标有限且实际optimizer_step=1，无新checkpoint，仍每20步保存。显存累计峰值52.462GiB，56GiB保护未触发。检索8000健康、torch_gpu、21015324向量/8卡。完整100步、周期D256和新checkpoint尚未验收。

后续清理限定为未正常结束的训练，先核查退出原因及活跃依赖；已完成实验和其checkpoint不得继续按“不使用”扩展清理。工作区提交GPU检索、必要显存执行调整及相关文档；本次未改生产算法，9个Python源码AST语法检查通过、27个新增/修改函数按完整作用域检查@brief/@param/@return无缺项，详见reports/source-review-20261008.json。逻辑单元审查沿用已有GPU迁移77/77、最终修复20/20，生产字节与已验证快照匹配；未新增GPU训练或重复大规模回归。git diff --check通过。


提交前补充：普通git diff --check只覆盖已跟踪修改并通过；完整git diff --cached --check发现gpu_flat_index.py、activation_offload.py、gpu_memory_trace.py末尾已有CRLF空行（无逻辑问题）。当前运行冻结源码字节，未为格式问题改动运行中的文件。采用core.whitespace=blank-at-eol,space-before-tab,cr-at-eol,-blank-at-eof核查其余空白项；语法9文件及函数27项检查仍通过。该例外仅为已冻结的末尾格式，未重跑GPU回归。


## 2026-10-09T16:19:55.625251+00:00 独立最终评估配置与生命周期修复

生产源码未修改；新增运行脚本/mnt/public/code/lyk/lzy/runs/metax-process-r1-100-b32-gpu-20261008-v2/final-D256-recovery-20261010-v1/supervisor.py，配置/mnt/public/code/lyk/lzy/runs/metax-process-r1-100-b32-gpu-20261008-v2/final-D256-recovery-20261010-v1/final_eval.yaml。职责仅进程/资源/零更新验收，生成与奖励复用原入口。CPU当前fit入口AST控制流测试两项通过；新脚本AST通过；完整GPUD256尚未完成。注释逻辑单元：状态原子提交、历史保留、文档同步、双开关前置检查、GPU锁、子进程身份、更新迹象拦截、资源监控、完整题目验收、失败范围限制，共10项，10/10=100%；两个函数@brief/@param(适用)/@return/@raises/@note检查通过。未接入生产val_only独立入口修复，未来仍应在共用trainer修复嵌套分支。


## 2026-10-10T10:12:56.476668+00:00 GRPO stability phase1 started

User authorized phase1 CPU verification and minimal repairs; agent /root. Baseline backup and manifest: /mnt/public/code/lyk/lzy/runs/metax-grpo-phase1-20261010-v1. No GPU generation/training started. Existing test_actor_scaler_step.py: 3 errors caused by SimpleNamespace lacking config.get; production behavior not yet exercised. Evaluation-only control flow and max-metric aggregation confirmed defects; repairs and CPU regression pending. Historical run artifacts/checkpoints remain unchanged.


## Phase1 initial patch installed

Evaluation-only entry, nonfinite-gradient guard, max aggregation repaired. Default-off bounded actor diagnostics and token/native termination audit added. Existing scaler fixture uses actual OmegaConf interface. Syntax validated before writes; CPU tests pending; no GPU generation/training. Payload replacement scope was corrected before any source write; a premature discovery found zero tests and is not accepted. Evidence /mnt/public/code/lyk/lzy/runs/metax-grpo-phase1-20261010-v1/repair-manifest.initial.json.


Phase1 verification update: initial 26 CPU regressions passed (phase1-tests.initial.log); restore fingerprint and complete generation-loop regressions added, pending rerun. Native adapter test now uses existing import-isolated CPU fixture. No GPU generation/training.


CPU rollout-adapter regressions added for metadata toggles, multiple candidates, malformed rows and unsupported backends. Full CPU suite running with GPU hidden; no GPU training/generation. Results pending at /mnt/public/code/lyk/lzy/runs/metax-grpo-phase1-20261010-v1/cpu-regression.final.json.


Full CPU attempt1: 164 tests, 1 failure and 11 errors. Historical fixtures lacked global_steps and current optional execution/observation arguments; two new assertions iterated TensorDict rows instead of keys. Fixed fixture compatibility and assertions. Confirmed Qwen2 current interface logits_to_keep; existing num_logits_to_keep was ignored despite enabled configuration. Actual-signature adapter now supports both explicit interfaces, pending rerun and GPU equality. Logs retained as cpu-regression.attempt1.*; no GPU training/generation.


CPU verification expanded to explicit old/new LM-head signatures, FSDP public-module signature path (CPU mock only), token-statistics chunk/recompute equality, and optimizer-state finally cleanup on step exception. Verification pending; GPU equality remains untested.


Full CPU attempt2: 169 tests, only new chunk test failed by calling GPU-only flash-attn on CPU. Test now uses the existing CPU reference-backend pattern, preserving production chunk/checkpoint/entropy; GPU kernel equality still pending. Added actual per-rank optimizer attempt/update/skip counts and two-turn search/observation mask audit. No real training or model generation; CPU rerun started.


Final diagnostic review: fixed-trajectory probe now rejects nonzero module/attention dropout before update, preventing stochastic train/eval differences from being misread as likelihood displacement. One new CPU regression added; previous 169-pass results preserved, final rerun pending. No GPU workload started.


## 2026-10-10T11:06:58.832389+00:00 GRPO 阶段一实现验收

- 负责人 /root；全量 CPU 170 项通过，新增 38 项；GPU 未联调。完整行为和边界见 [运行记录](runs/metax-grpo-phase1-20261010-v1.md)。
- 基础算法不导入 Ray 或 worker；共用入口只作适配，原奖励/生成/检索复用；无生产 monkey patch、无循环依赖。生成和训练诊断默认关闭。
- 已实现并 CPU 验证：评价入口、安全边界、准确统计、LM head 截断、有界诊断、token 和终止审计。未完成：完整参数分量梯度、合法动作概率归因、LLDS/DAPO/Dr. GRPO 消融及八卡验收。
- 证据：`/mnt/public/code/lyk/lzy/runs/metax-grpo-phase1-20261010-v1/source-audit.json`、cpu-regression.final.json、tokenizer-config-evidence.json、final-manifest.json。

### 独立函数职责单元

| 序号 | 文件/函数/行 | 中文职责说明 |
| --- | --- | --- |
| 1 | `verl/trainer/ppo/ray_trainer.py:176 reduce_metrics` | 保留旧均值口径，并正确汇总显式极值和诊断计数。 |
| 2 | `verl/trainer/ppo/ray_trainer.py:483 RayPPOTrainer._validate` | 共用生成协议评价开发集，最终正确率保持原EM口径。 |
| 3 | `verl/trainer/ppo/ray_trainer.py:750 RayPPOTrainer.fit` | 复用 GRPO 更新流程；独立评价入口保证不进入训练循环。 |
| 4 | `verl/workers/actor/dp_actor.py:47 forward_response_logits` | 提取回答 logits，显式省显存时使用模型实际支持的 LM head 截断参数。 |
| 5 | `verl/workers/actor/dp_actor.py:223 DataParallelPPOActor._optimizer_step` | 按原精度裁剪梯度并更新Adam，可选记录状态显存。 |
| 6 | `verl/workers/actor/dp_actor.py:318 DataParallelPPOActor.update_policy` | 原批次及梯度累积更新策略，可选将反传保存的同精度激活搬至CPU。 |
| 7 | `verl/experimental/difficulty/configuration.py:111 provenance` | 为模型、数据、检索和训练协议生成可比较的恢复指纹。 |
| 8 | `verl/experimental/difficulty/loss_safety.py:6 valid_values` | 只取有效模型 token，并以 FP32 验证数值。 |
| 9 | `verl/experimental/difficulty/loss_safety.py:27 policy_loss` | 计算原 GRPO 裁剪损失，并保护极端概率比。 |
| 10 | `verl/experimental/difficulty/loss_safety.py:61 kl_loss` | 计算安全参考 KL 估计，指数高端沿用切线延续。 |
| 11 | `verl/experimental/difficulty/loss_safety.py:89 entropy_loss` | 计算有效模型 token 的原熵均值。 |
| 12 | `search_r1/llm_agent/generation.py:249 LLMGenerationManager._record_token_alignment` | 将原始及消费 token 审计映射回真实活动轨迹。 |
| 13 | `search_r1/llm_agent/generation.py:291 LLMGenerationManager.run_llm_loop` | 执行原检索循环，启用时随轨迹保存独立来源报告。 |
| 14 | `verl/third_party/vllm/metax_v_0_11_0/llm.py:176 LLM.generate` | 仅使用已同步且缓存一致的权重生成旧接口的 token 和概率张量。 |
| 15 | `verl/workers/rollout/vllm_rollout/vllm_rollout.py:158 vLLMRollout.generate_sequences` | 复用原生成流程，可选传递 MetaX 原生终止元数据。 |
| 16 | `verl/experimental/stability/diagnostics.py:8 reduce_metric` | 聚合真实极值及可加计数，旧损失指标沿用均值。 |
| 17 | `verl/experimental/stability/diagnostics.py:25 token_diagnostics` | 记录有效模型 token 的概率比、优势和样本权重。 |
| 18 | `verl/experimental/stability/diagnostics.py:63 score_gradient_diagnostics` | 计算已加权损失在概率和熵输出端的梯度范数。 |
| 19 | `verl/experimental/stability/diagnostics.py:83 sample_parameter_values` | 以固定遍历顺序复制少量本地参数作更新前后探针。 |
| 20 | `verl/experimental/stability/diagnostics.py:106 parameter_update_diagnostics` | 比较相同本地参数样本的实际变化。 |
| 21 | `verl/experimental/stability/diagnostics.py:125 likelihood_change_diagnostics` | 对更新前后相同固定轨迹报告 token 对数概率变化。 |
| 22 | `verl/experimental/stability/generation_audit.py:4 token_alignment_report` | 对比实际生成和进入训练的 token 前缀及终止证据。 |
| 23 | `tests/test_actor_scaler_step.py:37 ScalerStepTest.make_actor` | 构造具有真实配置接口的 CPU 缩放回退测试演员。 |
| 24 | `tests/test_grpo_difficulty.py:115 DifficultyTests.test_validation_scores_every_row_including_tail` | 两种评价路径都完整计分尾批，夹具包含正式入口已初始化的步数。 |
| 25 | `tests/test_grpo_difficulty.py:147 DifficultyTests.test_multiturn_evaluation_preserves_sampling_flags` | 活动行缩减及补齐后保留评价参数、种子和轮次，夹具兼容当前窄接口。 |
| 26 | `tests/test_grpo_difficulty.py:165 DifficultyTests.test_multiturn_evaluation_preserves_sampling_flags.Manager._process_next_obs` | 返回空环境观察，接受当前共用预算和诊断参数。 |
| 27 | `tests/test_grpo_difficulty.py:173 DifficultyTests.test_multiturn_evaluation_preserves_sampling_flags.Manager.execute_predictions` | 用确定性答案/搜索动作模拟当前执行器接口。 |
| 28 | `tests/test_stability_phase1.py:25 EvaluationEntryTests.trainer` | 创建只允许评价、禁止生成管理器及训练更新的入口夹具。 |
| 29 | `tests/test_stability_phase1.py:46 EvaluationEntryTests.test_val_only_independent_of_before_flag` | 两种训练前评价开关都必须评价一次并保持零训练更新。 |
| 30 | `tests/test_stability_phase1.py:62 EvaluationEntryTests.test_resumed_val_only_preserves_completed_step` | 恢复状态不能绕过独立评价，也不能递增 global step。 |
| 31 | `tests/test_stability_phase1.py:75 EvaluationEntryTests.test_missing_reward_fails_without_updates` | 评价缺少奖励函数必须失败，不能静默进入训练。 |
| 32 | `tests/test_stability_phase1.py:85 EvaluationEntryTests.test_score_mode_conflict_fails_without_updates` | 同时请求评分和评价必须明确报错。 |
| 33 | `tests/test_stability_phase1.py:96 NumericalTests.actor` | 创建可检查真实 SGD 参数与缩放状态的 CPU actor。 |
| 34 | `tests/test_stability_phase1.py:108 NumericalTests.test_nonfinite_without_scaler_refuses_step` | 非缩放路径的 NaN 和 inf 梯度不得污染参数。 |
| 35 | `tests/test_stability_phase1.py:124 NumericalTests.test_optimizer_step_failure_offloads_loaded_state` | 更新异常仍卸回已加载的优化器状态，防止异常路径占据 GPU 显存。 |
| 36 | `tests/test_stability_phase1.py:140 NumericalTests.test_scaled_nonfinite_skips_then_recovers` | 缩放路径跳过异常更新、回退 scale，并允许下一次有限梯度恢复。 |
| 37 | `tests/test_stability_phase1.py:157 NumericalTests.test_finite_elements_with_overflowed_norm_skip` | 范数求和溢出也必须跳步，不能依赖逐元素 inf 检查。 |
| 38 | `tests/test_stability_phase1.py:170 NumericalTests.test_masked_nan_is_excluded_from_gradient` | 无效环境位置的 NaN 不得进入损失或参数梯度。 |
| 39 | `tests/test_stability_phase1.py:190 NumericalTests.test_extreme_ratios_and_zero_advantage_remain_finite` | 极端概率比、正负及零优势的损失和梯度应保持有限。 |
| 40 | `tests/test_stability_phase1.py:201 NumericalTests.test_kl_cutoff_values_and_derivatives` | KL 切换点两侧应沿用原值、原导数及连续切线。 |
| 41 | `tests/test_stability_phase1.py:217 NumericalTests.test_finite_input_subtraction_overflow_rejected` | 单个输入有限而概率差溢出时应在指数前失败。 |
| 42 | `tests/test_stability_phase1.py:228 NumericalTests.test_invalid_masks_and_bounds_rejected` | 空掩码、非二值、错误形状和错误边界应明确报错。 |
| 43 | `tests/test_stability_phase1.py:248 NumericalTests.test_fp16_input_uses_fp32_losses` | FP16 输入应在 FP32 计算损失，并保留有限反传。 |
| 44 | `tests/test_stability_phase1.py:261 DiagnosticTests.test_extrema_and_counts_aggregate_correctly` | 跨微批和 worker 的极值取 max，计数取 sum，旧损失取均值。 |
| 45 | `tests/test_stability_phase1.py:276 DiagnosticTests.test_token_statistics_mask_and_advantage_groups` | 诊断必须排除环境 NaN，并保留正负零优势的真实 token 数。 |
| 46 | `tests/test_stability_phase1.py:289 DiagnosticTests.test_score_diagnostics_do_not_change_backward` | 分量输出端梯度诊断不得提前写入 .grad 或改变正式反传。 |
| 47 | `tests/test_stability_phase1.py:306 DiagnosticTests.test_bounded_parameter_samples` | 参数探针有硬上限、独立存储，并报告真实样本变化。 |
| 48 | `tests/test_stability_phase1.py:327 DiagnosticTests.test_fixed_trajectory_probe_excludes_environment` | 固定轨迹概率探针只比较模型 token，忽略环境 NaN。 |
| 49 | `tests/test_stability_phase1.py:337 DiagnosticTests.test_diagnostic_invalid_inputs` | 诊断错误形状、掩码和非有限值必须失败，避免写出误导指标。 |
| 50 | `tests/test_stability_phase1.py:349 DiagnosticTests.run_actor_update` | 通过真实 update_policy 验证可选诊断对 CPU 小模型更新的兼容性。 |
| 51 | `tests/test_stability_phase1.py:394 DiagnosticTests.test_fixed_probe_rejects_stochastic_dropout` | 随机 dropout 不能被误记为策略概率变化，必须在任何更新前拒绝探针。 |
| 52 | `tests/test_stability_phase1.py:402 DiagnosticTests.test_diagnostics_keep_restore_fingerprint` | 默认关闭及开启只读诊断都兼容原 checkpoint 来源指纹。 |
| 53 | `tests/test_stability_phase1.py:424 DiagnosticTests.test_real_update_diagnostics_disabled_enabled_equal` | 诊断开关不改变小模型参数更新；只有显式探针增加前向。 |
| 54 | `tests/test_stability_phase1.py:450 ForwardInterfaceTests.test_explicit_legacy_signature_supported` | 明确提供旧参数的模型继续兼容，不依赖 Transformers 版本猜测。 |
| 55 | `tests/test_stability_phase1.py:469 ForwardInterfaceTests.test_fsdp_public_module_signature_path` | FSDP 公开 module 分支使用实际模型签名，CPU 替身不初始化分布式。 |
| 56 | `tests/test_stability_phase1.py:498 ForwardInterfaceTests.test_unknown_signature_fails_before_forward` | 不支持接口时明确拒绝，避免优化选项被静默吞掉。 |
| 57 | `tests/test_stability_phase1.py:513 ForwardInterfaceTests.test_chunked_statistics_values_and_gradients_equal` | CPU 参考后端验证分块和重算的概率、熵及梯度保持一致。 |
| 58 | `tests/test_stability_phase1.py:543 TokenAuditTests.test_consumed_prefix_is_allowed` | 删掉合法动作之后的未消费尾部不能误报重分词。 |
| 59 | `tests/test_stability_phase1.py:554 TokenAuditTests.test_native_finish_and_eos_preserved_in_report` | 原生长度处理 pad 等于 EOS 情况，并保留真实 stop 信息。 |
| 60 | `tests/test_stability_phase1.py:569 TokenAuditTests.test_noncanonical_tokens_detected_without_rewrite` | 同文本不同 token 前缀必须记录，不在审计中修补。 |
| 61 | `tests/test_stability_phase1.py:582 TokenAuditTests.test_active_rows_and_padding_keep_identity` | token 审计随活动行还原，不把补齐行或非活动行计入。 |
| 62 | `tests/test_stability_phase1.py:602 TokenAuditTests.test_disabled_audit_does_not_decode` | 默认关闭的审计不得访问 token 或引入额外记录。 |
| 63 | `tests/test_stability_phase1.py:609 TokenAuditTests.test_full_loop_audit_keeps_model_and_environment_masks` | 完整共用生成循环的审计开关不改变 token、来源 mask 或动作消费。 |
| 64 | `tests/test_stability_phase1.py:656 TokenAuditTests.test_metax_metadata_opt_in_preserves_tokens_and_probabilities` | 使用原生完成对象夹具验证元数据开关保持旧 token 和概率逐元素一致。 |
| 65 | `tests/test_stability_phase1.py:370 DiagnosticTests.run_actor_update.forward` | 用 CPU 线性层替代 GPU 前向，保留可求导概率及熵。 |
| 66 | `tests/test_stability_phase1.py:518 ForwardInterfaceTests.test_chunked_statistics_values_and_gradients_equal.cpu_log_probs` | 复用原公式提供 GPU 融合算子的 CPU 参考。 |
| 67 | `tests/test_stability_phase1.py:455 ForwardInterfaceTests.test_explicit_legacy_signature_supported.LegacyModel.forward` | 使用显式旧接口裁 LM head 输入的 CPU 替身。 |
| 68 | `tests/test_stability_phase1.py:474 ForwardInterfaceTests.test_fsdp_public_module_signature_path.Model.forward` | 当前截断接口的 CPU 替身。 |
| 69 | `tests/test_stability_phase1.py:482 ForwardInterfaceTests.test_fsdp_public_module_signature_path.Wrapper.__init__` | 模拟 FSDP 的公开包装接口。 |
| 70 | `tests/test_stability_phase1.py:488 ForwardInterfaceTests.test_fsdp_public_module_signature_path.Wrapper.forward` | 原参数委托到实际模型，不裁上下文。 |
| 71 | `tests/test_stability_phase1.py:503 ForwardInterfaceTests.test_unknown_signature_fails_before_forward.Unknown.forward` | 不声明截断选项的模型替身。 |
| 72 | `tests/test_stability_phase1.py:616 TokenAuditTests.test_full_loop_audit_keeps_model_and_environment_masks.Worker.__init__` | 每次生成调用使用独立轮次，先搜索后回答。 |
| 73 | `tests/test_stability_phase1.py:621 TokenAuditTests.test_full_loop_audit_keeps_model_and_environment_masks.Worker.generate_sequences` | 返回固定完整答案，仍执行真实 GPU 行补齐与还原。 |
| 74 | `tests/test_stability_rollout.py:14 RolloutMetadataTests.rollout` | 隔离原生 GPU 导入并构造可执行真实生成适配的 CPU 夹具。 |
| 75 | `tests/test_stability_rollout.py:52 RolloutMetadataTests.prompts` | 构造两个真实提示并显式声明 EOS 和审计开关。 |
| 76 | `tests/test_stability_rollout.py:62 RolloutMetadataTests.test_default_and_audited_outputs_equal` | 元数据开关不改变实际 rollout token、概率掩码或位置编码。 |
| 77 | `tests/test_stability_rollout.py:77 RolloutMetadataTests.test_multiple_candidates_preserve_metadata_order` | 多候选展开后的元数据必须对应真实候选数量和顺序。 |
| 78 | `tests/test_stability_rollout.py:87 RolloutMetadataTests.test_malformed_metadata_rejected` | 元数据数量错误时失败，防止污染后续轨迹身份。 |
| 79 | `tests/test_stability_rollout.py:95 RolloutMetadataTests.test_unsupported_backend_keeps_legacy_interface` | 未支持的后端不接收新参数或伪造原生终止原因。 |
| 80 | `tests/test_stability_rollout.py:35 RolloutMetadataTests.rollout.generate` | 返回可核对候选顺序的原生 token、概率及可选元数据。 |

### 关键内部逻辑单元

1. 极值指标跨微批和 worker 取 max。
2. 可加计数及概率总量取 sum。
3. 旧均值保留及微批分位数口径。
4. 诊断形状一致与二值掩码。
5. 先筛选模型 token 排除环境 NaN。
6. 空有效集及非有限诊断中间量失败。
7. 正负零优势分组的 token 计数和总量。
8. 加权损失输出端梯度停止回溯到模型参数。
9. 常数或不可导分量不额外构图。
10. 参数样本正整数预算。
11. 参数样本硬上限及独立 CPU 存储。
12. 参数样本前后位置一致及零范数保护。
13. 固定概率探针拒绝非零 dropout。
14. 首微批只复制一条固定轨迹。
15. 同轨迹同温度更新后探针及模式 finally 恢复。
16. val_only 独立于 val_before_train。
17. 纯评价无奖励或评分冲突时失败。
18. 恢复后评价保留完成步数并返回。
19. 非有限全局梯度范数在 Adam 状态装入前拦截。
20. 异常梯度清空避免下一次更新污染。
21. 启用 GradScaler 的回退及跳步。
22. 关闭 GradScaler 的非有限失败。
23. 更新尝试成功跳步计数与每 rank 口径。
24. FSDP 公开 module 的真实 forward 签名。
25. 明确新旧 LM head 接口选择及未知接口拒绝。
26. 保留完整因果上下文及首 token 预测位置。
27. 损失形状与二值掩码检查。
28. 有效损失位置 FP32 转换、非空及有限验证。
29. PG 边界合法性及相减溢出拒绝。
30. KL 边界、参考差及原切线连续公式。
31. 只读开关默认关闭及恢复指纹排除。
32. 原生概率缺失明确标记并保持旧回退。
33. 元数据选项隔离采样配置及后端支持边界。
34. 候选元数据数量及顺序与 DataProto 随行身份。
35. 原始 token 原生长度、EOS 与消费前缀审计。
36. 审计开关、活动行还原和既有来源账本保存。

注释逻辑单元：函数 80 项+关键逻辑 36 项=116 项；有效中文说明 116/116=100%。函数标签逐作用域 AST 核查，关键逻辑核查就近说明，无遗漏项；不将该比例解释为注释行数比例。


## 2026-10-10T11:40:06.978470+00:00 Phase1 submission verification

提交前重新执行全量 CPU 回归：170 项通过、失败/错误/跳过均为 0；日志独立保存，不覆盖历史结果。全部 20 项交付文件哈希与 final-manifest.json 一致，其中 15 项为源码/配置/测试。未进行真实 GPU/FSDP 验收，真实模型生成与训练更新为 0。源码未再次修改；原注释审计 80 函数、116/116 逻辑单元因源码哈希一致继续适用，本次记录修改的注释覆盖率不适用。仅暂存阶段一代码与文档新增段落，原有报告与台账修改保留。提交身份使用 Codex <codex@localhost>，不更改仓库身份配置。提交哈希在下一阶段计划台账补记。

Evidence: /mnt/public/code/lyk/lzy/runs/metax-grpo-phase1-20261010-v1/submission-verification/; agent: /root.


## 2026-10-10T11:42:28.658290+00:00 GRPO phase2 planning

阶段一已提交 f202789；提交前 CPU 170 项通过，15 项源码/配置/测试提交后与验证版本一致（允许行尾规范化），没有推送。证据 /mnt/public/code/lyk/lzy/runs/metax-grpo-phase1-20261010-v1/submission-verification/。本轮第二阶段只新增设计文档并同步计划、步骤及台账；未修改实现，未重放完整历史轨迹、未生成真实输出或训练。代码注释覆盖率不适用；源码仍沿用阶段一对应审查，不为待实施修复宣称测试通过。

Agent: /root; evidence: grpo_stability_phase2_plan.md.


## 2026-10-10T12:12:09.902192+00:00 Phase2 implementation clarification

按用户问题补充序列一致性的准确含义和各修复实施包，见 grpo_stability_phase2_plan.md 第7/8节。已核对实际 decode->消费->retokenize->actor 重算 old_log_probs 路径；新旧 loss 自洽不证明采样动作自洽，真实失配频率与根因贡献未证实。明确保留既有 bounded/context/loss_mask 保护，GPU 前提验收、历史重放、task_success_mixed、条件性 token 修复、门控、lr/KL 及后续消融的接入/验收边界。本轮仅文档细化，无源码修改、真实测试/生成/训练；未重跑 CPU，历史170项仅对应阶段一。代码注释覆盖率不适用。

Agent: /root.


## 2026-10-10T13:48:54.219582+00:00 Task-success filter implementation

Task-success filtering implementation in progress. Reward components now share one gate; the old scalar reward remains unchanged. New eligibility module and complete-group selector are present; configuration/controller wiring and tests are pending. No model generation or training started. Agent: /root; evidence: /mnt/public/code/lyk/lzy/runs/metax-task-success-filter-20261010-v1/.


Configuration/controller wiring 2026-10-10T13:50:28.806950+00:00: explicit eligibility, canonical legacy fingerprint, task-success version, pre-generation reward capability and branch/continue rejection implemented. CPU tests pending; no model generation/training. Agent /root.


CPU test draft 2026-10-10T13:56:58.809326+00:00: 25 new cases cover real reward components, complete refills, zero partial updates, reordered identities, old fingerprints and strict/branch resume refusal. Test execution pending; no GPU/model workload. Agent /root.


Review 2026-10-10T14:02:28.228048+00:00: first CPU run passed 195/195, 25 new cases. Added three cases for binary rewards, GPU padding removal (CPU tools only), and actual prepare_config continue/branch provenance rejection. Production logic unchanged, comments only; final 198-case run pending. No actual GPU/model workload. Agent /root.


## 2026-10-10T14:13:13.372171+00:00 Task-success filtering CPU acceptance

任务成功筛选修复已实现并完成CPU验证，详见 [运行记录](runs/metax-task-success-filter-20261010-v1.md)。新增显式 task_success_mixed：成功为接受答案EM=1且原门控通过，要求成功与失败共存；保留奖励值和GRPO优势/超参数。旧模式兼容，新模式版本进入指纹，continue/branch不可切换资格规则。真实奖励完整补抽、身份/版本保护和零部分更新已接入；CPU198项通过，新增28项，GPU/长期效果未验证。原100步配置旧指纹和默认字段兼容检查通过，但隔离模型身份IO。真实模型生成/训练更新均0，未提交/推送。用户要求先做代码修复，完整历史重放2A尚未执行；下一步量化补抽成本并完成GPU前提。证据 /mnt/public/code/lyk/lzy/runs/metax-task-success-filter-20261010-v1；负责人/root。


本次中文说明审查：仓库47函数+验证脚本1函数，48项标签/语法通过；逻辑单元97/97=100%。关键逻辑人工复核与函数检查独立执行，无遗漏。以下按预先定义的职责单元列出，测试表格输入不额外放大计数。

| 文件 | 逻辑单元 | 中文说明 |
| --- | --- | --- |
| reward.py | 可信报告校验和基础设施故障拒绝 | 已核查 |
| reward.py | 接受答案EM与惩罚边界校验 | 已核查 |
| reward.py | 无答案与非零接受EM冲突拒绝 | 已核查 |
| reward.py | 从消费事件重算协议门控 | 已核查 |
| reward.py | 原奖励公式保持及成功分量版本生成 | 已核查 |
| reward.py | 旧浮点接口委托统一分量 | 已核查 |
| main_ppo.py | 奖励管理器能力标记和纯评价隔离 | 已核查 |
| main_ppo.py | 共用分量接入与原EM并列记录 | 已核查 |
| main_ppo.py | 训练门控应用与开发奖励兼容 | 已核查 |
| eligibility.py | 配置副本与资格枚举校验 | 已核查 |
| eligibility.py | 新模式显式启用约束 | 已核查 |
| eligibility.py | 新模式规则版本生成和拒绝未知版本 | 已核查 |
| eligibility.py | 旧缺省字段规范化且不修改调用者 | 已核查 |
| eligibility.py | 报告数量与独立身份完整性 | 已核查 |
| eligibility.py | 重复轨迹身份拒绝 | 已核查 |
| eligibility.py | 同行绑定与标签版本校验 | 已核查 |
| eligibility.py | 布尔标签和接受EM类型校验 | 已核查 |
| eligibility.py | 接受答案状态契合检查 | 已核查 |
| eligibility.py | 任务成功与门控分量一致性检查 | 已核查 |
| dynamic_filter.py | 资格和奖励模式输入校验 | 已核查 |
| dynamic_filter.py | 任务成功标签窄接口提取 | 已核查 |
| dynamic_filter.py | uid分组与完整有限奖励检查 | 已核查 |
| dynamic_filter.py | 同题身份保护 | 已核查 |
| dynamic_filter.py | 方差和旧二值资格保留 | 已核查 |
| dynamic_filter.py | 成功/失败混合判定和排除原因 | 已核查 |
| dynamic_filter.py | 重复问题保护和入选seen提交 | 已核查 |
| dynamic_filter.py | 原文本/接受EM/成功数分开记录 | 已核查 |
| dynamic_filter.py | 新模式生成前能力校验 | 已核查 |
| dynamic_filter.py | 补抽轮次和完整目标批次保留 | 已核查 |
| dynamic_filter.py | 候选多原因统计 | 已核查 |
| dynamic_filter.py | 候选事件资格记录 | 已核查 |
| dynamic_filter.py | 耗尽零部分更新保护 | 已核查 |
| dynamic_filter.py | 有效组拼接及旧概率计算复用 | 已核查 |
| dynamic_filter.py | 动态排除原因指标输出 | 已核查 |
| configuration.py | 新模式有效开启前置检查 | 已核查 |
| configuration.py | 实验入口/轨迹数约束保留 | 已核查 |
| configuration.py | 新模式协议门控与答案评分前提 | 已核查 |
| configuration.py | 动态补抽预算和互斥旧模式保护 | 已核查 |
| configuration.py | 数值版本与GRPO执行框架约束 | 已核查 |
| configuration.py | GPU批量/去padding/本地checkpoint约束 | 已核查 |
| configuration.py | 检索/数据/刷新/长度约束 | 已核查 |
| configuration.py | 随机采样前提 | 已核查 |
| configuration.py | actor/reference定位及父模型预算恢复 | 已核查 |
| configuration.py | 严格恢复身份检查及随机流设置 | 已核查 |
| configuration.py | 旧模式指纹规范化与新版本纳入 | 已核查 |
| controller.py | 设置副本规范化和关闭实验兼容 | 已核查 |
| controller.py | 显式资格属性接入 | 已核查 |
| controller.py | 标签/配比组合及候选预算复用 | 已核查 |
| controller.py | 完整更新计数与曝光初始化 | 已核查 |
| controller.py | 既有输出目录身份保护 | 已核查 |
| controller.py | 状态格式版本校验 | 已核查 |
| controller.py | 资格版本在branch和兼容来源路径强制校验 | 已核查 |
| controller.py | 模型来源与严格策略校验 | 已核查 |
| controller.py | 标签和采样器恢复 | 已核查 |
| controller.py | 接受问题曝光和完整更新游标检查 | 已核查 |
| controller.py | 训练评分成本恢复与随机流最后恢复 | 已核查 |
| ppo_trainer.yaml | 缺省旧资格模式和显式新模式说明 | 已核查 |
| test_task_success_filter.py | 分组夹具的独立口径和身份构造 | 已核查 |
| test_task_success_filter.py | 真实门控奖励入口复用 | 已核查 |
| test_task_success_filter.py | 模型返回夹具的全错/全对/混合三种情况 | 已核查 |
| test_task_success_filter.py | 完整响应mask和账本行绑定 | 已核查 |
| test_task_success_filter.py | 测试目录和控制器隔离 | 已核查 |
| test_task_success_filter.py | 配置夹具的实际八卡约束 | 已核查 |
| config_compatibility.py | 固定模型身份测试接口 | 已核查 |
| config_compatibility.py | 加载修改前配置函数副本 | 已核查 |
| config_compatibility.py | 实际历史配置与旧缺省指纹对比 | 已核查 |
| config_compatibility.py | 新模式身份变化对比 | 已核查 |
| config_compatibility.py | 实际配置前置检查 | 已核查 |
| config_compatibility.py | 模板其他配置不变校验 | 已核查 |
| test_task_success_filter.py | 新分量保持旧奖励，并从原始事件重算门控。 | 已核查 |
| test_task_success_filter.py | 成功、错答和缺答案仍分别得到一、零和负零点一。 | 已核查 |
| test_task_success_filter.py | 新分量接口不能绕过旧来源和奖励输入保护。 | 已核查 |
| test_task_success_filter.py | 真实评分入口保存成功分量，训练奖励和开发 EM 保持原语义。 | 已核查 |
| test_task_success_filter.py | 全错差异组在旧模式有正优势，新模式直接排除。 | 已核查 |
| test_task_success_filter.py | 成功失败混合组完整保留，奖励矩阵不被筛选器改写。 | 已核查 |
| test_task_success_filter.py | 全成功组没有相对任务信号，保持排除。 | 已核查 |
| test_task_success_filter.py | 原文本正确与门控后成功独立，筛选只读取后者。 | 已核查 |
| test_task_success_filter.py | 新模式缺标签或独立身份时失败，旧模式仍接受历史报告。 | 已核查 |
| test_task_success_filter.py | 拒绝字符串标记、版本缺失、分量矛盾、非法 EM 与同行错配。 | 已核查 |
| test_task_success_filter.py | 复制轨迹身份不能冒充同题独立的八次 rollout。 | 已核查 |
| test_task_success_filter.py | 成功标签不能绕过奖励有限性与完整八条组约束。 | 已核查 |
| test_task_success_filter.py | 新模式保留同题身份检查和已接受问题去重。 | 已核查 |
| test_task_success_filter.py | 成功混合也不能绕过用户已有的有限奖励方差阈值。 | 已核查 |
| test_task_success_filter.py | 完整组重排后成功标签与独立轨迹身份同步，筛选不串组。 | 已核查 |
| test_task_success_filter.py | 缺省与显式旧模式得到相同字典，调用者原设置不被修改。 | 已核查 |
| test_task_success_filter.py | 模式拼写、规则版本和未启用组合不得静默沿用旧行为。 | 已核查 |
| test_task_success_filter.py | 新字段缺省兼容旧指纹，启用资格规则会改变训练身份。 | 已核查 |
| test_task_success_filter.py | 合法配置通过前置检查，资格修复不更改奖励及学习率裁剪。 | 已核查 |
| test_task_success_filter.py | 新模式在生成前拒绝关闭实验、关闭动态、无门控或旧答案评分。 | 已核查 |
| test_task_success_filter.py | 已有旧运行目录可接受新增缺省配置，不产生策略误失配。 | 已核查 |
| test_task_success_filter.py | 同版本恢复成功，资格变化在 branch 和兼容来源路径仍被拒绝。 | 已核查 |
| test_task_success_filter.py | 共用补抽和真实奖励仅保留成功混合组，完整状态可恢复。 | 已核查 |
| test_task_success_filter.py | 全错差异组在新模式耗尽补抽，不计算训练概率或推进步数。 | 已核查 |
| test_task_success_filter.py | 纯评价奖励不能作为新筛选训练入口，拒绝发生在生成前。 | 已核查 |
| test_task_success_filter.py | 无缺答案惩罚时仍按成功混合筛选，二值奖励保护保持。 | 已核查 |
| test_task_success_filter.py | 补齐复制行不冒充独立轨迹，去补齐后报告和成功标签原样保留。 | 已核查 |
| test_task_success_filter.py | 实际入口指纹检查拒绝将旧资格 checkpoint 作为新模式续训。 | 已核查 |


## 2026-10-11T04:44:58.595324+00:00 Reward design and root-cause replay

本次历史回放与奖励设计已完成，负责人/root；检查日期2026-10-11（北京时间），全部命令经ssh mx。详细报告见 reports/grpo_reward_rootcause_20261011.md；产物 /mnt/public/code/lyk/lzy/runs/metax-grpo-reward-rootcause-20261011-v1。3200个实际入选组、25600条训练轨迹及全部100步奖励均值对齐；81–100无成功组40.625%，占正优势轨迹48.05898%。任务成功口径41–60全失败组45，原文本EM口径44，不能混用。完整2A奖励/资格重放已完成；原始token/mask、真实终止元数据不足的子项仍未知，未做反事实真实补采。

发现原训练及当前actor的PG/Entropy/clip/ppo_kl只记录mini最后micro，KL记录全部micro，需优先修复指标覆盖并增加total_loss，不能伪造历史总loss。response_length包含环境文本；loss模型token/轨迹为216、264、282、333、245，不能据旧长度断定持续增长。根因最强证据为奖励方差资格与标准差归一化的错误强化；策略漂移与整轨迹信用问题强怀疑，LLDS/数值溢出/实际token失配因果未确认。

新增bounded_process_v2方案候选：R=S-min(.12,.1*M+.02*min(N_invalid,2)+.02*min(N_loop,2))；先独立启用一个新项，保留task_success_mixed资格。G8下成功R≥.88、失败R≤0且≥-.12，混合组均值至少.005，失败优势必负；仅代数验证，未证明训练效果。完整违规与原生截断区分；复用search_diagnostic，只对第三次起相同query且无新可见证据的循环候选软罚；不罚文风、普通回退、总长度，不针对字符。整轨迹广播仍会强化成功错误前缀，动作级PG屏蔽另做独立消融，KL/Entropy mask分开。

实施顺序：先真实GPU前提及全micro指标验收，再A0旧筛选/A1任务成功筛选；A2无效动作软罚、A3重复无新增证据软罚分别对A1；lr减半与KL加倍单独对照；确认token实现错误则先修、重锁基线。5步接线、20步筛选，长期100新增步/3配对seed；开发集与正常纠错评价、相同更新和rollout预算同时比较。监控仅配套保护，预防重点是信号、信用分配和更新偏移。真实模型生成0、更新0，无生产源码/配置修改、无新GPU实验或生产CPU复测，未提交/推送；上次198项仅适用原筛选修复。

仅新增远端独立分析脚本 historical_replay.py（不在生产源码目录），以及报告/文档。脚本流式重建完整8轨迹组、真实入选前缀、旧门控奖励和样本标准差优势；不导入训练器/Ray/GPU。函数2个均含中文@brief、各@param、@return与适用@raises/@note；27逻辑单元说明审核，证据 source-audit.json。原始日志身份、奖励、每步均值断言通过，脚本退出0。首次单字符重复启发式包含空白误报，attempt1完整保留；最终排除空白并重跑，首次正优势异常长串候选为step51。启发式不用于训练奖励。奖励设计cap代数校验见reward-design-check.json；不属于效果验收。生产源码/配置0修改，生产注释覆盖不适用，未重跑生产CPU或GPU测试。


## 2026-10-11T05:06:25.399661+00:00 LR/KL/reward trial validation planning

User confirmed lr=5e-7 and actor KL=.002. Validation plan: grpo_stability_trial_validation_plan.md. Common task_success_mixed baseline; separate B/L/K/R and LK/LKR comparisons; candidate bounded invalid-action reward remains unimplemented. CPU/history and GPU prerequisites before 5-step smoke, 20-step screen and selected 100-new-step/3-paired-seed confirmation. Independent EM/generation/recovery and cost metrics; no new training, model generation, source/config changes or tests. Planning only; no fabricated run_id. Agent /root.

Documentation only; code-comment coverage not applicable. No production CPU/GPU test rerun; prior198 passes apply to previous selector repair only.


## 2026-10-11T05:22:47.905170+00:00 Budget-limited trial plan

User total budget 1–2 days. Latest section7 of grpo_stability_trial_validation_plan.md supersedes mandatory six-arm/three-seed first round: only B vs target T(lr5e-7,actorKL.002,one validated process penalty), common task_success_mixed and paired seed42. Start20 new steps each, extend40 then60 only with value and time. Target first report24h, hard budget48h including preparation/evaluation/cleanup; share parent D256, mid fixed64 questions every20steps, final cold D256 per arm. Original historical training step means10.56–19.27min; D256~40min, new sampling cost unknown. No model workload/source/config changes or tests started; planning only, no run_id. Single-seed short/midterm results cannot claim long-term causal repair; conditional one ablation only. Agent/root.

Documentation only; source-comment coverage not applicable, no production tests rerun.


## 2026-10-11T05:54:06.537783+00:00 Continuous trajectory logging implementation

连续轨迹展示修复进行中：只读复用真实消费账本；模型输出全文连续展示，搜索观察独立缩略，奖励及诊断移到末尾。旧总字符限制改为辅助诊断预算；search_result_max_chars默认1000，0为搜索全文。保留原dirty修改；CPU及历史预览待执行，无真实生成/训练。负责人/root；产物 /mnt/public/code/lyk/lzy/runs/metax-trajectory-readable-20261011-v1。


## 2026-10-11T06:02:30.196859+00:00 连续轨迹日志验收

连续轨迹日志修复已完成。修改仅限 verl/utils/trajectory_logging.py、tests/test_trajectory_logging.py、verl/trainer/config/ppo_trainer.yaml；共用展示器复用真实账本和既有奖励解释，不新增生成、检索或奖励路径。思考/动作消费文本按真实轮次全文输出；对应visible_text只在搜索结果中缩略。奖励、执行状态、原因码、调用身份、未消费尾部及引用诊断统一置于连续轨迹之后。

search_result_max_chars默认1000，首尾正文按3:1保留并标注省略数量；0表示搜索全文。兼容max_chars_per_trajectory旧字段，改为末尾辅助诊断预算；不再截断模型思考/最终回答。无逐轮账本时完整生成历史展示一次，来源不明的information不缩略；模型自己生成的伪观察也全文保留。无接受答案则明确未作答，不补造答案。样例数、批次频率、异常隔离及默认关闭的直接调用保持兼容。控制台每条一次print，文件一次write同一完整块；多进程汇总日志是否另有外部插入尚未GPU验证。

最终CPU204项通过，新增6项，失败/错误/跳过0；test_fp16.py明确排除。覆盖32k多轮模型文本、20k无账本历史、18k伪观察、搜索0/短/长预算、未作答、尾部隔离、控制台/文件一致、真实RewardManager奖励/输入/Python随机状态不变及展示失败隔离。源码AST函数说明14项无缺失；人工逐项检查36/36逻辑单元中文说明，覆盖100%，函数与关键逻辑分别合格；范围含两个运行脚本和配置。CPU及历史展示验收不能代替真实GPU日志集成或训练稳定性结论。

历史预览取原100步运行首条真实候选轨迹（原step1，3轮、2次真实搜索），匹配评分审计第257行同一trace_uid，模型消费552字符，两次可见观察2028/2084字符，实际返回奖励1不变；逐轮完整顺序和记录不变检查通过。无需重新生成。预览：/mnt/public/code/lyk/lzy/runs/metax-trajectory-readable-20261011-v1/historical-preview.readable.log。

负责人/root；全部命令经ssh mx。产物 /mnt/public/code/lyk/lzy/runs/metax-trajectory-readable-20261011-v1，详细记录 runs/metax-trajectory-readable-20261011-v1.md。原有dirty筛选代码/文档保留，本次未提交/推送；真实生成0、训练更新0，无新checkpoint。下一步：新启动任务复用该展示器；保留1–2天B/T验证计划，在GPU前提和指标/reward接线完成后使用新日志核对至少一条实际轨迹。已有历史大日志未改写。

### 本次逻辑单元注释清单（36/36）

1. display_text：完整展示模式、控制字符清理与幂等排版；说明位置：函数说明及原有清理分支说明。
2. render_search_result：真实观察的展示职责和预算校验；说明位置：函数说明及参数异常说明。
3. render_search_result：仅剥离真实工具字段的完整information外壳；说明位置：仅真实工具字段允许省略注释。
4. render_search_result：首尾3:1分配、省略量计算与标签恢复；说明位置：首尾保留及预算范围注释。
5. render_trajectory：完整消费轨迹与末尾奖励诊断的职责；说明位置：函数说明和副作用约束。
6. render_trajectory：辅助预算与无搜索场景的搜索预算校验；说明位置：函数异常说明和入口拒绝注释。
7. render_trajectory：候选阶段及同行身份的只读呈现；说明位置：沿用真实候选身份说明和候选标记。
8. render_trajectory：按账本顺序保留每轮完整消费文本；说明位置：账本消费文本注释。
9. render_trajectory：绑定call_id展示可见搜索观察并缩略；说明位置：visible_text/raw_text边界注释。
10. render_trajectory：执行状态和长调用身份移到诊断；说明位置：长身份留在诊断区注释。
11. render_trajectory：原因码、原位置与未消费尾部隔离；说明位置：账本尾部移至末尾注释。
12. render_trajectory：引用诊断不混入模型输出；说明位置：末尾诊断职责说明。
13. render_trajectory：未作答结束状态不补造答案；说明位置：函数不补造答案约束。
14. render_trajectory：无账本只展示一次历史及缺失回退；说明位置：无来源身份不可误删模型文本注释。
15. render_trajectory：复用答案提取及既有分值和返回策略；说明位置：仅解释既有奖励注释。
16. render_trajectory：辅助诊断单独截断且完整输出起止边界；说明位置：诊断预算不吞模型输出注释。
17. HumanTrajectoryLogger.__init__：新增搜索展示预算、严格整数及范围校验；说明位置：函数配置说明和预算0/下限注释。
18. HumanTrajectoryLogger.emit：共享连续渲染器一次输出并隔离故障；说明位置：函数整块输出和故障隔离说明。
19. test_real_turns_visible_evidence_and_tail：真实可见观察、未消费尾部和新的奖励边界；说明位置：真实裁剪与边界说明。
20. test_newlines_controls_and_auxiliary_budget：控制字符及旧预算下完整模型与奖励保留；说明位置：函数说明和模型不截断注释。
21. test_continuous_long_model_output_and_deferred_diagnostics：真实两轮账本及32000字符模型完整性；说明位置：函数说明和逐轮全文断言注释。
22. test_continuous_long_model_output_and_deferred_diagnostics：工具位置、诊断尾部顺序及输入不变；说明位置：函数诊断隔离及顺序说明。
23. test_search_abbreviation_boundaries_and_full_option：200正文预算的首尾、808省略量及0全文；说明位置：函数说明和精确预算注释。
24. test_search_abbreviation_boundaries_and_full_option：短观察及非法预算分支；说明位置：函数参数边界职责说明。
25. test_model_information_tag_never_abbreviated：真实执行器生成的18000字符伪观察不缩略；说明位置：无真实call_id不缩略注释。
26. test_no_ledger_history_displayed_once：20000字符无账本历史单份全文；说明位置：函数说明与无来源身份注释。
27. test_no_ledger_history_displayed_once：无来源观察不得截断、空历史回退；说明位置：函数回退说明和不可误删注释。
28. test_unanswered_trace_not_fabricated：真实缺答案轨迹完整结束和负奖励；说明位置：函数不补造答案说明。
29. test_console_and_file_each_receive_complete_single_block：旧预算下长轨迹的同一控制台/文件输出；说明位置：函数完整块职责。
30. test_console_and_file_each_receive_complete_single_block：一次print验证避免逐轮打印穿插；说明位置：一次print注释。
31. test_invalid_configuration_rejected：新增搜索预算的类型、负值及过小值拒绝；说明位置：函数说明和非法配置启动拒绝注释。
32. ppo_trainer.yaml：1000搜索正文预算、0全文及旧字段辅助语义；说明位置：就近配置中文注释。
33. cpu_verify.py：无GPU限制、单线程及排除真实GPU测试；说明位置：驱动头部及单线程说明。
34. cpu_verify.py：收集现有CPU测试和真实统计/失败返回；说明位置：驱动可复现CPU回归说明。
35. historical_preview.py：历史问题/标准答案与同trace报告对应；说明位置：同trace获取注释。
36. historical_preview.py：逐轮完整消费、顺序、缩略及奖励记录不变核验；说明位置：每轮及顺序断言注释。


## 2026-10-11T06:17:23.744369+00:00 提交前验收与指标结论更正

启动前复核更正：AST核验当前dp_actor.py第451行及原训练源码快照第395行，Entropy/PG/clip/ppo_kl指标字典均位于micro_batch循环内，每个微批都有记录。此前将其解释为“仅末微批”的判断有误，相关历史熵/PG统计不应再标为末微批样本；它们是现有微批均值聚合，仍不等同于全token加权统计。后续只补充total_loss、有效token加权熵及覆盖计数，不迁移既有正确的日志循环。奖励方差资格错误强化的重放结果不受此更正影响。证据：metax-grpo-bt-verification-20261011-v1/metric-loop-audit.json。分功能提交前CPU204项复验通过，真实训练/生成0。


## 2026-10-11T06:20:42.176868+00:00 实验前损失展示接入

原PG/Entropy循环保持正确位置；只读接入total_loss、有效模型token熵分子/分母及微批覆盖计数。新增3项CPU案例，待回归；无真实训练。模块独立于GPU/Ray，仅worker适配调用，聚合复用原reduce_metric。负责人/root。


## 2026-10-11T06:22:54.772649+00:00 有界过程软罚接入

bounded_invalid_v1接入独立纯模块，复用已校验门控/成功标签；仅原生stop且真实执行拒绝的消费动作每轮计一次，最多两轮×.02；缺答案与软罚总成本封顶.12。长度截断与未知终止免新增罚；loop项0。旧默认值及恢复指纹兼容，新奖励版本/系数纳入身份；评价原EM不变。新增8项CPU案例待回归，无GPU启动。负责人/root。


## 2026-10-11T06:30:50.858750+00:00 顺序验证监督接入

新增参数化stability_trial.py：默认只检查，显式launch顺序父D256/B20/冷D256/T20/冷D256；原生终止覆盖不足时使用预冻结LK替代配置并明确记录。持有八卡锁、46小时停止预留2小时收尾，显存56GiB保护只停止本次任务；完整checkpoint复用原校验，唯一RAY_TMPDIR/启动身份清理不涉及检索。新增6项CPU案例待测试，真实GPU验证未宣称完成。负责人/root。


## 2026-10-11T06:37:49.887072+00:00 B/T启动前锁定验收

最终启动前验收：CPU224项通过，新增20项（指标3、奖励10、监督7），失败/错误/跳过0；test_fp16.py另在真实cuda:0运行1项通过，覆盖CPU以外的FP16小模型更新、单rank FSDP和溢出恢复。world_size=1下FSDP使用NO_SHARD，不能冒称八卡FULL_SHARD已验收；八卡完整更新将在B前2–5步按真实日志检查。正式GRPO更新仍0，真实7B生成0。

当前task_success_mixed与连续轨迹日志已分功能提交06688fc、7d0b5f7，研究文档f7975c5；未推送。损失展示只增加total_loss、有效模型token熵总量/计数及微批覆盖，现有循环位置正确。新bounded_invalid_v1奖励已接入：R=S-min(.12,.1*M+.02*min(N_invalid,2))，N_invalid仅原生stop且执行器拒绝的消费动作；length/未知免新增罚；loop项未启用；legacy默认原数值和旧恢复指纹兼容。新版本/系数进入训练身份，评价保持原EM。

监督入口默认仅检查，显式launch才顺序父D256、B20、B冷D256、T20、T冷D256；最初2–5步为同一训练中的八卡接线验收。持有八卡独占锁，56GiB总显存保护，整个预算48小时且46小时停止预留2小时收尾，任何非有限/更新跳过/实际微批覆盖不足停止并保留结果。只清理本阶段唯一RAY_TMPDIR和启动身份一致的进程，不全局停止Ray，不触碰独立检索。原生终止覆盖<95%或没有stop时采用已预冻结的T-LK配置，显式记录未验证新增奖励；不改正在运行的配置。父D256缺答案>12时停止，不擅自带异常父模型训练或更换父模型覆盖失败。两组20步完成后先分析，不自动延长40/60；总耗时目标一到两天不变。

父加载文件17项已流式哈希通过（仅HF Actor权重/分词器；旧优化器rank文件未使用），参考Qwen2.5-7B固定。固定D64为原D256顺序前30NQ/34Hotpot，生成配置不缩短；训练32题×8、micro8、mini128，fresh optimizer/scheduler/scaler，同seed42，同预热10步。B lr1e-6/Actor KL.001/legacy；T lr5e-7/Actor KL.002/bounded_invalid_v1。审计记录原生token/终止，文本文件每批每来源2条、控制台1条，两组相同；保留全量结构化审计，未新增字符特定惩罚。

职责：loss_observations和bounded_reward纯模块只消费张量/普通报告；worker与RewardManager仅薄接线；监督脚本调用现有Hydra入口、评分、checkpoint校验，不复制生成/训练算法。注释：43新增/修改函数标签无缺失，46/46语义逻辑单元有效中文说明，覆盖100%，关键逻辑独立检查；详列source-audit.json。GPU8、长期收益与实际异常复现待观察。产物 /mnt/public/code/lyk/lzy/runs/metax-grpo-bt-verification-20261011-v1；负责人/root；本条UTC由远程脚本填写。

### 本次46项逻辑单元注释验收

1. loss_observations：只读总Loss、有效模型token熵与微批覆盖计数；说明：函数说明和float32/排除环境注释。
2. DataParallelPPOActor.update_policy：反传前观测原总Loss，不改变系数/累积/mask；说明：反传前只读说明。
3. reduce_metric：两类明确计数命名空间求和，其余旧指标口径保持；说明：可加总量说明。
4. reduce_metrics：跨微批/rank先加分子分母再算熵；说明：全局加权说明。
5. ActorObservationTests：真实四微批覆盖与Loss恒等式；说明：函数说明和真实微批注释。
6. ActorObservationTests：长短token加权、环境排除和无图/无梯度；说明：各测试职责及熵算例。
7. check_config：新奖励缺省兼容与版本、有限系数、门控、.12边界校验；说明：函数参数说明和版本边界注释。
8. bounded_reward：仅使用已可信校验的报告与同一任务标签；说明：函数职责和输入前提。
9. bounded_reward：legacy直接返回原分量；事件数不一致失败；说明：函数兼容职责及raises。
10. bounded_reward：无元数据标未知；length/未知免新增罚；说明：不通过长度猜测注释。
11. bounded_reward：重算消费动作原因，真实拒绝且stop才计一次；说明：执行拒绝第二道条件注释。
12. bounded_reward：最多两次计费，总成本.12封顶，成功标签不变；说明：成本与G8优势符号说明。
13. RewardManager.__call__：新训练候选接线与评价原EM保留；说明：新软罚只接可信终止说明。
14. provenance：仅新奖励进入恢复身份，旧缺省兼容；说明：旧缺省不改变身份注释。
15. render_trajectory：区分原公式、新训练候选成本和终止免罚；说明：新旧分值展示注释。
16. BoundedRewardTests：真实账本/原门控夹具和成功恢复.98；说明：各函数职责。
17. BoundedRewardTests：截断/未知/正常回答免罚，五轮计费和缺答案封顶；说明：对应测试说明。
18. BoundedRewardTests：缺元数据、事件数/身份错配及非法配置；说明：对应测试说明。
19. BoundedRewardTests：legacy精确兼容、真实训练/验证入口、日志解释；说明：对应测试说明。
20. BoundedRewardTests：G8边界优势符号和恢复指纹变化；说明：对应测试说明。
21. BoundedRewardTests：合法重复检索、未消费尾部和硬门控；说明：正常探索与原门控说明。
22. stability_trial.now/save/rows：UTC、原子小状态、只读闭合行；说明：各函数说明。
23. stability_trial.verify：冻结哈希与父Actor验收；说明：函数说明和小型清单注释。
24. stability_trial.training_summary：实测更新次数、微批覆盖、有限数值、checkpoint进度；说明：每rank及覆盖注释。
25. stability_trial.evaluation_summary：完整唯一零更新评价和原生终止覆盖；说明：函数说明。
26. stability_trial.publish：原子状态及仅本run区块更新；说明：函数note和文档边界注释。
27. stability_trial.interrupt：信号异常触发所属任务清理；说明：函数职责。
28. stability_trial.owned_processes：唯一完整Ray环境值匹配，保留其他环境隐私；说明：函数职责和完整匹配。
29. stability_trial.owned_processes：带空格comm正确提取启动ticks，IO竞态跳过；说明：右括号及ticks注释。
30. stability_trial.cleanup_owned：只终止独占Ray环境进程，二次启动身份核验；说明：函数note和PID复用注释。
31. stability_trial.run_phase：冻结阶段调用原入口，独占环境覆盖和外部Ray地址清理；说明：函数note和分步覆盖注释。
32. stability_trial.run_phase：56GiB总显存、46h截止与真实进度发布；说明：驱动包含检索说明。
33. stability_trial.run_phase：20步完整状态逐文件验收、冷评价统计；说明：冷评价前原校验说明。
34. stability_trial.run_phase：正常/失败均只清理本次进程组与Ray环境；说明：finally说明。
35. stability_trial.main：默认仅检查，launch锁/重复任务/GPU占用拒绝；说明：函数note和占用复核注释。
36. stability_trial.main：父缺答案≤12、原生覆盖95%，预冻结LK回退；说明：健康门限注释和设计配置。
37. stability_trial.main：顺序B/T20并等待分析，不自动扩展40/60；说明：函数note。
38. TrialSupervisorTests：闭合日志、唯一环境/带空格进程身份；说明：对应函数说明。
39. TrialSupervisorTests：默认不启动、阶段环境覆盖与冻结失败；说明：对应函数说明。
40. TrialSupervisorTests：跳过更新/覆盖不足停止，完整零更新评价；说明：对应函数说明。
41. prepare_configs.py：固定30/34来源题单，不按结果选择；说明：固定来源配比注释。
42. prepare_configs.py：同parent/seed、fresh optimizer及目标Actor lr/KL；说明：实际配置差异核对注释。
43. prepare_configs.py：评价/训练调用原入口并保留预冻结LK；说明：共用seed入口注释。
44. parent_verify.py：只核验HF Actor加载文件，不读旧优化器；说明：脚本头和核验范围注释。
45. gpu_verify.py：要求真实GPU，不将skip作为通过；说明：显式GPU注释。
46. ppo_trainer.yaml：默认旧奖励、真实stop软罚和成本上限；说明：配置就近说明。


## 2026-10-11T06:44:02.228693+00:00 验证实验实际启动

验证监督器已实际启动：launcher PID2829354，父D256评价PID2829362，启动UTC2026-10-11T06:41:56.895844+00:00。当前phase=parent-eval，正式GRPO训练步数B/T均0，无本次新checkpoint；不是已完成评价。冻结代码6cbd7dca5bafca19a9e4eb9c1c83c444a81c2233，292项源码/13项资产哈希核对通过，真实配置入口B/T均通过，固定reference与父元数据一致。实际命令为bash env/metax/run.sh -u scripts/difficulty/stability_trial.py --run-directory /mnt/public/code/lyk/lzy/runs/metax-grpo-bt-verification-20261011-v1 --launch，经ssh mx后台启动。下一步先确认父健康与原生终止门限，再按冻结方案顺序B20、B冷D256、T20、T冷D256。CPU224通过和单卡小模型1项通过仅代表已执行范围；父评价/八卡首段/长期效果尚在进行。进度以status.json自动区块实测时间为准；负责人/root。
