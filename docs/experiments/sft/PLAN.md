# 固定实验计划：DeepSeek 轨迹 SFT

版本1.0，2026-11-18。本文固定已确定的设计；资产和运行状态另见HANDOFF。数据发布或模型下载尚未完成时，不能把本计划当作验收完成记录。

## 1. 目标与分支

使用DeepSeek的成功搜索轨迹，对Qwen2.5-7B Base做离线SFT，比较Base、SFT和已有RL checkpoint60/80的效果、交互过程与成本。

- 仓库：`trickyzerg664/R1`；分支：`sft`。
- 代码起点：官方 `PeterGriffinJin/Search-R1@598e61bd1d36895726d28a8d06b3a15bed19f5d3`。
- 运行位置：host3 → lzy_yolo11 → `/root/myprojects/R1/R1`。直接使用原目录和Git记录，无额外worktree。
- 不整支继承fork main、data-difficulty-muxi或sft-mx的实验修改。历史RL文档用于确认模型身份、评价规范和结果，SFT代码集中在 `search_sft/`。
- 当前代码阶段不重新训练RL，不混入Qwen教师数据，不自动将主实验改成3B、Instruct、Coder、LoRA或QLoRA。

## 2. 学生与教师数据身份

学生：Qwen2.5-7B **Base**，与历史RL相同。逐文件校验依据 `configs/sft/base_model_hashes.json`，历史身份为 `bd3619d6054e534b7ab1dd0cbbdf05bd82d9c48f80b9d865d3db5cbff399efa0`。

公开来源 `Qwen/Qwen2.5-7B`，已确认官方快照 `d149729398750b98c0af14eb82c78cfe92750796` 的四个LFS分片哈希匹配历史记录。下载仍须对本地全部11个核心文件做SHA256校验，metadata匹配不等于权重已经下载完成。

教师：私有HF `tr1ckyzerg/R1-sft@a23313e8ef015b931abf5fa6c1704f14c4e1547d`，文件 `runs/b29ca10632104eae9b39963290fe9531/accepted.jsonl`。

- 原始3,011题，73,835,966字节。
- SHA256：`d210492c2583c878f466869010a43dcb25b86161f58af5ad181c1d5197f62519`。
- 只用该thinking-disabled、content显式think的DeepSeek成功批次；失败history不拼入监督数据，原始文件只读保留。

## 3. 数据政策与最终发布

1. 按规范化问题去重，原始3,011题去重后3,009题。
2. 保守移出首次检索前已提到题干外正确答案的955题；题干选项/末轮记忆表述另隔离，合计移出或隔离1,147题，剩1,862题。命中包括候选猜测，不声称全部已证明依赖记忆；保留原因与原始行号。
3. 学生tokenizer/协议重放额外移出32题单轮超256、16题需预算强制收尾，当前草案1,814题。
4. 严格排除历史D1000、D256、T2000、T1024、T128及相关官方test中的同题/明显近重复；原QA源train/test已有，但历史冻结清单仍需按真实版本对齐，不能临时随机切一份冒充。
5. 允许与历史RL训练池P10000重合，记录交集；缺少完整题池时写未核实，不记0。不能把训练池重合当作测试泄漏。
6. 检查每步推理只依赖该时刻可见信息，拒绝伪造观察、未来信息、严重循环、错误答案和不能完整重放的题。gold不在检索原文字面出现不单独作为删除依据。
7. 完成筛选、评价排重及语义复核后，按来源自然比例、seed42、规范化问题SHA256排序，约90/10分train/val；从train按自然比例取256题pilot。同题全部轮次同split。
8. 正式release不可原地覆盖；保留原始、评测文件、tokenizer、编译代码、split及数据文件哈希。pilot/full入口只接受final且已完成评价排重的数据。

| 当前draft，非最终发布 | 问题数 | assistant行 | 监督token |
|---|---:|---:|---:|
| train | 1,632 | 3,897 | 243,299 |
| val | 182 | 440 | 27,847 |
| train内pilot | 256 | 615 | 37,956 |

按batch32，草案pilot名义20次更新、full122次更新。正式数据可能减少，必须重新计算，不硬编码这些步数。

## 4. 逐轮监督和训练参数

每次真实assistant调用展开一行：输入为原问题及此前可见动作/观察；目标为当前 `<think>…</think>` 加一个search或answer动作。仅当前输出参与交叉熵，历史、工具结果和padding不计损失；不加入gold、未来观察或教师私有提示。

学生初始提示只按tokenizer的真实规则序列化一次，后续按连续生成边界追加token；不反复套聊天模板。使用学生tokenizer编码教师文本，不复用教师token ID。动作闭标签是消费边界，不凭空补EOS。

