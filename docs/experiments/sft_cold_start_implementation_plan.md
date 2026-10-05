# R1 SFT 冷启动：代码修改与验收计划

日期：2026-10-03。负责人：Codex。状态：技术设计；未修改训练源码、创建开发分支、制作演示或启动新训练。

## 1. 开发基准与实现边界

以远程 `/mnt/public/code/lyk/lzy/R1-vllm-metax` 的 `data-difficulty-muxi` 分支提交 `7a9789a306aa4231665cbed3ad0d03457839d1c1` 为基准，后续在独立 SFT 开发分支实施。该基准包含 v4 使用的答案元数据与 token 分块修复，以及新的中文注释约束。保留当前 v4 的运行目录、配置、权重和进程。

研究范围继续限定为“是否先 SFT 冷启动再 RL 更好”。C0=Base，C1=Base→SFT，C2=Base→RL，C3=同一 SFT 权重→RL。先导 256 道 SFT 题、两条 25 周期 RL；正式 1,000 道 SFT 题、两条最多 100 周期 RL、3 个训练种子。SFT/RL 题目重叠比例研究暂不实施。

当前源码已确认：

- `verl/trainer/fsdp_sft_trainer.py:38` 导入不存在的 `SFTDataset`；第 46 行顶层导入 `peft`，当前环境缺该包，全参数 SFT 也受影响。
- 旧入口写死 BF16；`_compute_loss` 对 label 使用 `[1:]`、对 mask 使用 `[:-1]`，必须先重新定义 mask 的 token 位置语义，再修改移位。
- `_normalize_config_bsz` 将 train/micro batch 都除以卡数；微批大小在旧配置中是全局值。
- 旧训练按微批平均、尾批丢弃；调度器与提前停止使用的步数来源不同。`resume_path` 不构成完整恢复实现。
- 检索生成器已有有界上下文、观察裁剪、模型/环境 token 区分和确定性评价设置，但没有足够的逐轮可见输入及检索原始返回记录。

## 2. 预计修改文件

以下为拟定路径，最终以实施 diff 为准。

| 文件/模块 | 具体职责 | 接入边界 |
| --- | --- | --- |
| `verl/experimental/cold_start/__init__.py` | 冷启动实验包入口 | 无 GPU/Ray 初始化副作用 |
| `cold_start/manifest.py` | 题目隔离、分层选题、数据/教师/协议哈希及版本检查 | 输入普通记录和配置，输出冻结 manifest |
| `cold_start/trajectory.py` | 校验完整演示、转换逐轮 token 样本、统计问题级权重 | 不自行生成、检索或判分 |
| `cold_start/reporting.py` | 汇总四组逐题效果、筛选和成本 | 不选择最优 T 结果或修改训练 |
| `verl/utils/dataset/sft_dataset.py` | 补齐 `SFTDataset`；通用 prompt/response 和预分词逐轮格式 | 不依赖 cold_start 包、Ray 或运行目录 |
| `verl/utils/dataset/sft_sampler.py` | 可恢复的全局批次顺序、跨卡分片、尾批占位 | 从 manifest 获取稳定行 ID |
| `verl/utils/dataset/__init__.py` | 导出 SFTDataset | 保留已有 RL/RM 导出 |
| `verl/utils/sft_loss.py` | 移位 CE、样本权重、全局归一化辅助函数 | CPU 可独立验证，无检索逻辑 |
| `verl/utils/sft_checkpoint.py` | SFT rank 状态保存/恢复、HF 导出和完成标记 | 不反向依赖实验包，不改变现有 RL checkpoint 格式 |
| `verl/trainer/fsdp_sft_trainer.py` | 可配置精度/scaler、数据和损失适配、训练调度、恢复/导出 | 复用训练骨架，移除不必要的自身模块重复导入 |
| `verl/trainer/config/sft_trainer.yaml` | 补充通用入口所需配置默认值 | 冷启动之外保留原默认行为；修复项单独登记 |
| `verl/trainer/config/sft_cold_start.yaml` | 冷启动专用数据、精度、预算及输出设置 | 显式覆盖基础 SFT 配置 |
| `search_r1/llm_agent/generation.py` | 可选逐轮 trace sink，记录真实输入/后处理输出/检索结果 | 默认关闭；关闭时生成、检索和奖励行为一致 |
| `scripts/cold_start/prepare.py` | 冻结题目与制作已审查的逐轮训练数据 | CLI 只解析参数、读写文件和调用模块 |
| `scripts/cold_start/collect.py` | 初始化现有 rollout/检索组件并采集教师演示 | 复用 LLMGenerationManager 与 RewardManager |
| `scripts/cold_start/train_sft.sh` | 经 `env/metax/run.sh` 调用 torchrun 和 SFT 配置 | 参数化路径、GPU、seed、run_id |
| `scripts/cold_start/run_rl.sh` | 校验 HF 导出、构造 C2/C3 初始化与输出配置 | 调用已有 RL 入口，不写第二套 RL 主循环 |
| `scripts/cold_start/evaluate.py` | 对各 HF 权重执行同协议完整检索评价 | 独立评价；不使用固定四轨迹的难度评分函数替代单条 EM |

