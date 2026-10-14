# T1024五模型对比

用户最新指定顺序：ckpt80、原始Qwen2.5-7B、官方GRPO v0.2、ckpt60、官方PPO v0.2；同一GPU0逐模型执行。

数据：NQ335+HotpotQA689，原128题完整保留；固定seed20261014，复用既有SHA排序及公开train/P/D/D256排重，不按模型得分抽题，标签不改。

同一greedy单轨迹、batch8、10轮、256新生成token/次、2048观察、4096上下文、wiki18/E5/top3和action-stop；TP1、float16、显存比例0.45。不更新任何权重。

直接复用共享phase_evaluate、ObservedRollout、生成器、奖励器、完整批次续跑及paired_compare，T1024通过既有datasets.D256别名映射，不读取真实D256开发集。

原T128发布缺modelscope_hub的问题由现有modelscope-upload环境独立发布器修复；扩大测试同样隔离GPU环境与上传环境，保持GPU依赖不变。

推理、文档Git和魔搭归档由三个独立进程执行：每模型完成立即发布不可变事件并顺序启动下一个；文档进程独立读取事件、更新文档并提交Git，上传进程独立归档。Git/上传网络等待不阻塞下一模型，分别维护状态和续跑确认。原训练保持暂停。

每模型完整结果/日志上传并验收私有魔搭trickyzerg/R1-mx；文档、逐题答案及轻量日志逐模型提交Git，以trickyzerg <3261677617@qq.com>为作者和提交者，独立index保留当前分支及未提交工作。

CPU验收：
{
  "checked_utc": "2026-10-14T13:00:34.315160+00:00",
  "rows": 1024,
  "sources": {
    "nq": 335,
    "hotpotqa": 689
  },
  "retained_original128_unchanged": true,
  "original_columns_unchanged": true,
  "unique_question_ids": 1024,
  "five_tokenizers_all_prompts_equal": true,
  "training_paused": true,
  "checkpoint60_80_resume_files_present": true,
  "gpu_evaluation_started": false,
  "sampler_parent_sha256": "5baa39bbd12a60c5fa81b1eb50422ce0aa40e052db6a18b210830b1e54627377",
  "sampler_delta": "total128->1024; quotas42/86->335/689; new output directory",
  "measured_T128_seconds": {
    "checkpoint80": 109.08277325518429,
    "official_grpo_v02": 241.273703571409,
    "official_ppo_v02": 140.21288716048002
  },
  "linear_T1024_seconds": {
    "checkpoint80": 872.6621860414743,
    "official_grpo_v02": 1930.189628571272,
    "official_ppo_v02": 1121.7030972838402
  },
  "estimated_four_trained_models_minutes": [
    70,
    100
  ],
  "base_qwen_runtime_unmeasured": true,
  "estimate_is_not_actual_measurement": true
}

