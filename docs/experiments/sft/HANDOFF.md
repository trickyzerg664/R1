# 当前状态与接手说明

更新日期为 2026-11-22。当前 SFT 正式训练和四模型统一评测均已完成。接手时请重新核对服务器和产物状态。

- 训练位于 host5 的 lzy 容器，工作区为 /root/myprojects/R1/R1，分支为 sft。
- 正式训练从原始 Qwen2.5-7B 开始，使用 deepseek_host5_full_20261120_v2.yaml。host5-full-20261120-v2 完成 88 个优化器更新，最终验证损失为 0.4908150。[训练记录](runs/host5-full-20261120-v2.md)
- 最终 HF 导出位于 /root/data/search-r1/sft-runs/host5-full-20261120-v2/hf，已独立加载校验。
- 四模型统一评测与真实轨迹审计见 [Host5 统一评测](HOST5_COMPARISON.md)。后续 GRPO 训练尚未启动。
- 训练中实际使用的 DeepSpeed 0.15.4 补丁位于 scripts/sft/patches。补丁需应用到对应版本的安装目录，记录中保存了修复前后的校验值。

## 2026-11-18 历史快照

更新日期：2026-11-18。这是状态快照，接手时必须重新检查进程、Git、文件和空闲资源。

## 当前任务与位置

- 用户要求：准备同历史RL的7B Base，并将SFT计划固定为可供任何agent接手的仓库文档。未启动真实数据pilot/full。
- host3 → lzy_yolo11 → `/root/myprojects/R1/R1`，分支sft，沿用原Git工作区。
- 官方起点598e61bd；初次实现ccd104a；磁盘修正29a0d31。最新文档/资产准备提交以 `git log` 为准，不把fork main 71e072a4作为新起点。
- 原9个RL修改保存在data-difficulty的cb6551f，34项CPU测试通过，不属于本SFT分支。

## 状态表

| 项目 | 已确认状态 | 证据/下一步 |
|---|---|---|
| SFT实现 | 已提交并推送；独立search_sft入口 | configs/sft、scripts/sft/run_host3.sh |
| CPU验证 | 最新26项通过，4.60s | 历史实现记录及sft_validation_20261117.json |
| 双卡小模型 | ZeRO-3/FP16/SDPA/CPUAdam通过，恢复与连续参数差0；HF冷加载通过 | .cache/sft-validation-20261117/comparison.json及v4日志；仅20,768参数 |
| 7B Base | 已下载，11/11核心文件本地SHA匹配历史RL身份 | .cache/models/Qwen2.5-7B/base-verification.json |
| 正式隔离环境 | .envs/sft尚未建立 | 已有.cache/sft-smoke-env仅用于准备/验证，继承系统Torch |
| DeepSeek raw | 3,011题，完整SHA校验通过 | data/sft/raw/accepted.jsonl |
| 学生重放draft | 1,814题；train1632/3897行，val182/440行，pilot256/615行 | data/sft/releases/deepseek-draft-20261117-v1 |
| 正式数据 | 未发布，历史评价排重及证据复核未全部完成 | 缺完整data/sft/evaluation/manifest.json，禁止手改draft为final |
| 检索资产 | Wiki/FAISS/E5/Arrow已在；无需重下 | 见资产路径，正式查询回归未做 |
| 真实7B资源 | 未验收，CPU卸载预算偏紧 | 先解决内存，再按RUNBOOK形成真实7B短跑配置 |
| 真实训练 | pilot/full均未启动 | 无真实数据run_id及训练步数 |
| 统一评价 | 尚未建立并验收最终工作区 | 按PLAN冻结口径，不能用旧分数代替新后端重评 |

## Base下载接手

- 公开仓库Qwen/Qwen2.5-7B；固定revision `d149729398750b98c0af14eb82c78cfe92750796`。
- 目标：`.cache/models/Qwen2.5-7B`。
- 任务状态：`.cache/sft-base-download-20261118/status.json`；模型校验完成文件：目标目录的base-verification.json。
- 已完成的下载命令：`.cache/sft-smoke-env/bin/python -m search_sft.download_base --endpoint https://hf-mirror.com --job-dir .cache/sft-base-download-20261118`。
- 直连HF曾连接超时；经镜像下载完成，四个权重分片和7个小文件共11个核心文件均已做本地SHA256校验，与历史RL身份一致。
- status内pid是已完成下载任务的历史PID，不能据此认定下载仍运行。接手先检查phase和base-verification.json，完整资产无需重下；只有文件损坏/缺失时再按RUNBOOK恢复。公开模型不需要私人HF token。
- Base资产状态为ready；仅完成下载与文件校验，尚未加载真实7B或启动训练，不能据此宣称资源验收完成。