另新增约 6 个 CPU 测试文件，覆盖 manifest、轨迹、dataset/mask、权重/分布式归一化、sampler/恢复、导出及组间配置。细化后预计约 **22–27 个代码/配置/测试文件，2,600–4,300 行净新增或实质修改**，文档另计；这是静态估算。此前 14–20 文件/1,800–3,300 行为初步估算，本版明确加入尾批一致性、训练恢复、采集追踪和同协议评价，因此上调。

## 3. 数据制作：先获得可审计的完整检索演示

### 3.1 题集与 manifest

从原 NQ/HotpotQA train 中排除完整 P10000、D1000、T2000。稳定 ID 与规范化文本均查重；近重复筛查阈值和人工判定规则在生成前冻结，不把字符串不同直接视为无泄漏。

先冻结待尝试的候选题目顺序，按来源约 47%/53% 分层。记录不同来源、问题长度、尝试次数和合格率。只能在候选清单中按固定顺序取合格题，不因模型答题结果临时更换分层策略。64 题探针不足时先报告教师合格率及成本，再决定是否修订教师方案。

manifest 至少包含：schema_version、源文件/P/D/T/问题清单哈希、Base/tokenizer 版本、教师权重和生成协议哈希、检索索引/编码器/topk、seed、最大尝试数、选择顺序、审核版本、原始轨迹清单、样本行 ID、不同问题数 Q、展开样本数 M、每题有效目标 token 数 N_q。

256 题先导嵌套于正式题集。D256 用于完整检索 EM 和协议表现；SFT teacher-forcing 验证若需要单独数据，从 SFT 候选之外划独立 S_val 并记录，不能把 D/T 轨迹并入 SFT 训练或使用 teacher-forcing loss 代替 EM。

### 3.2 逐轮记录接口

在 `LLMGenerationManager` 增加可选 `trace_sink=None`。sink 留在调用方；生成器只发送结构化记录，不认识 C0/C1 等实验组，也不自行写固定路径。事件中的 tensor 在启用记录时复制为 CPU token 列表，不保留 GPU 张量或计算图。

记录位置及字段：

1. `_generate_with_gpu_padding` 调用前：经过有效长度处理后的真实 `input_ids`、attention/position 信息、原始轨迹 ID、attempt_id、turn_id、sampling seed；记录发生在复制补齐行之外，不能将 GPU 补齐行计入数据。
2. `_postprocess_responses` 后：当前轮保留的 assistant token IDs、原始输出、闭合的动作标签、停止原因。训练 target 使用 RL 实际保留并重新分词的输出，原始 vLLM 输出只用于审计。
3. `_batch_search` 返回后、格式化前：查询、真实返回 passages、分数和检索耗时。原生文档 ID 存在时保留；不存在时使用索引版本与文档内容哈希作稳定身份，不能把“Doc 1”称为检索文档 ID。不得为追踪再发一次检索请求。
4. `_process_next_obs` 后：模型下一轮实际可见的 observation token、裁剪标记和预算。下轮输入以记录的真实 token 为准，不能用完整原始文档回填。
5. 轨迹结束：使用当前 `response_only_v1` 与 `info_mask` 判分，记录标准答案、正确性、自然/强制结束、调用有效性和审核状态。标准答案仅在独立审核字段中，不拼入学生输入。

