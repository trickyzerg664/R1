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
    @param limit 非负字符预算。
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
    return text if len(text)<=limit else text[:max(0,limit-len(marker))]+marker[:limit]


def render_trajectory(record, max_chars=12000):
    """@brief 将已算出的分数及真实轨迹渲染为中文分块日志，不重新评分。
    @param record 含问题、模型输出、分数和可选来源报告的只读字典。
    @param max_chars 单条字符总预算，至少2000，优先保留奖励总结。
    @return 带真实换行和起止边界的日志字符串。
    @raises ValueError 字符预算小于2000。
    """
    if max_chars<2000:
        raise ValueError('max_chars must be at least 2000')
    # 只读取已有阶段和同行身份；候选标记不表示已进入优化器更新。
    report,meta=record.get('process_report'),record.get('meta',{})
    identity=report.get('trace_uid') if report else record.get('uid')
    header=(f"\n{'='*72}\n[轨迹开始] 阶段={display_text(record.get('phase'),60)} "
            f"step={display_text(meta.get('trajectory_step',meta.get('evaluation_step')),40)} "
            f"评分批次={record.get('batch_number')} 行={record.get('row')}\n"
            f"来源={display_text(record.get('data_source'),60)} 题号={display_text(record.get('question_id'),100)} "
            f"轨迹={display_text(identity,100)}\n")
    if 'trajectory_candidate_round' in meta:
        header+=f"候选轮次={meta['trajectory_candidate_round']+1}（尚未完成动态筛选）\n"
    body=['\n[问题 / 初始提示]\n'+display_text(record.get('prompt'),2500)]
    # 有账本时按真实轮次呈现模型消费输出和已执行搜索；不补造思考或工具结果。
    if report:
        calls={c['call_id']:c for c in report.get('calls',[])}
        for event in report.get('events',[]):
            body.append(f"\n[第 {event['turn']+1} 轮：模型思考 / 动作原文]\n"+display_text(event.get('consumed'),4000))
            body.append(f"实际执行={event.get('executed') or '无'}；接受={event.get('accepted')}")
            # 原因位置继续对应未改写原文，显示副本的字符位置不能反向用于执行。
            for reason in event.get('reasons',[]):
                code=reason['code'];body.append(f"检查提示：{REASONS.get(code,code)} ({code})；字符位置={reason.get('span')}")
            call=calls.get(event.get('call_id'))
            if call:
                body.append(f"\n[真实工具调用] call_id={call['call_id']}；状态={call.get('status')}\n"
                            f"查询：{display_text(call.get('query'),500)}\n[模型实际可见的检索结果]\n"+
                            display_text(call.get('visible_text'),3000))
            # 未执行尾部单列，避免被误读为接受的答案或实际发生的第二次调用。
            if event.get('tail'):
                body.append('\n[未执行尾部：仅审计，不作为第二个动作评分]\n'+display_text(event['tail'],800))
            # 引文诊断沿用原报告，不用文字重合宣称语义成立，也不新增奖惩。
            reasoning=event.get('reasoning',{})
            for check in reasoning.get('quote_checks',[])+reasoning.get('citation_checks',[]):
                body.append('引文 / 文档引用诊断：'+display_text(check,500))
        body.append('\n[推理语义] 事实支持、多跳关系及冲突待复核；文字匹配不等于推理成立，不计入奖励。')
    else:
        # 无来源账本时展示完整生成历史，明确不确认逐轮来源或实际接受动作。
        body.append('\n[模型思考 / 回答原文：已排除环境token]\n'+display_text(record.get('model_response'),5000))
        body.append('\n[生成历史：包含环境反馈，未记录逐轮调用身份]\n'+display_text(record.get('full_response'),4000))
    # 只复用原答案提取器解释分数，不能再次调用随机评分逻辑。
    extracted=extract_solution(record['scoring_text'],record['answer_mode'])
    # 原答案分与接受答案EM分别列出，历史答案模式可包含格式分，不能混称过程奖励。
    summary=['\n[答案与奖励判定]','标准答案：'+display_text(record.get('target'),350),
             '评分提取答案：'+display_text(extracted,350),
             f"答案提取模式：{record['answer_mode']}；原始答案分（EM规则）={record['original_em']:g}"]
    if report:
        # 门控与缺答案仅解释真实评分记录，公式是展示，不能覆盖返回分。
        gate,missing=int(bool(report['protocol_valid'])),int(bool(report['missing_answer']))
        codes=sorted({r['code'] for r in report.get('reasons',[])})
        summary+=['实际接受答案：'+display_text(report.get('answer'),350),
                  f"来源 / 动作门控：{'通过' if gate else '失败'}；无答案={missing}",
                  '原因码：'+(', '.join(codes) if codes else '无'),
                  f"接受答案EM={report['accepted_answer_em']:g}；未作答惩罚系数={record['penalty']:g}",
                  f"候选过程奖励={report['protocol_reward']:g} = {report['accepted_answer_em']:g} × {gate} - {record['penalty']:g} × {missing}",
                  '返回策略：'+('采用过程奖励' if record['apply_process_reward'] and record['reward_gate'] else '保留原始答案分（验证或仅审计）')]
    else:
        summary.append(f"过程检查关闭；没有来源合法性判定；错误答案格式分={record['format_score']:g}")
    # 规则奖励与后续KL、优势及损失明确区分；实际返回分优先保留。
    summary+=[f"本次实际返回规则奖励={record['returned_reward']:g}",
              '这里展示评分入口奖励；KL、GRPO优势及最终损失在后续流程计算。']
    # 极长标准答案或答案内容也受预算限制，实际奖励及结束边界始终保留。
    fixed_ending='\n'.join(summary[-2:])+f"\n[轨迹结束]\n{'='*72}\n"
    decision=display_text('\n'.join(summary[:-2]),max(0,min(2200,max_chars-len(header)-len(fixed_ending)-250)))
    ending=decision+'\n'+fixed_ending
    # 总预算先保留奖励结论，长文本仅截显示副本，不改变模型或环境token。
    # 块之间明确保留空行，避免strip把奖励标题拼到上一段末尾。
    return header+display_text('\n'.join(body),max(0,max_chars-len(header)-len(ending)-2))+'\n\n'+ending


class HumanTrajectoryLogger:
    """确定性展示限额；独立于采样、奖励及checkpoint。"""
    def __init__(self, config=None):
        """@brief 校验展示配置；未传配置时关闭，兼容既有直接调用。
        @param config 含开关、频率、样例数、字符预算和可选文件路径的映射。
        @return 无。
        @raises ValueError 开关、整数预算或文件路径非法。
        """
        v=dict(config or {});self.enabled=v.get('enabled',False)
        self.console_samples=v.get('console_samples_per_source',1)
        self.file_samples=v.get('file_samples_per_source',0)
        self.every=v.get('every_n_batches',1);self.max_chars=v.get('max_chars_per_trajectory',12000)
        self.file_path=v.get('file_path')
        # 控制台0表示关闭；文件0表示选中批次全量记录；非法配置启动时显式报错。
        if type(self.enabled) is not bool or any(type(x) is not int for x in (self.console_samples,self.file_samples,self.every,self.max_chars)):
            raise ValueError('Invalid trajectory logging switches/budgets')
        if min(self.console_samples,self.file_samples)<0 or self.every<1 or self.max_chars<2000:
            raise ValueError('Invalid trajectory logging limits')
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
        try:text=render_trajectory(record,self.max_chars)
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
