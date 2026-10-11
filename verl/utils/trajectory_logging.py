"""只读中文轨迹日志；不评分、不消费随机数、不修改训练数据。"""
from pathlib import Path
import re
import sys
from verl.utils.reward_score.qa_em import extract_solution

REASONS = {'forged_observation':'模型冒充工具观察', 'nested_action':'动作嵌套',
           'empty_action':'空动作', 'search_forbidden':'本轮禁止搜索',
           'action_after_answer':'答案后新增动作', 'action_parse_mismatch':'解析错配',
           'call_result_mismatch':'调用返回错配', 'unclosed_action':'未闭合动作', 'missing_action':'缺少动作'}


def display_text(value, limit):
    """@brief 整理展示副本的换行、控制字符和长度，保持原文不变。
    @param value 文本或标量；None显示未记录。
    @param limit 非负字符预算，None表示完整展示。
    @return 安全多行文本，字面量反斜线n不会被转换成换行。
    """
    # 统一真实换行并滤除终端控制字符，避免模型文本影响后续日志。
    text = ('未记录' if value is None else str(value)).replace('\r\n','\n').replace('\r','\n')
    text = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', text)
    text = ''.join(c for c in text if c in '\n\t' or ord(c)>=32)
    # 控制标签独占显示行，仅改副本排版，真实动作边界仍由原解析器确定。
    text = re.sub(r'[ \t]*\n*[ \t]*(</?(?:think|search|answer|information)>)[ \t]*\n*[ \t]*',
                  r'\n\1\n', text).strip()
    # 截断只影响展示；完整原文仍由已有轨迹审计保存。
    marker = '\n[展示截断；启用原始轨迹审计可保存完整内容]'
    return text if limit is None or len(text)<=limit else text[:max(0,limit-len(marker))]+marker[:limit]


def render_search_result(value, max_chars=1000):
    """@brief 缩略真实工具观察，保留首尾内容及省略数量，不修改模型可见原文。
    @param value 账本记录的真实可见观察文本或None。
    @param max_chars 正文字符预算；0表示完整展示，正数至少200。
    @return 带完整information边界的展示副本或未记录提示。
    @raises ValueError 预算非法。
    """
    if type(max_chars) is not int or max_chars < 0 or 0 < max_chars < 200:
        raise ValueError('search_result_max_chars must be 0 or at least 200')
    text = display_text(value, None)
    # 仅真实工具字段允许省略；模型自己生成的information标签仍全文保留。
    wrapped = text.startswith('<information>') and text.endswith('</information>')
    content = text[len('<information>'):-len('</information>')].strip() if wrapped else text
    if max_chars and len(content) > max_chars:
        # 首尾各保留信息，标注原长及省略量；预算不含标签和省略说明。
        head = max_chars * 3 // 4
        tail = max_chars - head
        omitted = len(content) - max_chars
        content = (content[:head] + f'\n[搜索结果省略 {omitted} 字符；原正文 {len(content)} 字符]\n'
                   + content[-tail:])
    return '<information>\n' + content + '\n</information>' if wrapped else content


