# 单次实验记录：metax-grpo-reward-100-20261011-v1

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

- 产物：/mnt/public/code/lyk/lzy/runs/metax-grpo-reward-100-20261011-v1。
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


## 2026-10-11T11:11:04.576143+00:00 CPU与父模型验收

本轮234项CPU回归全部通过，失败/错误/跳过0；新增4项覆盖声明100步检查点、旧20步兼容、单训练组及新奖励禁止回退。初始HF Actor17文件全部SHA256匹配COMPLETE；检索健康ready，GPU仅独立检索PID2137145，无其他训练。配置/源码冻结仍待执行，GPU尚未启动。测试使用CUDA_VISIBLE_DEVICES='' bash env/metax/run.sh <run>/cpu_verify.py；证据cpu-regression.final.json/log、parent-actor-verification.json。本次最后仅补目标/元数据分支中文说明，无行为变更，234结果仍适用；真实八卡新实验及后期退化改善尚未验证。


## 2026-10-11T11:13:43.262463+00:00 冻结与实际启动

配置白名单验收通过：除新奖励、task_success_mixed、必要终止/只读诊断与日志、输出路径外，全部历史配置一致，学习率/KL/采样/长度/batch/保存评价频率无变化。实际入口的initial_model_id/reference_id/retrieval_id/seed均与旧100步run.json匹配。已提交监督扩展650a3bc、方案与停止记录5afad19；冻结293源码和15资产，manifest/source-snapshot/配置差异齐全；监督仅检查模式通过。按既有用户授权启动父D256健康验收→一个100步训练→step100冷D256；预算沿原2026-10-11T06:15:27起点，46h截止2026-10-13T04:15:27UTC，预留2h收尾。此时正式训练0、评分0，不宣称算法效果。


<!-- metax-grpo-reward-100-20261011-v1-current -->

{
  "status": "failed",
  "phase": "stopped",
  "error": "Stage failed: parent-eval exit=1",
  "checked_utc": "2026-10-11T11:14:25.571425+00:00"
}

<!-- /metax-grpo-reward-100-20261011-v1-current -->


启动检查：{"checked_utc": "2026-10-11T11:14:08.165382+00:00", "state": {"status": "running", "phase": "parent-eval", "child_pid": 2868872, "gpu_current_MiB": [9627, 9691, 9627, 9627, 9627, 9627, 9627, 10331], "trained_step": 0, "checked_utc": "2026-10-11T11:13:44.957899+00:00"}, "parent_completed_answers": 0, "supervisor_alive": true}；证据startup-inspection.json；负责人/root。


## 2026-10-11T11:15:35.161235+00:00 Ray启动路径错误与最小修复

新奖励100步v1在ray.init报AF_UNIX路径超107字节，父评价0/256、训练0、模型未加载。监督器已失败清理自身进程；独立检索保留。增加启动前Ray socket路径字节长度检查，按10位PID保守估计，超过107在GPU启动前拒绝；缩短本次ray_base，训练语义及总预算不变。新增CPU回归覆盖长目录拒绝与短目录通过，尚待本次运行。 注释范围：verify职责/路径保守估计/按阶段遍历/过长拒绝，测试职责/禁止GPU/长短目录对照；7/7语义单元中文说明，100%，verify参数与异常标签、测试函数标签完整。
