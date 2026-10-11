> Checked UTC: 2026-10-10T11:42:28.658290+00:00; agent: /root; baseline commit: f20278902082e2bfc28c7a48a8d58e34482b38f3.
> CPU acceptance: 170 passed. GPU/FSDP acceptance: pending.

# GRPO 稳定性修复：第二阶段计划

状态：方案已制定，尚未修改第二阶段训练代码、启动生成或训练。保持 GRPO。

## 1. 目标与证据边界

第一阶段解决评价入口、极值归约、梯度异常保护、Qwen2 回答段 logits 接口，并补齐默认关闭的诊断。第二阶段优先验证“奖励差异怎样变成错误强化”，提高正常作答和工具交互能力。

原 100 步实验：/mnt/public/code/lyk/lzy/runs/metax-process-r1-100-b32-gpu-20261008-v2。
依据：train.yaml、metrics.jsonl、process-audit.jsonl、status.json，以及 final-D256-recovery-20261010-v1/summary.json。原训练已完成 100 个新增周期、3200 道入选题、25600 条入选轨迹；从旧 step40 权重重启并重置优化器，不能按旧绝对轮数解释。D256 从 step80 的 132/256 到 step100 的 129/256，后者出现 7 条缺答案；冷评价记录更新数为 0。小幅 EM 变化单独不足以证明整体能力显著下降。

step100 已保存的训练指标：KL surrogate 81.886、entropy 0.08464、grad_norm 50.228、scaler 16。这些是旧聚合口径下的指标，不能冒充第一阶段修复后的精确最大值，也不能将 KL surrogate 当作全分布精确 KL。历史有限数值并不证明没有数值风险，也没有证据支持将溢出直接认定为原根因。

## 2. 优先级和针对问题

| 优先级 | 工作 | 对应问题 | 证据等级 | 验证成本 |
| --- | --- | --- | --- | --- |
| P0 | 冻结第一阶段提交、验证和父模型 | 无法公平比较或将 CPU 验证外推至 GPU | 必要前提 | 低；真实 GPU 验收另计 |
| P1 | 分离任务成功与奖励方差，修正动态组资格 | 无任务成功的组因缺答案惩罚差异入选，错答获得正优势 | 代码和历史记录确认机制存在；退化贡献待实验 | 低至中 |
| P1 | 历史奖励/优势重放与真实 token 审计 | 原文本 EM、实际接受答案和训练奖励混淆；生成与更新序列可能不同 | 标签混用已确认；真实 token 失配频率待测 | CPU 低；生成审计中 |
| P2 | 有证据后调整消费前缀的协议门控 | 后续正确答案可能强化此前失败动作和无效重试 | 整轨迹优势广播确认；具体门控边界待分类 | 中 |
| P2 | 学习率或 KL 单变量对照 | 后期持续偏离 reference、低熵和大梯度 | 指标支持；主因和最优系数未确认 | 中至高 |
| P3 | 长度/标准差消融、动作概率保护 | 长度加权偏差、稀疏组放大、LLDS 假设 | 尚缺对应因果证据 | 高 |

## 3. 第一项最小修复：动态筛选按任务成功判定

现有 mixed_groups 在 finite 模式仅检查总奖励方差。当前奖励为：
R = accepted_answer_em × protocol_gate − 0.1 × missing_answer。

因此七条错答奖励 0、一条未作答奖励 −0.1 的组会入选。按当前样本标准差归一化，七条错答优势约 +0.35354，未作答约 −2.4748。模型学到的是组内相对优劣，奖励为 0 的输出仍可能被强化。提高惩罚系数在标准差归一化后大部分抵消，不能据此消除该机制。

建议新增显式 eligibility 配置，默认保留旧 reward_variance 行为。实验模式 task_success_mixed 使用：
S_i = 1 当且仅当执行器接受的答案 EM=1 且协议门控通过；
接受组必须 0 < sum(S_i) < G，同时奖励有限、完整同题组、无重复且方差满足现有要求。

首项修复保留奖励数值、缺答案惩罚、GRPO 标准差归一化、整轨迹优势、KL、熵、学习率和采样参数。先限制候选组资格，便于测量筛选贡献。该修复排除无成功组，并不保证混合成功组内所有错答优势都非正；不能把后一个指标当作本项验收条件。

