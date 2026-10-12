# 单次实验记录：metax-qwen7b-quality-100-20261012-v1

## 当前状态

负责人/root；准备阶段，训练0/100、已保存checkpoint0。旧scoremask-v2已停止12步、无checkpoint；本次不恢复其优化器。CPU、历史重放、模型与来源冻结待完成；尚未启动GPU。

## 可复现信息

分支data-difficulty-muxi，新规则提交07c59d5。初始actor和固定reference均为/mnt/public/model/huggingface/Qwen2.5-7B，优化器/调度器/scaler从零开始。新资格answer_correct_3_6_v1，重复repetition_v1及质量成功task_success_quality_v1。其余参数沿用旧运行：lr1e-6、warmup10后常数、KL.001、熵.001、seed42、32题×8轨迹、8GPU、mini128/micro8、clip.2、gradclip1、response256、max10轮+final、temperature1、top_p.95、max16补抽、bounded_invalid_v1、过程成本封顶.12。

mx八张MetaX C500，FP16/FSDP/vLLM；数据/固定D256/prompt/检索及环境版本沿用旧冻结配置，具体资产哈希和解析配置在本次manifest/plan中。检索PID2137145为独立服务，保持ready。

## 运行位置及恢复

产物根：/mnt/public/code/lyk/lzy/runs/metax-qwen7b-quality-100-20261012-v1。训练日志train/console.log、metrics.jsonl、process-audit.jsonl、trajectories.readable.log；状态status.json。监督器独立PID及启动ticks在launcher-process.json，训练子进程train/process.json。初始D256使用原始Qwen完整原生轨迹在新奖励配置下CPU重放，原EM独立保留；训练100步，每20步存checkpoint并固定验证，最后独立D256。当前可恢复checkpoint无；未来只能按本次新指纹恢复完整checkpoint。

启动命令（验收后执行）：bash env/metax/run.sh -u scripts/difficulty/stability_trial.py --run-directory /mnt/public/code/lyk/lzy/runs/metax-qwen7b-quality-100-20261012-v1 --launch。工作目录/mnt/public/code/lyk/lzy/R1-vllm-metax。

## 阶段进度与证据

准备：旧实验精准停止12步、检索保留；独立工作树7232ea6合入原分支为07c59d5，运行记录单独提交b450214。Git身份缺省首次提交失败，沿用历史Codex进程级身份后成功；进度文档冲突保留原分支全文并追加工作树验证历史，其余源码与已测工作树逐字相同。migration依赖提交e3544d4保留。

## 验证及结果

此前工作树CPU272项270通过、2GPU跳过，真实tokenizer256初始/3072候选已回放；证据quality-code-verification-20261012。此次合入后CPU与正式RewardManager初始256题重放待执行；不把历史CPU结果冒充本次GPU训练结果。新筛选改变候选分布，新奖励改变目标，无法单因素归因；轻度重复存在正常实体复述的软罚边界，详见quality_controls.md。

## 失败、变更与交接历史

原日志与旧manifest保留，本次不覆盖；代码/配置快照/哈希将绑定本次独立run。冻结、启动、首轮候选和实际训练步数分别记录。下一步CPU/重放通过、模型资产与新指纹验收、Git文档提交后冻结并启动。

2026-10-12T13:44:39.545677+00:00 合入后CPU272项270通过/2GPU跳过；正式RewardManager+真实tokenizer重放256唯一题/918轮，原EM84.0/256、缺提取8，训练候选新奖励改变7条，独立新公式/token/文本/人工梯度掩码/原EM参照错配均0，模型生成和更新0。证据cpu-regression.log、historical-rescore.log/json。进入模型资产与新指纹冻结验收。

资产与配置验收开始；CPU全量回归通过，训练0步，原始Qwen模型进行完整文件哈希与safetensors头部验证。

冻结验收通过：{"checked_utc": "2026-10-12T13:45:31.170237+00:00", "run": "/mnt/public/code/lyk/lzy/runs/metax-qwen7b-quality-100-20261012-v1", "model": "/mnt/public/model/huggingface/Qwen2.5-7B", "sources": 298, "assets": 16, "config_differences": 9, "identity": {"initial_model_id": "7c3269c21a61915411e593401dbe335b9c427a02702067f986bce261e592a76e", "reference_id": "7c3269c21a61915411e593401dbe335b9c427a02702067f986bce261e592a76e", "retrieval_id": "wiki18-e5-metax-gpu-fp32-shard8-20261008-v1", "seed": 42, "training": "0920d9cfc59c260a5b8fe798211f75dc53b0f04eecf518e91257fb6e3b5c9753", "versions": {"torch": "2.6.0+metax3.3.0.2", "transformers": "4.57.1", "vllm": "0.11.0+empty"}, "world_size": 8}, "cpu_verified": true, "gpu_started": false, "free_bytes": 2970972892160}。下一步按用户授权验收复用初始D256→100步训练→最终D256。初始化与旧Qwen运行相同；初始评价复用完整原生token的CPU重评分，训练从0开始。
