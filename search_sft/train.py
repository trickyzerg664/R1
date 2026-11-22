"""离线逐轮 SFT：模型状态由 DeepSpeed 管理，样本和归一化由本模块控制。"""
from __future__ import annotations
import argparse
import importlib.metadata
import json
import math
import os
from pathlib import Path
import random
import shutil
import subprocess
import numpy as np
import torch
import torch.distributed as dist

from . import BASE_COMMIT
from .checkpoint import load as load_checkpoint, save as save_checkpoint
from .common import configured_path, load_config, sha256, write_json
from .data import global_batches, load_release, micro_slots, model_batch
from .loss import backward_loss, target_loss_sum
from .preflight import verify_base, training_disk_budget


def parameter_probe(model):
    """Small deterministic FP16 shard sample; consumes no training RNG."""
    samples={}
    for name,p in model.named_parameters():
        value=getattr(p,'ds_tensor',p).detach().reshape(-1)
        if p.requires_grad and name.endswith('weight') and value.numel():
            count=min(2048,value.numel())
            indices=torch.arange(count,device=value.device,dtype=torch.long)*(value.numel()-1)//max(1,count-1)
            samples[name]=value.index_select(0,indices).float().cpu().clone()
            if len(samples)==20:break
    return samples


def version_check():
    expected={'transformers':'4.47.1','deepspeed':'0.15.4'}
    for package,version in expected.items():
        if importlib.metadata.version(package)!=version:
            raise ValueError(f'{package} must be {version}; use the isolated SFT environment')
    if shutil.which('ninja') is None:
        raise ValueError('ninja must be on PATH; use scripts/sft/run_host3.sh or activate the SFT environment')


def rank0_result(callback):
    """rank0 的资产/磁盘错误广播给所有进程，避免其它卡卡在 collective。"""
    value=[None]
    if dist.get_rank()==0:
        try:value[0]={'result':callback()}
        except Exception as error:value[0]={'error':str(error)}
    dist.broadcast_object_list(value,src=0)
    if 'error' in value[0]:raise ValueError(value[0]['error'])
    return value[0]['result']


def validate(engine,rows,device):
    engine.eval()
    total=torch.zeros((),device=device,dtype=torch.float64)
    world,rank=dist.get_world_size(),dist.get_rank()
    with torch.no_grad():
        for start in range(0,len(rows),world):
            row=rows[start+rank] if start+rank<len(rows) else None
            logits=engine(**model_batch(row,device)).logits
            total+=target_loss_sum(logits,row).double()*(row['row_weight'] if row is not None else 0.)
    dist.all_reduce(total)
    engine.train()
    return total.item()/len(rows)


