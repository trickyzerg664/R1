from pathlib import Path
from collections import Counter
from difflib import SequenceMatcher
from search_sft.common import read_jsonl,write_json,sha256,normalize
import hashlib,json,re,statistics
from datetime import datetime

root=Path('/root/data/search-r1/sft-runs/common-comparison-20261121-v1')
import time
for _ in range(1440):
    f=root/'comparison.json'
    if f.is_file() and len(json.loads(f.read_text())['models'])==4:
        break
    p=root/'status.json'
    if p.is_file() and json.loads(p.read_text()).get('phase') in ('partial','evaluation_failed'):
        raise SystemExit('Evaluation exited before producing all four comparable results')
    time.sleep(15)
else:
    raise SystemExit('Timed out waiting for four-way comparison')
c=json.loads((root/'comparison.json').read_text())
meta=json.loads((root/'dataset-manifest.json').read_text())
def load(label):
   return {r['id']:r for r in read_jsonl(root/label/'trajectories.jsonl')}
models={m:load(m) for m in c['models']}
questions={r['id']:r for r in read_jsonl(root/'test_questions.jsonl')}
assert sha256(root/'test_questions.jsonl')==c['dataset_sha256']==meta['question_sha256']
assert all(set(q)==set(questions) and len(q)==331 for q in models.values())
def norm_query(q):
   return ' '.join(re.findall(r'[a-z0-9]+',q.lower()))
def near(a,b):
   sa,sb=set(a.split()),set(b.split())
   return len(sa&sb)/max(1,len(sa|sb))>=.75 or SequenceMatcher(None,a,b,autojunk=False).ratio()>=.88
def duplicate(tr):
   q=[norm_query(x) for x in tr['queries']]
   return any(near(a,b) for i,a in enumerate(q) for b in q[:i])
def check_em(r):
   if not r['answer']: return False
   pred=normalize(r['answer'])
   return bool(pred and any(normalize(g)==pred for g in r['golden_answers']))
def maybe_unsupported(r):
   return bool(r['strict_em'] and r['queries'] and not r['answer_literal_in_visible_retrieval'])
def flags(tr,flag):
   return flag in tr['flags']
metrics={}
for model, by_id in models.items():
   rr=list(by_id.values())
   assert all(all(r[k]==questions[r['id']][k] for k in ('question','source','golden_answers')) and check_em(r)==r['strict_em'] for r in rr)
   assert sum(check_em(r) for r in rr)==c['models'][model]['overall']['correct']
   assert all(sum(len(t.get('retrieved',[])) for t in r['turns'])==3*len(r['queries']) for r in rr)
   metrics[model]=dict(exact_or_near_queries=sum(duplicate(r) for r in rr),exact_queries=sum(flags(r,'exact_repeat_query') for r in rr),
                       identical_top3=sum(flags(r,'same_top3_in_same_order') for r in rr),
                       generated_information_tags=sum(flags(r,'model_generated_information_tag') for r in rr),
                       missing_think_tags=sum(flags(r,'missing_think_tags') for r in rr),
                       answer_recovered_from_bad_format=sum(flags(r,'answer_recovered_from_invalid_protocol') for r in rr),
                       no_answer=sum(not r['answer'] for r in rr),
                       forced_final_attempts=sum(any(t['forced_reason'] for t in r['turns']) for r in rr),
                       stops=dict(Counter(r['stop_reason'] for r in rr)),
                       lexical_evidence_candidates=sum(maybe_unsupported(r) for r in rr),
                       correctly_answered_without_search=sum(r['strict_em'] and not r['queries'] for r in rr))
pairs=[]
seen=set()
def sample(category,criterion,limit):
   ranked=sorted((id for id in questions if criterion(id) and id not in seen),
                 key=lambda id:hashlib.sha256((category+id).encode()).digest())
   for id in ranked[:limit]:
       rows={}
       for m,q in models.items():
           r=q[id]
           rows[m]={'strict_em':r['strict_em'],'answer':r['answer'],'stop':r['stop_reason'],'flags':r['flags'],
                    'turns':[dict(text=t['generated'],titles=[z['title'] for z in t.get('retrieved',[])]) for t in r['turns']]}
       pairs.append(dict(category=category,id=id,question=questions[id]['question'],gold=questions[id]['golden_answers'],models=rows))
       seen.add(id)
sample('SFT correct, Base incorrect',lambda id:models['sft-full'][id]['strict_em'] and not models['qwen25-7b-base'][id]['strict_em'],2)
sample('Base correct, SFT incorrect',lambda id:not models['sft-full'][id]['strict_em'] and models['qwen25-7b-base'][id]['strict_em'],2)
sample('SFT alone correct',lambda id: models['sft-full'][id]['strict_em'] and not any(q[id]['strict_em'] for m,q in models.items() if m!='sft-full'),2)
sample('both GRPO correct, SFT incorrect',lambda id: not models['sft-full'][id]['strict_em'] and all(models[m][id]['strict_em'] for m in ('official-grpo-v02','historical-grpo-ckpt80')),2)
for model,q in models.items():
   sample(model+' repetition or budget',lambda id:duplicate(q[id]) and q[id]['stop_reason']!='natural_answer',1)
   sample(model+' correct answer, check evidence',lambda id:maybe_unsupported(q[id]),1)
audit={'time':datetime.now().astimezone().isoformat(),'n':331,'metrics':metrics,'method':'Exact or near query comparison uses word-set Jaccard >=.75 or string similarity >=.88. Lexical evidence flags require passage-level manual review.',
       'paired_examples':pairs}
write_json(root/'trajectory-comparison.json',audit)
print(json.dumps({'metrics':metrics,'example_ids':[(r['category'],r['id']) for r in pairs]},ensure_ascii=False))
for e in pairs:
 print(json.dumps(e,ensure_ascii=False))

result='; '.join(f"{k} {m['overall']['correct']}/331" for k,m in c['models'].items())
for f in (Path('docs/experiments/sft/HANDOFF.md'),Path('docs/experiments/sft/runs/host5-full-20261120-v2.md')):
    with f.open('a',encoding='utf-8') as stream:
        stream.write(f"\n- {audit['time']} Four-model same-questions evaluation complete on host5/lzy ({result}). Common holdout excludes the entire official published train, historical P10000, and raw SFT teacher pool by normalized/near-match screening. Official v0.2 deaa9d14b92dd4d481414e77b9f733c934df830a; historical GRPO quality action-stop step 80; verified Qwen2.5-7B Base; final SFT step 88. Deployments share Wiki18/E5 exact top-3 and the same decoding limits. Tagged search-only actions are executed and missing think tags are counted separately; earlier incompatible diagnostic preserved. Results: {root/'comparison.json'}, {root/'trajectory-comparison.json'}, and per-model trajectories.jsonl.\n")
