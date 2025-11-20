const apiBase = window.location.origin;
const transcriptEl = document.getElementById("transcript");
const textInput = document.getElementById("text-input");
const recordBtn = document.getElementById("record-btn");
const sendBtn = document.getElementById("send-btn");
const langSelect = document.getElementById("lang-select");
const voiceSelect = document.getElementById("voice-select");
const healthIndicator = document.getElementById("health-indicator");
const sessionIdEl = document.getElementById("session-id");
const streamToggle = document.getElementById("stream-toggle");
const streamStatus = document.getElementById("stream-status");
const timeline = document.getElementById("timeline");
const logEl = document.getElementById("log");
const metricASR = document.getElementById("metric-asr");
const metricLLM = document.getElementById("metric-llm");
const metricTTS = document.getElementById("metric-tts");

let mediaRecorder;
let chunks = [];
let isRecording = false;
let streaming = false;
let streamRecorder;
let streamSocket;
let streamChunks = [];

const sessionId = crypto.randomUUID();
sessionIdEl.textContent = sessionId.slice(0, 8);

function log(message) {
  const ts = new Date().toLocaleTimeString();
  logEl.textContent += `[${ts}] ${message}\n`;
  logEl.scrollTop = logEl.scrollHeight;
}

async function checkHealth() {
  healthIndicator.textContent = "Checking health…";
  try {
    const res = await fetch(`${apiBase}/health`);
    const data = await res.json();
    const allOk = data.asr === "ok" && data.llm === "ok" && data.tts === "ok";
    healthIndicator.className = `pill ${allOk ? "pill-ok" : "pill-warn"}`;
    healthIndicator.textContent = allOk ? "Online" : "Degraded";
    metricASR.textContent = data.asr;
    metricLLM.textContent = data.llm;
    metricTTS.textContent = data.tts;
    log("Health check completed");
  } catch (err) {
    healthIndicator.className = "pill pill-warn";
    healthIndicator.textContent = "Unavailable";
    log("Health check failed: " + err.message);
  }
}

function addMessage(role, text, lang = "auto") {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.innerHTML = `<div class="meta">${role === "user" ? "You" : "Agent"} · ${lang.toUpperCase()}</div>${text}`;
  transcriptEl.appendChild(div);
  transcriptEl.scrollTop = transcriptEl.scrollHeight;
}

async function blobToBase64(blob) {
  const arrayBuffer = await blob.arrayBuffer();
  const bytes = new Uint8Array(arrayBuffer);
  let binary = "";
  bytes.forEach((b) => (binary += String.fromCharCode(b)));
  return btoa(binary);
}

async function transcribeAndChat(audioBlob) {
  const audioBase64 = await blobToBase64(audioBlob);
  const lang = langSelect.value;
  log("Sending audio to /transcribe");
  const transcribeRes = await fetch(`${apiBase}/transcribe`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ audio_base64: audioBase64, lang, session_id: sessionId }),
  });
  const transcription = await transcribeRes.json();
  addMessage("user", transcription.text, transcription.lang || lang);
  textInput.value = transcription.text;
  await sendText(transcription.text, transcription.lang || lang);
}

async function sendText(text, detectedLang) {
  const lang = detectedLang || langSelect.value;
  if (!text.trim()) return;
  sendBtn.disabled = true;
  addMessage("user", text, lang);
  log("Sending text to /chat");
  const res = await fetch(`${apiBase}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, lang, session_id: sessionId }),
  });
  const data = await res.json();
  addMessage("bot", data.reply, data.lang);
  log(`LLM replied in ${data.lang}`);
  await speakText(data.reply, data.lang);
  sendBtn.disabled = false;
}

async function speakText(text, lang) {
  const voice = voiceSelect.value;
  log("Requesting TTS playback");
  const res = await fetch(`${apiBase}/tts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, lang, voice }),
  });
  const data = await res.json();
  metricTTS.textContent = `${data.duration_ms} ms`;
  const audioBytes = Uint8Array.from(atob(data.audio_base64), (c) => c.charCodeAt(0));
  const blob = new Blob([audioBytes.buffer], { type: "audio/wav" });
  const url = URL.createObjectURL(blob);
  const audio = new Audio(url);
  audio.play();
}

async function startRecording() {
  if (isRecording) return;
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);
  chunks = [];
  mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
  mediaRecorder.onstop = async () => {
    isRecording = false;
    recordBtn.textContent = "🎤 Hold to record";
    const blob = new Blob(chunks, { type: "audio/webm" });
    await transcribeAndChat(blob);
  };
  mediaRecorder.start();
  isRecording = true;
  recordBtn.textContent = "⏺️ Recording…";
}

function stopRecording() {
  if (mediaRecorder && isRecording) {
    mediaRecorder.stop();
  }
}

function addTimeline(text) {
  const row = document.createElement("div");
  row.className = "row";
  row.textContent = text;
  timeline.prepend(row);
  const rows = timeline.querySelectorAll(".row");
  if (rows.length > 20) rows[rows.length - 1].remove();
}

async function startStream() {
  if (streaming) return;
  const wsUrl = apiBase.replace("http", "ws") + "/stream";
  streamSocket = new WebSocket(wsUrl);
  streamStatus.textContent = "Connecting…";
  streamChunks = [];

  streamSocket.onopen = async () => {
    streamSocket.send(JSON.stringify({ session_id: sessionId, lang: langSelect.value }));
    addTimeline("🔌 Stream connected");
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    streamRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
    streamRecorder.ondataavailable = (e) => {
      if (streamSocket.readyState === WebSocket.OPEN && e.data.size > 0) {
        e.data.arrayBuffer().then((buf) => streamSocket.send(buf));
      }
    };
    streamRecorder.start(600);
    streaming = true;
    streamToggle.textContent = "Stop stream";
    streamStatus.textContent = "Streaming audio…";
  };

  streamSocket.onmessage = async (event) => {
    if (typeof event.data === "string") {
      const msg = JSON.parse(event.data);
      if (msg.type === "partial_text") {
        streamStatus.textContent = `ASR: ${msg.text}`;
      } else if (msg.type === "final_text") {
        addTimeline(`🗣️ ${msg.text}`);
      } else if (msg.type === "done") {
        streamStatus.textContent = "Awaiting new speech…";
        if (streamChunks.length) {
          const blob = new Blob(streamChunks, { type: "audio/wav" });
          const url = URL.createObjectURL(blob);
          const audio = new Audio(url);
          audio.play();
          streamChunks = [];
        }
      }
    } else {
      streamChunks.push(event.data);
    }
  };

  streamSocket.onclose = () => {
    stopStream();
  };

  streamSocket.onerror = (err) => {
    log("Stream error: " + err.message);
    stopStream();
  };
}

function stopStream() {
  if (streamRecorder && streamRecorder.state !== "inactive") {
    streamRecorder.stop();
  }
  if (streamSocket && streamSocket.readyState === WebSocket.OPEN) {
    streamSocket.close();
  }
  streaming = false;
  streamToggle.textContent = "Start stream";
  streamStatus.textContent = "Stream stopped";
}

recordBtn.addEventListener("mousedown", startRecording);
recordBtn.addEventListener("touchstart", (e) => {
  e.preventDefault();
  startRecording();
});
recordBtn.addEventListener("mouseup", stopRecording);
recordBtn.addEventListener("mouseleave", stopRecording);
recordBtn.addEventListener("touchend", stopRecording);

sendBtn.addEventListener("click", () => sendText(textInput.value));
textInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
    sendText(textInput.value);
  }
});

streamToggle.addEventListener("click", () => {
  if (streaming) stopStream();
  else startStream();
});

checkHealth();
