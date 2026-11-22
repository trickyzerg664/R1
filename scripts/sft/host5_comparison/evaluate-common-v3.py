import gc
import hashlib
import json
import os
import re
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import datasets
import faiss
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, StoppingCriteria, StoppingCriteriaList
from search_r1.search.retrieval_server import Encoder
from search_sft.common import normalize, contains, sha256, read_jsonl, write_json
from search_sft.protocol import ACTION, REMINDER, initial_ids, observation_ids, observation_text, reasoning

root = Path.cwd()
data = Path('/root/data/search-r1')
run = model_path
manifest = dataset_manifest
limits = manifest['protocol']
assert sha256(questions_file) == manifest['question_sha256']
rows = list(read_jsonl(questions_file))
assert len(rows) == 331 and len({r['id'] for r in rows}) == 331
# Deterministic interleaving by hash avoids a source-sorted prefix on restart.
rows.sort(key=lambda r: hashlib.sha256(r['id'].encode()).hexdigest())
trace_file = out/'trajectories.jsonl'
done = {}
if trace_file.exists():
    valid_bytes = 0
    with trace_file.open('rb') as stream:
        for line in stream:
            if not line.endswith(b'\n'):
                break
            rec = json.loads(line)
            assert rec['id'] not in done
            done[rec['id']] = rec
            valid_bytes += len(line)
    with trace_file.open('r+b') as stream:
        stream.truncate(valid_bytes)
assert set(done) <= {r['id'] for r in rows}

def stamp():
    return datetime.now().astimezone().isoformat()

def phase(name, **details):
    write_json(out/'status.json',dict(time=stamp(),phase=name,complete=len(done),total=len(rows),**details))
    print(stamp(),name,len(done),details,flush=True)

torch.set_num_threads(4)
faiss.omp_set_num_threads(8)
assert torch.cuda.is_available()
phase('loading_model')
tok = common_tokenizer
local_tok = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
assert local_tok.get_vocab() == tok.get_vocab(), 'Model tokenizer vocabulary is incompatible with the common prompt tokenizer'
del local_tok
tokenizer_sha256 = sha256(model_path/'tokenizer.json')
model = AutoModelForCausalLM.from_pretrained(model_path, local_files_only=True, torch_dtype=torch.float16,
    attn_implementation='sdpa').eval().to('cuda')
gc.collect()
if not shared_retrieval:
    phase('loading_retrieval')
    shard_dir = data/'cache/retriever/datasets/json'
    shards = sorted(shard_dir.rglob('json-train-*-of-00028.arrow'))
    assert len(shards) == 28
    corpus = datasets.concatenate_datasets([datasets.Dataset.from_file(str(f),in_memory=False) for f in shards])
    index = faiss.read_index(str(data/'retrieval/wiki18/e5_Flat.index'))
    assert index.ntotal == len(corpus) and index.d == 768 and index.is_trained
    encoder = Encoder('e5',str(data/'models/e5-base-v2'),'mean',256,False)
    shared_retrieval.update(index=index,corpus=corpus,encoder=encoder)
index,corpus,encoder=(shared_retrieval[k] for k in ('index','corpus','encoder'))
phase('evaluating',index_rows=index.ntotal,gpu=torch.cuda.get_device_name(0))

turn_limit = limits['max_turns']
target_cap = limits['max_target_tokens']
window = limits['max_total_tokens']
observation_cap = limits['max_observation_tokens']
reminder = tok.encode(REMINDER,add_special_tokens=False)
reserve = target_cap+len(reminder)+16
minimum_observation = len(tok.encode('\n\n<information></information>\n\n',add_special_tokens=False))+24
stop_mark = re.compile(r'</(?:search|answer)>')
model_eos = [151643,151645]
eos_ids = set(model_eos if isinstance(model_eos,list) else [model_eos])
pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
tag_other = re.compile(r'</?(?:think|search|answer|information)>',re.I)
action_only = re.compile(r'\s*<(search|answer)>(.*?)</\1>\s*',re.S)
action_in_text = re.compile(r'<(search|answer)>([^<>]+)</\1>',re.S)
control_tags = re.compile(r'</?(?:search|answer|information)>',re.I)
def extra_action(raw):
    matches=list(action_in_text.finditer(raw))
    if len(matches)!=1:
        return None
    action=matches[0]
    surrounding=raw[:action.start()]+raw[action.end():]
    if control_tags.search(surrounding) or not action[2].strip():
        return None
    return action[1],action[2].strip()


