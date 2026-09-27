# P/D/T 原始数据去重审计：pdt-source-audit-20260927-0157

## 当前状态

- 负责人：Codex；2026-09-27 01:57 UTC 在源机只读检查 `/root/data/search-r1/datasets/nq_hotpotqa_train/{train,test}.parquet`。
- 阶段：原始数据审计完成；未冻结 P/D/T，也未生成任何正式训练/验证/测试文件；正式评分 0 题。
- 方法：只读取 `question`、`data_source` 两列；仅统计 NQ/HotpotQA；问题文本按 Unicode NFKC、casefold、去标点、空白合并建立去重键。不同规范化方法可能改变重叠数，冻结时需明确版本。
- 原始行数：训练 NQ 79,168、HotpotQA 90,447；官方测试 NQ 3,610、HotpotQA 7,405。
- 审计结果：训练内部重复 62 行；测试内部重复 0 行；训练与整个官方测试问题重叠 2 行。去重并排除官方测试问题后，可供 P/D 的 NQ 79,118、HotpotQA 90,433；测试可用 NQ 3,610、HotpotQA 7,405。
- 当前限制：未执行 tokenizer 长度筛选、稳定 question_id 生成或资产文件哈希；源机计数不代替目标机审计结果。尚未解决零奖励，最终模型/tokenizer 与长度上限可能变化，因此本次不冻结正式 P/D/T。
- 下一步：目标机并行运行零奖励诊断和相同去重审计；确定最终模型及长度后，生成并校验稳定 P/D/T 清单、输入与产物哈希、互斥题目集合。正式 C0/P 评分之前完成。
