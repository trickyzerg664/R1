import copy
import pytest
import torch
import torch.nn.functional as F
from search_sft.data import global_batches,micro_slots,model_batch
from search_sft.loss import backward_loss,target_loss_sum


def test_tail_logits_predict_first_and_last_target_token():
    from transformers import Qwen2Config,Qwen2ForCausalLM
    torch.manual_seed(8)
    model=Qwen2ForCausalLM(Qwen2Config(vocab_size=32,hidden_size=16,intermediate_size=32,num_hidden_layers=1,num_attention_heads=2,num_key_value_heads=2,max_position_embeddings=32,attention_dropout=0.,pad_token_id=1,eos_token_id=1))
    model.config._attn_implementation='eager';model.train()
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
    row={'input_ids':[2,1,4,5,6,1],'prompt_length':3,'target_length':3,'row_weight':1.}
    ids=torch.tensor([row['input_ids']])
    labels=ids.clone();labels[:,:3]=-100
    standard=model(input_ids=ids,labels=labels,use_cache=False).loss*3
    standard.backward()
    reference={n:p.grad.clone() for n,p in model.named_parameters() if p.grad is not None}
    model.zero_grad()
    tail=model(**model_batch(row,'cpu')).logits
    actual=target_loss_sum(tail,row,chunk_size=2)
    actual.backward()
    torch.testing.assert_close(actual,standard)
    for n,p in model.named_parameters():
        if n in reference:torch.testing.assert_close(p.grad,reference[n],rtol=1e-5,atol=1e-6)


@pytest.mark.parametrize('size',[1,3,32,35])
def test_distributed_accumulation_and_tail_match_global_gradient(size):
    torch.manual_seed(9)
    parameters=torch.randn(4,12,requires_grad=True)
    rows=[{'input_ids':[2,3,4,5],'target_length':2,'row_weight':.3+(i%3)} for i in range(size)]
    for indices in global_batches(size,32,42):
        direct=sum(target_loss_sum(parameters.unsqueeze(0)[:,:3],rows[i])*rows[i]['row_weight'] for i in indices)/len(indices)
        expected=torch.autograd.grad(direct,parameters)[0]
        combined=torch.zeros_like(parameters)
        for rank in range(2):
            current=parameters.detach().clone().requires_grad_()
            for slot in micro_slots(indices,2):
                row=rows[slot[rank]] if slot[rank] is not None else None
                backward_loss(current.unsqueeze(0)[:,:3] if row else current.unsqueeze(0)[:,:1],row,len(indices),2).backward()
            combined+=current.grad/2
        torch.testing.assert_close(combined,expected,rtol=1e-5,atol=1e-6)


def test_zero_weight_dummy_has_finite_zero_gradient():
    x=torch.randn(1,1,12,requires_grad=True)
    loss=backward_loss(x,None,3,2);loss.backward()
    assert loss.item()==0 and torch.isfinite(x.grad).all() and not x.grad.any()