class ActionStop(StoppingCriteria):
    def __init__(self, width):
        self.width=width

    def __call__(self,input_ids,scores,**kwargs):
        suffix=input_ids[:,max(self.width,input_ids.shape[1]-16):].tolist()
        matches=[bool(stop_mark.search(tok.decode(r,skip_special_tokens=False))) for r in suffix]
        return torch.tensor(matches,device=input_ids.device,dtype=torch.bool)

def unpack(seq):
    kept=[]
    finish='target_limit'
    for token in seq:
        if token in eos_ids or token==pad:
            finish='eos'
            break
        kept.append(token)
    raw=tok.decode(kept,skip_special_tokens=False)
    close=stop_mark.search(raw)
    if close:
        finish='action_close'
    return kept,raw,finish

def retrieve(queries):
    scores, ids = index.search(encoder.encode(queries),3)
    return [[{'document':dict(corpus[int(doc)]),'score':float(score),'corpus_row':int(doc)}
         for doc,score in zip(group,score_group) if doc>=0] for group,score_group in zip(ids,scores)]

def make(item):
    prompt = initial_ids(item['question'],tok,manifest['prompt'])
    return dict(item,context=prompt,initial_tokens=len(prompt),turns=[],answer=None,stop_reason=None,
                flags=[],queries=[],observation_ids=[])

@torch.inference_mode()
def evaluate(items):
    group=[make(r) for r in items]
    for number in range(1,turn_limit+1):
        active=[r for r in group if r['stop_reason'] is None]
        if not active:
            break
        for r in active:
            reason = 'turn_budget' if number == turn_limit else (
                'context_budget' if window-len(r['context']) < reserve+target_cap+minimum_observation else None)
            r['forced_reason']=reason
            if reason:
                r['context'].extend(reminder)
        width=max(len(r['context']) for r in active)
        prompt=[([pad]*(width-len(r['context'])))+r['context'] for r in active]
        masks=[([0]*(width-len(r['context'])))+([1]*len(r['context'])) for r in active]
        max_new=min(target_cap,window-width)
        assert max_new>0
        sequences=model.generate(
            input_ids=torch.tensor(prompt,device='cuda'),
            attention_mask=torch.tensor(masks,device='cuda'),
            max_new_tokens=max_new, do_sample=False, num_beams=1, use_cache=True,
            eos_token_id=model_eos,pad_token_id=pad,
            stopping_criteria=StoppingCriteriaList([ActionStop(width)]))
        searching=[]
        for r,seq in zip(active,sequences[:,width:].tolist()):
            generated,raw,stop=unpack(seq)
            r['context'].extend(generated)
            parsed=ACTION.fullmatch(raw)
            turn={'turn':number,'generated':raw,'generated_tokens':len(generated),
                  'generation_stop':stop,'forced_reason':r['forced_reason']}
            r['turns'].append(turn)
            if re.search(r'</?information>',raw,re.I):
                r['flags'].append('model_generated_information_tag')
            if parsed and parsed[1].strip() and parsed[3].strip() and not tag_other.search(parsed[1]) and not tag_other.search(parsed[3]):
                reasoning_text,action,value=parsed[1].strip(),parsed[2],parsed[3].strip()
            else:
                action_match=action_only.fullmatch(raw)
                if action_match and action_match[2].strip() and not tag_other.search(action_match[2]):
                    action,value=action_match[1],action_match[2].strip()
                    reasoning_text=''
                    turn['missing_think_tags']=True
                    r['flags'].append('missing_think_tags')
                elif extra_action(raw):
                    action,value=extra_action(raw)
                    reasoning_text=reasoning(raw)
                    turn['noncanonical_action_wrapper']=True
                    r['flags'].append('noncanonical_action_wrapper')
                else:
                    answers=re.findall(r'<answer>([^<>]+)</answer>',raw,re.S)
                    if len(answers)==1 and answers[0].strip():
                        r['answer']=answers[0].strip()
                        r['flags'].append('answer_recovered_from_invalid_protocol')
                    r['stop_reason']='invalid_protocol'
                    r['flags'].append('invalid_protocol')
                    if stop=='target_limit':
                        r['flags'].append('target_token_limit')
                    continue
            turn.update(action=action,value=value,reasoning=reasoning_text)
            if action=='answer':
                r['answer']=value
                r['stop_reason']='forced_final' if r['forced_reason'] else 'natural_answer'
            elif r['forced_reason']:
                r['stop_reason']='search_after_forced_final'
                r['flags'].append('search_after_forced_final')
            else:
                key=normalize(value)
                if key in {normalize(q) for q in r['queries']}:
                    r['flags'].append('exact_repeat_query')
                r['queries'].append(value)
                searching.append((r,turn,value))
        if searching:
            found=retrieve([q for _,_,q in searching])
            for (r,turn,_),docs in zip(searching,found):
                budget=min(observation_cap,window-len(r['context'])-reserve)
                ids,truncated=observation_ids(observation_text(docs),tok,budget)
                r['context'].extend(ids)
                shown=tok.decode(ids,skip_special_tokens=False)
                matched=tuple(d['corpus_row'] for d in docs)
                if matched in r['observation_ids']:
                    r['flags'].append('same_top3_in_same_order')
                r['observation_ids'].append(matched)
                turn.update(visible_observation=shown,observation_tokens=len(ids),observation_truncated=truncated,
                    retrieved=[{'id':item['corpus_row'],'title':item['document']['contents'].split('\n',1)[0],
                                'score':item['score'],'contents':item['document']['contents']} for item in docs])
                if truncated:
                    r['flags'].append('observation_truncated')
    for r in group:
        del r['context'],r['forced_reason'],r['observation_ids']
        r['flags']=sorted(set(r['flags']))
        r['token_total']=r['initial_tokens']+sum(t['generated_tokens']+t.get('observation_tokens',0) for t in r['turns'])
        r['generated_tokens']=sum(t['generated_tokens'] for t in r['turns'])
        if not r['stop_reason']:
            r['stop_reason']='unfinished'
        a=normalize(r['answer']) if r['answer'] else ''
        r['strict_em']=bool(a and any(a==normalize(g) for g in r['golden_answers']))
        visible=' '.join(t.get('visible_observation','') for t in r['turns'])
        r['answer_literal_in_visible_retrieval']=bool(r['answer'] and contains(r['answer'],visible))
        r['first_turn_mentions_gold']=any(contains(g,reasoning(r['turns'][0]['generated'])) for g in r['golden_answers'] if not contains(g,r['question']))
    return group

