"""任务成功标签校验与筛选配置规范化；基础模块不持有训练器或 worker。"""
from verl.experimental.process_checks.reward import TASK_SUCCESS_VERSION

TASK_MIXED_VERSION = 'task_success_mixed_v1'
ANSWER_RANGE_MODE = 'answer_correct_3_6'
ANSWER_RANGE_VERSION = 'answer_correct_3_6_v1'


def normalize_dynamic_filter(settings):
    """@brief 规范化组资格模式，旧缺省配置保持原恢复身份。
    @param settings 普通动态筛选配置映射，可为空。
    @return 独立配置字典；旧模式移除缺省字段，新模式包含规则版本。
    @raises ValueError 模式、开启条件或规则版本非法。
    """
    result = dict(settings or {})
    mode = result.get('eligibility', 'reward_variance')
    # 新模式必须显式启用；关闭时保留旧配置的完整语义。
    if mode not in ('reward_variance', 'task_success_mixed', ANSWER_RANGE_MODE):
        raise ValueError('Unknown dynamic eligibility mode')
    if mode in ('task_success_mixed', ANSWER_RANGE_MODE):
        if result.get('enabled', False) is not True:
            raise ValueError('task_success_mixed requires dynamic filtering enabled')
        # 固定3至6规则使用独立版本，不能作为旧成功混合资格恢复。
        expected_version = ANSWER_RANGE_VERSION if mode == ANSWER_RANGE_MODE else TASK_MIXED_VERSION
        if result.get('eligibility_version', expected_version) != expected_version:
            raise ValueError('Unsupported task-success eligibility version')
        result['eligibility_version'] = expected_version
    else:
        # 旧 checkpoint 没有新字段；显式缺省与缺失必须得到相同指纹和策略。
        if result.get('eligibility_version') is not None:
            raise ValueError('reward_variance has no task-success eligibility version')
        result.pop('eligibility', None)
        result.pop('eligibility_version', None)
    return result


def task_success_labels(reports, trace_uids, count):
    """@brief 校验原协议或新增质量成功标签，不从奖励值或原文本EM猜测。
    @param reports 含奖励分量和成功标签版本的逐轨迹报告。
    @param trace_uids 与报告逐行绑定的独立轨迹身份数组。
    @param count 当前真实轨迹行数。
    @return 与输入顺序一致的 Python 布尔成功标签列表。
    @raises ValueError 标签缺失、身份错配、重复身份、版本或分量矛盾。
    @note 来源及协议由共用奖励入口先验证；这里验证标签契合和同行绑定。
    """
    # 报告只允许逐行传递，禁止用 group uid 代替独立轨迹 uid。
    if reports is None or trace_uids is None or len(reports) != count or len(trace_uids) != count:
        raise ValueError('task_success_mixed requires row-bound task-success reports')
    if len(set(map(str, trace_uids))) != count:
        raise ValueError('Duplicate task-success trace identity')
    labels = []
    # 每行分别校验版本与分量；任意一行异常都拒绝整批，避免静默筛掉坏标签。
    for report, uid in zip(reports, trace_uids):
        if not isinstance(report, dict) or report.get('trace_uid') != uid:
            raise ValueError('Task-success report identity mismatch')
        # 标签版本区分协议成功与质量成功，逐行验证对应分量。
        from verl.experimental.process_checks.repetition import QUALITY_SUCCESS_VERSION, REPETITION_VERSION
        label_version = report.get('task_success_version')
        if label_version not in (TASK_SUCCESS_VERSION, QUALITY_SUCCESS_VERSION):
            raise ValueError('Missing or unsupported task-success label version')
        gate, success = report.get('protocol_gate'), report.get('task_success')
        accepted = report.get('accepted_answer_em')
        # 布尔标签必须显式，不能把字符串 false 或任意非零值转成成功。
        if type(gate) is not bool or type(success) is not bool:
            raise ValueError('Task-success flags must be booleans')
        if isinstance(accepted, bool) or accepted not in (0., 1.):
            raise ValueError('Task-success accepted EM must be binary')
        if type(report.get('answered')) is not bool or (not report['answered'] and accepted != 0.):
            raise ValueError('Task-success accepted-answer state mismatch')
        quality = True
        # 新标签同时校验质量门控与规则版本；旧标签严格维持原有成功语义。
        if label_version == QUALITY_SUCCESS_VERSION:
            quality = report.get('quality_gate')
            level = report.get('repetition_level')
            if (type(quality) is not bool or level not in ('normal', 'mild', 'severe')
                    or quality != (level != 'severe') or report.get('repetition_version') != REPETITION_VERSION):
                raise ValueError('Invalid repetition quality label')
        elif any(key in report for key in ('quality_gate', 'repetition_version')):
            raise ValueError('Legacy task-success labels cannot contain quality gates')
        if success != (accepted == 1. and gate and quality):
            raise ValueError('Task-success label disagrees with reward components')
        labels.append(success)
    return labels
