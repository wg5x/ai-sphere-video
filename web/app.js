import { base64ToArrayBuffer, decodePcm16ToFloat32, encodePcm16, resampleTo16k } from "./audio.js";
import { createAvatarDriver } from "./avatarDriver.js";
import { buildMouthCues } from "./lipSync.js";

const APP_BASE_URL = getAppBaseUrl();
const DEFAULT_CONFIG = {
  speaker: "zh_female_vv_jupiter_bigtts",
  botName: "赛博国潮小孩",
  systemRole: "你是一个国潮风格的虚拟人。你会用简短、自然、友好的中文回答，适合实时语音对话。",
  speakingStyle: "活泼、清晰、不要太长。",
  openingLine: "你好呀，我在这里。",
  speechRate: 0,
  loudnessRate: 0,
};

const state = {
  audioContext: null,
  audioProcessor: null,
  micSource: null,
  micStream: null,
  muted: false,
  playbackContext: null,
  playbackMuted: false,
  nextPlaybackTime: 0,
  socket: null,
  uploadReady: false,
};

const dom = {
  assistantLine: document.querySelector("[data-assistant-line]"),
  configForm: document.querySelector("[data-config-form]"),
  endButton: document.querySelector("[data-end]"),
  events: document.querySelector("[data-events]"),
  expression: document.querySelector("[data-expression]"),
  face: document.querySelector("[data-face]"),
  health: document.querySelector("[data-health]"),
  interruptButton: document.querySelector("[data-interrupt]"),
  muteButton: document.querySelector("[data-mute]"),
  mouth: document.querySelector("[data-mouth]"),
  startButton: document.querySelector("[data-start]"),
  status: document.querySelector("[data-status]"),
  textForm: document.querySelector("[data-text-form]"),
  textInput: document.querySelector("[data-text-input]"),
};

const avatar = createAvatarDriver((name, frame) => setFaceExpression(name, frame));

setExpression("开心");
refreshHealth();
startV2SamplePreviewIfRequested();

dom.startButton.addEventListener("click", () => {
  void startCall();
});

dom.endButton.addEventListener("click", () => {
  endCall();
});

dom.interruptButton.addEventListener("click", () => {
  interrupt();
});

dom.muteButton.addEventListener("click", () => {
  state.muted = !state.muted;
  state.uploadReady = !state.muted && state.socket?.readyState === WebSocket.OPEN && dom.status.dataset.status === "connected";
  dom.muteButton.textContent = state.muted ? "恢复" : "静音";
  setStatus(state.muted ? "muted" : dom.status.dataset.status || "idle");
});

dom.textForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = dom.textInput.value.trim();
  if (!text || state.socket?.readyState !== WebSocket.OPEN) return;
  setExpression("思考");
  state.socket.send(JSON.stringify({ type: "user_text", text }));
  dom.textInput.value = "";
});

async function refreshHealth() {
  try {
    const response = await fetch(getAppUrl("health"));
    const body = await response.json();
    dom.health.textContent = body.volcengine ? "豆包配置已加载" : "未配置豆包密钥";
  } catch {
    dom.health.textContent = "服务未连接";
  }
}

async function startCall() {
  if (state.socket && state.socket.readyState === WebSocket.OPEN) return;

  setStatus("connecting");
  setExpression("思考");
  clearEvents();
  state.playbackMuted = false;

  const playbackReady = await ensurePlaybackReady();
  if (!playbackReady) {
    setStatus("idle");
    addEvent("system", "音频播放不可用");
    return;
  }

  const ws = new WebSocket(getWsUrl("realtime"));
  ws.binaryType = "arraybuffer";
  state.socket = ws;

  ws.onopen = async () => {
    const micReady = await startMicrophone(ws);
    if (!micReady || state.socket !== ws || ws.readyState !== WebSocket.OPEN) {
      ws.close();
      return;
    }

    ws.send(JSON.stringify({ type: "start", payload: { config: readConfig() } }));
  };

  ws.onmessage = (message) => {
    if (state.socket !== ws || typeof message.data !== "string") return;
    handleServerMessage(message.data);
  };

  ws.onerror = () => {
    addEvent("system", "WebSocket 连接错误");
    setStatus("idle");
  };

  ws.onclose = () => {
    if (state.socket === ws) {
      state.socket = null;
      state.uploadReady = false;
      stopMicrophone();
      setStatus("idle");
    }
  };
}

