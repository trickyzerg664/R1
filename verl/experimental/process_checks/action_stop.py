"""复用正式动作解析器，判断能否在当前前缀安全结束本轮生成。"""
import re
from .protocol import parse_action


def pending_literal(prefix):
    """@brief 检查动作之前是否仍有尚未闭合的引用或行内代码。
    @param prefix 当前动作起点之前的原始模型文本。
    @return 是否应等待字面量闭合，避免把引用中的动作误执行。
    @note 未闭合引用采用保守等待；普通英文缩写不会开启单引号引用。
    """
    state = None
    escaped = False
    for i, char in enumerate(prefix):
        # 转义引号不关闭引用，行内代码内的引号也不改变状态。
        if escaped:
            escaped = False
            continue
        if char == '\\' and state in ('"', "'"):
            escaped = True
            continue
        if state is not None:
            if char == state:
                state = None
            continue
        if char in ('`', '"'):
            state = char
        elif char == '“':
            state = '”'
        elif char == "'" and (i == 0 or not re.match(r'\w', prefix[i - 1])):
            # 与正式解析器一致：don't、That's 等词内单引号不视为字面量起点。
            state = "'"
    return state is not None


def action_complete(text):
    """@brief 只在正式解析器认可的完整合法首动作之后允许停止。
    @param text 本轮已生成 token 解码所得文本，尚未追加强制结束 token。
    @return 是否允许仅生成结束 token；不改变已经采样的动作内容。
    @note 违规、嵌套、空动作与未闭合字面量保留原生成行为。
    """
    # 先做廉价判断，再复用原有保护、配对、嵌套与协议检查，避免独立实现评分规则。
    if '</search>' not in text and '</answer>' not in text:
        return False
    parsed = parse_action(text)
    if not parsed['valid'] or parsed['reasons']:
        return False
    start = parsed['action_span'][0]
    # 字面量尚未闭合时，未来的引号可能改变正式解析结果，因此暂不停止。
    return not pending_literal(text[:start])
