# 单次实验记录：metax-qwen7b-quality-100-20261012-v1

## 当前状态

负责人/root；准备阶段，训练0/100、已保存checkpoint0。旧scoremask-v2已停止12步、无checkpoint；本次不恢复其优化器。CPU、历史重放、模型与来源冻结待完成；尚未启动GPU。

## 可复现信息

分支data-difficulty-muxi，新规则提交07c59d5。初始actor和固定reference均为/mnt/public/model/huggingface/Qwen2.5-7B，优化器/调度器/scaler从零开始。新资格answer_correct_3_6_v1，重复repetition_v1及质量成功task_success_quality_v1。其余参数沿用旧运行：lr1e-6、warmup10后常数、KL.001、熵.001、seed42、32题×8轨迹、8GPU、mini128/micro8、clip.2、gradclip1、response256、max10轮+final、temperature1、top_p.95、max16补抽、bounded_invalid_v1、过程成本封顶.12。

mx八张MetaX C500，FP16/FSDP/vLLM；数据/固定D256/prompt/检索及环境版本沿用旧冻结配置，具体资产哈希和解析配置在本次manifest/plan中。检索PID2137145为独立服务，保持ready。

## 运行位置及恢复

产物根：/mnt/public/code/lyk/lzy/runs/metax-qwen7b-quality-100-20261012-v1。训练日志train/console.log、metrics.jsonl、process-audit.jsonl、trajectories.readable.log；状态status.json。监督器独立PID及启动ticks在launcher-process.json，训练子进程train/process.json。初始D256使用原始Qwen完整原生轨迹在新奖励配置下CPU重放，原EM独立保留；训练100步，每20步存checkpoint并固定验证，最后独立D256。当前可恢复checkpoint无；未来只能按本次新指纹恢复完整checkpoint。

启动命令（验收后执行）：bash env/metax/run.sh -u scripts/difficulty/stability_trial.py --run-directory /mnt/public/code/lyk/lzy/runs/metax-qwen7b-quality-100-20261012-v1 --launch。工作目录/mnt/public/code/lyk/lzy/R1-vllm-metax。

## 阶段进度与证据

准备：旧实验精准停止12步、检索保留；独立工作树7232ea6合入原分支为07c59d5，运行记录单独提交b450214。Git身份缺省首次提交失败，沿用历史Codex进程级身份后成功；进度文档冲突保留原分支全文并追加工作树验证历史，其余源码与已测工作树逐字相同。migration依赖提交e3544d4保留。

## 验证及结果

此前工作树CPU272项270通过、2GPU跳过，真实tokenizer256初始/3072候选已回放；证据quality-code-verification-20261012。此次合入后CPU与正式RewardManager初始256题重放待执行；不把历史CPU结果冒充本次GPU训练结果。新筛选改变候选分布，新奖励改变目标，无法单因素归因；轻度重复存在正常实体复述的软罚边界，详见quality_controls.md。

## 失败、变更与交接历史

原日志与旧manifest保留，本次不覆盖；代码/配置快照/哈希将绑定本次独立run。冻结、启动、首轮候选和实际训练步数分别记录。下一步CPU/重放通过、模型资产与新指纹验收、Git文档提交后冻结并启动。

2026-10-12T13:44:39.545677+00:00 合入后CPU272项270通过/2GPU跳过；正式RewardManager+真实tokenizer重放256唯一题/918轮，原EM84.0/256、缺提取8，训练候选新奖励改变7条，独立新公式/token/文本/人工梯度掩码/原EM参照错配均0，模型生成和更新0。证据cpu-regression.log、historical-rescore.log/json。进入模型资产与新指纹冻结验收。

资产与配置验收开始；CPU全量回归通过，训练0步，原始Qwen模型进行完整文件哈希与safetensors头部验证。

