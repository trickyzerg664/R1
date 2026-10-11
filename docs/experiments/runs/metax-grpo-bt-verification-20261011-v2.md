# 单次实验记录：metax-grpo-bt-verification-20261011-v2

## 当前状态

- run_id：metax-grpo-bt-verification-20261011-v2；mx；/root；原v1失败后的独立重启，当前准备/CPU验证阶段，无正式GPU启动。
- B/T本次正式步数0/20；本次checkpoint0。v1实际完成B第1步、无持久checkpoint，不能从该步恢复。
- 父权重保持metax-process-r1-100-b32-gpu-20261008-v2/checkpoints/step_60/actor；参考Qwen2.5-7B，fresh optimizer/scheduler/scaler，seed42。
- 共用父D256已在v1完整评分122/256、缺答案0，原生stop/length779/779；本次显式复用，新增父评分0。冻结全部原始证据并重新验收，无训练更新。
- 下一步：CPU回归及配置冻结通过后重新从B第0步启动，两组首轮20步，保留256微批覆盖/有限指标/更新/显存/预算门限。

## 可复现信息

- 方案参数与v1完全一致：GRPO32题×8轨迹、micro8、mini128、8×MetaX C500、FP16、FlashAttention2、生成256token/turn、搜索10轮+最终回答。
- B：lr1e-6、Actor KL=.001、legacy reward。T：lr5e-7、Actor KL=.002、bounded_invalid_v1。task_success_mixed两组相同；不切换PPO。
- 七份配置只改输出路径、实验名称、冷加载checkpoint位置。D64、P、D256、父权重、参考权重、采样/奖励/损失/预热保持原值；restart-config-verification.json提供逐字段回退对照。
- 允许变更：DataProto跨rank指标收集修复；监督父评价复用与错误信息补全。原其他metadata仍取首份；未改训练计算。
- 代码commit、源快照、各配置/数据hash及冻结父评价原始文件hash见plan.json/manifest.json/source-snapshot.tar.gz，完成提交后才冻结/启动。
- 环境、命令见commands.json。独立检索服务保留PID2137145；各阶段独占RAY_TMPDIR，保留八卡锁。

## 运行位置及恢复

- 产物：/mnt/public/code/lyk/lzy/runs/metax-grpo-bt-verification-20261011-v2。
- started.json保留v1最初预算起点，另记重启准备时间；总48小时包含已用时间，监督46小时截止不重置。
- 正式PID尚未生成，实际启动后补填supervisor-process.json和各阶段process.json；无可恢复本次checkpoint。
- 默认只检查；显式--launch才运行。复用父评价不产生GPU任务，B/T仍调用原Hydra入口。
- v1产物全部保留，父评价记录hash绑定；不覆盖旧日志或把v1的第1步计入v2正式步数。

## 阶段进度与证据

| 阶段 | 已核实状态 | 证据 |
| --- | --- | --- |
| v1异常 | B第1步后监督主动停止，微批32/预期256 | v1/supervisor-console.log、B/metrics.jsonl |
| 修复前CPU复现 | 新跨rank测试4项均失败，含32!=256 | v1/concat-reproduction.log |
| 修复实现 | DataProto拼接收集全部rank列表/标量，字段缺失拒绝 | verl/protocol.py |
| 全量CPU | 正在核验，不以旧224项背书 | 本次cpu-regression.final.json |
| 配置与源冻结 | 待完成 | plan.json/manifest.json |
| 修复后正式八卡 | 未启动 | status.json实际检查时间为准 |

## 验证及结果

