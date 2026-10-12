# metax-qwen7b-tokenfix-100-20261012-v1

负责人 /root；2026-10-12T09:35:15.813044+00:00。用户要求同配置重启，并明确从原始Qwen7B开始。actor=/mnt/public/model/huggingface/Qwen2.5-7B，优化器/调度器/scaler从0，seed42；其余训练超参逐字段核对。保留token对齐、人工边界和概率布局修复及日志修复。

当前CPU准备，训练0/100、评分0/256，GPU尚未启动。原stopped_by_user运行与checkpoint20/40保持。计划初始D256→一个100步训练→最终D256，每20步评价保存。新监督single_train记录初始缺答案门槛256，允许未训练模型缺答案和全length终止；仍要求原生终止覆盖>=95%、完整唯一评价、无更新、资源/数值/文件身份保护，旧默认缺答案门槛12保持。

本轮监督扩展全量CPU回归返回码 0；证据 /mnt/public/code/lyk/lzy/runs/metax-qwen7b-tokenfix-100-20261012-v1/cpu-regression.log。模型/数据/源码冻结待完成，GPU未启动。

资产与配置验收开始；CPU全量回归通过，训练0步，原始Qwen模型进行完整文件哈希与safetensors头部验证。

冻结验收通过：{"checked_utc": "2026-10-12T09:45:14.044657+00:00", "run": "/mnt/public/code/lyk/lzy/runs/metax-qwen7b-tokenfix-100-20261012-v1", "model": "/mnt/public/model/huggingface/Qwen2.5-7B", "sources": 295, "assets": 9, "config_differences": 10, "identity": {"initial_model_id": "7c3269c21a61915411e593401dbe335b9c427a02702067f986bce261e592a76e", "reference_id": "7c3269c21a61915411e593401dbe335b9c427a02702067f986bce261e592a76e", "retrieval_id": "wiki18-e5-metax-gpu-fp32-shard8-20261008-v1", "seed": 42, "training": "f0a614f1a94a0fdaec4cc32eb8a7b4b74f681374bb4909ff7231e6abcfaf53d4", "versions": {"torch": "2.6.0+metax3.3.0.2", "transformers": "4.57.1", "vllm": "0.11.0+empty"}, "world_size": 8}, "cpu_verified": true, "gpu_started": false, "free_bytes": 2839140677632}。下一步按用户授权启动初始D256→100步训练→最终D256。初始化改变，不能归因于单个代码修复。


按用户授权实际启动：{"pid": 3262363, "proc_start_ticks": "1012239300", "started_utc": "2026-10-12T09:49:20.375695+00:00", "argv": ["bash", "env/metax/run.sh", "-u", "scripts/difficulty/stability_trial.py", "--run-directory", "/mnt/public/code/lyk/lzy/runs/metax-qwen7b-tokenfix-100-20261012-v1", "--launch"]}。流程为原始Qwen初始D256→一个100步训练→最终D256，训练超参指纹与旧运行相同，初始化指纹改为原始Qwen。此时只确认监督进程创建，完成训练0步、评分题数尚未确认。


<!-- metax-qwen7b-tokenfix-100-20261012-v1-current -->

{
  "status": "running",
  "phase": "parent-eval",
  "child_pid": 3262371,
  "gpu_current_MiB": [
    40758,
    41205,
    40885,
    15925,
    40821,
    41205,
    15989,
    41654
  ],
  "trained_step": 0,
  "checked_utc": "2026-10-12T10:28:22.381158+00:00"
}

<!-- /metax-qwen7b-tokenfix-100-20261012-v1-current -->

启动实查：{"checked_utc": "2026-10-12T09:58:10.776118+00:00", "launcher_alive": true, "state": {"status": "running", "phase": "parent-eval", "child_pid": 3262371, "gpu_current_MiB": [36342, 38517, 39030, 38645, 40885, 38773, 40821, 41590], "trained_step": 0, "checked_utc": "2026-10-12T09:57:39.136323+00:00"}, "completed_parent_answers": 16, "worker_count": 8, "errors": []}；八卡rollout worker已进入生成，检索健康ready。证据startup-inspection.json。已完成训练0/100；初始评价题数以该检查值为准，后续监督器按分钟更新。
