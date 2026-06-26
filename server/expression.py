from __future__ import annotations


AVAILABLE_EXPRESSIONS = {
    "不满",
    "大哭",
    "大笑",
    "委屈哭",
    "嫌弃",
    "开心",
    "思考",
    "惊恐",
    "惊讶",
    "愤怒",
    "斜眼惊讶",
    "比心眨眼",
    "生气",
    "眨眼笑",
    "眯眼笑",
    "难过",
}

EXPRESSION_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("大笑", ("哈哈", "笑死", "太好笑", "大笑")),
    ("比心眨眼", ("爱你", "比心", "喜欢你", "谢谢你")),
    ("委屈哭", ("委屈", "想哭", "哭了", "难受")),
    ("大哭", ("大哭", "崩溃", "伤心死")),
    ("愤怒", ("愤怒", "气死", "太过分")),
    ("生气", ("生气", "不爽", "火大")),
    ("惊恐", ("害怕", "恐怖", "吓人", "惊恐")),
    ("斜眼惊讶", ("真的假的", "不会吧", "离谱")),
    ("惊讶", ("惊讶", "震惊", "哇", "没想到")),
    ("思考", ("想一想", "让我想", "思考", "分析", "考虑")),
    ("嫌弃", ("嫌弃", "算了吧", "不要")),
    ("不满", ("不满", "不太行", "不满意")),
    ("难过", ("难过", "失落", "沮丧")),
    ("眯眼笑", ("可以呀", "不错", "舒服")),
    ("眨眼笑", ("好的", "没问题", "当然", "收到")),
    ("开心", ("开心", "高兴", "太棒", "好呀")),
)


def pick_expression(text: str, *, role: str = "assistant") -> str:
    if role == "user":
        return "思考"

    clean_text = str(text or "").strip()
    for expression, keywords in EXPRESSION_KEYWORDS:
        if any(keyword in clean_text for keyword in keywords):
            return expression
    return "开心"
