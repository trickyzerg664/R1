# sft-mx：从数据准备到启动训练的执行计划

日期：2026-10-05（北京时间）。负责人：Codex。状态：完整实施计划，新增 SFT 代码、正式教师采集与训练尚未执行。

开发工作区 `/mnt/public/code/lyk/lzy/R1-sft-mx`；分支 `sft-mx`，本轮核查 HEAD `72299650246511963a211b1133bf714c1d062ca6`，核查时工作区干净。基于已提交的 `data-difficulty-muxi`，包含 KV 缓存失效修复。当前任务是规划，不启动模型采集或训练。

## 1. 首轮范围与完成目标

先完成一条可恢复、可评价的 SFT 链路：冻结候选题 → 强教师真实交互 → 审核与逐轮样本 → CPU/GPU 验收 → S256 一轮 SFT → HF 权重重载 → D256 完整检索评价。通过后使用嵌套 S1000 独立训练，随后进入 C2/C3 的 RL 对照。

正式教师优先采用在检索规划、协议遵从和证据使用上优于当前 7B Base 的固定模型。型号、权重/API 版本、采样设置与成本预算在探针前冻结；当前尚未选定。Base 自生成作为教师来源对照。强教师并不免于过程审核，标准答案只用于事后判分。

首轮固定学生为原 Qwen2.5-7B Base；全参数 SFT、1 epoch、lr=5e-6、seed=42。教师来源、数据规模和训练超参分别管理，不同时搜索多组超参。S256/S1000 来自同一冻结数据版本；正式 S1000 从 Base 重新训练，不从 S256 追加训练，以保持规定的一轮预算。

## 2. 当前已确认的代码缺口

本轮静态检查和安装元数据核对得到：

| 位置 | 当前行为 | 必须完成的修改 |
| --- | --- | --- |
| `verl/utils/dataset/__init__.py` | 只导出 RL/RM Dataset | 新增并导出 SFTDataset，支持预分词逐轮数据 |
| `fsdp_sft_trainer.py::_build_dataloader` | 导入缺失的 SFTDataset；训练/验证都 shuffle/drop_last，8 worker 预取 | 接入版本检查、恢复采样器、真实尾批；验证不漏重；初版 num_workers=0 |
| `_normalize_config_bsz` | 原地修改配置，将全局 batch 除以卡数 | 保留全局配置，单独派生每卡值和累积次数 |
| `_build_model_optimizer` | 写死 FlashAttention2、BF16；顶层导入 PEFT | 可配置已支持的 attention/FP16；LoRA 启用时才导入 PEFT |
| `_compute_loss` | label 移位为 `[1:]`，旧 mask 为 `[:-1]` | 用明确定义的 labels/mask 边界，监督当前 target；问题均衡目标 |
| `training_step` | 普通 backward/step，按微批数再平均 | FP16 scaler、正确全局分母、梯度裁剪、真实更新和失败检测 |
| `validation_step / fit` | 平均各批 loss；尾批丢弃；步数定义不统一 | 精确统计、共享步数计划、周期日志与保存、空验证显式处理 |
| `save_checkpoint` | 只保存 HF 模型/tokenizer，无完整训练恢复 | 保存 optimizer/scheduler/scaler/RNG/采样游标，完整标记与校验 |
| trainer 文件末尾 | 再次导入自身 FSDPSFTTrainer | 清理重复模块导入，保留单一入口 |
| `LLMGenerationManager` | 已有检索与 bounded 上下文，没有完整逐轮采集接口 | 可选 trace_sink；模型/工具来源、原始/保留 token、实际观察和结束状态 |

实际环境：torch `2.6.0+metax3.3.0.2`，transformers `4.57.1`，tensordict `0.6.2`，PEFT 未安装。安装版 Qwen2 前向参数名为 **`logits_to_keep`**，旧技术计划中的 `num_logits_to_keep` 仅是旧接口思路，实施须使用本机真实签名并验收。

当前 RL 的成功记录不构成 SFT 验收；本轮未运行新 CPU/GPU 测试。

## 3. 阶段 A：冻结研究配置与候选题

输入路径均配置化；已确认源文件为 `/mnt/public/code/lyk/lzy/data/datasets/nq_hotpotqa_train/train.parquet`，P/D/T manifest 为 `/mnt/public/code/lyk/lzy/data/runs/formal-pdt-7b8-v1/manifest.json`。官方 test 只读取 question 列用于隔离，T.parquet 与测试答案保持封存。