function readConfig() {
  const formData = new FormData(dom.configForm);
  return {
    ...DEFAULT_CONFIG,
    speaker: String(formData.get("speaker") || DEFAULT_CONFIG.speaker).trim(),
    botName: String(formData.get("botName") || DEFAULT_CONFIG.botName).trim(),
    systemRole: String(formData.get("systemRole") || DEFAULT_CONFIG.systemRole).trim(),
    speakingStyle: String(formData.get("speakingStyle") || DEFAULT_CONFIG.speakingStyle).trim(),
    openingLine: String(formData.get("openingLine") || "").trim(),
  };
}

function handleServerMessage(raw) {
  let data;
  try {
    data = JSON.parse(raw);
  } catch {
    return;
  }

  if (data.type === "status") {
    setStatus(data.status || "idle");
    state.uploadReady = data.status === "connected" && !state.muted;
    if (data.status === "connected") {
      addEvent("system", "已连接");
    }
    return;
  }

  if (data.type === "event" && data.event) {
    const event = data.event;
    const cleanText = cleanEventText(event.text || "");
    addEvent(event.type, cleanText);
    if (event.type === "assistant") {
      dom.assistantLine.textContent = cleanText;
    }
    setExpression(event.expression || (event.type === "asr" ? "思考" : "开心"));
    return;
  }

  if (data.type === "audio" && data.data) {
    if (!state.playbackMuted) {
      playPcmAudio(data.data);
    }
    return;
  }

  if (data.type === "error") {
    addEvent("system", data.message || "发生错误");
    setStatus("idle");
  }
}

function endCall() {
  const ws = state.socket;
  state.socket = null;
  state.uploadReady = false;
  state.playbackMuted = true;
  stopPlayback();
  stopMicrophone();
  setExpression("开心");

  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "finish" }));
  }
  if (ws?.readyState === WebSocket.OPEN || ws?.readyState === WebSocket.CONNECTING) {
    ws.close();
  }
}

function interrupt() {
  state.playbackMuted = true;
  stopPlayback();
  setExpression("思考");
  if (state.socket?.readyState === WebSocket.OPEN) {
    state.socket.send(JSON.stringify({ type: "interrupt" }));
  }
  window.setTimeout(() => {
    state.playbackMuted = false;
  }, 250);
}

async function startMicrophone(ws) {
  stopMicrophone();
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    const audioContext = new AudioContextClass();
    const source = audioContext.createMediaStreamSource(stream);
    const processor = audioContext.createScriptProcessor(2048, 1, 1);

    processor.onaudioprocess = (event) => {
      if (!state.uploadReady || state.muted || ws.readyState !== WebSocket.OPEN) return;
      const input = event.inputBuffer.getChannelData(0);
      const pcm = encodePcm16(resampleTo16k(input, audioContext.sampleRate));
      if (pcm.byteLength > 0) {
        ws.send(pcm);
      }
    };

    source.connect(processor);
    processor.connect(audioContext.destination);
    state.micStream = stream;
    state.audioContext = audioContext;
    state.micSource = source;
    state.audioProcessor = processor;
    return true;
  } catch (error) {
    addEvent("system", getMicrophoneFailureText(error));
    setStatus("idle");
    return false;
  }
}

function stopMicrophone() {
  state.audioProcessor?.disconnect();
  state.micSource?.disconnect();
  state.micStream?.getTracks().forEach((track) => track.stop());
  void state.audioContext?.close().catch(() => undefined);
  state.audioProcessor = null;
  state.audioContext = null;
  state.micSource = null;
  state.micStream = null;
}

async function ensurePlaybackReady() {
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextClass) return false;
  if (!state.playbackContext || state.playbackContext.state === "closed") {
    state.playbackContext = new AudioContextClass({ sampleRate: 24000 });
    state.nextPlaybackTime = state.playbackContext.currentTime + 0.08;
  }
  if (state.playbackContext.state === "suspended") {
    await state.playbackContext.resume();
  }
  return state.playbackContext.state !== "closed";
}

function playPcmAudio(base64Audio) {
  const playbackContext = state.playbackContext;
  if (!playbackContext) return;

  const samples = decodePcm16ToFloat32(base64ToArrayBuffer(base64Audio));
  if (!samples.length) return;

  const buffer = playbackContext.createBuffer(1, samples.length, 24000);
  buffer.copyToChannel(samples, 0);

  const source = playbackContext.createBufferSource();
  source.buffer = buffer;
  source.connect(playbackContext.destination);

  const startAt = Math.max(playbackContext.currentTime + 0.02, state.nextPlaybackTime);
  source.start(startAt);
  scheduleMouthCues(samples, startAt);
  state.nextPlaybackTime = startAt + buffer.duration;
}

function stopPlayback() {
  state.nextPlaybackTime = state.playbackContext?.currentTime || 0;
  setMouthShape("closed");
}