- 全量CPU真实入口不创建GPU；新4项跨rank拼接+2项父复用验收；单rankGPU旧测试不能替代跨rank验收。
- 修复前仅保留rank0所有微批指标，历史PG/熵/KL/norm须标记rank0样本；此前“全局均值”解释已更正。
- v1第1步有限loss/KL/norm、每rank两次更新，日志SIGTERM来源监督；无证据支持本次为模型退化、NaN或OOM。
- 正式验证要求：8rank完整256微批、有效token计数/全局加权熵有限、两个更新、无skip，首步通过后再观察后续2–5步；20步后才能冷D256对比。
- 修复收益目前仅涉及观察和监督正确性，不能宣称已证明长期退化改善。

## 失败、变更与交接历史

- v1监督07:39:59 UTC报告Microbatch observation coverage differs并主动终止。根因是DP_COMPUTE_PROTO最终DataProto.concat保留第0个rank的meta_info。
- v2首次CPU230项：0fail、1error，新增夹具中整数numpy总量无法直接json.dumps；修复夹具使用与实际浮点观察一致的数值，失败证据cpu-regression.attempt1.*保留。生产拼接已正确收齐所有rank，回归重跑中。
- 负责人/root；每次状态检查更新本记录与总台账；模型训练效果尚未证明。


## 2026-10-11T08:34:34.549052+00:00

CPU230项全部通过，失败/错误/跳过0；新增跨rank4项及父复用2项。修复前4项失败复现、首次CPU夹具1error及最终通过均保留；尚无修复后八卡实际更新证据。最后只补中文注释，未改变已测行为。注释审计按同名concat曾误选未修改DataProtoFuture.concat，已改为精确选取DataProto类。10函数标签完整，24/24语义逻辑单元均有有效中文说明，100%；此前17项清单由本完整清单补足，细目见本次source-audit.json。指标修复e6f4cbc、父评价复用4bf5ff9已提交，未推送。负责人/root。


## 2026-10-11T08:37:01.334099+00:00 冻结完成与重新启动

修复运行已冻结：源码092d63e9142774c37688f470f504927f33fb85d4，293份源码、16份资产含共享父评价3个原始文件；B/T真实配置验收通过、固定参考身份匹配父元数据、仅检查模式通过。两臂从父step60权重重新0步训练，复用父评分不新增评分，原总预算不重置。CPU230通过，正式八卡首步待验收。本次启动命令和PID见launcher-process.json/supervisor-process.json，真实后续进度以status.json为准；负责人/root。


2026-10-11T08:37:20.786386+00:00 restart inspection: {"checked_utc": "2026-10-11T08:37:20.786386+00:00", "state": {"status": "running", "phase": "B", "child_pid": 2847063, "gpu_current_MiB": [9627, 9691, 9627, 9627, 9627, 9627, 9627, 10331], "trained_step": 0, "latest_metrics": {}, "published_checkpoint_steps": [], "checked_utc": "2026-10-11T08:37:03.663885+00:00"}, "phase": "B", "fix8rank_verified": false}


{"checked_utc": "2026-10-11T08:38:54.535555+00:00", "state": {"status": "running", "phase": "B", "child_pid": 2847063, "trained_step": 0, "published_checkpoint_steps": [], "checked_utc": "2026-10-11T08:38:06.253003+00:00"}}


{"checked_utc": "2026-10-11T08:40:20.498071+00:00", "state": {"status": "running", "phase": "B", "child_pid": 2847063, "trained_step": 0, "published_checkpoint_steps": [], "checked_utc": "2026-10-11T08:40:10.739462+00:00"}}


{"checked_utc": "2026-10-11T08:41:36.434524+00:00", "state": {"status": "running", "phase": "B", "child_pid": 2847063, "trained_step": 0, "published_checkpoint_steps": [], "checked_utc": "2026-10-11T08:41:12.103531+00:00"}}


{"checked_utc": "2026-10-11T08:43:10.672946+00:00", "state": {"status": "running", "phase": "B", "child_pid": 2847063, "trained_step": 0, "published_checkpoint_steps": [], "checked_utc": "2026-10-11T08:42:13.444465+00:00"}}


