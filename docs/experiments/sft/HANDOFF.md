# 当前状态与接手说明

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
| CPU验证 | 26项通过，4.47s | 历史实现记录及sft_validation_20261117.json |
| 双卡小模型 | ZeRO-3/FP16/SDPA/CPUAdam通过，恢复与连续参数差0；HF冷加载通过 | .cache/sft-validation-20261117/comparison.json及v4日志；仅20,768参数 |
| 7B Base | 正在下载；当前状态以status.json为准 | 见下节，完成全部11文件SHA后更新本行 |
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
- 当前下载命令：`.cache/sft-smoke-env/bin/python -m search_sft.download_base --endpoint https://hf-mirror.com --job-dir .cache/sft-base-download-20261118`。
- 直连HF曾连接超时；镜像可达，LFS分片摘要和7个小文件已与历史记录匹配。权重下载中；不要仅凭目录存在判定完成。
- status有pid；先用ps与命令行确认是否仍活着。活着先观察.incomplete文件字节，不重复启动；已退出或失败才用同命令恢复。公开模型不需要私人HF token。
- 下载过程没有加载7B或启动训练。后续只有全部11个核心文件本地SHA匹配，才将资产状态改为ready。

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

1. 检查下载进程与状态，完成Base本地SHA校验；同步本状态表。
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