def render_trajectory(record, max_chars=12000, search_result_max_chars=1000):
    """@brief 连续展示一条真实消费轨迹，随后列出奖励和过程诊断。
    @param record 含问题、模型输出、分数和可选来源报告的只读字典。
    @param max_chars 兼容旧配置的辅助诊断预算，至少2000；不再限制模型输出。
    @param search_result_max_chars 每次真实搜索正文预算，0为全文，正数至少200。
    @return 带真实换行和起止边界的完整轨迹日志字符串。
    @raises ValueError 辅助预算或搜索预算非法。
    @note 只缩略真实工具观察；模型消费输出无总长度截断，不补造缺失答案。
    """
    if type(max_chars) is not int or max_chars < 2000:
        raise ValueError('max_chars must be at least 2000')
    # 即使本条没有搜索，也在入口拒绝无效预算。
    if type(search_result_max_chars) is not int or search_result_max_chars < 0 or 0 < search_result_max_chars < 200:
        raise ValueError('search_result_max_chars must be 0 or at least 200')
    report, meta = record.get('process_report'), record.get('meta', {})
    identity = report.get('trace_uid') if report else record.get('uid')
    header = (f"\n{'='*72}\n[轨迹开始] 阶段={display_text(record.get('phase'),60)} "
              f"step={display_text(meta.get('trajectory_step',meta.get('evaluation_step')),40)} "
              f"评分批次={record.get('batch_number')} 行={record.get('row')}\n"
              f"来源={display_text(record.get('data_source'),60)} 题号={display_text(record.get('question_id'),100)} "
              f"轨迹={display_text(identity,100)}\n")
    if 'trajectory_candidate_round' in meta:
        header += f"候选轮次={meta['trajectory_candidate_round']+1}（尚未完成动态筛选）\n"
    body = ['\n[问题 / 初始提示]\n' + display_text(record.get('prompt'), 2500),
            '\n[连续轨迹：思考 → 搜索 → 搜索结果 → 回答]']
    diagnostics = []
    # 账本消费文本是实际执行历史；原始未消费尾部移到末尾，不混入连续轨迹。
    if report and report.get('events'):
        calls = {c['call_id']: c for c in report.get('calls', [])}
        for event in report['events']:
            turn = event['turn'] + 1
            body.append(f"\n[第 {turn} 轮]\n" + display_text(event.get('consumed'), None))
            call = calls.get(event.get('call_id'))
            if call:
                # 展示绑定本轮call_id的可见文本；raw_text含不可见内容，禁止替代。
                body.append(f"\n[真实工具调用] 搜索结果；状态={call.get('status')}\n"
                            + render_search_result(call.get('visible_text'), search_result_max_chars))
            diagnostics.append(f"第 {turn} 轮：实际执行={event.get('executed') or '无'}；接受={event.get('accepted')}")
            if call:
                # 长调用身份留在诊断区，主轨迹保留简短来源标识。
                diagnostics.append(f"真实工具调用身份：{call['call_id']}")
            for reason in event.get('reasons', []):
                code = reason['code']
                diagnostics.append(f"检查提示：{REASONS.get(code,code)} ({code})；字符位置={reason.get('span')}")
            if event.get('tail'):
                diagnostics.append('[未执行尾部：仅审计，不作为第二个动作评分]\n'
                                   + display_text(event['tail'], 800))
            reasoning = event.get('reasoning', {})
            for check in reasoning.get('quote_checks', []) + reasoning.get('citation_checks', []):
                diagnostics.append('引文 / 文档引用诊断：' + display_text(check, 500))
        if not report.get('answered'):
            body.append('\n[本轨迹未接受最终回答；按实际结束状态展示]')
    else:
        # 无逐轮账本时只展示一份历史，来源无法确认，不能误删模型伪观察文本。
        history = record.get('full_response')
        if history is None or history == '':
            history = record.get('model_response')
        body.append('\n[生成历史：逐轮来源未记录，保留全文]\n' + display_text(history, None))
    body.append('\n[连续轨迹结束]')

    # 仅复用原答案提取器解释既有奖励，分值和奖励返回策略保持原有口径。
    extracted = extract_solution(record['scoring_text'], record['answer_mode'])
    summary = ['\n[答案与奖励判定]', '标准答案：' + display_text(record.get('target'),350),
               '评分提取答案：' + display_text(extracted,350),
               f"答案提取模式：{record['answer_mode']}；原始答案分（EM规则）={record['original_em']:g}"]
    if report:
        gate, missing = int(bool(report['protocol_valid'])), int(bool(report['missing_answer']))
        codes = sorted({r['code'] for r in report.get('reasons', [])})
        summary += ['实际接受答案：' + display_text(report.get('answer'),350),
                    f"来源 / 动作门控：{'通过' if gate else '失败'}；无答案={missing}",
                    '原因码：' + (', '.join(codes) if codes else '无'),
                    f"接受答案EM={report['accepted_answer_em']:g}；未作答惩罚系数={record['penalty']:g}",
                    f"候选过程奖励={report['protocol_reward']:g} = {report['accepted_answer_em']:g} × {gate} - {record['penalty']:g} × {missing}",
                    '返回策略：' + ('采用过程奖励' if record['apply_process_reward'] and record['reward_gate'] else '保留原始答案分（验证或仅审计）')]
    else:
        summary.append(f"过程检查关闭；没有来源合法性判定；错误答案格式分={record['format_score']:g}")
    # 原过程奖励仍展示原公式；启用软罚时另列训练候选，避免误读新旧分值。
    if report and 'training_reward' in report:
        summary += [f"奖励版本：{report['reward_version']}；完整无效动作数={report['invalid_action_count']}",
                    f"训练候选奖励={report['training_reward']:g}；总过程成本={report['process_penalty']:g}",
                    f"原生终止未知={report['unknown_termination_count']}；长度截断免新增罚={report['length_termination_count']}"]
    summary += [f"本次实际返回规则奖励={record['returned_reward']:g}",
                '这里展示评分入口奖励；KL、GRPO优势及最终损失在后续流程计算。']
    # 诊断独立放在答案之后，辅助截断不会吞掉任何一轮模型思考或最终回答。
    ending = '\n'.join(summary)
    if diagnostics:
        ending += '\n\n[过程诊断：不属于模型输出]\n' + display_text('\n'.join(diagnostics), max_chars)
    return header + '\n'.join(body) + '\n\n' + ending + f"\n[轨迹结束]\n{'='*72}\n"


