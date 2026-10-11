# 单次实验记录：metax-grpo-bt-verification-20261011-v1

## 当前状态

- run_id：metax-grpo-bt-verification-20261011-v1；B/T配对首轮；负责人/root；主机mx。
- 状态：CPU及单卡小模型验收完成、配置准备完成；截至2026-10-11T06:37:49.887072+00:00尚未启动7B评价/正式训练。
- 当前动作：分功能提交新增代码，随后冻结并启动共同父评价。
- 正式GRPO已完成/目标新增步数：B 0/20，T 0/20；旧父模型为原100步运行step60权重，不恢复其优化器。
- 真实评价已完成/目标：0；父D256一次共享、D64固定开发探针、每臂最终D256冷加载。四轨迹标签评分不适用于本次零更新greedy评价。
- 新持久checkpoint：无；计划各组保存完整step20后才冷评价。
- 下一步与验收：父正常生成和原生终止门限、八卡前2–5步完整更新；未通过即记录失败，不自动改配置重启。
- 方案：grpo_stability_trial_validation_plan.md第7节及本条启动前锁定细则。

## 可复现信息

最终启动前验收：CPU224项通过，新增20项（指标3、奖励10、监督7），失败/错误/跳过0；test_fp16.py另在真实cuda:0运行1项通过，覆盖CPU以外的FP16小模型更新、单rank FSDP和溢出恢复。world_size=1下FSDP使用NO_SHARD，不能冒称八卡FULL_SHARD已验收；八卡完整更新将在B前2–5步按真实日志检查。正式GRPO更新仍0，真实7B生成0。

当前task_success_mixed与连续轨迹日志已分功能提交06688fc、7d0b5f7，研究文档f7975c5；未推送。损失展示只增加total_loss、有效模型token熵总量/计数及微批覆盖，现有循环位置正确。新bounded_invalid_v1奖励已接入：R=S-min(.12,.1*M+.02*min(N_invalid,2))，N_invalid仅原生stop且执行器拒绝的消费动作；length/未知免新增罚；loop项未启用；legacy默认原数值和旧恢复指纹兼容。新版本/系数进入训练身份，评价保持原EM。

监督入口默认仅检查，显式launch才顺序父D256、B20、B冷D256、T20、T冷D256；最初2–5步为同一训练中的八卡接线验收。持有八卡独占锁，56GiB总显存保护，整个预算48小时且46小时停止预留2小时收尾，任何非有限/更新跳过/实际微批覆盖不足停止并保留结果。只清理本阶段唯一RAY_TMPDIR和启动身份一致的进程，不全局停止Ray，不触碰独立检索。原生终止覆盖<95%或没有stop时采用已预冻结的T-LK配置，显式记录未验证新增奖励；不改正在运行的配置。父D256缺答案>12时停止，不擅自带异常父模型训练或更换父模型覆盖失败。两组20步完成后先分析，不自动延长40/60；总耗时目标一到两天不变。

父加载文件17项已流式哈希通过（仅HF Actor权重/分词器；旧优化器rank文件未使用），参考Qwen2.5-7B固定。固定D64为原D256顺序前30NQ/34Hotpot，生成配置不缩短；训练32题×8、micro8、mini128，fresh optimizer/scheduler/scaler，同seed42，同预热10步。B lr1e-6/Actor KL.001/legacy；T lr5e-7/Actor KL.002/bounded_invalid_v1。审计记录原生token/终止，文本文件每批每来源2条、控制台1条，两组相同；保留全量结构化审计，未新增字符特定惩罚。

职责：loss_observations和bounded_reward纯模块只消费张量/普通报告；worker与RewardManager仅薄接线；监督脚本调用现有Hydra入口、评分、checkpoint校验，不复制生成/训练算法。注释：43新增/修改函数标签无缺失，46/46语义逻辑单元有效中文说明，覆盖100%，关键逻辑独立检查；详列source-audit.json。GPU8、长期收益与实际异常复现待观察。产物 /mnt/public/code/lyk/lzy/runs/metax-grpo-bt-verification-20261011-v1；负责人/root；本条UTC由远程脚本填写。

