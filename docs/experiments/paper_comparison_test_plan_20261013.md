# 论文对比测试集方案（2026-10-13）

主对比采用论文七项划分：nq/test 3610、hotpotqa/dev 7405、triviaqa/test 11313、popqa/test 14267、2wikimultihopqa/dev 12576、musique/dev 2417、bamboogle/test 125。前两项报告同领域未训练题；后五项报告本次未用于训练的数据集泛化，不以数据集名称不同保证题目不重复。

当前quality-v1从原始Qwen2.5-7B初始化，实际训练文件P.parquet共10000题（NQ4668、Hotpot5332）。本次将论文同领域11015评测题与整个P题池比对，精确/归一化重复0；7道词集合Jaccard>=.9的近重复候选保守剔除。D256与P归一化重复0，但D256源于原始train划出且反复用于开发，应排除在正式最终测试之外。D/D256与官方11015评测题归一化重复0。原始169615题source_train与评测有3个归一化重复，不属于当前P，不能称为当前模型已训练样本。

已生成两个静态测试文件及审计：/mnt/public/code/lyk/lzy/data/runs/paper-comparison-clean-20261013-v1/，实际数量以leakage-audit.json为准。其他五项尚未下载/逐题去重，不宣称已无泄漏。后续对所有候选执行source+split+id、标准化问题、近重复人工复核，排除整个RL候选池、额外SFT样本及开发调参题；冻结保留/剔除ID、理由、哈希。不去除正常答错题，也不依据模型得分选择测试题。

清洗后的集合与论文全量不完全相同。严格公平的模型对比应将本模型、原始Base和作者7B-Base-GRPO检查点在同一清洗测试集重跑；论文原始数字仅作参照，七项平均等权，同时报告逐项EM、题数、未作答和成本。使用相同wiki18/E5/top3及同一评分程序；论文预算4动作/500生成/500观察与本项目10轮/256生成等差异应另做协议对齐评价，不能悄然混用。

固定测试集只在冻结方案与检查点后评价；D256用于开发，不根据最终测试分数反复调奖励、筛选或选择检查点。清洗只覆盖公开的本次微调数据，词集合规则不能穷尽语义改写。后续若改变模型初始化或使用新SFT数据必须重新查重。

本次仅离线数据审计与Parquet准备，没有启动GPU模型生成或训练，没有修改训练源码/配置。七项论文划分来源：https://github.com/PeterGriffinJin/Search-R1/blob/main/scripts/data_process/qa_search_test_merge.py 与 https://huggingface.co/datasets/RUC-NLPIR/FlashRAG_datasets 。


## 官方公开权重核验与对照建议（2026-10-14）

已在线核验作者GitHub及HuggingFace：原Search-R1系列v0.2公开Qwen2.5-7B Base/GRPO完整推理权重，主对照候选 PeterJinGo/SearchR1-nq_hotpotqa_train-qwen2.5-7b-em-grpo-v0.2；另有同Base/PPO版本。HF文件目录包括7个safetensors分片、权重索引、配置和tokenizer，总体约30.5GB。文件存在不证明与论文表格某行的精确最终保存步完全一致；冻结对照前记录公开仓库revision。

主对照建议：原始Qwen2.5-7B、官方7B Base GRPO v0.2、本次预先固定的最终checkpoint。v0.3官方7B Base GRPO对应第二篇实证论文系列、结果+格式奖励，可作为额外对照但需区分版本。不要将7B-Instruct检查点混入Base主对照。

同一测试题、同一wiki18/E5/top3检索、提示与执行协议、生成/观察token预算、最大动作轮数、采样及答案抽取/EM程序统一；输出终止策略也统一。比较答案EM、协议异常/缺答案/重复、检索次数和生成耗时。模型权重可比较最终能力，不能仅靠训练数据/步数不同的现成模型证明动态筛选策略的独立收益。

已有11,008题仅针对本次P池清洗（NQ3603+Hotpot7405）；正式双方未训练测试还须用官方公开训练池联合排重，并排除本次D/D256开发题。此前原始source_train与官方评测有3个归一化重复、未落入本次P，联合过滤后的最终数量尚未核验，不能直接宣称11,008题双方均未训练。其余5项评测也须联合排重后冻结。预训练是否见过网页无法由这次RL题目查重完全证明。

来源：https://github.com/PeterGriffinJin/Search-R1/blob/main/docs/experiment_log.md
https://huggingface.co/collections/PeterJinGo/search-r1-v02
https://huggingface.co/PeterJinGo/SearchR1-nq_hotpotqa_train-qwen2.5-7b-em-grpo-v0.2/tree/main
https://huggingface.co/collections/PeterJinGo/search-r1-v03

本次仅核验公开资源及对照方案，未下载权重、未启动模型评价、未修改训练或正式冻结评测配置。


## 固定128题正式测试子集准备（2026-10-13T16:48:19.173298+00:00）

用户要求按1小时预算直接抽题，并明确不做小测试、不做任何显卡验证。CPU数据准备完成：NQ test42题、HotpotQA dev86题；固定种子20261014，SHA256稳定随机排序及来源比例配额。产物/mnt/public/code/lyk/lzy/data/runs/paper-comparison-sampled-128-20261014-v1/test128.parquet，哈希8d6414f06366a0eb451f6828987db99ad1c6a1aa14b603813bdee21934f396a2。原始问题/提示/答案/split不变；题目身份和输入哈希见sample-manifest.json、sample-ids.jsonl。与官方公开169615题源train、本次P10000、D1000和D256联合执行归一化及词集合Jaccard>=.9近重复排除，本次抽样顺序中额外剔除2道NQ近重复题并补齐。规则未穷尽语义改写或预训练污染。