主方案教师为未经过 RL 的同一 Base。每题最多 8 次尝试，只保留一条合格轨迹；保留失败尝试的成本和原因。检索服务错误记为基础设施失败，不当作普通错误答案。正确最终答案还需满足真实工具调用、标签闭合、无被迫结束及证据支持；分层人工复核至少 10%。未通过审核的轨迹不得进入最终训练 manifest。

### 3.3 预分词数据格式

原始轨迹采用可审计 JSONL；冻结训练数据采用 Parquet。每行对应一次真实模型调用，至少有：

```text
sample_id, question_id, source, trajectory_id, turn_id
context_ids: list[int]       # 本轮生成前实际可见的非 padding token
target_ids: list[int]        # 本轮实际保留的 assistant 输出
question_target_tokens: int # N_q，整题所有保留轮次的有效 target token 数
sample_weight: float        # M / (Q * N_q)
protocol_hash, tokenizer_hash, review_version
```

多轮样本的 context 可包含以前的 assistant、检索观察和反馈；只预测本轮 target。不套用新的 chat template，不从文本重新猜测角色边界，不人为追加搜索轮 EOS，不把 teacher 提示或未来观察引入该轮输入。空 target、超过协议预算、缺审核或版本不符均报错；不静默截断 target 来凑长度。

## 4. Dataset、mask 和问题均衡损失

### 4.1 Dataset 输出与正确移位

`input_ids = context_ids + target_ids`。labels 与 input_ids 位置对齐：context、环境文本、历史 assistant 和 padding 对应位置设为 -100，当前 target 对应位置保留 token ID。attention_mask 由真实长度产生，不能仅比较 pad_token_id，因为 pad 与 eos 可能相同。position_ids 从 attention_mask 累加生成。

计算时使用 `logits[:, :-1]` 预测 `labels[:, 1:]`。若仍输出 loss_mask，它也是 label 所在 token 的 mask，使用 `loss_mask[:, 1:]`；不能沿用旧入口的 `[:-1]` 配合新定义。首个 target token 必须有 loss，最后一个 target token 由前一个位置预测，环境与 padding 全部无 loss。

SFT 使用动态右侧 padding，最大长度 4096，`truncation=error`。初版关闭 packing 和 remove_padding，先验收标签边界与上下文一致性；后续性能优化另作独立版本。

### 4.2 明确问题均衡的数学定义

本版选择“每题的全部目标 token 平均，再对题平均”，不选择每轮等权：

```text
L = (1 / Q) * sum_q [sum_(turn, target token) CE / N_q]
```

逐轮样本均匀采样时，对每个 target token 使用已冻结 `sample_weight = M / (Q * N_q)`。某全局更新批次有 B 个真实逐轮样本，则其损失估计为：

```text
batch_loss = sum_(real rows, target tokens) sample_weight * CE / B
```

该估计在均匀逐轮采样下对应上面的按题目标；不宣称每个有限 mini-batch 都含相同数量的完整问题。多轮、长轨迹不会仅因目标 token 更多而在完整数据目标中获得更大问题权重。Q/M/N_q 由冻结数据计算，不按当批长度临时修改，不按各卡 token 数分别归一化。

### 4.3 梯度累积与跨卡归一化

沿用既有全局批量命名：8 卡时 global batch=32、global micro batch=8，即每卡 batch=4、每次前向 1 个样本、累积 4 次。新实现保留原始配置值，local batch/micro batch 单独派生，避免原地除卡数后污染日志与配置哈希。

先跨卡汇总本次逻辑更新的真实样本数 B。若 FSDP 通信按卡平均梯度，第 r 卡每个微批反向损失使用 `world_size * local_weighted_CE_sum / B`；多个微批的分子直接累加，不能再除一次微批数。普通 token_mean 模式另用全局有效 token 分母，不能混用两种归一化。

在 CPU 上比较单进程完整批与模拟分卡/不同微批拆分的损失和梯度；GPU 烟测再验证实际 FSDP reduction 语义。检查不等长度、只有部分 rank 有真实样本、尾批及零有效目标。全局无有效目标立即失败；单 rank 的零有效目标按零贡献处理，不能跳过其他 rank 正在执行的 collective。

## 5. SFT Trainer：精度、显存与训练状态

### 5.1 导入和构建

