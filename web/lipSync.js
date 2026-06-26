export function getMouthShapeForRms(rms) {
  if (rms < 0.018) return "closed";
  if (rms < 0.055) return "small";
  if (rms < 0.13) return "medium";
  return "wide";
}

export function buildMouthCues(samples, sampleRate = 24000, windowMs = 50) {
  const windowSize = Math.max(1, Math.round(sampleRate * (windowMs / 1000)));
  const cues = [];

  for (let offset = 0; offset < samples.length; offset += windowSize) {
    const end = Math.min(samples.length, offset + windowSize);
    const rms = getRms(samples, offset, end);
    cues.push({
      atSeconds: Number((offset / sampleRate).toFixed(4)),
      shape: getMouthShapeForRms(rms),
    });
  }

  return compressMouthCues(cues);
}

function getRms(samples, start, end) {
  if (end <= start) return 0;
  let sum = 0;
  for (let index = start; index < end; index += 1) {
    sum += samples[index] * samples[index];
  }
  return Math.sqrt(sum / (end - start));
}

function compressMouthCues(cues) {
  const result = [];
  let previousShape = "";
  for (const cue of cues) {
    if (cue.shape === previousShape) continue;
    result.push(cue);
    previousShape = cue.shape;
  }
  return result;
}
