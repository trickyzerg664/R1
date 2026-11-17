"""生成仅供程序验收的随机小模型/数据；禁止作为7B或真实数据结果汇报。"""
import argparse
import copy
from pathlib import Path
import random
import torch
import yaml
from tokenizers import Tokenizer
from tokenizers.models import WordLevel
from tokenizers.pre_tokenizers import Whitespace
from transformers import PreTrainedTokenizerFast,Qwen2Config,Qwen2ForCausalLM
from search_sft.common import load_config,sha256,tokenizer_identity,write_json,write_jsonl


def make(root):
    root=Path(root).resolve()
    if root.exists():raise ValueError('Synthetic fixture already exists')
    root.mkdir(parents=True)
    torch.manual_seed(17)
    model=root/'model'
    vocab={'[PAD]':0,'[EOS]':1,'[UNK]':2,**{f'w{i}':i for i in range(3,32)}}
    tokenizer=Tokenizer(WordLevel(vocab,unk_token='[UNK]'));tokenizer.pre_tokenizer=Whitespace()
    fast=PreTrainedTokenizerFast(tokenizer_object=tokenizer,pad_token='[PAD]',eos_token='[EOS]',unk_token='[UNK]')
    fast.save_pretrained(model)
    config=Qwen2Config(vocab_size=32,hidden_size=32,intermediate_size=64,num_hidden_layers=2,num_attention_heads=4,num_key_value_heads=2,max_position_embeddings=128,pad_token_id=0,eos_token_id=1,attention_dropout=0.)
    Qwen2ForCausalLM(config).save_pretrained(model)
    release=root/'release';release.mkdir()
    rng=random.Random(42)
    def rows(n,prefix):
        return [{'sample_id':f'{prefix}{i}:0','question_id':f'{prefix}{i}','source':'synthetic',
                 'input_ids':[rng.randrange(3,32) for _ in range(10)],'prompt_length':7,'target_length':3,
                 'question_target_tokens':3,'row_weight':1/3} for i in range(n)]
    train,val=rows(35,'train'),rows(3,'val')
    files={}
    for name,items in [('train',train),('pilot',train),('val',val)]:
        f=release/(name+'.jsonl');write_jsonl(f,items);files[name]={'path':f.name,'sha256':sha256(f)}
    settings=load_config('configs/sft/deepseek.yaml');settings.pop('_config_path')
    settings['model']['path']=str(model);settings['data']['release_dir']=str(release)
    settings['output'].update(root=str(root/'runs'),save_every_batches=1)
    settings['training'].update(global_batch_size=32,learning_rate=.001)
    write_json(release/'manifest.json',{'status':'draft','evaluation_exclusions_complete':False,'protocol':settings['protocol'],
               'tokenizer_hashes':tokenizer_identity(model),'files':files,'synthetic_only':True})
    path=root/'smoke.yaml';path.write_text(yaml.safe_dump(settings),encoding='utf-8')
    print(path)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);make(p.parse_args().output)
