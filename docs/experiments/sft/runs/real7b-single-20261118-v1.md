# real7b-single-20261118-v1

状态：prepared。用户确认一张卡释放后要求单卡试验。沿用已修正的int64抽样探针；独立修正恢复阶段磁盘预检对已有checkpoint的重复预算，正式源码不变。

- 位置：host3 / lzy_yolo11 / /root/myprojects/R1/R1；sft，HEAD38beb1b；保留已有文档改动。
- 真实同一Qwen2.5-7B Base，全参数；FP16/SDPA/ZeRO-3/CPU optimizer offload。
- 合成64行，每行4096 token（3840 prompt+256 target），global32，micro1，单卡累积32。
- 原配置不变；独立scratch源码只加同步阶段日志、FP32主参数抽样和无条件Base哈希校验。
- 阶段：第一批更新并保存；新进程恢复第二批并保存；导出与新进程CPU冷加载。
- 本次从scratch/source启动并校验实际模块路径，修复v1探针未生效的问题。
- 保护：可用内存低于12GiB、磁盘低于10GiB、GPU管理查询失败、阶段超时3600秒，仅终止自产进程组。
- 输出：/root/data/search-r1/sft-resource-checks/real7b-single-20261118-v1；日志/资源：/root/myprojects/R1/R1/.cache/real7b-single-20261118-v1。不是pilot/full，不使用真实教师数据。

- 2026-11-18T17:29:12.869366+08:00：物理GPU0已空闲，另一张卡仍有其它用户负载；已准备real7b-single-20261118-v1，实际模块路径核对通过。

- 2026-11-18T17:29:36.723903+08:00：启动first-update，PID1031，日志/root/myprojects/R1/R1/.cache/real7b-single-20261118-v1/first-update.log。

- 2026-11-18T17:33:27.079405+08:00：first-update结束：failed，exit=-9，guard=gpu_management_query_failed；最低可用内存35.40GiB。

- 2026-11-18T17:33:27.081189+08:00：单卡资源验证结果not_passed；成功更新与参数变化见/root/myprojects/R1/R1/.cache/real7b-single-20261118-v1/assessment.json。

## 单卡验证收尾 2026-11-18T17:36:39.831707+08:00

# 单卡真实7B全参验证结果

运行：real7b-single-20261118-v1。故障时间：2026-11-18 17:33:15（北京时间）。

结论：真实7B已加载并完成优化器初始化；完成6个微批次前后向，第7个微批次反向期间同一张GPU0（0000:04:00.0）再次掉卡，资源验收未通过。

- 模型：同一Qwen2.5-7B Base，7,615,616,512参数全部可训练；核心11文件按历史SHA验证。
- 配置：单TITAN RTX 24GB，UUID绑定GPU0；FP16动态缩放、SDPA、ZeRO-3、CPU optimizer offload；micro1、累积32、global32；合成4096输入token/256目标token。
- 已完成：权重加载、CPUAdam初始化、7次前向、6次完整反向，损失有限。
- 未完成：第一次真实optimizer更新、checkpoint、恢复、导出；没有权重变化或梯度范数验收证据。微批次的engine.step(boundary=false)不是实际参数更新。
- 内核：Xid79 GPU has fallen off the bus；PCIe Uncorrected Fatal；SDES和Completion Timeout；设备恢复失败。
- 故障前torch allocated峰值：19.206GiB；设备总显存采样峰值：21220MiB；温度采样峰值：86C；功耗采样峰值：260.23W。这些采样不能排除瞬时供电/温度事件。
- 最低宿主机可用内存：35.403GiB；没有CPU内存保护或CUDA OOM记录。
- 守护器因GPU管理查询失败停止本次进程组，随后清理本次worker；exit=-9是清理动作，不是OOM证据。残留worker/线程详见final-assessment.json。
- 另一张GPU1仍有其它用户任务；本训练仅用GPU0，但整机不是单GPU负载，因此不能排除整机供电或散热因素。
- 结果说明故障不要求本训练进行双GPU通信；仍需排查GPU0、其插槽/链路/供电，以及驱动平台，不能仅凭日志认定板卡损坏或温度为根因。
- 没有重置GPU、重启机器或终止其他用户任务；不继续在故障设备上重试。
- 独立scratch修正了恢复磁盘预检重复计入已有checkpoint的问题；本次未进入恢复阶段，该修正尚未得到真实恢复验证。正式源码及正式训练配置未修改。
- 原始证据：/root/myprojects/R1/R1/.cache/real7b-single-20261118-v1；输出元信息：/root/data/search-r1/sft-resource-checks/real7b-single-20261118-v1/single-cpu。未启动真实数据pilot/full。
