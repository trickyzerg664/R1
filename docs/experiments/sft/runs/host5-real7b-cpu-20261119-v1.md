# host5-real7b-cpu-20261119-v1

用户2026-11-19授权准备完成后在host5开始实验；本run为host5资源前置验收，非正式数据pilot/full。
真实Qwen2.5-7B Base，全参数，FP16/SDPA/ZeRO3/CPU optimizer offload；单TITAN RTX24GB，NCCL world1，micro1/accum32/global32，合成4096-token输入/256目标。
复用迁移后已通过环境检查的.cache/sft-smoke-env，冻结pip清单；独立scratch复制已加阶段/参数探针和FP16导出的资源验证源码，避免修改正式源码。
本资源run warmup_ratio=0，以便两次更新都验证真实变化；正式实验5% warmup不变。
CPU内存预算紧，基本估算113.5GiB、开始可用119.06GiB。本次单卡闲置主机资源测试采用MemAvailable<4GiB终止自产进程组；此阈值只用于host5候选，未修改旧run。输出磁盘<10GiB、GPU查询失败、单阶段5400秒同样停止。
阶段：第一步保存；新进程恢复第二步保存及FP16 HF导出；独立CPU冷加载。尚未运行/通过的阶段不记成功。
输出：/root/data/search-r1/sft-runs/host5-real7b-cpu-20261119-v1；日志：/root/myprojects/R1/R1/.cache/host5-real7b-cpu-20261119-v1。host3原件不修改。正式数据仍draft，历史评测资产恢复中。

- 2026-11-19T15:27:16.203395+08:00：host5单卡CPU卸载资源候选已准备；正式pilot/full尚未启动。

- 2026-11-19T15:27:16.276626+08:00：启动first-update，PID4254，日志/root/myprojects/R1/R1/.cache/host5-real7b-cpu-20261119-v1/first-update.log

- 2026-11-19T15:37:36.171932+08:00：first-update结束，status=failed，exit=-9，guard=host_mem_available_below_4GiB
