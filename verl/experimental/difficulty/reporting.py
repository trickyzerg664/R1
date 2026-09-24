"""[data-difficulty] 纯结果计算：五档迁移和逐步指标展开，与训练进程解耦。"""
from .sampling import validate_labels


def migration(old_payload, new_payload, rows):
    # 两次标签必须对应同一完整题池，按永久 ID 配对而非按文件排列位置配对。
    """输出旧 k 到新 k 的 5×5 计数及行归一化比例。
    空行比例置零；两次评分题池不同或标签不完整时拒绝生成比较结果。
    """
    old = validate_labels(old_payload, rows)
    new = validate_labels(new_payload, rows)
    counts = [[0] * 5 for _ in range(5)]
    for identity, record in old.items():
        counts[record['k']][new[identity]['k']] += 1
    proportions = [[n / sum(row) if sum(row) else 0. for n in row] for row in counts]
    return {'counts': counts, 'row_proportions': proportions}


def metric_rows(events):
    # 保留事件顺序及重复 step；恢复后的多次尝试不应在汇总中被静默覆盖。
    """把训练和最终评价事件展平成表格行，保留时间顺序及重复 step。
    不自动把不同 run 的同一步骤合并，也不把尚未结束的尝试当作最终结果。
    """
    result = []
    for event in events:
        if event.get('event') not in ('train', 'final_validation'):
            continue
        result.append({**{key: value for key, value in event.items() if key != 'metrics'},
                       **event.get('metrics', {})})
    return result
