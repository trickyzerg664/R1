# P/D/T 冻结工具验证：pdt-tool-validation-20260927-0200

- 负责人：Codex；2026-09-27 02:05 UTC，源机 `/root/myprojects/R1/R1`，`data-difficulty` 分支工作树含本次新增工具与测试。
- 运行范围：从 `/root/data/search-r1/datasets/nq_hotpotqa_train/{train,test}.parquet` 和本地 Qwen2.5-3B tokenizer 生成 P=20、D=10、T=10，`max_prompt_length=256`、seed=42。输出 `/root/data/search-r1/runs/pdt-tool-validation-20260927-0200`。这不是正式 P/D/T，也不用于评分或训练。
- 结果：CLI 构建返回 0，内置校验打印 `P/D/T 校验通过：P=20, D=10, T=10`；再次独立运行 `--verify` 返回 0。独立 CPU 单元测试 2 项通过，难度模块总计 20 项通过。未执行 GPU 任务、难度评分或正式切分。
- 完整性：`manifest.json` 最后发布，记录输入/输出/tokenizer 哈希、每题 ID/来源/原始定位/问题哈希及 prompt token 长度；`--verify` 已核对。未在本记录抄写完整哈希，目标机正式运行需保留其自身 manifest。
- 下一步：目标机零奖励排查；锁定最终模型和长度后用独立目录运行正式默认规模，再复验哈希与来源容量。正式 C0 评分、A/B 对照尚未开始。