实施位置：
- process_checks/reward.py：集中输出通过可信报告校验的奖励分量与 task_success，兼容原 process_score 浮点返回接口，避免复制协议判定。
- trainer/main_ppo.py：向现有逐轨迹报告传递 task_success、accepted_answer_em、原文本 original_em、门控和 returned_reward，评价继续报告原 EM。
- difficulty/dynamic_filter.py：复用 mixed_groups / training_batches，加入显式组资格模式和排除原因，不改变完整组补抽流程。
- difficulty/configuration.py、controller.py 及 ppo_trainer.yaml：校验模式与必需标签，记录恢复指纹和筛选策略版本。
- tests/test_dynamic_filter.py、test_process_checks.py、test_grpo_difficulty.py：扩展现有测试；优势公式复用 core_algos，不重新实现 GRPO。

缺少 task_success 的旧报告不得静默以 original_em 或总奖励方差代替新模式。离线重放可从可信事件、accepted_answer_em 和原规则重建，并标注推导来源。新配置必须进入训练指纹；旧模式缺省值规范化后维持历史兼容，新模式不能冒称严格续训。

代价：有效组减少，额外生成成本可能增加，选择的难度和来源分布可能改变。保留 max_rounds=16 和完整 32×8 批次；耗尽时沿用“没有完整批次就不更新”。先量化补抽可行性，不扩大补抽上限掩盖问题。

## 4. 实施顺序与验收

### 2A：历史离线重放

流式读取既有审计，按 trace_uid 关联候选和实际入选记录，再用 uid/question_id 构造完整八条组。只保留训练入选集合用于学习信号结论；候选保留率另算，禁止把 generation/train 两次报告重复计数。若不能从历史产物恢复某组身份，报告无法恢复的范围。

比较原规则与 task_success_mixed 的资格、优势、保留率。将 original_em、accepted_answer_em、门控后成功分别交叉统计，报告早/中/后期：
- 没有成功的入选组比例、这些组的正优势轨迹和正优势 token 占比；
- 缺答案、协议错误、长度上限、正常答案、成功重试及各来源分布；
- 每周期能否凑齐 32 个完整新问题组，候选轮数、生成 token 和检索成本。
历史缺原始 token/mask 时，只报告轨迹优势计数，token 占比标为不可计算；不从字符串长度伪造 token 结果。对超出现有候选记录所能支持的反事实补抽标为未知。

产物是分组统计与可复核样例；只重放既有数据，不产生训练更新。以原规则重算结果对齐记录为先决验收，发现原 EM 与接受 EM 差异时先解释差异。

### 2B：单独接入筛选修复

CPU 覆盖：全错混合惩罚、全对、正确/错误混合、正确但门控失败、原 EM 与接受 EM 不一致、残组、uid 错配、乱序、重复问题、无标签、NaN、补抽耗尽、旧缺省指纹和新模式恢复拒绝。

验收：旧开关行为一致；新模式所有入选组都含通过门控的成功与失败；组大小严格为 8；无成功组进入更新的数量为 0；不改变保留轨迹的奖励值和优势计算。开关与诊断进入独立配置，不将实验名称写入训练核心。

### 2C：生成一致性检查；有证据再修

复用第一阶段 record_token_diagnostics 和 stability_diagnostics，从固定正常父 checkpoint 采集少量完整多轮轨迹。检查原始/消费/重编码 token、EOS、实际 finish_reason、mask、观察裁剪、temperature、top_p 及原生 logprob 是否可用。

EOS 删除和非规范 token 重编码已有合成案例，真实发生率及影响尚未知。采样 logprob 若为截断分布，不能直接与完整 softmax 的 old_log_prob 比较。先确认双方定义与消费边界；不得用缺失 logprob 的零回退做概率证据。

仅在确认训练 token 与实际行为序列有不合理差异后，制定独立修复：保留消费前缀的原始 token 与精确边界，定义 EOS 和终止动作的训练位置。搜索后观察、下一轮拼接、最终回答、padding 与环境 mask 都需单独验收；不盲目给每轮追加 EOS。该变量不与筛选修复同时引入。

### 2D：协议与信用分配

当前 HARD_CODES 没有 missing_action/unclosed_action；无效动作后允许反馈重试。先将历史成功重试按长度截断、格式破损、无动作输出分类，区分实际消费前缀与未消费尾部，以及文字标签提及与真实角色伪造。

