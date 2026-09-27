"""[data-difficulty] 从原始问答表确定性构建互斥的 P/D/T 题池。"""
import hashlib
import json
import re
import unicodedata


SOURCES = ('nq', 'hotpotqa')


def normalize_question(value):
    """统一 Unicode、大小写、标点和空白，用于跨来源与 split 去重。"""
    value = unicodedata.normalize('NFKC', str(value)).casefold()
    return ' '.join(re.sub(r'[^\w\s]', ' ', value).split())


def _digest(parts):
    return hashlib.sha256(json.dumps(parts, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def source_targets(total, source_counts):
    """按训练来源比例分配目标题数，余数以确定的来源顺序补齐。"""
    if total < 1 or not source_counts or any(n <= 0 for n in source_counts.values()):
        raise ValueError('Positive size and nonempty source counts are required')
    denominator = sum(source_counts.values())
    exact = {source: total * count / denominator for source, count in source_counts.items()}
    targets = {source: int(value) for source, value in exact.items()}
    remaining = total - sum(targets.values())
    for source in sorted(source_counts, key=lambda key: (-(exact[key] - targets[key]), key))[:remaining]:
        targets[source] += 1
    return targets


def _select(frame, split, targets, used_keys, token_length, max_prompt_length, seed):
    """哈希排序后按来源取足合法题；已用题和超长 prompt 不进入任何输出。"""
    selected_indices, details = [], []
    rejected_length = {source: 0 for source in SOURCES}
    for source in SOURCES:
        subset = frame.loc[frame['data_source'] == source]
        ranked = sorted(
            ((_digest([seed, split, source, str(row['id']), row['_question_key']]), index)
             for index, row in subset.iterrows()),
            key=lambda item: item[0],
        )
        accepted = 0
        for _, index in ranked:
            if accepted == targets[source]:
                break
            row = frame.loc[index]
            question_key = row['_question_key']
            if not question_key or question_key in used_keys:
                continue
            length = token_length(row['prompt'])
            if length > max_prompt_length:
                rejected_length[source] += 1
                continue
            used_keys.add(question_key)
            selected_indices.append(index)
            details.append({
                'question_id': _digest([source, split, str(row['id']), question_key]),
                'source': source,
                'origin_split': split,
                'original_id': str(row['id']),
                'question_hash': _digest(question_key),
                'prompt_tokens': int(length),
            })
            accepted += 1
        if accepted != targets[source]:
            raise ValueError(f'Not enough eligible {source} rows for {split}: {accepted}/{targets[source]}')
    output = frame.loc[selected_indices].drop(columns=['_question_key']).copy().reset_index(drop=True)
    output['question_id'] = [entry['question_id'] for entry in details]
    return output, details, rejected_length


def validate_splits(frames, sizes):
    """拒绝题目或永久 ID 重叠；核对实际行数，避免将部分切分当作正式清单。"""
    seen_questions, seen_ids = set(), set()
    for part in ('P', 'D', 'T'):
        frame = frames[part]
        if len(frame) != sizes[part]:
            raise ValueError(f'{part} has {len(frame)} rows, expected {sizes[part]}')
        if not set(frame['data_source']).issubset(SOURCES):
            raise ValueError(f'{part} contains an unsupported source')
        questions = {normalize_question(question) for question in frame['question']}
        identities = set(frame['question_id'])
        if len(questions) != len(frame) or len(identities) != len(frame):
            raise ValueError(f'{part} contains duplicate questions or IDs')
        if questions & seen_questions or identities & seen_ids:
            raise ValueError(f'{part} overlaps another split')
        seen_questions.update(questions)
        seen_ids.update(identities)


def freeze_splits(train, test, sizes, token_length, max_prompt_length, seed=42):
    """只接受原始 DataFrame 与 tokenizer 长度回调；算法不依赖 Ray/GPU/文件路径。

    T 从官方 test 选取；整个官方 test 的问题均从训练 split 排除。
    D 先于 P 从训练 split 选取，以免开发集与训练候选池交叉。
    """
    required = {'id', 'question', 'data_source', 'prompt'}
    for name, frame in (('train', train), ('test', test)):
        if not required.issubset(frame.columns):
            raise ValueError(f'{name} is missing required columns')
        if not frame.index.is_unique:
            raise ValueError(f'{name} row index must be unique')
    if set(sizes) != {'P', 'D', 'T'} or any(n < 1 for n in sizes.values()):
        raise ValueError('P/D/T sizes must all be positive')
    if max_prompt_length < 1:
        raise ValueError('max_prompt_length must be positive')

    # 测试题无论是否抽入 T 都不能进入 P/D，降低官方测试泄漏风险。
    test_keys = {normalize_question(value) for value in test['question']}
    train = train.loc[train['data_source'].isin(SOURCES)].copy()
    test = test.loc[test['data_source'].isin(SOURCES)].copy()
    train['_question_key'] = train['question'].map(normalize_question)
    test['_question_key'] = test['question'].map(normalize_question)
    counts = {source: int((train['data_source'] == source).sum()) for source in SOURCES}
    targets = {part: source_targets(size, counts) for part, size in sizes.items()}

    frames, entries, length_rejections = {}, {}, {}
    frames['T'], entries['T'], length_rejections['T'] = _select(
        test, 'test', targets['T'], set(), token_length, max_prompt_length, seed)
    used_train = set(test_keys)
    for part in ('D', 'P'):
        frames[part], entries[part], length_rejections[part] = _select(
            train, 'train', targets[part], used_train, token_length, max_prompt_length, seed)
    validate_splits(frames, sizes)
    return frames, {'schema_version': 1, 'seed': seed, 'sizes': sizes, 'source_targets': targets,
                    'max_prompt_length': max_prompt_length, 'length_rejections': length_rejections,
                    'samples': entries}