## 已有资产与文件系统

| 内容 | 路径 | 占用GiB |
|---|---|---:|
| SFT原始/draft/tokenizer | 项目data/sft | 0.10 |
| 源QA train/test | /root/data/search-r1/datasets/nq_hotpotqa_train | 0.40 |
| Wiki18 JSONL | /root/data/search-r1/retrieval/wiki18/wiki-18.jsonl | 13.41 |
| E5 Flat index | /root/data/search-r1/retrieval/wiki18/e5_Flat.index | 60.13 |
| E5模型 | /root/data/search-r1/models/e5-base-v2 | 0.41 |
| Arrow缓存 | /root/data/search-r1/cache/retriever/datasets | 12.82 |
| corpus offsets | /root/myprojects/search-r1-synth/cache/corpus_offsets.npy | 0.16 |

有效资产约87.4GiB。索引768维、21,015,324向量，头部/长度匹配；索引和语料文件身份与既有SHA校验记录一致，本轮未重读60GiB计算完整SHA或加载到内存。

项目盘与/root/data是不同文件系统。下载前快照：项目盘空闲约214GiB，数据盘261GiB；下载及其它任务会改变它们。默认输出应使用 `/root/data/search-r1/sft-runs`，Base/环境放项目盘。单run187.2GiB，加保留pilot HF共需输出盘约215.6GiB。若保留pilot全部状态则约300.7GiB，当前数据盘余量不足；不要只按单run计算两阶段。

part_aa/part_ab及wiki-18.jsonl.gz额外约64.9GiB，未删除。已有Coder-7B-Instruct、Coder来源PRM和Qwen3不能代替本实验Base，不删除其它项目权重。

## 接手后按依赖推进

1. 确认当前分支、Git和Base完成记录；11个核心文件已校验，无需重复下载。
2. 获取并核对历史评价题单、完成数据排重/可见性复核；生成新的final release和更新数量。可与环境准备并行。
3. 建立正式独立环境；明确CPU/GPU/磁盘资源方案，不能沿用小模型结果宣称7B通过。
4. 用户授权相应实验阶段后，完成真实7B资源短跑、完整保存/恢复/导出验收。
5. final数据、资源及程序通过后，按PLAN运行pilot；验收后full从Base重新开始。
6. 统一评价、成本和逐题结果记录；各阶段都使用唯一run_id并留真实证据。

已确认风险：当前CPU模型状态估算113.5–170.2GiB，而上次可用约106GiB；正确7B下载不解决这个内存问题。历史D/T清单缺失仍会阻止正式发布。teacher数据成本与RL训练池交集未完整核实，记unknown，不编造0。

## 最近检查快照

检查时间：2026-11-18T00:30:12+08:00。

- 下载phase：downloading；PID：3828658；已校验3 / 11核心文件。
- 已写入权重（含未完成分片）约8.78GiB，不代表全部SHA已通过。进度继续以status.json和进程为准。
- 本次固定计划/命令入口和默认模型、数据盘输出路径已同步。CLI帮助可调用；当前配置下26项CPU回归通过（4.60s），没有重跑GPU训练。

## Base完成快照

检查时间：2026-11-18T00:40:38+08:00。

- 下载phase=complete；11/11核心文件通过本地SHA256，errors为空；共15,242,788,009字节（14.196GiB）。
- 本次交接入口提交38beb1b已推送；本段及教师精确模型标识是host3工作区中的补充更新，尚未提交/推送。自动审批拒绝了补充提交并推送，理由是公开GitHub目的地可能暴露私有数据来源及实验元信息；等待用户确认后再处理外发。
- 本次只完成文档和Base准备，没有启动真实7B资源验收或真实数据pilot/full。下一项仍是历史评价资产/最终数据、正式环境及资源问题。

## 2026-11-18 用户授权真实7B资源验证

运行记录：runs/real7b-feasibility-20261118-v1.md。只用合成输入，不启动正式数据pilot/full。