冻结验收通过：{"checked_utc": "2026-10-12T13:45:31.170237+00:00", "run": "/mnt/public/code/lyk/lzy/runs/metax-qwen7b-quality-100-20261012-v1", "model": "/mnt/public/model/huggingface/Qwen2.5-7B", "sources": 298, "assets": 16, "config_differences": 9, "identity": {"initial_model_id": "7c3269c21a61915411e593401dbe335b9c427a02702067f986bce261e592a76e", "reference_id": "7c3269c21a61915411e593401dbe335b9c427a02702067f986bce261e592a76e", "retrieval_id": "wiki18-e5-metax-gpu-fp32-shard8-20261008-v1", "seed": 42, "training": "0920d9cfc59c260a5b8fe798211f75dc53b0f04eecf518e91257fb6e3b5c9753", "versions": {"torch": "2.6.0+metax3.3.0.2", "transformers": "4.57.1", "vllm": "0.11.0+empty"}, "world_size": 8}, "cpu_verified": true, "gpu_started": false, "free_bytes": 2970972892160}。下一步按用户授权验收复用初始D256→100步训练→最终D256。初始化与旧Qwen运行相同；初始评价复用完整原生token的CPU重评分，训练从0开始。

2026-10-12T13:46:56.977915+00:00 按用户授权实际启动：{"pid": 3464301, "proc_start_ticks": "1013664962", "started_utc": "2026-10-12T13:46:56.977915+00:00", "argv": ["bash", "env/metax/run.sh", "-u", "scripts/difficulty/stability_trial.py", "--run-directory", "/mnt/public/code/lyk/lzy/runs/metax-qwen7b-quality-100-20261012-v1", "--launch"]}。原分支功能07c59d5、文档b7e9e2e，冻结298源码/16资产；初始Qwen7B与reference相同，新训练指纹0920d9cf，配置差异仅新资格/重复开关与7输出路径。复用完整原生初始D256CPU新评分84/256，随后100步新训练。此时仅确认监督进程创建，训练0/100，worker生成/首步更新待实查。


<!-- metax-qwen7b-quality-100-20261012-v1-current -->

{
  "status": "failed",
  "phase": "stopped",
  "error": "Training did not reach target 100",
  "wall_clock_limit_disabled": true,
  "deadline": null,
  "supervisor_pid": 150230,
  "checked_utc": "2026-10-13T07:23:14.491250+00:00"
}

<!-- /metax-qwen7b-quality-100-20261012-v1-current -->

2026-10-12T13:56:19.274107+00:00 八卡实际首批验收（/root）：launcher/child启动身份有效，8个worker；实际模型/训练指纹与预检一致，298源码/16资产冻结复核通过，检索ready，无OOM/Traceback/ActorDied/非有限错误。首批256候选/925轮已完成真实生成评分；正常231、轻度17、重度8，重度均无正奖、质量成功false。32问题仅8组资格正确次数3–6、完整G8保留，新奖励与returned_reward逐行一致，实际可保留重度正优势0。当前正在首步补抽，完成训练0/100、checkpoint=[]；不把候选step1当成完成更新，尚未首步实际反传验收。证据startup-inspection.json、train/run.json、metrics/process-audit/console日志。

启动检查字段名复核：只读startup_check.py原采样/文本前缀字段使用单数拼写，已改为生产sampled_prefix_matches/text_prefix_matches并要求布尔字段齐全；真实925轮重验错配0。该派生检查错误不影响训练源、概率或奖励；CPU/GPU结果边界维持，首步反传待完成。


2026-10-12T15:22:27.012475+00:00 /root 生成证据与交互协议改进设计：见[evidence_protocol_quality_plan_20261012.md](../evidence_protocol_quality_plan_20261012.md)。仅代码/日志核对与设计文档，未改源码、配置、采样、奖励或模型，未启停训练，未跑验收测试；代码注释覆盖不适用。顺序为固定诊断、协议/停止边界、小规模SFT对照、语义判定校准后奖励、独立消融。最新状态仅代表该检查时刻：{"status": "running", "phase": "train", "trained_step": 5, "published_checkpoint_steps": [], "checked_utc": "2026-10-12T15:22:12.140382+00:00"}。前四步候选5120条EM18.98%、未作答13.22%；训练批次质量成功48.34%、未作答8.59%、重度2.05%、轻度6.15%，口径不同且筛选存在偏差。收益全部待验证。


