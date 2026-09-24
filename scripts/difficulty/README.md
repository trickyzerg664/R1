# 目标设备迁移脚本

[`migrate_target.sh`](migrate_target.sh) 在目标设备上直接从 Git 仓库取得 `data-difficulty` 分支，重建训练与检索环境，下载并校验固定版本资产，生成临时烟测输入，并运行环境检查和 18 项 CPU 测试。**目标设备不需要连接本机或配置本机 SSH。**脚本不会自动启动检索服务、评分或训练。

## 运行条件

目标设备需要 Linux/x86_64、NVIDIA 驱动，以及 `git`、`curl`、`python3`（含 `venv`）、`tar` 和 `nvidia-smi`。还需能通过 HTTPS 访问 GitHub、依赖源和资产下载源。缺少 `uv` 时脚本会在目标代码目录下创建独立引导环境。选择容量充足的数据卷；资产下载器会检查下载、索引拼接和语料解包的空间。完整检索服务曾在本机占用约 62 GiB 内存。

建议在 `tmux` 会话中运行，以免长时间下载因终端断开而中止。使用前确认 `data-difficulty` 分支包含该脚本；若下面的 `curl` 返回 404，检查脚本所在提交是否已经推送。

## 在目标设备运行

```bash
# 首次只下载引导脚本；后续代码由脚本从 Git 仓库克隆。
curl -fL https://raw.githubusercontent.com/trickyzerg664/R1/data-difficulty/scripts/difficulty/migrate_target.sh \
  -o /tmp/r1-migrate-target.sh

# 核对路径和步骤，不连接网络或写入目录。
bash /tmp/r1-migrate-target.sh \
  --repo /work/R1 --data-root /data/search-r1 --dry-run

# 正式执行。首次 /work/R1 应不存在或为空。
bash /tmp/r1-migrate-target.sh \
  --repo /work/R1 --data-root /data/search-r1
```

| 参数 | 必填 | 含义 |
| --- | --- | --- |
| `--repo /path/to/R1` | 是 | 目标机代码目录，首次须为空 |
| `--data-root /path/to/search-r1` | 是 | 模型、数据、索引、缓存和运行日志所在数据卷目录 |
| `--repo-url HTTPS_URL` | 否 | Git 仓库地址；默认 `https://github.com/trickyzerg664/R1.git` |
| `--branch NAME` | 否 | Git 分支；默认 `data-difficulty` |
| `--expected-commit 40位SHA` | 否 | 要求克隆或更新后的 HEAD 与指定提交完全一致，防止分支移动后运行不同代码 |
| `--refresh-code` | 否 | 目标目录已有仓库时，从远端只做快进更新；工作树有修改时拒绝更新 |
| `--dry-run` | 否 | 只展示参数与计划，不创建文件、不联网 |
| `--help` | 否 | 显示脚本用法 |

GPU 型号、卡数和显存占用参数不写入迁移脚本。后续实验通过 `SEARCH_R1_N_GPUS` 及目标机配置指定；方案仍使用每题四条轨迹、最多 10 轮。

## 运行结果与接续

每次运行都会在 `<data-root>/runs/migration-<UTC时间>-<pid>/` 保存 `bootstrap.log`、`events.tsv`、实际 `git-head.txt` 和 `git-status.txt`。只有 `events.tsv` 最后一条为 `COMPLETE`，才表示代码、环境、资产与静态检查都完成。失败时查看 `FAILED stage=... exit=...`，修复后用同样参数重跑；完整资产会跳过重复下载。重复运行默认保留目标机现有提交，只有加 `--refresh-code` 才从仓库快进。

脚本会从下载的原始训练 split 生成 `runs/smoke-input/{score,train,dev}.parquet` 和 `sample-manifest.json`，供目标机完成两题评分及少量训练验证。这些切片**不是正式 P/D/T**；正式实验前仍需独立冻结题池。准备完成后的检索启动、四轨迹评分、更新、完整 checkpoint 和恢复步骤见[迁移与烟测计划](../../docs/experiments/data_difficulty_migration.md)，结果按[进度台账](../../docs/experiments/data_difficulty_progress.md)登记。