每种新门控规则独立重放、独立开关、版本化，量化正确样本误罚和零奖励增加。不得把缺动作一律当作恶意或异常，不对逗号等字符加特殊惩罚。未执行尾部继续不影响已接受动作奖励。首项筛选通过后才测试门控；逐动作信用分配属于更大算法变更，另列后续实验。

## 5. 对照实验

计划组名只用于设计，不生成未启动的 run_id 或结果：

| 组 | 相对共同基线唯一差异 | 目的 |
| --- | --- | --- |
| A0 | 第一阶段修复版本，原筛选/奖励/超参数 | 测量剩余退化 |
| A1 | task_success_mixed 筛选 | 测量无成功组排除效果 |
| A2（条件组） | 单项已验证协议门控 | 测量无效前缀强化影响 |
| A3（条件组） | 已确认的 token 对齐修复 | 测量训练/生成一致性 |
| H1（条件组） | lr 从 1e-6 降到 5e-7 | 测量更新幅度 |
| H2（条件组） | KL 系数从 .001 提到 .002 | 测量 reference 约束 |

H1/H2 只是预先指定的探索值，不是最优参数结论；分别相对当时锁定的共同基线，不与 A1 同时更改。组合实验只在单项贡献成立后开展。

父模型预先选原新增 step60，正常作答检查不通过时按预定规则退到 step40；各组必须使用同一最终父模型，不能逐组挑选。step100 只用于退化诊断。旧 checkpoint 的配置指纹会拒绝策略变化，优先使用统一 actor 权重冷起点、固定原 reference，并为所有组重置 optimizer/scheduler/scaler/RNG，以新 lineage 记录；不放宽旧严格恢复校验。结果仅证明这种共同重启设置，不能声称复现旧优化器历史或“再训练 20 步就是旧绝对 step80”。

锁定问题池、来源、seed、模型/tokenizer/reference、检索实现、32题×8轨迹、mini128/micro8、epochs1、FP16、clip .2、gradclip1、温度1/top_p.95、response256/max_turns10、观察和上下文长度。筛选改变补抽数量，无法要求各组逐条轨迹相同；配对种子与候选顺序，报告实际曝光和来源变化。

先完成 CPU 和真实 GPU 前提验收，再做 5 步接通验证、20 步筛选。20 步只证明可运行和早期变化；长期确认使用至少 100 个新增周期，并要求 A0 能展示剩余退化或明确报告未复现。若未复现，不宣布 A1 已修复后期坍缩。入围后至少三个配对种子。以相同更新预算比较能力，同时报告相同生成 token/检索/时长预算下的收益，防止靠更昂贵筛选获得表面优势。

## 6. 评价、停止与交付

主指标：正常作答率、原 EM、接受答案 EM、协议成功率、无答案率、广义重复/无效动作率。重复诊断采用统一词/token 窗口统计，只用于观察；不按某个字符制定奖励。并列报告问题来源和长度分层结果。

稳定性指标：KL surrogate 与 reference logprob 差、有效 token 熵、ratio/clip/边界占比、grad_norm、scaler、真实更新/跳步次数、固定轨迹概率位移、候选有效组和额外成本。记录各自归约定义，不能把输出端梯度当作全参数梯度。

沿用已有数值/资源监管；20 步探索后才冻结能力退化阈值，进入长跑后各组使用同一停止规则。非有限参数/损失立即失败；补抽耗尽不做部分更新。能力保护同时看正常作答和无答案，避免只依赖小开发集 EM。

D256 为已使用开发集，支持配对 bootstrap/McNemar 与曲线趋势，不能当独立最终测试。选项锁定后再用未参与选择的 T 评价，未锁定前不读取 T。

每项交付同步设计、步骤、实现记录和进度台账；保存代码哈希、配置指纹、父模型和规则版本、旧/新重放统计、CPU/GPU验收及真实运行记录。仅文档规划的代码注释覆盖率记“不适用”。LLDS、DAPO Clip-Higher、token-level loss、Dr. GRPO 标准差与长度消融留到对应机制证据充分后；本阶段不预设有效性。


## 7. 生成序列一致性的准确含义与实施细化

这里检查同一条 rollout 在采样、环境消费和梯度计算三个阶段的对应关系。GRPO 的 ratio 使用同一动作 token 和同一历史上下文下的新旧概率；模型更新后概率变化是正常现象。

