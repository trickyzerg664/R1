"""CPU验证嵌套元数据按题保存，跨候选批拼接保持答案完整。"""
import unittest
import numpy as np
import torch
from verl import DataProto
from verl.experimental.difficulty.dynamic_filter import merge_groups
from verl.utils.dataset.rl_dataset import collate_fn


class CollateTests(unittest.TestCase):
    def test_fixed_and_variable_answer_counts_stay_one_dimensional(self):
        # 单答案、等长多答案和不同数量答案均须保持一题一个对象。
        for answers in ((["北京"], ["上海"]), (["纽约", "New York"], ["伦敦", "London"]),
                        (["纽约", "New York"], ["伦敦"])):
            with self.subTest(answers=answers):
                batch = collate_fn([{"golden_answers": value} for value in answers])
                self.assertEqual(batch["golden_answers"].shape, (2,))
                self.assertEqual(batch["golden_answers"].tolist(), list(answers))

    def test_numpy_answers_keep_values_and_objects(self):
        # Parquet读出的答案是数组，整理过程不展开、不复制其内部元素。
        answers = [np.array(["yes"]), np.array(["no"])]
        batch = collate_fn([{"golden_answers": value} for value in answers])
        self.assertEqual(batch["golden_answers"].shape, (2,))
        for index, value in enumerate(answers):
            self.assertIs(batch["golden_answers"][index], value)

    def test_tensor_scalar_dictionary_and_chat_compatibility(self):
        # 共用数据入口继续堆叠张量，标量、字典和对话均保留逐题值。
        rows = [{"input_ids": torch.tensor([i, i+1]), "index": i,
                 "reward_model": {"ground_truth": [str(i)]},
                 "raw_prompt": [{"role": "user", "content": str(i)}]} for i in range(2)]
        batch = collate_fn(rows)
        self.assertEqual(batch["input_ids"].tolist(), [[0, 1], [1, 2]])
        for key in ("index", "reward_model", "raw_prompt"):
            self.assertEqual(batch[key].shape, (2,))
            self.assertEqual(batch[key].tolist(), [row[key] for row in rows])

    def test_merge_candidates_with_different_answer_counts(self):
        # 重现失败批次：第一批含多答案题，第二批全为单答案；同时验证反向合并。
        def candidate(answers):
            rows = []
            for answer in answers:
                tokens = torch.tensor([1, 2, 3, 4, 5])
                mask = torch.ones(5, dtype=torch.long)
                rows.append({"prompts": tokens[:2], "responses": tokens[2:],
                             "responses_with_info_mask": tokens[2:], "input_ids": tokens,
                             "attention_mask": mask, "info_mask": mask, "position_ids": torch.arange(5),
                             "dynamic_rewards": torch.tensor([0., 0., 1.]), "golden_answers": answer})
            return DataProto.from_single_dict(collate_fn(rows))
        mixed = [["yes"], ["纽约", "New York"]]
        single = [["no"], ["伦敦"]]
        for first, second in ((mixed, single), (single, mixed)):
            merged = merge_groups([candidate(first), candidate(second)], 0)
            self.assertEqual(len(merged), 4)
            self.assertEqual(merged.non_tensor_batch["golden_answers"].shape, (4,))
            self.assertEqual(merged.non_tensor_batch["golden_answers"].tolist(), first + second)
            self.assertEqual(merged.batch["dynamic_rewards"].sum().item(), 4.)


if __name__ == "__main__":
    unittest.main()
