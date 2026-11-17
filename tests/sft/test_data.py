import copy
import json
from pathlib import Path
import pytest
from search_sft.common import normalize,sha256
from search_sft.data import global_batches,micro_slots,load_release
from search_sft.prepare import EvaluationIndex,load_evaluations,materialize,prior_knowledge_reasons,split_questions
from search_sft.protocol import ReplayError,assistant_target,compile_trajectory,observation_ids


class CharacterTokenizer:
    chat_template=None
    def encode(self,text,**kwargs):return [ord(c) for c in text]
    def decode(self,ids,**kwargs):return ''.join(chr(i) for i in ids)


LIMITS={'max_target_tokens':256,'max_observation_tokens':2048,'max_total_tokens':4096,'max_turns':10}


def turn(action,value,thought,documents=None):
    return {'action':action,'value':value,'response':{'choices':[{'message':{'content':f'<think>{thought}</think><{action}>{value}</{action}>'}}]},'observation':documents}


def trajectory():
    return {'id':'q1','source':'hotpotqa','status':'accepted','question':'Where is the birthplace of Person A?',
            'golden_answers':['Zedland'],'turns':[
                turn('search','Person A birthplace','Find the birthplace.',[{'document':{'contents':'Person A\nBorn in Town B.'}}]),
                turn('search','Town B country','Find the country.',[{'document':{'contents':'Town B\nLocated in Zedland.'}}]),
                turn('answer','Zedland','The evidence is sufficient.')]}


def test_each_row_has_only_past_observations_and_current_target():
    tokenizer=CharacterTokenizer();rows=compile_trajectory(trajectory(),tokenizer,LIMITS)
    assert len(rows)==3
    first=tokenizer.decode(rows[0]['input_ids'][:rows[0]['prompt_length']])
    second=tokenizer.decode(rows[1]['input_ids'][:rows[1]['prompt_length']])
    third=tokenizer.decode(rows[2]['input_ids'][:rows[2]['prompt_length']])
    assert 'Born in Town B.' not in first
    assert 'Born in Town B.' in second and 'Located in Zedland.' not in second
    assert 'Located in Zedland.' in third
    for row in rows:
        target=tokenizer.decode(row['input_ids'][-row['target_length']:])
        assert target.startswith('<think>') and '<information>' not in target
        assert len(row['input_ids'])==row['prompt_length']+row['target_length']


@pytest.mark.parametrize('kind',['native','inner_action','mismatch','future_answer'])
def test_invalid_trajectory_is_rejected(kind):
    x=trajectory()
    if kind=='native':x['turns'][0]['response']['choices'][0]['message']['reasoning_content']='private'
    if kind=='inner_action':x['turns'][0]=turn('search','x','Example <search>bad</search>',[])
    if kind=='mismatch':x['turns'][0]['value']='different'
    if kind=='future_answer':x['turns'].insert(0,turn('answer','Zedland','Answer early.'))
    with pytest.raises(ReplayError):compile_trajectory(x,CharacterTokenizer(),LIMITS)


def test_overlength_target_and_forced_context_are_not_silently_truncated():
    x=trajectory();x['turns'][0]=turn('search','x','a'*300,[])
    with pytest.raises(ReplayError,match='target_budget'):compile_trajectory(x,CharacterTokenizer(),LIMITS)
    with pytest.raises(ReplayError):compile_trajectory(trajectory(),CharacterTokenizer(),dict(LIMITS,max_total_tokens=800))


def test_structured_observation_preserves_tags_and_headers():
    tokenizer=CharacterTokenizer()
    text='\n\n<information>Doc 1(Title: A) '+'a'*200+'\nDoc 2(Title: B) '+'b'*200+'</information>\n\n'
    ids,cut=observation_ids(text,tokenizer,180)
    value=tokenizer.decode(ids)
    assert cut and len(ids)<=180
    assert value.startswith('\n\n<information>') and value.endswith('</information>\n\n')
    assert 'Doc 1(Title: A)' in value and 'Doc 2(Title: B)' in value


