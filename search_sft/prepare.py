"""将成功教师轨迹编译为可追溯的逐轮监督数据。"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import difflib
import hashlib
import json
from pathlib import Path
import re

from . import BASE_COMMIT, FORMAT_VERSION
from .common import configured_path, contains, load_config, normalize, read_jsonl, sha256, tokenizer_identity, write_json, write_jsonl
from .protocol import PROMPT, ReplayError, assistant_target, compile_trajectory, reasoning

MEMORY = re.compile(r'rely on (?:my|general)|based on (?:my|general|common) knowledge|from memory|I (?:recall|know from)', re.I)


def prior_knowledge_reasons(row):
    first = reasoning(row['turns'][0]['response']['choices'][0]['message'].get('content') or '')
    first = re.sub(r'(?m)^\s*\d+[.)]\s+', '', first)
    matched = [g for g in row['golden_answers'] if contains(g, first)]
    reasons = []
    if any(not contains(g, row['question']) for g in matched):
        reasons.append('pre_search_gold_not_in_question')
    elif matched:
        reasons.append('pre_search_gold_already_in_question_quarantine')
    final = reasoning(row['turns'][-1]['response']['choices'][0]['message'].get('content') or '')
    if MEMORY.search(final):
        reasons.append('final_memory_language_quarantine')
    return reasons


def question_from_record(row):
    if row.get('question'):
        return str(row['question'])
    prompt = row.get('prompt')
    if prompt is None:
        raise ValueError('Evaluation row lacks question/prompt')
    if not isinstance(prompt, str):
        prompt = prompt[0]['content']
    return prompt.split('Question:', 1)[-1].strip()


class EvaluationIndex:
    """排除 ID、规范化文本及高度相似题；清单身份由发布者显式确认。"""
    def __init__(self):
        self.ids, self.questions = set(), set()
        self.words, self.inverted = [], defaultdict(set)

    def add(self, row):
        for key in ('id', 'question_id', 'original_id'):
            if row.get(key) is not None:
                self.ids.add(str(row[key]))
        q = normalize(question_from_record(row))
        if q not in self.questions:
            self.questions.add(q)
            index = len(self.words)
            self.words.append(q)
            for word in set(q.split()):
                self.inverted[word].add(index)

    def matches(self, row):
        if any(str(row[k]) in self.ids for k in ('id', 'original_id') if row.get(k) is not None):
            return 'evaluation_id_overlap'
        q = normalize(row['question'])
        if q in self.questions:
            return 'evaluation_question_overlap'
        words = set(q.split())
        if len(words) >= 4:
            counts = Counter(i for w in words for i in self.inverted.get(w, ()))
            for i, overlap in counts.items():
                other = self.words[i]
                if overlap >= .9 * len(words) and .9 <= len(other) / max(1, len(q)) <= 1.1:
                    if difflib.SequenceMatcher(None, q, other, autojunk=False).ratio() >= .95:
                        return 'evaluation_near_duplicate'
        return None


def load_evaluations(path, required_names):
    index, evidence = EvaluationIndex(), []
    if path is None or not path.is_file():
        return index, evidence, False
    manifest = json.loads(path.read_text(encoding='utf-8'))
    names = set()
    for item in manifest['sets']:
        f = Path(item['path'])
        if not f.is_absolute():
            f = path.parent / f
        if sha256(f) != item['sha256']:
            raise ValueError('Evaluation file hash mismatch: ' + str(f))
        rows = read_jsonl(f) if f.suffix == '.jsonl' else None
        if f.suffix == '.parquet':
            import pandas as pd
            rows = pd.read_parquet(f).to_dict('records')
        if rows is None:
            raise ValueError('Evaluation input must be jsonl/parquet')
        count = 0
        for row in rows:
            index.add(row)
            count += 1
        if not count:
            raise ValueError('Empty evaluation set: ' + item['name'])
        names.add(item['name'])
        evidence.append(dict(item, rows=count, path=str(f.resolve())))
    complete = manifest.get('complete') is True and set(required_names) <= names
    return index, evidence, complete


def split_questions(questions, seed, val_ratio, pilot_size):
    groups = defaultdict(list)
    for row in questions:
        groups[row['source']].append(row)
    def key(row, prefix):
        return hashlib.sha256((prefix + normalize(row['question'])).encode()).hexdigest()
    train, val = [], []
    for source, group in sorted(groups.items()):
        ordered = sorted(group, key=lambda x: key(x, str(seed) + ':'))
        n = round(len(group) * val_ratio)
        val.extend(ordered[:n]); train.extend(ordered[n:])
    if not train or not val:
        raise ValueError('Need nonempty train and validation question splits')
    pilot_size = min(pilot_size, len(train))
    counts = Counter(r['source'] for r in train)
    fractions = {s:pilot_size * n / len(train) for s,n in counts.items()}
    quota = {s:int(n) for s,n in fractions.items()}
    for s in sorted(counts, key=lambda s:(-(fractions[s]-quota[s]),s))[:pilot_size-sum(quota.values())]:
        quota[s] += 1
    pilot = []
    for source in sorted(counts):
        pilot.extend(sorted([r for r in train if r['source']==source], key=lambda x:key(x,'pilot'+str(seed)+':'))[:quota[source]])
    return {'train':train, 'val':val, 'pilot':pilot}


def materialize(questions):
    rows = []
    q, m = len(questions), sum(len(x['samples']) for x in questions)
    for item in questions:
        n = sum(x['target_length'] for x in item['samples'])
        for sample in item['samples']:
            # 题等权、题内 token 平均；行损失使用 token CE 总和，不能重复平均。
            rows.append(dict(sample, question_target_tokens=n, row_weight=m/(q*n)))
    return rows


def prepare(config, draft=False, output=None):
    from transformers import AutoTokenizer
    data = config['data']
    source = configured_path(data['raw_file'])
    if sha256(source) != data['raw_sha256']:
        raise ValueError('Raw data hash mismatch')
    model = configured_path(config['model']['path'])
    tokenizer = AutoTokenizer.from_pretrained(model, local_files_only=True)
    eval_path = configured_path(data['evaluation_manifest']) if data.get('evaluation_manifest') else None
    eval_index, eval_evidence, complete = load_evaluations(eval_path, data['required_evaluation_sets'])
    if not complete and not draft:
        raise ValueError('Complete verified evaluation exclusions required; use --draft for inspection only')
    destination = configured_path(output or data['release_dir'])
    if destination.exists():
        raise ValueError('Release directory already exists; choose a new version')
    rejects, usable, seen, counts = [], [], set(), Counter()
    for line, row in enumerate(read_jsonl(source), 1):
        counts['raw_questions'] += 1
        key = normalize(row['question'])
        reasons = []
        if key in seen:
            reasons.append('duplicate_question')
        else:
            seen.add(key)
            reasons.extend(prior_knowledge_reasons(row))
            overlap = eval_index.matches(row)
            if overlap:
                reasons.append(overlap)
        if not reasons:
            try:
                samples = compile_trajectory(row, tokenizer, config['protocol'], config['protocol'].get('prompt', PROMPT))
                if normalize(row['turns'][-1]['value']) not in {normalize(g) for g in row['golden_answers']}:
                    raise ReplayError('final_gold_mismatch')
                usable.append({'id':row['id'], 'source':row['source'], 'question':row['question'], 'source_line':line, 'samples':samples})
            except (ReplayError, KeyError, TypeError, IndexError) as error:
                reasons.append(str(error))
        if reasons:
            counts.update(reasons)
            rejects.append({'id':row['id'], 'source_line':line, 'reasons':reasons})
    splits = split_questions(usable, config['training']['seed'], data['validation_ratio'], data['pilot_questions'])
    destination.mkdir(parents=True)
    files, stats = {}, {}
    for name, questions in splits.items():
        rows = materialize(questions)
        f = destination / (name + '.jsonl')
        write_jsonl(f, rows)
        files[name] = {'path':f.name, 'sha256':sha256(f)}
        stats[name] = {'questions':len(questions), 'rows':len(rows), 'sources':dict(Counter(x['source'] for x in questions)), 'target_tokens':sum(x['target_length'] for x in rows)}
    write_jsonl(destination/'rejected.jsonl', rejects)
    # question_id、题目与原始行号放独立审计，训练 Dataset 不读取 gold 或原始 messages。
    write_jsonl(destination/'questions.jsonl', [{'id':x['id'],'question':x['question'],'source_line':x['source_line']} for x in usable])
    try:
        import subprocess
        code_commit = subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        code_commit = None
    manifest = {'version':FORMAT_VERSION, 'status':'draft' if draft else 'final', 'base_commit':BASE_COMMIT,
                'code_commit':code_commit, 'source_sha256':sha256(source), 'tokenizer_hashes':tokenizer_identity(model),
                'prompt':config['protocol'].get('prompt',PROMPT),
                'compiler_hashes':{p.name:sha256(p) for p in Path(__file__).parent.glob('*.py')},
                'protocol':config['protocol'], 'files':files, 'statistics':stats,
                'evaluation_exclusions_complete':complete, 'evaluation_evidence':eval_evidence,
                'filter_counts_overlapping':dict(counts), 'usable_questions':len(usable), 'seed':config['training']['seed']}
    write_json(destination/'manifest.json', manifest)
    print(json.dumps({'release':str(destination), 'status':manifest['status'], 'statistics':stats,'filter_counts':dict(counts)},ensure_ascii=False))
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    parser.add_argument('--draft', action='store_true')
    parser.add_argument('--output')
    args = parser.parse_args()
    prepare(load_config(args.config), args.draft, args.output)

if __name__ == '__main__':
    main()
