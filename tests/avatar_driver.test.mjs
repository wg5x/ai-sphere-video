import test from "node:test";
import assert from "node:assert/strict";

import { chooseSpeakingExpression, createAvatarDriver } from "../web/avatarDriver.js";

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
  driver.setMouthShape("medium");
  driver.setMouthShape("closed");

  assert.deepEqual(frames, ["难过", "委屈哭", "难过"]);
});
