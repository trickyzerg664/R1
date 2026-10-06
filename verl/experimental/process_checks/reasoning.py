"""推理诊断只报告可复核证据，语义支持与多跳关系保留未知状态。"""
import hashlib
import re


def normalized(text):
    """
    @brief 统一空白和大小写供引文及重复查询诊断使用。
    @param text 待比较字符串。
    @return 归一化字符串，不用于最终答案EM。
    """
    # 引文与查询只统一大小写和空白，不引入近义词或事实支持判断。
    return ' '.join(text.casefold().split())


def documents(observation, call_id):
    """
    @brief 从实际可见观察提取文档编号和内容，绑定真实调用。
    @param observation 程序记录的可见工具文本，可被上下文预算截断。
    @param call_id 所属真实调用ID。
    @return 带调用ID、文档编号、正文和内容哈希的列表。
    """
    # 文档编号在不同调用中重用，身份必须包含调用ID。
    headers = list(re.finditer(r'Doc\s+(\d+)\(Title:\s*([^\n]*?)\)\s*', observation))
    rows = []
    for i, match in enumerate(headers):
        end = headers[i + 1].start() if i + 1 < len(headers) else len(observation)
        body = observation[match.end():end].split('</information>')[0].strip()
        digest = hashlib.sha256(normalized(body).encode()).hexdigest()
        rows.append(dict(call_id=call_id, doc_id=match.group(1), title=match.group(2),
                         text=body, sha256=digest))
    return rows


def review_reasoning(text, evidence):
    """
    @brief 核查引文和文档引用，输出待人工或独立裁判复核的事实、冲突与多跳项。
    @param text 共用动作解析器定位的本轮动作之前文字，不含查询或答案。
    @param evidence 本轮生成前模型已见的文档列表；禁止加入本轮搜索后新结果。
    @return 诊断字典；exact_present只表示文字存在，不证明事实或推理成立。
    """
    # 调用方提供实际动作边界，引用或代码中的标签不能提前截断待审查文字。
    prefix = text
    quote_checks = []
    # 只定位明确引号中的较长文字，实际已见正文逐字匹配也仅标文字存在。
    for match in re.finditer(r'"([^"\n]{8,})"|“([^”\n]{8,})”', prefix):
        quote = match.group(1) or match.group(2)
        refs = [dict(call_id=d['call_id'], doc_id=d['doc_id']) for d in evidence
                if normalized(quote) in normalized(d['text'])]
        quote_checks.append(dict(text=quote, span=list(match.span()), references=refs,
                                 status='exact_present' if refs else 'unverified'))
    # 无限定调用的Doc编号只定位候选文档，不能证明模型指的是哪次搜索。
    citation_checks = []
    for match in re.finditer(r'\bDoc\s+(\d+)\b', prefix):
        refs = [dict(call_id=d['call_id'], doc_id=d['doc_id']) for d in evidence
                if d['doc_id'] == match.group(1)]
        citation_checks.append(dict(doc_id=match.group(1), span=list(match.span()), references=refs,
                                    status='available' if refs else 'unverified'))
    # 自动列出待审查的断言；文本重合或关键词命中不当作语义支持。
    claims = [dict(text=s.strip(), status='unknown') for s in
              re.split(r'(?<=[.!?。！？])\s+|\n+', prefix)
              if len(s.strip()) >= 12 and not s.lstrip().startswith(('```', '>'))][:32]
    multi_hop = [dict(text=c['text'], status='unknown') for c in claims
                 if re.search(r'\b(therefore|thus|hence|consequently)\b|因此|所以|由此', c['text'], re.I)]
    # 同一短语的不同数值只形成冲突候选，保留原文供复核，不能自动判谁对谁错。
    numeric = {}
    for doc in evidence:
        for match in re.finditer(r'([A-Za-z][A-Za-z \-]{3,55})\s+(is|was|were|became)\s+([^.!?\n]*\d[^.!?\n]*)', doc['text']):
            key = normalized(match.group(1) + ' ' + match.group(2))
            numeric.setdefault(key, []).append(dict(call_id=doc['call_id'], doc_id=doc['doc_id'],
                                                    text=match.group(0), values=re.findall(r'\d+', match.group(3))))
    conflicts = [dict(subject=k, evidence=v, status='unknown') for k, v in numeric.items()
                 if len({tuple(item['values']) for item in v}) > 1]
    return dict(quote_checks=quote_checks, citation_checks=citation_checks, claims=claims,
                multi_hop_checks=multi_hop, conflict_candidates=conflicts,
                semantic_review_status='requires_review' if claims else 'not_applicable')


def search_diagnostic(query, visible_documents, previous_calls):
    """
    @brief 分别记录重复查询、近似查询与没有新增文档，保持诊断不影响奖励。
    @param query 本次实际执行的查询字符串。
    @param visible_documents 本次模型实际可见的文档列表。
    @param previous_calls 本轨迹此前的成功调用及可见文档。
    @return 查询重复及新增文档数；重复但返回新证据不标冗余。
    """
    q = normalized(query)
    tokens = set(re.findall(r'\w+', q))
    exact = any(normalized(c['query']) == q for c in previous_calls)
    # 两个短查询共享词很常见，近似诊断要求至少三个词，仍不作惩罚。
    near = False
    for call in previous_calls:
        old = set(re.findall(r'\w+', normalized(call['query'])))
        if len(tokens) >= 3 and len(old) >= 3 and len(tokens & old) / len(tokens | old) >= .9:
            near = True
    # 新文档按可见正文内容去重；查询重复与是否新增证据分开记录。
    old_hashes = {d['sha256'] for c in previous_calls for d in c.get('documents', [])}
    new_count = len({d['sha256'] for d in visible_documents} - old_hashes)
    return dict(repeated_query=exact, near_duplicate_query=near, new_documents=new_count,
                redundant_search_candidate=bool((exact or near) and not new_count))
