# real7b-single-gpu1-20261118-v1

状态：prepared。用户明确要求改用空闲物理GPU1进行同配置对照；GPU0故障未恢复。沿用已修正的int64抽样探针；独立修正恢复阶段磁盘预检对已有checkpoint的重复预算，正式源码不变。

- 位置：host3 / lzy_yolo11 / /root/myprojects/R1/R1；sft，HEAD38beb1b；保留已有文档改动。
- 真实同一Qwen2.5-7B Base，全参数；FP16/SDPA/ZeRO-3/CPU optimizer offload。
- 合成64行，每行4096 token（3840 prompt+256 target），global32，micro1，单卡累积32。
- 原配置不变；独立scratch源码只加同步阶段日志、FP32主参数抽样和无条件Base哈希校验。
- 阶段：第一批更新并保存；新进程恢复第二批并保存；导出与新进程CPU冷加载。
- 本次从scratch/source启动并校验实际模块路径，修复v1探针未生效的问题。
- 保护：可用内存低于12GiB、磁盘低于10GiB、GPU管理查询失败、阶段超时3600秒，仅终止自产进程组。
- 输出：/root/data/search-r1/sft-resource-checks/real7b-single-gpu1-20261118-v1；日志/资源：/root/myprojects/R1/R1/.cache/real7b-single-gpu1-20261118-v1。不是pilot/full，不使用真实教师数据。

- 2026-11-18T19:10:57.688542+08:00：物理GPU1已空闲，GPU0仍为故障状态，未重置设备；已准备real7b-single-gpu1-20261118-v1，实际模块路径核对通过。

- 2026-11-18T19:11:48.727435+08:00：启动first-update，PID1373，日志/root/myprojects/R1/R1/.cache/real7b-single-gpu1-20261118-v1/first-update.log。

- 2026-11-18T19:11:48.771047+08:00：first-update结束：failed，exit=-15，guard=gpu_management_query_failed；最低可用内存108.51GiB。

- 2026-11-18T19:11:48.772022+08:00：单卡资源验证结果not_passed；成功更新与参数变化见/root/myprojects/R1/R1/.cache/real7b-single-gpu1-20261118-v1/assessment.json。
