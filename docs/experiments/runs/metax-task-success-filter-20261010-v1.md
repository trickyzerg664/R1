# 单次实验记录：metax-task-success-filter-20261010-v1

<!-- 创建运行时复制为 runs/metax-task-success-filter-20261010-v1.md，替换占位项；不适用写明原因，未知写“未核实”。 -->

## 当前状态

- run_id：metax-task-success-filter-20261010-v1；负责人 /root；mx。
- 状态：实现和CPU验收完成；检查UTC 2026-10-10T14:13:13.372171+00:00。
- 方案：稳定性第二阶段2B，用户明确要求先修组资格；2A完整历史重放未执行。
- CPU回归198项通过；新增28项。GPU、真实生成和长期效果未验证。
- 实际训练global step／追加步数：0／0；真实评分题数：0；新checkpoint：无。
- 下一步：历史重放量化保留率/补抽成本，完成GPU前提后单变量对照。

## 可复现信息

- 分支 data-difficulty-muxi，基础commit f20278902082e2bfc28c7a48a8d58e34482b38f3；修复未提交，原有dirty文档和报告保留。
- 源码快照final-source/，哈希final-manifest.json；修复前backup/、baseline-manifest.json和baseline-dirty.diff。
- CPU命令：ssh mx "cd /mnt/public/code/lyk/lzy/R1-vllm-metax && CUDA_VISIBLE_DEVICES='' bash env/metax/run.sh /mnt/public/code/lyk/lzy/runs/metax-task-success-filter-20261010-v1/cpu_verify.final.py"，退出0。
- 实际配置核对命令：同SSH目录与env/metax/run.sh执行该产物目录config_compatibility.py，退出0。
- 设备：CPU，CUDA_VISIBLE_DEVICES为空；未加载7B权重或调用检索服务。真实actor/reference身份和GPU后端未在本次核验。
- 数据：CPU内存夹具；配置身份核对读取既有P/D文件哈希，模型大文件身份接口隔离，未使用T或生成D256。
- 实际旧配置来源：metax-process-r1-100-b32-gpu-20261008-v2/train.yaml；历史配置未修改。
- 新模式开关difficulty.dynamic_filter.eligibility=task_success_mixed；旧缺省reward_variance，规则版本与标签版本固定。
- 奖励、优势公式、学习率、KL、熵、采样和裁剪不变。旧checkpoint不可通过continue/branch切换资格。

## 运行位置及恢复

- 产物：/mnt/public/code/lyk/lzy/runs/metax-task-success-filter-20261010-v1。
- 日志：cpu-regression.attempt1.*（195项）、cpu-regression.final.*（198项）；config-compatibility.json、source-audit.json。
- CPU任务已完成，无新训练进程；启动前核查未发现main_ppo/cpu_verify存活。
- 实现开始UTC：2026-10-10T13:46:06.284292+00:00；最终检查UTC：2026-10-10T14:13:13.372171+00:00。
- 不适用训练恢复，无父checkpoint或新持久训练步数。新策略需要共同权重重启的新实验，严格恢复校验保留。
- 开启真实训练前重新核查进程、检索和checkpoint完整性；本次未启动。

## 阶段进度与证据

| 动作 | 状态 | 证据 |
| --- | --- | --- |
| 保存基线与原dirty内容 | 完成 | baseline-manifest.json / backup/ |
| 统一奖励分量、资格筛选和配置恢复接入 | 完成 | final-source/ / repair-only.patch |
| CPU首轮195项及最终198项 | 全部通过 | cpu-regression.attempt1.* / final.* |
| 实际旧配置兼容 | CPU通过，模型身份IO隔离 | config-compatibility.json |
| 函数与逻辑注释审查 | 48函数；97/97单元 | source-audit.json |
| 完整历史重放、GPU、长期对照 | 未执行 | 计划下一步 |

## 验证及结果

- 全量CPU198项通过，失败/错误/跳过均0；新增28项，test_fp16.py未运行。
- 覆盖全错惩罚差异、全成功、成功混合、门控失败、两种EM口径、版本/身份/布尔校验、重排、去补齐、完整补抽和无部分更新。
- 真实奖励入口与GRPO优势入口参与CPU测试；生成器模拟返回，无真实模型训练或评分。
- 原配置旧指纹/显式缺省一致，新模式身份变化；模板其余参数一致。实际模型完整性尚未核验。
- 逻辑单元97/97=100%中文说明，函数标签和关键逻辑分别核查；完整列表在实现记录/source-audit.json。
- 仅实现和CPU结论；补抽成本、有效题分布、GPU和后期退化改善尚未测量。

## 失败、变更与交接历史

| 事件 | 结果与保留证据 |
| --- | --- |
| 首轮25项新增回归 | 全量195项通过，attempt1日志保留 |
| 增加恢复入口/二值/去补齐3项 | 全量198项通过，final日志保留 |
| 审计传输引号冲突 | 源码未写入、非测试失败；audit-wrapper-attempt1.json |
| 分离清单后重跑审计 | 48函数无缺失，97逻辑单元，source-audit.json |
| 交接 | 原dirty文档保留；未提交/推送；下一步历史重放与GPU前提验收 |



## 2026-10-11T06:17:23.744369+00:00 本次提交前复验

CPU204项通过；证据 /mnt/public/code/lyk/lzy/runs/metax-grpo-bt-verification-20261011-v1/cpu-regression.final.json。准备按功能提交，无GPU启动。提交哈希由后续统一提交记录发布。