- 初始权重：/mnt/public/code/lyk/lzy/runs/metax-process-r1-100-b32-gpu-20261008-v2/checkpoints/step_60/actor。
- 基础工作区功能提交与后续提交完整哈希：产物commits.json；最终启动源码版本与hash：plan.json/manifest.json；未提交生产变更为0后才启动。
- 历史原配置来自metax-process-r1-100-b32-gpu-20261008-v2/train.yaml，七份冻结配置包含两套T候选及评价，不将未执行候选记为完成。
- CPU环境vllm-metax-clean33，CUDA_VISIBLE_DEVICES为空；GPU小模型CUDA_VISIBLE_DEVICES=0；正式计划8×MetaX C500、FP16、FlashAttention2，GPU检索21,015,324向量独立服务PID2137145已核查。
- 数据/配置/检索及入口哈希在plan.json；D64.parquet与D256/P文件固定，T未使用。fresh optimizer无严格恢复分支，后续40/60必须另行锁定保留状态续训。

## 运行位置及恢复

- 产物根：/mnt/public/code/lyk/lzy/runs/metax-grpo-bt-verification-20261011-v1。
- 实际开始UTC见started.json；最后检查UTC 2026-10-11T06:37:49.887072+00:00；supervisor-process.json、各阶段process.json启动后才生成。
- console/log、metrics.jsonl、process-audit.jsonl、answers.jsonl和checkpoints均按parent-eval/B/B-eval/T/T-eval目录独立保存。
- 状态见status.json，配置选择见selected-design.json；当前GPU正式阶段PID未生成，不填计划PID。
- 本次无可恢复正式步数；不适用旧父优化器恢复，禁止伪称从旧训练完整状态续训。
- 已核查没有其他main_ppo训练；GPU仅独立检索占用。启动器再次核查八卡占用和独占锁。

## 阶段进度与证据

| 动作 | 实测状态 | 证据 |
| --- | --- | --- |
| 工作区分功能提交前CPU | 204项通过 | cpu-regression.prechange.* |
| 新奖励/指标CPU | 215项、217项及最终224项通过 | reward-attempt1/reward-final/final.* |
| 单卡FP16/FSDP小模型 | 1项通过、无skip | gpu-regression.json/log |
| 父HF Actor文件完整性 | 17文件hash通过 | parent-actor-verification.json |
| B/T及固定D64配置准备 | 完成，未启动GPU | config-check.json、各config.yaml |
| 中文注释检查 | 43函数，46/46逻辑单元 | source-audit.json |
| 父D256/正式B/T | 尚未开始 | 自动状态区块后续更新 |

## 验证及结果

实际执行入口（全部经ssh mx）：

```text
cd /mnt/public/code/lyk/lzy/R1-vllm-metax
CUDA_VISIBLE_DEVICES='' bash env/metax/run.sh /mnt/public/code/lyk/lzy/runs/metax-grpo-bt-verification-20261011-v1/cpu_verify.py
CUDA_VISIBLE_DEVICES=0 bash env/metax/run.sh /mnt/public/code/lyk/lzy/runs/metax-grpo-bt-verification-20261011-v1/gpu_verify.py
CUDA_VISIBLE_DEVICES='' bash env/metax/run.sh /mnt/public/code/lyk/lzy/runs/metax-grpo-bt-verification-20261011-v1/prepare_configs.py
```

- 正式启动命令会在完成冻结后写入commands.json，不将计划命令称作已执行。
- 当前只有CPU夹具、GPU小模型和历史文件核验结果；没有本次模型EM、训练reward或退化修复结论。
- 单卡FSDP验收与八卡完整更新单独记录；比较原EM/接受答案EM/生成异常和成本，新旧训练Reward均值不作为判胜。

## 失败、变更与交接历史

- 初次Git提交因远程未配置身份而失败，未创建提交；复用此前Codex <codex@localhost>身份以单命令配置重试成功，未改全局Git。
- 此前“PG/Entropy仅末微批”解释经AST复核更正，current/historical均完整micro循环；数值历史不被伪造重算。新增只读加权统计。
- 配置脚本首次传输引号失败、无GPU启动；修正JSON传输后7份配置及D64生成成功，记录config-preparation-attempt1.json。
- 新奖励未叠加循环惩罚、未新增动作级mask改动、保持GRPO。八卡训练与长期结论待验证。


