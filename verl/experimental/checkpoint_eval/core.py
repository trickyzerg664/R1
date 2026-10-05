"""CPU评价算法：确定性选题、过程诊断和配对统计，不依赖训练器或GPU。"""
import hashlib
import json
import math
import random
import re
from collections import Counter


def select_rows(rows, excluded, quotas, seed):
    """
    @brief 按来源哈希排序选取固定开发题，选择过程不读取模型回答。
    @param rows 包含question_id、source、question和target的题目列表。
    @param excluded 不允许选入的历史开发题ID集合。
    @param quotas 每个来源的正整数题数。
    @param seed 固定选题整数种子。
    @return 按来源及哈希顺序排列的题目列表。
    @raises ValueError ID重复、题数不足或配额无效时抛出。
    """
    identities = [row['question_id'] for row in rows]
    # 输入重复或配额无效属于资产错误，不能靠截取若干行掩盖。
    if len(identities) != len(set(identities)) or not quotas or any(n < 1 for n in quotas.values()):
        raise ValueError('Duplicate IDs or invalid quotas')
    result = []
    for source, count in quotas.items():
        # 仅对可用题排序；不依据标签难度或已见模型结果挑选问题。
        available = [row for row in rows if row['source'] == source and row['question_id'] not in excluded]
        ranked = sorted(available, key=lambda row: hashlib.sha256(
            json.dumps([int(seed), source, row['question_id']]).encode()).hexdigest())
        # 少于配额必须失败，避免六个模型比较不同大小的开发集。
        if len(ranked) < count:
            raise ValueError(f'Not enough {source} questions')
        result.extend(ranked[:count])
    return result


def label_flags(row):
    """
    @brief 在生成前标记时间指代或多部分答案风险，不擅自修改原始标签。
    @param row 含question和非空字符串列表target的原始题目。
    @return 风险理由列表；空列表不代表事实已由外部来源全部验证。
    @raises ValueError 标签为空或类型异常时抛出。
    """
    question = row['question'].casefold()
    target = row['target']
    # 空标签会把可回答问题全部判零，在任何生成开始前拒绝。
    if not isinstance(target, list) or not target or any(not isinstance(x, str) or not x.strip() for x in target):
        raise ValueError('Invalid answer label')
    flags = []
    # 先登记时间不明确的题；有显式历史年份仍保留理由供审查，绝不看回答后变更。
    if re.search(r'\b(current(?:ly)?|latest|most recent|last year|this week|this season|last time)\b', question):
        flags.append('题目含未说明参照日期的时间指代')
    if re.search(r'\b(how many farms|total population|how many seasons|record number|most stage wins)\b', question):
        flags.append('统计量或纪录可能随数据年代变化')
    # 只有明确要求两个部分且提供多个target时才标记，普通同义答案不误作组合。
    if len(target) > 1 and re.search(r'\bwho\b.*\band when\b', question):
        flags.append('问题要求人名和时间，原EM却将多个target作为任一可接受答案')
    return flags


def process_features(text):
    """
    @brief 检查模型文本的标签和查询重复，不将环境返回当作模型生成。
    @param text 仅含模型生成token解码的字符串。
    @return 标签闭合、模型自写information、重复查询等诊断字段。
    """
    stack, bad, nested = [], [], []
    # 堆栈同时检查闭合和嵌套次序，标签计数相等仍可能格式异常。
    for match in re.finditer(r'<(/?)(think|search|information|answer)>', text):
        close, tag = match.groups()
        if not close:
            # 嵌套本身记录下来；不会在本次评价中改变历史答案奖励。
            if tag == 'answer' and stack:
                nested.append(list(stack))
            stack.append(tag)
        elif stack and stack[-1] == tag:
            stack.pop()
        else:
            bad.append(match.group())
    queries = [' '.join(x.casefold().split()) for x in re.findall(r'<search>(.*?)</search>', text, re.S)]
    counts = Counter(queries)
    return {'format_anomaly': bool(stack or bad), 'unclosed_tags': stack,
            'misnested_closings': bad, 'nested_answer': bool(nested),
            'model_information': '<information>' in text,
            'answer_tag_count': text.count('<answer>'),
            'search_tag_count': text.count('<search>'),
            'exact_repeat_queries': sum(n - 1 for n in counts.values()),
            'model_hint': 'Hint:' in text}


def validate_prefix(records, expected_ids):
    """
    @brief 拒绝缺题、重复题或乱序的续跑前缀，避免把半批或另一题集并入结果。
    @param records 按批次提交的逐题结果列表。
    @param expected_ids 本次完整评价集的冻结顺序。
    @return 无。
    @raises ValueError 结果不是准确前缀或奖励不是二值时抛出。
    """
    ids = [row['question_id'] for row in records]
    # 准确前缀是续跑的最低要求：乱序、遗漏及复制题都不能提交。
    if ids != list(expected_ids[:len(ids)]) or len(ids) != len(set(ids)):
        raise ValueError('Evaluation records are not a unique ordered prefix')
    # 本评价采用二值EM，不能混入改变奖励定义的历史记录。
    if any(row['reward'] not in (0, 1) for row in records):
        raise ValueError('Nonbinary reward in evaluation records')


