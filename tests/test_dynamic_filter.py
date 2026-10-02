"""CPU验证完整补抽路径、组完整性、padding、恢复边界和安全损失梯度。"""
import tempfile
from pathlib import Path
import unittest
from types import SimpleNamespace
import numpy as np
import torch
from torch.utils.data import DataLoader
from verl import DataProto
from verl.experimental.difficulty.controller import DifficultyExperiment
from verl.experimental.difficulty.dynamic_filter import mixed_groups,merge_groups,take_rows,training_batches
from verl.experimental.difficulty.loss_safety import policy_loss,kl_loss,entropy_loss
from verl.trainer.ppo.ray_trainer import repeat_search_batch
from verl.trainer.ppo import core_algos
from verl.utils.dataset.rl_dataset import collate_fn


class Dataset:
    def __getitem__(self,i):
        return {'input_ids':torch.tensor([3,4]),'attention_mask':torch.ones(2,dtype=torch.long),
                'position_ids':torch.arange(2),'question_id':f'q{i}', 'data_source':'nq',
                'reward_model':{'ground_truth':{'target':['yes']}}}
    def __len__(self):return 100


class Manager:
    config=SimpleNamespace(max_start_length=2)
    def __init__(self,all_wrong=False):self.calls=0;self.all_wrong=all_wrong;self.seeds=[]
    def run_llm_loop(self,gen_batch,initial_input_ids):
        self.calls+=1; self.seeds.append(gen_batch.non_tensor_batch['rollout_seed'].tolist())
        n=len(gen_batch); p=gen_batch.batch['input_ids']; r=torch.full((n,self.calls+1),2,dtype=torch.long)
        for i in range(n):
            group=i//8;k=0 if self.all_wrong or group==0 else 8 if group==1 else 4
            if i%8<k:r[i,0]=1
        attention=torch.ones(n,p.shape[1]+r.shape[1],dtype=torch.long)
        return DataProto.from_dict({'prompts':p,'responses':r,'responses_with_info_mask':r,
            'input_ids':torch.cat((p,r),dim=-1),'attention_mask':attention,'info_mask':attention,
            'position_ids':attention.cumsum(-1)-1},meta_info={'active_mask':[False]*n,
                'valid_search_stats':[0]*n,'generation_diagnostics':[dict(observation_truncations=0,
                generation_calls=1,generation_limit_hits=0,forced_final=0)]*n})


class Worker:
    def __init__(self):self.calls=0
    def compute_log_prob(self,batch):
        self.calls+=1
        return DataProto.from_dict({'old_log_probs':torch.zeros_like(batch.batch['responses'],dtype=torch.float32)},
                                   meta_info={'temperature':1.})


def reward(batch):
    result=torch.zeros_like(batch.batch['responses'],dtype=torch.float32)
    result[:,-1]=(batch.batch['responses'][:,0]==1).float()
    return result


class DynamicTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.rows=[{'question_id':f'q{i}','source':'nq'} for i in range(100)]
        self.settings={'mode':'train','group_size':8,'dynamic_filter':{'enabled':True,'max_rounds':4},'labels':None,'ratios':None}
        self.provenance={'initial_model_id':'test'}
    def controller(self,name='a',steps=2):
        return DifficultyExperiment(self.rows,self.settings,8,steps,42,Path(self.tmp.name)/name,self.provenance)
    def loader(self,c):return DataLoader(Dataset(),batch_sampler=c.sampler,num_workers=0,collate_fn=collate_fn)
    def test_complete_refill_and_checkpoint_replay(self):
        c=self.controller(); manager=Manager(); worker=Worker()
        stream=training_batches(self.loader(c),c,manager,reward,repeat_search_batch,worker,0,2,4)
        batch=next(stream)
        self.assertEqual(len(batch),64);self.assertEqual(worker.calls,1)
        self.assertGreaterEqual(c.sampler.cursor,2)
        groups,_=mixed_groups(batch,8);self.assertEqual(len(groups),8)
        self.assertEqual(len(set(batch.non_tensor_batch['question_id'])),8)
        self.assertEqual(batch.batch['dynamic_rewards'].sum().item(),32)
        self.assertEqual(batch.batch['old_log_probs'].dtype,torch.float32)
        self.assertEqual(len(batch.meta_info['generation_diagnostics']),64)
        self.assertNotEqual(manager.seeds[0],manager.seeds[1])
        c.after_step(1,{},1.,accepted_question_ids=batch.meta_info['dynamic_question_ids']);state=c.state_dict()
        restored=self.controller('b');restored.load_state_dict(state)
        self.assertEqual(restored.sampler.cursor,c.sampler.cursor)
        self.assertEqual(restored.accepted_question_ids,c.accepted_question_ids)
        self.assertEqual(next(iter(restored.sampler)),next(iter(c.sampler)))
    def test_cap_fails_without_partial_update(self):
        c=self.controller(); worker=Worker()
        stream=training_batches(self.loader(c),c,Manager(True),reward,repeat_search_batch,worker,0,2,2)
        with self.assertRaises(RuntimeError):next(stream)
        self.assertEqual(c.completed_step,0);self.assertEqual(worker.calls,0)
    def test_incomplete_group_rejected(self):
        c=self.controller();stream=training_batches(self.loader(c),c,Manager(),reward,repeat_search_batch,Worker(),0,2,4)
        batch=next(stream);part=take_rows(batch,list(range(7)))
        with self.assertRaises(ValueError):mixed_groups(part,8)
    def test_duplicate_question_excluded(self):
        c=self.controller();stream=training_batches(self.loader(c),c,Manager(),reward,repeat_search_batch,Worker(),0,2,4)
        batch=next(stream);seen=set(batch.non_tensor_batch['question_id'])
        groups,_=mixed_groups(batch,8,seen);self.assertEqual(groups,[])
    def test_padding_preserves_prompt_response_mask_rewards(self):
        def part(p,r):
            tokens=torch.arange(1,p+r+1).reshape(1,-1)
            mask=torch.ones_like(tokens); info=mask.clone();info[0,p]=0
            scores=torch.zeros(1,r);scores[0,-1]=1.
            return DataProto.from_dict({'prompts':tokens[:,:p],'responses':tokens[:,p:],
                'responses_with_info_mask':tokens[:,p:],'input_ids':tokens,'attention_mask':mask,
                'info_mask':info,'position_ids':mask.cumsum(-1)-1,'dynamic_rewards':scores},
                non_tensors={'uid':np.array(['u'],dtype=object)},meta_info={})
        a,b=part(2,3),part(4,2);merged=merge_groups([a,b],0)
        self.assertEqual(merged.batch['prompts'][0].tolist(),[0,0,1,2])
        self.assertEqual(merged.batch['responses'][1].tolist(),[5,6,0])
        self.assertEqual(merged.batch['attention_mask'].sum(-1).tolist(),[5,6])
        self.assertEqual(merged.batch['dynamic_rewards'].sum(-1).tolist(),[1,1])
        self.assertEqual(merged.batch['info_mask'][0,4].item(),0)
    def test_mid_filter_resume_rejected(self):
        c=self.controller();next(iter(c.sampler)); state=c.state_dict()
        with self.assertRaises(ValueError):self.controller('b').load_state_dict(state)


class SafeLossTests(unittest.TestCase):
    def test_normal_policy_matches_legacy(self):
        old=torch.tensor([[-1.,-2.,-3.]])
        current=torch.tensor([[-.9,-2.3,-2.8]],requires_grad=True)
        adv=torch.tensor([[1.,-1.,.5]]);mask=torch.ones_like(adv)
        a=policy_loss(old,current,adv,mask,.2)[0]
        b=core_algos.compute_policy_loss(old,current,adv,mask,.2)[0]
        self.assertTrue(torch.allclose(a,b))
        self.assertTrue(torch.allclose(torch.autograd.grad(a,current,retain_graph=True)[0],torch.autograd.grad(b,current)[0]))
    def test_normal_kl_matches_legacy(self):
        x=torch.tensor([[-1.,-2.]],requires_grad=True);ref=torch.zeros_like(x);mask=torch.ones_like(x)
        a=kl_loss(x,ref,mask)[0];b=core_algos.kl_penalty(x,ref,'low_var_kl').mean()
        self.assertTrue(torch.allclose(a,b,atol=1e-6))
    def test_large_kl_finite_nonzero_gradient(self):
        x=torch.tensor([[-100.]],requires_grad=True);loss,_=kl_loss(x,torch.zeros_like(x),torch.ones_like(x));loss.backward()
        self.assertTrue(torch.isfinite(loss));self.assertTrue(torch.isfinite(x.grad).all());self.assertNotEqual(x.grad.item(),0.)
    def test_masked_nan_does_not_contaminate(self):
        x=torch.tensor([[-1.,float('nan')]],requires_grad=True);mask=torch.tensor([[1.,0.]])
        loss,_=kl_loss(x,torch.zeros_like(x),mask);loss.backward()
        self.assertTrue(torch.isfinite(x.grad).all());self.assertEqual(x.grad[0,1].item(),0.)
    def test_zero_advantage_large_ratio_finite(self):
        x=torch.tensor([[100.]],requires_grad=True);zero=torch.zeros_like(x)
        loss,*_=policy_loss(zero,x,zero,torch.ones_like(x),.2);loss.backward()
        self.assertEqual(loss.item(),0.);self.assertTrue(torch.isfinite(x.grad).all())
    def test_valid_nan_fails_explicitly(self):
        with self.assertRaises(FloatingPointError):kl_loss(torch.tensor([[float('nan')]]),torch.zeros(1,1),torch.ones(1,1))
    def test_empty_mask_fails(self):
        with self.assertRaises(ValueError):entropy_loss(torch.zeros(1,1),torch.zeros(1,1))


if __name__=='__main__':unittest.main()

