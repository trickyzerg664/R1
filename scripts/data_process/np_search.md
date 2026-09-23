# NQ 数据预处理脚本

该脚本用于将 NQ 数据集转换为 Search-R1 / verl 训练所需的数据格式，并保存为 Parquet 文件。

## 主要函数

### `make_prefix(dp, template_type)`

用于为原始问题构造模型输入 Prompt。

主要工作：

* 从 `dp['question']` 中读取问题；
* 根据 `template_type` 选择 Prompt 模板；
* 在 Prompt 中规定模型使用：

  * `<think>`：推理；
  * `<search>`：调用搜索；
  * `<answer>`：输出最终答案。

当前只支持：

```python
template_type = "base"
```

返回值为拼接完成后的完整问题 Prompt。

---

### `make_map_fn(split)`

用于生成 Hugging Face `Dataset.map()` 所需要的数据处理函数。

它本身不会直接处理数据，而是返回内部函数：

```python
process_fn(example, idx)
```

`split` 用于区分：

```text
train
test
```

例如：

```python
make_map_fn("train")
```

返回的处理函数会自动将：

```python
"split": "train"
```

写入 `extra_info`。

该函数定义在：

```python
if __name__ == "__main__":
```

内部，因此只在直接运行该脚本时使用，不作为模块的公共函数。

---

### `process_fn(example, idx)`

`process_fn` 是真正负责处理单条数据的函数。

主要步骤：

1. 清除问题首尾空格：

```python
example["question"] = example["question"].strip()
```

2. 如果问题没有以 `?` 结尾，则补充问号。

3. 调用：

```python
make_prefix(...)
```

生成完整 Prompt。

4. 将：

```python
example["golden_answers"]
```

转换为：

```python
{
    "target": example["golden_answers"]
}
```

供后续 Reward 计算使用。

5. 最终构造训练数据：

```python
{
    "data_source": "nq",
    "prompt": [...],
    "ability": "fact-reasoning",
    "reward_model": {...},
    "extra_info": {...}
}
```

---

## 主程序流程

脚本入口：

```python
if __name__ == "__main__":
```

主要执行以下步骤：

```text
解析命令行参数
        ↓
加载 NQ 数据集
        ↓
获取 train / test
        ↓
Dataset.map(process_fn)
        ↓
生成新的训练数据格式
        ↓
保存 train.parquet / test.parquet
        ↓
可选复制到 HDFS
```

核心处理代码：

```python
train_dataset = train_dataset.map(
    function=make_map_fn("train"),
    with_indices=True
)

test_dataset = test_dataset.map(
    function=make_map_fn("test"),
    with_indices=True
)
```

其中：

```python
with_indices=True
```

表示 `process_fn` 除了获得当前样本 `example`，还可以获得样本索引 `idx`。

---

## 输出

默认生成：

```text
./data/nq_search/
├── train.parquet
└── test.parquet
```

命令行参数：

```text
--local_dir      本地输出目录
--hdfs_dir       HDFS 输出目录，可选
--template_type  Prompt 类型，当前仅支持 base
```

整个脚本的核心关系可以概括为：

```text
make_prefix()
    ↓
负责构造 Prompt

make_map_fn()
    ↓
负责生成数据处理函数

process_fn()
    ↓
负责处理单条样本

Dataset.map()
    ↓
负责批量处理整个数据集

to_parquet()
    ↓
负责保存处理结果
```
