"""[data-difficulty] 正式题池冻结的独立 CPU 语义检查。"""
import unittest

import pandas as pd

from verl.experimental.difficulty.pool_preparation import freeze_splits, normalize_question, validate_splits


def example_frames():
    """包含跨 split 重复、训练内部重复和超长 prompt 的小型真实形状输入。"""
    train, test = [], []
    for source in ('nq', 'hotpotqa'):
        for number in range(9):
            text = f'{source} train question {number}?'
            train.append({'id': f'train-{source}-{number}', 'question': text, 'data_source': source,
                          'prompt': [{'role': 'user', 'content': 'long prompt' if number == 0 else 'ok'}]})
        for number in range(3):
            test.append({'id': f'test-{source}-{number}', 'question': f'{source} test question {number}?',
                         'data_source': source, 'prompt': [{'role': 'user', 'content': 'ok'}]})
    # 官方测试中的任何题都不得进入训练或开发，即使它没有被抽进最终 T。
    train.append({'id': 'leaked-test', 'question': 'NQ TEST QUESTION 2!', 'data_source': 'nq',
                  'prompt': [{'role': 'user', 'content': 'ok'}]})
    train.append({'id': 'duplicate', 'question': 'nq train question 1', 'data_source': 'nq',
                  'prompt': [{'role': 'user', 'content': 'ok'}]})
    return pd.DataFrame(train), pd.DataFrame(test)


class PoolPreparationTests(unittest.TestCase):
    def test_fixed_source_counts_and_disjointness(self):
        train, test = example_frames()
        sizes = {'P': 4, 'D': 2, 'T': 2}
        length = lambda prompt: len(prompt[0]['content'])
        frames, manifest = freeze_splits(train, test, sizes, length, 5, seed=42)
        validate_splits(frames, sizes)
        for part in sizes:
            self.assertEqual(frames[part]['data_source'].value_counts().to_dict(), {'nq': sizes[part] // 2,
                                                                                     'hotpotqa': sizes[part] // 2})
            self.assertTrue(all(entry['prompt_tokens'] <= 5 for entry in manifest['samples'][part]))
        self.assertTrue(all(str(value).startswith('test-') for value in frames['T']['id']))
        self.assertNotIn(normalize_question('nq test question 2'),
                         {normalize_question(value) for part in ('P', 'D') for value in frames[part]['question']})
        # 输入行顺序不应改变哈希抽样结果和正式清单身份。
        shuffled = train.sample(frac=1, random_state=7)
        again, _ = freeze_splits(shuffled, test.sample(frac=1, random_state=8), sizes, length, 5, seed=42)
        for part in sizes:
            self.assertEqual(list(frames[part]['question_id']), list(again[part]['question_id']))

    def test_capacity_and_overlap_fail_closed(self):
        train, test = example_frames()
        length = lambda prompt: len(prompt[0]['content'])
        with self.assertRaisesRegex(ValueError, 'Not enough eligible'):
            freeze_splits(train, test, {'P': 100, 'D': 2, 'T': 2}, length, 5)
        frames, _ = freeze_splits(train, test, {'P': 4, 'D': 2, 'T': 2}, length, 5)
        frames['D'].loc[0, 'question'] = frames['P'].loc[0, 'question']
        with self.assertRaisesRegex(ValueError, 'overlaps another split'):
            validate_splits(frames, {'P': 4, 'D': 2, 'T': 2})


if __name__ == '__main__':
    unittest.main()