计划冻结：
{
  "schema_version": 1,
  "control": "/mnt/public/code/lyk/lzy/maintenance/test1024-five-models-20261014",
  "evaluation": "/mnt/public/code/lyk/lzy/runs/metax-five-model-test1024-20261014-v1",
  "repository": "/mnt/public/code/lyk/lzy/R1-vllm-metax",
  "run": "/mnt/public/code/lyk/lzy/runs/metax-qwen7b-actionstop-resume40-20261013-v2",
  "phase": "T1024",
  "expected_count": 1024,
  "model_order": [
    "checkpoint80",
    "base_qwen25_7b",
    "official_grpo_v02",
    "checkpoint60",
    "official_ppo_v02"
  ],
  "settings": "/mnt/public/code/lyk/lzy/runs/metax-five-model-test1024-20261014-v1/settings.json",
  "dataset": "/mnt/public/code/lyk/lzy/runs/metax-five-model-test1024-20261014-v1/test1024-with-ids.parquet",
  "dataset_sha256": "d9a0f0e64f1ff608f65a32c19c692aae36728a7e5e4facb1dda73913fce8d094",
  "hashes": {
    "/mnt/public/code/lyk/lzy/R1-vllm-metax/search_r1/llm_agent/generation.py": "3650a86d63070e549afba9e06c1cbdce492fcdf4efcbf67d6219ed3c478f0496",
    "/mnt/public/code/lyk/lzy/R1-vllm-metax/verl/trainer/main_ppo.py": "56cac87e385164ef4bec26346a01c01d4d31607922843c1fef14e90301abc25f",
    "/mnt/public/code/lyk/lzy/R1-vllm-metax/verl/experimental/checkpoint_eval/runtime.py": "bc074b8627fb55159316d0ecaec79dd4d9cb00c6e333ab7f8ee621275093ced7",
    "/mnt/public/code/lyk/lzy/R1-vllm-metax/verl/experimental/checkpoint_eval/core.py": "0381a86edd42afa2abf167732ef38b1455d5968bd716ce89184680868321f293",
    "/mnt/public/code/lyk/lzy/R1-vllm-metax/verl/experimental/process_checks/protocol.py": "839cbd6454daeb3a3abbb2dcb8b1d37bc7dbb748116b874f051552c6da7f43a4",
    "/mnt/public/code/lyk/lzy/R1-vllm-metax/verl/experimental/process_checks/action_stop.py": "55aea44fb5d4c894e38777b7c5ff8200fc135f08cdbd5496e40dfdd84f70f46e",
    "/mnt/public/code/lyk/lzy/R1-vllm-metax/verl/workers/rollout/vllm_rollout/vllm_rollout.py": "259b73d313caa2d9090c7deb7cfccf11cde9272b39f6c7bc98b7a2a28e1b8c55",
    "/mnt/public/code/lyk/lzy/R1-vllm-metax/verl/third_party/vllm/metax_v_0_11_0/llm.py": "7a0b14f49deeef502cba8cad95d0c1506861f4e392462411b3d2a3be41680098",
    "/mnt/public/code/lyk/lzy/runs/metax-five-model-test1024-20261014-v1/test1024-with-ids.parquet": "d9a0f0e64f1ff608f65a32c19c692aae36728a7e5e4facb1dda73913fce8d094",
    "/mnt/public/code/lyk/lzy/data/runs/paper-comparison-sampled-1024-20261014-v1/test1024.parquet": "9714767acdc73f98cdc1525519f472e4c245590507de1b57be3104e8a39d26e8",
    "/mnt/public/code/lyk/lzy/runs/metax-five-model-test1024-20261014-v1/formal-config.yaml": "42f59cf0ba6e1bf57e3c664a28d9cd61ecabab3a4bd38459ac7dff23a7b81425",
    "/mnt/public/code/lyk/lzy/runs/metax-five-model-test1024-20261014-v1/settings.json": "1f7af89de7e392fd408c52ec2b6d404f39603eac24e98f4c9c9e0515c9f7b878",
    "/mnt/public/code/lyk/lzy/maintenance/test1024-five-models-20261014/test1024_eval.py": "314e0330481e83943dab226ec6525fdc2a2923a13f524024306115a0a969ccca",
    "/mnt/public/code/lyk/lzy/maintenance/test1024-five-models-20261014/workflow1024.py": "11d81462674ec61fe79d1fc7bf1db07d7e1066099c239d98a677a8b49f67705e",
    "/mnt/public/code/lyk/lzy/maintenance/test1024-five-models-20261014/async_publish1024.py": "d18d3f6ce83aa0bc49208b3ed9fecb1963601d14f72130d02fcf51f19c2dcaa8",
    "/mnt/public/code/lyk/lzy/maintenance/test1024-five-models-20261014/sample_test1024.py": "e81b534f5bfdf8c792edf8f31c86acf8b438ec5cfedbe5b1d3c46211c65c4998",
    "/mnt/public/code/lyk/lzy/runs/metax-qwen7b-actionstop-resume40-20261013-v2/train/checkpoints/step_80/COMPLETE.json": "a5cf56df361569c8b5d3f4f09c3b75e97016b4f127a0f2e17b47f7839db684d7",
    "/mnt/public/model/huggingface/Qwen2.5-7B/config.json": "267ce68584c5f24c3b267d934db2de68dd21d1ca677fb78ed809eb60067f7642",
    "/mnt/public/model/huggingface/Qwen2.5-7B/model.safetensors.index.json": "624bf7c47cd12468fdc16e38a47cf4f19e0415b859a223ba3c027eed2f0e1028",
    "/mnt/public/model/huggingface/Qwen2.5-7B/tokenizer_config.json": "c91efca15ceff6e9ee9424db58a6f59cd41294e550a86cbd07e3c1fb500b34f9",
    "/mnt/public/model/huggingface/Qwen2.5-7B/tokenizer.json": "c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539",
    "/mnt/public/code/lyk/lzy/models/official-search-r1-v02/SearchR1-nq_hotpotqa_train-qwen2.5-7b-em-grpo-v0.2/COMPLETE.json": "50cfdd8901be27c1763300c4a297367813dd9609fd840c69cce8a773e877b1cc",
    "/mnt/public/code/lyk/lzy/runs/metax-qwen7b-actionstop-resume40-20261013-v2/train/checkpoints/step_60/COMPLETE.json": "9e6512deb49e3129805b6580e689641e3f90fe094b021e59e2b6039827856a32",
    "/mnt/public/code/lyk/lzy/models/official-search-r1-v02/SearchR1-nq_hotpotqa_train-qwen2.5-7b-em-ppo-v0.2/COMPLETE.json": "48528cf8b4bc8864d43c953ba0a05dd2cc4848ed4ee44e54c39ca95db22bbf3b"
  },
  "gpu": "0",
  "retriever_pid": 2137145,
  "prior_publication_control": "/mnt/public/code/lyk/lzy/maintenance/checkpoint80-test128-20261014",
  "modelscope_repo": "trickyzerg/R1-mx",
  "git_base": "ec179e34ae50e3e4474e4c88cc89aeaf5e0323de",
  "git_branch": "data-difficulty-muxi",
  "git_remote": "origin",
  "git_author_name": "trickyzerg",
  "git_author_email": "3261677617@qq.com",
  "git_extra_paths": [
    "docs/experiments/runs/metax-five-model-test1024-20261014-v1.md",
    "docs/experiments/test1024_five_model_execution_20261014.md"
  ]
}


2026-10-14T13:15:15.856517+00:00 T1024正式GPU已启动，核验：{"evaluation": {"phase": "evaluating", "pid": 1555832, "checked_utc": "2026-10-14T13:00:38.699514+00:00", "status": "running", "current_model": "checkpoint80", "evaluation_pid": 1555837, "model_index": 0, "completed_models": [], "model_order": ["checkpoint80", "base_qwen25_7b", "official_grpo_v02", "checkpoint60", "official_ppo_v02"]}, "current_model_progress": {"status": "running", "model": "checkpoint80", "phase": "T1024", "completed": 952, "total": 1024, "checked_utc": "2026-10-14T13:15:13.767987+00:00"}}。Git和魔搭由独立工作器消费完成事件，尚未完成模型不提前提交。原T128记录已推送data-difficulty-muxi，SHA c17815ec1953b13c99a6148960be329a08933908。


2026-10-14T13:16:33.974724+00:00 模型完整结束：checkpoint80

# T1024五模型对比

固定NQ335+HotpotQA689，原128题完整保留；greedy单轨迹、10轮、256生成/2048观察/4096上下文，同一检索和action-stop。

