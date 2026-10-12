# 单次实验记录：metax-grpo-reward-100-20261011-v2

## 当前状态

- 负责人/root；v1单组历史对照。当前CPU准备，GPU未启动；训练0/100、评价0/256、本次完整checkpoint0。
- 旧B/T v2已停止：B8步、T0、无checkpoint；日志保留。
- 初始是历史100步真正的step40 actor；新建优化器和调度，从0训练100步。
- 下一步：HF哈希、CPU回归、配置差异、源码提交与冻结通过后启动。

## 可复现信息

- 历史基线：/mnt/public/code/lyk/lzy/runs/metax-process-r1-100-b32-gpu-20261008-v2。
- 初始actor：/mnt/public/code/lyk/lzy/runs/metax-process-r1-40-20261006-v1/checkpoints/step_40/actor；固定reference：/mnt/public/model/huggingface/Qwen2.5-7B。
- lr1e-6、warmup10后常数、Actor KL.001、clip.2、grad_clip1、entropy_coef.001保持历史。
- 同P/D256数据、8卡、train_batch32/val8、8轨迹、最长256、max_turns10、temperature1、top_p.95、每20步保存与D256验证。
- seed42，历史prepare_config也把experiment_seed由null设42并seed_all42；训练入口与历史相同main_ppo。
- 新奖励bounded_invalid_v1：缺答案罚.1、确认完整无效动作每次.02最多2次、过程罚总上限.12；长度截断/未知终止不算确认无效动作，无重复标点特例。
- 保留已授权task_success_mixed修复；结论为奖励+筛选组合效果，不能单独归因于奖励。
- 原生终止记录、只读诊断、连续轨迹、全rank指标修复保留；损失与优化器算法不变。
- 检索wiki18-e5-metax-gpu-fp32-shard8-20261008-v1、retriever PID2137145；启动前须核实健康。
- 代码/资产哈希及快照：manifest.json、source-snapshot.tar.gz待冻结；参数差异historical-config-diff.json待验收。
- 标签、配比、刷新及B分支续接：不适用。
- 总48小时沿用原验证起点，46小时停止预留收尾，不追加旧奖励训练臂。

## 运行位置及恢复

- 产物：/mnt/public/code/lyk/lzy/runs/metax-grpo-reward-100-20261011-v2。
- train/config.yaml、train/console.log、train/metrics.jsonl、train/process-audit.jsonl、train/validation-answers.jsonl、train/trajectories.readable.log。
- parent-eval/为初始零更新健康/原生终止验收；final-eval/为step100独立冷D256。
- commands.json记录实际命令；解析配置train/resolved-preflight.yaml；status.json持续记录真实步数。
- CPU准备时间见prepared.json；GPU开始/PID时间待启动，结束未核实。
- 20/40/60/80/100完整checkpoint为潜在恢复点，必须通过完整校验；本次暂无可恢复点。
- 故障不自动改变学习率、KL、batch、采样或上下文；未完整100步不能宣称完成。
- 旧v2训练已退出；新启动时重验八卡独占锁/GPU进程。

## 阶段进度与证据

| 时间UTC | 动作 | 实测进度 | 证据 | 下一步 |
| --- | --- | --- | --- | --- |
| prepared.json | CPU准备 | 训练0/100、评分0/256 | plan.unfrozen.json、配置 | 校验冻结 |

## 验证及结果

- 本次新增4项CPU回归待执行，不引用旧230项结果替代。
- 验收：每rank两次更新、全8rank微批256、loss/KL/norm/token熵有限；最终100步及完整step100、冷D256唯一256题且更新0。
- 比较相同步数20/40/60/80/100原EM、缺答案、无效动作、原生终止、回答长度、重复率与搜索行为；奖励需分解，不直接比较不同公式总reward。
- 历史EM分别113/116/122/132/129，均256题；step100重复验证需分轮，不合并为512题。
- 历史部分loss/熵/KL日志只有rank0，新日志全rank；不能直接将两者标量均值按同口径解释。
- 新筛选可能增加补抽时间；耗时和改善尚未实测。

## 失败、变更与交接历史

