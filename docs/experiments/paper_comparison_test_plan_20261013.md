# 论文对比测试集方案（2026-10-13）

主对比采用论文七项划分：nq/test 3610、hotpotqa/dev 7405、triviaqa/test 11313、popqa/test 14267、2wikimultihopqa/dev 12576、musique/dev 2417、bamboogle/test 125。前两项报告同领域未训练题；后五项报告本次未用于训练的数据集泛化，不以数据集名称不同保证题目不重复。

当前quality-v1从原始Qwen2.5-7B初始化，实际训练文件P.parquet共10000题（NQ4668、Hotpot5332）。本次将论文同领域11015评测题与整个P题池比对，精确/归一化重复0；7道词集合Jaccard>=.9的近重复候选保守剔除。D256与P归一化重复0，但D256源于原始train划出且反复用于开发，应排除在正式最终测试之外。D/D256与官方11015评测题归一化重复0。原始169615题source_train与评测有3个归一化重复，不属于当前P，不能称为当前模型已训练样本。

已生成两个静态测试文件及审计：/mnt/public/code/lyk/lzy/data/runs/paper-comparison-clean-20261013-v1/，实际数量以leakage-audit.json为准。其他五项尚未下载/逐题去重，不宣称已无泄漏。后续对所有候选执行source+split+id、标准化问题、近重复人工复核，排除整个RL候选池、额外SFT样本及开发调参题；冻结保留/剔除ID、理由、哈希。不去除正常答错题，也不依据模型得分选择测试题。

清洗后的集合与论文全量不完全相同。严格公平的模型对比应将本模型、原始Base和作者7B-Base-GRPO检查点在同一清洗测试集重跑；论文原始数字仅作参照，七项平均等权，同时报告逐项EM、题数、未作答和成本。使用相同wiki18/E5/top3及同一评分程序；论文预算4动作/500生成/500观察与本项目10轮/256生成等差异应另做协议对齐评价，不能悄然混用。

固定测试集只在冻结方案与检查点后评价；D256用于开发，不根据最终测试分数反复调奖励、筛选或选择检查点。清洗只覆盖公开的本次微调数据，词集合规则不能穷尽语义改写。后续若改变模型初始化或使用新SFT数据必须重新查重。

本次仅离线数据审计与Parquet准备，没有启动GPU模型生成或训练，没有修改训练源码/配置。七项论文划分来源：https://github.com/PeterGriffinJin/Search-R1/blob/main/scripts/data_process/qa_search_test_merge.py 与 https://huggingface.co/datasets/RUC-NLPIR/FlashRAG_datasets 。