| 模型 | 正确题数 | EM | NQ EM | HotpotQA EM | 未作答 | 检索次数 | 实测推理分钟 |
|---|---:|---:|---:|---:|---:|---:|---:|
| checkpoint80 | 488/1024 | 47.66% | 53.43% | 44.85% | 0 | 3591 | 14.53 |

未完成模型：base_qwen25_7b、official_grpo_v02、checkpoint60、official_ppo_v02

原始EM按冻结标签计算；T128语义复核为独立已提交报告，不覆盖本次1024题金标准。

更新UTC：2026-10-14T13:16:33.955690+00:00



2026-10-14T13:27:44.315506+00:00 T1024 heartbeat verification: {"checked_utc": "2026-10-14T13:27:44.315506+00:00", "checkpoint80": {"questions": 1024, "correct": 488.0, "em": 0.4765625, "inference_seconds": 872.0227878522128, "git_commit": "324bdbab60ed6a84edd2ccf93ec8265c44be5e46", "git_branch": "data-difficulty-muxi", "identity": "trickyzerg <3261677617@qq.com>|trickyzerg <3261677617@qq.com>", "git_remote_verified": true, "cloud_verified": true, "cloud_files": 262, "metadata_files": 8}, "current_model_progress": {"status": "running", "model": "base_qwen25_7b", "phase": "T1024", "completed": 392, "total": 1024, "checked_utc": "2026-10-14T13:27:33.025929+00:00"}, "processes_verified": [1555832, 1571379, 1555856, 1555857], "training_resumed": false}


2026-10-14T13:28:51.971945+00:00 T1024 heartbeat verification: {"checked_utc": "2026-10-14T13:28:51.971945+00:00", "evaluation": {"phase": "evaluating", "pid": 1555832, "checked_utc": "2026-10-14T13:16:33.267537+00:00", "status": "running", "current_model": "base_qwen25_7b", "evaluation_pid": 1571379, "model_index": 1, "completed_models": ["checkpoint80"], "model_order": ["checkpoint80", "base_qwen25_7b", "official_grpo_v02", "checkpoint60", "official_ppo_v02"]}, "progress": {"status": "running", "model": "base_qwen25_7b", "phase": "T1024", "completed": 440, "total": 1024, "checked_utc": "2026-10-14T13:28:45.768351+00:00"}, "workers": {"git": {"status": "waiting", "pid": 1555856, "current_model": "base_qwen25_7b", "completed_models": ["checkpoint80"]}, "cloud": {"status": "waiting", "pid": 1555857, "current_model": "base_qwen25_7b", "completed_models": ["checkpoint80"]}}, "processes": {"evaluation": {"pid": 1555832, "alive": true, "identity_matches": true}, "git": {"pid": 1555856, "alive": true, "identity_matches": true}, "cloud": {"pid": 1555857, "alive": true, "identity_matches": true}, "model": {"pid": 1571379, "alive": true, "command": "/mnt/public/code/lyk/lzy/envs/vllm-metax-clean33/bin/python -u /mnt/public/code/lyk/lzy/maintenance/test1024-five-models-20261014/test1024_eval.py --settings /mnt/public/code/lyk/lzy/runs/metax-five-model-test1024-20261014-v1/settings.json --model base_qwen25_7b "}}, "receipts": {"git": {"checkpoint80": {"model": "checkpoint80", "commit": "324bdbab60ed6a84edd2ccf93ec8265c44be5e46", "branch": "data-difficulty-muxi", "author": "trickyzerg <3261677617@qq.com>|trickyzerg <3261677617@qq.com>", "remote_verified": true, "checked_utc": "2026-10-14T13:16:54.749250+00:00"}}, "cloud": {"checkpoint80": {"model": "checkpoint80", "prefix": "runs/metax-five-model-test1024-20261014-v1/checkpoint80", "verified": true, "errors": [], "checked_utc": "2026-10-14T13:17:47.082022+00:00"}}}}


2026-10-14T13:31:06.340435+00:00 T1024 heartbeat verification: {"checked_utc": "2026-10-14T13:31:06.340435+00:00", "evaluation": {"phase": "evaluating", "pid": 1555832, "checked_utc": "2026-10-14T13:16:33.267537+00:00", "status": "running", "current_model": "base_qwen25_7b", "evaluation_pid": 1571379, "model_index": 1, "completed_models": ["checkpoint80"], "model_order": ["checkpoint80", "base_qwen25_7b", "official_grpo_v02", "checkpoint60", "official_ppo_v02"]}, "progress": {"status": "running", "model": "base_qwen25_7b", "phase": "T1024", "completed": 560, "total": 1024, "checked_utc": "2026-10-14T13:31:05.158632+00:00"}, "workers": {"git": {"status": "waiting", "pid": 1555856, "current_model": "base_qwen25_7b", "completed_models": ["checkpoint80"]}, "cloud": {"status": "waiting", "pid": 1555857, "current_model": "base_qwen25_7b", "completed_models": ["checkpoint80"]}}, "process_identity": {"evaluation": true, "git": true, "cloud": true, "child_command": "/mnt/public/code/lyk/lzy/envs/vllm-metax-clean33/bin/python -u /mnt/public/code/lyk/lzy/maintenance/test1024-five-models-20261014/test1024_eval.py --settings /mnt/public/code/lyk/lzy/runs/metax-five-model-test1024-20261014-v1/settings.json --model base_qwen25_7b "}, "persisted_batches": 70, "persisted_records": 560, "batch_counts": [8], "receipts": {"git": {"checkpoint80": {"model": "checkpoint80", "commit": "324bdbab60ed6a84edd2ccf93ec8265c44be5e46", "branch": "data-difficulty-muxi", "author": "trickyzerg <3261677617@qq.com>|trickyzerg <3261677617@qq.com>", "remote_verified": true, "checked_utc": "2026-10-14T13:16:54.749250+00:00"}}, "cloud": {"checkpoint80": {"model": "checkpoint80", "prefix": "runs/metax-five-model-test1024-20261014-v1/checkpoint80", "verified": true, "errors": [], "checked_utc": "2026-10-14T13:17:47.082022+00:00"}}}}


