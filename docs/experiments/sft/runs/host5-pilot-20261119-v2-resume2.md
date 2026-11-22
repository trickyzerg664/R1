# host5-pilot-20261119-v2 resume1

恢复容器NVML访问后，从已完整保存的第10批恢复正式pilot，不重置为Base、不修改冻结模块/配置。失败attempt1日志/指标与第10批源checkpoint保留。第11–18批重放，尚未完成恢复/导出验收。

- 2026-11-20T12:35:22.094620+08:00：启动正式SFT pilot，PID394，日志/root/myprojects/R1/R1/.cache/host5-pilot-20261119-v2-resume2/pilot.log

- 2026-11-20T15:11:39.720909+08:00：pilot结束，status=complete，exit=0，guard=None

- 2026-11-20T15:11:39.789003+08:00：启动正式SFT cold-load，PID4320，日志/root/myprojects/R1/R1/.cache/host5-pilot-20261119-v2-resume2/cold-load.log

- 2026-11-20T15:12:26.584775+08:00：cold-load结束，status=complete，exit=0，guard=None

- 2026-11-20T15:12:29.395863+08:00：pilot完整checkpoint及HF冷加载已通过，仅清理本run可重建swap临时状态；checkpoint/HF保留。

- 2026-11-20T15:12:29.396358+08:00：正式pilot收尾：训练及HF冷加载通过；尚未进行统一效果评价/full。
