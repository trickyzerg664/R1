# Checkpoint80 上传、暂停与 T128 三模型评测执行方案

用户已授权：80 步完整保存后暂停训练、上传权重与相关日志到现有私有魔搭仓库 trickyzerg/R1-mx，随后在同一小测试集上比较 checkpoint80、官方 GRPO v0.2、官方 PPO v0.2，并将测试结果 Markdown 和日志上传 Git。Git 作者/提交者沿用 trickyzerg <3261677617@qq.com>；不修改全局身份，不使用 Codex 署名。

1. 原训练保持运行，独立控制器每秒检查 step_80/COMPLETE.json。标记须包含 HF 推理文件、8 个 rank 状态、driver 与 metadata；所有相对路径都在检查点目录内且非空。
2. 完整标记发布后，对冻结 PID 与启动 ticks 相符的原监督器发送 SIGTERM，复用其 finally 清理本次训练进程组和唯一 RAY_TMPDIR。将预期中断记录为用户暂停，保留 checkpoint80 作为恢复点，独立检索与上传器继续运行。
3. 复用现有上传器及持久化缓存，等待 checkpoint80 与配置、指标、控制台、可读轨迹、原始审计的云端大小和 SHA256 验收。上传未验收时不执行评测。
4. 原训练退出且通过共享训练锁后，单卡 GPU0 顺序运行三个模型。三者使用相同 128 题顺序、检索库/top3、提示词、十轮、每次256生成token、2048观察token、4096上下文、动作停止、贪心单轨迹和批量8。共享生成器、评分、完整批次恢复、汇总和配对比较实现，不更新权重。
5. 完整结果要求每模型128条唯一相同顺序的记录。输出整体与NQ/Hotpot分项EM、缺答案、异常/重复诊断、真实检索调用数、生成token及实测耗时；记录配对对错转换和题目重采样区间。128题为快速比较，不代替论文全量结果。
6. 全部评测原始日志与结果上传魔搭并校验。Git 结果分支 results/ckpt80-test128-20261014-v1 保存对比md、json、逐题answers.jsonl和控制台日志。使用独立Git index提交仅本次结果路径，保留当前分支、index及已有未提交修改；推送后通过ls-remote核对提交SHA。

冻结数据：/mnt/public/code/lyk/lzy/data/runs/paper-comparison-sampled-128-20261014-v1/test128.parquet，NQ42题+Hotpot86题，SHA256 8d6414f06366a0eb451f6828987db99ad1c6a1aa14b603813bdee21934f396a2。

官方版本：GRPO deaa9d14b92dd4d481414e77b9f733c934df830a；PPO 053b6e1addc3affc5bf7e920b654b8ac9610c7ba。

控制器目录：/mnt/public/code/lyk/lzy/maintenance/checkpoint80-test128-20261014；运行目录：/mnt/public/code/lyk/lzy/runs/metax-ckpt80-test128-20261014-v1。

CPU 检查与正式 GPU 评测分开记录。准备完成、控制器启动不等于 checkpoint80、上传或评测完成。任一阶段失败保留产物与暂停状态，通知用户，不自动恢复训练。


2026-10-14T09:37:23.969180+00:00 最终注释审查补记：88/125=70.4%，完整逻辑单元清单见 /mnt/public/code/lyk/lzy/maintenance/checkpoint80-test128-20261014/comment_review.final.json。旧86/120=71.7%仅代表修复前范围；最终包含question_id派生适配。四项CPU门控、原始列与顺序一致性、128题三模型提示一致性已通过；正式GPU评测状态以控制器阶段为准。
