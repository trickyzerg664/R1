# Search-R1 推理脚本

该脚本展示了 Search-R1 在推理阶段如何让大模型进行多轮：

```text
推理 → 搜索 → 获取信息 → 继续推理 → 最终回答
```

模型负责决定什么时候搜索、搜索什么内容，以及什么时候结束搜索并给出答案。

---

## 1. 模型与设备配置

```python
model_id = "PeterJinGo/SearchR1-nq_hotpotqa_train-qwen2.5-7b-em-ppo"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
```

指定要加载的 Search-R1 模型，并优先使用 GPU。

```python
tokenizer = transformers.AutoTokenizer.from_pretrained(model_id)

model = transformers.AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.float16,
    device_map="auto"
)
```

`tokenizer` 负责文本与 Token 之间的转换。

`AutoModelForCausalLM` 加载语言模型，使用 FP16 降低显存占用，`device_map="auto"` 自动分配模型设备。

---

## 2. Prompt 设计

```python
prompt = f"""Answer the given question. \
You must conduct reasoning inside <think> and </think> first every time you get new information. \
...
Question: {question}\n"""
```

Prompt 规定模型使用以下标签：

```text
<think>...</think>
<search>...</search>
<information>...</information>
<answer>...</answer>
```

其中：

* `<think>`：模型推理
* `<search>`：模型提出搜索请求
* `<information>`：Retriever 返回的信息
* `<answer>`：最终答案

这套标签定义了模型和搜索工具之间的交互方式。

---

## 3. 搜索结果拼接模板

```python
curr_search_template = \
    '\n\n{output_text}<information>{search_results}</information>\n\n'
```

当模型生成：

```text
<search>xxx</search>
```

后，程序会执行搜索，并把搜索结果拼接成：

```text
<search>xxx</search>

<information>
搜索结果
</information>
```

然后继续加入 `prompt`，供模型下一轮推理使用。

---

## 4. 自定义停止条件 `StopOnSequence`

```python
class StopOnSequence(transformers.StoppingCriteria):
```

该类用于让模型在生成：

```text
</search>
```

后立即暂停。

这是必要的，因为模型生成搜索请求后，需要由 Python 程序真正执行 Retriever，而不能让模型继续自行生成“搜索结果”。

### 初始化停止字符串

```python
self.target_ids = [
    tokenizer.encode(target_sequence, add_special_tokens=False)
    for target_sequence in target_sequences
]
```

将：

```text
</search>
```

等字符串转换成 Token ID。

模型生成过程本质上处理的是 Token，因此停止条件也通过 Token 判断。

### 判断是否需要停止

```python
for i, target in enumerate(targets):
    if torch.equal(
        input_ids[0, -self.target_lengths[i]:],
        target
    ):
        return True
```

每生成一个 Token，就检查当前序列末尾是否与某个 `</search>` Token 序列完全一致。

匹配成功后返回 `True`，`model.generate()` 停止。

---

## 5. 提取搜索 Query

```python
def get_query(text):
    pattern = re.compile(r"<search>(.*?)</search>", re.DOTALL)
    matches = pattern.findall(text)

    if matches:
        return matches[-1]
    else:
        return None
```

该函数从模型输出中提取：

```text
<search>...</search>
```

里面的搜索内容。

例如：

```text
<search>Mike Barnett CSKA Moscow</search>
```

得到：

```text
Mike Barnett CSKA Moscow
```

使用 `matches[-1]` 是因为完整上下文中可能存在多轮搜索，需要取得最新的一次。

---

## 6. 调用 Retriever

```python
def search(query: str):
    payload = {
        "queries": [query],
        "topk": 3,
        "return_scores": True
    }

    results = requests.post(
        "http://127.0.0.1:8000/retrieve",
        json=payload
    ).json()['result']
```

该函数将模型生成的 Query 发送给本地 Retriever。

其中：

```python
"topk": 3
```

表示返回最相关的 3 篇文档。

Retriever 服务运行在：

```text
127.0.0.1:8000
```

因此运行脚本前需要先启动对应的检索服务。

---

## 7. 整理搜索结果

```python
def _passages2string(retrieval_result):
    format_reference = ''

    for idx, doc_item in enumerate(retrieval_result):

        content = doc_item['document']['contents']

        title = content.split("\n")[0]
        text = "\n".join(content.split("\n")[1:])

        format_reference += \
            f"Doc {idx+1}(Title: {title}) {text}\n"

    return format_reference
```

Retriever 返回的是结构化数据，不适合直接提供给模型。

这里将每篇文档整理为：

```text
Doc 1(Title: xxx) 文档正文
Doc 2(Title: xxx) 文档正文
Doc 3(Title: xxx) 文档正文
```