2026-10-14T13:31:42.585412+00:00 用户请求核验T1024测试进度：checkpoint80已完成1024题，EM=488/1024=47.65625%，NQ179/335，HotpotQA309/689；纯推理872.02秒。当前base_qwen25_7b完成592/1024，状态running；后续顺序official_grpo_v02、checkpoint60、official_ppo_v02。评测控制器、当前推理、Git、魔搭发布器及检索进程存活，日志持续推进。checkpoint80 Git回执remote_verified=true，提交324bdbab60ed6a84edd2ccf93ec8265c44be5e46至data-difficulty-muxi；魔搭回执verified=True，errors=[]。本次仅读取状态及同步记录，没有启动GPU验证或修改实验配置。


2026-10-14T13:35:53.590889+00:00 T1024 heartbeat verification: {"checked_utc": "2026-10-14T13:35:53.590889+00:00", "evaluation": {"phase": "evaluating", "pid": 1555832, "checked_utc": "2026-10-14T13:16:33.267537+00:00", "status": "running", "current_model": "base_qwen25_7b", "evaluation_pid": 1571379, "model_index": 1, "completed_models": ["checkpoint80"], "model_order": ["checkpoint80", "base_qwen25_7b", "official_grpo_v02", "checkpoint60", "official_ppo_v02"]}, "progress": {"status": "running", "model": "base_qwen25_7b", "phase": "T1024", "completed": 752, "total": 1024, "checked_utc": "2026-10-14T13:35:52.590621+00:00"}, "workers": {"git": {"status": "waiting", "pid": 1555856, "current_model": "base_qwen25_7b", "completed_models": ["checkpoint80"]}, "cloud": {"status": "waiting", "pid": 1555857, "current_model": "base_qwen25_7b", "completed_models": ["checkpoint80"]}}, "process_identity": {"evaluation": true, "git": true, "cloud": true, "child_command": "/mnt/public/code/lyk/lzy/envs/vllm-metax-clean33/bin/python -u /mnt/public/code/lyk/lzy/maintenance/test1024-five-models-20261014/test1024_eval.py --settings /mnt/public/code/lyk/lzy/runs/metax-five-model-test1024-20261014-v1/settings.json --model base_qwen25_7b "}, "persisted_batches": 94, "persisted_records": 752, "batch_counts": [8], "receipts": {"git": {"checkpoint80": {"model": "checkpoint80", "commit": "324bdbab60ed6a84edd2ccf93ec8265c44be5e46", "branch": "data-difficulty-muxi", "author": "trickyzerg <3261677617@qq.com>|trickyzerg <3261677617@qq.com>", "remote_verified": true, "checked_utc": "2026-10-14T13:16:54.749250+00:00"}}, "cloud": {"checkpoint80": {"model": "checkpoint80", "prefix": "runs/metax-five-model-test1024-20261014-v1/checkpoint80", "verified": true, "errors": [], "checked_utc": "2026-10-14T13:17:47.082022+00:00"}}}}


2026-10-14T13:40:42.782327+00:00 T1024 heartbeat verification: {"checked_utc": "2026-10-14T13:40:42.782327+00:00", "evaluation": {"phase": "evaluating", "pid": 1555832, "checked_utc": "2026-10-14T13:16:33.267537+00:00", "status": "running", "current_model": "base_qwen25_7b", "evaluation_pid": 1571379, "model_index": 1, "completed_models": ["checkpoint80"], "model_order": ["checkpoint80", "base_qwen25_7b", "official_grpo_v02", "checkpoint60", "official_ppo_v02"]}, "progress": {"status": "running", "model": "base_qwen25_7b", "phase": "T1024", "completed": 928, "total": 1024, "checked_utc": "2026-10-14T13:40:40.282286+00:00"}, "workers": {"git": {"status": "waiting", "pid": 1555856, "current_model": "base_qwen25_7b", "completed_models": ["checkpoint80"]}, "cloud": {"status": "waiting", "pid": 1555857, "current_model": "base_qwen25_7b", "completed_models": ["checkpoint80"]}}, "process_identity": {"evaluation": true, "git": true, "cloud": true, "child_command": "/mnt/public/code/lyk/lzy/envs/vllm-metax-clean33/bin/python -u /mnt/public/code/lyk/lzy/maintenance/test1024-five-models-20261014/test1024_eval.py --settings /mnt/public/code/lyk/lzy/runs/metax-five-model-test1024-20261014-v1/settings.json --model base_qwen25_7b "}, "persisted_batches": 116, "persisted_records": 928, "batch_counts": [8], "receipts": {"git": {"checkpoint80": {"model": "checkpoint80", "commit": "324bdbab60ed6a84edd2ccf93ec8265c44be5e46", "branch": "data-difficulty-muxi", "author": "trickyzerg <3261677617@qq.com>|trickyzerg <3261677617@qq.com>", "remote_verified": true, "checked_utc": "2026-10-14T13:16:54.749250+00:00"}}, "cloud": {"checkpoint80": {"model": "checkpoint80", "prefix": "runs/metax-five-model-test1024-20261014-v1/checkpoint80", "verified": true, "errors": [], "checked_utc": "2026-10-14T13:17:47.082022+00:00"}}}}


