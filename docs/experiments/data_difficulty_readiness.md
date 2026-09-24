# data-difficulty：实验条件检查与代码修改方案

> 当前进度与交接统一见[进度台账](data_difficulty_progress.md)；每次运行按[运行模板](runs/TEMPLATE.md)建档并在阶段节点同步。历史检查结果不代表当前运行状态。

> 进度更新：模型与数据已下载并校验。用户决定暂缓小数据/检索服务验证，先完成第一批代码修复；已实现内容和 CPU 测试见[代码修改记录](data_difficulty_code_changes.md)。下文中的初始检查和待办以该记录为准。

检查日期：2026-09-23。基于提交 `71e072a` 及当前工作区；分支 `data-difficulty`。这是初步检查，未完成完整模型训练或联网下载验证。

用户确认实验可在其他更强设备（例如 A6000）运行。本机硬件与容量仅是检查快照，不构成远程实验的前置限制。优先在目标设备验证现有 FA2 路径，本机后端适配降为可选。

## 1. 初始检查结果（历史快照）

| 条件 | 结果 | 影响和后续动作 |
| --- | --- | --- |
| 分支 | 已创建并切换 data-difficulty | 保留原有实验设计文档 |
| GPU | 两张 TITAN RTX，SM 7.5，每张约 24 GB；检查时各约 24 GB 空闲 | 显存可用于短流程检查，完整 3B 训练容量仍需实测 |
| 主环境 | Python 3.9.25、Torch 2.4.0+cu121、Transformers 4.47.1、vLLM 0.6.3；现有检查通过 | 仅证明依赖导入与小型 FP16 GPU 运算成功 |
| FA2 训练支持 | 检查明确返回 False | 当前 FSDP 模型加载写死 flash_attention_2，阻塞本机默认训练；目标设备另行验证 |
| 检索环境 | Python 3.10.21、FAISS 1.8.0 等导入通过，GPU add/search 通过 | 小索引检查成功，真实语料尚未验证 |
| 问答数据、语料与索引 | 在项目、root/data 和所检查 HF 缓存中未发现真实实验 parquet、wiki-18 或索引 | 需要在目标设备确认/准备；模型已在用户指定的外部目录发现，见下表 |
| 检索服务 | 检查时 8000 端口无监听 | retrieval_launch.sh 仍使用占位路径，需要资产和实际配置 |
| 磁盘 | 所在文件系统约 61 GB 可用，使用率 97% | 先计算资产及完整 checkpoint 保留预算，再确定存储位置 |
| 训练入口 | 默认 8 GPU、n_agent=5，TRAIN_DATA_DIR/TEST_DATA_DIR 与 DATA_DIR 定义不一致 | 新建专用实验入口，显式路径、GPU 数和 group size |
| 难度标签及 sampler | 未实现 | 不能直接执行 A/B 矩阵 |
| GRPO 组 ID | 检索路径 uid=原数据 index | 多来源局部 index、重复抽题可能错误合组，必须先修复 |
| 完整断点恢复 | 当前只导出模型与 tokenizer，未见配套完整恢复流程 | 无法严格执行第二阶段同训练状态分支 |
| KL reference | actor/ref 都从 model.path 构建 | 换 actor checkpoint 可能连 reference 一起换，必须解耦 |
| 全流程随机种子 | 主训练路径未见统一 seed 配置贯穿 driver/worker/rollout；子集抽样写死 42 | 需要显式随机流及状态保存，才能解释多种子结果 |
| 评价全量性 | val DataLoader 使用 drop_last=True | 最后不足一个 batch 的题被遗漏，影响分来源评价 |
| Prompt 长度过滤 | filter_prompts 参数存在，但实际预过滤逻辑被注释 | 数据准备阶段必须检查长度；不应假定超长问题已过滤 |
| 检索错误处理 | requests.post(...).json() 无显式 timeout/status 校验 | 请求可能阻塞，服务错误需与模型答错分开 |

已执行并通过：

```bash
bash env/run.sh searchr1 python env/check.py searchr1
bash env/run.sh retriever python env/check.py retriever
```

训练环境检查输出包含 vLLM 缺少构建 commit hash 的警告，导入成功；本次未将其判为训练阻塞项。FA2 不支持则是已证实的阻塞项。