- 用户最新要求允许KL与学习率保持一致，本轮采用原值以隔离更多变量。
- 初次准备命令因系统python缺yaml在导入即失败，无文件/训练副作用；已改用项目独立环境。
- 新奖励原生终止证据不足必须停止，不回退旧奖励；此前失败/停止运行全保留。


## 2026-10-11T11:16:23.869996+00:00 v2准备

v1在Ray启动前失败，评价0/256、训练0，原状态与日志保留。v2只缩短Ray独占目录并加入启动前107字节验收；新奖励、task_success_mixed、lr1e-6、KL.001、旧step40初始Actor、数据和100步预算均不变。复用v1完整HF17文件哈希，重新检查所有文件大小/mtime一致；不复用step60评价。当前CPU准备，235项CPU回归待执行，GPU未启动；预算起点不重置。


## 2026-10-11T11:18:02.367083+00:00

Ray路径修复后的CPU235项全部通过，失败/错误/跳过0；v2路径保守按10位PID分别95/89/94字节，均小于107。旧v1父评价0、训练0、清理完成；HF17文件验证复用且大小mtime一致。实际训练算法与超参未改。下一步提交运行环境修复与记录，再重做冻结及仅检查；正式GPU尚未启动。


## 2026-10-11T11:20:08.889408+00:00 验收后实际启动

v2冻结验收和监督器仅检查通过；源码6d903c1389bbc64e9a964d09e979ff72bb90f8be，293源码/15资产，配置白名单16项（包括诊断/奖励/筛选及产物路径），学习率/KL无差异。CPU235全通过、HF17文件验证一致，Ray路径最大95字节。历史日志实际lr：step1=1e-7、step10/20/80/100=1e-6，新运行保留同调度。按既有用户授权启动初始D256健康验收→单组100步→独立最终D256。总预算从原验证起点计算，不重置。此时训练0/100、评分0/256，后期效果待验证。


启动检查：{"checked_utc": "2026-10-11T11:20:48.589929+00:00", "state": {"status": "running", "phase": "parent-eval", "child_pid": 2869860, "gpu_current_MiB": [9627, 9691, 9627, 9627, 9627, 9627, 9627, 10331], "trained_step": 0, "checked_utc": "2026-10-11T11:20:10.582404+00:00"}, "parent_completed_answers": 0, "supervisor_identity_alive": true, "ray_local_started": true, "ray_socket_error": false}；证据startup-inspection.json，负责人/root。


2026-10-11T12:41:09.201505+00:00 日志查询：{"status": "running", "phase": "train", "child_pid": 2878057, "gpu_current_MiB": [28249, 27929, 27609, 27545, 27545, 27865, 27609, 28249], "trained_step": 3, "published_checkpoint_steps": [], "checked_utc": "2026-10-11T12:40:40.167420+00:00"}；实际日志与闭合行数见 /mnt/public/code/lyk/lzy/runs/metax-grpo-reward-100-20261011-v2/log-query.json，负责人/root。


## 2026-10-11T14:33:32.738603+00:00 当前进度与正常性检查

当前判定：运行和数值稳定性正常，生成行为已有需要关注的早期变化，尚无充分证据确认策略坍缩或普遍重复输出。最近完成14/100、正在第15步补抽；本次完整checkpoint0，按配置第20步首存/首评。监督与训练PID身份匹配，检索ready，冻结内容全匹配；14步每rank更新2/跳过0、全rank微批256，loss/KL/grad_norm/token熵无非有限值，console无Traceback/OOM/ActorDied。本次不同训练阶段的显存读取约32.4–43.3GiB（33177–44378MiB），低于56GiB监督门限。初始独立D256为115/256、缺答案0，零更新、原生终止覆盖100%。

step1→14：KL .2595→.2079；token加权熵 .7121→.7767（先降后升，无持续塌至0）；grad_norm2.7827→1.8193，14步最高4.4376，未见爆炸；loss最新-.0005556。lr预热10步后1e-6，KL系数.001保持历史。需关注：含搜索观察的response_length均值1490→2016，实际训练掩码模型token每轨迹207.6→280.0；搜索次数2.66→3.59；单轮generation limit hit36.46%→51.23%，强制最终生成5→26，缺答案1/256→8/256（3.125%）。response_length不能解释成单次最终答案长度，generation limit hit不能解释成51%未作答。