复用现有永久 question_id 和 normalize_question，排除完整 P10000、D1000、PDT manifest 问题哈希及全部官方 test 问题，再全局去重和近重复复核。158551 道为此前只读审计的初步可用题数，尚未做长度与近重复审核。

拟冻结训练候选 5000 题（NQ2334/HotpotQA2666），独立验证候选512题（239/273）。按来源、tokenizer 问题长度三分位和 seed42 的哈希顺序固定候选；各来源的长度档配额与轮转顺序写入 manifest。探针取其中64题（30/34），成功且审核合格的同版本轨迹可以进入后续训练集。

目标 S256=120/136，S1000=467/533，S_val128=60/68。S256 嵌套于 S1000；S_val 与训练候选互斥。缺题不能缩小规模或临时改变来源配比。候选清单与样本数据分开发布，不把“冻结候选”写成“已有演示”。

**交付**：候选题文件、独立验证候选、隔离报告与版本 manifest。**通过条件**：ID/文本/近重复规则核对，来源配额足够，原文件哈希一致，长度与拒绝原因有记录。

## 4. 阶段 B：教师桥接与真实逐轮追踪

强教师可以本地运行或通过已配置接口调用；采集层用统一 TeacherPolicy 接口，核心轨迹校验不依赖具体提供商。接口返回可见 assistant 文本、结束状态及可用成本，不索取或依赖不可见的内部推理。短决策说明和合法动作满足学生协议即可。

通过 TeacherRolloutAdapter 接入已有 `generate_sequences` 接口，复用 LLMGenerationManager、真实检索、动作后处理与 RewardManager；不另写一套行为不同的搜索主循环。采集无需训练 logprob，提供商未暴露的字段明确记为不可用，不伪造概率或结束原因。

强教师和学生 tokenizer 分离：

1. 维护学生原始 prompt 与实际历史，按学生 tokenizer 构建有界上下文。
2. 教师获得相同可见事实，可使用自己的消息包装；额外指令不得携带 gold、未来结果、示例答案或额外工具信息。
3. 教师文本经原动作后处理，再以学生 tokenizer 转为本轮 target，记录教师原始输出。
4. 查询在同一检索索引执行一次，记录原始 passages，再按学生预算裁剪真实 observation。
5. 用学生协议重放得到下一轮 context；保存实际 token，不复制教师 token ID，不把教师私有提示写入学生训练输入。

预算沿用启动时冻结协议：topk3、每轮输出上限256、观察上限2048、总轨迹预算4096、最大10轮。每条轨迹/attempt/turn 派生可重现 seed。每轮都先检查学生可见长度；目标超预算直接拒绝，不静默截断。教师原生 finish_reason 可用时记录；不可用时长度命中保守拒绝并保留审查证据。

trace_sink 默认关闭；开启后记录原始输入、原始/后处理输出、活动 ID、真实检索、观察裁剪、forced_final 和最终奖励。回调只接收普通记录或复制到 CPU 的 token；不访问 trainer 私有状态，不保留 GPU 图。GPU 补齐行不能变成真实样本，记录工具结果不能额外发检索请求。

**交付**：教师适配器、可选追踪、collect CLI、事件与异常格式。**通过条件**：追踪关闭时共享生成行为一致；ID 与轮次对应；当前/未来信息边界正确；真实工具结果来源可追溯。

## 5. 阶段 C：64题探针与数据审核

在同一64题、同一检索与学生预算下评估候选强教师和 Base；每题最多8次采样。两种教师最多1024次轨迹尝试是总上限，实际调用成本与采样参数分别记录。基础设施错误设有限重试并另计成本，不算普通答错，不无限重试。

检查答案正确、think/动作闭合、恰当动作、证据可见与多跳关系、真实工具调用、无模型自写 information、无强制结束/目标截断/严重循环。每题固定顺序取第一条审核合格完整轨迹；全部失败保留原因。所有拟保留探针轨迹人工复核。

报告合格题比例、尝试数、来源/长度/行为分布、循环与错误类型，以及每条合格轨迹成本。正式教师按这些指标选择并冻结，通用榜单只作为候选依据。若弱教师仅产出容易单跳题，不靠增加容易题凑规模；强教师也不足时先修订新版本再扩大。

选定教师后按冻结候选顺序扩大到 S256/S1000/S_val。正式至少10%分层人工复核，所有风险、多跳证据不确定和改写查询轨迹额外复核；系统性错误暂停相关版本并扩大审查范围。错误输出留在审计记录中，不作为正向交叉熵目标。