2026-10-14T13:43:36.848555+00:00 模型完整结束：base_qwen25_7b

# T1024五模型对比

固定NQ335+HotpotQA689，原128题完整保留；greedy单轨迹、10轮、256生成/2048观察/4096上下文，同一检索和action-stop。

| 模型 | 正确题数 | EM | NQ EM | HotpotQA EM | 未作答 | 检索次数 | 实测推理分钟 |
|---|---:|---:|---:|---:|---:|---:|---:|
| checkpoint80 | 488/1024 | 47.66% | 53.43% | 44.85% | 0 | 3591 | 14.53 |
| base_qwen25_7b | 229/1024 | 22.36% | 25.67% | 20.75% | 44 | 2678 | 25.89 |

未完成模型：official_grpo_v02、checkpoint60、official_ppo_v02

原始EM按冻结标签计算；T128语义复核为独立已提交报告，不覆盖本次1024题金标准。

更新UTC：2026-10-14T13:43:36.803460+00:00



2026-10-14T13:45:53.708571+00:00 T1024 heartbeat verification: {"checked_utc": "2026-10-14T13:45:53.708571+00:00", "evaluation": {"phase": "evaluating", "pid": 1555832, "checked_utc": "2026-10-14T13:43:35.772518+00:00", "status": "running", "current_model": "official_grpo_v02", "evaluation_pid": 1614985, "model_index": 2, "completed_models": ["checkpoint80", "base_qwen25_7b"], "model_order": ["checkpoint80", "base_qwen25_7b", "official_grpo_v02", "checkpoint60", "official_ppo_v02"]}, "progress": {"status": "running", "model": "official_grpo_v02", "phase": "T1024", "completed": 40, "total": 1024, "checked_utc": "2026-10-14T13:45:36.563092+00:00"}, "workers": {"git": {"status": "waiting", "pid": 1555856, "current_model": "official_grpo_v02", "completed_models": ["checkpoint80", "base_qwen25_7b"]}, "cloud": {"status": "waiting", "pid": 1555857, "current_model": "official_grpo_v02", "completed_models": ["checkpoint80", "base_qwen25_7b"]}}, "process_identity": {"evaluation": true, "git": true, "cloud": true, "child_command": "/mnt/public/code/lyk/lzy/envs/vllm-metax-clean33/bin/python -u /mnt/public/code/lyk/lzy/maintenance/test1024-five-models-20261014/test1024_eval.py --settings /mnt/public/code/lyk/lzy/runs/metax-five-model-test1024-20261014-v1/settings.json --model official_grpo_v02 "}, "persisted_batches": 5, "persisted_records": 40, "batch_counts": [8], "receipts": {"git": {"base_qwen25_7b": {"model": "base_qwen25_7b", "commit": "0fd055291f7dd7d54c5f21590d9696e64e14ebef", "branch": "data-difficulty-muxi", "author": "trickyzerg <3261677617@qq.com>|trickyzerg <3261677617@qq.com>", "remote_verified": true, "checked_utc": "2026-10-14T13:43:59.150020+00:00"}, "checkpoint80": {"model": "checkpoint80", "commit": "324bdbab60ed6a84edd2ccf93ec8265c44be5e46", "branch": "data-difficulty-muxi", "author": "trickyzerg <3261677617@qq.com>|trickyzerg <3261677617@qq.com>", "remote_verified": true, "checked_utc": "2026-10-14T13:16:54.749250+00:00"}}, "cloud": {"base_qwen25_7b": {"model": "base_qwen25_7b", "prefix": "runs/metax-five-model-test1024-20261014-v1/base_qwen25_7b", "verified": true, "errors": [], "checked_utc": "2026-10-14T13:44:21.754312+00:00"}, "checkpoint80": {"model": "checkpoint80", "prefix": "runs/metax-five-model-test1024-20261014-v1/checkpoint80", "verified": true, "errors": [], "checked_utc": "2026-10-14T13:17:47.082022+00:00"}}}}


2026-10-14T13:46:33.712828+00:00 T1024 model publication verified: {"checked_utc": "2026-10-14T13:46:33.712828+00:00", "model": "base_qwen25_7b", "summary": {"n": 1024, "correct": 229.0, "em": 0.2236328125, "missing_answer": 44, "format_anomaly": 28, "model_information": 2, "rewarded_model_information": 0, "actual_search_queries": 2678, "generated_tokens": 174380, "forced_final": 222, "generation_limit_hits": 47, "sources": {"hotpotqa": {"n": 689, "correct": 143.0, "em": 0.20754716981132076}, "nq": {"n": 335, "correct": 86.0, "em": 0.25671641791044775}}}, "cost": {"total_seconds": 1553.3034512735903, "generation_seconds": 1490.182536708191, "search_seconds": 26.32419397123158}, "unique_paired_records": 1024, "commit": "0fd055291f7dd7d54c5f21590d9696e64e14ebef", "remote_verified": true, "identity": "trickyzerg <3261677617@qq.com>|trickyzerg <3261677617@qq.com>", "cloud_verified": true, "cloud_files": 262}


