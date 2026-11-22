# host5-pilot-20261119-v2 resume1

恢复容器NVML访问后，从已完整保存的第10批恢复正式pilot，不重置为Base、不修改冻结模块/配置。失败attempt1日志/指标与第10批源checkpoint保留。第11–18批重放，尚未完成恢复/导出验收。

- 2026-11-20T12:24:21.306953+08:00：启动正式SFT pilot，PID51，日志/root/myprojects/R1/R1/.cache/host5-pilot-20261119-v2-resume1/pilot.log

- 2026-11-20T12:31:48.086004+08:00：pilot结束，status=failed，exit=1，guard=None

- 2026-11-20T12:31:48.087188+08:00：正式pilot收尾：未通过，保留失败记录，不自动启动full。