2026-10-12T15:42:04.043042+00:00 /root 异常轨迹展示核对：首六步训练批次重度27/1536=1.76%，第6步1/256=0.39%；样例均来自train_candidates，不据此声称具体样例已入选训练。8651d6796d4d4752b8e6cb4fddf2cefc:131（step6，美国个人收入）第2轮实际consumed含124行olland，原tokenizer+现有inspect_turn离线重算body_tokens256、repeated_ratio.95703125、severe；第2-10轮持续类似输出、tail均空，第11轮无answer标签，未接受答案、规则奖励-.12。68e0cb9d3a3742e199418026c1aec3cd:12（step4，双面人演员）实际消费文本模拟其他用户对话并转向Frobenius矩阵范数，第4-10轮长段复述，未作答、-.12；跨轮复述与当前单轮重复统计分开解释。dee2c04ca20c493b8f9559c9baf77f11:255（step5，圈R）真实执行query和HTTP检索，最终模板1答复、-.02。:8同组演员题已见Aaron Eckhart证据仍答Geoffrey Rush，reward0。样例由readable元数据关联process-audit完整消费事件核实，未执行tail不作执行内容；没有新模型生成/参数更新或GPU测试，无源码/配置变更，注释覆盖不适用。最新状态：{"status": "running", "phase": "train", "trained_step": 6, "published_checkpoint_steps": [], "checked_utc": "2026-10-12T15:41:43.269558+00:00"}。


2026-10-12T16:18:59.181531+00:00 /root 用户质疑3–6动态筛选实查：前8步1152候选组、279满足资格，按生产顺序和每步上限32重建最终256组/2048条；全部组answer_correct_k介于3–6，逐组原始可读8条复算错误0；各步原EM直方图及正奖励条数与实际训练指标全部一致。第8步3/4/5/6正确组分别10/10/8/4。当前可读文件仅train_candidates标头，不另记最终入选视图；整组保留含失败轨迹，difficulty/k为original_em而非筛选用的协议门控accepted_em，可能有k7/k8，不代表筛选失效。新增静态派生视图/mnt/public/code/lyk/lzy/runs/metax-qwen7b-quality-100-20261012-v1/analysis/selected-step1-8.readable.log及analysis/dynamic-filter-step1-8-verification.json，不热改源码/配置/训练。标签是EM规则正确，长正确句可能不满足exact match，未人工复核所有标准答案。无GPU测试/新生成，源码注释覆盖不适用。


2026-10-12T16:27:52.398273+00:00 /root 用户请求训练及上传进度：quality-v1检查时状态{"status": "running", "phase": "train", "trained_step": 9, "published_checkpoint_steps": [], "checked_utc": "2026-10-12T16:26:52.789749+00:00"}；检查时第10步候选日志round2保留25/32，训练进程3464339存在，无优化器跳过；最新训练批次质量成功.578125、重度重复.0078125、未作答.0625，不当作固定验证结果。魔搭trickyzerg/R1-mx两组历史实验归档于2026-10-13北京时间00:09:56完成，327文件/652222036014字节；verification errors=[]、unavailable_hash_metadata=[]，最终提交日志成功，上传进程已退出。completed状态不再叠加残留progress.uploaded_bytes，避免重复统计；本次两组归档未含当前quality-v1训练。仅进度读取及文档同步，未改源码、参数、模型或启停进程，未运行测试，注释覆盖不适用。


2026-10-13T03:21:32.549265+00:00 /root 用户请求当前进度：{"status": "running", "phase": "train", "trained_step": 37, "published_checkpoint_steps": [20], "checked_utc": "2026-10-13T03:21:07.053543+00:00"}。北京时间11:20实查训练37/100，已发布step20；第38步候选round2保留3/32。第20步固定验证256题，NQ .43333333333333335、HotpotQA .45588235294117646，来自metrics.jsonl正式train step20字段；未与筛选训练成功率混用。第37步2243.48秒，16轮候选补抽，最近五步1563.40/1569.68/2008.10/1521.38/2243.48秒；筛选耗时增大。最新训练批次质量成功.59375，重度重复/缺答案均0，无优化器跳过，只代表该批次。上传仍completed，327文件652222036014字节、校验errors=[]，不含quality-v1当前实验。仅只读检查及文档记录，未改源码/配置/模型或启停任务，未跑测试，注释覆盖不适用。


2026-10-13T03:49:59.059216+00:00 /root 论文测试集设计与训练泄漏审计：见paper_comparison_test_plan_20261013.md；当前P10000与论文同领域11015无精确/归一化重复，但7道近重复保守剔除；生成冻结Parquet/剔除清单/哈希至/mnt/public/code/lyk/lzy/data/runs/paper-comparison-clean-20261013-v1，保留数量{"nq": 3603, "hotpotqa": 7405}。其余五项待获取和逐题去重，不宣称已无泄漏。未跑模型/更新参数，无源码变化，注释覆盖不适用；当前运行不改数据或预算。


