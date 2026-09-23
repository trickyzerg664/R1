1. 函数作用

run_llm_loop() 是 Search-R1 中负责执行多轮 LLM rollout 的核心控制函数。

整体过程可以概括为：

原始问题
  ↓
LLM 生成 response
  ↓
解析 search / answer 等动作
  ↓
环境执行动作
  ↓
返回 observation
  ↓
拼接到上下文
  ↓
继续下一轮 LLM 生成
  ↓
直到得到最终答案或达到最大轮数

它主要负责：

管理 batch 中多条 trajectory 的运行状态；

只让尚未结束的样本继续参与生成；

执行模型生成的搜索动作；

将搜索结果加入下一轮上下文；

保存完整 rollout trajectory；

统计 turn、合法动作和搜索次数；

达到最大轮数后执行一次禁止搜索的最终生成。

2. 关键变量

original_left_side

original_left_side = {
    'input_ids': initial_input_ids[:, -self.config.max_start_length:]
}

保存原始 prompt。

只保留最后 max_start_length 个 token，最终用于构造训练样本。

original_right_side

original_right_side = {
    'responses': initial_input_ids[:, []],
    'responses_with_info_mask': initial_input_ids[:, []]
}

初始化一个形状为：

[batch_size, 0]

的空 Tensor。

后续不断向其中追加：

LLM response
→ observation
→ LLM response
→ observation
...

它主要用于保存完整的 rollout trajectory。

active_mask

active_mask = torch.ones(
    gen_batch.batch['input_ids'].shape[0],
    dtype=torch.bool
)

表示 batch 中哪些 trajectory 仍未结束。

例如：

[True, False, True, False]

表示：

样本0：继续
样本1：已结束
样本2：继续
样本3：已结束

已经结束的样本不会再次送入 LLM，从而减少不必要的 GPU 计算。

rollings

rollings = gen_batch

rollings 保存当前真正送给 LLM 的完整上下文。

最开始可能只有：

Question

搜索一轮后变成：

Question

<think>...</think>
<search>...</search>

<information>
搜索结果
</information>

下一轮模型会基于这个更新后的上下文继续生成。

因此：

rollings = 当前工作状态
original_right_side = 最终 trajectory 记录

3. 统计变量

turns_stats
valid_action_stats
valid_search_stats
active_num_list

分别用于统计：

turns_stats
    每条 trajectory 经历的轮数

valid_action_stats
    合法 action 的数量

valid_search_stats
    合法 search 的数量

active_num_list
    每一轮结束后还剩多少 active trajectory

例如：

ACTIVE_TRAJ_NUM: [64, 50, 27, 8, 0]

表示随着推理进行，trajectory 正逐步结束。

4. 主循环

for step in range(self.config.max_turns):

最多执行 max_turns 轮搜索 / 推理交互。

如果所有 trajectory 都已经结束：

if not active_mask.sum():
    break

则提前结束。

5. 裁剪无效 Padding

rollings.batch = self.tensor_fn.cut_to_effective_len(
    rollings.batch,
    keys=['input_ids', 'attention_mask', 'position_ids']
)

去掉 batch 尾部无用 padding，减少模型推理时的计算量。

6. 只生成 active trajectory

rollings_active = DataProto.from_dict({
    k: v[active_mask]
    for k, v in rollings.batch.items()
})

如果：

active_mask = [True, False, True, False]

那么实际送入模型的只有：

样本0
样本2

然后调用：

gen_output = self._generate_with_gpu_padding(rollings_active)

执行一次 LLM generation。

7. 处理模型输出

responses_ids, responses_str = self._postprocess_responses(
    gen_output.batch['responses']
)

得到：

responses_ids
    模型输出的 token ids

responses_str
    模型输出的字符串

随后：

responses_ids, responses_str = self.tensor_fn._example_level_pad(
    responses_ids,
    responses_str,
    active_mask
)

将只包含 active 样本的生成结果重新恢复为完整 batch 大小，保证后续所有 Tensor 的 batch 维度一致。

8. 执行模型动作

next_obs, dones, valid_action, is_search = self.execute_predictions(
    responses_str,
    self.tokenizer.pad_token,
    active_mask
)

execute_predictions() 会解析模型输出。

例如模型生成：

<search>Obama birthplace</search>

环境执行搜索后返回：

next_obs
    搜索结果等环境 observation

dones
    当前 trajectory 是否结束

valid_action
    当前动作是否合法

is_search
    当前动作是否为搜索

例如：

dones = [False, True, False]

表示第二条 trajectory 已经完成。

9. 更新 active_mask

curr_active_mask = torch.tensor(
    [not done for done in dones],
    dtype=torch.bool
)

active_mask = active_mask * curr_active_mask

本质上相当于：

active_mask = active_mask & curr_active_mask

也就是说：

trajectory 一旦结束，后续不会重新变成 active。

同时更新统计信息：

turns_stats[curr_active_mask] += 1
valid_action_stats += torch.tensor(valid_action)
valid_search_stats += torch.tensor(is_search)

10. 将 observation 转为 Token

next_obs_ids = self._process_next_obs(next_obs)

环境返回的搜索结果最初是字符串，例如：

<information>
Barack Obama was born in Honolulu...
</information>

这里将其编码为 token ids，供下一轮 LLM 使用。

11. 更新下一轮上下文

rollings = self._update_rolling_state(
    rollings,
    responses_ids,
    next_obs_ids
)

假设原始上下文为：

Question

当前模型输出：

<think>需要搜索</think>
<search>xxx</search>

环境返回：

<information>yyy</information>

更新后：

Question
<think>需要搜索</think>
<search>xxx</search>
<information>yyy</information>

下一轮 LLM 就基于这个完整上下文继续生成。

12. 保存完整 trajectory

original_right_side = self._update_right_side(
    original_right_side,
    responses_ids,
    next_obs_ids
)

这一步与更新 rollings 类似，但目的不同：

rollings
    用于下一轮 LLM inference

original_right_side
    用于最终保存完整 rollout

最终可能记录：

response1
information1
response2
information2
response3

这些数据后续会参与 GRPO 的 reward、advantage 和 loss 计算。

13. Final LLM Rollout

如果执行完 max_turns 后仍然存在 active trajectory：

if active_mask.sum():

会再进行一次最终生成。

与普通生成最大的区别是：

self.execute_predictions(
    ...,
    do_search=False
)

即：

最后一轮禁止继续搜索

目的是防止模型达到最大搜索轮数后仍不断生成 <search>。

最后一轮只保存模型 response：

original_right_side = self._update_right_side(
    original_right_side,
    responses_ids
)

因为 rollout 即将结束，不再需要把 observation 拼回下一轮上下文。

14. 整理最终结果

最后将统计信息写入：

meta_info

包括：

meta_info['turns_stats']
meta_info['active_mask']
meta_info['valid_action_stats']
meta_info['valid_search_stats']

最终：

return self._compose_final_output(
    original_left_side,
    original_right_side,
    meta_info
)

将：

原始 prompt
+
完整 rollout trajectory
+
统计信息

组合成最终训练数据。

15. 整体数据流

                 rollings
                    │
                    ▼
                   LLM
                    │
                    ▼
             responses_ids
                    │
                    ▼
          execute_predictions
                    │
              search / answer
                    │
                    ▼
              next_obs_ids
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
_update_rolling_state   _update_right_side
          │                   │
          ▼                   ▼
 下一轮 LLM 上下文       保存完整 trajectory