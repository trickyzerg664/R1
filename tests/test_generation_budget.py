"""无需GPU的检索标签、轨迹预算与兼容性验证。"""
import unittest
import torch
from search_r1.llm_agent.context_budget import observation_ids, pad_token_rows, ContextBudget


class CharTokenizer:
    pad_token_id = 0
    pad_token = '~'
    padding_side = 'right'
    def encode(self, text, add_special_tokens=False):
        return [ord(c) for c in text]
    def decode(self, ids, **kwargs):
        return ''.join(chr(int(i)) for i in ids if i)
    def batch_decode(self, rows, **kwargs):
        return [self.decode(row) for row in rows]
    def __call__(self, texts, **kwargs):
        return {'input_ids': pad_token_rows([self.encode(text) for text in texts],0,self.padding_side)}


class GenerationBudgetTests(unittest.TestCase):
    def setUp(self):
        self.tok = CharTokenizer()

    def test_untruncated_ids_identical(self):
        # 已闭合且未超限的观察必须逐token一致，不改变已有评分条件。
        text = '\n\n<information>Doc 1(Title: A) body</information>\n\n'
        ids, cut = observation_ids(text, self.tok, 300)
        self.assertFalse(cut)
        self.assertEqual(ids, self.tok.encode(text))

    def test_truncated_tags_and_document_headers(self):
        # 长正文不能挤掉后续文档标题或结束标签。
        text = '\n\n<information>' + '\n'.join(f'Doc {i}(Title: T{i}) ' + 'x'*500 for i in range(1,4)) + '</information>\n\n'
        ids, cut = observation_ids(text, self.tok, 180)
        result = self.tok.decode(ids)
        self.assertTrue(cut)
        self.assertLessEqual(len(ids), 180)
        self.assertTrue(result.endswith('</information>\n\n'))
        self.assertIn('[retrieval truncated]', result)
        for i in range(1,4): self.assertIn(f'Doc {i}(Title: T{i})', result)

    def test_tiny_budget_rejected(self):
        # 无法保留标签的配置显式失败，不输出半截标签。
        with self.assertRaises(ValueError):
            observation_ids('\n\n<information>'+'x'*500+'</information>\n\n',self.tok,4)

    def test_empty_and_mixed_padding_long(self):
        # 空观察与不同长度批次均保持整数类型和预定补齐方向。
        self.assertEqual(pad_token_rows([[],[]],0).shape,(2,0))
        self.assertEqual(pad_token_rows([[],[]],0).dtype,torch.long)
        self.assertEqual(pad_token_rows([[1,2],[3]],0,'left').tolist(),[[1,2],[0,3]])
        self.assertEqual(pad_token_rows([[1,2],[3]],0,'right').tolist(),[[1,2],[3,0]])

    def test_context_reserves_final_answer(self):
        # 检索反馈不得消耗最终回答预算，完整历史超限须失败。
        prefix=pad_token_rows([[1]*80,[1]*40],0)
        budget=ContextBudget(prefix,0,800,64,self.tok)
        responses=pad_token_rows([[2]*400,[2]*10],0)
        generated=pad_token_rows([[3]*64,[3]*20],0)
        limits=budget.observation_limits(responses,generated)
        self.assertGreater(limits[1],limits[0])
        bounded=pad_token_rows([[2]*(400+64+limits[0]),[2]*(10+20+limits[1])],0)
        budget.validate(bounded)
        self.assertTrue(bool(budget.final_mask(bounded).all()))
        with self.assertRaises(ValueError): budget.validate(pad_token_rows([[1]*801,[1]],0))

    def test_question_too_long_rejected(self):
        # 问题本身几乎占满窗口时，不静默裁剪原问题。
        with self.assertRaises(ValueError): ContextBudget(pad_token_rows([[1]*790],0),0,800,64,self.tok)

    def test_manager_legacy_disabled_compatibility(self):
        # 默认关闭新功能时，观察及滚动窗口仍使用已有截取方向。
        from search_r1.llm_agent.generation import LLMGenerationManager, GenerationConfig
        from verl import DataProto
        config=GenerationConfig(2,6,10,8,6,1)
        manager=LLMGenerationManager(self.tok,None,config)
        self.assertEqual(manager._process_next_obs(['abcdefgh','xy']).tolist(),[[97,98,99,100,101,102],[120,121,0,0,0,0]])
        ids=torch.arange(1,9).reshape(1,-1)
        batch=DataProto.from_dict({'input_ids':ids,'attention_mask':torch.ones_like(ids),'position_ids':torch.arange(8).reshape(1,-1)})
        result=manager._update_rolling_state(batch,torch.arange(9,14).reshape(1,-1),torch.arange(14,19).reshape(1,-1))
        self.assertEqual(result.batch['input_ids'].tolist(),[list(range(9,19))])

    def test_manager_complete_history_and_final_answer(self):
        # 真正经过DataProto与生成循环，验证预算到期仍保留问题、最终答案及掩码。
        from search_r1.llm_agent.generation import LLMGenerationManager, GenerationConfig
        from verl import DataProto
        tok=self.tok
        class Worker:
            def __init__(self): self.inputs=[]
            def generate_sequences(self,batch):
                inputs=tok.batch_decode(batch.batch['input_ids'])
                self.inputs.extend(inputs)
                replies=['<answer>done</answer>' if 'budget exhausted' in text else '<search>q</search>' for text in inputs]
                return DataProto.from_dict({'responses':pad_token_rows([tok.encode(text) for text in replies],0)})
        class Manager(LLMGenerationManager):
            def batch_search(self,queries): return ['Doc 1(Title: A) '+'x'*1500 for _ in queries]
        worker=Worker()
        config=GenerationConfig(10,32,900,64,250,1,observation_truncation='structured',context_policy='bounded',record_diagnostics=True)
        manager=Manager(tok,worker,config)
        # 刻意超过max_start_length，确保训练与奖励也保留完整问题。
        question='ORIGINAL_QUESTION'+' Q'*30
        # 数据集固定补到窗口长度；输出仅保留必要补齐，避免训练处理大量无效位置。
        content=pad_token_rows([tok.encode(question)],0)
        prefix=torch.cat([torch.zeros((1,900-content.shape[1]),dtype=torch.long),content],dim=1)
        attention=(prefix!=0).long()
        positions=(attention.cumsum(-1)-1)*attention
        batch=DataProto.from_dict({'input_ids':prefix,'attention_mask':attention,'position_ids':positions})
        output=manager.run_llm_loop(batch,prefix)
        self.assertTrue(all(text.startswith('ORIGINAL_QUESTION') for text in worker.inputs))
        self.assertEqual(tok.decode(output.batch['prompts'][0]),question)
        self.assertEqual(output.batch['prompts'].shape[1],len(question))
        visible=tok.decode(output.batch['responses'][0])
        self.assertTrue(visible.endswith('<answer>done</answer>'))
        self.assertEqual(visible.count('<information>'),visible.count('</information>'))
        self.assertLessEqual(int(output.batch['attention_mask'].sum()),900)
        self.assertEqual(output.meta_info['active_mask'],[False])
        self.assertEqual(output.meta_info['generation_diagnostics'][0]['forced_final'],1)
        model=tok.decode(output.batch['input_ids'][0][output.batch['info_mask'][0].bool()])
        self.assertIn('<answer>done</answer>',model)
        self.assertNotIn('[retrieval truncated]',model)
        self.assertNotIn('budget exhausted',model)


if __name__ == '__main__': unittest.main()