近期最后8MiB候选奖励记录按trace_uid去重147条（抽样，不代表全训练或固定验证集）：缺答案1，确认无效动作1，12条存在完全相同的重复搜索；执行模型文本未检出四次重复8词片段（仅粗略探针，不能证明完全无重复）。缺答案例为搜索禁止阶段仍search，缺答案.1+确认无效动作.02，总奖-.12，新奖励正确应用。真实搜索结果与未执行尾部未混入重复文本检查。此前一次诊断脚本因把标量当列表len报TypeError，已修正为独立抽样；错误在只读检查脚本，训练未受影响，无代码或参数改动，未运行新测试；注释覆盖不适用。

下一步保持冻结参数完成第20步固定D256，比较缺答案/EM/长度/搜索重复等质量，不能仅凭训练reward .563判定改善（task_success_mixed改变样本选择）。证据progress-health-inspection.json、recent-candidate-health-sample.json、train/metrics.jsonl、train/console.log、parent-eval/summary.json；负责人/root。

最后状态快照：{"status": "running", "phase": "train", "child_pid": 2878057, "gpu_current_MiB": [33177, 33690, 33370, 33305, 33305, 33626, 33370, 34010], "trained_step": 14, "published_checkpoint_steps": [], "checked_utc": "2026-10-11T14:33:14.438789+00:00"}


## 2026-10-11T16:11:18.616989+00:00 实际轨迹阅读示例

用户请求按实例讲解可读轨迹。本次选train/trajectories.readable.log首条（行2至117），trace_uid=9a14bb605140406784b96ed5c2d8e037:0，问题为费城人棒球队位于哪个美国州，3轮search/search/answer，最终Pennsylvania、规则奖励1。来源train_candidates、step1、评分批次1、行0；候选轮次、对话轮次、训练步数含义不同。真实工具结果仅绑定真实call_id的visible_text；原始生成未执行tail分离，不能当真实检索返回或又一次最终答复。候选正分不保证入选训练；此UID在step1未出现train头，首组8行实际奖励见trajectory-reading-example.json，保留原日志未修改。无源码/参数/训练操作；本次未跑测试，注释覆盖不适用。负责人/root，证据/mnt/public/code/lyk/lzy/runs/metax-grpo-reward-100-20261011-v2/trajectory-reading-example.json。


## 2026-10-11T16:42:13.105558+00:00 answer后继续生成的代码与实例核对

当前生成器实际SamplingParams仅设置max_tokens=256、ignore_eos=false及温度/top_p等，运行kwargs没有</search>或</answer>停止字符串。闭合动作标签是应用协议文本，不自动充当EOS。vLLM先完成本轮原始采样（EOS或长度等终止），随后LLMGenerationManager._postprocess_responses通过parse_action只保留首个动作的consumed，tail用于审计；多轮循环接受answer后done并移除active_mask，不继续该轨迹工具交互。尾部不进入当前消费轨迹、训练响应或用于直接追加无效动作惩罚；仍浪费原始生成计算，不能据此证明后期策略坍缩。

刚讲解的trace_uid=9a14bb605140406784b96ed5c2d8e037:0实际三轮：第1轮search，raw72/processed31，未执行尾部为模型生成information和answer；第2轮search，raw98/processed56，同样尾部模拟information及answer；第3轮answer，raw28/processed27仅移除EOS，tail为空。三轮均原生finish_reason stop、eos_observed true。故该例实际最终answer后没有继续生成；日志答案之后的内容是排在末尾的前两轮诊断，不能按文件展示位置当作时间顺序。一般情况下原始answer后仍有文本与缺少动作标签停止条件相容，需要区分EOS终止能力/协议边界/后期重复坍缩。

推论：模型倾向补全整段搜索-观察-答案式文本，尾部自造工具结果不是实际检索。现状属于可解释的停止边界问题，非理想代理交互；确认答案后的程序结束逻辑正常，不把原始继续生成归为完全正常或确认后期退化。后续动作边界停止应独立评估，保留闭合标签、token前缀及训练/推理一致性；本次仅解释，没有修改当前对照的代码/参数或启动额外任务，未跑新测试，注释覆盖不适用。

证据generation-stop-explanation.json及同trace原始审计；负责人/root。


