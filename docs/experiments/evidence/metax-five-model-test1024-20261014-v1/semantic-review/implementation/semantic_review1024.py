"""T1024语义复核的CPU文件工具；只应用助手逐题裁定，不自动猜测语义。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timezone

POLICY = 'T1024-equivalence-v1'
MODELS = ['checkpoint80', 'base_qwen25_7b', 'official_grpo_v02', 'checkpoint60', 'official_ppo_v02']


def digest(value):
    """
    @brief 为裁定输入生成稳定摘要，防止跨题或标签变化后误用裁定。
    @param value 可JSON序列化的数据。
    @return 十六进制SHA256字符串。
    """
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def key(record):
    """
    @brief 使用题号、原标签及最终答案定位同一语义裁定。
    @param record 保存题号、标签及提取答案的逐题记录。
    @return 模型无关的裁定键字符串。
    """
    # 保留答案原文，禁止用包含匹配把未审阅的新答案自动判对。
    return digest([record['question_id'], record['target'], record['extracted_answer']])


def atomic_json(path, value):
    """
    @brief 原子写入复核产物，避免续跑读取半个JSON文件。
    @param path 输出Path对象。
    @param value 可JSON序列化的数据。
    @return 无。
    @note 仅写复核目录，临时文件在同目录替换。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(tmp, path)


def load_result(run, label):
    """
    @brief 只读取已完整生成的1024题结果。
    @param run 当前T1024运行目录Path对象。
    @param label 五模型之一的标签字符串。
    @return 完整结果字典，未完成时返回None。
    @raises ValueError 完成结果题量、题号或EM计数不符时抛出。
    """
    path = run / label / 'T1024/result.json'
    # 流式测试只有完整结果文件才进入正式复核汇总，活动批次不提前给完整分数。
    if not path.exists():
        return None
    result = json.loads(path.read_text(encoding='utf-8'))
    if not result.get('complete'):
        return None
    records = result['records']
    # 完整性及原始分数必须先验证，不能把部分结果包装为完整复核。
    if len(records) != 1024 or len({r['question_id'] for r in records}) != 1024:
        raise ValueError('题量或唯一题号异常')
    # 正式EM使用response-only奖励；legacy可能误匹配检索文段，不能代替正式结果。
    if sum(int(r['reward'] == 1) for r in records) != result['summary']['correct']:
        raise ValueError('逐题EM与原始汇总不一致')
    return result


def ingest(run, label, input_path):
    """
    @brief 录入助手已逐题阅读的错误答案裁定，保存到共享裁定库。
    @param run 当前T1024运行目录Path对象。
    @param label 已完成的模型标签。
    @param input_path 手工裁定JSON的Path对象。
    @return 本次录入裁定数整数。
    @raises ValueError 模型未完成、摘要变化、裁定缺失或跨模型冲突时抛出。
    @note 原始结果和标签保持不变；裁定需人工阅读后显式提供。
    """
    result = load_result(run, label)
    # 拒绝把完整模型裁定写入仍在生成的结果，保护输入身份及完整性。
    if result is None:
        raise ValueError('模型尚未完成')
    incoming = json.loads(input_path.read_text(encoding='utf-8'))
    # 裁定必须绑定逐题原记录，旧版本答案即使题号相同也不能直接沿用。
    if incoming['records_digest'] != digest(result['records']):
        raise ValueError('裁定输入与结果摘要不同')
    root = run / 'semantic-review'
    path = root / 'decisions.json'
    registry = json.loads(path.read_text()) if path.exists() else {'policy': POLICY, 'decisions': {}}
    # 独立口径不能混算，否则不同模型的语义分数失去可比性。
    if registry['policy'] != POLICY:
        raise ValueError('复核标准版本不同')
    by_row = {r['row']: r for r in result['records']}
    for decision in incoming['decisions']:
        record = by_row[decision['row']]
        # 仅受理实际被正式EM判错且最终答案原文相同的条目，保留原正确项。
        if record['reward'] != 0 or decision['answer'] != record['extracted_answer']:
            raise ValueError('裁定不是当前EM错题答案')
        # 输入只能使用已定义状态；无理由的裁定无法追溯，不予受理。
        if decision['verdict'] not in {'equivalent', 'incorrect', 'uncertain', 'label_issue'} or not decision['reason']:
            raise ValueError('裁定类别或理由不合法')
        token = key(record)
        saved = {'verdict': decision['verdict'], 'reason': decision['reason'],
                 'question_id': record['question_id'], 'question': record['question'],
                 'target': record['target'], 'answer': record['extracted_answer'],
                 'reviewer': 'Codex逐题审阅', 'reviewed_utc': datetime.now(timezone.utc).isoformat()}
        previous = registry['decisions'].get(token)
        # 相同题与答案在不同模型间必须保持一致，冲突需要显式复议。
        if previous and previous['verdict'] != saved['verdict']:
            raise ValueError('同题同答案裁定冲突，必须先复议')
        registry['decisions'][token] = saved
    atomic_json(path, registry)
    return len(incoming['decisions'])


