# GRPO 稳定性修复：阶段一

本阶段完成实现修复和 CPU 验证。保持 GRPO；未启动真实模型训练、评分或生成，未改奖励、优势归一化、学习率、KL 系数、裁剪半径或采样参数。MetaX 八卡与真实 FP16 融合算子的验收尚未执行。

## 已确认问题及修复

| 问题 | 修复 | 针对的风险与证据 |
| --- | --- | --- |
| val_only 的返回嵌套在 val_before_train 内；恢复分支也会绕过它 | 恢复后独立判断 val_only，评价一次立即返回；缺少奖励函数或与 score 冲突时失败 | 防止纯评价意外更新模型。CPU 覆盖两个开关组合、恢复步数、无奖励和冲突模式，训练更新调用为零 |
| 标为 max 的概率差指标最后被取均值 | 真正最大值用 max；新增可加总量用 sum；原损失均值保留 | 防止极端轨迹被均值掩盖。跨微批及 worker 数值归约回归通过 |
| GradScaler 逐元素检查不能涵盖有限梯度的范数求和溢出；关闭缩放时也可能更新非有限梯度 | 裁剪后检查全局范数；清空异常梯度。启用缩放则回退 scale 并跳步，未启用则抛错；异常时不装入 Adam 状态 | 防止参数污染。CPU 验证 NaN、inf、有限元素范数溢出、下一次更新恢复及状态卸载异常路径。没有证据表明原训练已发生这类非有限异常 |
| 原 Qwen2 LM head 参数 num_logits_to_keep 被当前接口忽略；实际只接受 logits_to_keep | 检查实际模型公开 forward 签名，支持明确的新/旧接口；未知接口失败；保留完整上下文 | 原实验 actor/ref 都开启该优化。旧 CPU 测试观察 [7,7]，修复后 [7,4]；概率输出、梯度及 CPU BF16 对照通过。属于已确认显存优化失效，不能认定为坍缩根因 |
| 原优化器更新指标为成功比例，无法表示 mini-batch 更新数 | 新增每 rank 的尝试、成功、跳步计数；旧比例保留 | CPU 两个 mini-batch 正确报告 2 次尝试、2 次更新、0 次跳步；跨 rank 汇总是每 rank 均值 |
| 缺少发生退化时的逐 token 和实际更新证据 | 新增默认关闭的稳定性模块及生成审计 | 下一轮可收集概率差极值/微批分位数、正负零优势 token 计数、加权分量输出端梯度、最多 256 个本地参数变化样本、固定轨迹更新前后概率、原始/消费 token 与原生 finish/stop reason |

## 数值与诊断边界

- safe_v1 保留正常区原公式和已有 KL 切线延续；增加二值掩码、形状、非空有效集、参数边界及相减溢出检查。极端概率比、零优势、有效位置 NaN、切换点值与梯度均有 CPU 回归。
- 分量梯度是在 log-prob/entropy 输出端的梯度，不能冒充完整参数梯度。参数变化只代表固定本地小样本。micro_p95 是微批分位数的均值，不是全局 token 分位数。
- 固定轨迹探针每个 mini 只保留首微批一条轨迹，额外一次前向；前后使用同 token、上下文和温度。非零模块/attention dropout 在任何更新前被拒绝，防止随机性污染概率位移证据。
- 原生 logprob 缺失时保持旧零值回退，但审计明确标为不可用。其他后端没有新增接口时不传新参数，不伪造 finish_reason。
- 实际 Qwen2 tokenizer 的 CPU 合成 token 案例确认 EOS 被后处理删除，同文本非规范 token 流可被重分词为不同 token 前缀。历史训练没有保存原始采样 token，无法估计真实频率或确认根因。本阶段没有改变重分词、EOS、消费边界或奖励。
- 轨迹探针尚未按合法动作分类，不能单凭总概率下降判定 LLDS。本阶段没有引入概率保护、DAPO 或 Dr. GRPO。

## 验证与范围

最终 CPU 全量 170 项通过，失败 0、错误 0、跳过 0；新增 38 项。明确排除需真实 GPU 的 test_fp16.py。完整共用生成循环覆盖搜索、观察、最终答案、活动行缩减/补齐、模型/环境掩码以及多候选元数据身份。小模型诊断开关前后参数更新逐元素一致；这些更新属于 CPU 单元测试。

实际原实验配置的恢复指纹兼容检查通过；默认模板除两个只读诊断开关组外逐字段相同。80 个新增/修改函数的语法、中文 @brief/@param/@return 检查通过，关键逻辑说明另有人工清单；git diff --check 通过。原有未提交记录保留，未提交或推送本次修复。

## 后续验收顺序