{"checked_utc": "2026-10-11T08:44:34.000364+00:00", "state": {"status": "running", "phase": "B", "child_pid": 2847063, "trained_step": 0, "published_checkpoint_steps": [], "checked_utc": "2026-10-11T08:44:16.102194+00:00"}}


{"checked_utc": "2026-10-11T08:45:57.816257+00:00", "state": {"status": "running", "phase": "B", "child_pid": 2847063, "trained_step": 0, "published_checkpoint_steps": [], "checked_utc": "2026-10-11T08:45:17.425282+00:00"}}


{"checked_utc": "2026-10-11T08:47:32.611195+00:00", "state": {"status": "running", "phase": "B", "child_pid": 2847063, "trained_step": 0, "published_checkpoint_steps": [], "checked_utc": "2026-10-11T08:47:20.104842+00:00"}}


{"checked_utc": "2026-10-11T08:49:08.293442+00:00", "state": {"status": "running", "phase": "B", "child_pid": 2847063, "trained_step": 0, "published_checkpoint_steps": [], "checked_utc": "2026-10-11T08:48:21.426771+00:00", "observed_metrics": {}}}


{"checked_utc": "2026-10-11T08:50:40.789880+00:00", "state": {"status": "running", "phase": "B", "child_pid": 2847063, "trained_step": 0, "published_checkpoint_steps": [], "checked_utc": "2026-10-11T08:50:24.129322+00:00", "observed_metrics": {}}}


{"checked_utc": "2026-10-11T08:52:08.013821+00:00", "state": {"status": "running", "phase": "B", "child_pid": 2847063, "trained_step": 0, "published_checkpoint_steps": [], "checked_utc": "2026-10-11T08:51:25.477669+00:00", "observed_metrics": {}}}


{"checked_utc": "2026-10-11T08:53:25.100438+00:00", "state": {"status": "running", "phase": "B", "child_pid": 2847063, "trained_step": 0, "published_checkpoint_steps": [], "checked_utc": "2026-10-11T08:52:26.835944+00:00", "observed_metrics": {}}}


## 修复后首步真实八卡验收

UTC 2026-10-11T08:54:40.402062+00:00 修复后真实八卡首步验收通过：B已完成1/20、T0/20，本次完整checkpoint0。实际micro_batches_sum=256，model_tokens_sum=110232，与state_tokens/total=110232一致；每rankoptimizer_updates=2、step=1、skip=0。total_loss=-0.00126550335、KL=.3570661245、grad_norm=2.025775254、token加权熵=5.304382329全部有限。监督器status=running/phase=B/step1，已通过原先32!=256报错位置并继续运行，原数值/更新/显存门限保留。B第1步日志lr=1e-7为原10步warmup调度后的值，参数样本delta0与初始预热相容；本验收证明完整接线和监督，不宣称长期退化改善。证据 first-step-verification.json、B/metrics.jsonl、status.json。父D256复用122/256缺答案0、终止779/779；本次新增父评分0，T保持预定lr5e-7/KL.002/bounded_invalid_v1待后续运行。源/配置仍冻结092d63e，源码未改，CPU230通过；下一步按同一运行观察2–5步更新和两组20步冷D256结果，未自动扩展40/60。原失败v1全部保留、无checkpoint所以从同父重训；总预算仍原起点。负责人/root。


2026-10-11T09:11:25.363856+00:00 log query: {"status": "running", "phase": "B", "child_pid": 2847063, "trained_step": 2, "published_checkpoint_steps": [], "checked_utc": "2026-10-11T09:10:51.131757+00:00"}; evidence /mnt/public/code/lyk/lzy/runs/metax-grpo-bt-verification-20261011-v2/log-query.json


