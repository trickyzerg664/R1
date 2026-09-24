"""[data-difficulty] CPU 核心验收：配额、标签恢复、完整状态与训练接口。"""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
import torch
from omegaconf import OmegaConf
from verl.experimental.difficulty.sampling import DifficultyBatchSampler, bucket, pool_hash, validate_labels
from verl.experimental.difficulty.scoring import score_pool
from verl.experimental.difficulty.controller import DifficultyExperiment
from verl.experimental.difficulty.generation import request_sampling_params
from verl.experimental.difficulty.checkpoint import (save_checkpoint, read_checkpoint, load_driver,
    save_rank_state, load_rank_state, runtime_state, restore_runtime)
from verl.experimental.difficulty.reporting import migration
from verl.experimental.difficulty.configuration import prepare_config


def pool():
    # 每来源每档十题，使各组配额无需跨来源或重复抽题即可满足。
    rows = [{'question_id': f'{s}-{k}-{i}', 'source': s} for s in ('nq', 'hotpotqa')
            for k in range(5) for i in range(10)]
    records = [{**r, 'k': int(r['question_id'].split('-')[1]),
                'bucket': bucket(int(r['question_id'].split('-')[1])),
                'rewards': [1] * int(r['question_id'].split('-')[1]) + [0] * (4-int(r['question_id'].split('-')[1]))}
               for r in rows]
    payload = {'metadata': {'schema_version': 1, 'group_size': 4, 'pool_hash': pool_hash(rows),
                            'context': {'version': 'v0'}}, 'records': records}
    return rows, payload


