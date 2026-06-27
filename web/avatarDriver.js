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

const STRUCTURED_FACE_ASSET_BASE = "/outputs/avatar_faces/";
const V2_SAMPLE_FACE_ASSET_BASE = "/outputs/avatar_faces_v2_sample/";
const LEGACY_FACE_ASSET_BASE = "/outputs/faces/";
const V2_SAMPLE_EXPRESSIONS = new Set(["开心", "思考", "生气"]);
const V2_SAMPLE_MOUTH_BY_REALTIME = {
  closed: "mouth_00_closed",
  tiny: "mouth_01_tiny",
  small: "mouth_02_small",
  medium: "mouth_03_medium",
  large: "mouth_04_large",
  wide: "mouth_05_wide",
};

const LEGACY_TO_EMOTION = {
  不满: "angry",
  大哭: "sad",
  大笑: "happy",
  委屈哭: "sad",
  嫌弃: "angry",
  开心: "happy",
  思考: "thinking",
  惊恐: "surprised",
  惊讶: "surprised",
  愤怒: "angry",
  斜眼惊讶: "surprised",
  比心眨眼: "happy",
  生气: "angry",
  眨眼笑: "happy",
  眯眼笑: "happy",
  难过: "sad",
};

const LEGACY_FALLBACK_BY_ASSET = {
  happy_closed: "开心",
  happy_open_small: "眨眼笑",
  happy_open_wide: "大笑",
  thinking_closed: "思考",
  thinking_open_small: "开心",
  thinking_open_wide: "惊讶",
  surprised_closed: "惊讶",
  surprised_open_small: "惊讶",
  surprised_open_wide: "斜眼惊讶",
  sad_closed: "难过",
  sad_open_small: "委屈哭",
  sad_open_wide: "大哭",
  angry_closed: "生气",
  angry_open_small: "愤怒",
  angry_open_wide: "愤怒",
};

function buildPngSrc(base, name) {
  return `${base}${encodeURIComponent(name)}.png`;
}

function buildNestedPngSrc(base, directory, name) {
  return `${base}${encodeURIComponent(directory)}/${encodeURIComponent(name)}.png`;
}

export function chooseSpeakingExpression(baseEmotion, mouthShape) {
  if (mouthShape === "closed") return baseEmotion;
  const mapping = SPEAKING_EXPRESSION_BY_EMOTION[baseEmotion] || SPEAKING_EXPRESSION_BY_EMOTION["开心"];
  return mapping[mouthShape] || baseEmotion;
}

export function normalizeEmotion(expression) {
  return LEGACY_TO_EMOTION[expression] || "happy";
}

export function normalizeMouthShape(shape) {
  if (shape === "small") return "open_small";
  if (shape === "medium" || shape === "wide") return "open_wide";
  return "closed";
}

function normalizeLegacyMouthShape(shape) {
  if (shape === "tiny") return "small";
  if (shape === "large") return "wide";
  return shape;
}

export function chooseAvatarFrame(baseExpression, realtimeMouthShape) {
  const emotion = normalizeEmotion(baseExpression);
  if (V2_SAMPLE_EXPRESSIONS.has(baseExpression)) {
    const mouthShape = V2_SAMPLE_MOUTH_BY_REALTIME[realtimeMouthShape] || V2_SAMPLE_MOUTH_BY_REALTIME.closed;
    const legacyMouthShape = normalizeLegacyMouthShape(realtimeMouthShape);
    const legacyExpression = chooseSpeakingExpression(baseExpression, legacyMouthShape);

    return {
      assetId: `v2_sample_${baseExpression}_${mouthShape}`,
      assetSrc: buildNestedPngSrc(V2_SAMPLE_FACE_ASSET_BASE, baseExpression, mouthShape),
      emotion,
      fallbackSrc: buildPngSrc(LEGACY_FACE_ASSET_BASE, legacyExpression),
      legacyExpression,
      mouthShape,
    };
  }

  const mouthShape = normalizeMouthShape(realtimeMouthShape);
  const assetId = `${emotion}_${mouthShape}`;
  const legacyExpression = LEGACY_FALLBACK_BY_ASSET[assetId] || baseExpression || "开心";

  return {
    assetId,
    assetSrc: buildPngSrc(STRUCTURED_FACE_ASSET_BASE, assetId),
    emotion,
    fallbackSrc: buildPngSrc(LEGACY_FACE_ASSET_BASE, legacyExpression),
    legacyExpression,
    mouthShape,
  };
}

export function createAvatarDriver(renderExpression) {
  let baseEmotion = "开心";
  let currentExpression = "";
  let currentMouthShape = "closed";

  function renderNext() {
    const nextFrame = chooseAvatarFrame(baseEmotion, currentMouthShape);
    if (nextFrame.assetId === currentExpression) return;
    currentExpression = nextFrame.assetId;
    renderExpression(nextFrame.legacyExpression, {
      ...nextFrame,
      baseEmotion,
    });
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
