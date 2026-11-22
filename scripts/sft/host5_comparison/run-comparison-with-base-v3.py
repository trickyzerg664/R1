import gc
import math
import os
import random
import subprocess
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
import torch
from transformers import AutoTokenizer
from search_sft.common import read_jsonl,write_json,sha256
import json

root=Path('/root/data/search-r1/sft-runs')
base=root/'common-comparison-20261121-v1'
questions=base/'test_questions.jsonl'
manifest=json.loads((base/'dataset-manifest.json').read_text())
assert sha256(questions)==manifest['question_sha256']
configured={
 'sft-full':root/'host5-full-20261120-v2/hf',
 'qwen25-7b-base':Path.cwd()/'.cache/models/Qwen2.5-7B',
 'official-grpo-v02':base/'weights/official-grpo-v02',
 'historical-grpo-ckpt80':base/'weights/historical-grpo-ckpt80'}
evidence={label:model/('sft_provenance.json' if label=='sft-full' else 'COMPLETE.json') for label,model in configured.items()}
evidence['qwen25-7b-base']=base/'base-model-verification.json'
shared={}
compiled=compile((base/'evaluate-common-v3.py').read_text(),str(base/'evaluate-common-v3.py'),'exec')
tok=AutoTokenizer.from_pretrained(configured['sft-full'],local_files_only=True)
finished=[]
def status(phase, model=None, **details):
    rec=dict(time=datetime.now().astimezone().isoformat(),phase=phase,model=model,finished=finished.copy(),**details)
    write_json(base/'status.json',rec)
    print(json.dumps(rec),flush=True)
pending=[label for label in configured if not (base/label/'summary.json').is_file()]
finished.extend(label for label in configured if label not in pending)
while pending:
    available=[label for label in pending if evidence[label].is_file()]
    if not available:
        status('waiting_weights',None,waiting=pending)
        def active_download():
            for entry in Path('/proc').glob('[0-9]*/cmdline'):
                try:
                    args=[a.decode(errors='replace') for a in entry.read_bytes().split(bytes([0]))]
                except OSError:
                    continue
                if any(a.startswith(str(base)+'/download-') and a.endswith('.py') for a in args):
                    return True
            return False
        while not available and active_download():
            time.sleep(15)
            available=[label for label in pending if evidence[label].is_file()]
        if not available:
            status('partial',missing=pending)
            raise SystemExit(2)
    label=available[0]
    pending.remove(label)
    model_path=configured[label]
    model_out=base/label
    model_out.mkdir(exist_ok=True)
    ns=dict(model_path=model_path,model_label=label,model_evidence=evidence[label],out=model_out,questions_file=questions,
            dataset_manifest=manifest,common_tokenizer=tok,shared_retrieval=shared)
    status('evaluating',label)
    try:
        exec(compiled,ns)
    except Exception as error:
        status('evaluation_failed',label,error=f'{type(error).__name__}: {error}')
        raise
    del ns
    gc.collect()
    torch.cuda.empty_cache()
    finished.append(label)
    status('model_complete',label)

if len(finished)!=len(configured):
    status('partial',missing=sorted(set(configured)-set(finished)))
    raise SystemExit(2)
by_model={l:{r['id']:r for r in read_jsonl(base/l/'trajectories.jsonl')} for l in configured}
test_ids={r['id'] for r in read_jsonl(questions)}
assert all(len(m)==331 and set(m)==test_ids for m in by_model.values())
summary={l:json.loads((base/l/'summary.json').read_text()) for l in configured}
for label,traces in by_model.items():
    assert summary[label]['question_file_sha256']==manifest['question_sha256']
    assert sum(r['strict_em'] for r in traces.values())==summary[label]['overall']['correct']

paired={}
labels=list(configured)
order=sorted(test_ids)
for i,l in enumerate(labels):
    for k in labels[i+1:]:
        delta=[int(by_model[l][q]['strict_em'])-int(by_model[k][q]['strict_em']) for q in order]
        wins,losses=delta.count(1),delta.count(-1)
        rng=random.Random(20261121)
        reps=sorted(sum(rng.choices(delta,k=len(delta)))/len(delta) for _ in range(10000))
        n=wins+losses
        p=min(1.0,2*sum(math.comb(n,x) for x in range(min(wins,losses)+1))/2**n)
        paired[l+' vs '+k]={'delta_pp':100*sum(delta)/len(delta),'left_only_correct':wins,'right_only_correct':losses,
                             'paired_bootstrap_95ci_pp':[100*reps[249],100*reps[9749]],'mcnemar_exact_p_unadjusted':p}
write_json(base/'comparison.json',dict(n=331,dataset_sha256=manifest['question_sha256'],models=summary,paired=paired,
          limits=manifest['protocol'],prompt_tokenizer_sha256=sha256(configured['sft-full']/'tokenizer.json'),
          tensor_dtype='float16',model_source={l:str(p) for l,p in configured.items()}))
status('complete',n=331)