2026-10-13T03:57:38.630652+00:00 /root 用户再次确认11008题训练隔离：{"checked_utc": "2026-10-13T03:57:38.630652+00:00", "run": "metax-qwen7b-quality-100-20261012-v1", "train_files_config_lines": ["train_files: /mnt/public/code/lyk/lzy/data/runs/formal-pdt-7b8-v1/P.parquet"], "pool_rows": 10000, "pool_hash_matches_audit": true, "checks": [{"source": "nq", "rows": 3603, "normalized_overlap_with_P": 0, "sha256_matches_saved_audit": true}, {"source": "hotpotqa", "rows": 7405, "normalized_overlap_with_P": 0, "sha256_matches_saved_audit": true}], "near_duplicate_candidates_removed": 7, "near_duplicate_rule": "word-set Jaccard >= .9; at least five distinct words; conservatively removed; not exhaustive semantic deduplication"}。结论仅针对当前quality-v1实际P训练池与已保存审计；近重复规则不保证穷尽语义改写，不推广到其他历史训练/SFT或模型预训练。没有模型生成/参数更新，无源码变更，注释覆盖不适用。


2026-10-13T04:18:27.527629+00:00 /root 当前质量/奖励审计与授权同步：见health_quality_reward_20261013.md。step36–38完整10496候选/768入选，重度0、轻度1、未作答3；奖励公式不一致0，真实GRPO函数CPU重放333失败正优势0。入选97条冗余检索候选、其中51正优势，实际代表44f097c5bdfd4022a6c79ba3f2222e1e:49 reward1/adv+1.2076124；早期严重重复正确Dirca取消正奖返回-.12。语义幻觉未全量人工审查，未执行information尾部不算执行/训练内容。训练检查38/100、step20完整；预测10月14日19:20–21:00参数更新完成，监督器实际46h截止19:46:56，有提前停止风险，未调整。用户授权向同账号私有trickyzerg/R1-mx同步，独立低优先级后台PID123371，完整step20+日志快照98.3GB，已传9.79GB、未整批提交/验收；新完整checkpoint、小时日志及终态自动同步。仅维护独立上传辅助和审计产物，无训练源码/参数/模型变化，没有新GPU验收；数据审计CPU重放结果不冒充GPU更新，源码注释覆盖不适用。


2026-10-13T04:28:29.719923+00:00 /root 用户明确取消监督时限，已完成：独立辅助maintenance/quality-v1-supervision-unlimited/supervise_quality_unlimited.py先编译/4项CPU身份检查与冻结预检通过，ready后接管旧父监督3464301（启动ticks1013664962）。仅结束父监督本身，未停止/重启原训练3464339，启动ticks1013665154不变；新监督150230持有独占训练锁，status wall_clock_limit_disabled=true/deadline=null，GPU<=56GiB、有限数值、两mini更新及微批覆盖、100步完整checkpoint验收保留，最终评价复用原run_phase(deadline=inf)。原冻结源码/plan/训练配置/优化器未热修改；supervision-override.json记录授权，previous-supervisor.json保存原身份。12:26确认训练39/100、step20检查点、检索2137145与上传123371正常。新估计10月14日19:30–21:20参数更新结束，验证/保存另计；魔搭已传30.50/98.33GB，未整批提交/验收。辅助代码位于maintenance而非冻结生产源码；本次CPU控制预检通过，未重新GPU训练，不以预检替代完整训练验收。详见health_quality_reward_20261013.md。


2026-10-13T04:45:16.301283+00:00 /root 核验论文与当前实验测试rollout口径：作者公开_validate检索分支不重复n_agent，do_sample=False，vLLM覆盖temperature=0/n=1/best_of=1；当前冻结验证/最终评价复用相同口径，每题一条完整多轮检索轨迹。训练论文GRPO每题5条，当前G8每题8条，只用于训练分组与筛选。实查validation-answers.jsonl仅step20/evaluation_round1，共256行/256唯一question_id；NQ52/120，HotpotQA62/136，总114/256。现有D256属于开发验证，清洗后11008题尚无本轮正式测试结果。仅阅读代码/配置与聚合既有记录，未启动模型生成、修改训练/评分配置或运行测试；注释覆盖不适用。


