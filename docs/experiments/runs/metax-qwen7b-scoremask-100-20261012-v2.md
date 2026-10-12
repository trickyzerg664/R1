# 单次实验记录：metax-qwen7b-scoremask-100-20261012-v2

## 当前状态

负责人/root；2026-10-12T10:56:18.648974+00:00。状态preparing，训练0/100、评分0/256，GPU未启动。用户授权修复验证评分掩码、提交Git并从原始Qwen7B同配置重启。旧run已停止，完成训练0步、checkpoint无；原评价/冻结/日志保留。

## 可复现信息

方案：原始Qwen初始D256→单组100步→最终D256，每20步保存评价；本轮尝试使用已完成旧初始评价的原生token逐轮CPU重放，只有完整唯一、文本/来源/奖励/零更新证据全通过才显式冻结复用。初始化、reference均为/mnt/public/model/huggingface/Qwen2.5-7B，seed42，lr1e-6、warmup10、KL/entropy .001、32题×8轨迹、8卡、response256、最多10轮+最终轮；实际配置与hash待验收。分支data-difficulty-muxi，修复待提交。

## 运行位置及恢复

产物根目录：/mnt/public/code/lyk/lzy/runs/metax-qwen7b-scoremask-100-20261012-v2。当前只CPU修复验证，未启动生产模型。独立检索PID2137145保留。训练优化器/调度/scaler从0，不加载旧checkpoint；本次恢复未执行。

## 阶段进度与证据

开始构造真实多轮生成→RewardManager回归，含跨单字符/整个结束标签、协议开关、训练/验证及工具诱饵答案；测试尚未执行。下一步先确认旧生产代码能复现，再应用修复并全量CPU、真实tokenizer历史重放。CPU测试不能代替8卡实际训练验收。


2026-10-12T10:58:21.726647+00:00 评分来源/梯度掩码分离已应用：generation的来源矩阵保留所有模型消费字符，只屏蔽工具观察；sampled_loss_mask独立屏蔽人工梯度。main_ppo只补充接口说明。旧生产回归2项16个子场景均按预期失败（来源矩阵误删人工字符），无错误，证据regression-before-fix.log/result.json；本次全量CPU开始，结果待确认。负责人/root；生产GPU尚未重启。


2026-10-12T11:01:02.864992+00:00 首轮全量CPU260项：既有测试通过，新增关闭协议场景因测试夹具仍配置非零过程惩罚而触发既有配置拒绝，8个子场景报错、2项GPU跳过。已将关闭协议夹具惩罚设0，生产代码未再改动；失败cpu-regression.log保留。开始第二轮全量回归，GPU尚未启动。负责人/root。


2026-10-12T11:04:01.971249+00:00 全量CPU260项：258通过、2项GPU跳过；新增真实多轮评分回归2项16个组合通过，覆盖单字符/整个结束标签、协议开关、训练/验证、对错与工具诱饵。开始真实Qwen tokenizer全量初始评价重放；无GPU模型生成。负责人/root；失败首轮日志保留。


2026-10-12T11:09:27.122412+00:00 初始评价CPU重放首轮已逐题完成：正式原EM84/256、缺提取8，训练候选奖励和人工梯度掩码均无变化；汇总脚本预设83/256导致断言失败，原日志与派生文件保存historical-rescore-first-attempt。逐题发现额外一题嵌套答案未被协议接受，但原验证提取规则能得到正确Sam Cooke，属于原EM与协议门控口径差异。改用独立消费字符串逐题评分参照，保留原评分公式，不用协议83作为原验证期望。生产源代码未改；重放重试待确认。负责人/root。


## 2026-10-12T11:14:17.271993+00:00 评分来源掩码修复验收（/root）

已实现：generation._update_right_side的responses_with_info_mask只排工具观察，保留完整消费的人工闭合片段；sampled_loss_mask仍独立排人工/补齐梯度，actor交集未改。main_ppo仅补充评分与梯度的接口说明，奖励公式、KL、lr及初始化未改。共用修改复用于所有检索训练和评价，默认协议关闭已覆盖。

CPU260项：258通过、2需GPU跳过；真实多轮→RewardManager新增2项16个组合，覆盖跨单字符/整个标签、协议开关、训练/验证、对错和工具诱饵。首轮新夹具配置8个错误已修复、日志保留；旧生产2项16子场景按预期复现失败。验收后仅补充测试内部说明，AST与已测版本一致，无生产语义变化。

真实Qwen tokenizer重放256唯一题/918轮，正式原EM84/256（32.8125%）、缺提取8，旧79/256→新84/256：5题均0变1。四题原已被协议接受；额外一题嵌套答案原EM可提取但协议未接受，因此协议接受EM仍83/256，不能将两种口径混用。314个人工边界保持屏蔽，token/文本错位0、独立消费字符串评分差异0、训练候选奖励差异0、有效梯度掩码差异0、参数更新0。汇总脚本首轮预设83失败，已改为逐题独立参照，失败文件保存historical-rescore-first-attempt；生产奖励规则没有为此改动。

