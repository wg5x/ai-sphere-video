import test from "node:test";
import assert from "node:assert/strict";

import {
  chooseAvatarFrame,
  chooseSpeakingExpression,
  createAvatarDriver,
  normalizeEmotion,
  normalizeMouthShape,
} from "../web/avatarDriver.js";

test("chooseSpeakingExpression maps mouth volume to existing face assets", () => {
  assert.equal(chooseSpeakingExpression("开心", "closed"), "开心");
  assert.equal(chooseSpeakingExpression("开心", "small"), "眨眼笑");
  assert.equal(chooseSpeakingExpression("开心", "medium"), "大笑");
  assert.equal(chooseSpeakingExpression("开心", "wide"), "大笑");
  assert.equal(chooseSpeakingExpression("难过", "medium"), "委屈哭");
  assert.equal(chooseSpeakingExpression("生气", "wide"), "愤怒");
  assert.equal(chooseSpeakingExpression("惊讶", "medium"), "惊讶");
});

test("avatar driver separates base emotion from speaking frame", () => {
  const frames = [];
  const driver = createAvatarDriver((name) => frames.push(name));

  driver.setEmotion("难过");
  driver.setMouthShape("small");
  driver.setMouthShape("closed");

  assert.deepEqual(frames, ["难过", "委屈哭", "难过"]);
});

test("normalizeEmotion maps legacy Chinese expressions to structured emotions", () => {
  assert.equal(normalizeEmotion("开心"), "happy");
  assert.equal(normalizeEmotion("思考"), "thinking");
  assert.equal(normalizeEmotion("斜眼惊讶"), "surprised");
  assert.equal(normalizeEmotion("大哭"), "sad");
  assert.equal(normalizeEmotion("愤怒"), "angry");
});

test("normalizeMouthShape maps realtime volume shapes to asset mouth shapes", () => {
  assert.equal(normalizeMouthShape("closed"), "closed");
  assert.equal(normalizeMouthShape("small"), "open_small");
  assert.equal(normalizeMouthShape("medium"), "open_wide");
  assert.equal(normalizeMouthShape("wide"), "open_wide");
});

test("chooseAvatarFrame returns structured asset id and legacy fallback", () => {
  assert.deepEqual(
    chooseAvatarFrame("难过", "medium"),
    {
      assetId: "sad_open_wide",
      assetSrc: "/outputs/avatar_faces/sad_open_wide.png",
      emotion: "sad",
      fallbackSrc: "/outputs/faces/%E5%A4%A7%E5%93%AD.png",
      legacyExpression: "大哭",
      mouthShape: "open_wide",
    },
  );
});

test("chooseAvatarFrame uses v2 sample assets for available preview expressions", () => {
  assert.deepEqual(
    chooseAvatarFrame("开心", "large"),
    {
      assetId: "v2_sample_开心_mouth_04_large",
      assetSrc: "/outputs/avatar_faces_v2_sample/%E5%BC%80%E5%BF%83/mouth_04_large.png",
      emotion: "happy",
      fallbackSrc: "/outputs/faces/%E5%A4%A7%E7%AC%91.png",
      legacyExpression: "大笑",
      mouthShape: "mouth_04_large",
    },
  );
});
