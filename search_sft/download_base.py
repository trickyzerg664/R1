"""下载固定的公开Base快照，逐文件核对历史RL哈希；不启动或加载模型。"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import json
import os
from pathlib import Path
import shutil
from .common import sha256,write_json

REPOSITORY='Qwen/Qwen2.5-7B'
REVISION='d149729398750b98c0af14eb82c78cfe92750796'


def download(target,job,expected_file,endpoint,workers=4):
    # Hub常量在首次导入时读取endpoint；不使用私人仓库token下载公开模型。
    os.environ['HF_ENDPOINT']=endpoint
    os.environ.setdefault('HF_HUB_ETAG_TIMEOUT','20')
    os.environ.setdefault('HF_HUB_DOWNLOAD_TIMEOUT','30')
    os.environ['HF_HUB_DISABLE_PROGRESS_BARS']='1'
    from huggingface_hub import HfApi,hf_hub_download
    expected=json.loads(Path(expected_file).read_text())
    target=Path(target).resolve();job=Path(job).resolve()
    target.mkdir(parents=True,exist_ok=True);job.mkdir(parents=True,exist_ok=True)
    state={'repo':REPOSITORY,'revision':REVISION,'endpoint':endpoint,'target':str(target),
           'pid':os.getpid(),'phase':'checking_metadata','historical_identity':expected['identity'],
           'verified_files':{},'errors':{}}
    write_json(job/'status.json',state)
    print(json.dumps({'phase':state['phase'],'pid':state['pid'],'target':str(target)}),flush=True)
    try:
        if all((target/name).is_file() for name in expected['hashes']):
            actual={name:sha256(target/name) for name in expected['hashes']}
            if actual==expected['hashes']:
                state.update(phase='complete',verified_files=actual,bytes_verified=sum((target/n).stat().st_size for n in actual))
                write_json(job/'status.json',state);write_json(target/'base-verification.json',state)
                print(json.dumps({'phase':'complete','already_present':True,'verified_files':len(actual)}),flush=True)
                return state
        info=HfApi(endpoint=endpoint,token=False).model_info(REPOSITORY,revision=REVISION,files_metadata=True,timeout=30)
        entries={x.rfilename:x for x in info.siblings}
        for name,digest in expected['hashes'].items():
            if name.endswith('.safetensors'):
                lfs=entries[name].lfs
                remote_digest=lfs.get('sha256') if isinstance(lfs,dict) else getattr(lfs,'sha256',None)
                if remote_digest!=digest:raise ValueError('Historical shard metadata mismatch: '+name)
        total=sum(entries[n].size for n in expected['hashes'])
        existing=sum((target/n).stat().st_size for n in expected['hashes'] if (target/n).is_file())
        if shutil.disk_usage(target).free<max(0,total-existing)+2**30:
            raise ValueError('Insufficient space for one Base snapshot')
        state.update(phase='downloading',bytes_expected=total)
        write_json(job/'status.json',state)
        def one(name):
            path=target/name
            if path.is_file() and sha256(path)==expected['hashes'][name]:return name,expected['hashes'][name]
            local=Path(hf_hub_download(REPOSITORY,name,revision=REVISION,local_dir=str(target),token=False))
            digest=sha256(local)
            if digest!=expected['hashes'][name]:raise ValueError('SHA256 mismatch: '+name)
            return name,digest
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures={executor.submit(one,name):name for name in expected['hashes']}
            for future in as_completed(futures):
                name=futures[future]
                try:
                    name,digest=future.result();state['verified_files'][name]=digest
                    print(json.dumps({'verified_file':name,'completed':len(state['verified_files']),'total':len(expected['hashes'])}),flush=True)
                except Exception as error:
                    # 日志只保存错误类别，避免把CDN签名URL或运行环境凭证写入文档。
                    state['errors'][name]=type(error).__name__
                    print(json.dumps({'failed_file':name,'error':type(error).__name__}),flush=True)
                state['bytes_verified']=sum((target/n).stat().st_size for n in state['verified_files'])
                write_json(job/'status.json',state)
        if state['errors']:raise RuntimeError('Some files failed; inspect status.json and rerun to resume')
        state['phase']='complete'
        write_json(job/'status.json',state);write_json(target/'base-verification.json',state)
        print(json.dumps({'phase':'complete','bytes_verified':state['bytes_verified'],'verified_files':len(state['verified_files'])}),flush=True)
        return state
    except Exception as error:
        state.update(phase='failed',last_error=type(error).__name__)
        write_json(job/'status.json',state)
        raise


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--target',default='.cache/models/Qwen2.5-7B')
    p.add_argument('--job-dir',default='.cache/sft-base-download')
    p.add_argument('--expected',default='configs/sft/base_model_hashes.json')
    p.add_argument('--endpoint',default=os.environ.get('HF_ENDPOINT','https://huggingface.co'))
    p.add_argument('--workers',type=int,default=4)
    a=p.parse_args();download(a.target,a.job_dir,a.expected,a.endpoint,a.workers)

if __name__=='__main__':main()
