"""CPU验证：真实奖励入口、旧模式兼容、完整评价记录和版本边界。"""
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
import torch
from verl import DataProto
from verl.trainer.main_ppo import RewardManager
from verl.utils.reward_score import qa_em
from verl.utils.reward_score.answer_audit import make_record, append_records


class Tokenizer:
    def decode(self, ids, **kwargs):
        return ''.join(chr(int(i)) for i in ids if int(i))


def batch(response, target='Paris', environment=''):
    # 用字符token构造真实DataProto，环境中的答案标签必须被屏蔽。
    prompt = 'Use <answer> and </answer>. Example <answer>Beijing</answer>.'
    full = response + environment
    responses = [ord(c) for c in full] or [0]
    mask = [1] * len(response) + [0] * len(environment) or [0]
    return DataProto.from_dict(
        {'prompts': torch.tensor([[ord(c) for c in prompt]]),
         'responses': torch.tensor([responses]),
         'attention_mask': torch.tensor([[1]*len(prompt)+[1]*len(full)+([0] if not full else [])]),
         'info_mask': torch.tensor([[1]*len(prompt)+mask])},
        non_tensors={'reward_model': np.array([{'ground_truth': {'target': [target]}}], dtype=object),
                     'data_source': np.array(['nq'], dtype=object)},
        meta_info={'evaluation_step': 50})


class RewardBoundaryTests(unittest.TestCase):
    def test_single_answer(self):
        self.assertEqual(qa_em.extract_solution('<answer>Paris</answer>', 'response_only_v1'), 'Paris')

    def test_no_answer(self):
        self.assertIsNone(qa_em.extract_response_answer('<search>Paris</search>'))

    def test_nested_innermost(self):
        self.assertEqual(qa_em.extract_response_answer('<answer><think>x</think><answer>Paris</answer>'), 'Paris')

    def test_unclosed_latest(self):
        self.assertIsNone(qa_em.extract_response_answer('<answer>Paris</answer><answer>Rome'))

    def test_empty_latest(self):
        self.assertIsNone(qa_em.extract_response_answer('<answer>Paris</answer><answer> </answer>'))

    def test_last_complete(self):
        self.assertEqual(qa_em.extract_response_answer('<answer>Rome</answer><answer>Paris</answer>'), 'Paris')

    def test_structural_content_rejected(self):
        self.assertIsNone(qa_em.extract_response_answer('<answer><search>Paris</search></answer>'))

    def test_legacy_default_unchanged(self):
        self.assertIsNone(qa_em.extract_solution('<answer>Paris</answer>'))
        self.assertEqual(qa_em.extract_solution('<answer>Beijing</answer><answer>Paris</answer>'), 'Paris')

    def test_prompt_example_not_rewarded(self):
        data = batch('<search>capital</search>', 'Beijing')
        self.assertEqual(RewardManager(Tokenizer(), 0)(data).sum().item(), 1.)
        self.assertEqual(RewardManager(Tokenizer(), 0, answer_mode='response_only_v1')(data).sum().item(), 0.)

    def test_environment_excluded(self):
        data = batch('<search>capital</search>', environment='<answer>Paris</answer>')
        self.assertEqual(RewardManager(Tokenizer(), 0, answer_mode='response_only_v1')(data).sum().item(), 0.)

    def test_generated_answer_rewarded(self):
        data = batch('<answer>Paris</answer>', environment='<answer>Rome</answer>')
        self.assertEqual(RewardManager(Tokenizer(), 0, answer_mode='response_only_v1')(data).sum().item(), 1.)

    def test_strict_equality_preserved(self):
        self.assertEqual(qa_em.compute_score_em('<answer>Paris is the capital.</answer>', {'target':['Paris']}, answer_mode='response_only_v1'), 0.)

    def test_alias_normalization_preserved(self):
        self.assertEqual(qa_em.compute_score_em('<answer>The PARIS!</answer>', {'target':['Rome','Paris']}, answer_mode='response_only_v1'), 1.)

    def test_zero_response_safe(self):
        self.assertEqual(RewardManager(Tokenizer(), 0, answer_mode='response_only_v1')(batch('')).sum().item(), 0.)

    def test_record_complete_and_shadow_metric(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'audit.jsonl'
            reward = RewardManager(Tokenizer(), 0, answer_mode='response_only_v1', audit_path=str(path))
            data = batch('<search>capital</search>', 'Beijing', '<answer>Paris</answer>')
            reward(data); reward(data)
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]['evaluation_step'], 50)
            self.assertEqual(rows[0]['reward'], 0.)
            self.assertEqual(rows[0]['legacy_reward'], 1.)
            self.assertIn('<answer>Paris</answer>', rows[0]['full_response'])
            self.assertNotIn('Paris', rows[0]['model_response'])
            self.assertEqual(rows[1]['reward_call'], 2)

    def test_unknown_mode_rejected(self):
        with self.assertRaises(ValueError):
            RewardManager(Tokenizer(), 0, answer_mode='typo')
        with self.assertRaises(ValueError):
            qa_em.extract_solution('x', 'typo')

    def test_training_diagnostics_grouping(self):
        # 真正调用训练汇总：全错组和混合组比例、生成计数及结束比例同时核对。
        from types import SimpleNamespace
        from verl.experimental.difficulty.controller import DifficultyExperiment
        experiment = object.__new__(DifficultyExperiment)
        experiment.sampler = SimpleNamespace(exposures=np.array([1, 1]))
        data = DataProto.from_dict(
            {'responses':torch.ones(8,1,dtype=torch.long),
             'attention_mask':torch.ones(8,1,dtype=torch.long),
             'token_level_scores':torch.tensor([[1.]]+[[0.]]*7)},
            non_tensors={'uid':np.array(['a']*4+['b']*4,dtype=object)},
            meta_info={'generation_diagnostics':[dict(observation_truncations=1,
                generation_limit_hits=1,generation_calls=2,forced_final=0)]*8,
                'active_mask':[False]*7+[True]})
        metrics = experiment.metrics(data)
        self.assertEqual(metrics['difficulty/effective_fraction'], .5)
        self.assertEqual(metrics['generation/observation_truncations'], 8)
        self.assertEqual(metrics['generation/limit_hit_fraction'], .5)
        self.assertEqual(metrics['generation/answer_stop_fraction'], 7/8)


if __name__ == '__main__':
    unittest.main()

