"""独立进程将完整 ZeRO 状态转为标准 HF 分片；不占用训练中的优化器内存。"""
import argparse
import json
import subprocess
import sys
import shutil
from pathlib import Path
from .common import configured_path, load_config, write_json


def export(checkpoints, output, model_path):
    from deepspeed.utils.zero_to_fp32 import convert_zero_checkpoint_to_fp32_state_dict
    from transformers import AutoConfig,AutoTokenizer
    import torch
    root=Path(checkpoints);out=Path(output)
    tag=json.loads((root/'latest.json').read_text())['tag']
    if not (root/tag/'complete.json').is_file():raise ValueError('Incomplete checkpoint')
    if out.exists():raise ValueError('Export directory exists')
    out.mkdir(parents=True)
    # 0.15.4 已提供安全分片导出接口；不写另一套 ZeRO 参数合并数学。
    convert_zero_checkpoint_to_fp32_state_dict(str(root),str(out),max_shard_size='2GB',safe_serialization=True,tag=tag)
    config=AutoConfig.from_pretrained(model_path,local_files_only=True)
    config.torch_dtype=torch.float32
    config.save_pretrained(out)
    if (Path(model_path)/'generation_config.json').is_file():
        shutil.copyfile(Path(model_path)/'generation_config.json',out/'generation_config.json')
    AutoTokenizer.from_pretrained(model_path,local_files_only=True).save_pretrained(out)
    write_json(out/'sft_provenance.json',json.loads((root/tag/'complete.json').read_text()))


def verify_export(output,model_path):
    from transformers import AutoTokenizer,AutoModelForCausalLM
    import torch
    original=AutoTokenizer.from_pretrained(model_path,local_files_only=True)
    tokenizer=AutoTokenizer.from_pretrained(output,local_files_only=True)
    examples=['Question: Where is the city?\n<think>Search.</think><search>city country</search>',
              '\n\n<information>Doc 1(Title: Example) A city.</information>\n\n<answer>Example</answer>']
    for text in examples:
        if tokenizer.encode(text)!=original.encode(text):raise ValueError('Export tokenizer changes prompt token IDs')
    model=AutoModelForCausalLM.from_pretrained(output,local_files_only=True,torch_dtype=torch.float32,
                                             attn_implementation='eager',low_cpu_mem_usage=True)
    model.eval()
    inputs=tokenizer(examples[0],return_tensors='pt')
    with torch.no_grad():logits=model(**inputs,num_logits_to_keep=1,use_cache=False).logits
    if not torch.isfinite(logits).all():raise ValueError('Nonfinite exported-model logits')
    result={'cold_load_verified':True,'tokenizer_equivalence_verified':True,'parameters':sum(p.numel() for p in model.parameters())}
    write_json(Path(output)/'export_verification.json',result)
    print(json.dumps(result))


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--checkpoints');p.add_argument('--output',required=True);p.add_argument('--verify-only',action='store_true')
    args=p.parse_args();c=load_config(args.config)
    model=configured_path(c['model']['path'])
    if args.verify_only:verify_export(args.output,model)
    else:
        if not args.checkpoints:p.error('--checkpoints required for export')
        export(args.checkpoints,args.output,model)
        subprocess.run([sys.executable,'-m','search_sft.export','--config',args.config,'--output',args.output,'--verify-only'],check=True)

if __name__=='__main__':main()