已验证CPU/真实tokenizer/正式奖励入口，未运行本次GPU kernel实验（算子与actor未改）、未启动8卡新训练；不能宣称已完成真实反传验收。完整重评分证据将显式冻结为新run初始评价，旧原始文件不变。证据cpu-retry.log、regression-before-fix.log、historical-rescore-retry.log/json、scoring-fix-verification.json。下一步Git提交、配置/权重/源码冻结验收，然后启动原始Qwen7B训练100步。

注释范围：3个修改源/测试文件、11个函数，@brief/@param/@return及适用约束11/11完整。独立内部逻辑20/20有效中文说明；合计31/31、100%，遗漏0。函数清单：["generation._postprocess_responses", "generation._update_right_side", "generation._compose_final_output", "RewardManager.__call__", "BoundaryWorker.__init__", "BoundaryWorker.generate_sequences", "GenerationMaskTests.test_full_loop_keeps_context_and_masks_boundary", "ScoringBoundaryTests.search", "ScoringBoundaryTests.check_boundary_reward", "ScoringBoundaryTests.test_one_character_answer_boundary_scores_normally", "ScoringBoundaryTests.test_multi_token_answer_boundary_scores_normally"]；内部单元：["同向补齐的独立人工梯度掩码", "有工具观察时保留完整消费字符", "无工具观察时保留完整消费字符", "人工边界矩阵独立维护", "最终info_mask仅排观察", "评分入口禁止使用梯度掩码删字符", "夹具跨界参数保存", "夹具单字符/整个标签分支", "既有多轮来源/梯度断言", "工具诱饵答案来源", "协议开关遍历", "训练/验证遍历", "答案对错遍历", "正式多轮生成接口", "同行标准答案与来源数组", "来源保留与人工屏蔽断言", "两种观察模式损失交集", "真实RewardManager与临时审计", "奖励/提取/观察排除断言", "原EM与协议接受EM对照"]。外部CPU重放脚本3函数均带完整说明，关键逻辑包括完整行、唯一题/零更新/原初始化、逐轮原始前缀与人工掩码、文本核对、两种损失交集、同行来源、训练候选奖励不变、独立消费评分、原上下文保留、差异仅0变1、证据hash；准备脚本4函数说明完整，缓存重评分门限与三份原始文件冻结有就近中文注释。详情comment-coverage.json；无遗漏。

资产与配置验收开始；CPU全量回归通过，训练0步，原始Qwen模型进行完整文件哈希与safetensors头部验证。

冻结验收通过：{"checked_utc": "2026-10-12T11:16:50.781938+00:00", "run": "/mnt/public/code/lyk/lzy/runs/metax-qwen7b-scoremask-100-20261012-v2", "model": "/mnt/public/model/huggingface/Qwen2.5-7B", "sources": 295, "assets": 16, "config_differences": 7, "identity": {"initial_model_id": "7c3269c21a61915411e593401dbe335b9c427a02702067f986bce261e592a76e", "reference_id": "7c3269c21a61915411e593401dbe335b9c427a02702067f986bce261e592a76e", "retrieval_id": "wiki18-e5-metax-gpu-fp32-shard8-20261008-v1", "seed": 42, "training": "f0a614f1a94a0fdaec4cc32eb8a7b4b74f681374bb4909ff7231e6abcfaf53d4", "versions": {"torch": "2.6.0+metax3.3.0.2", "transformers": "4.57.1", "vllm": "0.11.0+empty"}, "world_size": 8}, "cpu_verified": true, "gpu_started": false, "free_bytes": 3001179692032}。下一步按用户授权验收复用初始D256→100步训练→最终D256。初始化与旧Qwen运行相同；初始评价复用完整原生token的CPU重评分，训练从0开始。


2026-10-12T11:18:08.208924+00:00 按用户授权实际重启：{"pid": 3322726, "proc_start_ticks": "1012772083", "started_utc": "2026-10-12T11:18:08.208924+00:00", "argv": ["bash", "env/metax/run.sh", "-u", "scripts/difficulty/stability_trial.py", "--run-directory", "/mnt/public/code/lyk/lzy/runs/metax-qwen7b-scoremask-100-20261012-v2", "--launch"]}。修复提交363fbcb，冻结295源码/16资产，原始Qwen7B与reference身份一致、训练指纹f0a614f1a94a0fdaec4cc32eb8a7b4b74f681374bb4909ff7231e6abcfaf53d4不变，配置仅7项产物/名称路径变化。新初始D256为完整原生轨迹CPU重评分84/256，协议接受83/256独立保留；监督器启动后再验收所有冻结原始评价，随后原始Qwen单组100步→最终D256。此时只确认监督进程创建，实际训练0/100、参数更新0，尚未确认worker生成。旧run停止与原manifest保留，检索服务ready。负责人/root；下一步实查8卡worker、模型载入、首批生成与异常日志。