补齐 Dataset 后将 `peft` 改为 LoRA 启用时按需导入；首轮全参数 SFT，LoRA rank=0，不为此安装 PEFT。attention backend 复用已有 `get_attention_implementation`，不写死 FlashAttention；冷启动初始配置选择当前 MetaX 路径已支持的后端，SFT 单独验收。

沿用 FSDP FULL_SHARD 骨架、FP32 主权重、FP16 前向、FP32 reduce/buffer，非重入梯度检查点和 `use_cache=False`。dtype、attention backend、scaler 和卸载均由配置声明。旧通用入口保留 BF16 默认选项，冷启动配置显式选择 FP16。

### 5.2 FP16 更新顺序

使用 FSDP 对应的 ShardedGradScaler，初始 scale=16。一个逻辑更新内 scale 保持一致：全部微批 `scale(loss).backward()` → 一次 `unscale_` → FSDP grad clip=1 → `scaler.step` → `scaler.update`。使用与现有 actor 一致且经 SFT 单独验证的更新判据。

分开记录 consumed_batch、optimizer_step 和 skipped_update；任何非有限梯度或跳过更新使本次实验按数值失败停止并保存失败记录。scheduler 仅在真实更新后前进，不将消费的批次数当作有效训练更新。

初始超参：lr=5e-6、1 epoch、warmup=5%、global batch=32、global micro=8、max_length=4096、grad_clip=1。total_steps 只从同一个批次计划与预算函数生成；调度和 fit 共用。按展开 M 行计算预算，1000 题不等于 1000 步。

### 5.3 卸载与词表峰值

初版梯度累积时关闭 FSDP 原生 `CPUOffload(offload_params=True)`。PyTorch 2.6 文档明确说明 CPU offload 与 `no_sync` 外的梯度累积组合有正确性限制，不能仅凭能运行就接受。优化器状态卸载单独使用当前通用 FSDP optimizer 搬运辅助函数：反向后搬入、优化器更新后搬出；先在 SFT 中单独验证。

不要只把全序列 logits 切成小块后就声称解决显存：Qwen 词表大，4096 长度的完整 logits 已有峰值。逐轮 current target 位于有效序列末尾，可复用 Qwen 的 `num_logits_to_keep` 思路，只生成覆盖当前 target 的后缀 logits，保留首个 target 的预测位置；历史全部仍参与 causal attention。

这里必须处理动态右侧 padding：短样本的 target 可能远离张量末尾，不能直接设置“最大 target 长度+1”。先裁去该微批共同的右侧 padding；若张量宽度为 S、最短真实 context 长度为 C_min，则保留 K=min(S, S-C_min+1) 个末尾 logits，用绝对位置映射 label，确保最早 target 的前驱位置也在保留范围。微批只有一个真实样本时才退化为“target 长度+1”；不同 context/target 长度及尾批占位必须分别测试。占位行不参与 C_min；全占位 rank 仍执行合法的零贡献前后向和同序 collective。

后缀 CE/logprob 以可配置 token chunk（起点 256）和必要的重算计算，只计算概率损失，不计算熵。默认路径与优化路径的概率、损失和梯度必须一致；使用 FP32 稳定的 CE 累加，不能复制一套不同的 softmax 公式。若当前 transformers/backend 不支持后缀 logits，回退原计算并明确测量实际峰值，不以 chunk 标志推断显存下降。

