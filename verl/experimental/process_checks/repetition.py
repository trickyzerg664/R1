"""实际消费模型文本的重复检测与有界奖励；不依赖训练器、Ray 或 GPU。"""
from collections import defaultdict
import math
import re
from .protocol import protected_text

REPETITION_VERSION = 'repetition_v1'
QUALITY_SUCCESS_VERSION = 'task_success_quality_v1'
CONTROL_TAG = re.compile(r'</?(?:think|search|answer|information)>')
THINK_TAG = re.compile(r'</?think>')


def repetition_config(settings):
    """@brief 校验独立重复规则，缺省关闭且拒绝误拼字段。
    @param settings 可空的规则映射；阈值为有限数值，次数为正整数。
    @return 带全部默认值的独立字典。
    @raises ValueError 开关、版本、阈值或字段非法。
    """
    defaults = dict(enabled=False, version=REPETITION_VERSION, min_tokens=64,
                    mild_ratio=.15, severe_ratio=.40, mild_penalty=.10,
                    severe_penalty=.12, tag_penalty=.02, tag_run=4,
                    duplicate_opens=3, short_gap_tokens=8)
    supplied = dict(settings or {})
    # 配置拼错必须在启动时失败，避免静默沿用另一套阈值。
    if set(supplied) - set(defaults):
        raise ValueError('Unknown repetition configuration fields')
    result = dict(defaults, **supplied)
    # 严格布尔和版本避免字符串false以及旧规则混用。
    if type(result['enabled']) is not bool or result['version'] != REPETITION_VERSION:
        raise ValueError('Invalid repetition switch/version')
    # 次数阈值不能接受布尔或小数，正文和标签的最短限制分开处理。
    for key in ('min_tokens', 'tag_run', 'duplicate_opens', 'short_gap_tokens'):
        if type(result[key]) is not int or result[key] <= 0:
            raise ValueError('Repetition counts must be positive integers')
    # 数值显式拒绝NaN/Inf和隐式类型转换，保证奖励始终有限。
    for key in ('mild_ratio', 'severe_ratio', 'mild_penalty', 'severe_penalty', 'tag_penalty'):
        if isinstance(result[key], bool) or not isinstance(result[key], (int, float)) or not math.isfinite(result[key]):
            raise ValueError('Repetition thresholds must be finite numbers')
    # 总成本仍由既有过程上限封顶；单项成本也不得突破原 .12 边界。
    if not 0 < result['mild_ratio'] < result['severe_ratio'] <= 1:
        raise ValueError('Invalid repetition ratio interval')
    if any(not 0 <= result[key] <= .12 for key in ('mild_penalty', 'severe_penalty', 'tag_penalty')):
        raise ValueError('Invalid repetition penalty')
    if result['severe_penalty'] <= 0 or result['tag_run'] < 4:
        raise ValueError('Severe repetition requires a positive cost and at least four tags')
    return result


def repeated_coverage(tokens):
    """@brief 合并至少四次非重叠出现的 4/8/16 gram 后续位置，首份内容不罚。
    @param tokens 一轮正文 token ID 列表，不含固定协议标签。
    @return 重复位置数除以正文长度；空正文返回零。
    """
    covered = bytearray(len(tokens))
    # 非重叠计数防止同一长词的滑动窗口虚增次数；跨 n 的位置只计一次。
    for n in (4, 8, 16):
        occurrences = defaultdict(list)
        for start in range(len(tokens) - n + 1):
            key = tuple(tokens[start:start + n])
            positions = occurrences[key]
            if not positions or start >= positions[-1] + n:
                positions.append(start)
        for positions in occurrences.values():
            if len(positions) >= 4:
                for start in positions[1:]:
                    covered[start:start + n] = b'\x01' * n
    return sum(covered) / len(tokens) if tokens else 0.


