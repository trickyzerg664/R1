# metax-qwen7b-tokenfix-100-20261012-v1

负责人 /root；2026-10-12T09:35:15.813044+00:00。用户要求同配置重启，并明确从原始Qwen7B开始。actor=/mnt/public/model/huggingface/Qwen2.5-7B，优化器/调度器/scaler从0，seed42；其余训练超参逐字段核对。保留token对齐、人工边界和概率布局修复及日志修复。

当前CPU准备，训练0/100、评分0/256，GPU尚未启动。原stopped_by_user运行与checkpoint20/40保持。计划初始D256→一个100步训练→最终D256，每20步评价保存。新监督single_train记录初始缺答案门槛256，允许未训练模型缺答案和全length终止；仍要求原生终止覆盖>=95%、完整唯一评价、无更新、资源/数值/文件身份保护，旧默认缺答案门槛12保持。

本轮监督扩展全量CPU回归返回码 0；证据 /mnt/public/code/lyk/lzy/runs/metax-qwen7b-tokenfix-100-20261012-v1/cpu-regression.log。模型/数据/源码冻结待完成，GPU未启动。

资产与配置验收开始；CPU全量回归通过，训练0步，原始Qwen模型进行完整文件哈希与safetensors头部验证。

冻结验收通过：{"checked_utc": "2026-10-12T09:45:14.044657+00:00", "run": "/mnt/public/code/lyk/lzy/runs/metax-qwen7b-tokenfix-100-20261012-v1", "model": "/mnt/public/model/huggingface/Qwen2.5-7B", "sources": 295, "assets": 9, "config_differences": 10, "identity": {"initial_model_id": "7c3269c21a61915411e593401dbe335b9c427a02702067f986bce261e592a76e", "reference_id": "7c3269c21a61915411e593401dbe335b9c427a02702067f986bce261e592a76e", "retrieval_id": "wiki18-e5-metax-gpu-fp32-shard8-20261008-v1", "seed": 42, "training": "f0a614f1a94a0fdaec4cc32eb8a7b4b74f681374bb4909ff7231e6abcfaf53d4", "versions": {"torch": "2.6.0+metax3.3.0.2", "transformers": "4.57.1", "vllm": "0.11.0+empty"}, "world_size": 8}, "cpu_verified": true, "gpu_started": false, "free_bytes": 2839140677632}。下一步按用户授权启动初始D256→100步训练→最终D256。初始化改变，不能归因于单个代码修复。


按用户授权实际启动：{"pid": 3262363, "proc_start_ticks": "1012239300", "started_utc": "2026-10-12T09:49:20.375695+00:00", "argv": ["bash", "env/metax/run.sh", "-u", "scripts/difficulty/stability_trial.py", "--run-directory", "/mnt/public/code/lyk/lzy/runs/metax-qwen7b-tokenfix-100-20261012-v1", "--launch"]}。流程为原始Qwen初始D256→一个100步训练→最终D256，训练超参指纹与旧运行相同，初始化指纹改为原始Qwen。此时只确认监督进程创建，完成训练0步、评分题数尚未确认。


<!-- metax-qwen7b-tokenfix-100-20261012-v1-current -->

{
  "status": "stopped_for_fix_restart",
  "phase": "stopped",
  "reason": "User requested scoring mask fix and fresh original-Qwen restart",
  "trained_step": 0,
  "published_checkpoint_steps": [],
  "checked_utc": "2026-10-12T10:52:00.169490+00:00"
}

<!-- /metax-qwen7b-tokenfix-100-20261012-v1-current -->

启动实查：{"checked_utc": "2026-10-12T09:58:10.776118+00:00", "launcher_alive": true, "state": {"status": "running", "phase": "parent-eval", "child_pid": 3262371, "gpu_current_MiB": [36342, 38517, 39030, 38645, 40885, 38773, 40821, 41590], "trained_step": 0, "checked_utc": "2026-10-12T09:57:39.136323+00:00"}, "completed_parent_answers": 16, "worker_count": 8, "errors": []}；八卡rollout worker已进入生成，检索健康ready。证据startup-inspection.json。已完成训练0/100；初始评价题数以该检查值为准，后续监督器按分钟更新。


## 2026-10-12T10:44:07.256038+00:00 运行与验证评分复核（/root）

当前phase=train、status=running，已完成训练0/100、已发布checkpoint=[]。初始D256已完整唯一完成：原验证EM79/256（30.8594%），评分提取缺答案26；协议接受答案EM83/256（32.4219%），协议缺答案10。训练阶段已启动并在加载worker/模型；本次尚无train指标事件，无法评价实际梯度或反传健康。日志持续推进，检索health ready，未见OOM、Traceback、ActorDied或通信异常；启动barrier设备提示为警告，不能当作已发生故障。

确认验证评分缺陷：按question_id匹配17条已作答记录的评分文本缺少</answer>，末轮存在人工重建边界；其中4条协议接受答案正确但原验证记0。main_ppo.py:119-121用info_mask构造评分文本，将用于排除人工边界梯度的掩码也用于删除评分字符。验证仍返回original_em，因此准确率低估4/256；当前训练apply_process_reward=true且reward_gate=true，main_ppo.py:146-159从协议接受答案计算candidate_score，不能将该验证提取错误直接等同于训练奖励错误。

918轮原生终止均已知（stop737/length181），采样前缀错位0、文本前缀错位0、314个人工边界token已标记。模型输出质量仍需关注：粗筛49条有8词片段至少重复4次，消费文本未见至少20汉字混杂或1000连续空白；粗筛不能单独判定乱码。262个冻结Python源文件此前复核未变，本次仅只读检查并保存派生证据、更新文档，未修改训练源代码/配置/模型、未运行新测试。

证据：/mnt/public/code/lyk/lzy/runs/metax-qwen7b-tokenfix-100-20261012-v1/progress-health-20261012-104407.json；parent-eval/summary.json、answers.jsonl、process-audit.jsonl，train/console.log与metrics.jsonl。下一步优先分离评分文本与梯度掩码，修复验证提取并回归验收；继续检查首步真实loss/KL/梯度与更新覆盖，不能使用当前原EM直接评价修复效果。


2026-10-12T10:52:00.223899+00:00 用户要求修复评分掩码、提交Git并重启：已核验launcher/child启动身份后停止并清理所属Ray进程，独立检索PID2137145保持。状态stopped_for_fix_restart；完成训练0/100，checkpoint=[]。初始评价和旧冻结清单、日志全部保留，未覆盖旧manifest。证据user-fix-restart-stop-request.json、user-fix-restart-stop-result.json、status.supervisor-exit-fix-restart.json。负责人/root；下一步评分来源掩码修复与CPU/历史真实tokenizer回归。