class HumanTrajectoryLogger:
    """确定性展示限额；独立于采样、奖励及checkpoint。"""
    def __init__(self, config=None):
        """@brief 校验展示配置；未传配置时关闭，兼容既有直接调用。
        @param config 含开关、频率、样例数、辅助诊断预算、搜索正文预算和可选文件路径的映射。
        @return 无。
        @raises ValueError 开关、整数预算或文件路径非法。
        """
        v=dict(config or {});self.enabled=v.get('enabled',False)
        self.console_samples=v.get('console_samples_per_source',1)
        self.file_samples=v.get('file_samples_per_source',0)
        self.every=v.get('every_n_batches',1);self.max_chars=v.get('max_chars_per_trajectory',12000)
        self.search_chars=v.get('search_result_max_chars',1000)
        self.file_path=v.get('file_path')
        # 控制台0表示关闭；文件0表示选中批次全量记录；非法配置启动时显式报错。
        if type(self.enabled) is not bool or any(type(x) is not int for x in (self.console_samples,self.file_samples,self.every,self.max_chars,self.search_chars)):
            raise ValueError('Invalid trajectory logging switches/budgets')
        if min(self.console_samples,self.file_samples)<0 or self.every<1 or self.max_chars<2000:
            raise ValueError('Invalid trajectory logging limits')
        # 0允许搜索全文；过小预算无法保留可读的首尾证据。
        if self.search_chars < 0 or 0 < self.search_chars < 200:
            raise ValueError('Invalid search result display limit')
        if self.file_path is not None and (not isinstance(self.file_path,str) or not self.file_path.strip()):
            raise ValueError('Trajectory file_path must be a nonempty string or null')
        self.batch_number,self.counts,self.warned=0,{},False

    def begin_batch(self):
        """@brief 重置每来源展示计数，频率按奖励调用批次计算，不使用随机数。
        @return 无。
        """
        # 此计数只控制展示；不会保存到训练状态或改变任何抽题随机流。
        self.batch_number+=1;self.counts={}

    def selected(self, source):
        """@brief 判断本行是否需要展示，避免未选中行额外解码。
        @param source 当前来源字符串。
        @return 是否需要控制台或文件输出的布尔值。
        """
        # 固定顺序选每来源前几行，不改输入轨迹顺序或随机状态。
        if not self.enabled or (self.batch_number-1)%self.every:return False
        count=self.counts.get(str(source),0)
        return count<self.console_samples or bool(self.file_path and (self.file_samples==0 or count<self.file_samples))

    def warn(self, error):
        """@brief 日志失败只提醒一次；提醒失败也不能中断训练。
        @param error 展示构造或输出捕获的异常对象。
        @return 无。
        """
        # 仅隔离可选展示故障；原来源检查、评分和审计异常继续按原规则传播。
        if not self.warned:
            self.warned=True
            try:print('[轨迹日志警告] 可读日志输出失败，训练继续：'+type(error).__name__,file=sys.stderr,flush=True)
            except Exception:pass

    def emit(self, source, record):
        """@brief 一次输出完整轨迹块，分别隔离格式化及输出异常。
        @param source 当前来源字符串，用于独立样例限额。
        @param record 只读展示字典。
        @return 无。
        """
        if not self.selected(source):return
        # 先消费展示名额，失败也不会在同一批次无限尝试打印其他行。
        count=self.counts.get(str(source),0);self.counts[str(source)]=count+1
        # 格式化失败只丢失本条可读日志，不能影响奖励返回。
        try:text=render_trajectory(record,self.max_chars,self.search_chars)
        except Exception as exc:
            self.warn(exc);return
        # 控制台与文件故障分别处理，一个失败仍尝试另一个目的地。
        if count<self.console_samples:
            try:print(text,end='',flush=True)
            except Exception as exc:self.warn(exc)
        if self.file_path and (self.file_samples==0 or count<self.file_samples):
            try:
                # UTF8追加可读副本；未配置路径时不会创建文件或目录。
                path=Path(self.file_path);path.parent.mkdir(parents=True,exist_ok=True)
                with path.open('a',encoding='utf-8') as stream:stream.write(text)
            except Exception as exc:self.warn(exc)
