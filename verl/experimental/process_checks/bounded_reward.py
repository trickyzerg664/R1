"""有界无效动作软罚：只消费可信报告与原生终止，不罚文风或长度截断。"""
from .protocol import parse_action

REWARD_VERSION = 'bounded_invalid_v1'
INVALID_CODES = {'empty_action', 'nested_action', 'search_forbidden',
                 'missing_action', 'unclosed_action', 'action_parse_mismatch'}

def bounded_reward(report, components, config):
    """@brief 在原门控与成功标签上追加有界软罚，未知终止和长度截断免新增惩罚。
    @param report 已由原process_reward_components校验的同行程序报告。
    @param components 原奖励分量字典，任务成功标签保持不变。
    @param config 已由check_config校验的过程配置。
    @return 新字典，包含原奖励、新训练奖励、惩罚及终止覆盖计数。
    @raises ValueError 终止记录与事件数量不一致。
    @note 仅原生stop且执行器拒绝的消费动作可计数；不分析未消费尾部。
    """
    result = dict(components)
    if config['reward_variant'] == 'legacy':
        return result
    events = report['events']
    native = report.get('token_diagnostics')
    # 没有原生记录时全部标未知；绝不通过字符/长度猜测违规。
    if native is not None and len(native) != len(events):
        raise ValueError('Termination records differ from process event count')
    native = native if native is not None else [{} for _ in events]
    invalid = unknown = length = 0
    for event, termination in zip(events, native):
        finish = termination.get('finish_reason')
        if finish == 'length':
            length += 1
            continue
        if finish != 'stop':
            unknown += 1
            continue
        # 原解析器重算原因；真实执行拒绝作为第二道条件，不误罚正常重试或接受动作。
        codes = {r['code'] for r in parse_action(event['consumed'])['reasons']}
        codes.update(r['code'] for r in event['reasons'])
        if not event['accepted'] and event['executed'] is None and codes & INVALID_CODES:
            invalid += 1
    missing_cost = config['missing_answer_penalty'] * (not report['answered'])
    # 成功基值为可信任务标签；总过程成本封顶.12，使G8混合组中的失败优势仍为负。
    extra_cost = config['invalid_action_penalty'] * min(invalid, 2)
    penalty = min(config['process_penalty_cap'], missing_cost + extra_cost)
    result.update(training_reward=float(components['task_success']) - penalty,
                  process_penalty=penalty, invalid_action_penalty=extra_cost,
                  invalid_action_count=invalid, unknown_termination_count=unknown,
                  length_termination_count=length, termination_events=len(events),
                  reward_version=REWARD_VERSION)
    return result