pending=[r for r in rows if r['id'] not in done]
batch_size=int(os.environ.get('SFT_EVAL_BATCH','8'))
for i in range(0,len(pending),batch_size):
    wave_start=time.monotonic()
    observed=evaluate(pending[i:i+batch_size])
    with trace_file.open('a',encoding='utf-8') as stream:
        for rec in observed:
            stream.write(json.dumps(rec,ensure_ascii=False)+'\n')
            done[rec['id']]=rec
        stream.flush()
        os.fsync(stream.fileno())
    phase('evaluating',wave_seconds=round(time.monotonic()-wave_start,2))

def stats(seq):
    n=len(seq)
    hits=sum(r['strict_em'] for r in seq)
    return {'questions':n,'correct':hits,'strict_em':hits/n,
        'stop_reasons':dict(Counter(r['stop_reason'] for r in seq)),
        'flags':dict(Counter(flag for r in seq for flag in r['flags'])),
        'forced_final_attempts':sum(any(t.get('forced_reason') for t in r['turns']) for r in seq),
        'no_search':sum(not r['queries'] for r in seq),
        'mean_searches':sum(len(r['queries']) for r in seq)/n,
        'search_count_distribution':dict(sorted(Counter(len(r['queries']) for r in seq).items())),
        'mean_generated_tokens':sum(r['generated_tokens'] for r in seq)/n,
        'first_turn_mentions_gold':sum(r['first_turn_mentions_gold'] for r in seq),
        'correct_search_answers_absent_as_literal':sum(r['strict_em'] and bool(r['queries']) and not r['answer_literal_in_visible_retrieval'] for r in seq)}

all_records=[done[r['id']] for r in rows]
summary={'time':stamp(),'model':model_label,'question_file_sha256':sha256(questions_file),
    'model_provenance_sha256':sha256(model_evidence),'tokenizer_sha256':tokenizer_sha256,
    'retrieval':'Wiki18/E5-base-v2/CPU FAISS exact top3, FP32 E5',
    'decoding':'greedy; action-close stopping; bounded 10 turns, 4096 context, 256 generated tokens, 2048 observation',
    'action_parser':'execute one complete unique tagged action without tool-output injection; separately track missing think and noncanonical surrounding text',
    'overall':stats(all_records),
    'by_source':{s:stats([r for r in all_records if r['source']==s]) for s in sorted({r['source'] for r in rows})}}
write_json(out/'summary.json',summary)
phase('complete')