参考：[PyTorch 2.6 FSDP](https://docs.pytorch.org/docs/2.6/fsdp.html)、[AMP 梯度累积](https://docs.pytorch.org/docs/2.6/notes/amp_examples.html#gradient-accumulation)。MetaX 兼容性须以本机 GPU 验证为准。

## 6. 数据尾批、验证和可恢复性

全局 batch plan 对 M 行先按 seed/epoch 排列，再按全局 32 行切分，每卡分到相同数量的槽位。尾批用带 `is_padding_sample` 的占位行补槽；真实行不复制，不丢弃。占位行提供合法可前向的 context，labels 全 -100、权重 0，不计 B/问题数/token 数。各 rank 前后向次数一致，真实样本按实际全局 B 归一化。

验证顺序不 shuffle；每个真实 ID 恰好计一次，聚合 loss 的分子与分母，不平均各卡/各批已归一化的均值。空验证集作为显式配置处理，不能对空列表 stack。

可恢复 sampler 保存 seed、epoch、全局排列版本与下一个全局 batch 游标；游标按真正消费完成的批次推进，不按 DataLoader 已预取位置推进。第一版固定 world_size/FSDP 包装配置，不支持跨拓扑精确恢复。

checkpoint 只在逻辑更新边界保存，包括：模型、各 rank 的 optimizer 分片、scheduler、scaler、Python/NumPy/Torch/设备 RNG、batch 游标、有效更新计数、配置/数据/协议哈希及拓扑。单独定义 SFT schema，不将现有 RL driver.pt 当成 SFT 可恢复状态。

同一文件夹区分训练恢复状态与 HF 初始化导出，例如：

```text
checkpoints/step_N/
  hf/                  # safetensors 分片、config、tokenizer
  rank_0.pt ...        # 训练状态与各 rank RNG
  trainer_state.json   # 游标、步数、配置/数据/拓扑信息
  COMPLETE.json        # 文件清单与 SHA256，最后发布
```

所有 rank 保存完成并同步后才写 COMPLETE；部分目录不供恢复或 C3 加载。检查点不能仅凭目录名视为完成。明确验证导出权重 dtype、配置与 tokenizer 文件完整性，并保留原 Base 的 tokenizer/特殊 token 语义。

## 7. SFT→RL 接续与统一评价

`run_rl.sh` 调用已有 RL 入口，C3 的 `actor_rollout_ref.model.path` 指向已校验的 SFT HF 导出；C2 指向相同 Base。当前 worker 由同一模型初始化路径构建 actor/reference，实施时核对配置展开与源码，若实际接口不同则只补最小明确的权重路径适配。

C3 reference 冻结为 SFT 起点；C2 reference 冻结为 Base。两组开启全新 RL optimizer/scheduler/scaler/采样游标和 RNG，不传入 v4 resume_path，不加载 SFT optimizer。同一 seed 的 C1/C3 共用同一份 HF 导出。

RL 保持 G8、每周期 8 道有效题/64 轨迹、补抽上限 8、P10000、奖励、检索、context/response 限制及更新参数。初始化配置校验输出两组展开配置的差异白名单：组名、权重路径、run_id/输出位置及其对应起点信息；冻结的研究参数必须一致。当前 v4 是否可复用为 C2，由配置/源码/数据/产物复核决定，不自动复用。

`evaluate.py` 复用同一生成管理器、检索服务和 RewardManager，执行单题单条完整检索轨迹，`do_sample=false`，各轮都保留确定性参数。不要调用固定 repeat_times=4 的 difficulty.score_batch 后挑最高奖励。

按每个 question_id 保存总体/来源 EM、动作与答案完成、实际成本。D256 是开发主指标，D32 保留历史诊断；T2000 只在方案锁定后统一评价。分别记录 SFT/教师拒绝尝试/RL 被丢弃候选/检索/评价成本。Base、SFT 后及 RL 保存节点均用同协议离线评价，SFT val loss 仅作为训练诊断。

## 8. 实施顺序与可审查提交

| 批次 | 代码工作 | 完成条件 |
| --- | --- | --- |
| A：schema/数据/损失 | manifest、逐轮 schema、SFTDataset、mask/权重、sampler、CPU 测试 | 首尾 target 对齐；环境/历史无 loss；隔离、尾批、微批拆分与分卡梯度核对通过 |
| B：教师采集 | 可选 trace sink、collect/prepare CLI、过程/成本与审核记录 | trace 关闭时行为一致；记录当前/未来信息边界、活动 ID 与 GPU 补齐一致；64 题探针可执行 |
| C：训练链路 | lazy PEFT、精度/scaler、后缀 logits/CE、批量预算和日志 | 环境导入通过；独立真实 GPU 更新有限且改变参数；参数/optimizer dtype 正确；实际显存记录 |
| D：保存/恢复/导出 | rank 状态、游标、COMPLETE、HF 文件 | 连续 2 步与第 1 步保存后恢复至 2 步同序列，数值符合预定容差；HF 重载输出一致；缺文件/损坏/错配置拒绝 |
| E：RL/评价 | C2/C3 wrappers、统一评价、四组汇总 | 新 RL 状态与 reference 起点核对；C0/C1 能完整检索评价；C3 能进入一个真实 RL 更新；成本不漏记 |
| F：256 题先导 | 冻结合格 S256，一轮 SFT、两条 25 周期 RL | 四组开发结果、有效更新、筛选分布及成本齐全；之后决定是否进入 1000 题/3 seed 正式实验 |

A–E 的 GPU 操作需要独立可用资源，执行前核查已有训练；本计划不抢占正在运行的 v4，不承诺与其并行训练。P/D/T、Base、protocol、tokenizer 与源码快照在实际启动时冻结；只有真正运行才创建 run_id。

## 9. 必须覆盖的验证

- **泄漏与轨迹**：S 与完整 P/D/T 互斥；检索异常保留为失败；未来 observation 和标准答案不进入当前 input；GPU 补齐不产生额外样本。
- **mask**：单 token target、首/末 target、搜索标签、环境中带 `<answer>` 文本、历史 assistant、eos/pad 相同、超长/空目标；只改环境位置的预测 logits 时损失不变，改变有效 target 时损失改变。
- **目标与分布式**：同题不同轮数/长度、零权重占位、不同微批拆分、不均衡 rank、尾批；无权重与问题均衡各与明确公式比较，不用实现自身生成“期望结果”。
- **精度/显存**：scaler unscale/clip/step 顺序、skip 判据、optimizer offload、完整/后缀/分块概率和梯度；GPU 实测峰值，CPU 测试不替代 FSDP/MetaX 验收。
- **恢复/导出**：同拓扑恢复、数据/配置/tokenizer 变更拒绝、不完整/损坏清单拒绝、HF 重载、SFT optimizer 不进入 RL。
- **公平与评价**：同题同协议单条 EM，C1/C3 同权重，C2/C3 初始 reference/状态正确，拒绝尝试与丢弃轨迹成本纳入统计。

所有新增/修改函数按控制文档补齐中文 `@brief`、`@param`、`@return` 及适用的异常/约束说明。关键逻辑就近解释；逻辑单元覆盖 ≥50%，函数与关键逻辑另外完整检查。每批提交前同步实现记录及进度，列出注释覆盖清单、实际检查命令、已验证/未验证项，避免将本计划写成完成结果。

## 10. 当前未完成项

本文件是静态代码计划。新 dataset、演示数据、SFT 入口修复、后缀损失、恢复/导出与 C3 接续均未实现；未进行新 CPU/GPU 测试。正式合格演示的数量、教师成功率、SFT 实际显存和训练收益均待实测。SFT/RL 重叠实验不在本轮范围。


## 2026-10-05 v4最终结果后的执行与验收补充

- 负责人Codex；v4已完成100周期、退出0、五份检查点哈希通过，最终D32没有净提升。具体配对分析、行为变化、成本及限制见[v4最终评估与下一步计划](v4_final_assessment_next_plan_20261005.md)。新计划均尚未执行。
- 先按既有数据隔离与单条评价协议冻结D256，建议排除历史D32并分层120NQ/136HotpotQA，先审标注后看模型输出；同协议评价Base及已保存step20/40/60/80/100。不存在step50检查点，不以其单次D32高分指定最佳权重。ID无漏重、标签版本、来源结果、配对区间、动作/缺答案及生成/检索分开计时作为验收。T2000不参与开发评分或训练。
- 若D256复现后期下降，按独立方案做同权重重启的学习率单因素诊断；重启状态不等于无缝恢复，reference与数据/采样/其他超参必须一致，配置变化需预登记。未确认下降时不同时扩展多项超参搜索。v4不直接追加训练，旧四轨迹与当前G8不作单因素归因。
- SFT主问题与四组对照继续，重叠比例延期。先补技术计划A–E与CPU/GPU/导出恢复验收，再64题演示探针、256题1epochSFT、seed42的C2/C3各25周期及共同保存评价节点。协议如调整，两组都按新协议重跑，旧v4不自动作为C2。
- 更新预算：50个RL先导周期按本次实测约29–39小时，正式600周期约350–463小时，数据制作/SFT/保存/评价另计；先导通过前不投入完整预算。D256不显著不能判等效或直接否定SFT，锁定模型/预算/评价后才使用T。
- 当前SFTDataset、cold_start采集与统一离线评价仍未实现。本次只有统计分析与文档修改，未改源码/训练参数、未运行新CPU/GPU测试、未创建训练分支或启动实验；代码注释覆盖率不适用。
