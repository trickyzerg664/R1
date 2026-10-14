"""CPU回归：保证原EM不变、缺失答案不借用legacy、未审保持待审及跨模型一致。"""
import hashlib
import json
import tempfile
from pathlib import Path
import semantic_review1024 as review


def expect_failure(action, message):
    """
    @brief 验证明确错误输入被拒绝。
    @param action 无参数可调用对象。
    @param message 缺少拒绝时的断言说明。
    @return 无。
    @raises AssertionError 操作未抛出ValueError时抛出。
    """
    try:
        action()
    except ValueError:
        return
    raise AssertionError(message)


def main():
    """
    @brief 用完整题量的临时CPU夹具验证复核文件流程安全边界。
    @return 无。
    @note 临时目录自动清理；不读取真实模型、不调用GPU。
    """
    with tempfile.TemporaryDirectory() as directory:
        run = Path(directory)
        records = []
        for row in range(1024):
            # 额外legacy命中模拟工具文段污染，正式response-only分数仍应为0。
            records.append({'row': row, 'question_id': str(row), 'question': 'CPU夹具',
                            'target': ['one'], 'extracted_answer': None if row == 1 else '1',
                            'reward': int(row == 0), 'legacy_reward': int(row in (0, 1)),
                            'data_source': 'nq' if row < 335 else 'hotpotqa'})
        result = {'complete': True, 'records': records, 'summary': {'correct': 1}}
        for model in review.MODELS[:2]:
            review.atomic_json(run / model / 'T1024/result.json', result)
        original = run / 'checkpoint80/T1024/result.json'
        before = hashlib.sha256(original.read_bytes()).hexdigest()
        decisions = [{'row': 1, 'answer': None, 'verdict': 'incorrect', 'reason': '无最终答案'},
                     {'row': 2, 'answer': '1', 'verdict': 'equivalent', 'reason': '夹具预先给定人工裁定'}]
        input_path = run / 'input.json'
        review.atomic_json(input_path, {'records_digest': review.digest(records), 'decisions': decisions})
        review.ingest(run, 'checkpoint80', input_path)
        rows = review.refresh(run)
        # 未审答案不能被静默记错、完整标记不能提前给出；同题同答案跨模型复用。
        for row in rows[:2]:
            assert row['original_correct'] == 1
            assert row['equivalent_added'] == 1
            assert row['pending'] == 1021
            assert row['review_complete'] is False and row['semantic_accuracy'] is None
        assert hashlib.sha256(original.read_bytes()).hexdigest() == before
        # 同一裁定键禁止跨模型矛盾，不允许以不同模型名称覆盖已有结果。
        decisions[1]['verdict'] = 'incorrect'
        review.atomic_json(input_path, {'records_digest': review.digest(records), 'decisions': decisions})
        expect_failure(lambda: review.ingest(run, 'base_qwen25_7b', input_path), '裁定冲突应拒绝')
        review.atomic_json(input_path, {'records_digest': 'stale', 'decisions': []})
        expect_failure(lambda: review.ingest(run, 'checkpoint80', input_path), '旧结果摘要应拒绝')
        # 完成标记存在但题量或汇总错误时仍必须拒绝，保护伪完整文件场景。
        result['summary']['correct'] = 2
        review.atomic_json(original, result)
        expect_failure(lambda: review.load_result(run, 'checkpoint80'), '错误EM汇总应拒绝')
        result['summary']['correct'] = 1
        result['records'] = records[:-1]
        review.atomic_json(original, result)
        expect_failure(lambda: review.load_result(run, 'checkpoint80'), '缺失题目应拒绝')
    print(json.dumps({'cpu_regression': 'passed', 'checks': ['response_only_em', 'raw_immutable',
                     'pending_not_complete', 'cross_model_reuse', 'conflict_rejected',
                     'stale_digest_rejected', 'summary_rejected', 'missing_rows_rejected']}))


if __name__ == '__main__':
    main()