2026-10-14T13:50:51.424160+00:00 T1024 heartbeat verification: {"checked_utc": "2026-10-14T13:50:51.424160+00:00", "evaluation": {"phase": "evaluating", "pid": 1555832, "checked_utc": "2026-10-14T13:43:35.772518+00:00", "status": "running", "current_model": "official_grpo_v02", "evaluation_pid": 1614985, "model_index": 2, "completed_models": ["checkpoint80", "base_qwen25_7b"], "model_order": ["checkpoint80", "base_qwen25_7b", "official_grpo_v02", "checkpoint60", "official_ppo_v02"]}, "progress": {"status": "running", "model": "official_grpo_v02", "phase": "T1024", "completed": 240, "total": 1024, "checked_utc": "2026-10-14T13:50:49.897996+00:00"}, "workers": {"git": {"status": "waiting", "pid": 1555856, "current_model": "official_grpo_v02", "completed_models": ["checkpoint80", "base_qwen25_7b"]}, "cloud": {"status": "waiting", "pid": 1555857, "current_model": "official_grpo_v02", "completed_models": ["checkpoint80", "base_qwen25_7b"]}}, "process_identity": {"evaluation": true, "git": true, "cloud": true, "child_command": "/mnt/public/code/lyk/lzy/envs/vllm-metax-clean33/bin/python -u /mnt/public/code/lyk/lzy/maintenance/test1024-five-models-20261014/test1024_eval.py --settings /mnt/public/code/lyk/lzy/runs/metax-five-model-test1024-20261014-v1/settings.json --model official_grpo_v02 "}, "persisted_batches": 30, "persisted_records": 240, "batch_counts": [8], "receipts": {"git": {"base_qwen25_7b": {"model": "base_qwen25_7b", "commit": "0fd055291f7dd7d54c5f21590d9696e64e14ebef", "branch": "data-difficulty-muxi", "author": "trickyzerg <3261677617@qq.com>|trickyzerg <3261677617@qq.com>", "remote_verified": true, "checked_utc": "2026-10-14T13:43:59.150020+00:00"}, "checkpoint80": {"model": "checkpoint80", "commit": "324bdbab60ed6a84edd2ccf93ec8265c44be5e46", "branch": "data-difficulty-muxi", "author": "trickyzerg <3261677617@qq.com>|trickyzerg <3261677617@qq.com>", "remote_verified": true, "checked_utc": "2026-10-14T13:16:54.749250+00:00"}}, "cloud": {"base_qwen25_7b": {"model": "base_qwen25_7b", "prefix": "runs/metax-five-model-test1024-20261014-v1/base_qwen25_7b", "verified": true, "errors": [], "checked_utc": "2026-10-14T13:44:21.754312+00:00"}, "checkpoint80": {"model": "checkpoint80", "prefix": "runs/metax-five-model-test1024-20261014-v1/checkpoint80", "verified": true, "errors": [], "checked_utc": "2026-10-14T13:17:47.082022+00:00"}}}}


2026-10-14T13:55:43.711168+00:00 T1024 heartbeat verification: {"checked_utc": "2026-10-14T13:55:43.711168+00:00", "evaluation": {"phase": "evaluating", "pid": 1555832, "checked_utc": "2026-10-14T13:43:35.772518+00:00", "status": "running", "current_model": "official_grpo_v02", "evaluation_pid": 1614985, "model_index": 2, "completed_models": ["checkpoint80", "base_qwen25_7b"], "model_order": ["checkpoint80", "base_qwen25_7b", "official_grpo_v02", "checkpoint60", "official_ppo_v02"]}, "progress": {"status": "running", "model": "official_grpo_v02", "phase": "T1024", "completed": 416, "total": 1024, "checked_utc": "2026-10-14T13:55:25.096545+00:00"}, "workers": {"git": {"status": "waiting", "pid": 1555856, "current_model": "official_grpo_v02", "completed_models": ["checkpoint80", "base_qwen25_7b"]}, "cloud": {"status": "waiting", "pid": 1555857, "current_model": "official_grpo_v02", "completed_models": ["checkpoint80", "base_qwen25_7b"]}}, "process_identity": {"evaluation": true, "git": true, "cloud": true, "child_command": "/mnt/public/code/lyk/lzy/envs/vllm-metax-clean33/bin/python -u /mnt/public/code/lyk/lzy/maintenance/test1024-five-models-20261014/test1024_eval.py --settings /mnt/public/code/lyk/lzy/runs/metax-five-model-test1024-20261014-v1/settings.json --model official_grpo_v02 "}, "persisted_batches": 52, "persisted_records": 416, "batch_counts": [8], "receipts": {"git": {"base_qwen25_7b": {"model": "base_qwen25_7b", "commit": "0fd055291f7dd7d54c5f21590d9696e64e14ebef", "branch": "data-difficulty-muxi", "author": "trickyzerg <3261677617@qq.com>|trickyzerg <3261677617@qq.com>", "remote_verified": true, "checked_utc": "2026-10-14T13:43:59.150020+00:00"}, "checkpoint80": {"model": "checkpoint80", "commit": "324bdbab60ed6a84edd2ccf93ec8265c44be5e46", "branch": "data-difficulty-muxi", "author": "trickyzerg <3261677617@qq.com>|trickyzerg <3261677617@qq.com>", "remote_verified": true, "checked_utc": "2026-10-14T13:16:54.749250+00:00"}}, "cloud": {"base_qwen25_7b": {"model": "base_qwen25_7b", "prefix": "runs/metax-five-model-test1024-20261014-v1/base_qwen25_7b", "verified": true, "errors": [], "checked_utc": "2026-10-14T13:44:21.754312+00:00"}, "checkpoint80": {"model": "checkpoint80", "prefix": "runs/metax-five-model-test1024-20261014-v1/checkpoint80", "verified": true, "errors": [], "checked_utc": "2026-10-14T13:17:47.082022+00:00"}}}}