**交付**：全部尝试 JSONL、证据定位/审核文件、教师选择报告。**通过条件**：审核可信且行为覆盖可解释；不足如实报告；强教师私有信息不进入学生输入。

## 6. 阶段 D：转换并发布逐轮数据

每个真实模型调用一行，字段至少包括 sample_id/question_id/source/trajectory_id/turn_id、context_ids、target_ids、N_q、sample_weight、student/teacher/tokenizer/protocol/review/trace 哈希。原始追踪与 gold 存独立审计文件，Dataset 不加载未来轮次或标准答案。

输入 `context_ids + target_ids`，context/历史/工具/padding labels 为-100，当前 target labels 为真实 token。用 `logits[:, :-1]` 预测 `labels[:, 1:]`，若保留 mask 则与 labels 同位置并移位 `[1:]`。首/末 target 都参与损失；pad=eos 时 attention_mask 以长度产生；搜索轮不人工追加 EOS。

初版动态右侧 padding，关闭 packing/remove_padding，context+target≤4096、truncation=error。缺轮次、空目标、超预算、版本错误或未审核的整题拒绝，不发布残缺轨迹。冻结 Q（不同问题）、M（展开样本）、N_q（整题有效目标 token 数）：

```text
L = (1/Q) * sum_q [sum_(turn,target token) CE / N_q]
sample_weight = M / (Q*N_q)
batch_loss = sum_(real rows,target tokens) sample_weight * CE / B
```

B 为本次真实全局行数。逐行均匀采样对应按题 token 平均，不能再按每轮或每卡 token 数分别归一化。S256/S1000 分别计算自己的 Q/M/N_q/权重和 manifest，不能直接复用父数据集的权重。

数据发布目录包含 candidates、attempts、reviews、prepared/train.parquet、prepared/val.parquet、manifest.json；校验成功最后写 COMPLETE.json。大数据与轨迹留在仓库外产物目录，Git 只保存代码/配置/文档。

**通过条件**：全量隔离/完整性/token 边界/审核和文件哈希检查通过，统计由实际数据计算，无漏题、重复行或缺失目标。

## 7. 阶段 E：关键训练代码修改

模块按职责拆分，下面均为拟新增/修改文件，当前尚不存在或尚未实现对应功能。

| 模块 | 修改内容 |
| --- | --- |
| `verl/experimental/cold_start/manifest.py` | 配置和数据版本、隔离、来源分层、教师/协议指纹；CPU 核心 |
| `cold_start/trajectory.py` | 事件/完整轨迹校验、证据审查状态、逐轮转换与统计 |
| `cold_start/teacher.py` | 教师窄接口、适配与学生上下文重放；本地/API实现与核心分离 |
| `cold_start/reporting.py` | 教师合格率、成本、数据分布与评价汇总 |
| `search_r1/llm_agent/generation.py` | 可选 trace_sink，复用后处理/检索/观察/结束边界 |
| `verl/utils/dataset/sft_dataset.py` 与 `__init__.py` | 补通用 SFTDataset 与逐轮格式，labels/mask、版本及长度校验 |
| `verl/utils/dataset/sft_sampler.py` | 确定性全局批次、跨卡分片、尾批占位、更新边界游标 |
| `verl/utils/sft_loss.py` | 正确移位、问题权重、全局分母和可测试的后缀 CE |
| `verl/utils/sft_checkpoint.py` | 独立 SFT 恢复格式、原子发布、HF导出与哈希核验 |
| `verl/trainer/fsdp_sft_trainer.py` | 最小接入数据/损失/精度/scaler/日志/保存恢复；清理自身重复导入 |
| `verl/trainer/config/sft_trainer.yaml`、`sft_cold_start.yaml` | 通用默认兼容；冷启动专用参数、路径、版本与数值设置 |
| `scripts/cold_start/{prepare,collect,review,evaluate}.py` | CLI只做参数、IO及组合，不复制核心算法；默认检查不启动GPU |
| `scripts/cold_start/train_sft.sh` | preflight、torchrun、资源锁、日志、退出与恢复入口 |
| `tests/test_sft_*.py`、`test_cold_start_*.py` | 按真实边界测试，不以GPU模拟替代实测 |

依赖方向：CLI/运行适配 → 数据与核心算法；trainer → 通用 dataset/loss/checkpoint。核心不依赖 Ray、GPU、具体组名或本机绝对路径；不 monkey patch、不持有 trainer 全状态。

