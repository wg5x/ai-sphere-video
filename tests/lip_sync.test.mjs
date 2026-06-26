import test from "node:test";
import assert from "node:assert/strict";

import { buildMouthCues, getMouthShapeForRms } from "../web/lipSync.js";

test("getMouthShapeForRms maps silence and loud samples to mouth shapes", () => {
  assert.equal(getMouthShapeForRms(0), "closed");
  assert.equal(getMouthShapeForRms(0.025), "small");
  assert.equal(getMouthShapeForRms(0.08), "medium");
  assert.equal(getMouthShapeForRms(0.18), "wide");
});

test("buildMouthCues creates timed mouth cues from PCM samples", () => {
  const samples = new Float32Array([
    ...new Array(1200).fill(0),
    ...new Array(1200).fill(0.2),
  ]);

  const cues = buildMouthCues(samples, 24000, 50);

  assert.equal(cues.length, 2);
  assert.deepEqual(cues[0], { atSeconds: 0, shape: "closed" });
  assert.deepEqual(cues[1], { atSeconds: 0.05, shape: "wide" });
});