实际路径：vLLM 原始 token -> batch_decode(skip_special_tokens=True) -> parse_action 的消费文本 -> _batch_tokenize(add_special_tokens=False) -> 多轮拼接 -> actor 重算 old_log_probs -> 更新策略。
old_log_probs 由 actor 重算，并未直接使用 rollout 返回的 logprob。新旧策略 loss 可以在处理后的 token 上一致，但处理后的序列仍可能与实际采样动作不同。当前审计确认的是路径和合成可发生性，真实比例与退化贡献未确定。

举例（示意，不是实际词表 ID）：采样 [A,B,C] 和重分词 [D,C] 可显示相同文本。直接把 reward 对应到 [D,C] 的 likelihood，并未逐 token 评价当时采样的 [A,B,C]。另一方面，首个 search/answer 后的未执行尾部被删除是合理消费边界，不能仅因长度不同就判错。

必须分别检查：
1. 保留的动作前缀 token 是否变了；消费字符边界是否落在一个 token 内部。
2. 各轮生成看到的问题、模型前缀、真实观察和提醒是否与 actor 对该轮 token 评分时的因果上下文相同；未来观察不可见。
3. EOS、动作闭合、长度上限、最终强制回答分别怎样结束，训练是否有对应的监督定义；不能在每轮盲目恢复 EOS。
4. 模型 token loss_mask=1，观察/环境反馈/padding=0；观察仍需在 attention 中作为后续动作的条件。logits 与目标 token 必须正确错位一位。
5. sampling temperature、top_p 及 logprob 来源。top_p 会改变采样分布；vLLM 返回的 logprob 是否包含截断/重归一化必须检查，不能预设。原生 logprob 不可用时不能用回退零值比较。

本轮已核对 bounded 路径保存完整原问题且超预算失败，actor state_masking 使用 loss_mask；这些实现已有保护，不作为已发现的新错误。

## 8. 各项实施包、验证与通过标准

### P0：真实 GPU 前提验收

在现有 CPU 170 项通过的基础上，用小型 Qwen2、实际 FP16/fused 算子和 MetaX 后端比较全量 logits 与回答段 logits 的 logprob、entropy、梯度和实际参数更新；同输入/权重/种子记录误差和显存。逐步验证单卡与八卡 FSDP，包含一个 rank 注入非有限梯度、有限元素范数溢出、所有 rank 一致跳步/scaler 回退、下一次有限更新恢复及 CPU 卸载往返。复用已有 actor/scaler 与 head 测试接口，不复制生产更新器。GPU 数值容差在对照前锁定，差异超容差视为失败。纯 val_only 使用固定 checkpoint 保存更新计数和前后参数校验，要求真实更新为 0。属于后续验证安排，本轮未执行。

### P1：历史重放

先使原奖励、group UID/trace UID 和训练入选集合对齐，再逐组使用现有评分与优势实现重算，避免重写公式。分别输出 original_em、accepted_answer_em、task_success 和奖励方差四项。按原 1-20/21-40/41-60/61-80/81-100 分段；给出无成功组的相对正优势占比、代表轨迹及新规则会丢弃的组。历史原始 token 缺失时只算可证明的轨迹统计，新增采样另算。验收是原规则重放一致、身份完整、重复报告不计入、反事实覆盖范围明确；只做离线分析。

### P1：筛选改动

引入三类显式字段：accepted_answer_em、protocol_gate、task_success。成功标签由统一的可信奖励分量函数计算，原文本 EM 继续独立保留。增加 difficulty.dynamic_filter.eligibility，缺省规范化为旧 reward_variance；新 task_success_mixed 要求 0<成功数<G 且当前 finite 条件成立。奖励值和 GRPO 标准差保持。
先 CPU 测试，再用同一父权重 A0/A1 接通、短跑和长跑。重点通过条件：无成功组进入更新数为 0；8 条同题完整组不变；旧模式兼容；不改变入选轨迹的奖励/优势；最大 16 轮不足则零部分更新。代价按 token/时间/检索和来源分布报告。该修复解决无成功组的错误学习信号，不代表从所有混合组中消除了错误正优势。

### P1/P2：序列对齐

