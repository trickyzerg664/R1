# 单次实验记录：metax-grpo-reward-100-20261011-v2

## 当前状态

- 负责人/root；v1单组历史对照。当前CPU准备，GPU未启动；训练0/100、评价0/256、本次完整checkpoint0。
- 旧B/T v2已停止：B8步、T0、无checkpoint；日志保留。
- 初始是历史100步真正的step40 actor；新建优化器和调度，从0训练100步。
- 下一步：HF哈希、CPU回归、配置差异、源码提交与冻结通过后启动。

## 可复现信息

- 历史基线：/mnt/public/code/lyk/lzy/runs/metax-process-r1-100-b32-gpu-20261008-v2。
- 初始actor：/mnt/public/code/lyk/lzy/runs/metax-process-r1-40-20261006-v1/checkpoints/step_40/actor；固定reference：/mnt/public/model/huggingface/Qwen2.5-7B。
- lr1e-6、warmup10后常数、Actor KL.001、clip.2、grad_clip1、entropy_coef.001保持历史。
- 同P/D256数据、8卡、train_batch32/val8、8轨迹、最长256、max_turns10、temperature1、top_p.95、每20步保存与D256验证。
- seed42，历史prepare_config也把experiment_seed由null设42并seed_all42；训练入口与历史相同main_ppo。
- 新奖励bounded_invalid_v1：缺答案罚.1、确认完整无效动作每次.02最多2次、过程罚总上限.12；长度截断/未知终止不算确认无效动作，无重复标点特例。
- 保留已授权task_success_mixed修复；结论为奖励+筛选组合效果，不能单独归因于奖励。
- 原生终止记录、只读诊断、连续轨迹、全rank指标修复保留；损失与优化器算法不变。
- 检索wiki18-e5-metax-gpu-fp32-shard8-20261008-v1、retriever PID2137145；启动前须核实健康。
- 代码/资产哈希及快照：manifest.json、source-snapshot.tar.gz待冻结；参数差异historical-config-diff.json待验收。
- 标签、配比、刷新及B分支续接：不适用。
- 总48小时沿用原验证起点，46小时停止预留收尾，不追加旧奖励训练臂。

## 运行位置及恢复

- 产物：/mnt/public/code/lyk/lzy/runs/metax-grpo-reward-100-20261011-v2。
- train/config.yaml、train/console.log、train/metrics.jsonl、train/process-audit.jsonl、train/validation-answers.jsonl、train/trajectories.readable.log。
- parent-eval/为初始零更新健康/原生终止验收；final-eval/为step100独立冷D256。
- commands.json记录实际命令；解析配置train/resolved-preflight.yaml；status.json持续记录真实步数。
- CPU准备时间见prepared.json；GPU开始/PID时间待启动，结束未核实。
- 20/40/60/80/100完整checkpoint为潜在恢复点，必须通过完整校验；本次暂无可恢复点。
- 故障不自动改变学习率、KL、batch、采样或上下文；未完整100步不能宣称完成。
- 旧v2训练已退出；新启动时重验八卡独占锁/GPU进程。

## 阶段进度与证据

| 时间UTC | 动作 | 实测进度 | 证据 | 下一步 |
| --- | --- | --- | --- | --- |
| prepared.json | CPU准备 | 训练0/100、评分0/256 | plan.unfrozen.json、配置 | 校验冻结 |

## 验证及结果

- 本次新增4项CPU回归待执行，不引用旧230项结果替代。
- 验收：每rank两次更新、全8rank微批256、loss/KL/norm/token熵有限；最终100步及完整step100、冷D256唯一256题且更新0。
- 比较相同步数20/40/60/80/100原EM、缺答案、无效动作、原生终止、回答长度、重复率与搜索行为；奖励需分解，不直接比较不同公式总reward。
- 历史EM分别113/116/122/132/129，均256题；step100重复验证需分轮，不合并为512题。
- 历史部分loss/熵/KL日志只有rank0，新日志全rank；不能直接将两者标量均值按同口径解释。
- 新筛选可能增加补抽时间；耗时和改善尚未实测。

## 失败、变更与交接历史

- 用户最新要求允许KL与学习率保持一致，本轮采用原值以隔离更多变量。
- 初次准备命令因系统python缺yaml在导入即失败，无文件/训练副作用；已改用项目独立环境。
- 新奖励原生终止证据不足必须停止，不回退旧奖励；此前失败/停止运行全保留。


## 2026-10-11T11:16:23.869996+00:00 v2准备

v1在Ray启动前失败，评价0/256、训练0，原状态与日志保留。v2只缩短Ray独占目录并加入启动前107字节验收；新奖励、task_success_mixed、lr1e-6、KL.001、旧step40初始Actor、数据和100步预算均不变。复用v1完整HF17文件哈希，重新检查所有文件大小/mtime一致；不复用step60评价。当前CPU准备，235项CPU回归待执行，GPU未启动；预算起点不重置。


## 2026-10-11T11:18:02.367083+00:00

Ray路径修复后的CPU235项全部通过，失败/错误/跳过0；v2路径保守按10位PID分别95/89/94字节，均小于107。旧v1父评价0、训练0、清理完成；HF17文件验证复用且大小mtime一致。实际训练算法与超参未改。下一步提交运行环境修复与记录，再重做冻结及仅检查；正式GPU尚未启动。