<!-- metax-grpo-bt-verification-20261011-v1-current -->

{
  "status": "failed",
  "phase": "stopped",
  "error": "Microbatch observation coverage differs",
  "checked_utc": "2026-10-11T07:39:59.836720+00:00"
}

<!-- /metax-grpo-bt-verification-20261011-v1-current -->


## 2026-10-11T06:44:02.228693+00:00 验证实验实际启动

验证监督器已实际启动：launcher PID2829354，父D256评价PID2829362，启动UTC2026-10-11T06:41:56.895844+00:00。当前phase=parent-eval，正式GRPO训练步数B/T均0，无本次新checkpoint；不是已完成评价。冻结代码6cbd7dca5bafca19a9e4eb9c1c83c444a81c2233，292项源码/13项资产哈希核对通过，真实配置入口B/T均通过，固定reference与父元数据一致。实际命令为bash env/metax/run.sh -u scripts/difficulty/stability_trial.py --run-directory /mnt/public/code/lyk/lzy/runs/metax-grpo-bt-verification-20261011-v1 --launch，经ssh mx后台启动。下一步先确认父健康与原生终止门限，再按冻结方案顺序B20、B冷D256、T20、T冷D256。CPU224通过和单卡小模型1项通过仅代表已执行范围；父评价/八卡首段/长期效果尚在进行。进度以status.json自动区块实测时间为准；负责人/root。


## 2026-10-11 首批真实评价与日志确认

UTC2026-10-11T06:48:07.942504+00:00启动复核：共同父D256评价已完成首批8题的回答审计落盘；原生finish_reason实际观测到stop/length，完整D256覆盖率门限尚未判定。八卡引擎完成加载并实际生成，当前仍parent-eval，B/T正式更新均0。冻结292项源码及13项资产哈希再次一致。首批可读轨迹已按连续思考/搜索/结果/回答展示，未改变评分；不得以8题结果宣称父评价或训练修复完成。证据 launch-verification.json、parent-eval/answers.jsonl、parent-eval/trajectories.readable.log；当前进度以后续自动区块时间为准。负责人/root。


## 2026-10-11T06:55:29.897317+00:00 用户进度查询

当前阶段 parent-eval，状态 running；当前独立评价已落盘 56 条（阶段目标256；未完成不能称完整评价），本阶段训练步数 0；具体以status.json实际检查时间为准。证据 /mnt/public/code/lyk/lzy/runs/metax-grpo-bt-verification-20261011-v1/progress-query.json；负责人/root。


## 异常诊断与修复开始

本次异常诊断：UTC 2026-10-11T08:25:05.121718+00:00；B已完成第1个GRPO训练步、每rank两次优化器更新；无COMPLETE checkpoint，T尚未开始。父D256已完成122/256、缺答案0、原生终止779/779。监督器在微批计数检查实际32/预期256时主动SIGTERM，当前训练进程已退出、独立检索保留。根因是DP_COMPUTE_PROTO经DataProto.concat仅保留data[0].meta_info，丢弃rank1–7所有训练指标；此前CPU微批测试及单rankGPU测试未覆盖真实跨rank返回路径。微批循环自身覆盖完整；历史和本次全局PG/熵/KL/norm统计可能仅rank0，不能宣称全局均值。第1步total_loss=-0.0578348096、KL=.3623620658、grad_norm=2.02278173均有限，未出现跳过更新；该异常由监控数据汇集错误触发。修复将合并各rank metrics、保持其他metadata首份语义，覆盖计数仍256；不改变loss/reward/优化器。旧失败运行保留，新v2共用同父/参考/数据/超参/seed且两臂均从0重训；复用完整父评价需hash绑定并重验零更新/完整性，总48小时预算从原开始计。CPU/修复后八卡尚未验证。负责人/root。


<!-- metax-grpo-bt-verification-20261011-v2-current -->

{
  "status": "stopped_by_user",
  "phase": "stopped",
  "stopped_phase": "B",
  "trained_step": 8,
  "T_trained_step": 0,
  "published_checkpoint_steps": [],
  "reason": "User requested original initial checkpoint and revised controlled settings",
  "checked_utc": "2026-10-11T10:53:39.965951+00:00"
}

<!-- /metax-grpo-bt-verification-20261011-v2-current -->