function setStatus(status) {
  dom.status.dataset.status = status;
  const labels = {
    connected: "通话中",
    connecting: "连接中",
    ending: "结束中",
    idle: "未开始",
    muted: "已静音",
  };
  dom.status.textContent = labels[status] || status;
}

function setExpression(name) {
  dom.expression.textContent = name;
  avatar.setEmotion(name);
}

function setFaceExpression(name, frame) {
  const fallbackSrc = frame?.fallbackSrc || `/outputs/faces/${encodeURIComponent(name)}.png`;
  const assetSrc = frame?.assetSrc || fallbackSrc;
  dom.face.onerror = assetSrc === fallbackSrc ? null : () => {
    dom.face.onerror = null;
    dom.face.src = getAppUrl(fallbackSrc);
  };
  dom.face.src = getAppUrl(assetSrc);
  dom.face.alt = name;
  if (frame?.assetId) {
    dom.face.dataset.assetId = frame.assetId;
  } else {
    delete dom.face.dataset.assetId;
  }
}

function scheduleMouthCues(samples, audioStartAt) {
  const playbackContext = state.playbackContext;
  if (!playbackContext) return;

  for (const cue of buildMouthCues(samples, 24000, 50)) {
    const delayMs = Math.max(0, (audioStartAt + cue.atSeconds - playbackContext.currentTime) * 1000);
    window.setTimeout(() => {
      if (!state.playbackMuted) {
        setMouthShape(cue.shape);
      }
    }, delayMs);
  }

  const closeDelayMs = Math.max(0, (audioStartAt + samples.length / 24000 - playbackContext.currentTime) * 1000);
  window.setTimeout(() => setMouthShape("closed"), closeDelayMs + 80);
}

function setMouthShape(shape) {
  avatar.setMouthShape(shape);
  if (dom.mouth) {
    dom.mouth.dataset.shape = "closed";
  }
}

function startV2SamplePreviewIfRequested() {
  const params = new URLSearchParams(window.location.search);
  if (params.get("v2sample") !== "1") return;

  const expressions = ["开心", "思考", "生气"];
  const mouthShapes = ["closed", "tiny", "small", "medium", "large", "wide", "large", "medium", "small", "tiny"];
  let expressionIndex = 0;
  let mouthIndex = 0;

  dom.assistantLine.textContent = "v2 小样预览：开心 / 思考 / 生气";
  setExpression(expressions[expressionIndex]);

  window.setInterval(() => {
    setMouthShape(mouthShapes[mouthIndex]);
    mouthIndex += 1;
    if (mouthIndex < mouthShapes.length) return;

    mouthIndex = 0;
    expressionIndex = (expressionIndex + 1) % expressions.length;
    setExpression(expressions[expressionIndex]);
  }, 240);
}

function addEvent(type, text) {
  const item = document.createElement("li");
  item.className = `event ${type}`;
  item.innerHTML = `<span>${typeLabel(type)}</span><p></p>`;
  item.querySelector("p").textContent = text;
  dom.events.prepend(item);
  while (dom.events.children.length > 24) {
    dom.events.lastElementChild.remove();
  }
}

function clearEvents() {
  dom.events.innerHTML = "";
}

function cleanEventText(text) {
  return String(text).replace(/^(ASRResponse|ChatResponse):\s*/, "");
}

function typeLabel(type) {
  if (type === "asr") return "你";
  if (type === "assistant") return "虚拟人";
  return "系统";
}

function getMicrophoneFailureText(error) {
  if (error instanceof DOMException) {
    if (error.name === "NotAllowedError" || error.name === "SecurityError") return "麦克风权限未开启";
    if (error.name === "NotFoundError") return "没有检测到麦克风";
    if (error.name === "NotReadableError") return "麦克风暂时不可用";
  }
  return "麦克风启动失败";
}

function getAppBaseUrl() {
  const pathname = window.location.pathname;
  if (pathname.endsWith("/")) return new URL(pathname, window.location.origin);
  const basename = pathname.slice(pathname.lastIndexOf("/") + 1);
  const basePath = basename.includes(".") ? pathname.replace(/[^/]*$/, "") : `${pathname}/`;
  return new URL(basePath || "/", window.location.origin);
}

function getAppUrl(path) {
  const value = String(path || "");
  if (/^(?:https?:|wss?:|data:|blob:)/.test(value)) return value;
  return new URL(value.replace(/^\/+/, ""), APP_BASE_URL).toString();
}

function getWsUrl(path) {
  const url = new URL(String(path || "").replace(/^\/+/, ""), APP_BASE_URL);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  return url.toString();
}
