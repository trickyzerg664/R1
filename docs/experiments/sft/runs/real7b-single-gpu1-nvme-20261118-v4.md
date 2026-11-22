# real7b-single-gpu1-nvme-20261118-v4

状态：prepared，等待GPU1空闲后再启动。原NCCL被故障GPU0的NVML初始化阻塞；Gloo+CPU optimizer offload实际触发主机可用内存低于12GiB保护，本候选改为NVMe optimizer offload。GPU1 UUID绑定、global32、累积32、FP16、SDPA、4K输入不变。使用原生DeepSpeed FP16模型导出及新进程CPU冷加载，不使用不支持NVMe外置状态的FP32合并导出。不是原NCCL/CPU卸载配置验收。

- 位置：host3 / lzy_yolo11 / /root/myprojects/R1/R1；sft，HEAD38beb1b；保留已有文档改动。
- 真实同一Qwen2.5-7B Base，全参数；FP16/SDPA/ZeRO-3/NVMe optimizer offload。
- 合成64行，每行4096 token（3840 prompt+256 target），global32，micro1，单卡累积32。
- 原配置不变；独立scratch源码只加同步阶段日志、FP16模型参数抽样（NVMe主状态不可直接抽样）和无条件Base哈希校验。
- 阶段：第一批更新并保存；新进程恢复第二批并保存；导出与新进程CPU冷加载。
- 本次从scratch/source启动并校验实际模块路径，修复v1探针未生效的问题。
- 保护：可用内存低于12GiB、磁盘低于10GiB、GPU管理查询失败、阶段超时3600秒，仅终止自产进程组。
- 输出：/root/data/search-r1/sft-resource-checks/real7b-single-gpu1-nvme-20261118-v4；日志/资源：/root/myprojects/R1/R1/.cache/real7b-single-gpu1-nvme-20261118-v4。不是pilot/full，不使用真实教师数据。
- NVMe主状态：/root/myprojects/R1/R1/.cache/real7b-single-gpu1-nvme-20261118-v4/nvme，在项目盘约85.1GiB主状态+最多约28.4GiB梯度文件，按113.5GiB加余量预检；checkpoint约85.1GiB/份，保存峰值约170.2GiB，在数据盘按187.2GiB门槛预检；FP16 HF约14.2GiB。两文件系统独立检查。

- 2026-11-18T19:51:16.340943+08:00：物理GPU1已空闲，GPU0仍为故障状态，未重置设备；已准备real7b-single-gpu1-nvme-20261118-v4，实际模块路径核对通过。

- 2026-11-18T19:52:18.609547+08:00：启动first-update，PID2344，日志/root/myprojects/R1/R1/.cache/real7b-single-gpu1-nvme-20261118-v4/first-update.log。

- 2026-11-18T20:13:08.284284+08:00：first-update结束：complete，exit=0，guard=None；最低可用内存45.41GiB。

- 2026-11-18T20:13:08.287849+08:00：启动resume-second-update，PID3151，日志/root/myprojects/R1/R1/.cache/real7b-single-gpu1-nvme-20261118-v4/resume-second-update.log。

- 2026-11-18T20:22:27.887523+08:00：GPU1恢复worker3157执行pause；仅控制本次进程，保留checkpoint。等待记录/root/myprojects/R1/R1/.cache/real7b-single-gpu1-nvme-20261118-v4/resource-waits.json。

## GPU1因共享资源停止等待 2026-11-18T20:45:58.422878+08:00

NVMe/Gloo候选完成首次32微批前后向、未溢出的零学习率warmup step（范数31.882936）及完整checkpoint1。恢复期间其它用户再次占用GPU1，已等待约22分钟，仍无法满足后续显存需求；仅终止自产controller/launcher/worker并释放本次GPU上下文，没有操作其它用户任务。

真实非零学习率权重变化、恢复完成及导出均未通过，不把本次写为资源验收成功。完整可恢复来源：/root/data/search-r1/sft-resource-checks/real7b-single-gpu1-nvme-20261118-v4/single-cpu/checkpoints/step_00000001/complete.json。/root/myprojects/R1/R1/.cache/real7b-single-gpu1-nvme-20261118-v4/nvme是被中断的工作目录，不可直接当作checkpoint；下次必须新进程从完整checkpoint重新load。

重试保留相同config/source/world1/stage=smoke/run-id=single-cpu，使用原Python及CACHE内libaio环境，命令torch.distributed.run --standalone --nproc_per_node=1 -m search_sft.train --config /root/myprojects/R1/R1/.cache/real7b-single-gpu1-nvme-20261118-v4/cpu.yaml --stage smoke --run-id single-cpu --resume，cwd=/root/myprojects/R1/R1/.cache/real7b-single-gpu1-nvme-20261118-v4/source，CUDA_VISIBLE_DEVICES固定GPU1 UUID，LD_LIBRARY_PATH/CPATH/LIBRARY_PATH采用.cache/sft-libaio-20261118/sysroot/usr下已验证路径。须先核对GPU1有足够持续空闲，不能重启controller的first-update入口覆盖同一run。完成训练原生FP16导出后，运行search_sft.export --verify-only进行新进程CPU冷加载。

## GPU1候选资源验证收尾 2026-11-18T20:45:58.422878+08:00

real7b-single-gpu1-nvme-20261118-v4结果incomplete_shared_gpu_busy。Gloo/NVMe optimizer offload/FP16 native HF export；真实结果和局限见/root/myprojects/R1/R1/.cache/real7b-single-gpu1-nvme-20261118-v4/report.md及final-assessment.json。已保留NCCL初始化失败、Gloo CPU卸载内存保护记录；非正式训练、非原NCCL方案验收。
