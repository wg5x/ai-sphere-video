import test from "node:test";
import assert from "node:assert/strict";

import { decodePcm16ToFloat32, encodePcm16, resampleTo16k } from "../web/audio.js";

test("resampleTo16k downsamples 48k input to one third length", () => {
  const input = new Float32Array(480);
  const output = resampleTo16k(input, 48000);

  assert.equal(output.length, 160);
});

test("encodePcm16 writes little-endian signed 16-bit samples", () => {
  const encoded = encodePcm16(new Float32Array([-1, 0, 1]));
  const view = new DataView(encoded);

  assert.equal(view.getInt16(0, true), -32768);
  assert.equal(view.getInt16(2, true), 0);
  assert.equal(view.getInt16(4, true), 32767);
});

test("decodePcm16ToFloat32 decodes little-endian PCM into normalized samples", () => {
  const buffer = new ArrayBuffer(4);
  const view = new DataView(buffer);
  view.setInt16(0, -32768, true);
  view.setInt16(2, 32767, true);

  const decoded = decodePcm16ToFloat32(buffer);

  assert.equal(decoded.length, 2);
  assert.equal(decoded[0], -1);
  assert.ok(decoded[1] > 0.999);
});