def run(config,stage,run_id,resume=False,stop_after_batches=None):
    import deepspeed
    from transformers import AutoModelForCausalLM
    from transformers.integrations import HfDeepSpeedConfig
    version_check()
    if stop_after_batches is not None and (stage!='smoke' or stop_after_batches<1):
        raise ValueError('Early checkpoint stopping is only supported for a positive synthetic smoke boundary')
    local_rank=int(os.environ.get('LOCAL_RANK','0'))
    torch.cuda.set_device(local_rank)
    deepspeed.init_distributed(dist_backend='nccl')
    rank,world=dist.get_rank(),dist.get_world_size()
    t=config['training']
    if world!=t['world_size']:raise ValueError('world_size differs from registered configuration')
    if t['global_batch_size']%world:raise ValueError('global_batch_size must be divisible by world_size')
    seed=t['seed']+rank
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
    model_path=configured_path(config['model']['path'])
    release=configured_path(config['data']['release_dir'])
    rows,val,manifest=load_release(release,stage,model_path,allow_draft=stage=='smoke')
    if manifest['protocol']!=config['protocol']:raise ValueError('Data and runtime protocol differ')
    identity=rank0_result(lambda:verify_base(model_path,config['model']['expected_hashes'])) if stage!='smoke' else 'synthetic_smoke_not_7b'
    if not run_id or '/' in run_id or '\\' in run_id or run_id in ('.','..'):
        raise ValueError('run_id must be one directory component')
    root=configured_path(config['output']['root'])/run_id
    def initialize_directory():
        if root.exists() and not resume:raise ValueError('Run exists; use --resume or a new run_id')
        if not root.exists() and resume:raise ValueError('Resume run missing')
        root.mkdir(parents=True,exist_ok=True)
        return str(root)
    rank0_result(initialize_directory)
    batches=global_batches(len(rows),t['global_batch_size'],t['seed'])
    signature={'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
               'source_hashes':{p.name:sha256(p) for p in Path(__file__).parent.glob('*.py')},
               'config_sha256':sha256(config['_config_path']), 'manifest_sha256':sha256(release/'manifest.json'),
               'model_identity':identity,'world_size':world,'stage':stage}
    ds_config=json.loads(Path(config['backend']['config']).read_text())
    ds_config.update(train_batch_size=t['global_batch_size'],train_micro_batch_size_per_gpu=1,
                     gradient_accumulation_steps=t['global_batch_size']//world,gradient_clipping=t['clip_grad'])
    ds_config['optimizer']['params'].update(lr=t['learning_rate'],betas=t['betas'],weight_decay=t['weight_decay'])
    # 先激活 ZeRO 初始化上下文，防止每卡先加载完整 7B。
    hf_ds_config=HfDeepSpeedConfig(ds_config)
    model=AutoModelForCausalLM.from_pretrained(model_path,torch_dtype=torch.float16,
                attn_implementation=config['model']['attention'],local_files_only=True)
    model.config.use_cache=False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
    parameters=sum(p.ds_numel if hasattr(p,'ds_numel') else p.numel() for p in model.parameters())
    def check_space():
        budget=training_disk_budget(parameters,config['output'].get('disk_margin_ratio',0.1))
        budget['available_bytes']=shutil.disk_usage(root).free
        # A complete checkpoint already occupies disk on resume; avoid reserving
        # that same checkpoint a second time against the remaining free space.
        existing=0
        latest=root/'checkpoints/latest.json'
        if resume and latest.is_file():
            tag=json.loads(latest.read_text())['tag']
            checkpoint=(root/'checkpoints'/tag).resolve()
            if checkpoint.parent==(root/'checkpoints').resolve() and (checkpoint/'complete.json').is_file():
                existing=sum(min(p.stat().st_size,p.stat().st_blocks*512) for p in checkpoint.rglob('*') if p.is_file())
        budget['existing_checkpoint_credit_bytes']=min(existing,budget['checkpoint_bytes'])
        budget['required_free_bytes']-=budget['existing_checkpoint_credit_bytes']
        if budget['available_bytes']<budget['required_free_bytes']:
            raise ValueError('Insufficient disk for sequential checkpoint/export phases: '+json.dumps(budget))
        return budget
    disk_budget=rank0_result(check_space)
    warmup=max(1,math.ceil(len(batches)*t['warmup_ratio']))
    def scheduler(optimizer):
        def factor(step):
            if step<warmup:return step/max(1,warmup)
            return .5*(1+math.cos(math.pi*min(1.,(step-warmup)/max(1,len(batches)-warmup))))
        return torch.optim.lr_scheduler.LambdaLR(optimizer,factor)
    engine,optimizer,_,lr_scheduler=deepspeed.initialize(model=model,model_parameters=model.parameters(),config=ds_config,lr_scheduler=scheduler)
    state={'cursor':0,'updates':0}
    if resume:state=load_checkpoint(engine,root/'checkpoints',signature)
    if rank==0:
        write_json(root/'run.json',{'signature':signature,'base_commit':BASE_COMMIT,'resolved_model_path':str(model_path),
                   'parameters':parameters,'trainable_parameters':sum(p.ds_numel if hasattr(p,'ds_numel') else p.numel() for p in model.parameters() if p.requires_grad),
                   'planned_batches':len(batches),'training_rows':len(rows),'validation_rows':len(val),
                   'warmup_updates':warmup,'backend':ds_config,'disk_budget':disk_budget,'mode':stage,'status':'running'})
    device=torch.device('cuda',local_rank)
    previous_probe=parameter_probe(engine.module)
    engine.train()
    log=(root/'metrics.jsonl').open('a',encoding='utf-8') if rank==0 else None
    try:
        for batch_index in range(state['cursor'],len(batches)):
            batch=batches[batch_index]
            slots=micro_slots(batch,world)
            measured=torch.zeros((),device=device)
            skipped_before=engine.skipped_steps
            lr_used=optimizer.param_groups[0]['lr']
            if rank==0:print(json.dumps({'phase':'training_batch_start','batch':batch_index+1,'rows':len(batch),'lr_used':lr_used}),flush=True)
            for micro_index,slot in enumerate(slots):
                index=slot[rank]
                row=rows[index] if index is not None else None
                engine.set_gradient_accumulation_boundary(micro_index==len(slots)-1)
                logits=engine(**model_batch(row,device)).logits
                loss=backward_loss(logits,row,len(batch),world)
                if not torch.isfinite(loss):raise FloatingPointError('Nonfinite target loss')
                measured+=loss.detach()
                # 已按真实全局 batch 归一化，禁止引擎再除配置 GAS。
                engine.backward(loss,scale_wrt_gas=False)
                engine.step()
            dist.all_reduce(measured)
            applied=engine.skipped_steps==skipped_before
            current_probe=parameter_probe(engine.module)
            differences=[current_probe[name]-value for name,value in previous_probe.items()]
            changed=sum(int(torch.count_nonzero(value)) for value in differences)
            max_delta=max((float(value.abs().max()) for value in differences),default=0.)
            previous_probe=current_probe
            grad_norm=engine.get_global_grad_norm()
            grad_norm=float(grad_norm) if grad_norm is not None else None
            if applied and (grad_norm is None or not math.isfinite(grad_norm)):
                raise FloatingPointError('Successful optimizer update needs finite gradient norm')
            state={'cursor':batch_index+1,'updates':state['updates']+int(applied)}
            metric={'batch':state['cursor'],'actual_updates':state['updates'],'actual_batch_rows':len(batch),
                    'loss':measured.item()/world,'lr':optimizer.param_groups[0]['lr'],'overflow_skipped':not applied,
                    'lr_used':lr_used,'grad_norm':grad_norm,
                    'sampled_fp16_values_changed':changed,'sampled_values':sum(x.numel() for x in current_probe.values()),
                    'max_abs_fp16_delta':max_delta,
                    'peak_gpu_bytes':torch.cuda.max_memory_allocated(device)}
            if rank==0:log.write(json.dumps(metric)+'\n');log.flush();print(json.dumps(metric),flush=True)
            if state['cursor']%config['output']['save_every_batches']==0 or state['cursor']==len(batches):
                save_checkpoint(engine,root/'checkpoints',state['cursor'],state['updates'],signature)
            if stop_after_batches is not None and state['cursor']>=stop_after_batches:
                save_root=root/'checkpoints'
                if not (save_root/f'step_{state["cursor"]:08d}'/'complete.json').exists():
                    save_checkpoint(engine,save_root,state['cursor'],state['updates'],signature)
                break
        val_loss=validate(engine,val,device)
        if state['updates']<1:raise FloatingPointError('No successful optimizer updates')
        if rank==0:
            write_json(root/'result.json',dict(state,validation_loss=val_loss,status='complete' if state['cursor']==len(batches) else 'stopped_at_checkpoint',stage=stage,
                         formal_training_run=stage!='smoke',resume_verified=False,export_verified=False))
        if state['cursor']==len(batches) and ds_config['zero_optimization'].get('offload_optimizer',{}).get('device')=='nvme':
            from .export import export_native
            def export_destination():
                if (root/'hf').exists():raise ValueError('Do not overwrite existing HF export')
                return str(root/'hf')
            destination=rank0_result(export_destination)
            export_native(engine,destination,model_path,{'signature':signature,'state':state})
    finally:
        if log:log.close()
        # 对象保持到训练结束，HF 初始化的 ZeRO 配置不能提前被垃圾回收。
        del hf_ds_config
        dist.destroy_process_group()


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--stage',choices=['pilot','full','smoke'],required=True)
    p.add_argument('--run-id',required=True);p.add_argument('--resume',action='store_true')
    p.add_argument('--stop-after-batches',type=int)
    args=p.parse_args()
    try:run(load_config(args.config),args.stage,args.run_id,args.resume,args.stop_after_batches)
    finally:
        if dist.is_initialized():dist.destroy_process_group()

if __name__=='__main__':main()