## 1.1 用户提供的模型目录检查

只读目录：`/root/myprojects/reward_sql/RewardSQL/checkpoints`。验证未加载完整模型到 GPU，没有改动该目录。

| 子目录 | 配置架构 | 文件检查 | 当前环境兼容性 |
| --- | --- | --- | --- |
| PRM-Models | Qwen2ForCausalLM，hidden_size=3584，28 层 | 四个分片齐全；索引与分片头部 339 个 tensor key 一致；索引声明约 15.23 GB 权重 | AutoConfig 和 AutoTokenizer 离线加载通过，完整 forward/rollout 待测 |
| GRPO-Models | Qwen3ForCausalLM，hidden_size=4096，36 层 | 四个分片齐全；索引与分片头部 399 个 tensor key 一致；索引声明约 16.38 GB 权重 | tokenizer 通过；Transformers 4.47.1 AutoConfig 报不识别 qwen3 |
| qwen2.5-coder-7b-instruct | Qwen2ForCausalLM | 索引要求四片，只发现第 4 片；第 1/2/3 片缺失或不可访问 | 权重不完整，当前不能加载完整模型 |

PRM-Models 的 config 记录了 Qwen2.5-Coder-7B-Instruct 来源路径，但目录名称和模型架构不能证明它是原始权重或已训练到哪个阶段。GRPO-Models 的训练历史也未确认，不能只凭目录名选择为初始模型。

原项目根目录 `train_grpo.sh` 默认启用 `Qwen/Qwen2.5-3B`（Base）；`scripts/nq_hotpotqa/v0.2/train_grpo.sh` 默认启用 `Qwen/Qwen2.5-7B`（Base），并提供其他模型的注释配置。它们与现有 Coder/PRM/Qwen3 目录不同。为控制多组对照成本，当前建议先沿用原入口的 Qwen2.5-3B Base，但模型选择尚未由用户最终确定。

需要确认实验 C0 使用哪个目录以及权重的训练经历。若用 Qwen3，需独立验证 Transformers、vLLM、仓库内适配层、去 padding 模型注册与 chat template/thinking 模式的组合；不能只升级 Transformers 后宣称兼容。先在独立环境验证，避免破坏现有锁定环境。

文件检查仅验证分片存在、头部可读和 tensor key 映射；未做全文件哈希或完整前向验证。跨机器传输前生成资产清单和校验值，传输后复核。

## 2. 修改边界和建议顺序

以下为初始修改方案；实际实现进度以进度台账和代码修改记录为准。后续将修改拆为可单独验证的阶段；每阶段通过对应检查后再进入下一阶段。

### P0-A：目标设备预检与统一实验入口

修改位置：`verl/workers/fsdp_workers.py`、`verl/trainer/config/ppo_trainer.yaml`，新增 `scripts/experiments/difficulty/` 中的入口和配置。

- 在目标设备先验证现有 FA2 actor/ref 路径，无需为本机 TITAN 预先改写正式训练后端。若决定使用不兼容 FA2 的设备，再增加可配置 attention 实现；例如验证 eager 或关闭 Flash SDPA kernel 的兼容 SDPA 路径。
- 可选的 TITAN 适配设置 `use_remove_padding=false`、序列并行度 1、FP16。不能只把 attention 字符串替换掉，还保留依赖 varlen FA2 的去 padding 路径。
- vLLM rollout 与训练 attention 分开验证。确认 XFORMERS 配置在实际 worker 生效，以及仓库自带 vLLM 适配层能生成多轮轨迹。
- GRPO 无 critic，优先适配实际 actor/ref 路径；其他算法路径不声称已经适配。
- 专用入口显式配置数据路径、模型路径、实际 GPU 数、n_agent=4、rollout.n=1、独立 KL loss 和绝对训练步数。启动前检查文件和参数整除关系。
- 保留研究配置中的总 batch 语义，micro batch 根据吞吐测试锁定；若目标资源不足，统一缩小所有组的总 batch，并更新预算，不单独给某组变更。

验收：小模型完整 rollout→reward→update 通过，再对正式模型做短流程检查；记录显存峰值。后端能导入不算验收通过。