2026-10-14T14:00:47.316174+00:00 T1024 heartbeat verification: {"checked_utc": "2026-10-14T14:00:47.316174+00:00", "evaluation": {"phase": "evaluating", "pid": 1555832, "checked_utc": "2026-10-14T13:43:35.772518+00:00", "status": "running", "current_model": "official_grpo_v02", "evaluation_pid": 1614985, "model_index": 2, "completed_models": ["checkpoint80", "base_qwen25_7b"], "model_order": ["checkpoint80", "base_qwen25_7b", "official_grpo_v02", "checkpoint60", "official_ppo_v02"]}, "progress": {"status": "running", "model": "official_grpo_v02", "phase": "T1024", "completed": 664, "total": 1024, "checked_utc": "2026-10-14T14:00:40.582371+00:00"}, "workers": {"git": {"status": "waiting", "pid": 1555856, "current_model": "official_grpo_v02", "completed_models": ["checkpoint80", "base_qwen25_7b"]}, "cloud": {"status": "waiting", "pid": 1555857, "current_model": "official_grpo_v02", "completed_models": ["checkpoint80", "base_qwen25_7b"]}}, "process_identity": {"evaluation": true, "git": true, "cloud": true, "child_command": "/mnt/public/code/lyk/lzy/envs/vllm-metax-clean33/bin/python -u /mnt/public/code/lyk/lzy/maintenance/test1024-five-models-20261014/test1024_eval.py --settings /mnt/public/code/lyk/lzy/runs/metax-five-model-test1024-20261014-v1/settings.json --model official_grpo_v02 "}, "persisted_batches": 83, "persisted_records": 664, "batch_counts": [8], "receipts": {"git": {"base_qwen25_7b": {"model": "base_qwen25_7b", "commit": "0fd055291f7dd7d54c5f21590d9696e64e14ebef", "branch": "data-difficulty-muxi", "author": "trickyzerg <3261677617@qq.com>|trickyzerg <3261677617@qq.com>", "remote_verified": true, "checked_utc": "2026-10-14T13:43:59.150020+00:00"}, "checkpoint80": {"model": "checkpoint80", "commit": "324bdbab60ed6a84edd2ccf93ec8265c44be5e46", "branch": "data-difficulty-muxi", "author": "trickyzerg <3261677617@qq.com>|trickyzerg <3261677617@qq.com>", "remote_verified": true, "checked_utc": "2026-10-14T13:16:54.749250+00:00"}}, "cloud": {"base_qwen25_7b": {"model": "base_qwen25_7b", "prefix": "runs/metax-five-model-test1024-20261014-v1/base_qwen25_7b", "verified": true, "errors": [], "checked_utc": "2026-10-14T13:44:21.754312+00:00"}, "checkpoint80": {"model": "checkpoint80", "prefix": "runs/metax-five-model-test1024-20261014-v1/checkpoint80", "verified": true, "errors": [], "checked_utc": "2026-10-14T13:17:47.082022+00:00"}}}}


2026-10-14T14:01:04.835947+00:00 按用户要求复查T1024 EM错题且不创建定时任务：ckpt80逐条阅读536个错题，新增明确等价134题，622/1024=60.7421875%，原EM488/1024；原始Qwen逐条阅读675个新待审错误、复用120个同题同答案裁定，新增236题，465/1024=45.41015625%，原EM229/1024。两者争议/标签疑误分别62/15与60/14，不加分。语义复核独立产物位于运行目录semantic-review；原result.json和标签不改。CPU安全回归8项通过，覆盖response-only EM、原结果不可变、未审保持pending、跨模型复用、冲突拒绝、旧摘要拒绝、错误汇总拒绝和缺题拒绝。GRPO已阅读首536题中151个新的EM错题，裁定暂存grpo_semantic_spec.json，等待完整结果后验收。


2026-10-14T14:05:45.051327+00:00 T1024 heartbeat verification: {"checked_utc": "2026-10-14T14:05:45.051327+00:00", "evaluation": {"phase": "evaluating", "pid": 1555832, "checked_utc": "2026-10-14T13:43:35.772518+00:00", "status": "running", "current_model": "official_grpo_v02", "evaluation_pid": 1614985, "model_index": 2, "completed_models": ["checkpoint80", "base_qwen25_7b"], "model_order": ["checkpoint80", "base_qwen25_7b", "official_grpo_v02", "checkpoint60", "official_ppo_v02"]}, "progress": {"status": "running", "model": "official_grpo_v02", "phase": "T1024", "completed": 856, "total": 1024, "checked_utc": "2026-10-14T14:05:40.274164+00:00"}, "workers": {"git": {"status": "waiting", "pid": 1555856, "current_model": "official_grpo_v02", "completed_models": ["checkpoint80", "base_qwen25_7b"]}, "cloud": {"status": "waiting", "pid": 1555857, "current_model": "official_grpo_v02", "completed_models": ["checkpoint80", "base_qwen25_7b"]}}, "process_identity": {"evaluation": true, "git": true, "cloud": true, "child_command": "/mnt/public/code/lyk/lzy/envs/vllm-metax-clean33/bin/python -u /mnt/public/code/lyk/lzy/maintenance/test1024-five-models-20261014/test1024_eval.py --settings /mnt/public/code/lyk/lzy/runs/metax-five-model-test1024-20261014-v1/settings.json --model official_grpo_v02 "}, "persisted_batches": 107, "persisted_records": 856, "batch_counts": [8], "receipts": {"git": {"base_qwen25_7b": {"model": "base_qwen25_7b", "commit": "0fd055291f7dd7d54c5f21590d9696e64e14ebef", "branch": "data-difficulty-muxi", "author": "trickyzerg <3261677617@qq.com>|trickyzerg <3261677617@qq.com>", "remote_verified": true, "checked_utc": "2026-10-14T13:43:59.150020+00:00"}, "checkpoint80": {"model": "checkpoint80", "commit": "324bdbab60ed6a84edd2ccf93ec8265c44be5e46", "branch": "data-difficulty-muxi", "author": "trickyzerg <3261677617@qq.com>|trickyzerg <3261677617@qq.com>", "remote_verified": true, "checked_utc": "2026-10-14T13:16:54.749250+00:00"}}, "cloud": {"base_qwen25_7b": {"model": "base_qwen25_7b", "prefix": "runs/metax-five-model-test1024-20261014-v1/base_qwen25_7b", "verified": true, "errors": [], "checked_utc": "2026-10-14T13:44:21.754312+00:00"}, "checkpoint80": {"model": "checkpoint80", "prefix": "runs/metax-five-model-test1024-20261014-v1/checkpoint80", "verified": true, "errors": [], "checked_utc": "2026-10-14T13:17:47.082022+00:00"}}}}


