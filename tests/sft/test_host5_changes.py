import json
from pathlib import Path
import pytest
from search_sft.common import sha256
from search_sft.prepare import load_review, prepare
from test_data import CharacterTokenizer, trajectory, LIMITS


def test_review_is_bound_to_raw_identity_and_has_unique_decisions(tmp_path):
    path=tmp_path/'review.json'
    decision={'id':'q1','source_line':1,'verdict':'quarantine','reason':'missing second-hop evidence'}
    path.write_text(json.dumps({'source_sha256':'source-a','decisions':[decision]}))
    with pytest.raises(ValueError,match='source identity'):load_review(path,'source-b')
    path.write_text(json.dumps({'source_sha256':'source-a','decisions':[decision,decision]}))
    with pytest.raises(ValueError,match='duplicate'):load_review(path,'source-a')


def test_review_quarantine_is_enforced_and_keep_does_not_bypass_prior_filter(tmp_path,monkeypatch):
    import transformers
    rows=[]
    for index in range(20):
        row=trajectory();row.update(id=f'q{index}',question=f'Where is person number {index} located?')
        rows.append(row)
    rows[0]['turns'][0]['response']['choices'][0]['message']['content']='<think>It is Zedland, verify.</think><search>Person A birthplace</search>'
    source=tmp_path/'raw.jsonl'
    source.write_text(''.join(json.dumps(x)+'\n' for x in rows))
    review=tmp_path/'review.json'
    review.write_text(json.dumps({'source_sha256':sha256(source),'decisions':[
        {'id':'q0','source_line':1,'verdict':'keep','reason':'cannot override automated prior filter'},
        {'id':'q1','source_line':2,'verdict':'quarantine','reason':'missing second-hop evidence'}]}))
    monkeypatch.setattr(transformers.AutoTokenizer,'from_pretrained',lambda *a,**k:CharacterTokenizer())
    monkeypatch.setattr('search_sft.prepare.tokenizer_identity',lambda p:{'tokenizer.json':'fixture'})
    config={'model':{'path':str(tmp_path)},'data':{'raw_file':str(source),'raw_sha256':sha256(source),
        'release_dir':str(tmp_path/'release'),'review_manifest':str(review),'required_evaluation_sets':[],
        'validation_ratio':.1,'pilot_questions':4},'protocol':LIMITS,'training':{'seed':42}}
    result=prepare(config,draft=True)
    ids={json.loads(x)['id'] for x in (tmp_path/'release/questions.jsonl').read_text().splitlines()}
    assert 'q0' not in ids and 'q1' not in ids
    assert len(ids)==18
    assert result['semantic_review_evidence']['sha256']==sha256(review)


def test_failed_native_save_cannot_publish_success_metadata(tmp_path,monkeypatch):
    from search_sft.export import export_native
    class FailedEngine:
        def save_16bit_model(self,*args,**kwargs):return False
    with pytest.raises(RuntimeError,match='did not save'):
        export_native(FailedEngine(),tmp_path/'hf',tmp_path,{})
    assert not (tmp_path/'hf/sft_provenance.json').exists()
