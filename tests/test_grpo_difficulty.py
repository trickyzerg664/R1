"""CPU regressions for question grouping, complete evaluation and attention choice."""
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
import torch
from omegaconf import OmegaConf
from transformers import AutoModelForCausalLM, Qwen2Config

from verl import DataProto
from verl.protocol import pad_dataproto_to_divisor, unpad_dataproto
from verl.trainer.ppo.ray_trainer import RayPPOTrainer, compute_advantage, repeat_search_batch
from verl.utils.model import get_attention_implementation
from search_r1.llm_agent.generation import GenerationConfig, LLMGenerationManager

ROOT = Path(__file__).resolve().parents[1]


# [data-difficulty] 故意生成相同题目 ID/index，验证抽题分组不依赖题目身份。
def prompts(size):
    ids = torch.arange(1, size + 1).reshape(-1, 1).repeat(1, 2)
    return DataProto.from_dict(
        {'input_ids': ids, 'attention_mask': torch.ones_like(ids),
         'position_ids': torch.arange(2).expand(size, -1)},
        non_tensors={'index': np.zeros(size, dtype=object),
                     'question_id': np.array(['same-question'] * size, dtype=object)},
        meta_info={'do_sample': False, 'validate': True})


# [data-difficulty] 用内存样本覆盖尾批场景，不加载实验数据或占用 GPU。
class FakeDataset:
    def __init__(self, parquet_files, **kwargs):
        self.dataframe = pd.DataFrame({'index': range(int(parquet_files))})

    def __len__(self):
        return len(self.dataframe)

    def __getitem__(self, i):
        ids = torch.tensor([i + 1, 2])
        return {'input_ids': ids, 'attention_mask': torch.ones_like(ids),
                'position_ids': torch.arange(2), 'index': i, 'data_source': 'nq'}


# [data-difficulty] 模拟四路生成，检查补齐及评价参数，然后返回可核对的固定结果。
class EchoWorker:
    world_size = 4

    def generate_sequences(self, batch):
        assert len(batch) % self.world_size == 0
        assert batch.meta_info['do_sample'] is False
        assert batch.meta_info['validate'] is True
        tensors = dict(batch.batch.items())
        tensors['responses'] = torch.ones((len(batch), 1), dtype=torch.long)
        return DataProto.from_dict(tensors, meta_info=batch.meta_info.copy())


# [data-difficulty] 隔离模型和检索依赖，仍经过真实的 DataProto 补齐/还原工具。
class FakeGenerationManager:
    def __init__(self, actor_rollout_wg, **kwargs):
        self.worker = actor_rollout_wg

    def run_llm_loop(self, gen_batch, initial_input_ids):
        padded, count = pad_dataproto_to_divisor(gen_batch, self.worker.world_size)
        return unpad_dataproto(self.worker.generate_sequences(padded), count)