### P0-B：题目 ID 与 GRPO 分组修复

修改位置：`verl/utils/dataset/rl_dataset.py`、`verl/trainer/ppo/ray_trainer.py` 的 fit/compute_advantage 调用处；新增数据清单工具。

建议语义：

```text
question_id = 永久题目身份（跨刷新稳定）
group_uid = run_id + global_step + 本批抽题序号
trajectory_id = group_uid + rollout 序号
```

在 batch.repeat(n_agent) 前创建 group_uid，重复展开时自然复制 uid。检索路径不要再覆盖为 index。先只针对本实验的 do_search=true 路径实现，非检索路径保持现有语义并增加回归检查。

验收：同一题在同批重复抽两次仍是两个四条组；不同来源相同 index 不串组；batch balance 后仍正确；0000/1111 优势为零，其余三个模式符号正确。检查所有组恰好 G=4，异常立即失败。

### P0-C：完整评价与检索错误分类

修改位置：`ray_trainer.py::_create_dataloader/_validate`、`search_r1/llm_agent/generation.py`。

- val drop_last 改为 false，检查每轮检索中活动 batch 的并行 padding/unpadding，确保补齐行不进入指标。
- 输出被评价 question_id，断言集合和预期清单一致；1、B−1、B+1 个题以及不整除 world size 的尾批都需覆盖。
- 独立设置开发集和最终测试入口，不能在探索期间将固定测试集当作开发集反复选择策略。
- 检索增加可配置超时、有限重试、HTTP 状态和 JSON 结构验证，重试耗时计入成本。失败时标记基础设施异常并暂停/重试，不转为 reward=0。
- 长度预检查覆盖 tokenizer/chat template/max_start_length 的实际截断，保存排除原因，避免不同实验隐式改变题池。

### P1-A：标签评估与轨迹导出

新增建议：`scripts/difficulty/score_pool.py`；训练代码抽取共享的评分/轨迹生成接口。不要复制一套与训练不同的简化 infer 流程。

能力要求：加载指定 checkpoint，使用同一 LLMGenerationManager、检索配置和 RewardManager；只生成并评分，不做优化器更新；一次四条轨迹；支持按 question_id 断点续跑和完整性检查。

保存 manifest 元数据和逐轨迹记录；哈希包含 checkpoint、题池、prompt、检索版本、采样配置。label_version 的每次刷新不可覆盖之前结果。分桶噪声复测采用独立 seed 流。

需要确认生成流程中的验证模式是否会强制 do_sample=false；难度评分必须显式启用随机采样，固定确定性评价独立配置。

### P1-B：配额 sampler 与固定步数训练

新增建议：`verl/utils/dataset/difficulty_sampler.py`；修改 `ray_trainer.py::_create_dataloader/fit` 和实验配置。

- 使用 batch_sampler 生成来源×桶配额，不能同时开启 DataLoader shuffle。
- 分开保存 immutable question_id 到当前 dataset 行号的映射，以及 versioned labels，避免刷新时修改 question_id。
- 初始五档条件比例、桶配额舍入补偿、候选不足策略都显式定义。
- A0 使用同一 sampler 的均匀分布模式；跨 batch 有放回，同 batch 优先不重复。
- 保存 generator 状态、已消费 batch 数和曝光统计。续训以消费位置为准，不以预取出来的 batch 数为准。
- 显式按 max_steps/绝对 global step 停止，检查外层 total_epochs 不会提前耗尽。
- 刷新只在 step 边界原子切换标签与采样状态；处理预取队列中的旧标签 batch，避免刷新后仍用旧配额。

验收：固定 seed 采样复现、来源比例和配额准确、容量不足明确报错、恢复后采样序列符合预期。

### P1-C：全流程随机性和实验记录

修改位置：driver 初始化、Ray worker 初始化、rollout SamplingParams、sampler 与日志。

设计独立 seed：数据切分 seed、难度评分 seed、训练 sampler seed、训练生成 seed、模型/worker seed、评价 seed。配置在启动时展开存档，避免任何未解释的写死 42。