1. 先完成 MetaX 小模型 FP16、真实融合算子、FSDP 单卡及八卡一致跳步/卸载验收，比较全量与回答段 LM head 的输出、参数梯度和实际更新；记录显存，不把 CPU 对照外推为 GPU 等价。
2. 使用独立 val_only 入口对同一 checkpoint 做零更新核验；开启 token 审计，检查旧策略与 rollout 的 token、mask、温度和分布来源，量化 EOS/重编码问题。完整参数梯度归因、合法动作概率探针仍待实现或专门离线测量。
3. 再设计奖励/优势对照：优先检验全错组相对正优势和异常轨迹的整段强化。动态筛选、奖励门控、学习率/KL 约束分开改，一次一个变量；记录正确率、正常作答率、有效组、熵、KL、梯度和工具成本。
4. LLDS、Clip-Higher、token loss 和标准差归一化消融排在实现验收之后，各自需要对应机制证据。

本报告只证明实现与 CPU 验证完成，长期生成稳定性和后期退化是否改善尚未测量。


## 可复现信息与交接

- 运行标识：metax-grpo-phase1-20261010-v1；负责人 /root；方案步骤：GRPO 稳定性修复阶段一。
- 开始 UTC：2026-10-10T10:11:07.954831+00:00；验收 UTC：2026-10-10T11:06:58.832389+00:00。
- 分支 data-difficulty-muxi；基础 commit 6eb9de1d967248c60826e6fef3827d8a8256be1f；本次修复未提交/推送。
- 主机 mx；设备：CPU，验证子进程 GPU 不可见；原 MetaX C500 未参与本次 GPU 联调。
- 环境版本：`{"torch": "2.6.0+metax3.3.0.2", "transformers": "4.57.1", "vllm": "0.11.0+empty", "vllm-metax": "0.11.0+g55c59a.d20251211.maca3.3.0.15.torch2.6"}`。
- 数据/模型：CPU 内存样本和小参数模型；实际 Qwen2.5-7B tokenizer 仅离线加载分词文件。未使用 D256 生成，未加载真实 actor 权重。
- 当前实际训练步数：0；追加步数：0；评分/生成题数：0；新 checkpoint：无。父 checkpoint 不适用于本次 CPU 检查，原有模型保留。
- 关键验证命令：`ssh mx "cd /mnt/public/code/lyk/lzy/R1-vllm-metax && CUDA_VISIBLE_DEVICES='' bash env/metax/run.sh /mnt/public/code/lyk/lzy/runs/metax-grpo-phase1-20261010-v1/cpu_verify.py"`，退出码 0。
- 产物目录：`/mnt/public/code/lyk/lzy/runs/metax-grpo-phase1-20261010-v1`；源码快照和哈希见 final-manifest.json / final-source/；原始 dirty 证据见 baseline-manifest.json / baseline-dirty.diff。
- 日志：cpu-regression.final.log/json；tokenizer-config-evidence.json；source-audit.json；phase1-only.patch。
- 本次不进行训练恢复；后续验收必须先核查原进程和 checkpoint 完整性。原实验配置指纹对比仅隔离大模型身份扫描，不替代完整恢复联调。


## 失败、变更和验证历史

1. 基线优化器测试 3 错误：旧 SimpleNamespace 夹具无 .get，未执行到被测逻辑。
2. 初次批量替换因模板两个同名字段被写入前拦截；提前的发现运行找到 0 测试，不作验收。
3. 新增初版 26 项通过：phase1-tests.initial.log。
4. 全量 attempt1 为 164 项，1 失败、11 错误：旧夹具缺步数/接口参数，新测试两处 TensorDict 迭代错误，及已有 Qwen2 截断实现问题。cpu-regression.attempt1.* 保留。
5. attempt2 为 169 项，1 错误：新分块测试在 CPU 调用 GPU 融合算子，改用已有 CPU 参考后端模式。cpu-regression.attempt2.* 保留。
6. 之后 169 项通过；cpu-regression.passed169.* 保留。最后补加非零 dropout 探针拒绝，全量 170 项通过。
7. 最后注释补充仅改注释，AST 与已通过测试的实现一致。中间台账见 run-record.intermediate.md。


## 2026-10-10T11:40:06.978470+00:00 Phase1 submission verification

提交前 170 项 CPU 回归再次通过；新日志位于 submission-verification/cpu-regression.final.json/log，源码与原 final-manifest.json 哈希一致。保持训练步数 0、真实生成 0；GPU/FSDP 尚未验证。新验证与旧结果分开保存。

Evidence: /mnt/public/code/lyk/lzy/runs/metax-grpo-phase1-20261010-v1/submission-verification/; agent: /root.