- 2026-11-18T14:58:46.898347+08:00：已创建冻结scratch、合成64行4096-token输入及CPU/NVMe候选配置。正式训练配置未修改，尚未加载7B。

- 2026-11-18T14:59:22.872534+08:00：启动cpu-first-update，PID=3968925，日志/root/myprojects/R1/R1/.cache/real7b-feasibility-20261118-v1/cpu-first-update.log。

- 2026-11-18T15:12:35.617237+08:00：检测GPU0000:04:00.0管理查询Unknown Error，已仅终止本次验证进程组；尚无成功更新记录，原因与其它负载关系未确定。

- 2026-11-18T15:14:27.756830+08:00：cpu-first-update结束：status=failed，exit=-9，guard=None，最低可用内存26.96GiB；不将batch计数当成功更新。

- 2026-11-18T15:14:27.757757+08:00：cpu资源验证阶段收尾，完成0/3个阶段；详细状态见/root/myprojects/R1/R1/.cache/real7b-feasibility-20261118-v1/cpu-summary.json。

## 真实7B资源验证收尾（2026-11-18T15:17:02.583136+08:00）

运行real7b-feasibility-20261118-v1：真实76.16亿参数和全量可训练参数已加载，CPUAdam/ZeRO-3初始化完成，进入4096-token训练计算；成功更新0，无checkpoint，恢复/导出未验证。主机可用内存最低26.96GiB，未触发12GiB保护。15:08:28附近宿主机出现PCIe Uncorrected Fatal和GPU0000:04:00.0 fallen off bus；本次只终止自产进程组，未重置设备或重启主机。SIGTERM未完整收尾后向同一组发SIGKILL，exit=-9为人为收尾，不作为CUDA OOM或数值失败。NVMe候选未启动，真实数据pilot/full未启动。已有其它GPU负载，掉卡根因未确定。设备恢复前不继续GPU测试；恢复后仍需完成真实更新、保存恢复和导出验收。证据：.cache/real7b-feasibility-20261118-v1/assessment.json、cpu-first-update.log、资源JSONL和external_stop_reason.json。

补充核对：重新逐文件SHA确认实际7B Base身份，参数数来自真实run.json。由于Python模块解析优先采用仓库cwd，运行实际复用了原search_sft入口，scratch新增的参数探针未生效；未声称获得梯度范数或权重变化证据。此执行入口差异已记入assessment，不影响4096-token配置、CPUAdam初始化及宿主机PCIe掉卡证据。父launcher已退出；残留worker状态另列，不能将僵尸PID误报为训练仍运行。

## 单卡验证前检查（2026-11-18T15:51:52.501221+08:00）

用户要求改用单卡。0000:81:00.0独立32x32 CUDA矩阵乘法同步成功，但仅余611MiB显存；前次worker3968937仍占19304MiB，另有非本任务残留占4284MiB。故障卡仍Unknown Error。未启动7B训练、未更新参数，未reset/reboot或终止其它任务。需先安排设备恢复、释放驱动残留显存，再做单卡真实7B验证。记录：runs/single-gpu-precheck-20261118-v1.md；产物：/root/myprojects/R1/R1/.cache/single-gpu-precheck-20261118-v1。

## 用户要求直接kill后的结果

检查时间：2026-11-18T15:53:04.553192+08:00。核对宿主机PID3402241对应容器PID3968937以及容器身份后，通过docker exec --user 0再次向主线程3968937和残留线程3969009发送SIGKILL，命令返回0。3秒后主进程仍Z、宿主机线程3402534仍R，关联显存仍19304MiB；设备可用显存仍611MiB，未发生释放。宿主机SSH普通用户直接kill因权限不足失败，随后通过所属容器root执行成功；这不是自动审批拒绝。没有向其他任务发信号，没有reset/reboot。需要安排设备恢复后才能继续真实7B单卡验证。证据：/root/myprojects/R1/R1/.cache/single-gpu-precheck-20261118-v1/worker-kill.json。

- 2026-11-18T16:52:21.577979+08:00：双卡已恢复且空闲，项目容器已启动；已准备real7b-dual-20261118-v2，实际模块路径核对通过。

- 2026-11-18T16:53:02.538047+08:00：启动first-update，PID78，日志/root/myprojects/R1/R1/.cache/real7b-dual-20261118-v2/first-update.log。