class DifficultyCoreTests(unittest.TestCase):
    def setUp(self):
        # 临时产物彼此隔离，所有测试隐藏 CUDA，不读取正式模型。
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.rows, self.payload = pool()
        self.labels = validate_labels(self.payload, self.rows)

    def test_sampler_quotas_and_replay(self):
        # 累计来源与桶配额保持指定比例；中断后的抽样顺序必须完全一致。
        sampler = DifficultyBatchSampler(self.rows, 20, 20, 42, [.2, .6, .2], self.labels)
        iterator = iter(sampler)
        batches = [next(iterator) for _ in range(7)]
        state = sampler.state_dict()
        remainder = list(iterator)
        resumed = DifficultyBatchSampler(self.rows, 20, 20, 999, [.2, .6, .2], self.labels)
        resumed.load_state_dict(state)
        self.assertEqual(list(resumed), remainder)
        counts = {b: 0 for b in 'HME'}
        for batch in batches + remainder:
            self.assertEqual(len(set(batch)), 20)
            self.assertEqual(sum(self.rows[i]['source'] == 'nq' for i in batch), 10)
            for i in batch:
                counts[self.labels[self.rows[i]['question_id']]['bucket']] += 1
        self.assertEqual(counts, {'H': 80, 'M': 240, 'E': 80})

    def test_branch_and_refresh_preserve_exposure(self):
        # 配比改变只能显式 branch，刷新标签保留消费位置与历史曝光。
        sampler = DifficultyBatchSampler(self.rows, 20, 10, 42, [.2,.6,.2], self.labels)
        next(iter(sampler))
        state = sampler.state_dict()
        branch = DifficultyBatchSampler(self.rows, 20, 10, 42, [.1,.8,.1], self.labels)
        with self.assertRaises(ValueError):
            branch.load_state_dict(state)
        branch.load_state_dict(state, branch=True)
        np.testing.assert_array_equal(branch.exposures, sampler.exposures)
        shifted = copy.deepcopy(self.payload)
        for row in shifted['records']:
            row['k'] = 4-row['k']
            row['bucket'] = bucket(row['k'])
            row['rewards'] = [1]*row['k'] + [0]*(4-row['k'])
        branch.refresh(validate_labels(shifted, self.rows))
        self.assertEqual(branch.cursor, 1)
        self.assertEqual(branch.debts, {})
        self.assertEqual(int(branch.exposures.sum()), 20)
        self.assertEqual(sum(map(sum, migration(self.payload, shifted, self.rows)['counts'])), 100)

    def test_invalid_labels_and_missing_bucket(self):
        # 缺轨迹、换题池或缺必需桶均应明确拒绝，不能静默退化为自然采样。
        broken = copy.deepcopy(self.payload)
        broken['records'][0]['rewards'] = [0]
        with self.assertRaises(ValueError):
            validate_labels(broken, self.rows)
        with self.assertRaises(ValueError):
            validate_labels(self.payload, self.rows[:-1])
        missing = {key: {**r, 'k': 1} for key, r in self.labels.items()}
        with self.assertRaises(ValueError):
            DifficultyBatchSampler(self.rows, 20, 10, 42, [.2,.6,.2], missing)

    def test_seed_attachment_preserves_dataproto_contract(self):
        # 真正经过 DataProto 校验、重复和生成补齐，防止整数 dtype 在 Ray 分发时才失败。
        from verl import DataProto
        from verl.protocol import pad_dataproto_to_divisor, unpad_dataproto
        exp = DifficultyExperiment(self.rows, {}, 2, 1, 42, self.root/'seed-contract',
                                   {'initial_model_id': 'c0'})
        batch = DataProto.from_dict({'input_ids': torch.ones(3, 2, dtype=torch.long)})
        exp.attach_seeds(batch, 1)
        batch.check_consistency()
        padded, added = pad_dataproto_to_divisor(batch, 8)
        padded.check_consistency()
        self.assertEqual(len(unpad_dataproto(padded, added)), 3)
        self.assertEqual(batch.non_tensor_batch['rollout_seed'].dtype, object)

    def test_scoring_resume_and_request_seed_independence(self):
        # 第二批故障后只补未完成题；每题四个不同种子，在重试中保持不变。
        calls = []
        def generate(indices, seeds):
            calls.append((indices, seeds))
            if len(calls) == 2:
                raise RuntimeError('retrieval unavailable')
            self.assertTrue(all(len(set(s)) == 4 for s in seeds))
            return [{'rewards': [0,1,0,1]} for _ in indices]
        output = self.root/'labels.json'
        with self.assertRaises(RuntimeError):
            score_pool(self.rows[:7], generate, output, {'model': 'c0'}, batch_size=3)
        self.assertFalse(output.exists())
        result = score_pool(self.rows[:7], generate, output, {'model': 'c0'}, batch_size=3)
        self.assertEqual(calls[1], calls[2])
        self.assertEqual(len(result['records']), 7)
        validate_labels(result, self.rows[:7])
        params = SimpleNamespace(seed=None, temperature=1.)
        generated = request_sampling_params(params, calls[0][1][0], 0, 4)
        self.assertEqual(len({p.seed for p in generated}), 4)
        self.assertIsNone(params.seed)
        self.assertNotEqual(generated[0].seed, request_sampling_params(params, calls[0][1][0], 1, 4)[0].seed)
        with self.assertRaises(ValueError):
            score_pool(self.rows[:7], generate, output, {'model': 'c1'}, batch_size=3)
        corrupted = json.loads(output.read_text())
        corrupted['records'][0]['rewards'] = [0]
        output.write_text(json.dumps(corrupted))
        with self.assertRaises(ValueError):
            score_pool(self.rows[:7], generate, output, {'model': 'c0'}, batch_size=3)

    def test_complete_checkpoint_optimizer_scheduler_rng(self):
        # 真实 CPU AdamW 更新验证恢复后的下一步，覆盖动量、学习率、RNG 和完整性校验。
        model = torch.nn.Linear(2, 1)
        opt = torch.optim.AdamW(model.parameters(), lr=.01)
        sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda n: min(1., (n+1)/4))
        scaler = torch.amp.GradScaler('cuda', enabled=False)
        def update():
            opt.zero_grad()
            model(torch.randn(3,2)).square().mean().backward()
            opt.step()
            sched.step()
        update()
        weights = copy.deepcopy(model.state_dict())
        state = runtime_state()
        checkpoint = self.root/'checkpoint'
        def save_actor(path):
            Path(path).mkdir()
            torch.save(weights, Path(path)/'weights.pt')
            save_rank_state(path, 0, 1, opt, sched, scaler, state)
        save_checkpoint(checkpoint, {'step': 1}, {'step': 1}, save_actor)
        self.assertEqual(load_driver(checkpoint)['step'], 1)
        update()
        expected = copy.deepcopy(model.state_dict())
        expected_lr = sched.get_last_lr()
        model.load_state_dict(weights)
        restored = load_rank_state(checkpoint/'actor', 0, 1, opt, sched, scaler)
        restore_runtime(restored)
        update()
        for key in expected:
            torch.testing.assert_close(model.state_dict()[key], expected[key], rtol=0, atol=0)
        self.assertEqual(sched.get_last_lr(), expected_lr)
        with self.assertRaises(ValueError):
            load_rank_state(checkpoint/'actor', 0, 2, opt, sched, scaler)
        (checkpoint/'driver.pt').write_bytes(b'broken')
        with self.assertRaises(ValueError):
            read_checkpoint(checkpoint)
        with self.assertRaises(ValueError):
            read_checkpoint(self.root/'incomplete')

    def test_controller_restore_policy_and_refresh_validation(self):
        # 控制器只接收普通数据，恢复时允许的变化与严格继续模式分别验证。
        path = self.root/'labels.json'
        path.write_text(json.dumps(self.payload))
        settings = {'labels': str(path), 'ratios': [.2,.6,.2], 'refresh_every': 2}
        provenance = {'initial_model_id': 'c0', 'reference_id': 'c0'}
        exp = DifficultyExperiment(self.rows, settings, 20, 5, 42, self.root/'first', provenance)
        next(iter(exp.sampler))
        exp.after_step(1, {}, .1)
        state = exp.state_dict()
        resumed = DifficultyExperiment(self.rows, settings, 20, 5, 42, self.root/'second', provenance)
        resumed.load_state_dict(state)
        self.assertEqual(next(iter(exp.sampler)), next(iter(resumed.sampler)))
        self.assertTrue(resumed.should_refresh(2))
        bad = copy.deepcopy(self.payload)
        bad['records'].pop()
        with self.assertRaises(ValueError):
            resumed.refresh(bad)
        altered = DifficultyExperiment(self.rows, {**settings, 'refresh_every': 3}, 20, 5, 42,
                                       self.root/'third', provenance)
        with self.assertRaises(ValueError):
            altered.load_state_dict(state)
        altered.load_state_dict(state, branch=True)

    def test_disabled_configuration_and_invalid_experiment(self):
        # 旧入口的配置在关闭实验时完全不修改；开启后禁止不受支持的组合。
        config = OmegaConf.load('verl/trainer/config/ppo_trainer.yaml')
        before = OmegaConf.to_container(config)
        prepare_config(config)
        self.assertEqual(OmegaConf.to_container(config), before)
        config.difficulty.enabled = True
        with self.assertRaises(ValueError):
            prepare_config(config)

    def test_retrieval_errors_do_not_become_zero_reward(self):
        # HTTP 失败及响应数量错误直接抛出，避免污染难度标签。
        from search_r1.llm_agent.generation import LLMGenerationManager
        manager = LLMGenerationManager.__new__(LLMGenerationManager)
        manager.config = SimpleNamespace(search_url='http://test', topk=3, search_timeout=2)
        response = SimpleNamespace(raise_for_status=lambda: None, json=lambda: {'result': []})
        with patch('search_r1.llm_agent.generation.requests.post', return_value=response) as post:
            with self.assertRaises(ValueError):
                manager._batch_search(['question'])
            self.assertEqual(post.call_args.kwargs['timeout'], 2)

    def test_real_training_loop_exact_steps_refresh_and_resume(self):
        # 保留真实 fit、优势计算和 DataLoader，仅替换模型计算与检索，验证接线和最后一步。
        from torch.utils.data import DataLoader
        from verl import DataProto
        from verl.utils.dataset.rl_dataset import collate_fn
        from verl.trainer.ppo.ray_trainer import RayPPOTrainer
        config = OmegaConf.load('verl/trainer/config/ppo_trainer.yaml')
        config.algorithm.adv_estimator = 'grpo'
        config.actor_rollout_ref.actor.use_kl_loss = True
        config.actor_rollout_ref.rollout.n_agent = 4
        config.trainer.n_gpus_per_node = 1
        config.trainer.save_freq = 1
        config.trainer.test_freq = -1
        config.trainer.total_training_steps = 3
        config.difficulty.enabled = True
        config.difficulty.refresh_steps = [1]
        rows = self.rows[:10]
        dataset = [{'input_ids': torch.tensor([1,2]), 'attention_mask': torch.ones(2, dtype=torch.long),
                    'position_ids': torch.tensor([0,1]), 'question_id': row['question_id'],
                    'data_source': row['source'], 'reward_model': {'ground_truth': ['answer']}}
                   for row in rows]
        class Manager:
            def __init__(self, **kwargs):
                pass
            def run_llm_loop(self, gen_batch, initial_input_ids):
                # [data-difficulty] 训练与评分入口都必须满足 DataProto 非张量字段约束。
                gen_batch.check_consistency()
                n = len(gen_batch)
                responses = (torch.arange(n) % 2)[:,None] + 1
                return DataProto.from_dict({'prompts': initial_input_ids, 'responses': responses,
                    'input_ids': torch.cat([initial_input_ids, responses], dim=1),
                    'attention_mask': torch.ones(n,3, dtype=torch.long),
                    'info_mask': torch.ones(n,3, dtype=torch.long),
                    'position_ids': torch.arange(3).repeat(n,1)},
                    meta_info={'valid_search_stats': [0]*n})
        class Worker:
            def __init__(self): self.updates = 0
            def compute_log_prob(self, batch):
                return DataProto.from_dict({'old_log_probs': torch.zeros_like(batch.batch['responses'], dtype=torch.float)})
            def update_actor(self, batch):
                self.updates += 1
                return DataProto(meta_info={'metrics': {'loss': [0.]}})
            def difficulty_runtime(self): return [runtime_state()]
            def difficulty_restore_runtime(self, states): restore_runtime(states[0])
            def save_training_checkpoint(self, path):
                Path(path).mkdir()
                torch.save({'updates': self.updates}, Path(path)/'toy.pt')
            def load_training_checkpoint(self, path):
                self.updates = torch.load(Path(path)/'toy.pt', weights_only=False)['updates']
        def make_trainer(output, resume=None, mode='train'):
            trainer = RayPPOTrainer.__new__(RayPPOTrainer)
            trainer.config = copy.deepcopy(config)
            trainer.config.difficulty.output_dir = str(output)
            trainer.config.difficulty.resume = resume
            trainer.config.difficulty.mode = mode
            trainer.config.difficulty.score_output = str(output / 'scored.json')
            trainer.total_training_steps = 3
            trainer.global_steps = 0
            trainer.tokenizer = SimpleNamespace(pad_token_id=0)
            trainer.actor_rollout_wg = Worker()
            trainer.use_reference_policy = trainer.use_critic = trainer.use_rm = False
            trainer.val_reward_fn = None
            trainer.reward_fn = lambda batch: (batch.batch['responses']-1).float()
            trainer.logger = SimpleNamespace(log=lambda **kwargs: None)
            trainer._balance_batch = lambda *args, **kwargs: None
            trainer.difficulty = DifficultyExperiment(rows, OmegaConf.to_container(trainer.config.difficulty),
                                                       2, 3, 42, output, {'initial_model_id': 'c0'})
            trainer.train_dataset = dataset
            trainer.train_dataloader = DataLoader(dataset, batch_sampler=trainer.difficulty.sampler,
                                                  collate_fn=collate_fn, num_workers=0)
            return trainer
        first = make_trainer(self.root/'run')
        with patch('verl.trainer.ppo.ray_trainer.LLMGenerationManager', Manager), \
             patch('verl.trainer.ppo.ray_trainer.compute_data_metrics', return_value={}), \
             patch('verl.trainer.ppo.ray_trainer.compute_timing_metrics', return_value={}):
            first.fit()
            self.assertEqual(first.actor_rollout_wg.updates, 3)
            self.assertEqual(first.difficulty.completed_step, 3)
            self.assertTrue((self.root/'run/labels_step_1.json').is_file())
            second = make_trainer(self.root/'resumed', str(self.root/'run/checkpoints/step_1'))
            second.fit()
            # 仅评分时恢复父权重和状态，但不得追加 optimizer 更新。
            scoring = make_trainer(self.root/'score', str(self.root/'run/checkpoints/step_1'), mode='score')
            scoring.fit()
            self.assertEqual(scoring.actor_rollout_wg.updates, 1)
            self.assertEqual(len(json.loads((self.root/'score/scored.json').read_text())['records']), len(rows))
        self.assertEqual(second.actor_rollout_wg.updates, 3)
        np.testing.assert_array_equal(first.difficulty.sampler.exposures, second.difficulty.sampler.exposures)
        self.assertEqual(load_driver(self.root/'resumed/checkpoints/step_3')['completed_step'], 3)


    def test_prepare_branch_budget_and_fixed_reference(self):
        # 使用微型本地文件验证身份/路径逻辑，不加载模型；B 分支只改变比例和追加预算。
        from hydra import compose, initialize_config_dir
        from verl.experimental.difficulty.configuration import provenance
        # 测试显式给出虚拟 world size，避免依赖执行机器的 GPU 环境变量。
        with initialize_config_dir(config_dir=str(Path('verl/trainer/config').resolve()), version_base=None):
            config = compose(config_name='difficulty_grpo', overrides=['trainer.n_gpus_per_node=2'])
        model = self.root/'model'
        model.mkdir()
        (model/'config.json').write_text('{}')
        (model/'weights.bin').write_bytes(b'initial model')
        train, dev = self.root/'train.parquet', self.root/'dev.parquet'
        train.write_bytes(b'frozen train')
        dev.write_bytes(b'frozen dev')
        config.actor_rollout_ref.model.path = str(model)
        config.data.train_files, config.data.val_files = str(train), str(dev)
        config.difficulty.retrieval_id = 'pinned retrieval'
        prepare_config(config)
        origin = provenance(config)
        checkpoint = self.root/'parent'
        def actor(path):
            Path(path).mkdir()
            (Path(path)/'weights.bin').write_bytes(b'trained model')
        save_checkpoint(checkpoint, {}, {'step': 200, 'initial_model_id': config.difficulty.initial_model_id,
                                        'provenance': origin}, actor)
        branch = copy.deepcopy(config)
        branch.difficulty.resume = str(checkpoint)
        branch.difficulty.resume_mode = 'branch'
        branch.difficulty.additional_steps = 300
        branch.difficulty.ratios = [.1,.8,.1]
        prepare_config(branch)
        self.assertEqual(branch.trainer.total_training_steps, 500)
        self.assertEqual(branch.actor_rollout_ref.ref.model_path, str(model))
        self.assertEqual(branch.actor_rollout_ref.model.path, str(checkpoint/'actor'))
        self.assertEqual(provenance(branch), origin)
        incompatible = copy.deepcopy(branch)
        incompatible.difficulty.seed = 99
        with self.assertRaises(ValueError):
            prepare_config(incompatible)


if __name__ == '__main__':
    unittest.main()