<!-- metax-qwen7b-scoremask-100-20261012-v2-current -->

{
  "status": "failed",
  "phase": "stopped",
  "error": "Supervisor interrupted: 15",
  "checked_utc": "2026-10-12T13:34:27.434911+00:00"
}

<!-- /metax-qwen7b-scoremask-100-20261012-v2-current -->


2026-10-12T11:28:30.218493+00:00 八卡实际启动验收（/root）：launcher与train启动tick匹配，8个WorkerDict身份已核验并载入Qwen7B/vLLM。首批256条候选已完成生成评分；['(main_task pid=3324511) [动态筛选] step=1 round=1/16 candidates=32 mixed=17 retained=17/32']。当前完成训练0/100，checkpoint=[]；候选生成与保留组数不能当作训练完成步数。原生审计925轮、采样前缀错位0、文本前缀错位0、人工边界327token。冻结源文件全部匹配，检索ready，无Traceback/OOM/ActorDied/非有限或token前缀错误。证据startup-inspection.json、train/console.log、process-audit.jsonl；当前仍在首步补抽，尚无实际反传/梯度更新验收。下一步按原监督器检查首个train事件和每20步checkpoint/D256，不能宣称退化已改善。旧run保留。


## 2026-10-12T12:28:39.716527+00:00 训练健康与重复输出复核（/root）

最新状态running/train，完成6/100，checkpoint=[]（配置第20步首存/首评）。前5步每rank更新2、跳过0、微批观测256，loss/KL/熵/grad均有限；grad_norm7.4102→3.3335（裁剪前）、token加权熵1.0053→0.7524中间反弹、KL1.097e-5→.00285663、lr5e-7处于10步预热。显存约42–44GiB随阶段切换变化，检索ready；日志未见OOM/Traceback/ActorDied/通信异常，八卡ECC读取为0，不能据此证明所有软硬件实现完全无bug。第20步固定验证尚未执行，训练reward不能当验证正确率。

输出有明确质量异常。完整去重3072条候选/11528轮审计，采样前缀错位0、文字前缀错位0；强重复探针为8词片段重复>=20或已观察“千方百计索”出现>=20。step1–5候选命中依次8/512、14/768、10/512、9/512、16/768，约1.56%–2.08%；实际入选命中4、6、7、3、4，共24/1280。筛查不是完整语义分类器。step1在首次参数更新前已存在严重lm重复；至少部分异常不能全部归因于本轮反传。初始D256同规则0/256，但题池/采样不同，不能直接用两者比例判定训练劣化。中文筛查包含正常中文解释，未把中文等同乱码。

已按filter_candidates顺序复核实际入选：每组8行question_id/奖励均值一致，先eligible组凑32，已完成step1–5更新。展示日志沿用train_candidates阶段标签，首轮“按train标签判断入选”得到0属于只读分析映射错误，已纠正；没有据此得出未入选结论。step4“千方百计索”647次、jdbcTemplate循环30次的两个代表候选未入选，但其他强重复已入选。

关键正强化例：step2 round1 trace_uid=d3a83057c7a246d0aa8df64df66841b4:183，8词片段answer/castException/CMD/go/143/search循环136次，11轮，最终The Beatles；reward1、组均.4825000027、相对组均+.5174999973，eligible且实际进入step2更新。异常发生于答案之前的消费正文，相关轮tail为空；模型消费token统一正优势，存在鼓励重复片段的策略梯度信号。四条代表共44轮原始token经真实Qwen tokenizer直接解码与日志完全一致，排除这些个例的编码展示错误。

用户询问重复惩罚：建议引入，尚未实施。仅轻扣0.1会让正例reward.9、同组均.47，仍获+.43相对优势；重度重复应取消正奖励/质量门控，并同步task_success，避免全劣质差异组入选。检测仅针对实际消费的采样模型文本，排工具观察、提示、人工边界和未执行尾部；对轻度采用有限软罚，重度设质量门控。原EM单独保留，先离线回放核验误罚和优势符号，再独立冻结对照，不热改当前运行。

证据health-quality-fullscan-20261012.json、health-quality-representatives-20261012.json、health-native-decode-20261012.json、health-gpu-snapshot-20261012.log、health-analysis-20261012.json及原始metrics/process-audit/readable日志。仅只读分析、原生token CPU解码和GPU状态读取；未修改源码/配置/模型，未停止或新启动训练，未运行本次GPU算子测试，源码注释覆盖不适用。下一步评估重复控制的误罚/奖励信用分配并在固定D256检验质量。


2026-10-12T13:34:28.004231+00:00 用户要求暂停并按新规则重启（/root）：已核验launcher/child启动身份后停止本实验并清理专属Ray环境，独立检索PID2137145保持ready。已完成12/100，完整checkpoint=[]；旧日志/权重/manifest保留，状态stopped_for_quality_restart。新资格与重复奖励改变指纹，将从原始Qwen7B及零优化器建立新运行。证据quality-restart-stop-request/result.json。
