const SPEAKING_EXPRESSION_BY_EMOTION = {
  不满: { small: "不满", medium: "生气", wide: "愤怒" },
  大哭: { small: "委屈哭", medium: "大哭", wide: "大哭" },
  大笑: { small: "眯眼笑", medium: "大笑", wide: "大笑" },
  委屈哭: { small: "难过", medium: "委屈哭", wide: "大哭" },
  嫌弃: { small: "嫌弃", medium: "不满", wide: "不满" },
  开心: { small: "眨眼笑", medium: "大笑", wide: "大笑" },
  思考: { small: "思考", medium: "开心", wide: "惊讶" },
  惊恐: { small: "惊讶", medium: "惊恐", wide: "惊恐" },
  惊讶: { small: "惊讶", medium: "惊讶", wide: "斜眼惊讶" },
  愤怒: { small: "生气", medium: "愤怒", wide: "愤怒" },
  斜眼惊讶: { small: "斜眼惊讶", medium: "惊讶", wide: "惊恐" },
  比心眨眼: { small: "比心眨眼", medium: "眨眼笑", wide: "大笑" },
  生气: { small: "生气", medium: "愤怒", wide: "愤怒" },
  眨眼笑: { small: "眨眼笑", medium: "开心", wide: "大笑" },
  眯眼笑: { small: "眯眼笑", medium: "眨眼笑", wide: "大笑" },
  难过: { small: "难过", medium: "委屈哭", wide: "大哭" },
};

export function chooseSpeakingExpression(baseEmotion, mouthShape) {
  if (mouthShape === "closed") return baseEmotion;
  const mapping = SPEAKING_EXPRESSION_BY_EMOTION[baseEmotion] || SPEAKING_EXPRESSION_BY_EMOTION["开心"];
  return mapping[mouthShape] || baseEmotion;
}

export function createAvatarDriver(renderExpression) {
  let baseEmotion = "开心";
  let currentExpression = "";
  let currentMouthShape = "closed";

  function renderNext() {
    const nextExpression = chooseSpeakingExpression(baseEmotion, currentMouthShape);
    if (nextExpression === currentExpression) return;
    currentExpression = nextExpression;
    renderExpression(nextExpression, { baseEmotion, mouthShape: currentMouthShape });
  }

  return {
    setEmotion(nextEmotion) {
      baseEmotion = nextEmotion || "开心";
      renderNext();
    },
    setMouthShape(nextShape) {
      currentMouthShape = nextShape || "closed";
      renderNext();
    },
  };
}