- 2026-11-18T16:54:59.295487+08:00：first-update结束：failed，exit=1，guard=None；最低可用内存39.91GiB。

- 2026-11-18T16:54:59.297543+08:00：双卡资源验证结果not_passed；成功更新与参数变化见/root/myprojects/R1/R1/.cache/real7b-dual-20261118-v2/assessment.json。

- 2026-11-18T16:57:11.593127+08:00：双卡已恢复且空闲，项目容器已启动；已准备real7b-dual-20261118-v3，实际模块路径核对通过。

- 2026-11-18T16:57:12.293075+08:00：启动first-update，PID402，日志/root/myprojects/R1/R1/.cache/real7b-dual-20261118-v3/first-update.log。

# 双卡资源验证暂停记录

时间：2026-11-18T17:08:04.484647+08:00。用户明确要求暂停任务。

- 本次运行：real7b-dual-20261118-v3；真实Qwen2.5-7B Base，全参数，双TITAN RTX，4K合成输入。
- 已终止本次控制器及匹配该运行配置路径的训练进程；未操作其他用户任务。
- 剩余本次训练进程：[]。
- 已完成optimizer update：0；checkpoint：None。
- 最近阶段：{"0": {"resource_phase": "backward_start", "batch": 1, "micro": 13}, "1": {"resource_phase": "backward_start", "batch": 1, "micro": 13}}。
- 无checkpoint时，累积梯度不保留，下次需从同一Base重新开始；不是可断点恢复状态。
- 本次尚未完成双卡资源验收，未启动真实数据pilot/full。
- 暂停前确认其他用户huoyao在两张卡上各有一个进程，每卡约4.2GB；本次不是独占资源测试。
- 产物：/root/myprojects/R1/R1/.cache/real7b-dual-20261118-v3；训练输出：/root/data/search-r1/sft-resource-checks/real7b-dual-20261118-v3/dual-cpu。
- v2因新增探针浮点索引舍入越界退出，v3使用int64索引修正；保留前次失败证据。


- 2026-11-18T17:29:12.869546+08:00：物理GPU0已空闲，另一张卡仍有其它用户负载；已准备real7b-single-20261118-v1，实际模块路径核对通过。

- 2026-11-18T17:29:36.723990+08:00：启动first-update，PID1031，日志/root/myprojects/R1/R1/.cache/real7b-single-20261118-v1/first-update.log。

- 2026-11-18T17:33:27.079578+08:00：first-update结束：failed，exit=-9，guard=gpu_management_query_failed；最低可用内存35.40GiB。

- 2026-11-18T17:33:27.081333+08:00：单卡资源验证结果not_passed；成功更新与参数变化见/root/myprojects/R1/R1/.cache/real7b-single-20261118-v1/assessment.json。

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


- 2026-11-18T19:10:57.688626+08:00：物理GPU1已空闲，GPU0仍为故障状态，未重置设备；已准备real7b-single-gpu1-20261118-v1，实际模块路径核对通过。

- 2026-11-18T19:11:48.727513+08:00：启动first-update，PID1373，日志/root/myprojects/R1/R1/.cache/real7b-single-gpu1-20261118-v1/first-update.log。

- 2026-11-18T19:11:48.771163+08:00：first-update结束：failed，exit=-15，guard=gpu_management_query_failed；最低可用内存108.51GiB。

- 2026-11-18T19:11:48.772101+08:00：单卡资源验证结果not_passed；成功更新与参数变化见/root/myprojects/R1/R1/.cache/real7b-single-gpu1-20261118-v1/assessment.json。

- 2026-11-18T19:12:48.307142+08:00：物理GPU1已空闲，GPU0仍为故障状态，未重置设备；已准备real7b-single-gpu1-20261118-v2，实际模块路径核对通过。

- 2026-11-18T19:13:43.060038+08:00：启动first-update，PID1444，日志/root/myprojects/R1/R1/.cache/real7b-single-gpu1-20261118-v2/first-update.log。

- 2026-11-18T19:14:38.149337+08:00：first-update结束：failed，exit=1，guard=None；最低可用内存107.79GiB。

- 2026-11-18T19:14:38.150253+08:00：单卡资源验证结果not_passed；成功更新与参数变化见/root/myprojects/R1/R1/.cache/real7b-single-gpu1-20261118-v2/assessment.json。