其中：

```python
content.split("\n")[0]
```

取得第一行作为标题。

```python
"\n".join(content.split("\n")[1:])
```

取得剩余内容作为正文。

---

## 8. 创建停止条件

```python
target_sequences = [
    "</search>",
    " </search>",
    "</search>\n",
    " </search>\n",
    "</search>\n\n",
    " </search>\n\n"
]
```

设置多种 `</search>` 写法，是因为空格和换行可能导致 Tokenizer 产生不同的 Token 序列。

```python
stopping_criteria = transformers.StoppingCriteriaList([
    StopOnSequence(target_sequences, tokenizer)
])
```

将自定义停止规则交给 Transformers，在模型生成过程中自动调用。

---

## 9. Chat Template

```python
if tokenizer.chat_template:
    prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}],
        add_generation_prompt=True,
        tokenize=False
    )
```

如果模型定义了 Chat Template，则将普通 Prompt 转换成 Qwen 使用的对话格式。

大致类似：

```text
<|im_start|>user
问题
<|im_end|>

<|im_start|>assistant
```

这样输入格式与模型训练时保持一致。

---

## 10. 推理主循环

```python
while True:
```

整个 Search-R1 推理过程都在这个循环中完成。

每轮执行一次：

```text
模型生成
→ 判断是否结束
→ 如果需要搜索则调用 Retriever
→ 将结果加入 Prompt
→ 继续下一轮
```

---

### 10.1 编码 Prompt

```python
input_ids = tokenizer.encode(
    prompt,
    return_tensors='pt'
).to(device)

attention_mask = torch.ones_like(input_ids)
```

将当前完整 Prompt 转成模型需要的 Tensor。

`attention_mask` 全部为 1，表示当前所有 Token 都属于有效输入。

---

### 10.2 模型生成

```python
outputs = model.generate(
    input_ids,
    attention_mask=attention_mask,
    max_new_tokens=1024,
    stopping_criteria=stopping_criteria,
    pad_token_id=tokenizer.eos_token_id,
    do_sample=True,
    temperature=0.7
)
```

模型开始生成新的内容。

生成可能因为两种情况停止：

```text
1. 生成 </search>
2. 生成 EOS，表示整个回答结束
```

其中：

* `max_new_tokens=1024`：单轮最多生成 1024 个 Token
* `do_sample=True`：采用采样生成
* `temperature=0.7`：控制生成随机性

---

## 11. 判断是否已经完成回答

```python
if outputs[0][-1].item() in curr_eos:
```

检查最后一个 Token 是否为 Qwen 的结束 Token。

如果是，说明模型已经完成最终回答。

```python
generated_tokens = outputs[0][input_ids.shape[1]:]
output_text = tokenizer.decode(
    generated_tokens,
    skip_special_tokens=True
)

print(output_text)
break
```

`outputs` 中同时包含：

```text
原始输入 + 新生成内容
```

因此：

```python
outputs[0][input_ids.shape[1]:]
```

只取本轮模型新生成的部分。

---

## 12. 获取搜索请求

如果模型没有正常结束，通常说明它生成了：

```text
</search>
```

并被停止条件截断。

```python
tmp_query = get_query(
    tokenizer.decode(
        outputs[0],
        skip_special_tokens=True
    )
)
```

从当前完整输出中找到最新的 `<search>` 内容。

---

## 13. 执行搜索

```python
if tmp_query:
    search_results = search(tmp_query)
else:
    search_results = ''
```

如果成功提取 Query，就调用 Retriever。

例如：

```text
<search>
Mike Barnett hockey player CSKA Moscow
</search>
```

会被转换为 Retriever 请求。

---

## 14. 将搜索结果加入上下文

```python
search_text = curr_search_template.format(
    output_text=output_text,
    search_results=search_results
)

prompt += search_text
```

将本轮：

```text
模型输出
+
搜索结果
```

加入原来的 Prompt。

因此 Prompt 会逐渐变成：

```text
Question

<think>...</think>
<search>...</search>
<information>...</information>

<think>...</think>
<search>...</search>
<information>...</information>
```

下一轮模型能够看到之前所有推理和检索结果。

---

## 15. 整体数据流

整个程序可以简化为：

```text
Question
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
LLM
   ↓
...
   ↓
<answer>
```

本质上是：

```text
Reasoning
→ Search
→ Observation
→ Reasoning
→ ...
→ Final Answer
```

其中：

* 模型决定是否搜索以及搜索什么；
* Python 程序负责执行搜索；
* Retriever 提供外部知识；
* 搜索结果重新加入模型上下文；
* 最终模型根据累积信息生成答案。
