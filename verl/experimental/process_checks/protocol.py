"""确定性动作解析和程序工具账本；模型不能自行声明工具来源。"""
from copy import deepcopy
import hashlib
import re
import uuid
from .reasoning import documents, review_reasoning, search_diagnostic

HARD_CODES = {'forged_observation', 'nested_action', 'empty_action', 'search_forbidden',
              'action_after_answer', 'action_parse_mismatch', 'call_result_mismatch'}


def digest(text):
    """
    @brief 为原始或可见文本计算完整性哈希。
    @param text 输入字符串。
    @return SHA256十六进制字符串；哈希不充当来源证明。
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def protected_text(text):
    """
    @brief 屏蔽代码、引用行及带标签的引号文字，保留原字符位置。
    @param text 模型输出字符串。
    @return 等长字符串，字面量区域用空格替代。
    """
    # 保护明确的字面量；未闭合代码块视为至输出末尾，避免从示例执行动作。
    ranges = [m.span() for m in re.finditer(r'```[\s\S]*?(?:```|\Z)|`[^`\n]*`|(?m:^\s*>[^\n]*)', text)]
    # 单引号必须在词边界外开闭；don't/That's等缩写不能跨答案标签被当成引用。
    # 明确引号内仍允许缩写和反斜线转义，保留含标签字面量的保护。
    quoted = r'"(?:\\.|[^"\\\n])*"|“[^”\n]*”|(?<!\w)\'(?:\\.|[^\'\\\n]|(?<=\w)\'(?=\w))*\'(?!\w)'
    for match in re.finditer(quoted, text):
        if re.search(r'</?(?:search|answer|information)>', match.group()):
            ranges.append(match.span())
    chars = list(text)
    for start, end in ranges:
        chars[start:end] = ' ' * (end - start)
    return ''.join(chars)


def parse_action(text):
    """
    @brief 解析最先可执行的动作并明确消费边界，未消费尾部只记录。
    @param text 一轮原始模型输出字符串。
    @return 含动作、内容、有效性、消费文本、尾部和违规位置的字典。
    @raises ValueError 输入类型错误。
    """
    # 原始输出类型不符属于调用错误，不能把其他对象强转为合法动作。
    if not isinstance(text, str):
        raise ValueError('Action output must be a string')
    clean = protected_text(text)
    # 只定位首个非字面量动作；闭合边界决定本轮真实可执行内容。
    start = re.search(r'<(search|answer)>', clean)
    action, content, end, reasons = None, '', len(text), []
    if start:
        close = re.search(r'</' + start.group(1) + '>', clean[start.end():])
        if close:
            close_start = start.end() + close.start()
            end = start.end() + close.end()
            action, content = start.group(1), text[start.end():close_start].strip()
            # 嵌套控制标签不能作为正常查询或答案执行；字面量标签已被保护。
            if re.search(r'</?(?:search|answer|information|think)>', clean[start.end():close_start]):
                reasons.append(dict(code='nested_action', span=[start.start(), end]))
            # 空白查询或答案不作为合法动作，不能触发检索或回答结束。
            if not content:
                reasons.append(dict(code='empty_action', span=[start.start(), end]))
        else:
            # 找不到配对结束标签时只记录未闭合错误，不执行残缺动作。
            reasons.append(dict(code='unclosed_action', span=[start.start(), len(text)]))
    else:
        reasons.append(dict(code='missing_action', span=[0, len(text)]))
    # 仅未受保护且实际消费的环境角色标签判为冒充，尾部不能改变已执行动作奖励。
    for match in re.finditer(r'</?information>', clean[:end]):
        reasons.append(dict(code='forged_observation', span=list(match.span())))
    # 来源违规由奖励门控处理；仍接受合法答案，以区分伪造观察与缺少答案。
    valid = action is not None and not any(r['code'] in {'nested_action', 'empty_action'} for r in reasons)
    return dict(action=action, content=content, valid=valid, consumed=text[:end], tail=text[end:],
                reasons=reasons, action_span=[start.start(), end] if start else None)


class TraceLedger:
    """单次生成调用的独立轨迹账本；事件随DataProto行传递。"""

    def __init__(self, count):
        """
        @brief 为每条真实轨迹创建唯一标识，避免组UID与轨迹UID混淆。
        @param count 非负真实轨迹数，不含GPU补齐副本。
        @return 无。
        @raises ValueError 轨迹数非法。
        """
        # 拒绝非法轨迹数；每个真实行分配程序身份，副本不创建额外工具账本。
        if count < 0:
            raise ValueError('Invalid trajectory count')
        prefix = uuid.uuid4().hex
        self.rows = [dict(trace_uid=f'{prefix}:{i}', events=[], calls=[], answered=False,
                          answer=None, infrastructure_error=None) for i in range(count)]

    def execute(self, predictions, active, final, search_fn, turn, raw_predictions=None):
        """
        @brief 执行共用解析器认可的动作，工具结果只由真实检索回调注入。
        @param predictions 全批次本轮消费输出，非活动行可为空。
        @param active 全批次活动布尔列表。
        @param final 全批次仅允许答案的布尔列表。
        @param search_fn 接受查询列表、返回等长字符串列表的真实工具接口。
        @param turn 当前非负全局生成轮次。
        @param raw_predictions 可选活动行原始输出，用于记录未消费尾部。
        @return 与执行器兼容的观察、结束、合法动作和真实搜索列表。
        @raises ValueError 行对应、解析、调用或返回数据错误；基础设施故障终止该批次。
        """
        n = len(self.rows)
        # 整批行数和轮次必须对齐，禁止部分错配后继续检索。
        if len(predictions) != n or len(active) != n or len(final) != n or turn < 0:
            raise ValueError('Process ledger row/turn mismatch')
        raw = iter(raw_predictions if raw_predictions is not None else
                   [text for text, flag in zip(predictions, active) if flag])
        outputs, done, valid, searched = [''] * n, [1] * n, [0] * n, [0] * n
        requests = []
        for i, flag in enumerate(active):
            if not flag:
                continue
            row = self.rows[i]
            try:
                parsed = parse_action(next(raw))
            except StopIteration as exc:
                raise ValueError('Missing raw output row') from exc
            # 原始、消费、尾部和本轮身份分别保存，来源证据不接受模型自行声明。
            event = dict(turn=turn, trace_uid=row['trace_uid'], raw=parsed['consumed'] + parsed['tail'],
                         consumed=predictions[i], tail=parsed['tail'], parsed=parsed,
                         reasons=deepcopy(parsed['reasons']), executed=None, call_id=None,
                         accepted=False, final=bool(final[i]))
            row['events'].append(event)
            # 原始后处理与执行必须消费同一动作，任何偏差停止，不能静默错配评分。
            if parsed['consumed'] != predictions[i]:
                event['reasons'].append(dict(code='action_parse_mismatch', span=[0, len(predictions[i])]))
                raise ValueError('Action parse mismatch')
            # 已接受答案终止轨迹；后续输入只记录违规，不再产生工具调用。
            if row['answered']:
                event['reasons'].append(dict(code='action_after_answer', span=parsed['action_span']))
                continue
            # 闭合非空答案才标记接受，缺失/嵌套动作不冒充作答成功。
            if parsed['valid'] and parsed['action'] == 'answer':
                row['answered'], row['answer'] = True, parsed['content']
                event['executed'], event['accepted'], valid[i] = 'answer', True, 1
            elif parsed['valid'] and parsed['action'] == 'search' and not final[i]:
                # 调用身份由程序分配，不接受模型提供的call_id或工具角色。
                call_id = f"{row['trace_uid']}:{turn}:{len(row['calls'])}"
                call = dict(call_id=call_id, trace_uid=row['trace_uid'], turn=turn,
                            query=parsed['content'], status='pending')
                row['calls'].append(call)
                event['executed'], event['accepted'], event['call_id'] = 'search', True, call_id
                requests.append((i, call))
                done[i], valid[i], searched[i] = 0, 1, 1
            else:
                # 到期后不检索；其他无效动作允许反馈后重试，违规不会被后续答案抹除。
                if parsed['valid'] and parsed['action'] == 'search' and final[i]:
                    event['reasons'].append(dict(code='search_forbidden', span=parsed['action_span']))
                done[i] = int(final[i])
                outputs[i] = '' if final[i] else '\nInvalid action. Submit a nonempty <search>query</search> or <answer>answer</answer>.\n'
        # 多余原始行也属于错配；不能误将另一轨迹的输出或观察绑定到本行。
        if next(raw, None) is not None:
            raise ValueError('Extra raw output row')
        if requests:
            try:
                results = search_fn([call['query'] for _, call in requests])
                # 工具回调必须按请求顺序返回等长文本；空字符串是正常的空检索。
                if len(results) != len(requests) or any(not isinstance(r, str) for r in results):
                    raise ValueError('Retriever call/result mismatch')
            except Exception as exc:
                # 保留调用身份和错误，不以空检索结果替代；训练器不评分部分失败批次。
                for i, call in requests:
                    call['status'] = 'error'
                    self.rows[i]['infrastructure_error'] = f'{type(exc).__name__}: {exc}'
                raise
            # 原返回文本、哈希和程序包装一起保存，模型自写information不会进入真实调用表。
            for (i, call), result in zip(requests, results):
                call.update(status='ok', raw_text=result, raw_sha256=digest(result))
                outputs[i] = f'\n\n<information>{result.strip()}</information>\n\n'
        return outputs, done, valid, searched

    def observe_visible(self, observations, turn):
        """
        @brief 记录实际裁剪并分词后可见的工具结果，诊断只使用模型已见内容。
        @param observations 全批次可见观察字符串列表。
        @param turn 对应生成轮次。
        @return 无。
        @raises ValueError 观察行数错配。
        """
        # 可见观察必须逐行对齐；只更新当前轮成功调用，拒绝跨轨迹借用证据。
        if len(observations) != len(self.rows):
            raise ValueError('Visible observation row mismatch')
        for row, text in zip(self.rows, observations):
            calls = [c for c in row['calls'] if c['turn'] == turn and c['status'] == 'ok']
            for call in calls:
                call.update(visible_text=text, visible_sha256=digest(text),
                            documents=documents(text, call['call_id']))

    def reports(self):
        """
        @brief 导出可按行传递的账本和诊断，重新验证来源与解析一致性。
        @return 每轨迹报告列表；未知语义不影响协议合法性。
        """
        reports = deepcopy(self.rows)
        for row in reports:
            # 搜索诊断按成功调用顺序比较实际可见文档，失败调用不提供证据。
            previous = []
            for call in row['calls']:
                if call['status'] == 'ok':
                    call['search_diagnostic'] = search_diagnostic(call['query'], call.get('documents', []), previous)
                    previous.append(call)
            for event in row['events']:
                # 本轮工具结果发生在生成之后，不能用于为本轮推理提供事后依据。
                evidence = [d for c in row['calls'] if c['turn'] < event['turn']
                            for d in c.get('documents', [])]
                span = event['parsed']['action_span']
                prefix = event['consumed'][:span[0]] if span else event['consumed']
                event['reasoning'] = review_reasoning(prefix, evidence)
            # 导出时重验客观事件，缺答案单独记录，协议合法性不取代语义支持判定。
            row.update(version='process_checks_v1', missing_answer=not row['answered'])
            errors = validate_report(row, row['trace_uid'])
            row['reasons'] = [dict(reason, turn=e['turn']) for e in row['events'] for reason in e['reasons']]
            row['reasons'].extend(dict(code=c, turn=None) for c in errors)
            row['protocol_valid'] = not row['infrastructure_error'] and not any(
                r['code'] in HARD_CODES for r in row['reasons'])
        return reports


def validate_report(report, expected_uid):
    """
    @brief 校验报告与所在DataProto行身份、原始调用结果和接受动作的一致性。
    @param report 程序导出的单轨迹字典。
    @param expected_uid 同行独立保存的轨迹ID。
    @return 来源或动作错配原因码列表。
    @raises ValueError 缺失或无法识别的报告。
    """
    # 版本和同行身份是评分前置条件，无法识别的记录不得回退旧奖励。
    if not isinstance(report, dict) or report.get('version') != 'process_checks_v1':
        raise ValueError('Missing/version-mismatched process report')
    errors = []
    if report.get('trace_uid') != expected_uid:
        errors.append('call_result_mismatch')
    # 调用身份必须唯一；重复call_id不能覆盖掉同一轨迹的其他返回。
    calls = {c['call_id']: c for c in report.get('calls', [])}
    if len(calls) != len(report.get('calls', [])):
        errors.append('call_result_mismatch')
    answers = []
    referenced = []
    turns = []
    for event in report.get('events', []):
        # 答案是轨迹终点；独立重算顺序，不能只信任事件内的违规标签。
        if answers:
            errors.append('action_after_answer')
        parsed = parse_action(event['raw'])
        turns.append(event['turn'])
        # 从原始文字重算动作和消费边界，不能只信任缓存的解析结果。
        if event['trace_uid'] != expected_uid or parsed != event['parsed'] or parsed['consumed'] != event['consumed']:
            errors.append('action_parse_mismatch')
        if event['accepted'] and (not parsed['valid'] or event['executed'] != parsed['action']):
            errors.append('action_parse_mismatch')
        if event['accepted'] and event['executed'] == 'answer':
            answers.append(parsed['content'])
        # 接受的搜索必须绑定同轮同查询的真实调用，末轮搜索不允许被伪造为已执行。
        if event['accepted'] and event['executed'] == 'search':
            referenced.append(event['call_id'])
            call = calls.get(event['call_id'])
            if (event['final'] or call is None or call['trace_uid'] != expected_uid
                    or call['query'] != parsed['content'] or call['turn'] != event['turn']):
                errors.append('call_result_mismatch')
    # 工具调用必须与接受的search动作一一对应，答案结束后不允许新增事件。
    if set(referenced) != set(calls) or len(referenced) != len(set(referenced)):
        errors.append('call_result_mismatch')
    if turns != sorted(set(turns)) or len(answers) > 1:
        errors.append('action_parse_mismatch')
    # 全局答案状态必须与实际接受事件一致，杜绝仅改answered或answer绕过门控。
    if bool(answers) != bool(report.get('answered')) or (answers[-1] if answers else None) != report.get('answer'):
        errors.append('action_parse_mismatch')
    # 成功调用核对原返回及可见正文完整性；错误状态只在已标基础设施故障时保留。
    for call in calls.values():
        if call['status'] == 'ok':
            if digest(call['raw_text']) != call['raw_sha256'] or 'visible_text' not in call:
                errors.append('call_result_mismatch')
            elif (digest(call['visible_text']) != call['visible_sha256'] or
                  documents(call['visible_text'], call['call_id']) != call['documents']):
                errors.append('call_result_mismatch')
        elif not report.get('infrastructure_error'):
            errors.append('call_result_mismatch')
    return sorted(set(errors))
