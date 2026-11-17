# Search-R1 SFT 实验

这是本分支的正式接手入口，更新于2026-11-18。

| 文档 | 用途 |
|---|---|
| [HANDOFF.md](HANDOFF.md) | 先读；当前状态、正在运行的任务、阻塞及下一步 |
| [PLAN.md](PLAN.md) | 固定设计、数据政策、参数和比较口径 |
| [RUNBOOK.md](RUNBOOK.md) | 命令、验收、保存和恢复步骤 |
| [runs/TEMPLATE.md](runs/TEMPLATE.md) | 真实运行及失败记录模板 |
| [历史实现记录](../sft.md) | 代码演进、CPU与双卡合成验证证据 |

从官方 `598e61bd` 独立创建 `sft`，在host3的lzy_yolo11容器 `/root/myprojects/R1/R1` 开展。学生为与历史RL相同的Qwen2.5-7B Base，教师数据为固定DeepSeek成功轨迹。先处理数据和真实7B资源验收，再做256题pilot；full独立从Base开始一轮。

目录中的示例命令均有前置条件，不能据此推断训练已开始。实验状态以HANDOFF指向的实际日志、进程和产物为准。