精度选 FP32 主权重、FP16 前向、FP32 reduce/buffer，ShardedGradScaler 初始16，开启非重入梯度检查点、use_cache=False。每次真实更新：全部微批 scale(loss).backward → 一次 unscale → FSDP clip1 → scaler.step/update；scale 在累积内一致，scheduler 仅随真实更新前进。任何非有限梯度或跳步使先导按数值失败停止，保留完整失败记录。

全局 batch32，初版每卡微批1；世界大小 W=4/8 时全局 micro=W，累积32/W次。配置不原地除卡数。尾批补合法零权重槽位，真实样本不丢弃/复制；零样本 rank 仍参加同序 collective。先跨卡取得真实 B，若 FSDP 按卡平均，则本卡反向分子乘 W/B，不再除累积次数。验证统计全量加权分子，按冻结目标归一化，不平均各卡或各批的均值。

显存先使用安装版 `logits_to_keep` 限制输出到当前 target 的预测位置，再对 CE 以256 token块稳定累加，不计算熵。微批裁去共同右侧 padding；后缀覆盖最早 target 的前驱位置，不能只用“最大目标长度+1”处理混合长度批。完整路径与优化路径概率/损失/梯度必须核对。FSDP 原生参数 CPUOffload 在累积路径关闭；如需 optimizer 状态卸载，复用已有搬运工具并单独验证，不能凭进程跑通判断更新正确。[PyTorch 2.6 FSDP](https://docs.pytorch.org/docs/2.6/fsdp.html)、[AMP 累积说明](https://docs.pytorch.org/docs/2.6/notes/amp_examples.html#gradient-accumulation)。

保存模型、各 rank optimizer/scaler/RNG、scheduler、数据/配置/拓扑版本、下一全局批游标、consumed_batch/optimizer_step。只有逻辑更新边界可发布；所有分片完成后最后写 COMPLETE。HF 推理导出与恢复状态区分；缺文件/哈希错误/数据配置变更拒绝恢复，首版只支持相同拓扑。

## 8. 阶段 F：启动前的分层验收

| 层级 | 实际验证 | 放行条件 |
| --- | --- | --- |
| CPU核心 | 隔离/近重复、模型工具来源、未来信息、pad=eos、首末target、权重、尾批、游标与坏版本 | 全部真实边界测试通过；负例应拒绝 |
| 入口检查 | MetaX环境导入、展开配置、假数据预检、batch/设备数检查 | 无缺失导入；路径/格式/精度错误在训练前报出 |
| 小模型GPU | FSDP通信、2次更新、保存恢复与HF重载 | 实际梯度有限、参数改变、拓扑与更新顺序正确 |
| 7B短跑 | 用正式Base与真实审核样本，在目标4/8卡拓扑运行少量更新 | 显存/CPU峰值、FP16稳定、全局损失和日志正确 |
| 恢复对照 | 同序数据连续2步，对比第1步保存后恢复到第2步 | 顺序/RNG/计数一致，参数和输出在启动前规定容差内 |
| 推理导出 | 独立HF冷加载并完整调用检索 | 权重/配置/tokenizer哈希与版本匹配，缓存条件明确 |

小模型通过不能替代7B实测。GPU探针需要单独run_id和数据，不消耗正式S256一轮预算；S256正式训练从Base重新开始。CPU/GPU与注释验收记录分别保存，每批同步实现文档、步骤和台账。新增/修改函数具备中文 @brief/@param/@return 等说明，关键逻辑单元覆盖≥50%。

## 9. 阶段 G：启动 S256 一轮训练

优先先导使用4张已确认空闲的 C500；batch32、每卡微批1、累积8。若资源与吞吐要求选择8卡，则每卡微批1、累积4；在启动前固定拓扑并重新跑对应7B与恢复验收。SFT阶段不需要在线检索，GPU7的既有retriever可以保留，只使用实际空闲设备。计划不终止其他任务以抢卡，也不预设目前所有GPU空闲。

启动预检逐项核对：

- branch/commit和允许的dirty快照；发布数据/模型/tokenizer/协议/审核哈希。
- GPU实际占用、通信与所选attention可用；MetaX隔离环境与精度配置。
- run目录唯一、运行锁、磁盘/CPU内存足够覆盖恢复分片与HF导出；不覆盖旧产物。
- global batch/micro/累积可整除；数据至少一个真实更新；S_val定义及尾批合法。
- total_steps 与 scheduler/fit共用 `ceil(M/32) * epochs`，warmup=ceil(5%*steps)，短跑上限同时作用于二者。
- C0冷缓存D256基线已有可核验结果，或在同一评价协议下重新建立；旧污染D32不当门槛。

按一轮的25%/50%/75%及末步保存（取整去重），S_val相同节点评价；每次真实更新记录loss分子/分母、lr、grad_norm、scaler、是否更新、样本/token数量、耗时和峰值显存。初版选择预定的末步作为C1，开发曲线用作诊断，不边看边无限追加epoch。

以下是**拟新增入口的调用约定**，脚本尚未实现，命令本次未执行；真实路径、run_id和GPU由预检输出填入：

```bash
# 题目和数据准备；config需已写入可核验源路径、教师与协议
python scripts/cold_start/prepare.py --stage candidates --config "$DATA_CONFIG" --output "$DATA_DIR"
python scripts/cold_start/collect.py --config "$TEACHER_CONFIG" --questions "$PROBE_FILE" --output "$ATTEMPT_DIR" --start
python scripts/cold_start/review.py --attempts "$ATTEMPT_DIR" --reviews "$REVIEW_DIR"
python scripts/cold_start/prepare.py --stage rows --config "$DATA_CONFIG" --reviews "$REVIEW_DIR" --output "$DATA_DIR"

# preflight成功、验收证据齐全后，才显式启动
bash scripts/cold_start/train_sft.sh --config "$TRAIN_CONFIG" --run-id "$RUN_ID" --gpus "$GPUS" --preflight-only
bash scripts/cold_start/train_sft.sh --config "$TRAIN_CONFIG" --run-id "$RUN_ID" --gpus "$GPUS" --start
```

wrapper 通过 `env/metax/run.sh -m torch.distributed.run` 启动既有 SFT trainer，无需 Ray；关闭默认HDFS上传，训练状态与日志保存在独立本地产物目录。采集脚本按教师环境选择运行器，不能把所有教师都强塞进学生MetaX venv。

## 10. 失败处理、评价与放大

OOM/非有限梯度/通信错误/写盘失败记录真实退出和最后完整检查点，不杀其他进程、不自动回退为截断目标或静默丢样本。只在相同数据/代码/精度/拓扑下从COMPLETE恢复；改变微批、offload或backend必须新版本并重新验收，不能宣称精确续跑。检索服务错误影响采集/评价，不污染模型答题失败统计。

S256完成后校验末步COMPLETE及HF文件，独立冷加载评价D256单题单轨迹，记录整体/来源EM、合法过程正确、缺答案、forced_final、模型自写information、重复查询及实际成本。C1−C0衡量SFT收益；S_val loss仅是拟合诊断。收益不确定或过程变差时先审查数据/训练链路，不投入正式预算。

通过后使用S1000从同一Base独立训练一轮，首个正式seed42；更多种子属于后续预算。C2=Base→RL，C3=同一SFT→RL，保持修复后的缓存、奖励、题池和RL参数一致，actor KL继续0.001；C2 reference为Base，C3 reference为SFT起点，两组启用全新RL状态。先25周期方向检查，再覆盖60/80/100节点验证后期稳定性。教师来源与SFT收益明确记录，T2000仅在方案锁定后统一评价。

## 11. 提交顺序、产物和时间估算

建议按可审查功能提交：①配置/候选/manifest，②教师适配/trace/探针，③审核/逐轮数据/Dataset/mask/损失，④FSDP精度/采样/日志，⑤保存恢复/导出，⑥启动/评价。数据和训练模块的CPU开发可以独立推进，实际探针与训练按依赖和资源顺序执行；不需要另开用户线程。

每次真正运行才建立run_id，记录源码提交/dirty快照、展开配置、设备、命令、日志、产物及可恢复状态。拟产物目录：仓库外 `data/runs/sft-mx/<data_version>/` 存候选/轨迹/审核/训练数据；`runs/<run_id>/` 存训练日志、状态、检查点、HF与评价；Git只记录程序、配置和汇总文档。

时间不沿用RL的每周期耗时来估算SFT。64题探针测每条合格演示成本；7B短跑测初始化、每次更新、保存和重载。用 `T_sft≈T_init+ceil(M/32)*T_update+T_save+T_val` 单独估算，D256完整检索耗时另计。M为实际展开行数，当前未知，不能把1000题写为1000更新或承诺固定小时数。

本轮完成的是静态代码/安装版本核对和计划；未新增训练源码、未制作正式轨迹、未运行新代码测试、未调用教师或启动训练。下一步从候选/schema及教师桥接接口开始实现，阶段通过后继续到GPU验收和S256正式启动。