## 2026-10-11T16:45:14.208246+00:00 模型续写与真实检索返回的下一轮上下文

本例下一轮模型输入由程序明确构造：上一轮上下文+首个完整动作之前的consumed模型文本+真实batch_search返回经观察裁剪后的next_obs_ids。模型在</search>之后续写的information/answer属于tail，不参与_update_rolling_state/_update_right_side拼接，只保留审计。真实工具结果由TraceLedger.execute通过search_fn注入，再由observe_visible绑定本轮call_id；模型无需在两份结果中自行判别，因为下一轮只提供真实返回这一份。模型原始采样时尚未获得工具结果，续写属于按文本上下文模拟；采样结束后程序截断并搜索，再以重建的输入发起下一轮生成。结论限定于本例首个search之后的尾部，不泛化为所有伪造内容都会自动删除。看到真实结果不能保证模型正确利用它，仍可能忽视证据或答错；提示中将information定义为工具返回，不保证模型有可靠来源判别能力。本次仅核对与解释，无源码、配置或训练变更，未运行测试，注释覆盖不适用。 证据search_r1/llm_agent/generation.py:_postprocess_responses/_update_rolling_state/run_llm_loop及verl/experimental/process_checks/protocol.py:TraceLedger.execute/observe_visible；同一实例trajectory-reading-example.json，负责人/root。


## 2026-10-12T02:44:31.708614+00:00 日志长空白回溯修复（待验收）

用户授权修复日志问题。只修改 verl/utils/trajectory_logging.py 与 tests/test_trajectory_logging.py：固定标签分段后以字符串边界清理替换重叠空白正则；保留旧排版、完整模型正文、预算与奖励接口。新增短文本兼容及隔离子进程长空白/完整轨迹回归，测试尚未执行。原始字节与哈希证据位于 /mnt/public/code/lyk/lzy/runs/metax-grpo-reward-100-20261011-v2/log-format-fix-20261012。旧进程仍加载原实现，未停止/热替换/恢复训练，49步和20/40 checkpoint状态待最终复核；原manifest与历史日志保留。下一步CPU回归及真实第50步行206历史重放。负责人/root。


## 2026-10-12T02:51:02.845799+00:00 用户停止当前实验

用户明确要求直接停止。已核验launcher/train启动tick和独占进程组，退出监督器与本实验worker；独立检索PID2137145保持原身份。完成49/100步，COMPLETE checkpoint20/40，49步未额外保存；历史日志、权重、原manifest均保留。证据 user-stop-request-20261012.json、user-stop-result-20261012.json、status.supervisor-exit-20261012.json；最终状态stopped_by_user。日志修复CPU回归仍处理中，未启动恢复或新训练。负责人/root。


## 2026-10-12T03:02:47.448737+00:00 日志回溯修复验收及停止状态

修复完成，仅源码verl/utils/trajectory_logging.py与tests/test_trajectory_logging.py。固定标签分段及顺序边界清理替换重叠空白正则，保持单次旧排版、完整消费模型文本、诊断预算及奖励/采样接口；日志关闭路径兼容。未新增评分器/生成器，未改模型或训练超参数。

本次命令：cd /mnt/public/code/lyk/lzy/R1-vllm-metax && /mnt/public/code/lyk/lzy/envs/vllm-metax-clean33/bin/python -m unittest tests.test_trajectory_logging -v；19项全部通过（17既有+2新增），256种短文本排版对照通过，长空白/交错空白/未闭合标签/完整轨迹及奖励随机流兼容均覆盖。首轮新增测试假设和冷启动预算问题已记录；最终子进程冷启动预算60秒、实际格式化限5秒。最终注释补齐后子进程脚本AST语义相同，没有重复GPU实验。git diff --check通过。

真实历史回放trace_uid ad54b1c9b3274b84937f6c8358f92316:206：30336空白尾部格式化 1.453ms，完整9轮轨迹 2.091ms；输入记录未变，消费文本完整，预览单独保存，原审计和轨迹日志未重写。证据 /mnt/public/code/lyk/lzy/runs/metax-grpo-reward-100-20261011-v2/log-format-fix-20261012 内cpu-tests.log/json、historical-replay.json、historical-row206.preview.log、source-audit.json、final-verification.json。

