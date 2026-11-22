# real7b-feasibility-20261118-v1

用途：真实Qwen2.5-7B全参数资源验证，合成输入，非pilot/full。

授权：2026-11-18用户要求在当前设备上验证全参SFT可行性。
源码：/root/myprojects/R1/R1，git HEAD 38beb1b；保留已有未提交PLAN/HANDOFF改动。
产物：/root/myprojects/R1/R1/.cache/real7b-feasibility-20261118-v1；checkpoint/export：/root/data/search-r1/sft-resource-checks/real7b-feasibility-20261118-v1。
第一阶段沿用CPU卸载；如内存受限，仅在scratch验证NVMe卸载。固定7B全参数/FP16/SDPA/4096长度/目标256/global32。
保护：MemAvailable低于12GiB或任一输出盘低于10GiB时终止本次子进程组；不终止其它任务。

- 2026-11-18T14:58:46.898347+08:00：已创建冻结scratch、合成64行4096-token输入及CPU/NVMe候选配置。正式训练配置未修改，尚未加载7B。

- 2026-11-18T14:59:22.872534+08:00：启动cpu-first-update，PID=3968925，日志/root/myprojects/R1/R1/.cache/real7b-feasibility-20261118-v1/cpu-first-update.log。

- 2026-11-18T15:12:35.617237+08:00：检测GPU0000:04:00.0管理查询Unknown Error，已仅终止本次验证进程组；尚无成功更新记录，原因与其它负载关系未确定。

- 2026-11-18T15:14:27.756830+08:00：cpu-first-update结束：status=failed，exit=-9，guard=None，最低可用内存26.96GiB；不将batch计数当成功更新。

- 2026-11-18T15:14:27.757757+08:00：cpu资源验证阶段收尾，完成0/3个阶段；详细状态见/root/myprojects/R1/R1/.cache/real7b-feasibility-20261118-v1/cpu-summary.json。

## 真实7B资源验证收尾（2026-11-18T15:17:02.583136+08:00）

运行real7b-feasibility-20261118-v1：真实76.16亿参数和全量可训练参数已加载，CPUAdam/ZeRO-3初始化完成，进入4096-token训练计算；成功更新0，无checkpoint，恢复/导出未验证。主机可用内存最低26.96GiB，未触发12GiB保护。15:08:28附近宿主机出现PCIe Uncorrected Fatal和GPU0000:04:00.0 fallen off bus；本次只终止自产进程组，未重置设备或重启主机。SIGTERM未完整收尾后向同一组发SIGKILL，exit=-9为人为收尾，不作为CUDA OOM或数值失败。NVMe候选未启动，真实数据pilot/full未启动。已有其它GPU负载，掉卡根因未确定。设备恢复前不继续GPU测试；恢复后仍需完成真实更新、保存恢复和导出验收。证据：.cache/real7b-feasibility-20261118-v1/assessment.json、cpu-first-update.log、资源JSONL和external_stop_reason.json。

补充核对：重新逐文件SHA确认实际7B Base身份，参数数来自真实run.json。由于Python模块解析优先采用仓库cwd，运行实际复用了原search_sft入口，scratch新增的参数探针未生效；未声称获得梯度范数或权重变化证据。此执行入口差异已记入assessment，不影响4096-token配置、CPUAdam初始化及宿主机PCIe掉卡证据。父launcher已退出；残留worker状态另列，不能将僵尸PID误报为训练仍运行。
