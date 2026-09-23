

## 目录

- [1. fit() 的整体算法流程](#section-01)
- [2. Rollout：生成训练轨迹](#section-02)
- [3. old_log_probs：旧策略概率](#section-03)
- [4. PPO Ratio：新旧策略的概率比](#section-04)
- [5. Reference Policy 与 ref_log_probs](#section-05)
- [6. KL Penalty 与 KL Loss](#section-06)
- [7. Reward：评价生成结果](#section-07)
- [8. Reward、Return、Value、Advantage](#section-08)
- [9. Critic 与 Value Function](#section-09)
- [10. TD Error](#section-10)
- [11. GAE：广义优势估计](#section-11)
- [12. gamma 与 lambda 的作用](#section-12)
- [13. GRPO：组内相对 Advantage](#section-13)
- [14. GAE 与 GRPO 的区别](#section-14)
- [15. Critic Update](#section-15)
- [16. PPO Actor Update](#section-16)
- [17. PPO Clipping](#section-17)
- [18. PPO Clip 与 KL 的区别](#section-18)
- [19. State Masking](#section-19)
- [20. 完整参数更新链路](#section-20)
- [21. 代码与算法对应关系](#section-21)
- [22. 最需要掌握的核心公式](#section-22)
- [23. 最终总结](#section-23)

> VS Code 跳转说明：这些目录链接只指向 `Section-01`、`Section-02` 等纯 ASCII 标题，避免中文标题自动锚点规则差异。请在 Markdown Preview 中直接单击目录链接；在源码编辑器中使用 `Ctrl + 单击`。

---


## Section-01

### 1. fit() 的整体算法流程

`fit()` 本身主要负责调度。真正的 PPO、GAE、Critic 更新等算法分别在 `compute_advantage()`、`update_actor()`、`update_critic()` 等函数内部完成。

从算法角度，可以把整个 `fit()` 压缩成：

```text
训练数据
   ↓
Actor Rollout
   ↓
Trajectory
   ↓
old_log_probs
   ↓
Reference Policy → ref_log_probs
   ↓
Critic → values
   ↓
Reward Model / reward_fn
   ↓
KL Penalty（可选）
   ↓
Advantage Estimation
   ↓
Critic Update
   ↓
Actor Update
   ↓
PPO / GRPO Loss
   ↓
backward()
   ↓
optimizer.step()
   ↓
模型参数更新
```

最核心的强化学习闭环是：

```text
Rollout
   ↓
Reward
   ↓
Advantage
   ↓
Policy Update
```

---


## Section-02

### 2. Rollout：生成训练轨迹

普通 LLM rollout：

```python
if not self.config.do_search:
    gen_batch_output = self.actor_rollout_wg.generate_sequences(gen_batch)
```

Search-R1 Agent rollout：

```python
final_gen_batch_output = generation_manager.run_llm_loop(
    gen_batch=gen_batch,
    initial_input_ids=first_input_ids,
)
```

普通生成：

```text
Prompt
  ↓
Actor
  ↓
Response
```

Search-R1：

```text
Prompt
  ↓
LLM
  ↓
<think>
  ↓
<search>
  ↓
Retriever
  ↓
<information>
  ↓
继续推理
  ↓
最终答案
```

一条 RL trajectory 可以写成：

$$
(s_1,a_1,s_2,a_2,\ldots,s_T,a_T)
$$

其中：

- $s_t$：第 $t$ 步生成 token 之前的状态
- $a_t$：第 $t$ 步生成的 token，也就是 action
- $T$：trajectory 长度

因此在 LLM RL 中，可以简单理解为：

```text
生成一个 token
≈
执行一个 action
```

---


## Section-03

### 3. old_log_probs：旧策略概率

关键代码：

```python
with torch.no_grad():
    output = self.actor_rollout_wg.compute_log_prob(
        final_gen_batch_output
    )
    final_gen_batch_output = final_gen_batch_output.union(output)
```

得到：

```text
old_log_probs
```

对应：

$$
\log \pi_{\theta_{old}}(a_t|s_t)
$$

表示：

> rollout 当前 trajectory 时，旧 Actor 对实际生成 token 的概率。

例如旧 Actor 生成 token `Bell`：

$$
P_{old}(Bell|s_t)=0.4
$$

则：

$$
old\_log\_prob_t=\log(0.4)
$$

### 为什么不比较新旧模型重新生成的文本？

PPO 不会让新模型重新生成一条文本，然后和旧文本逐 token 比较。

它会固定旧模型已经生成的 action：

```text
Alexander | Graham | Bell
```

然后让更新后的 Actor 对同一组 action 重新计算概率。

例如：

```text
旧 Actor：
P(Bell | s_t) = 0.40

新 Actor：
P(Bell | s_t) = 0.48
```

所以 PPO 比较的是：

$$
\pi_{\theta_{old}}(a_t|s_t)
$$

和：

$$
\pi_{\theta}(a_t|s_t)
$$

核心原则：

```text
状态相同
Action 相同
只比较新旧策略对这个 Action 分配的概率
```

---


## Section-04

### 4. PPO Ratio：新旧策略的概率比

PPO 使用：

$$
r_t(\theta)=\frac{\pi_{\theta}(a_t|s_t)}{\pi_{\theta_{old}}(a_t|s_t)}
$$

因为程序保存的是 log probability，所以也可以写成：

$$
r_t(\theta)=\exp(\log \pi_{\theta}(a_t|s_t)-\log \pi_{\theta_{old}}(a_t|s_t))
$$

例如：

$$
P_{old}=0.40
$$

$$
P_{new}=0.48
$$

则：

$$
r_t=\frac{0.48}{0.40}=1.2
$$

说明：

```text
当前 Actor 对该 action 的概率
相比 rollout 时提高了 20%
```

因此：

```text
old_log_probs
      ↓
new_log_probs
      ↓
PPO ratio
      ↓
衡量这一次策略更新改变了多少
```

`old_log_probs` 不直接修改参数。

它通过以下链路间接影响参数：

```text
old_log_probs
      ↓
PPO ratio
      ↓
PPO Loss
      ↓
Gradient
      ↓
模型参数
```

---


## Section-05

### 5. Reference Policy 与 ref_log_probs

关键代码：

```python
if self.use_reference_policy:
    ref_log_prob = self.ref_policy_wg.compute_ref_log_prob(batch)
    batch = batch.union(ref_log_prob)
```

Reference Policy 计算：

$$
\log \pi_{ref}(a_t|s_t)
$$

Reference Model 一般是 RL 训练开始前冻结的原始模型。

```text
初始模型
   │
   ├── Actor
   │    持续更新
   │
   └── Reference Model
        参数冻结
```

### 三种概率的区别

| 概率 | 来源 | 主要作用 |
|---|---|---|
| `old_log_probs` | rollout 时的 Actor | PPO ratio |
| `new_log_probs` | 当前正在训练的 Actor | 参与 PPO Loss |
| `ref_log_probs` | 冻结 Reference Model | KL 约束 |

关系：

```text
                  Current Actor
                  new_log_prob
                  /          \
                 /            \
          PPO Ratio            KL
              /                 \
             ↓                   ↓
       old_log_prob         ref_log_prob
       rollout旧策略        冻结参考策略
```

---


## Section-06

### 6. KL Penalty 与 KL Loss

关键代码：

```python
if not self.config.actor_rollout_ref.actor.use_kl_loss:
    batch, kl_metrics = apply_kl_penalty(
        batch,
        kl_ctrl=self.kl_ctrl,
        kl_penalty=self.config.algorithm.kl_penalty
    )
else:
    batch.batch['token_level_rewards'] = \
        batch.batch['token_level_scores']
```

KL Divergence 用于衡量 Actor 和 Reference Policy 的差异。

标准定义：

$$
D_{KL}(\pi_{\theta}\|\pi_{ref})
=
\sum_a
\pi_{\theta}(a|s)
\log
\frac{\pi_{\theta}(a|s)}{\pi_{ref}(a|s)}
$$

为了提高 Markdown 兼容性，也可以把它写成一行：

$$D_{KL}(\pi_{\theta}\|\pi_{ref})=\sum_a \pi_{\theta}(a|s)\log\frac{\pi_{\theta}(a|s)}{\pi_{ref}(a|s)}$$

直观理解：

```text
KL 小
→ Actor 与原始模型行为接近

KL 大
→ Actor 已经明显偏离原始模型
```

### 6.1 KL 作为 Reward Penalty

当：

```python
use_kl_loss = False
```

代码调用：

```python
apply_kl_penalty(...)
```

概念上可以理解为：

$$
R'_t=R_t-\beta KL_t
$$

其中：

- $R_t$：任务 Reward
- $KL_t$：Actor 与 Reference 的偏差
- $\beta$：KL 惩罚系数

流程：

```text
原始 Reward
     ↓
减去 KL Penalty
     ↓
Final Reward
     ↓
Advantage
     ↓
Actor Loss
```

### 6.2 KL 直接作为 Loss

如果：

```python
use_kl_loss = True
```

`fit()` 本身不修改 reward。

概念上，Actor 更新阶段可能形成：

$$
L_{total}=L_{policy}+\beta L_{KL}
$$

流程：

```text
Policy Loss ─┐
             ├→ Total Loss → backward()
KL Loss ─────┘
```

具体形式需要继续查看 `update_actor()` 内部实现。

---


## Section-07

### 7. Reward：评价生成结果

关键代码：

```python
if self.use_rm:
    reward_tensor = self.rm_wg.compute_rm_score(batch)
    batch = batch.union(reward_tensor)

reward_tensor = self.reward_fn(batch)
batch.batch['token_level_scores'] = reward_tensor
```

Reward 可以来自：

```text
Reward Model
+
Rule-based Reward Function
```

例如 QA：

```text
Ground Truth: Paris
Model Answer: Paris
```

可以得到：

$$
R=1
$$

回答错误：

$$
R=0
$$

因此 Reward Model 不是必须的。

---


## Section-08

### 8. Reward、Return、Value、Advantage

这是理解 PPO 最重要的一组概念。

### 8.1 Reward

Reward 是某一步实际获得的奖励：

$$
r_t
$$

例如：

```text
中间步骤：reward = 0
最终回答正确：reward = 1
```

### 8.2 Return

Return 是从当前时刻开始未来累计能够获得的 Reward：

$$
G_t=r_t+\gamma r_{t+1}+\gamma^2r_{t+2}+\cdots
$$

假设：

```text
r1 = 0
r2 = 0
r3 = 0
r4 = 1
```

且：

$$
\gamma=0.9
$$

则：

$$
G_4=1
$$

$$
G_3=0.9
$$

$$
G_2=0.81
$$

$$
G_1=0.729
$$

即使 Reward 只出现在最后一步，前面的状态仍然具有未来价值。

### 8.3 Value

Critic 预测：

$$
V(s_t)
$$

表示：

```text
从当前状态继续执行策略，
预计未来能够获得多少 Return
```

### 8.4 Advantage

理论定义：

$$
A(s_t,a_t)=Q(s_t,a_t)-V(s_t)
$$

表示：

```text
当前 action
相比当前状态下一般水平
究竟好多少
```

如果：

$$
A_t>0
$$

则希望：

$$
\pi_{\theta}(a_t|s_t)\uparrow
$$

如果：

$$
A_t<0
$$

则希望：

$$
\pi_{\theta}(a_t|s_t)\downarrow
$$

---


## Section-09

### 9. Critic 与 Value Function

关键代码：

```python
if self.use_critic:
    values = self.critic_wg.compute_values(batch)
    batch = batch.union(values)
```

Critic 学习：

$$
V_{\phi}(s_t)
$$

例如：

```text
刚看到问题：
V(s1) = 0.3

已经找到关键证据：
V(s2) = 0.8
```

Critic 希望：

$$
V_{\phi}(s_t)\approx G_t
$$

因此 Critic 本质是：

```text
未来累计收益估计器
```

---


## Section-10

### 10. TD Error

TD Error：

$$
\delta_t=r_t+\gamma V(s_{t+1})-V(s_t)
$$

它表示：

```text
执行当前 action 后，
实际看到的下一步价值
相比 Critic 原来的预测
好多少或差多少
```

例如：

$$
V(s_t)=0.3
$$

$$
V(s_{t+1})=0.8
$$

$$
r_t=0
$$

$$
\gamma=1
$$

那么：

$$
\delta_t=0+0.8-0.3=0.5
$$

说明：

```text
执行这个 action 以后，
未来价值从 0.3 提升到了 0.8
```

因此这个 action 比原本预期更好。

---


## Section-11

### 11. GAE：广义优势估计

`fit()` 中：

```python
batch = compute_advantage(
    batch,
    adv_estimator=self.config.algorithm.adv_estimator,
    gamma=self.config.algorithm.gamma,
    lam=self.config.algorithm.lam,
    num_repeat=self.config.actor_rollout_ref.rollout.n
)
```

如果：

```text
adv_estimator = GAE
```

先计算 TD Error：

$$
\delta_t=r_t+\gamma V(s_{t+1})-V(s_t)
$$

然后计算 GAE：

$$
A_t=\delta_t+\gamma\lambda\delta_{t+1}+(\gamma\lambda)^2\delta_{t+2}+\cdots
$$

递归形式：

$$
A_t=\delta_t+\gamma\lambda A_{t+1}
$$

GAE 的作用是：

```text
把后面的 Reward / TD 信息
向前传播到之前的 action
```

### 为什么最终 Reward 可以训练前面的 token？

假设：

```text
a1
a2
a3
a4
```

只有最后一步得到：

```text
r1 = 0
r2 = 0
r3 = 0
r4 = 1
```

通过 Value 和 GAE，可以得到：

```text
a1 → A1
a2 → A2
a3 → A3
a4 → A4
```

因此不是只有最后一个 token 被训练。

这就是：

```text
Credit Assignment
```

即：

> 最终结果产生以后，要把“功劳或责任”分配给前面的 action。

---


## Section-12

### 12. gamma 与 lambda 的作用

### gamma

Return：

$$
G_t=r_t+\gamma r_{t+1}+\gamma^2r_{t+2}+\cdots
$$

$\gamma$ 控制：

```text
未来 Reward 的重要程度
```

### lambda

GAE：

$$
A_t=\delta_t+\gamma\lambda\delta_{t+1}+(\gamma\lambda)^2\delta_{t+2}+\cdots
$$

$\lambda$ 控制：

```text
当前 Advantage
需要参考多远的未来 TD Error
```

简单记：

```text
gamma：
未来 Reward 打多少折

lambda：
未来 TD Error 参考多少
```

---


## Section-13

### 13. GRPO：组内相对 Advantage

`fit()` 没有把 Advantage 算法写死：

```python
adv_estimator=self.config.algorithm.adv_estimator
```

而且 `_balance_batch()` 的注释明确提到了：

```text
GRPO
RLOO
```

GRPO 的核心思想是：

```text
同一个问题生成多个 response
       ↓
比较它们的 Reward
       ↓
根据组内相对表现计算 Advantage
```

例如：

```text
Response A → Reward = 1.0
Response B → Reward = 0.8
Response C → Reward = 0.2
Response D → Reward = 0.0
```

组内均值：

$$
\mu_R=\frac{1}{G}\sum_{i=1}^{G}R_i
$$

一种常见的标准化形式：

$$
A_i=\frac{R_i-\mu_R}{\sigma_R+\epsilon}
$$

于是：

```text
高于组内平均
→ Advantage > 0

低于组内平均
→ Advantage < 0
```

GRPO 不依赖独立 Critic 来建立 baseline，而是使用：

```text
同一道题的其他 rollout
```

作为相对参照。

---


## Section-14

### 14. GAE 与 GRPO 的区别

### PPO + GAE

```text
Reward
   +
Critic V(s)
   ↓
TD Error
   ↓
GAE
   ↓
每个 timestep 的 Advantage
   ↓
PPO Update
```

特点：

- 使用 Critic
- baseline 来自 $V(s)$
- Advantage 可以随 timestep 不同
- 需要训练 Value Model

### GRPO

```text
同一道 Question
       ↓
多个 Response
       ↓
R1 R2 R3 ...
       ↓
组内比较
       ↓
A1 A2 A3 ...
       ↓
Policy Update
```

特点：

- 通常不需要独立 Critic
- baseline 来自 group reward
- 减少 Value Model 的显存和计算开销
- 依赖同一问题多个 rollout

---


## Section-15

### 15. Critic Update

关键代码：

```python
if self.use_critic:
    critic_output = self.critic_wg.update_critic(batch)
```

Critic 的训练目标是让：

$$
V_{\phi}(s_t)
$$

更接近目标 Return。

最基本的 Value Loss：

$$
L_V=(V_{\phi}(s_t)-\hat{G}_t)^2
$$

例如：

$$
V_{\phi}(s_t)=0.3
$$

目标：

$$
\hat{G}_t=0.9
$$

则：

$$
L_V=(0.3-0.9)^2=0.36
$$

更新过程：

```text
Value Loss
   ↓
backward()
   ↓
Critic Gradient
   ↓
optimizer.step()
   ↓
Critic 参数更新
```

---


## Section-16

### 16. PPO Actor Update

关键代码：

```python
actor_output = self.actor_rollout_wg.update_actor(batch)
```

Actor 更新需要：

```text
old_log_probs
new_log_probs
advantages
loss_mask
可能还有 KL
```

首先计算：

$$
r_t(\theta)=\frac{\pi_{\theta}(a_t|s_t)}{\pi_{\theta_{old}}(a_t|s_t)}
$$

最基本的 Policy Gradient 可以理解为：

$$
L_{PG}=-r_t(\theta)A_t
$$

因此：

$$
A_t>0
$$

会推动：

$$
\pi_{\theta}(a_t|s_t)\uparrow
$$

而：

$$
A_t<0
$$

会推动：

$$
\pi_{\theta}(a_t|s_t)\downarrow
$$

---


## Section-17

### 17. PPO Clipping

标准 PPO clipped objective：

$$
L^{CLIP}
=
\min
\left(
r_t(\theta)A_t,
\operatorname{clip}(r_t(\theta),1-\epsilon,1+\epsilon)A_t
\right)
$$

如果你的 Markdown Preview 对上面的多行公式显示不稳定，可以使用完全等价的一行版本：

$$L^{CLIP}=\min(r_t(\theta)A_t,\operatorname{clip}(r_t(\theta),1-\epsilon,1+\epsilon)A_t)$$

训练时通常最小化负目标：

$$
L_{actor}=-L^{CLIP}
$$

假设：

$$
\epsilon=0.2
$$

那么 ratio 的主要限制范围大约为：

$$
[0.8,1.2]
$$

### 正 Advantage

如果：

$$
A_t>0
$$

说明 action 好。

假设：

$$
P_{old}=0.4
$$

$$
P_{new}=0.8
$$

那么：

$$
r_t=2
$$

变化太大。

Clip 后：

$$
\operatorname{clip}(2,0.8,1.2)=1.2
$$

含义：

```text
好 action 可以提高概率
但一次 PPO Update 不应该提高得过猛
```

### 负 Advantage

如果：

$$
A_t<0
$$

说明 action 较差。

PPO 会降低它的概率，但同样限制：

```text
不能一次降得过猛
```

所以 PPO 的核心思想是：

```text
每轮对 Policy 做相对保守的小更新
```

---


## Section-18

### 18. PPO Clip 与 KL 的区别

### PPO Clip

比较：

$$
\pi_{\theta}
\quad vs \quad
\pi_{\theta_{old}}
$$

关注：

```text
这一轮 PPO Update
相比 rollout 时是否变化过大
```

属于：

```text
短期约束
```

### KL

比较：

$$
\pi_{\theta}
\quad vs \quad
\pi_{ref}
$$

关注：

```text
整个 RL 训练过程中
Actor 是否已经偏离原始模型太远
```

属于：

```text
长期约束
```

可以记成：

```text
                     Current Actor
                    /             \
                   /               \
              PPO Clip              KL
                 /                   \
                ↓                     ↓
            Old Actor            Reference
          当前rollout策略        初始冻结模型
```

---


## Section-19

### 19. State Masking

Search-R1 在更新 Actor 前：

```python
if self.config.do_search and \
        self.config.actor_rollout_ref.actor.state_masking:

    batch, metrics = self._create_loss_mask(batch, metrics)
```

原因是 Agent trajectory 中并非所有 token 都由 Actor 生成。

例如：

```text
<think>
需要搜索电话发明者
</think>

<search>
telephone inventor
</search>

<information>
Alexander Graham Bell ...
</information>

<answer>
Alexander Graham Bell
</answer>
```

其中：

```text
<think>
<search>
<answer>
```

属于 Actor action。

但是：

```text
<information>
```

属于 Retriever / Environment 返回的 observation。

因此可以使用：

```text
<think>           mask = 1
reasoning         mask = 1

<search>          mask = 1
query             mask = 1

<information>     mask = 0
retrieval result  mask = 0

<answer>          mask = 1
answer token      mask = 1
```

Actor Loss 可以概念化为：

$$
L=\frac{\sum_t M_tL_t}{\sum_tM_t}
$$

其中：

$$
M_t\in\{0,1\}
$$

这样只有真正属于 Actor 的 action token 才参与 Policy Gradient。

---


## Section-20

### 20. 完整参数更新链路

```text
Actor Rollout
      ↓
Trajectory
      ↓
old_log_probs
      │
      ├────────────────────┐
      │                    │
      ▼                    ▼
Reference Policy         Critic
      │                    │
ref_log_probs           V(s_t)
      │                    │
      ▼                    │
     KL                    │
      │                    │
      └────────┐     ┌─────┘
               ▼     ▼
                 Reward
                    │
                    ▼
           Advantage Estimation
              /           \
             /             \
           GAE             GRPO
            │               │
            ▼               ▼
      timestep A_t      group A_i
             \             /
              \           /
               └────┬────┘
                    ▼
              update_actor()
                    │
                    ▼
              new_log_probs
                    │
                    ▼
         ratio = exp(new - old)
                    │
                    ▼
                PPO Clip
                    │
                    ▼
               Policy Loss
                    │
             + KL Loss（可选）
                    │
                    ▼
                Total Loss
                    │
                    ▼
                backward()
                    │
                    ▼
                gradients
                    │
                    ▼
             optimizer.step()
                    │
                    ▼
                新 Actor
```

---


## Section-21

### 21. 代码与算法对应关系

| `fit()` 代码 | 算法概念 | 作用 |
|---|---|---|
| `generate_sequences()` | Policy Rollout | 普通 LLM 采样 |
| `run_llm_loop()` | Agent Rollout | LLM 与 Search 多轮交互 |
| `compute_log_prob()` | Old Policy Probability | 保存 `old_log_probs` |
| `compute_ref_log_prob()` | Reference Policy | 为 KL 提供参考概率 |
| `compute_values()` | Value Function | Critic 估计 $V(s_t)$ |
| `compute_rm_score()` | Reward Model | 模型式 Reward |
| `reward_fn()` | Rule-based Reward | 任务结果奖励 |
| `apply_kl_penalty()` | KL Regularization | Reward 层面的 KL 惩罚 |
| `compute_advantage()` | GAE / GRPO / RLOO | Reward 转化为 Advantage |
| `update_critic()` | Value Regression | 更新 Critic |
| `_create_loss_mask()` | Action Masking | 排除 Environment token |
| `update_actor()` | PPO / Policy Optimization | 更新 Actor 参数 |

---


## Section-22

### 22. 最需要掌握的核心公式

### 22.1 Return

$$
G_t=r_t+\gamma r_{t+1}+\gamma^2r_{t+2}+\cdots
$$

### 22.2 TD Error

$$
\delta_t=r_t+\gamma V(s_{t+1})-V(s_t)
$$

### 22.3 GAE

$$
A_t=\delta_t+\gamma\lambda\delta_{t+1}+(\gamma\lambda)^2\delta_{t+2}+\cdots
$$

### 22.4 PPO Ratio

$$
r_t(\theta)=\frac{\pi_{\theta}(a_t|s_t)}{\pi_{\theta_{old}}(a_t|s_t)}
$$

### 22.5 PPO Clip

$$
L^{CLIP}=\min(r_t(\theta)A_t,\operatorname{clip}(r_t(\theta),1-\epsilon,1+\epsilon)A_t)
$$

### 22.6 Critic Loss

$$
L_V=(V_{\phi}(s_t)-\hat{G}_t)^2
$$

### 22.7 GRPO Group Advantage

$$
\mu_R=\frac{1}{G}\sum_{i=1}^{G}R_i
$$

$$
A_i=\frac{R_i-\mu_R}{\sigma_R+\epsilon}
$$

### 22.8 KL Reward Penalty

$$
R'_t=R_t-\beta KL_t
$$

---


## Section-23

### 23. 最终总结

`RayPPOTrainer.fit()` 的算法本质可以总结为四步：

### 第一步：生成

```text
Actor
  ↓
Rollout
  ↓
Trajectory
```

### 第二步：评价

```text
Trajectory
   ↓
Reward
```

### 第三步：信用分配

PPO + GAE：

```text
Reward
+
Critic Value
   ↓
TD Error
   ↓
GAE
   ↓
Advantage
```

GRPO：

```text
同一道题多个 Response
        ↓
Group Reward
        ↓
Relative Advantage
```

### 第四步：受约束地更新 Actor

```text
Advantage
   ↓
决定概率升还是降

old_log_probs
   ↓
PPO Ratio
   ↓
PPO Clip
   ↓
限制单次更新幅度

ref_log_probs
   ↓
KL
   ↓
限制长期偏离 Reference
```

最终：

```text
Reward
→ 判断最终结果好不好

Advantage
→ 判断哪些 action 应增强或削弱

old_log_probs
→ 衡量本轮策略改变了多少

PPO Clip
→ 限制单次更新不能过猛

ref_log_probs
→ 提供冻结的参考策略

KL
→ 防止长期训练后偏离原模型过远

Critic
→ 预测未来 Return

GAE
→ 把最终结果的影响分配给前面的 action

GRPO
→ 用组内相对 Reward 替代 Critic baseline

State Masking
→ 只训练真正属于 Actor 的 action token
```

最终整个算法闭环就是：

```text
生成
  ↓
评价
  ↓
信用分配
  ↓
受约束的策略更新
  ↓
新的 Actor
```
