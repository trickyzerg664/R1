"""协议门控和无答案惩罚与原EM分开保存；不奖励推理文风。"""
import json
import math
from pathlib import Path
from .protocol import HARD_CODES, parse_action, validate_report


def check_config(config):
    """
    @brief 校验显式开关，拒绝未记录过程却修改奖励的配置。
    @param config 包含enabled、reward_gate、missing_answer_penalty、audit_path的映射。
    @return 普通字典，数值与布尔字段已校验。
    @raises ValueError 非有限/负惩罚或不一致开关。
    """
    result = dict(config or {})
    result.setdefault('enabled', False)
    result.setdefault('reward_gate', False)
    result.setdefault('missing_answer_penalty', 0.)
    result.setdefault('audit_path', None)
    # 拒绝字符串False等隐式真值，避免误开启实际奖励修改。
    if any(type(result[key]) is not bool for key in ('enabled', 'reward_gate')):
        raise ValueError('Process switches must be booleans')
    # 惩罚必须非负有限；修改奖励要求先启用完整来源检查及门控。
    penalty = float(result['missing_answer_penalty'])
    if not math.isfinite(penalty) or penalty < 0:
        raise ValueError('Missing-answer penalty must be finite and nonnegative')
    if (result['reward_gate'] or penalty) and not result['enabled']:
        raise ValueError('Process reward requires enabled process checks')
    if penalty and not result['reward_gate']:
        raise ValueError('Missing-answer penalty requires protocol gate')
    result['missing_answer_penalty'] = penalty
    return result


def process_score(report, expected_uid, accepted_answer_em, penalty):
    """
    @brief 从真实接受答案EM计算候选奖励，防止报告或解析被篡改后放行。
    @param report 程序过程报告。
    @param expected_uid 同行轨迹ID。
    @param accepted_answer_em 按原EM归一化判定的0/1分数。
    @param penalty 非负无答案惩罚系数。
    @return 实数奖励；故障不会转成模型负奖励。
    @raises ValueError 报告错配、基础设施故障或非法奖励输入。
    """
    # 故障和错配批次停止评分，不将基础设施失败转为模型负奖励。
    errors = validate_report(report, expected_uid)
    if errors or report.get('infrastructure_error'):
        raise ValueError('Cannot score untrusted/failed process report: ' + str(errors))
    # 接受答案的EM只允许0/1；惩罚必须非负有限，不能静默传播NaN。
    if accepted_answer_em not in (0., 1.) or not math.isfinite(penalty) or penalty < 0:
        raise ValueError('Invalid process reward inputs')
    # 未接受答案时EM必须为0，阻止调用方误把原尾部答案分数传入。
    if not report['answered'] and accepted_answer_em:
        raise ValueError('An unaccepted answer cannot have nonzero EM')
    # 从原始事件重新提取违规，不信任可被修改的protocol_valid布尔字段。
    codes = {r['code'] for event in report['events'] for r in parse_action(event['raw'])['reasons']}
    codes.update(r['code'] for event in report['events'] for r in event['reasons'])
    gate = not bool(codes & HARD_CODES)
    # R=EM乘协议合法门控减beta乘无答案标记；合法直接作答不要求额外搜索。
    return float(accepted_answer_em) * gate - penalty * (not report['answered'])


def append_reports(path, reports, phase):
    """
    @brief 在指定审计文件追加逐轨迹报告；调用方失败不能静默丢失证据。
    @param path 可选JSONL路径，为空时只保留DataProto行记录。
    @param reports 报告列表。
    @param phase 记录阶段，例如generation、train或validation。
    @return 无。
    @raises OSError 文件写入失败。
    """
    if not path:
        return
    # 一次追加完整批次，UTF8保留原文及原因位置；不创建额外Markdown文档。
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = ''.join(json.dumps(dict(phase=phase, report=r), ensure_ascii=False) + '\n' for r in reports)
    with target.open('a', encoding='utf-8') as stream:
        stream.write(payload)