- 2026-11-18T19:21:23.802112+08:00：物理GPU1已空闲，GPU0仍为故障状态，未重置设备；已准备real7b-single-gpu1-gloo-20261118-v3，实际模块路径核对通过。

- 2026-11-18T19:22:16.152994+08:00：启动first-update，PID1679，日志/root/myprojects/R1/R1/.cache/real7b-single-gpu1-gloo-20261118-v3/first-update.log。

- 2026-11-18T19:27:08.612611+08:00：first-update结束：failed，exit=1，guard=host_memory_below_12GiB；最低可用内存11.58GiB。

- 2026-11-18T19:27:08.615094+08:00：单卡资源验证结果not_passed；成功更新与参数变化见/root/myprojects/R1/R1/.cache/real7b-single-gpu1-gloo-20261118-v3/assessment.json。

- 2026-11-18T19:51:16.341099+08:00：物理GPU1已空闲，GPU0仍为故障状态，未重置设备；已准备real7b-single-gpu1-nvme-20261118-v4，实际模块路径核对通过。

- 2026-11-18T19:52:18.609631+08:00：启动first-update，PID2344，日志/root/myprojects/R1/R1/.cache/real7b-single-gpu1-nvme-20261118-v4/first-update.log。

- 2026-11-18T20:13:08.285123+08:00：first-update结束：complete，exit=0，guard=None；最低可用内存45.41GiB。

- 2026-11-18T20:13:08.287998+08:00：启动resume-second-update，PID3151，日志/root/myprojects/R1/R1/.cache/real7b-single-gpu1-nvme-20261118-v4/resume-second-update.log。

- 2026-11-18T20:22:27.887523+08:00：GPU1恢复worker3157执行pause；仅控制本次进程，保留checkpoint。等待记录/root/myprojects/R1/R1/.cache/real7b-single-gpu1-nvme-20261118-v4/resource-waits.json。

## GPU1因共享资源停止等待 2026-11-18T20:45:58.422878+08:00

NVMe/Gloo候选完成首次32微批前后向、未溢出的零学习率warmup step（范数31.882936）及完整checkpoint1。恢复期间其它用户再次占用GPU1，已等待约22分钟，仍无法满足后续显存需求；仅终止自产controller/launcher/worker并释放本次GPU上下文，没有操作其它用户任务。

真实非零学习率权重变化、恢复完成及导出均未通过，不把本次写为资源验收成功。完整可恢复来源：/root/data/search-r1/sft-resource-checks/real7b-single-gpu1-nvme-20261118-v4/single-cpu/checkpoints/step_00000001/complete.json。/root/myprojects/R1/R1/.cache/real7b-single-gpu1-nvme-20261118-v4/nvme是被中断的工作目录，不可直接当作checkpoint；下次必须新进程从完整checkpoint重新load。

重试保留相同config/source/world1/stage=smoke/run-id=single-cpu，使用原Python及CACHE内libaio环境，命令torch.distributed.run --standalone --nproc_per_node=1 -m search_sft.train --config /root/myprojects/R1/R1/.cache/real7b-single-gpu1-nvme-20261118-v4/cpu.yaml --stage smoke --run-id single-cpu --resume，cwd=/root/myprojects/R1/R1/.cache/real7b-single-gpu1-nvme-20261118-v4/source，CUDA_VISIBLE_DEVICES固定GPU1 UUID，LD_LIBRARY_PATH/CPATH/LIBRARY_PATH采用.cache/sft-libaio-20261118/sysroot/usr下已验证路径。须先核对GPU1有足够持续空闲，不能重启controller的first-update入口覆盖同一run。完成训练原生FP16导出后，运行search_sft.export --verify-only进行新进程CPU冷加载。

## GPU1候选资源验证收尾 2026-11-18T20:45:58.422878+08:00

real7b-single-gpu1-nvme-20261118-v4结果incomplete_shared_gpu_busy。Gloo/NVMe optimizer offload/FP16 native HF export；真实结果和局限见/root/myprojects/R1/R1/.cache/real7b-single-gpu1-nvme-20261118-v4/report.md及final-assessment.json。已保留NCCL初始化失败、Gloo CPU卸载内存保护记录；非正式训练、非原NCCL方案验收。


