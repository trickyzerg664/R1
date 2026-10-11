"""协议门控和无答案惩罚与原EM分开保存；不奖励推理文风。"""
import json
import math
from pathlib import Path
from .protocol import HARD_CODES, parse_action, validate_report

TASK_SUCCESS_VERSION = 'task_success_v1'


def check_config(config):
    """
    @brief 校验显式开关，拒绝未记录过程却修改奖励的配置。
    @param config 含过程开关、缺答案惩罚、奖励版本、无效动作系数、成本上限及审计路径的映射。
    @return 普通字典，数值与布尔字段已校验。
    @raises ValueError 非有限/负惩罚或不一致开关。
    """
    result = dict(config or {})
    result.setdefault('enabled', False)
    result.setdefault('reward_gate', False)
    result.setdefault('missing_answer_penalty', 0.)
    result.setdefault('audit_path', None)
    result.setdefault('reward_variant', 'legacy')
    result.setdefault('invalid_action_penalty', 0.)
    result.setdefault('process_penalty_cap', .12)
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
    # 新奖励显式版本与上限受限，未知终止保护不能由配置绕过。
    if result['reward_variant'] not in ('legacy', 'bounded_invalid_v1'):
        raise ValueError('Unknown process reward variant')
    invalid, cap = float(result['invalid_action_penalty']), float(result['process_penalty_cap'])
    if not math.isfinite(invalid) or invalid < 0 or not math.isfinite(cap) or not 0 < cap <= .12:
        raise ValueError('Invalid bounded process costs')
    if result['reward_variant'] != 'legacy' and (not result['reward_gate'] or penalty > cap or invalid <= 0):
        raise ValueError('Bounded reward requires gated costs within cap')
    if result['reward_variant'] == 'legacy' and invalid:
        raise ValueError('Invalid-action cost requires bounded reward variant')
    result.update(invalid_action_penalty=invalid, process_penalty_cap=cap)
    result['missing_answer_penalty'] = penalty
    return result


def process_reward_components(report, expected_uid, accepted_answer_em, penalty):
    """
    @brief 从可信事件统一计算门控、成功标签和原奖励，防止分项判定漂移。
    @param report 程序过程报告。
    @param expected_uid 同行轨迹ID。
    @param accepted_answer_em 按原EM归一化判定的0/1分数。
    @param penalty 非负无答案惩罚系数。
    @return 协议门控、布尔任务成功、标签版本和浮点奖励的字典；故障抛错。
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
    reward = float(accepted_answer_em) * gate - penalty * (not report['answered'])
    # 成功由接受答案与同一门控共同决定，不依赖惩罚大小或原文本 EM。
    return dict(protocol_reward=reward, protocol_gate=gate,
                task_success=bool(accepted_answer_em == 1. and gate),
                task_success_version=TASK_SUCCESS_VERSION)


def process_score(report, expected_uid, accepted_answer_em, penalty):
    """@brief 保持原浮点奖励接口，复用统一可信分量计算。
    @param report 程序过程报告。
    @param expected_uid 同行独立轨迹身份。
    @param accepted_answer_em 实际接受答案的零或一 EM。
    @param penalty 非负有限的无答案惩罚。
    @return 与历史公式一致的浮点训练奖励。
    @raises ValueError 来源、协议报告或输入奖励非法。
    """
    # 兼容旧调用方，筛选标签与旧奖励共享唯一门控实现。
    return process_reward_components(report, expected_uid, accepted_answer_em, penalty)['protocol_reward']


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