2026-10-11T09:31:29.327756+00:00 duration query: {"checked_utc": "2026-10-11T09:31:29.327756+00:00", "status": "running", "phase": "B", "trained_step": 3, "timings": {"B": [{"step": 1, "train_seconds": 746.246002079919, "step_seconds": 746.246002079919, "gen_seconds": 563.4140746612102, "rounds": 3}, {"step": 2, "train_seconds": 1482.3974567931145, "step_seconds": 736.1514547131956, "gen_seconds": 553.410706974566, "rounds": 3}, {"step": 3, "train_seconds": 2377.349385453388, "step_seconds": 894.9519286602736, "gen_seconds": 713.3773886766285, "rounds": 4}]}, "parent_evaluation_events": [{"schema_version": 1, "seed": 42, "event": "configuration", "config": {"data": {"record_token_diagnostics": true, "tokenizer": null, "train_files": "/mnt/public/code/lyk/lzy/data/runs/formal-pdt-7b8-v1/P.parquet", "val_files": "/mnt/public/code/lyk/lzy/runs/metax-checkpoint-curve-d256-20261005-v2/D256.parquet", "train_data_num": null, "val_data_num": null, "prompt_key": "prompt", "max_prompt_length": 4096, "max_response_length": 256, "max_start_length": 256, "max_obs_length": 2048, "train_batch_size": 32, "val_batch_size": 8, "return_raw_input_ids": false, "return_raw_chat": false, "shuffle_train_dataloader": true, "observation_truncation": "structured", "context_policy": "bounded", "record_generation_diagnostics": true}, "actor_rollout_ref": {"experiment_seed": 42, "hybrid_engine": true, "model": {"path": "/mnt/public/code/lyk/lzy/runs/metax-process-r1-100-b32-gpu-20261008-v2/checkpoints/step_60/actor", "external_lib": null, "override_config": {}, "enable_gradient_checkpointing": true, "attn_implementation": "flash_attention_2", "use_remove_padding": false}, "actor": {"activation_offload": true, "memory_diagnostics": true, "stability_diagnostics": {"enabled": true, "probe_after_update": false, "parameter_sample_size": 256}, "strategy": "fsdp", "ppo_mini_batch_size": 128, "ppo_micro_batch_size": 8, "use_dynamic_bsz": false, "ppo_max_token_len_per_gpu": 16384, "grad_clip": 1.0, "state_masking": true, "clip_ratio": 0.2, "entropy_coeff": 0.001, "use_kl_loss": true, "kl_loss_coef": 0.001, "kl_loss_type": "low_var_kl", "ppo_epochs": 1, "shuffle": false, "ulysses_sequence_parallel_size": 1, "optim": {"lr": 1e-06, "warmup_steps": 10, "lr_warmup_steps_ratio": 0.0, "min_lr_ratio": null, "warmup_style": "constant", "total_training_steps": -1}, "fsdp_config": {"wrap_policy": {"min_num_params": 0}, "param_offload": true, "grad_offload": false, "optimizer_offload": true, "fsdp_size": -1, "grad_scaler_init_scale": 16}, "response_logits_only": true, "checkpoint_token_statistics": true, "loss_numerics": "safe_v1", "token_statistics_chunk_size": 32}, "ref": {"memory_diagnostics": true, "model_path": "/mnt/public/model/huggingface/Qwen2.5-7B", "fsdp_config": {"param_offload": true, "wrap_policy": {"min_num_params": 0}, "fsdp_size": -1}, "log_prob_micro_batch_size": 8, "log_prob_use_dynamic_bsz": false, "log_prob_max_token_len_per_gpu": 16384, "ulysses_sequence_parallel_size": 1, "token_statistics_chunk_size": 32, "response_logits_only": true}, "rollout": {"name": "vllm", "temperature": 1.0, "top_k": -1, "top_p": 0.95, "prompt_length": 4096, "response_length": 256, "dtype": "float16", "gpu_memory_utilization": 0.32, "ignore_eos": false, "enforce_eager": true, "free_cache_engine": true, "load_format": "dummy_dtensor", "tensor_model_parallel_size": 1, "max_num_batched_tokens": 4352, "max_num_seqs": 64, "log_prob_micro_batch_size": 8, "log_prob_use_dynamic_bsz": false, "log_prob_max_token_len_per_gpu": 16384, "do_sample": true, "n": 1, "n_agent": 8, "offload_weights_to_cpu": true}}, "critic": {"strategy": "fsdp", "optim": {"lr": 1e-05, "lr_warmup_steps_ratio": 0.0, "min_lr_ratio": null, "warmup_style": "constant", "total_training_steps": -1}, "model": {"path": "~/models/deepseek-llm-7b-chat", "tokenizer_path": "/mnt/public/code/lyk/lzy/runs/metax-process-r1-100-b32-gpu-20261008-v2/checkpoints/step_60/actor", "override_config": {}, "external_lib": null, "enable_gradient_checkpointing": false, "use_remove_padding": false, "fsdp_config": {"param_offload": false, "grad_offload": false, "optimizer_offload": false, "wrap_policy": {"min_num_params": 0}, "fsdp_size": -1}}, "ppo_mini_batch_size": 128, "ppo_micro_batch_size": 64, "forward_micro_batch_size": 64, "use_dynamic_bsz": false, "ppo_max_token_len_per_gpu": 32768, "forward_max_token_len_per_gpu": 32768, "ulysses_sequence_parallel_size": 1, "ppo_epochs": 1, "shuffle": false, "grad_clip": 1.0, "cliprange_value": 0.5}, "reward_model": {"answer_mode": "response_only_v1", "validation_audit_path": "/mnt/public/code/lyk/lzy/runs/metax-grpo-bt-verification-20261011-v1/parent-eval/answers.jsonl", "enable": false, "strategy": "fsdp", "model": {"input_tokenizer": "/mnt/public/code/lyk/lzy/runs/metax-process-r1-100-b32-gpu-20261008-v2/checkpoints/step_60/actor", "path": "~/models/FsfairX-LLaMA3-RM-v0.1", "external_lib": null, "use_remove_padding": false, "fsdp_config": {"min_num_params": 0, "param_offload": false}}, "micro_batch_size": 64, "max_length": null, "ulysses_sequence_parallel_size": 1, "use_dynamic_bsz": false, "forward_max_token_len_per_gpu": 32768, "structure_format_score": 0, "final_format_score": 0, "retrieval_score": 0}, "retriever": {"timeout": 600, "url": "http://127.0.0.1:8000/retrieve", "topk": 3}, "algorithm": {"gamma": 1.0, "lam": 1.0, "adv_estimator": "grpo", "no_think_rl": false, "kl_penalty": "kl", "kl_ctrl": {"type": "fixed", "kl_coef": 0.001}, "state_masking": {"start_state_marker": "<information>", "end_state_marker": "</information>"}}, "trainer": {"total_epochs": 30, "total_training_steps": 20, "project_name": "metax_process_r1_100_b32", "experiment_name": "metax-grpo-bt-verification-20261011-v1-parent-eval", "logger": ["console"], "nnodes": 1, "n_gpus_per_node": 8, "save_freq": 20, "test_freq": -1, "critic_warmup": 0, "default_hdfs_dir": null, "default_local_dir": "/mnt/public/code/lyk/lzy/runs/metax-grpo-bt-verification-20261011-v1/parent-eval/checkpoints", "val_before_train": false, "val_only": true}, "max_turns": 10, "do_search": true, "difficulty": {"enabled": true, "mode": "train", "seed": 42, "score_seed": 1729, "score_batch_size": 8, "dynamic_filter": {"enabled": true, "max_rounds": 16, "eligibility": "task_success_mixed"}, "score_trace_chars": 0, "output_dir": "/mnt/public/code/lyk/lzy/runs/metax-grpo-bt-verification-20261011-v1/parent-eval", "labels": null, "ratios": null, "score_output": null, "refresh_steps": [], "refresh_every": 0, "resume": null, "resume_mode": "continue", "additional_steps": null, "retrieval_id": "wiki18-e5-metax-gpu-fp32-shard8-20261008-v1", "lineage": "eb482fb62db120d08db9fae3c3a93e2a00aa5c4c296a09de5ab4586702045f5d", "initial_model_id": "eb482fb62db120d08db9fae3c3a93e2a00aa5c4c296a09de5ab4586702045f5d", "group_size": 8}, "process_checks": {"enabled": true, "reward_gate": true, "missing_answer_penalty": 0.1, "reward_variant": "legacy", "invalid_action_penalty": 0.0, "process_penalty_cap": 0.12, "audit_path": "/mnt/public/code/lyk/lzy/runs/metax-grpo-bt-verification-20261011-v1/parent-eval/process-audit.jsonl"}, "trajectory_logging": {"enabled": true, "console_samples_per_source": 1, "every_n_batches": 1, "max_chars_per_trajectory": 12000, "search_result_max_chars": 1000, "file_path": "/mnt/public/code/lyk/lzy/runs/metax-grpo-bt-verification-20261011-v1/parent-eval/trajectories.readable.log", "file_samples_per_source": 2}}}], "parent_d256_stage_minutes": 41.39976094961166, "budget_remaining_hours": 42.73284629583359, "budget_stop_utc": "2026-10-13T04:15:27.574421+00:00"}; estimated duration pending interpretation, /root


