# Search-R1 实验资产下载

资产根目录：`/root/data/search-r1/`，位于独立数据卷。实验初始模型按原项目根目录默认设置采用 Qwen2.5-3B Base。仓库来源为 Hugging Face 官方仓库，固定 revision，下载文件清单写入资产根目录的 `asset-manifest.json`。

| 资产 | 来源 | 本地目录 |
| --- | --- | --- |
| 生成模型 | Qwen/Qwen2.5-3B | models/Qwen2.5-3B |
| 检索编码器 | intfloat/e5-base-v2 | models/e5-base-v2 |
| 问答数据 | PeterJinGo/nq_hotpotqa_train | datasets/nq_hotpotqa_train |
| 检索索引分片 | PeterJinGo/wiki-18-e5-index | retrieval/wiki18 |
| Wikipedia 语料 | PeterJinGo/wiki-18-corpus | retrieval/wiki18 |

下载脚本为 `scripts/assets/download_search_r1.py`。脚本仅下载必要的 PyTorch/safetensors 和 tokenizer 文件，不下载 E5 的 ONNX/OpenVINO 变体或重复的 pytorch_model.bin。

```bash
.envs/searchr1/bin/python -u scripts/assets/download_search_r1.py \
  --root /root/data/search-r1
```

脚本设置自己的 HF 缓存及临时目录，无须修改系统环境。小文件使用 Hub 的续传机制；大文件使用镜像直连的并发 HTTP Range 请求，逐段检查 Content-Range、大小，并在拼接后验证官方 SHA-256。镜像仅提供传输，固定 revision 和上游校验值仍来自官方 API。校验文件大小和上游提供的 SHA-256；无上游 SHA-256 的小文件记录本地哈希。并发锁防止同一目录同时运行两个下载任务。

下载约 76.73 GB（十进制）。下载后将 part_aa、part_ab 合并成 `retrieval/wiki18/e5_Flat.index`，解压并取出内部 tar 成员，得到真正的 `retrieval/wiki18/wiki-18.jsonl`。保留原下载文件供校验和迁移，因此必须预留索引副本及解压空间。

进度和结果：

- `/root/data/search-r1/runs/download-assets.log`：本轮下载日志。
- `/root/data/search-r1/runs/asset-download/status.json`：文件状态与最终完成状态。
- `/root/data/search-r1/asset-manifest.json`：上游版本、大小及校验值。

仅当 status 中 phase 为 complete，才表示所有下载、校验、索引合并和解压完成。元数据加载成功不代表完整 GPU 训练已通过；模型前向、检索服务和训练的验证属于后续步骤。


本轮使用独立进程会话（start_new_session）后台执行，进程号保存在 `runs/asset-download/download.pid`。后续可查看状态文件和日志；若任务失败，修复原因后重新执行同一命令，会接续未完成分段。不要同时启动第二个下载进程。

全部文件下载后，脚本还会离线读取两个模型的 config/tokenizer、检查 safetensors 索引，统计 train/test parquet 的实际行数及来源分布，并检查语料样例。结果写入 `/root/data/search-r1/asset-validation.json`，最终 phase=complete 才代表这些验证已完成。完整 GPU 推理和检索服务启动不在本次下载验证范围内。


实际发现上游 `wiki-18.jsonl.gz` 是 gzip 压缩的 tar 容器，不能仅 gzip 解压后当作 JSONL 使用。下载流程已增加格式识别，只读取其中唯一的普通 JSONL 文件，并写入固定目标路径，不按归档内部路径展开。原始下载文件保留。

如果已经完成文件下载与索引合并，但此前仅完成 gzip 解压，可以运行以下命令完成归档处理和验证，无需重新下载：

```bash
.envs/searchr1/bin/python scripts/assets/finalize_search_r1.py   --root /root/data/search-r1
```