## host5迁移补充 2026-11-18T22:42:57.899256+08:00

host5/lzy迁移完成；host3原件保留。host3单卡NVMe/Gloo续跑已完成非零更新、保存和HF冷加载；详情见HOST5_MIGRATION.md。host5只完成环境检查，真实7B/pilot/full未启动。用户要求停止剩余全量SHA核验，复制全部完成，不能宣称全量hash通过。

- 2026-11-19T15:27:16.203286+08:00：host5单卡CPU卸载资源候选已准备；正式pilot/full尚未启动。

- 2026-11-19T15:27:16.276538+08:00：启动first-update，PID4254，日志/root/myprojects/R1/R1/.cache/host5-real7b-cpu-20261119-v1/first-update.log

- 2026-11-19：host5单卡入口和独立候选配置已准备，bash语法检查通过；正式数据仍未发布，pilot/full未启动。资源run调度仍至少一步零学习率warmup，观察真实更新以参数探针为准。

- 2026-11-19T15:37:36.138972+08:00：first-update结束，status=failed，exit=-9，guard=host_mem_available_below_4GiB

- 2026-11-19T16:03:32.022367+08:00：正式SFT磁盘卸载适配已安装，等待数据证据复核清单及新final release；pilot/full未启动。源代码修改前副本与前后身份见.cache/host5-sft-adaptations-20261119。host3未修改。

- 2026-11-19T16:16:53.383077+08:00：启动正式SFT pilot，PID5256，日志/root/myprojects/R1/R1/.cache/host5-pilot-20261119-v1/pilot.log

- host5正式SFT补充：新final为1657题，train1491/3583行、val166/405行、pilot256/617行。180风险题助手复核为keep31/quarantine148/exclude1；原始数据未改。历史P10000已从原固定归档恢复，规范化问题精确交集104题，属于允许训练池重合，不记为测试泄漏。完整记录见.cache/host5-pilot-20261119-v1/p10000-overlap.json。29项CPU测试通过；没有新增GPU合成smoke。

- 2026-11-19T16:41:55.253195+08:00：pilot结束，status=failed，exit=1，guard=None

- 2026-11-19T16:41:55.274041+08:00：正式pilot收尾：未通过，保留失败记录，不自动启动full。

- 2026-11-19T16:49:07.953609+08:00：正式pilot v1首批在新增采样记录处因previous_probe作用域错误退出；前后向及lr0 optimizer调用已执行但0条完整batch指标、无checkpoint，最低可用内存62.20GiB，非内存保护。已修复初始化位置，静态检查从3处错误到0；保留日志及失败源码。清理该失败run可重建swap后，新run host5-pilot-20261119-v2从Base重新启动；同一final数据与训练参数，非smoke。

- 2026-11-19T16:49:11.602564+08:00：启动正式SFT pilot，PID6113，日志/root/myprojects/R1/R1/.cache/host5-pilot-20261119-v2/pilot.log

- 2026-11-19T21:00:41.515722+08:00：pilot结束，status=failed，exit=1，guard=gpu_management_query_failed

- 2026-11-19T21:00:41.516958+08:00：正式pilot收尾：未通过，保留失败记录，不自动启动full。

- 2026-11-20T12:24:21.307072+08:00：启动正式SFT pilot，PID51，日志/root/myprojects/R1/R1/.cache/host5-pilot-20261119-v2-resume1/pilot.log

- 2026-11-20T12:31:48.086192+08:00：pilot结束，status=failed，exit=1，guard=None

- 2026-11-20T12:31:48.087337+08:00：正式pilot收尾：未通过，保留失败记录，不自动启动full。

- 2026-11-20T12:35:22.094698+08:00：启动正式SFT pilot，PID394，日志/root/myprojects/R1/R1/.cache/host5-pilot-20261119-v2-resume2/pilot.log

- 2026-11-20T15:11:39.727758+08:00：pilot结束，status=complete，exit=0，guard=None

- 2026-11-20T15:11:39.789228+08:00：启动正式SFT cold-load，PID4320，日志/root/myprojects/R1/R1/.cache/host5-pilot-20261119-v2-resume2/cold-load.log

- 2026-11-20T15:12:26.584939+08:00：cold-load结束，status=complete，exit=0，guard=None

