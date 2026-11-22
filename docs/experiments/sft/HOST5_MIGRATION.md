# host5 迁移交接

记录时间：2026-11-18T22:42:57.899256+08:00。用户要求 docker run 创建 lzy 并拷贝实验所需内容；复制已完成，未启动 host5 真实7B或正式数据训练。

- 容器 lzy，基础镜像 ubuntu:22.04；实际创建命令在宿主机 `/home/luozhenyuan/lzy-r1-20261118/docker-run.sh`，未使用 Compose。
- 项目 `/root/myprojects/R1/R1`，分支 sft；完整 Git、现有环境、Base、SFT raw/draft、检索资产、全部历史资源验证输出（含两份完整 checkpoint 和 HF）已复制。
- 六阶段 tar 两端均 exit0，累计传输 347,234,918,400 字节（包括末次记录增量）。本地审查报告48文件已复制并通过小包哈希核对。
- 用户要求传完即可，已停止剩余逐文件SHA校验；已核对 39,936 项，当前已核对部分不一致数 0。不得写成全量哈希验收通过。
- host3 原文件不移动、不删除；迁移只读源端。获准的GPU1续跑已完成：第一步lr0 warmup，第二步lr5e-6、20,687/40,960采样FP16值变化，保存checkpoint2并保留checkpoint1，导出和独立进程冷加载通过。仅证明单卡Gloo/NVMe候选；不是原双卡方案或长期稳定性证明。
- 未拷贝可重建的中断NVMe工作区、wiki压缩包/下载分片；host3原件仍在。历史正式评价题单/最终数据尚缺属于源端既有状态。

## 进入与环境

```bash
ssh host5
docker exec -it lzy bash
cd /root/myprojects/R1/R1
source scripts/sft/host5_env.sh
```

现有 `.cache/sft-smoke-env` 已可用；Torch2.4.0、Transformers4.47.1、DeepSpeed0.15.4。FP16 CUDA、单rank NCCL、26项CPU测试通过，CPUAdam/AsyncIO编译加载及极小参数更新通过。CPU测试首次因系统distro缺失失败，安装python3-distro后通过；首次扩展探针退出时有DeepSpeed析构顺序警告，更新本身成功、进程exit0。另装procps供交接命令使用。

原 `run_host3.sh` 硬编码两rank，host5仅一张TITAN RTX24GB，不能直接照搬训练命令；需要独立单卡配置(world1/accum32/global32)并做真实7B资源验证后再决定训练。既有host3恢复配置含原GPU UUID、卸载路径和签名，不直接在host5恢复同run。正式pilot/full仍受final数据及评价排重等既有门禁约束。

## 挂载与空间

| host5宿主目录 | 容器目录 |
|---|---|
| /disk2/lzy-r1-20261118/myprojects | /root/myprojects |
| /disk2/lzy-r1-20261118/usr-local | /usr/local |
| /disk2/lzy-r1-20261118/data | /root/data |
| /srv/lzy-r1-20261118/sft-resource-checks | /root/data/search-r1/sft-resource-checks |
| /home/luozhenyuan/lzy-r1-20261118/sft-runs | /root/data/search-r1/sft-runs |
| /srv/lzy-r1-20261118/nvme-work | 项目.cache/real7b-single-gpu1-nvme-20261118-v4/nvme |

最近快照：/disk2剩约19.6GiB，/srv所在SATA SSD剩约63.1GiB，sft-runs所在NVMe剩约205.7GiB。新训练输出使用sft-runs；完整7B NVMe optimizer工作区在当前/srv余量下可能放不下，需另算预算，不宣称该fallback已就绪。

全部迁移清单、日志与检查记录在宿主机 `/home/luozhenyuan/lzy-r1-20261118/migration`；大体积源SHA清单保留于此。未修改host3文档，未commit/push。
