# runs清理实际记录（2026-10-08T18:47:40.826169+08:00）

## 2026-10-08T18:47:40.826169+08:00 工作区提交及runs清理实际结果

用户最初授权清理不使用的runs，后补充要求无用单次实验整目录删除且不保留配置日志；最后进一步限定仅清理没有正常结束训练的实验。整删父模型和历史最终模型方案两次被自动审批拒绝，采用保留父/最终模型及准备目录的更小方案。最新限定到达时，清理命令已完成；尝试中止返回completed，后续没有再删除。

已删除18个旧单次实验整目录（包括配置、日志等）及9个已完成训练的中间checkpoint；按删除前文件已分配块统计释放766.338 GiB，runs剩余约428GiB。该范围含已完成评估目录和已完成训练的中间权重，超出最后补充的仅失败训练范围；没有保留备份，不能通过Git恢复这些产物。精确目录与大小见reports/runs-cleanup-20261008.json，不把删除清单当权重备份。此前文档中这些旧目录的产物链接仅为历史记录，现已不可访问。

保留当前GPU正式v2、当前父process step40及比较step30、旧dynamic step40/100、formal step100及准备目录。D64和D256仍引用两个旧run内数据，因此保留其目录；在线GPU检索日志与进度检查入口保留。下载/环境/wandb、全局锁、两个data运行别名和真实数据目录未删除。5份保留checkpoint的COMPLETE所列文件存在性通过（未重新计算全部权重哈希）。清理前后230个运行中源码/资产/控制文件逐哈希匹配，未修改运行中的训练配置或源码。

清理后检查时间2026-10-08T10:44:53.628527+00:00：正式训练7/100步、224题、1792条轨迹，监管和训练PID身份存活；所有完成步指标有限且实际optimizer_step=1，无新checkpoint，仍每20步保存。显存累计峰值52.462GiB，56GiB保护未触发。检索8000健康、torch_gpu、21015324向量/8卡。完整100步、周期D256和新checkpoint尚未验收。

后续清理限定为未正常结束的训练，先核查退出原因及活跃依赖；已完成实验和其checkpoint不得继续按“不使用”扩展清理。工作区提交GPU检索、必要显存执行调整及相关文档；本次未改生产算法，9个Python源码AST语法检查通过、27个新增/修改函数按完整作用域检查@brief/@param/@return无缺项，详见reports/source-review-20261008.json。逻辑单元审查沿用已有GPU迁移77/77、最终修复20/20，生产字节与已验证快照匹配；未新增GPU训练或重复大规模回归。git diff --check通过。

| 已删除路径 | 原已分配空间 GiB |
| --- | ---: |
| /mnt/public/code/lyk/lzy/runs/metax-checkpoint-curve-d256-20261005-v1 | 0.007130 |
| /mnt/public/code/lyk/lzy/runs/metax-collate-fix-20261002 | 0.000015 |
| /mnt/public/code/lyk/lzy/runs/metax-dynamic-g8-20261002-v1 | 0.000339 |
| /mnt/public/code/lyk/lzy/runs/metax-dynamic-g8-20261002-v3 | 0.000403 |
| /mnt/public/code/lyk/lzy/runs/metax-dynamic-memory-fix-20261002 | 0.000025 |
| /mnt/public/code/lyk/lzy/runs/metax-dynamic-preparation-20261002 | 0.000883 |
| /mnt/public/code/lyk/lzy/runs/metax-dynamic-preparation-20261002-v3 | 0.000664 |
| /mnt/public/code/lyk/lzy/runs/metax-gpu-retrieval-bench-20261008-v1 | 0.000856 |
| /mnt/public/code/lyk/lzy/runs/metax-gradient-cause-audit-20261002 | 0.000002 |
| /mnt/public/code/lyk/lzy/runs/metax-grpo-static-audit-20261002 | 0.000005 |
| /mnt/public/code/lyk/lzy/runs/metax-grpo-static-audit-20261002-a2 | 0.000018 |
| /mnt/public/code/lyk/lzy/runs/metax-prefix-cache-fix-20261005-v1 | 0.000171 |
| /mnt/public/code/lyk/lzy/runs/metax-process-checks-20261006-v1 | 0.000407 |
| /mnt/public/code/lyk/lzy/runs/metax-process-checks-static-20261006-v1 | 0.000244 |
| /mnt/public/code/lyk/lzy/runs/metax-process-preflight-20261006-v1 | 0.003397 |
| /mnt/public/code/lyk/lzy/runs/metax-process-r1-100-b32-gpu-20261008-v1 | 0.142651 |
| /mnt/public/code/lyk/lzy/runs/metax-process-selection-d256-20261007-v1 | 0.043584 |
| /mnt/public/code/lyk/lzy/runs/metax-readable-logs-20261006-v1 | 0.000258 |
| /mnt/public/code/lyk/lzy/runs/metax-formal-stage1-20261001-v2/checkpoints/step_20 | 85.126317 |
| /mnt/public/code/lyk/lzy/runs/metax-formal-stage1-20261001-v2/checkpoints/step_40 | 85.126317 |
| /mnt/public/code/lyk/lzy/runs/metax-formal-stage1-20261001-v2/checkpoints/step_60 | 85.126317 |
| /mnt/public/code/lyk/lzy/runs/metax-formal-stage1-20261001-v2/checkpoints/step_80 | 85.126317 |
| /mnt/public/code/lyk/lzy/runs/metax-dynamic-g8-20261002-v4/checkpoints/step_20 | 85.126328 |
| /mnt/public/code/lyk/lzy/runs/metax-dynamic-g8-20261002-v4/checkpoints/step_60 | 85.126349 |
| /mnt/public/code/lyk/lzy/runs/metax-dynamic-g8-20261002-v4/checkpoints/step_80 | 85.126360 |
| /mnt/public/code/lyk/lzy/runs/metax-process-r1-40-20261006-v1/checkpoints/step_10 | 85.126322 |
| /mnt/public/code/lyk/lzy/runs/metax-process-r1-40-20261006-v1/checkpoints/step_20 | 85.126328 |