def refresh(run):
    """
    @brief 为已完成模型生成待审队列、逐题记录和独立语义分数。
    @param run 当前T1024运行目录Path对象。
    @return 各模型复核进度列表。
    @raises ValueError 已完成结果完整性检查不通过时抛出。
    @note 只读取原结果；未审答案始终标记pending，不自动判错或判对。
    """
    root = run / 'semantic-review'
    path = root / 'decisions.json'
    registry = json.loads(path.read_text()) if path.exists() else {'policy': POLICY, 'decisions': {}}
    rows = []
    pending = []
    for label in MODELS:
        result = load_result(run, label)
        # 未完成模型保持等待；待审绝不能被当作已审错误来计算最终分数。
        if result is None:
            rows.append({'model': label, 'evaluation_complete': False, 'review_complete': False})
            continue
        judged = []
        counts = {'original_correct': 0, 'equivalent_added': 0, 'incorrect': 0, 'uncertain': 0, 'label_issue': 0, 'pending': 0}
        for record in result['records']:
            # 正式EM与独立语义加分分开计数，仅助手确认的equivalent增加正确数。
            original = int(record['reward'] == 1)
            decision = registry['decisions'].get(key(record)) if not original else None
            verdict = 'original_correct' if original else decision['verdict'] if decision else 'pending'
            counts['equivalent_added' if verdict == 'equivalent' else verdict] += 1
            entry = {k: record[k] for k in ['row', 'question_id', 'data_source', 'question', 'target', 'extracted_answer']}
            entry.update(original_em=original, semantic_correct=int(original or verdict == 'equivalent'), verdict=verdict,
                         reason='原始EM正确，保留原判' if original else decision['reason'] if decision else '尚未逐题复核')
            judged.append(entry)
            if verdict == 'pending':
                pending.append(dict(entry, model=label))
        complete = counts['pending'] == 0
        # 对未审完模型只给确认数量，semantic_accuracy留空，防止提前比较排名。
        summary = {'model': label, 'policy': POLICY, 'evaluation_complete': True, 'review_complete': complete,
                   'n': 1024, **counts, 'original_em': counts['original_correct'] / 1024,
                   'semantic_correct_confirmed': counts['original_correct'] + counts['equivalent_added'],
                   'semantic_accuracy': (counts['original_correct'] + counts['equivalent_added']) / 1024 if complete else None,
                   'records_digest': digest(result['records']), 'sources': {}}
        for source in ['nq', 'hotpotqa']:
            # 分来源分母取实际逐题记录，不假定配额或把未答题剔除。
            group = [v for v in judged if v['data_source'] == source]
            summary['sources'][source] = {'n': len(group), 'original_correct': sum(v['original_em'] for v in group),
                                         'semantic_correct': sum(v['semantic_correct'] for v in group)}
        model_root = root / label
        atomic_json(model_root / 'summary.json', summary)
        model_root.mkdir(parents=True, exist_ok=True)
        (model_root / 'judgments.jsonl').write_text(''.join(json.dumps(v, ensure_ascii=False) + '\n' for v in judged), encoding='utf-8')
        # 包含每个修正与争议的完整输入，读者可逐项复算；原始EM列独立展示。
        report = ['# T1024语义复核：' + label, '', '标准：' + POLICY,
                  '', '原始EM不变；只对明确等价的最终答案加分。标签错误、歧义、缺关键字段不计新增正确。',
                  '', json.dumps(summary, ensure_ascii=False, indent=2), '', '## EM错题逐项裁定', '']
        for item in judged:
            if item['original_em'] == 0:
                report.extend([f"### row {item['row']}：{item['verdict']}", item['question'],
                               '标准：' + json.dumps(item['target'], ensure_ascii=False),
                               '答案：' + str(item['extracted_answer']), '理由：' + item['reason'], ''])
        (model_root / 'review.md').write_text('\n'.join(report), encoding='utf-8')
        rows.append(summary)
    atomic_json(root / 'status.json', {'policy': POLICY, 'checked_utc': datetime.now(timezone.utc).isoformat(), 'models': rows})
    atomic_json(root / 'pending.json', pending)
    (root / 'pending.jsonl').write_text(''.join(json.dumps(v, ensure_ascii=False) + '\n' for v in pending), encoding='utf-8')
    return rows


def main():
    """
    @brief 接收命令行参数录入裁定或刷新待审队列。
    @return 无。
    @note 不导入深度学习库，不启动训练、推理、上传或子进程。
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--model', choices=MODELS)
    parser.add_argument('--ingest', type=Path)
    args = parser.parse_args()
    if args.ingest:
        # 录入必须显式指定模型；无录入参数时只刷新CPU文件产物。
        if not args.model:
            parser.error('--ingest需要--model')
        print('ingested', ingest(args.run, args.model, args.ingest))
    print(json.dumps(refresh(args.run), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
