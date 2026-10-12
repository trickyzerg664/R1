# MX 迁移依赖

此目录保存选定训练目录之外、复现和追溯所需的小文件。对应保留实验：

- `metax-grpo-reward-100-20261011-v2`：完成49步，持久检查点20/40。
- `metax-process-r1-100-b32-gpu-20261008-v2`：完成100步，持久检查点20/40/60/80/100。

## 内容

- `data-splits.tar.gz`：冻结P/D/T和manifest、D256及选择记录、D64及选择记录；未压缩合计约7.5 MiB。封存T仅作为字节副本归档，未进行题目分析或评分。
- `dependency-manifest.json`：8个归档文件的原相对路径、大小、SHA256及两次训练冻结manifest的匹配结果。
- `*-packages.txt`、`environment-versions.json`：两个现有MetaX Python环境的版本清单。包名和版本用于重建参考，不是可直接跨GPU安装的通用requirements。
- `gpu-service-config.json`：实际检索启动参数、可用索引/语料/编码器路径和环境配置。
- `resource-manifest.json`：公开模型/数据/检索资源的下载来源、revision和上游哈希；不包含实际公开大文件。
- `SHA256SUMS`：本目录全部交付文件（不含此校验清单自身）的校验值。

未包含模型权重、优化器、公开语料/索引、完整Python环境或账号令牌。模型和相关训练材料须另存上述两个完整run目录。当前源码和`env/metax/run.sh`通过Git保存；原运行源码快照位于各run目录。若存在安装环境内的私有适配修改，其源码还需单独保存，包版本清单不能代替源码。

## 校验和恢复

```bash
cd migration/dependencies
sha256sum -c SHA256SUMS
# NEW_BASE换成新机器共同工作根，解压得到data/runs和最小runs依赖目录。
mkdir -p "$NEW_BASE"
tar -xzf data-splits.tar.gz -C "$NEW_BASE"
```

恢复后更新训练配置和检索配置中的旧绝对路径；在新机器重新下载指定公开资源、安装兼容环境并验收。此目录不包含旧process-step40父模型；按用户选择排除该模型后，无法原样从它重跑两次训练的起点。已保存检查点可用于模型评价或新训练起点，严格续训仍需核验原恢复规则、源码版本和GPU拓扑。

## 本次验证

检查8个归档成员的SHA256与源文件一致，并匹配两次训练manifest中引用的6条记录；导出版本和JSON解析成功，检查配置未发现凭据字段。无生产源码修改、训练/评分/GPU操作或模型上传。源码注释覆盖率不适用。