vLLM 分布式采样需验证实际 seed 的传递，不能只调用 driver 的 torch.manual_seed。推荐按 global step/group_uid/trajectory_id 派生生成 seed，避免难度评分消耗训练随机流；后端若不支持逐请求 seed，记录限制并验证可复现程度。

日志写入 run_id、父 checkpoint、git commit/dirty diff、配置哈希、标签版本和 step；奖励函数中的随机调试打印不应消耗训练采样流。

### P2：完整恢复与 reference 解耦

修改位置：`fsdp_workers.py::save_checkpoint` 并新增对应 load 方法、`ray_trainer.py` 保存/恢复流程、`main_ppo.py` 和配置。

保存模型权重之外，还要保存：

- FSDP 对应 optimizer 状态，按当前 PyTorch/FSDP 接口正确聚合或分片并恢复；
- scheduler、actor.grad_scaler、global step；
- Python/NumPy/Torch CPU/CUDA 各 rank RNG；
- sampler generator、消费位置、当前标签版本和必要配额状态；
- reference 的固定模型路径/revision/hash、数据清单和配置；
- rollout RNG 状态，或确定性逐轨迹 seed 派生所需状态。

checkpoint 使用完成标记，未完整写入的 checkpoint 不允许恢复。将便于推理的权重导出与用于续训的完整状态区分开来，避免误用。

增加独立 reference 配置；B 分支从 C1 恢复 actor，但 reference 始终保持第一阶段 C0。恢复后确保 rollout 引擎同步为最新 actor 权重，不继续使用初始化时权重。

warmup 支持绝对步数配置，恢复不能重新计算为新的追加步数比例。第二阶段停止条件明确为 parent_step+additional_steps。

验收：固定轨迹输入下，“连续更新”和“中断恢复后更新”的参数/optimizer/lr/scaler 在合理误差内一致；再验证含采样的恢复。FP16 溢出跳步附近也要验证。全链路非确定性单独报告，不承诺 GPU 位级一致。

### P3：实验指标与汇总

修改位置：`ray_trainer.py` 指标汇总；新增 `scripts/difficulty/summarize.py`。

每步记录历史桶与训练实际 k、0<k<4 比例、生成/上下文 token、检索请求和时间、KL、优势 RMS、梯度/溢出、曝光/覆盖和标签版本。

评分与重试任务也纳入成本，按每个策略独立所需的总预算画图。多来源评价提供固定来源权重的汇总，避免来源比例变化被误判为能力提升。

## 3. 建议先实现的最小范围

1. P0-A/B/C：能运行、分组正确、评价不漏题。
2. P1-A/B/C：能生成标签、按配比训练、固定随机性并记录指标。
3. 完成短流程与第一阶段探索。
4. P2：在运行第二阶段之前完成完整恢复和固定 reference。
5. P3 的基础指标从第一阶段开始记录，汇总图表随后补齐。

条件允许使用兼容 GPU 时，可以先沿用现有 FA2 路径完成研究；本机后端适配仍作为独立工程任务。无论选择哪种硬件，正式对照组采用同一实现。

本轮没有下载大型资产、启动长期服务、修改训练代码或创建 commit。实验所需功能和验收仍是待办，不能仅凭本文档将其视为已实现。


## 本机下载存储位置补充

进一步检查确认 `/root/data` 已挂载独立 NVMe 卷 `/dev/nvme1n1p1`，检查时总容量约 916 GiB、可用约 419 GiB，挂载为可读写。先前约 61–62 GiB 的剩余空间指代码所在根文件系统，不代表本机所有存储。

本机资产根目录采用 `/root/data/search-r1/`，已创建 models、datasets、retrieval、runs、cache、tmp 子目录并验证读写。无需另行挂载。模型、问答数据、检索资产、运行产物分别存入对应子目录；下载及解压临时文件也使用该卷。

下载时显式配置缓存和临时目录，避免 env/run.sh 将缓存重定向到代码所在磁盘。实际下载脚本需要在读取 env/run.sh 后确认或覆盖 HF_HOME、HF_HUB_CACHE、HF_DATASETS_CACHE、TMPDIR 等有效路径，现阶段未修改该环境脚本。此容量为共享文件系统当时的可用值，下载前仍应检查资产总量。