class DifficultyTests(unittest.TestCase):
    # [data-difficulty] 覆盖重复题、重排和五档奖励，防止错误合组改变优势。
    def test_duplicate_questions_remain_separate_groups_after_reordering(self):
        data = repeat_search_batch(prompts(5), 4)
        self.assertEqual(sorted(Counter(data.non_tensor_batch['uid']).values()), [4]*5)
        # Five independent draws of one question receive 0, 1, 2, 3, 4 successes.
        rewards = torch.tensor([0,0,0,0, 1,0,0,0, 1,1,0,0, 1,1,1,0, 1,1,1,1], dtype=torch.float32)
        data.batch['responses'] = torch.ones((20, 1), dtype=torch.long)
        data.batch['token_level_rewards'] = rewards[:, None]
        order = torch.tensor([5,19,0,12,8,3,16,7,10,15,2,18,6,9,1,17,4,11,13,14])
        data.reorder(order)
        result = compute_advantage(data, 'grpo', num_repeat=4)
        advantage = result.batch['advantages'][:, 0][torch.argsort(order)]
        torch.testing.assert_close(advantage[:4], torch.zeros(4))
        torch.testing.assert_close(advantage[-4:], torch.zeros(4))
        self.assertTrue(torch.all(advantage[4:16][rewards[4:16] == 1] > 0))
        self.assertTrue(torch.all(advantage[4:16][rewards[4:16] == 0] < 0))
        for start in (4,8,12):
            self.assertAlmostEqual(advantage[start:start+4].sum().item(), 0., places=5)

    # [data-difficulty] 人为把两个组并成八条，检查四条一组的约束会拒绝该输入。
    def test_wrong_group_size_fails_before_advantage(self):
        data = repeat_search_batch(prompts(2), 4)
        data.batch['responses'] = torch.ones((8,1), dtype=torch.long)
        data.batch['token_level_rewards'] = torch.zeros((8,1))
        data.non_tensor_batch['uid'][:] = 'merged-group'
        with self.assertRaisesRegex(ValueError, '4 trajectories'):
            compute_advantage(data, 'grpo', num_repeat=4)

    # [data-difficulty] 覆盖样本数远小于并行数的场景，并核对还原后的类型和数据。
    def test_padding_tiny_batches_preserves_rows_metadata_and_dataproto(self):
        for size in (1,2,3,4,5,9):
            data = prompts(size)
            padded, count = pad_dataproto_to_divisor(data, 8)
            self.assertEqual(len(padded) % 8, 0)
            result = unpad_dataproto(padded, count)
            self.assertIsInstance(result, DataProto)
            self.assertEqual(result.meta_info, data.meta_info)
            torch.testing.assert_close(result.batch['input_ids'], data.batch['input_ids'])
            np.testing.assert_array_equal(result.non_tensor_batch['question_id'], data.non_tensor_batch['question_id'])

    # [data-difficulty] 检索/非检索两条评价路径均逐一核对题目顺序，避免只查总数而漏掉重复计分。
    def test_validation_scores_every_row_including_tail(self):
        for do_search in (False, True):
            for size in (1,3,5,9):
                with self.subTest(do_search=do_search, size=size):
                    trainer = object.__new__(RayPPOTrainer)
                    trainer.config = OmegaConf.load(ROOT/'verl/trainer/config/ppo_trainer.yaml')
                    trainer.config.data.train_files = '4'
                    trainer.config.data.val_files = str(size)
                    trainer.config.data.train_batch_size = 2
                    trainer.config.data.val_batch_size = 4
                    trainer.config.do_search = do_search
                    trainer.tokenizer = SimpleNamespace(pad_token_id=0, eos_token_id=9)
                    trainer.actor_rollout_wg = EchoWorker()
                    seen = []
                    def reward(data):
                        seen.extend(data.non_tensor_batch['index'].tolist())
                        return torch.ones((len(data), 1))
                    trainer.val_reward_fn = reward
                    with patch('verl.utils.dataset.rl_dataset.RLHFDataset', FakeDataset):
                        trainer._create_dataloader()
                    with patch('verl.trainer.ppo.ray_trainer.LLMGenerationManager', FakeGenerationManager):
                        result = trainer._validate()
                    self.assertEqual(seen, list(range(size)))
                    self.assertEqual(result['val/num_samples'], size)
                    self.assertEqual(result['val/test_score/nq'], 1.)

    # [data-difficulty] 活动轨迹从 3→2→1→0，覆盖正常轮、补齐轮及最后一轮的参数传递。
    def test_multiturn_evaluation_preserves_sampling_flags(self):
        class Tokenizer:
            pad_token_id = 0
            pad_token = '<pad>'
        class Worker:
            def __init__(self): self.calls = []
            def generate_sequences(self, batch):
                # [data-difficulty] 同时核对活动筛选及补齐后的种子身份，避免轨迹缩减时串位。
                self.calls.append((len(batch), batch.meta_info.copy(), batch.non_tensor_batch['rollout_seed'].tolist()))
                outputs = ([11,10,10,11], [11,10], [11,11])[len(self.calls)-1]
                return DataProto.from_dict({'responses': torch.tensor(outputs)[:, None]},
                                           meta_info=batch.meta_info.copy())
        class Manager(LLMGenerationManager):
            def _postprocess_responses(self, responses):
                return responses, ['answer' if v == 11 else 'search' for v in responses[:,0].tolist()]
            def _process_next_obs(self, observations):
                return torch.zeros((len(observations), 1), dtype=torch.long)
            def execute_predictions(self, predictions, pad_token, active_mask=None, do_search=True):
                done = [not bool(active) or answer == 'answer' for answer, active in zip(predictions, active_mask)]
                search = [int(bool(active) and answer == 'search') for answer, active in zip(predictions, active_mask)]
                return ['']*len(predictions), done, [1]*len(predictions), search
        worker = Worker()
        manager = Manager(Tokenizer(), worker, GenerationConfig(
            max_turns=2, max_start_length=8, max_prompt_length=32,
            max_response_length=8, max_obs_length=4, num_gpus=2), is_validation=True)
        data = prompts(3)
        data.non_tensor_batch['rollout_seed'] = np.array([101, 202, 303])
        result = manager.run_llm_loop(data, data.batch['input_ids'])
        self.assertEqual([c[0] for c in worker.calls], [4,2,2])
        self.assertEqual([c[2] for c in worker.calls], [[101,202,303,101], [202,303], [303,303]])
        self.assertEqual([c[1]['sampling_round'] for c in worker.calls], [0,1,2])
        self.assertTrue(all(c[1]['do_sample'] is False and c[1]['validate'] is True for c in worker.calls))
        self.assertIsInstance(result, DataProto)
        self.assertEqual(len(result), 3)
        self.assertEqual(result.meta_info['active_mask'], [False]*3)

    # [data-difficulty] 兼容性错误应在加载权重前被配置检查发现。
    def test_attention_configuration_rejects_incompatible_padding(self):
        self.assertEqual(get_attention_implementation({}), 'flash_attention_2')
        for name in ('eager','sdpa'):
            with self.assertRaisesRegex(ValueError, 'use_remove_padding'):
                get_attention_implementation({'attn_implementation': name, 'use_remove_padding': True})
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            get_attention_implementation({'attn_implementation': 'unknown'})

    # [data-difficulty] 从同一份小模型权重出发比较后端；只比较有效 token，并检查有限梯度。
    def test_qwen_eager_and_sdpa_cpu_forward_backward(self):
        torch.manual_seed(42)
        config = Qwen2Config(vocab_size=32, hidden_size=16, intermediate_size=32,
                            num_hidden_layers=1, num_attention_heads=2, num_key_value_heads=2,
                            max_position_embeddings=32, attention_dropout=0.)
        ids = torch.tensor([[0,0,2,3,4],[0,5,6,7,8]])
        mask = (ids != 0).long()
        positions = (mask.cumsum(-1)-1).clamp(min=0)
        outputs = []
        with tempfile.TemporaryDirectory() as directory:
            initial = AutoModelForCausalLM.from_config(config, attn_implementation='eager')
            initial.save_pretrained(directory)
            for name in ('eager','sdpa'):
                implementation = get_attention_implementation({'attn_implementation': name})
                model = AutoModelForCausalLM.from_pretrained(directory, attn_implementation=implementation,
                                                           local_files_only=True)
                result = model(input_ids=ids, attention_mask=mask, position_ids=positions)
                self.assertTrue(torch.isfinite(result.logits).all())
                loss = result.logits[mask.bool()].square().mean()
                loss.backward()
                self.assertTrue(all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None))
                outputs.append(result.logits.detach()[mask.bool()])
        torch.testing.assert_close(outputs[0], outputs[1], atol=1e-5, rtol=1e-4)


if __name__ == '__main__':
    torch.set_num_threads(2)
    unittest.main()
