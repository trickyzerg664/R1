# grpo_loss_observations_20261011.md

Loss展示修复：原micro循环正确，新增只读total_loss、有效模型token熵总量与覆盖计数；聚合先汇总再求比值，优化目标/累积不变。3项新CPU测试，全量224通过，真实单卡FP16/FSDP小模型通过；八卡效果待首段更新。

检查UTC 2026-10-11T06:37:49.887072+00:00；负责人/root；证据 /mnt/public/code/lyk/lzy/runs/metax-grpo-bt-verification-20261011-v1/；source-audit.json含43函数/46项语义注释单元，全部覆盖。
