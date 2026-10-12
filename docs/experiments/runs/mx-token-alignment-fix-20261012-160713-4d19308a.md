# mx-token-alignment-fix-20261012-160713-4d19308a

负责人 /root。用户授权修复 rollout token 重编码及融合概率 labels 布局。CPU 验证已启动；GPU 待执行。原训练保持 stopped_by_user，不加载生产模型、不重启训练、不停止检索。

代码：当前分支及未提交补丁；源文件 SHA256、修改前后差异与基线备份见 `/mnt/public/code/lyk/lzy/runs/mx-token-alignment-fix-20261012-160713-4d19308a`。CPU 命令：`CUDA_VISIBLE_DEVICES= bash env/metax/run.sh -m unittest discover -s tests -v`。模型训练步数 0，评分题数 0；此运行只验证代码。奖励、KL、lr 与配置均未修改。

CPU 返回码：1；证据 `/mnt/public/code/lyk/lzy/runs/mx-token-alignment-fix-20261012-160713-4d19308a/cpu.log`。GPU 尚未执行；失败需保留并修复后重测。

旧夹具接口已同步 return_loss_mask/metadata，原活动行与种子断言保留。首次 CPU 249 项运行失败 1 项、跳过 2 项；失败日志保留 cpu.log。开始第二次全量 CPU 回归。

第二次 CPU 全量回归返回码 0；证据 /mnt/public/code/lyk/lzy/runs/mx-token-alignment-fix-20261012-160713-4d19308a/cpu-retry.log。GPU 与历史重放待执行。

CPU 全量回归通过（249项，跳过2项）。开始实际 GPU0 融合概率/梯度验证，并使用真实 tokenizer 重放前49步全部入选轨迹。证据目录 /mnt/public/code/lyk/lzy/runs/mx-token-alignment-fix-20261012-160713-4d19308a。不启动训练。

实际GPU算子返回码 0；历史重放返回码 0。证据 gpu-kernel.log、historical-replay.log/json。失败尝试保留；结果细节待最终汇总。

人工边界掩码独立输出 sampled_loss_mask，并在 actor 的工具观察开关两种取值下都合并。真实观察开关语义保持。新增动态零补齐与 UTF8 中间解码回归；此前249项和GPU11项结果保留，仅适用硬化前源码；开始最终全量回归。

最终测试返回码 {"cpu_exit": 0, "gpu_exit": 0, "checked_utc": "2026-10-12T08:39:43.688063+00:00"}；证据 cpu-final.log/gpu-final.log，训练未恢复。详细验收汇总待完成。

追加左右补齐审计与正式 update_policy 训练掩码验收。使用极大人工正优势，验证两种 state_masking 下人工输出不更新。此前252项/14项结果保留；开始最终源码回归。

验收源码测试返回码 {"cpu_exit": 0, "gpu_exit": 0, "checked_utc": "2026-10-12T08:48:15.782957+00:00"}；证据 cpu-acceptance.log/gpu-acceptance.log，训练仍未恢复。


## 2026-10-12T08:55:43.263980+00:00 token与概率修复验收完成

负责人 /root；运行 mx-token-alignment-fix-20261012-160713-4d19308a。保留原始采样前缀，字符跨 token 边界只重建末片段并独立屏蔽；sampled_loss_mask 在 state_masking 两种状态下都参与 actor 交集。融合概率两个入口 labels 连续复制。共用训练/生成/检索路径复用原因：所有搜索实验和评价都共享真实消费协议，需要同一token和掩码规则；默认关闭过程协议保持原消费文字，非规范编号变化属于修复目的。奖励、KL、学习率未改，日志修复未覆盖。

CPU254项，252通过、2跳过；实际GPU环境16项全部通过，其中真实融合算子覆盖16种batch/长度/重算组合，概率和梯度均在2e-6容差内。实际update_policy验证人工位置极大正优势仍无梯度更新。历史12544条/49761轮入选轨迹重放通过：训练前缀错位0，文本变化0，10330个人工边界token全部屏蔽，无长度超原生或256。早期一次旧夹具接口失败已修复，所有失败日志保留。

已实现和接入：原始token裁剪、独立边界掩码、actor损失交集、原生token审计、概率布局保护。已验证：CPU、实际GPU融合kernel、完整多轮小夹具、真实tokenizer历史重放。未验证：7B新训练是否改善退化、完整8卡生产模型运行、vLLM与FSDP同权重概率数值对账。模型训练0步/评分0题；原训练仍 stopped_by_user，检索PID2137145保留。下一步如启动训练须新建运行并冻结本次源码，旧运行源快照/检查点未改。

注释审查范围：search_r1/llm_agent/token_alignment.py, search_r1/llm_agent/generation.py, verl/utils/torch_functional.py, verl/experimental/stability/generation_audit.py, verl/workers/actor/dp_actor.py, tests/test_rollout_token_alignment.py, tests/test_grpo_difficulty.py。39处新增/修改函数的 @brief/@param/@return 及适用约束逐项通过；内部关键逻辑47项均有就近中文说明。职责与内部行为合计86/86，覆盖率100%；未发现遗漏项。函数清单与内部单元完整列表见 /mnt/public/code/lyk/lzy/runs/mx-token-alignment-fix-20261012-160713-4d19308a/comment-coverage.json。内部清单：原生长度校验与截取；尾部EOS/pad剔除；消费前缀校验与空消费；完整内容原编号返回；二分定位字符边界；精确token边界返回；跨边界安全前缀判定；UTF8临时字符回退扫描；人工片段重建及文本校验；共用协议消费边界选择；逐行原生元数据长度校验；原始编号与生成掩码同序构造；token和掩码同向补齐；响应掩码形状校验；环境反馈可选屏蔽；按完整上下文共同重排；有无观察两条完整历史拼接；独立人工边界历史维护；完整历史预算验证；最终二值人工掩码输出；审计活动行和形状校验；普通轮原始掩码还原传递；最终轮原始掩码还原传递；审计右pad与掩码同步剔除；审计左pad与掩码同步剔除；二值前缀掩码和原编号校验；人工片段审计字段记录；概率包装labels展平连续复制；直接融合入口连续保护；actor可选掩码字段选择；工具观察开关原掩码选择；人工二值掩码交集；测试词表规范合并分支；测试多字符token解码；完整与截断非规范前缀断言；单片段和多片段人工边界断言；终止长度和非法前缀拒绝断言；审计拒绝人工token冒充采样；两轮原始上下文和环境掩码验证；关闭过程协议兼容验证；动态合并二值掩码零补齐；UTF8非单调解码回退模拟；左右补齐逐行审计验证；真实actor更新中的极大人工优势及零更新断言；CPU融合接口连续布局验证；GPU多形状重算概率及梯度对照；旧活动行夹具掩码接口同步。

证据：/mnt/public/code/lyk/lzy/runs/mx-token-alignment-fix-20261012-160713-4d19308a 下 cpu-acceptance.log、gpu-acceptance.log、historical-replay.json、final-verification.json、逐文件前后备份及源码SHA256。Git差异空白检查通过，当前源码保留为未提交修改，未混合提交其他工作。