耗时估算（本地北京时间2026-10-11 17:31附近）：B已完成3/20、T0/20。前三步timing_s/step为746.246/736.151/894.952秒，平均13.208分钟，当前剩37步粗估8–9小时；父D256阶段实测41.40分钟，后续两次独立D256加D64末步评价、checkpoint保存/校验/模型初始化预留2–3小时。因此首轮B/T20步+独立评价预计还需10–13小时，约10月12日03:30–06:30，表达为凌晨3–7点左右；动态筛选轮数、回答长度、checkpointIO可能延长，T尚未运行不能认为与B速度完全相同。48小时原预算未重置，监督截止北京时间10月13日12:15。此为小样本估算，非完成承诺；负责人/root。


2026-10-11T10:47:54.711251+00:00 user requested stop; SIGTERM sent to verified supervisor only; cleanup completion pending. Evidence /mnt/public/code/lyk/lzy/runs/metax-grpo-bt-verification-20261011-v2/user-stop-request.json; /root


## 原初始权重与调度选择

用户主动停止已确认（UTC 2026-10-11T10:53:39.957215+00:00）：原v2训练监督及所属八卡worker均退出，独立检索PID2137145保留；B实际完成8步、T0步，无COMPLETE checkpoint。原status因通用SIGTERM处理记failed，现据user-stop-request/进程检查另记stopped_by_user，保留原异常快照供审计。下一轮必须使用原100步训练初始权重metax-process-r1-40-20261006-v1/checkpoints/step_40/actor，从global_step0新建优化器/调度器/scaler和seed42，不恢复旧step60或v2状态。用户最新纠正：新奖励应使用；若保留B/T，新bounded_invalid_v1在两组共同启用，才评估lr与KL组合，不能将奖励同时变化归因到lr/KL。当前代码实际是10个完整GRPO周期线性warmup后恒定学习率，Actor KL由actor.kl_loss_coef直接读取且固定；algorithm.kl_ctrl在use_kl_loss=true时未接入直接Actor KL。建议本轮沿用已测日程，目标峰值lr5e-7、β=.002，保持β固定，实测KL仍变化；后期衰减/自适应KL另作独立对照，不能临场改参数混淆结果。此为对用户调度问题的建议，尚未冻结或启动新实验，未修改训练源码或新配置、未重跑CPU/GPU；之前230项/八卡指标验收仅适用已有修复。原初始HF Actor完整性与新健康评价尚待执行。负责人/root。