先将原始 token、真实消费边界、processed token、轮次 trace UID、生成输入摘要及 mask 摘要放入既有审计；对未来新增诊断用窄接口传递。逐轮重建 actor 因果上下文，与实际生成输入核对。冻结参数时再比較 rollout/actor logprob，先统一概率定义与数值后端，避免把 FP16 舍入或 top_p 定义差异判作 token 错配。
若真实保留前缀发生重编码，独立开关试验保留原始 token 的消费前缀；原始前缀同步用于 next rolling context 与最终训练轨迹。字符切点在 token 内部时不能按字符数截 token，需先定义统一的 token 边界消费规则并验证 parser 动作语义，无法确定的样本显式拒绝新模式。不要在 scorer 单边替换 token。
CPU 覆盖 tokenizer 真实边界、尾部、EOS/pad 同 ID、跨轮观察、最终答案、重试、活动行减少及分布式补齐；GPU 冻结权重比较一致性。验收要求实际采样与更新目标有明确对应关系、环境 mask 正确、终止语义一致。改动单独对照 A3，不与 A1 同步引入。

### P2：门控与整轨迹强化

先将 missing_action/unclosed_action 成功重试按原生终止证据分类。历史缺该证据的样本保持未知，不能从文本强判。长度截断、字面量提及、未消费尾部、基础设施失败分别处理。客观协议破损可以候选门控；允许的续写/重试需预先定义规则。仅在误罚评审通过后添加单项规则开关和版本，复用 protocol.py/reward.py，不修改重复符号奖励。
原 GRPO 把正优势复制到整段模型 token，所以后续正确答案可能强化早前失败输出。门控减少部分整段错误强化，但可能增加稀疏奖励、抑制纠错行为。整轨迹 token 信用分配改动单独设计，不能把失败段 loss_mask=0 简化后直接声称已解决：屏蔽只移除正向更新，并不主动抑制失败动作。
CPU 重放真实正/负例与规则边界；A2 只改变一个门控规则。验收同时看正确样本误罚、有效组成本和正常作答率。

### P2：更新强度与 reference 约束

独立 H1: lr=5e-7，其余原值；独立 H2: KL coefficient=.002，其余原值。统一父模型、重置状态与 reference，以同一基线进行比较，原 grad_clip=1 与 ratio clip=.2 保持。降低学习率可能减缓学习，提高 KL 可能牺牲探索，不能只看 KL 变小。记录实际参数变化、正常作答/EM、reference delta、KL 切线区占比、熵与真实跳步。当前 KL 高端采用切线 surrogate，系数翻倍不会恢复精确 KL；若该区持续占比高，再单独检验稳定的 KL 约束实现或自适应控制，不能直接去掉数值保护。
短跑筛选不宣称长期稳定，长跑需要基线复现剩余退化并进行配对多种子比较。

### P3：后续机制消融

- Dr. GRPO 标准差：只移除组 std 除法并保持组中心化，记录有效梯度尺度；没有成功的组仍可能产生错答正优势，不能代替资格修复。
- 长度/Token-Level Loss：先量化响应长度与 reward/advantage/更新权重的关系。当前每 rank 一条微批通常先做轨迹 token 均值，再累积，不能直接改为每微批 token 均值并声称是全局 token loss。若采用 DAPO token normalization，需整个更新窗口跨 rank 的有效模型 token 分母，观察不计入；与固定长度分母实验分开，正确处理 gradient accumulation。
- Clip-Higher：仅上调正优势方向 upper clip，lower clip 保持 .8，记录低概率合法动作的 clip 阻塞率。只有现有正向裁剪限制探索的证据充分后测试，避免增加策略漂移。
- LLDS：冻结同一历史和合法动作集合，测量更新前后这些动作的条件 logprob，结合优势和 PG/KL/entropy 方向判断下降来源。总轨迹概率下降不能证明 LLDS；动作概率保护需明确适用动作和阈值，再独立消融，防止保护错误动作或已过时策略。

所有后续试验维持 GRPO。当前仅解释和细化计划，第二阶段源码修改/真实 GPU 测试/生成/训练均未执行；本次未重跑 CPU 测试，170 项属于此前阶段一提交前结果。


Checked UTC: 2026-10-10T12:12:09.902192+00:00; agent: /root.


## 2026-10-10T14:13:13.372171+00:00 2B implementation and CPU acceptance

任务成功筛选修复已实现并完成CPU验证，详见 [运行记录](runs/metax-task-success-filter-20261010-v1.md)。新增显式 task_success_mixed：成功为接受答案EM=1且原门控通过，要求成功与失败共存；保留奖励值和GRPO优势/超参数。旧模式兼容，新模式版本进入指纹，continue/branch不可切换资格规则。真实奖励完整补抽、身份/版本保护和零部分更新已接入；CPU198项通过，新增28项，GPU/长期效果未验证。原100步配置旧指纹和默认字段兼容检查通过，但隔离模型身份IO。真实模型生成/训练更新均0，未提交/推送。用户要求先做代码修复，完整历史重放2A尚未执行；下一步量化补抽成本并完成GPU前提。证据 /mnt/public/code/lyk/lzy/runs/metax-task-success-filter-20261010-v1；负责人/root。