完整轨迹预算4096、每轮目标256、观察2048、最多10个assistant轮次。遵循历史bounded/structured规范，保留问题和完整动作历史，不截断target凑样本。离线训练不启动检索服务。

按题等权、题内有效目标token平均。Q题、M行，题q有Nq个目标token：行权重 `M/(Q*Nq)` 乘该行token CE总和，再按真实batch行数归一化。只在当前target位置计算LM head，包含预测首token的prompt末位置。尾批保留，不重复真实样本补齐；分布式dummy权重0。

| 项目 | 首轮固定值 |
|---|---|
| 更新范围 | 同一7B Base，全参数 |
| 后端 | Transformers4.47.1 + DeepSpeed0.15.4，ZeRO-3，CPU optimizer offload |
| epoch | pilot/full各1轮，独立从Base开始 |
| optimizer | AdamW，lr5e-6，betas[0.9,0.95]，weight_decay0.01 |
| 调度 | warmup5%（向上取整），cosine；仅成功更新推进 |
| batch | 全局32行，2GPU，每卡micro1，常规累积16 |
| 精度/注意力 | FP16动态缩放，FP32主状态/归约，SDPA |
| 其它 | clip1.0，seed42，非重入梯度检查点，use_cache=False |
| 关闭项 | BF16、FA2、packing、remove_padding |

## 5. 运行与存储

先验证程序与真实7B资源，再运行pilot。pilot验收后，full重新从Base和新optimizer开始。末步是预指定评价模型，不用T1024选择中间checkpoint。

完整恢复状态包含模型分片、optimizer、scheduler、动态scale、每rank随机状态、样本顺序/游标和代码/配置/数据身份。只在optimizer边界保存，恢复要求相同world_size、阶段及冻结身份。新完整状态确认后才清理本run旧状态；保留失败记录。

单run保存峰值约170.2GiB，含10%余量预留187.2GiB；这是新旧完整状态临时共存，不是模型权重本身。离线FP32导出约28.4GiB，导出在训练结束后执行。

部署采用项目盘放Base/环境/小数据，独立 `/root/data` 放checkpoint与导出，避免复制已有索引。计划pilot验收后仅长期保留HF模型及日志，full保留最近完整恢复状态；pilot优化器状态的实际清理/归档要在验收后执行并登记，不在当前准备阶段删除。该方案输出盘预留约215.6GiB，环境/模型新增约22–26GiB。若选择保留pilot全部状态，额外约85.1GiB，须重新核对空间。

目前CPU内存仍是需解决的资源项：7B ZeRO-3当前配置模型状态估算约113.5GiB，含默认余量170.2GiB；上次可用约106GiB。估算不是实测，不能从小模型通过推断7B能跑。若调整卸载方式，先记录设计差异、磁盘影响并重新验收。

## 6. 评价和成功标准

组别为C0=同一Base、R60/R80=历史RL、S-pilot、S-full。主比较预指定S-full对R80，另报对C0/R60差异。不同数据量、训练方法与成本的比较不称为所有因素严格控制的算法优劣。

统一评价采用同一prompt/tokenizer语义、greedy单轨迹、10轮、每轮256、观察2048、完整预算4096、Wiki18/E5/topk3、action-stop、bounded/structured和response_only_v1。历史规范依据 `data-difficulty-muxi@6ff2d742` 的formal-config及T1024记录，评价后端适配在独立工作区完成，不合入SFT训练管线。

主指标严格EM；语义复核作辅助且四组规则一致。分来源及宏平均、逐题差值/配对区间、自然完成/forced_final、协议异常、重复查询、搜索数、token量和成本分别报告。历史T1024已公开，只用于回归对照，不据此调参；最终泛化另冻结未用于决策的留出集。

正式运行须有唯一run_id、Git和文件身份、完整配置、设备、日志、成功更新/跳步计数、checkpoint验证及HF新进程冷加载证据。CPU/合成小模型验证、真实7B资源验收和真实数据效果三者分别记录。

## 7. 变更规则与依据

修改基座、数据筛选、监督目标、长度、训练组、超参数或评价规则时，追加新版本、变更原因和受影响运行；历史版本保留。部署路径、下载进度和资源快照更新HANDOFF，实际命令更新RUNBOOK。

历史结果依据：`docs/experiments/evidence/metax-five-model-test1024-20261014-v1/` 在GitHub的 `6ff2d742` 版本。原始Base严格EM229/1024，RL60为475/1024，RL80为488/1024；新硬件/后端正式对照需统一重评，不直接混用旧分数。
