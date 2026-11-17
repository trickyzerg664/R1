"""运行前读取真实资源和资产身份；报告不等同于 7B 训练已验收。"""
from __future__ import annotations
import argparse
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import math
from . import BASE_COMMIT
from .common import configured_path, load_config, sha256, write_json


def training_disk_budget(parameters, margin_ratio=0.1):
    """当前 ZeRO-3/CPUAdam：FP32主权重+m+v=12字节/参数；梯度不进checkpoint。

    保存时新旧两份状态短暂共存；离线导出时旧状态已清理，因此取阶段峰值的最大值。
    基座权重须已存在，调用者传入的是剩余空间，不重复预留已经占用的基座文件。
    """
    if parameters < 1 or not math.isfinite(margin_ratio) or margin_ratio < 0:
        raise ValueError('Positive parameter count and nonnegative finite disk margin required')
    checkpoint = parameters * 12
    saving_peak = checkpoint * 2
    export_peak = checkpoint + parameters * 4
    return {'checkpoint_bytes':checkpoint, 'saving_peak_bytes':saving_peak,
            'export_peak_bytes':export_peak, 'margin_ratio':margin_ratio,
            'required_free_bytes':math.ceil(max(saving_peak,export_peak)*(1+margin_ratio))}


def verify_base(model_path, expected_path):
    expected = json.loads(Path(expected_path).read_text())
    root = Path(model_path)
    for name,digest in expected['hashes'].items():
        if not (root/name).is_file() or sha256(root/name)!=digest:
            raise ValueError('Historical Base file missing/changed: '+str(root/name))
    return expected['identity']


def report(config, check_model=False):
    import torch
    versions = {}
    for package in ('torch','transformers','deepspeed','numpy','PyYAML'):
        try: versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError: versions[package] = None
    root=Path.cwd()
    git=subprocess.run(['git','status','--porcelain'],capture_output=True,text=True)
    report={'official_base':BASE_COMMIT,'branch':subprocess.check_output(['git','branch','--show-current'],text=True).strip(),
            'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(), 'working_tree':git.stdout,
            'versions':versions, 'gpus':[], 'disk_free_bytes':shutil.disk_usage(root).free,
            'seven_b_training_verified':False,'model_identity_verified':False}
    for i in range(torch.cuda.device_count()):
        free,total=torch.cuda.mem_get_info(i)
        report['gpus'].append({'device':i,'name':torch.cuda.get_device_name(i),'capability':torch.cuda.get_device_capability(i),'free_bytes':free,'total_bytes':total})
    if Path('/proc/meminfo').exists():
        report['meminfo'] = Path('/proc/meminfo').read_text().splitlines()[:5]
    try:
        model=configured_path(config['model']['path'])
        report['model_path']=str(model)
        report['model_exists']=model.is_dir()
        if check_model:
            report['model_identity']=verify_base(model,config['model']['expected_hashes'])
            report['model_identity_verified']=True
    except ValueError as error:
        report['model_error']=str(error)
        if check_model:
            raise
    return report


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--check-model',action='store_true');p.add_argument('--output')
    args=p.parse_args();data=report(load_config(args.config),args.check_model)
    if args.output:write_json(args.output,data)
    print(json.dumps(data,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
