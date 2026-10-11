# 单次实验记录：metax-trajectory-readable-20261011-v1

## 当前状态

- run_id／实验组／attempt：metax-trajectory-readable-20261011-v1；只读日志CPU验收与真实历史预览；最终代码验收完成。
- 负责人：/root；主机mx；检查时间UTC：2026-10-11T06:02:30.196859+00:00。
- 方案：GRPO稳定性试验的日志可读性修复；用户要求连续展示一次完整思考和回答。
- 本次真实生成、训练global step、追加步数、真实评分题数均0；无父训练恢复、新checkpoint或新GPU实验。
- 下一步：真实任务启动时核对日志集成；不改变既定B/T对照条件或训练机制。

## 可复现信息

- 基础commit f20278902082e2bfc28c7a48a8d58e34482b38f3；分支data-difficulty-muxi；原工作区dirty修改保留，本次未提交/推送。
- 修改前backup/、baseline-manifest.json、baseline-dirty.diff；最终final-source/、final-manifest.json、repair-only.patch。
- 配置：trajectory_logging.search_result_max_chars=1000；0为全文。旧max_chars_per_trajectory仅限制辅助诊断；模型思考/动作/答案消费文本无展示长度上限。
- 样例数和频率不变；默认没有可读文件路径时不额外落盘。展示关闭时原训练路径不变。
- CPU内存夹具；设备CPU，CUDA_VISIBLE_DEVICES为空；env/metax/run.sh及既有vllm-metax-clean33环境；未加载7B、未调用检索服务。
- P/D/T、初始actor/reference、标签配比、学习率、KL、优化器、mask、token和终止条件均未修改或本次执行。不适用训练恢复和B分支。
- 真实历史材料：metax-process-r1-100-b32-gpu-20261008-v2；原step1候选第1行trace_uid与评分审计第257行对应，问题和标准答案从同一条旧可读记录取得。
- 原始启动命令见下节，产物绝对路径及文件SHA256见final-manifest.json，源码在final-source/中可复核。

## 运行位置及恢复

- 产物根目录：/mnt/public/code/lyk/lzy/runs/metax-trajectory-readable-20261011-v1。
- 开始时间UTC见started.json；完成CPU时间UTC见cpu-regression.final.json；文档同步UTC 2026-10-11T06:02:30.196859+00:00。
- CPU及预览任务已退出0；远程进程检查未发现main_ppo/cpu_verify任务。不存在本次模型checkpoint或可恢复训练步数。
- 无调度任务ID；短CPU进程不作为训练恢复依据。新训练启动前仍需重新核对进程和模型完整性。
- 自动审批曾在只读预览采集时超时，未执行；随后缩小为仅读首条历史报告的重试成功。无源码或测试失败。

## 阶段进度与证据

| 动作 | 实测结果 | 证据 |
| --- | --- | --- |
| 保存修改前状态 | 完成，既有dirty保留 | backup/、baseline-manifest.json |
| 连续展示、搜索独立预算与诊断后置 | 已接入共用展示器 | final-source/、repair-only.patch |
| CPU首轮及最终复验 | 各204项通过；最终结果存档 | cpu-regression.final.json/log |
| 历史三轮、两次搜索预览 | 通过，无重新生成 | historical-preview-check.json |
| 中文注释核验 | 14函数无缺失；36/36逻辑单元 | source-audit.json |
| 真实GPU日志与长期效果 | 未执行 | 后续GPU前提与B/T计划 |

## 验证及结果

实际执行（两轮CPU回归，最终生产修改后再验收）：

```text
ssh mx "cd /mnt/public/code/lyk/lzy/R1-vllm-metax && CUDA_VISIBLE_DEVICES='' bash env/metax/run.sh /mnt/public/code/lyk/lzy/runs/metax-trajectory-readable-20261011-v1/cpu_verify.py"
ssh mx "cd /mnt/public/code/lyk/lzy/R1-vllm-metax && CUDA_VISIBLE_DEVICES='' bash env/metax/run.sh /mnt/public/code/lyk/lzy/runs/metax-trajectory-readable-20261011-v1/historical_preview.py"
```

连续轨迹日志修复已完成。修改仅限 verl/utils/trajectory_logging.py、tests/test_trajectory_logging.py、verl/trainer/config/ppo_trainer.yaml；共用展示器复用真实账本和既有奖励解释，不新增生成、检索或奖励路径。思考/动作消费文本按真实轮次全文输出；对应visible_text只在搜索结果中缩略。奖励、执行状态、原因码、调用身份、未消费尾部及引用诊断统一置于连续轨迹之后。

search_result_max_chars默认1000，首尾正文按3:1保留并标注省略数量；0表示搜索全文。兼容max_chars_per_trajectory旧字段，改为末尾辅助诊断预算；不再截断模型思考/最终回答。无逐轮账本时完整生成历史展示一次，来源不明的information不缩略；模型自己生成的伪观察也全文保留。无接受答案则明确未作答，不补造答案。样例数、批次频率、异常隔离及默认关闭的直接调用保持兼容。控制台每条一次print，文件一次write同一完整块；多进程汇总日志是否另有外部插入尚未GPU验证。

最终CPU204项通过，新增6项，失败/错误/跳过0；test_fp16.py明确排除。覆盖32k多轮模型文本、20k无账本历史、18k伪观察、搜索0/短/长预算、未作答、尾部隔离、控制台/文件一致、真实RewardManager奖励/输入/Python随机状态不变及展示失败隔离。源码AST函数说明14项无缺失；人工逐项检查36/36逻辑单元中文说明，覆盖100%，函数与关键逻辑分别合格；范围含两个运行脚本和配置。CPU及历史展示验收不能代替真实GPU日志集成或训练稳定性结论。

历史预览取原100步运行首条真实候选轨迹（原step1，3轮、2次真实搜索），匹配评分审计第257行同一trace_uid，模型消费552字符，两次可见观察2028/2084字符，实际返回奖励1不变；逐轮完整顺序和记录不变检查通过。无需重新生成。预览：/mnt/public/code/lyk/lzy/runs/metax-trajectory-readable-20261011-v1/historical-preview.readable.log。

负责人/root；全部命令经ssh mx。产物 /mnt/public/code/lyk/lzy/runs/metax-trajectory-readable-20261011-v1，详细记录 runs/metax-trajectory-readable-20261011-v1.md。原有dirty筛选代码/文档保留，本次未提交/推送；真实生成0、训练更新0，无新checkpoint。下一步：新启动任务复用该展示器；保留1–2天B/T验证计划，在GPU前提和指标/reward接线完成后使用新日志核对至少一条实际轨迹。已有历史大日志未改写。


## 失败、变更与交接历史

- 初次源码/配置接入，补充6个CPU案例；全量204项通过。
- 真实预览检查后将长call_id移到诊断，保留连续轨迹的简短来源标记；最终全量204项及历史预览再次通过。
- 搜索正文预算仅作用于真实visible_text；没有来源身份时完整保留历史，避免误删模型异常输出。
- 所有历史轨迹、旧失败记录、既有未提交筛选代码和训练产物保留。未启动训练。


## 2026-10-11T06:17:23.744369+00:00 本次提交前复验

CPU204项通过；证据 /mnt/public/code/lyk/lzy/runs/metax-grpo-bt-verification-20261011-v1/cpu-regression.final.json。准备按功能提交，无GPU启动。提交哈希由后续统一提交记录发布。
