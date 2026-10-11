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