2026-10-13T04:54:57.620787+00:00 /root 用户询问约一万题正式测试耗时：当前quality-v1正式train step20 metrics timing_s/testing=1493.0207732524723秒，val/num_samples=256，即24分53秒/5.8321秒每题（并行吞吐摊销）。当前验证8卡、val_batch_size8、每题单轨迹，线性外推10000题16.2003小时，11008题17.8333小时。完整11008题预留18–24小时属于预算估计，考虑独立模型加载/启动及题目检索轮数与性能波动；独立启动耗时未单独实测，不能当作论文作者报告或正式测试实测。假设测试独占当前评测资源、沿用生成与检索配置，不与训练争用；未调批次或参数，未启动正式测试。仅日志读取/算术外推，无新GPU生成或源码变更，注释覆盖不适用。


2026-10-13T04:59:50.327685+00:00 /root 用户询问优化器保存：实查step20完整checkpoint含actor/rank_0.pt至rank_7.pt，每片7615654965字节；8/8序列化小型元数据均确认optimizer/scheduler/scaler/runtime及Adam exp_avg/exp_avg_sq/param_groups字段，未加载大张量。driver.pt确认sampler/RNG，模型safetensors及COMPLETE.json清单同时存在。checkpoint.py save_rank_state保存optimizer.state_dict，load_rank_state恢复优化器/学习率调度/缩放器，恢复要求相同world_size8与FSDP包装配置；训练器已接入load_training_checkpoint。检查时实际训练步39，当前持久化可恢复点step20。仅文件清单/元数据/代码读取，未完整重算91GB哈希、未执行GPU恢复、未改训练或源码；文档同步，注释覆盖不适用。


2026-10-13T08:37:20.188224+00:00 /root 训练加速只读分析：见quality_v1_speedup_plan_20261013.md。实查当前failed/stopped（15:23），完成42步/完整checkpoint40；step43补抽16轮512组仅28/32触发硬轮数上限，未完成partial优化器更新。step33–42除验证步40的9步平均29.77分钟，gen90.40%，更新2.24分钟；平均380.44候选组留32。优先按policy版本消除多轮完整权重重复导出加载与前缀缓存失效，再原生动作结束即停、提前排除已训练题/当前policy复验、候选批次与训练批次解耦及token预算短基准。2倍/3倍生成速度对应16.31/11.83分钟仅算术目标。step40验证46.03分钟，先前按step20估的一万题测试耗时需重新标定。未改冻结代码/参数/启动或恢复训练，无新GPU基准；同步方案/执行次序/验收和台账，注释覆盖不适用。


2026-10-13T08:52:27.612288+00:00 /root 用户授权审查并提交动态筛选最新改动：暂存区为空，改动位于工作区。原8项CPU通过；中文编码损坏已按HEAD恢复，新增12项回归复现同题先k8后k7时仍选旧k8（1失败）。已修复同题备用优先级、清理正常组旧备用并为恢复模式增加题池无法补齐时的提前拒绝。范围仅4个difficulty源文件及test_refill_recovery.py；权重同步优化本轮仅评估，未实施。新代码CPU回归及注释验收待完成，无GPU恢复或参数更新。详见refill_recovery_review_20261013.md。


2026-10-13T08:56:21.711867+00:00 /root 补齐候选预算正整数校验（拒绝bool/float/None）和中文关键逻辑说明；新增回归待最终全量CPU确认。首轮全量CPU先执行了包含该新增回归的版本，预算校验尚未应用，保留该次失败日志。无GPU生成或恢复训练。


2026-10-13T09:01:26.351198+00:00 /root 动态筛选恢复审查完成并准备提交：修复中文编码、同题k7优先于旧k8缓存、正常入选题旧缓存清理、剩余题池不足提前拒绝及候选预算正整数边界。最终全量CPU286项：284通过、2需GPU跳过，新增恢复回归14项；证据maintenance/review-refill-20261013/cpu-retry.log。默认硬上限及奖励/协议/质量检查保持，refill_7_8_v1仅显式开启；旧checkpoint采样适配必须显式声明。未运行GPU续训，未部署新策略，当前原run完成42步/完整checkpoint40。权重同步本轮仅评估；按用户时间要求后续仅做必要失效一致性及1步GPU检查。函数说明27/27(@brief/@param/@return及适用异常约束)，关键内部单元24/24有中文说明，合计51/51=100%，遗漏0；逻辑单元清单：复制配置避免兼容性试探污染调用方、授权恢复字段移除与其他指纹保持、既有优化器设备放置兼容、耗尽策略名称及组合校验、缺省error规范化保持旧身份、候选预算正整数校验、仅扩展候选预算及结构化事件、旧策略适配授权且其他字段一致、扩展游标恢复及曝光验证、默认硬边界与恢复游标边界、备用正确次数白名单、全对组必须真实奖励有方差、正常与备用次数资格判断、剩余独立题池不足提前拒绝、硬上限及恢复软边界循环、候选耗尽继续且随机流不重置、同一policy真实备用轨迹缓存、正常入选题移除旧备用、同题七次组替换八次组、缓存满时低优先级替换、七次优先且完整补齐更新、实际备用身份及轮次事件、备用指标独立统计、夹具模拟模式及真实来源指纹回归隔离。编码替换字符0，git diff --check通过。