当前实验已按用户要求停止：49/100步，完整checkpoint20/40，独立检索ready。未热替换、未恢复、未启动新训练。源码备份只含trajectory_logging.py.before与test_trajectory_logging.py.before两份修复前文本，不含权重/数据/整份大日志。原manifest及控制身份保留；未来重新启动必须记录此次展示源码差异并按原恢复规则核验，不能静默改旧manifest。

注释审查范围4个函数；逻辑单元23/23有效中文说明，覆盖100%，函数@brief/@param/@return及适用约束均完整，遗漏0。单元清单：{"_format_control_tags": ["函数职责/输入输出", "固定标签识别与线性分段", "按文本段遍历", "前一标签后的空白清理", "后一标签前空白清理", "标签换行生成", "拼接与首尾清理"], "display_text": ["函数职责/输入输出", "换行和终端控制字符清理", "调用独立标签排版", "诊断预算与完整模型输出边界"], "test_tag_whitespace_layout_matches_previous_output": ["函数职责", "旧正则限定短样本", "左右空白组合遍历", "控制标签与未闭合标签场景", "单次输出兼容断言"], "test_long_whitespace_formatting_timeout": ["函数职责/子进程隔离", "导入后实际性能计时", "30336与更大空白场景", "完整展示报告构造", "输入副本及奖励结束标记检查", "实际5秒预算", "子进程60秒冷启动超时/结果检查"]}。临时只读/停止脚本函数及关键分支另说明，未把它们接入训练。负责人/root；未提交/推送。下一步按用户后续选择分析模型异常；本次日志修复不宣称解决生成退化。


### 2026-10-12 指标走势与异常分析补充（/root）

- 11:04北京时间实查：完成49/100步；状态stopped_by_user，driver/main_task及抽查worker已退出，step20/40有COMPLETE标记，未做模型加载/恢复试验。
- 图表与报告已保存到产物目录 `/mnt/public/code/lyk/lzy/runs/metax-grpo-reward-100-20261011-v2/plots/`：mx_validation_accuracy.png、mx_training_trends.png、mx_generation_anomalies.png、mx_train_metrics.csv、mx_training_analysis.md。CSV包含49步、129指标字段；本次为日志事后快照，未接入自动更新。
- D256初始115/256、第20步118/256、第40步129/256，已对照逐题记录；41–49步尚无验证，不能将训练奖励当正确率。第40步加权熵约0.432，第49步2.569；候选保留率早期33.33%至近期19.74%，生成平均425秒至879秒。
- 审计按trace_uid去重，模型消费文本含至少20个汉字的候选比例第47/48/49步为3.28%/5.23%/7.42%，是筛查规则，不能将全部标记等同乱码。部分此类候选获得正奖励；第49步批次189行18奖励1、组均值0.5、eligible=true且无拒绝原因。
- 长空白30336字符与日志正则超线性回溯，结合初查GPU全0%和main_task CPU运行，支持第50步CPU日志格式化阻塞；未取得实时Python调用栈。400/800空格限时复现约0.083/0.643秒。全49步数值无NaN/Inf，不能据此判断生成健康。
- 本次只读分析训练日志并生成/保存派生图表；没有修改训练参数、停止或恢复训练，没有GPU实验。下一步：日志修复验收、同题比较父/20/40模型的正确率与生成质量，再做短程单因素对照。源代码修改及修复验收由“日志输出修复”聊天处理；本次源码注释覆盖不适用。


2026-10-12 答案前异常与奖励信用分配复核（/root）：第49步评分批次189行18，在对话轮4、5的实际消费模型文本中分别含66、55个汉字及无意义混杂；最终answer=five在轮5末尾，两个异常事件tail均为空。本条奖励1、组均值0.5；round2开始保留10组、本轮8个eligible组全部进入目标32组，因此该条实际入选并更新。已核对GRPO优势广播和info_mask，异常模型token未被按可读性屏蔽，获得正向策略梯度信号；答案后未执行tail被截断，仅审计。个例最终答对，不足以量化整体正确率损失。详细证据已追加到产物plots/mx_training_analysis.md。只读实现核查、未改训练源码/参数、未跑GPU实验，源码注释覆盖不适用。