def test_prior_filter_distinguishes_question_candidates_and_list_numbers():
    x=trajectory();x['turns'][0]=turn('search','x','It is Zedland. Verify.',[])
    assert prior_knowledge_reasons(x)==['pre_search_gold_not_in_question']
    x['question']='Is it Zedland or Otherland?'
    assert prior_knowledge_reasons(x)==['pre_search_gold_already_in_question_quarantine']
    x=trajectory();x['golden_answers']=['1'];x['turns'][0]=turn('search','x','1. Find the birthplace.',[])
    assert not prior_knowledge_reasons(x)


def test_splits_keep_question_groups_and_pilot_is_subset():
    questions=[{'id':str(i),'source':'nq' if i%3==0 else 'hotpotqa','question':f'Question {i}',
                'samples':[{'target_length':i%3+1} for _ in range(i%2+1)]} for i in range(40)]
    splits=split_questions(questions,42,.1,12)
    train={x['id'] for x in splits['train']};val={x['id'] for x in splits['val']};pilot={x['id'] for x in splits['pilot']}
    assert not train&val and pilot<=train and len(pilot)==12
    assert split_questions(questions,42,.1,12)==splits
    rows=materialize(splits['train'])
    # 每题整段 token 之和乘权重后相等，避免多轮题自动获得更多权重。
    masses=[sum(s['target_length'] for s in q['samples'])*len(rows)/(len(train)*sum(s['target_length'] for s in q['samples'])) for q in splits['train']]
    assert max(masses)==min(masses)


def test_tail_batch_has_no_repeated_real_row():
    batches=global_batches(35,32,42)
    assert list(map(len,batches))==[32,3]
    assert sorted(i for b in batches for i in b)==list(range(35))
    slots=micro_slots(batches[-1],2)
    assert slots[-1][-1] is None
    assert sorted(i for s in slots for i in s if i is not None)==sorted(batches[-1])


def test_evaluation_exclusions_verify_files_and_detect_near_duplicate(tmp_path):
    f=tmp_path/'eval.jsonl';f.write_text(json.dumps({'id':'eval1','question':'What city was the famous writer Charles born in?'})+'\n')
    manifest=tmp_path/'manifest.json'
    manifest.write_text(json.dumps({'complete':True,'sets':[{'name':'D256','path':'eval.jsonl','sha256':sha256(f)}]}))
    index,evidence,complete=load_evaluations(manifest,['D256','T1024'])
    assert not complete and evidence[0]['rows']==1
    assert index.matches({'id':'eval1','question':'Different'})=='evaluation_id_overlap'
    assert index.matches({'id':'x','question':'What city was the famous writer Charles born in ?'})=='evaluation_question_overlap'
    assert index.matches({'id':'x','question':'What city was the famous writer Charles born in?!'})=='evaluation_question_overlap'
    f.write_text('changed')
    with pytest.raises(ValueError,match='hash mismatch'):load_evaluations(manifest,['D256'])


def test_formal_training_rejects_draft_release(tmp_path):
    (tmp_path/'manifest.json').write_text(json.dumps({'status':'draft','evaluation_exclusions_complete':False}))
    with pytest.raises(ValueError,match='final decontaminated'):load_release(tmp_path,'full','unused')


def test_release_detects_tokenizer_change(tmp_path,monkeypatch):
    (tmp_path/'manifest.json').write_text(json.dumps({'status':'final','evaluation_exclusions_complete':True,'tokenizer_hashes':{'tokenizer.json':'old'}}))
    monkeypatch.setattr('search_sft.data.tokenizer_identity',lambda p:{'tokenizer.json':'new'})
    with pytest.raises(ValueError,match='Tokenizer changed'):load_release(tmp_path,'full','unused')


def test_release_rejects_cross_split_question_even_with_valid_hashes(tmp_path,monkeypatch):
    f=tmp_path/'rows.jsonl';f.write_text(json.dumps({'question_id':'shared'})+'\n')
    file={'path':f.name,'sha256':sha256(f)}
    (tmp_path/'manifest.json').write_text(json.dumps({'status':'final','evaluation_exclusions_complete':True,'tokenizer_hashes':{},'files':{'train':file,'val':file}}))
    monkeypatch.setattr('search_sft.data.tokenizer_identity',lambda p:{})
    with pytest.raises(ValueError,match='crosses train'):load_release(tmp_path,'full','unused')
