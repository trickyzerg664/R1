# Host5 SFT 统一评测与轨迹审计

正式 SFT 从 Qwen2.5-7B 基座训练，使用 host5-full-20261120-v2 第 88 步导出的模型。四个模型共享同一检索后端与题集。题集从官方测试集选取 243 道 HotpotQA hard 和 88 道 Natural Questions，核对了官方训练集、历史 GRPO 训练记录及原始 SFT 题池，并执行折叠文本去重和近重复筛查。题集 SHA-256 为 a0d3c6ae8cd89968d283264b5b3a621376040d86e5baa03669f1bf2a63db883a。

| 模型 | 正确题数 | 正确率 | 平均检索次数 | 出现完全重复查询的题数 | 无可评分答案 |
| --- | --- | --- | --- | --- | --- |
| Qwen2.5-7B Base | 82/331 | 24.8% | 2.91 | 109 | 28 |
| Host5 SFT | 132/331 | 39.9% | 1.93 | 38 | 26 |
| 官方 GRPO v0.2 | 147/331 | 44.4% | 1.69 | 11 | 16 |
| 历史 Action-Stop GRPO step 80 | 152/331 | 45.9% | 3.37 | 178 | 0 |

SFT 比 Base 提高 15.1 个百分点，配对 95% 区间为 +10.0 至 +20.5 个百分点。SFT 单独答对 69 题，Base 单独答对 19 题。官方 GRPO 使用 revision deaa9d14b92dd4d481414e77b9f733c934df830a。历史 GRPO 权重在魔搭仓库 trickyzerg/R1-mx 的 runs/metax-qwen7b-actionstop-resume40-20261013-v2/train/checkpoints/step_80/actor。

SFT 的 971 条生成轮次中，964 条符合规范。另有 1 条直接输出答案而缺少思考段，6 条被截断，其中 4 条的 think 标签未闭合，2 条的 answer 标签未闭合。共有 20 题收到终答指令后仍尝试搜索，另有 38 题出现完全重复的检索查询。终答遵循、重复检索和截断问题都应在后续 GRPO 评估中持续跟踪。

历史教师筛选题集上的 SFT 正确率为 238/331（71.9%）。那批题与官方训练集有重叠，统一对比使用本页冻结的题集。

## 复现入口

- 原始运行目录为 /root/data/search-r1/sft-runs/common-comparison-20261121-v1。题集指纹和来源位于 dataset-manifest.json，汇总位于 comparison.json 和 trajectory-comparison.json。
- [归档评测脚本](../../../scripts/sft/host5_comparison)保留本次运行路径。将三个脚本放回原运行目录后，评测由 run-comparison-with-base-v3.py 启动，读取已准备好的模型、题集和检索服务。audit-comparison.py 读取已有输出做轨迹审计。