2026-10-13T09:11:29.924726+00:00 /root 用户取消权重同步优化并要求重新选择目标：实际MetaX专用manager早已缓存未更新权重，通用manager不代表本次执行路径，先前以重复全模型同步推断加速收益有误；取消此项，无生产代码变更。只读重建ckpt40前40步1280唯一已训练题，6412唯一被评分题；未训练且最新k3–6仅52题，其中最近step35–40只5题，因此历史中等题优先不能作为首要持续加速目标。改选原生动作结束即停：最新process-audit尾部32MiB中409条train报告、1634轮，raw_model_tokens234097、processed23172，未消费约90.10%；1219轮有尾部。此为样本token浪费率，不是耗时比例或全量统计。步骤：在合法search/answer结束处原生停止并保留完整结束标签；复用现有真实检索/评分/概率与梯度token对齐，不降低G8、3–6标准、训练组数、最大动作预算。必要CPU边界检查通过后按用户已授权ckpt40恢复训练，首个完整步兼作GPU验证；下一步跨policy同步和奖励检查保留，无独立长性能对照/全量验证。当前仅选择方案，未开启新生成停止配置、未启动训练。


2026-10-13T09:27:27.400555+00:00 /root 用户授权动作结束停止并从ckpt40恢复：接入独立action_stop解析边界和V1公开processor。合法完整动作之前logits不变，之后仅生成EOS；原token、概率和现有消费/梯度掩码复用。引用、代码、孤立闭合、嵌套/空动作保留旧处理，默认关闭兼容。新增生成来源版本与显式resume_generation_adaptation白名单，不放宽奖励/数据/学习率/G8等字段。CPU验证待完成，尚未启动GPU；权重同步优化已取消。


2026-10-13T09:43:20.606684+00:00 /root 动作停止实现与恢复准备完成：7项必要CPU及真实Qwen EOS前缀回归通过；兼容回归293项291通过、2需GPU跳过。新run metax-qwen7b-actionstop-resume40-20261013-v1从完整ckpt40续训至绝对100步，剩余60步；用户明确启用已提交7/8备用补齐。默认及无授权生成适配拒绝已覆盖；原奖励/lr/G8/批量保持。准备完整父checkpoint校验通过，源码快照与未提交差异冻结，GPU尚未启动；监督取消墙钟时限，稳定要求连续3完整步及下一次新policy生成。


2026-10-13T09:47:51.784387+00:00 /root 用户授权的ckpt40动作停止恢复已启动监督PID420795，无墙钟截止；新run metax-qwen7b-actionstop-resume40-20261013-v1。CPU7项必要验证及293项兼容回归通过，ckpt40完整校验/配置预检/源码冻结通过，保留用户选择7/8备用补齐。实际GPU模型加载、首步更新及稳定性验收尚待确认；持续监督到至少连续3完整步，不把CPU结果冒充GPU成功。


2026-10-13T10:04:19.211824+00:00 /root 动作停止实现与恢复准备完成：8项必要CPU及真实Qwen EOS前缀回归通过；兼容回归294项292通过、2需GPU跳过。新run metax-qwen7b-actionstop-resume40-20261013-v2从完整ckpt40续训至绝对100步，剩余60步；用户明确启用已提交7/8备用补齐。默认及无授权生成适配拒绝已覆盖；原奖励/lr/G8/批量保持。准备完整父checkpoint校验通过，源码快照与未提交差异冻结，GPU尚未启动；监督取消墙钟时限，稳定要求连续3完整步及下一次新policy生成。