def summarize(records, excluded=()):
    """
    @brief 汇总单轨迹EM和过程失败，不将搜索标签数误作真实调用次数。
    @param records 含reward、extracted_answer、features和生成诊断的逐题记录。
    @param excluded 预先冻结的标注风险题ID集合，仅用于敏感性分析。
    @return 总体及按来源正确率、过程失败率、工具成本统计。
    @raises ValueError 子集为空或结果ID重复时抛出。
    """
    selected = [row for row in records if row['question_id'] not in set(excluded)]
    # 风险排除不得导致空分母，也不允许重复记录人为改变权重。
    if not selected or len({row['question_id'] for row in selected}) != len(selected):
        raise ValueError('Empty or duplicate evaluation set')
    n = len(selected)
    correct = sum(row['reward'] for row in selected)
    result = {'n': n, 'correct': correct, 'em': correct / n,
              'missing_answer': sum(row['extracted_answer'] is None for row in selected),
              'format_anomaly': sum(row['features']['format_anomaly'] for row in selected),
              'model_information': sum(row['features']['model_information'] for row in selected),
              'rewarded_model_information': sum(row['reward'] == 1 and row['features']['model_information'] for row in selected),
              'actual_search_queries': sum(row.get('actual_search_queries', 0) for row in selected),
              'generated_tokens': sum(row.get('generated_tokens', 0) for row in selected),
              'forced_final': sum(row.get('diagnostics', {}).get('forced_final', 0) for row in selected),
              'generation_limit_hits': sum(row.get('diagnostics', {}).get('generation_limit_hits', 0) for row in selected),
              'sources': {}}
    # 分来源分母由真实记录计算，不把原计划配额代替实际评分数量。
    for source in sorted({row['data_source'] for row in selected}):
        values = [row['reward'] for row in selected if row['data_source'] == source]
        result['sources'][source] = {'n': len(values), 'correct': sum(values), 'em': sum(values) / len(values)}
    return result


def paired_compare(before, after, excluded=(), seed=20261005, draws=10000):
    """
    @brief 对相同题目计算正确率变化、对错转换及配对bootstrap区间。
    @param before 较早模型的完整逐题结果。
    @param after 较晚模型的完整逐题结果。
    @param excluded 生成前登记的风险题ID集合。
    @param seed 重采样整数种子。
    @param draws 正整数重采样次数。
    @return 配对转换计数、差值区间和精确McNemar的未校正p值。
    @raises ValueError 两组ID、来源或标签不一致、样本为空时抛出。
    """
    a = {row['question_id']: row for row in before}
    b = {row['question_id']: row for row in after}
    # 先验证配对前提，再计算任何差值，防止结果看似合理但题目已变。
    if len(a) != len(before) or len(b) != len(after) or set(a) != set(b) or draws < 1:
        raise ValueError('Paired comparison requires the same unique IDs')
    # 同ID还须同标签及来源，否则分数不具备配对解释。
    for key in a:
        if a[key]['target'] != b[key]['target'] or a[key]['data_source'] != b[key]['data_source']:
            raise ValueError('Paired labels or sources changed')
    keys = [key for key in a if key not in set(excluded)]
    # 不为没有有效题目的子集构造零差值或虚假的置信区间。
    if not keys:
        raise ValueError('No paired questions')
    differences = [b[key]['reward'] - a[key]['reward'] for key in keys]
    improves = sum(x == 1 for x in differences)
    regresses = sum(x == -1 for x in differences)
    discordant = improves + regresses
    # 配对题目重采样保留同题关联；不能把结果解释成训练种子的波动区间。
    rng = random.Random(seed)
    n = len(keys)
    samples = sorted(sum(rng.choices(differences, k=n)) / n for _ in range(draws))
    lower = samples[int((draws - 1) * .025)]
    upper = samples[int((draws - 1) * .975)]
    p = min(1., 2 * sum(math.comb(discordant, i) for i in range(min(improves, regresses) + 1)) / 2 ** discordant) if discordant else 1.
    return {'n': n, 'improves': improves, 'regresses': regresses,
            'delta': sum(differences) / n, 'paired_bootstrap_95': [lower, upper],
            'mcnemar_p_uncorrected': p, 'bootstrap_seed': seed, 'bootstrap_draws': draws,
            'changed_ids': [key for key, delta in zip(keys, differences) if delta]}