Activation: difficulty.dynamic_filter.eligibility=task_success_mixed; enabled gated response_only_v1 training rewards required. Legacy remains reward_variance. CPU acceptance is separate from historical replay and GPU/long-run validation.


## 2026-10-11T04:44:58.595324+00:00 Reward design and root-cause replay

本次历史回放与奖励设计已完成，负责人/root；检查日期2026-10-11（北京时间），全部命令经ssh mx。详细报告见 reports/grpo_reward_rootcause_20261011.md；产物 /mnt/public/code/lyk/lzy/runs/metax-grpo-reward-rootcause-20261011-v1。3200个实际入选组、25600条训练轨迹及全部100步奖励均值对齐；81–100无成功组40.625%，占正优势轨迹48.05898%。任务成功口径41–60全失败组45，原文本EM口径44，不能混用。完整2A奖励/资格重放已完成；原始token/mask、真实终止元数据不足的子项仍未知，未做反事实真实补采。

发现原训练及当前actor的PG/Entropy/clip/ppo_kl只记录mini最后micro，KL记录全部micro，需优先修复指标覆盖并增加total_loss，不能伪造历史总loss。response_length包含环境文本；loss模型token/轨迹为216、264、282、333、245，不能据旧长度断定持续增长。根因最强证据为奖励方差资格与标准差归一化的错误强化；策略漂移与整轨迹信用问题强怀疑，LLDS/数值溢出/实际token失配因果未确认。

新增bounded_process_v2方案候选：R=S-min(.12,.1*M+.02*min(N_invalid,2)+.02*min(N_loop,2))；先独立启用一个新项，保留task_success_mixed资格。G8下成功R≥.88、失败R≤0且≥-.12，混合组均值至少.005，失败优势必负；仅代数验证，未证明训练效果。完整违规与原生截断区分；复用search_diagnostic，只对第三次起相同query且无新可见证据的循环候选软罚；不罚文风、普通回退、总长度，不针对字符。整轨迹广播仍会强化成功错误前缀，动作级PG屏蔽另做独立消融，KL/Entropy mask分开。

实施顺序：先真实GPU前提及全micro指标验收，再A0旧筛选/A1任务成功筛选；A2无效动作软罚、A3重复无新增证据软罚分别对A1；lr减半与KL加倍单独对照；确认token实现错误则先修、重锁基线。5步接线、20步筛选，长期100新增步/3配对seed；开发集与正常纠错评价、相同更新和rollout预算同时比较。监控仅配套保护，预防重点是信号、信用分配和更新偏移。真实模型生成0、更新0，无生产源码/配置修改、无新GPU实验或生产CPU复测，未提交/推送；上次198项仅适用原筛选修复。


## 2026-10-11T05:06:25.399661+00:00 LR/KL/reward trial validation planning

User confirmed lr=5e-7 and actor KL=.002. Validation plan: grpo_stability_trial_validation_plan.md. Common task_success_mixed baseline; separate B/L/K/R and LK/LKR comparisons; candidate bounded invalid-action reward remains unimplemented. CPU/history and GPU prerequisites before 5-step smoke, 20-step screen and selected 100-new-step/3-paired-seed confirmation. Independent EM/generation/recovery and cost metrics; no new training, model generation, source/config changes or tests. Planning only; no fabricated run_id. Agent /root.


## 2026-10-11T05:22:47.905170+00:00 Budget-limited trial plan

User total budget 1–2 days. Latest section7 of grpo_stability_trial_validation_plan.md supersedes mandatory six-arm/three-seed first round: only B vs target T(lr5e-7,actorKL.002,one validated process penalty), common task_success_mixed and paired seed42. Start20 new steps each, extend40 then60 only with value and time. Target first report24h, hard budget48h including preparation/evaluation/cleanup; share parent D256, mid fixed64 questions every20steps, final cold D256 per arm. Original historical training step means10.56–19.27min; D256~40min, new sampling cost unknown. No model workload/source/config changes or tests started; planning only, no run_id. Single-seed short/midterm results cannot claim long-term causal repair; conditional one ablation only. Agent/root.