同一模型每题1条完整轨迹，不使用G8或动态筛选；旧D256实测24.9–46.0分钟，128题线性外推12.4–23.0分钟，加载/波动后预算30–50分钟，未对新子集实际测时，不能保证任何模型/推理配置都小于1小时。三模型分别计时，1小时预算按单模型运行计。仅生成数据，未启动或预约评价，当前训练配置与数据不变。128题总体正确率统计误差较大，约±9个百分点（95%最保守近似），适合快速比较，不能等同论文全量结果。

实际命令：ionice -c 3 nice -n 19 /mnt/public/code/lyk/lzy/envs/vllm-metax-clean33/bin/python /mnt/public/code/lyk/lzy/maintenance/action-stop-20261013/sample_test_subset.py。退出0；CPU Parquet复读验收128行、来源配额、标签和原始行一致、身份唯一、归一化训练/开发重叠0。未做模型/GPU验证。


# 官方Search-R1 v0.2对照模型下载：official-search-r1-v02-download-20261014-v1

状态：downloading，检查UTC 2026-10-13T16:56:07.494913+00:00。用户明确要求服务器缺失时先下载GRPO v0.2和PPO v0.2，未授权启动推理评价。常用共享模型目录及本项目缓存/数据目录按SearchR1名称检索未找到对应现有资产。

两模型固定revision及目标目录：[{"repo": "PeterJinGo/SearchR1-nq_hotpotqa_train-qwen2.5-7b-em-grpo-v0.2", "revision": "deaa9d14b92dd4d481414e77b9f733c934df830a", "path": "/mnt/public/code/lyk/lzy/models/official-search-r1-v02/SearchR1-nq_hotpotqa_train-qwen2.5-7b-em-grpo-v0.2"}, {"repo": "PeterJinGo/SearchR1-nq_hotpotqa_train-qwen2.5-7b-em-ppo-v0.2", "revision": "053b6e1addc3affc5bf7e920b654b8ac9610c7ba", "path": "/mnt/public/code/lyk/lzy/models/official-search-r1-v02/SearchR1-nq_hotpotqa_train-qwen2.5-7b-em-ppo-v0.2"}]。官方文件元信息由本机直连huggingface.co/api/models?blobs=true取得，保存official-grpo-v02-metadata.json与official-ppo-v02-metadata.json，随脚本传至mx。mx直连官方域名失败，hf-mirror.com可达，镜像仅传输固定版本文件；权重LFS SHA256及小文件Git blob SHA1与官方元信息核验，再保存统一SHA256。文件总量60956824616字节。单卡推理、模型加载和GPU验证均未执行。

启动命令：ionice -c 3 /mnt/public/code/lyk/lzy/envs/vllm-metax-clean33/bin/python -u /mnt/public/code/lyk/lzy/maintenance/official-search-r1-v02-download/download_official_models.py；Python内部nice19，2并行下载，持久化.incomplete续传，每文件最多12次重试，不删除已有文件。进程PID854930，stdin=/dev/null，stdout/stderr=/mnt/public/code/lyk/lzy/maintenance/official-search-r1-v02-download/download.log，start_new_session=True，PPID1、SID=PID，关闭本机Codex/SSH不影响下载。独占download.lock禁止重复下载。

证据：/mnt/public/code/lyk/lzy/maintenance/official-search-r1-v02-download/status.json、download-manifest.json、launcher.json、download.log。每模型目标目录COMPLETE.json只在全部文件内容校验和权重索引引用完整后生成。仅此标记与phase=complete可称下载就绪。当前开始传输、尚未全部下载完成；不把启动标为成功下载。

不修改当前训练、检索、上传进程或训练配置。下载准备只消费CPU/磁盘/网络。脚本py_compile通过，真实小文件下载及Git blob校验已通过；大权重下载及校验仍执行中。未运行额外单元测试或显卡验证。

下一步：继续核验远端进度及文件哈希，完成后记录两个可加载资产目录；按用户最新指令，本次不启动任何模型推理或小测试。


2026-10-14T01:38:59.745277+00:00 用户询问不重启临时改为3–7主筛及收益：核验实际dynamic_filter.py、controller.py，3–6为已导入Python函数中的固定判断，资格模式初始化后保存，当前无在线配置重读/步边界切换接口；直接修改磁盘源文件或YAML不会让当前已加载进程安全生效。保持当前训练未改，不采用调试注入或运行时monkeypatch。现有7/8备用仅每16轮边界集中接纳；过16轮的新7组等待下一边界导致额外生成。按61–68步原候选记录离线单步重放（固定实际前一步权重与已训排除集合推导）3–7立即接纳，原平均20.625轮可降至19.125轮，估计平均少2.359分钟/步；67步28→22轮约少9.16分钟，61和68步不减少，其他步少1–2轮。证据immediate-3-7-offline-replay.json，全部CPU日志统计，无新GPU生成或验证。重放不代表跨步改策略后的权重/选题相同，不外推为未来准确率保证。若采用须在完整checkpoint边界恢复新阶段并显式登记新资格版本/恢复允许变更，仍保留G8、奖励方差、去重、奖励和优化器等条件；用户尚未授权重启，当前不执行。


2026-10-14T09:15:23.844911+00:00 用户授权 ckpt80 后暂停、魔搭上传及 T128 三模型评测；CPU 四项门控测试通过，128 题输入一致，正式 GPU 评测未开始。独立控制器目录：/mnt/public/code/lyk/lzy/maintenance/checkpoint80-test128-20261014