def inspect_turn(text, encode, config, initial_think=False):
    """@brief 分别检查正文重复、未闭合重复开启和无正文标签循环。
    @param text 一轮实际消费模型文字，不含工具观察或未执行尾部。
    @param encode 共用 tokenizer 的无特殊 token 编码回调。
    @param config 已校验重复配置。
    @param initial_think 首轮输入前缀是否已打开思考块。
    @return 正文比例、重复开启数、标签循环长度、级别及惩罚。
    @note 未闭合一次可由截断产生，不独立判为重复；每轮工具边界重新开始。
    """
    # 代码块、引用行和引号中的标签是字面量，不作为协议结构重复。
    clean = protected_text(text)
    quoted = r'"(?:\\.|[^"\\\n])*"|“[^”\n]*”|(?<!\w)\'(?:\\.|[^\'\\\n])*\'(?!\w)'
    for match in re.finditer(quoted, text):
        if THINK_TAG.search(match.group()):
            clean = clean[:match.start()] + ' ' * (match.end() - match.start()) + clean[match.end():]
    # 仅删活动协议标签；引用/代码里的文字仍参加正文重复检查。
    pieces, end = [], 0
    for tag in CONTROL_TAG.finditer(clean):
        pieces.extend((text[end:tag.start()], ' '))
        end = tag.end()
    pieces.append(text[end:])
    tokens = encode(''.join(pieces))
    ratio = repeated_coverage(tokens) if len(tokens) >= config['min_tokens'] else 0.
    opened, duplicate, short_duplicates, run, longest = initial_think, 0, 0, 0, 0
    previous_end = None
    # 仅 think 标签构成循环证据，避免合法 think/search/answer 各一次被误判。
    for tag in THINK_TAG.finditer(clean):
        gap = None if previous_end is None else text[previous_end:tag.start()]
        run = run + 1 if gap is not None and not gap.strip() else 1
        longest = max(longest, run)
        if tag.group() == '<think>':
            if opened:
                duplicate += 1
                if gap is not None and len(encode(gap)) <= config['short_gap_tokens']:
                    short_duplicates += 1
            opened = True
        else:
            opened = False
        previous_end = tag.end()
    # 标签规则不受最短正文限制；重度标记不会被后续正常答案稀释。
    severe = (ratio >= config['severe_ratio'] or longest >= config['tag_run']
              or short_duplicates >= config['duplicate_opens'])
    mild_cost = config['mild_penalty'] * max(0., ratio - config['mild_ratio']) / (
        config['severe_ratio'] - config['mild_ratio'])
    cost = config['severe_penalty'] if severe else min(
        config['mild_penalty'], mild_cost + duplicate * config['tag_penalty'])
    return dict(repeated_ratio=ratio, body_tokens=len(tokens), duplicate_think_opens=duplicate,
                tag_run=longest, level='severe' if severe else 'mild' if cost > 0 else 'normal',
                penalty=cost)


def repetition_reward(report, components, config, encode, prompt=''):
    """@brief 从可信消费事件重算重复，严重重复取消正奖并同步成功标签。
    @param report 已经由统一协议入口验证的逐轨迹报告。
    @param components 既有有界奖励分量。
    @param config 已校验完整过程配置，重复默认关闭。
    @param encode 真实 tokenizer 的无特殊 token 编码回调。
    @param prompt 原输入提示，仅用于识别末尾预置的思考开始标签。
    @return 新奖励分量字典；关闭时原分量逐字段保持不变。
    @note 开启时只消费 events.consumed；raw 尾部、calls 观察与人工重建标签不计正文。
    """
    settings = config['repetition']
    if not settings['enabled']:
        return dict(components)
    # 工具返回及环境提示不来自模型，逐轮检测阻止跨工具边界误拼重复片段。
    turns = [inspect_turn(event['consumed'], encode, settings,
                          initial_think=bool(i == 0 and re.search(r'<think>\s*$', prompt)))
             for i, event in enumerate(report['events'])]
    severe = any(turn['level'] == 'severe' for turn in turns)
    cost = max((turn['penalty'] for turn in turns), default=0.)
    quality_gate = not severe
    task_success = bool(components['task_success'] and quality_gate)
    # 采用最严重一轮的成本，和原过程成本合并封顶；答案正确也不能重置质量门控。
    penalty = min(config['process_penalty_cap'], components['process_penalty'] + cost)
    result = dict(components)
    result.update(task_success=task_success, task_success_version=QUALITY_SUCCESS_VERSION,
                  quality_gate=quality_gate, repetition_level='severe' if severe else
                  'mild' if cost > 0 else 'normal', repetition_penalty=cost,
                  repetition_version=REPETITION_VERSION, repetition_turns=turns,
                  process_penalty=penalty, training_reward=float(task_success) - penalty)
    return result
