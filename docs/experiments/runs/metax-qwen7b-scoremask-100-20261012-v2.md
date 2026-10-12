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