2026-10-14T14:10:51.880967+00:00 T1024 heartbeat verification: {"checked_utc": "2026-10-14T14:10:51.880967+00:00", "evaluation": {"phase": "evaluating", "pid": 1555832, "checked_utc": "2026-10-14T13:43:35.772518+00:00", "status": "running", "current_model": "official_grpo_v02", "evaluation_pid": 1614985, "model_index": 2, "completed_models": ["checkpoint80", "base_qwen25_7b"], "model_order": ["checkpoint80", "base_qwen25_7b", "official_grpo_v02", "checkpoint60", "official_ppo_v02"]}, "progress": {"status": "running", "model": "official_grpo_v02", "phase": "T1024", "completed": 1008, "total": 1024, "checked_utc": "2026-10-14T14:10:08.347920+00:00"}, "workers": {"git": {"status": "waiting", "pid": 1555856, "current_model": "official_grpo_v02", "completed_models": ["checkpoint80", "base_qwen25_7b"]}, "cloud": {"status": "waiting", "pid": 1555857, "current_model": "official_grpo_v02", "completed_models": ["checkpoint80", "base_qwen25_7b"]}}, "process_identity": {"evaluation": true, "git": true, "cloud": true, "child_command": "/mnt/public/code/lyk/lzy/envs/vllm-metax-clean33/bin/python -u /mnt/public/code/lyk/lzy/maintenance/test1024-five-models-20261014/test1024_eval.py --settings /mnt/public/code/lyk/lzy/runs/metax-five-model-test1024-20261014-v1/settings.json --model official_grpo_v02 "}, "persisted_batches": 126, "persisted_records": 1008, "batch_counts": [8], "receipts": {"git": {"base_qwen25_7b": {"model": "base_qwen25_7b", "commit": "0fd055291f7dd7d54c5f21590d9696e64e14ebef", "branch": "data-difficulty-muxi", "author": "trickyzerg <3261677617@qq.com>|trickyzerg <3261677617@qq.com>", "remote_verified": true, "checked_utc": "2026-10-14T13:43:59.150020+00:00"}, "checkpoint80": {"model": "checkpoint80", "commit": "324bdbab60ed6a84edd2ccf93ec8265c44be5e46", "branch": "data-difficulty-muxi", "author": "trickyzerg <3261677617@qq.com>|trickyzerg <3261677617@qq.com>", "remote_verified": true, "checked_utc": "2026-10-14T13:16:54.749250+00:00"}}, "cloud": {"base_qwen25_7b": {"model": "base_qwen25_7b", "prefix": "runs/metax-five-model-test1024-20261014-v1/base_qwen25_7b", "verified": true, "errors": [], "checked_utc": "2026-10-14T13:44:21.754312+00:00"}, "checkpoint80": {"model": "checkpoint80", "prefix": "runs/metax-five-model-test1024-20261014-v1/checkpoint80", "verified": true, "errors": [], "checked_utc": "2026-10-14T13:17:47.082022+00:00"}}}}


2026-10-14T14:11:08.834560+00:00 模型完整结束：official_grpo_v02

# T1024五模型对比

固定NQ335+HotpotQA689，原128题完整保留；greedy单轨迹、10轮、256生成/2048观察/4096上下文，同一检索和action-stop。

| 模型 | 正确题数 | EM | NQ EM | HotpotQA EM | 未作答 | 检索次数 | 实测推理分钟 |
|---|---:|---:|---:|---:|---:|---:|---:|
| checkpoint80 | 488/1024 | 47.66% | 53.43% | 44.85% | 0 | 3591 | 14.53 |
| base_qwen25_7b | 229/1024 | 22.36% | 25.67% | 20.75% | 44 | 2678 | 25.89 |
| official_grpo_v02 | 456/1024 | 44.53% | 51.64% | 41.07% | 18 | 1677 | 25.88 |

未完成模型：checkpoint60、official_ppo_v02

原始EM按冻结标签计算；T128语义复核为独立已提交报告，不覆盖本次1024题金标准。

更新UTC：2026-10-14T14:11:08.817671+00:00



2026-10-14T14:11:53.766342+00:00 模型完整结束：official_grpo_v02

# T1024五模型对比

固定NQ335+HotpotQA689，原128题完整保留；greedy单轨迹、10轮、256生成/2048观察/4096上下文，同一检索和action-stop。

| 模型 | 正确题数 | EM | NQ EM | HotpotQA EM | 未作答 | 检索次数 | 实测推理分钟 |
|---|---:|---:|---:|---:|---:|---:|---:|
| checkpoint80 | 488/1024 | 47.66% | 53.43% | 44.85% | 0 | 3591 | 14.53 |
| base_qwen25_7b | 229/1024 | 22.36% | 25.67% | 20.75% | 44 | 2678 | 25.89 |
| official_grpo_v02 | 456/1024 | 44.53% | 51.64% | 41.07% | 18 | 1677 | 25.88 |

未完成模型：checkpoint60、official_ppo_v02

原始EM按冻结标签计算；T128语义复核为独立已提交报告，不覆盖本次1024题金标准。

更新UTC：2026-10-14T14:11:53.745609+00:00

