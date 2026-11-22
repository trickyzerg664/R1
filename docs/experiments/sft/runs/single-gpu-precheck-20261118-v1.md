# 单卡验证前检查：single-gpu-precheck-20261118-v1

检查时间：2026-11-18T15:51:52.501221+08:00。状态：blocked，真实7B单卡训练未启动。

- 授权：用户要求改用一张卡试验；仅开展单卡只读检查和极小CUDA探针。
- 位置：host3 / lzy_yolo11 / /root/myprojects/R1/R1，sft分支，HEAD 38beb1b2b13490f156f286b642e3c6b058efaf19。
- 原故障卡0000:04:00.0仍无法查询。另一张TITAN RTX（0000:81:00.0）可以查询。
- 通过CUDA_VISIBLE_DEVICES仅选择后一张卡，执行torch.ones((32,32),device='cuda')，矩阵乘法并torch.cuda.synchronize()，结果32.0；进程正常退出。出现Can't initialize NVML警告。
- 检查命令：timeout --kill-after=5s 35s docker exec -e CUDA_VISIBLE_DEVICES=<selected GPU UUID> -e PYTHONUNBUFFERED=1 lzy_yolo11 .cache/sft-smoke-env/bin/python -c <上述独立CUDA探针>。实际Python使用项目绝对路径。
- 探针退出后快照：显存已用23600MiB，仅余611MiB，利用率0%，温度52C，功耗65.29W。
- 上次验证worker容器PID3968937/宿主机PID3402241仍关联19304MiB显存；主线程Z，残留线程3402534状态R。上次SIGKILL未使驱动释放上下文，不能重复kill声称解决。
- 另有非本次验证PID3359285，Z状态，关联4284MiB显存。未向其发信号。
- 没有加载7B，没有前后向、optimizer update、checkpoint或导出；小矩阵通过不代表单卡全参SFT通过。
- 没有重置GPU、重启容器/主机、终止其它任务，也未改正式配置。模型和数据未用于此探针。
- 前置条件：先安排设备恢复并释放残留显存，再检查单卡可用显存、主机内存和驱动状态。
- 恢复后的候选试验：独立run，真实同一7B Base、全参数、单GPU、microbatch1；若维持global32则累积32。是否增加CPU参数卸载以及长度阶梯须记录实际配置；当前未执行，不能宣称可行。
- 证据：/root/myprojects/R1/R1/.cache/single-gpu-precheck-20261118-v1/assessment.json。

## 用户要求直接kill后的结果

检查时间：2026-11-18T15:53:04.553192+08:00。核对宿主机PID3402241对应容器PID3968937以及容器身份后，通过docker exec --user 0再次向主线程3968937和残留线程3969009发送SIGKILL，命令返回0。3秒后主进程仍Z、宿主机线程3402534仍R，关联显存仍19304MiB；设备可用显存仍611MiB，未发生释放。宿主机SSH普通用户直接kill因权限不足失败，随后通过所属容器root执行成功；这不是自动审批拒绝。没有向其他任务发信号，没有reset/reboot。需要安排设备恢复后才能继续真实7B单卡验证。证据：/root/myprojects/R1/R1/.cache/single-gpu-precheck-20261118-v1/worker-kill.json。