- 2026-11-20T15:12:29.395950+08:00：pilot完整checkpoint及HF冷加载已通过，仅清理本run可重建swap临时状态；checkpoint/HF保留。

- 2026-11-20T15:12:29.396413+08:00：正式pilot收尾：训练及HF冷加载通过；尚未进行统一效果评价/full。

- 2026-11-20T15:33:46.710884+08:00 Pilot audit passed for training and export. With user authorization the pilot step-20 optimizer checkpoint was removed to free capacity. HF, logs, metrics and copied completion metadata were preserved. Free output bytes: 205636087808.

- 2026-11-20T15:33:46.780426+08:00：启动正式SFT full，PID4487，日志/root/myprojects/R1/R1/.cache/host5-full-20261120-v2/full.log

- 2026-11-20T18:31:23.464789+08:00：full结束，status=failed，exit=1，guard=gpu_management_query_failed

- 2026-11-20T18:31:23.480141+08:00：Training or cold-load did not pass. See assessment.json.

- 2026-11-20T19:32:58.579035+08:00 Restarted the idle lzy container and verified CUDA access. Launched host5-full-20261120-v2 resume1 from complete batch-10 checkpoint. Archived the original 13 metric rows and retained rows 1-10 as the active sequence. Only the failed attempt's disposable optimizer working files were rebuilt. metadata: /root/myprojects/R1/R1/.cache/host5-full-20261120-v2-resume1.

- 2026-11-20T19:32:58.644093+08:00：启动正式SFT full，PID40，日志/root/myprojects/R1/R1/.cache/host5-full-20261120-v2-resume1/full.log

- 2026-11-21T13:06:34.544934+08:00：full结束，status=complete，exit=0，guard=None

- 2026-11-21T13:06:34.550637+08:00：启动正式SFT cold-load，PID25211，日志/root/myprojects/R1/R1/.cache/host5-full-20261120-v2-resume1/cold-load.log

- 2026-11-21T13:07:24.237761+08:00：cold-load结束，status=complete，exit=0，guard=None

- 2026-11-21T13:07:24.245708+08:00：Full training and HF cold-load passed. Held-out evaluation is pending.

- 2026-11-21T14:10:55.219368+08:00 Held-out evaluation complete: 238/331 strict EM, with real Wiki18/E5 retrieval. All generated actions, emitted text and visible evidence are in /root/data/search-r1/sft-runs/host5-full-20261120-v2/holdout-eval-20261121-v1/trajectories.jsonl; both automated counts and targeted manual examples are in /root/data/search-r1/sft-runs/host5-full-20261120-v2/holdout-eval-20261121-v1/trajectory-audit.json.

- 2026-11-21T17:31:41.701067+08:00 A new 331-question four-model comparison is running on host5/lzy. Official published train contains all 331 prior SFT-review questions. The new official-test sample excludes the published train, historical P10000, original SFT teacher questions, and known historical development/evaluation questions with normalized and near-match checks. Sample SHA256 a0d3c6ae8cd89968d283264b5b3a621376040d86e5baa03669f1bf2a63db883a. Models: full step 88, original Qwen2.5-7B Base, official Search-R1 GRPO v0.2 deaa9d14, historical action-stop GRPO step 80. Current driver/status and archived parser diagnostics are under /root/data/search-r1/sft-runs/common-comparison-20261121-v1. The same runtime executes one unique complete tagged tool action and counts format deviations separately.

- 2026-11-21T19:14:01.409511+08:00 Four-model same-questions evaluation complete on host5/lzy (sft-full 132/331; qwen25-7b-base 82/331; official-grpo-v02 147/331; historical-grpo-ckpt80 152/331). Common holdout excludes the entire official published train, historical P10000, and raw SFT teacher pool by normalized/near-match screening. Official v0.2 deaa9d14b92dd4d481414e77b9f733c934df830a; historical GRPO quality action-stop step 80; verified Qwen2.5-7B Base; final SFT step 88. Deployments share Wiki18/E5 exact top-3 and the same decoding limits. Tagged search-only actions are executed and missing think tags are counted separately; earlier incompatible diagnostic preserved. Results: /root/data/search-r1/sft-runs/common-comparison-20261121-v1/comparison.json, /root/data/search-r1/sft-runs/common-comparison-20261121-v1/trajectory-comparison.json, and per-model trajectories.jsonl.
