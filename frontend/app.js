/**
 * Drishti v4.2 frontend — demo-ready UI.
 * Camera capture, mic streaming, audio playback, WebSocket bridge, brain panel rendering.
 *
 * Protocol (JSON over WebSocket):
 *   Client -> Server:
 *     { type: "audio", data: "<base64 PCM 16kHz mono>" }
 *     { type: "image", data: "<base64 JPEG>", frame_change: 0.0-1.0 }
 *     { type: "sensors", ... }
 *     { type: "text",  text: "...", end_of_turn: true }
 *     { type: "ping", ts: <number> }
 *
 *   Server -> Client:
 *     { type: "audio", data: "<base64 PCM 24kHz mono>" }
 *     { type: "input_transcription",  text: "..." }
 *     { type: "output_transcription", text: "..." }
 *     { type: "turn_complete" }
 *     { type: "brain_state", dimensions: {...}, ... }
 */

const FRAME_INTERVAL_MS = 1000;
const AUDIO_SAMPLE_RATE_IN = 16000;
const AUDIO_SAMPLE_RATE_OUT = 24000;
const AUDIO_CHUNK_SIZE = 4096;

// DOM — start screen
const startScreen = document.getElementById("start-screen");
const startBtn = document.getElementById("start-btn");
const startStatus = document.getElementById("start-status");
const pluginSelect = document.getElementById("plugin-select");

// DOM — camera
const cameraSection = document.getElementById("camera-section");
const videoEl = document.getElementById("video");
const canvasEl = document.getElementById("canvas");

// DOM — overlays
const statusDot = document.getElementById("status-dot");
const statusText = document.getElementById("status-text");
const envBadge = document.getElementById("env-badge");
const silentIndicator = document.getElementById("silent-indicator");
const speechOverlay = document.getElementById("speech-overlay");
const speechText = document.getElementById("speech-text");

// DOM — brain panel
const brainPanel = document.getElementById("brain-panel");
const pathStatus = document.getElementById("path-status");
const goalStatus = document.getElementById("goal-status");
const temporalDot = document.getElementById("temporal-dot");
const temporalText = document.getElementById("temporal-text");
const temporalAge = document.getElementById("temporal-age");

// State
let ws = null;
let mediaStream = null;
let audioContext = null;
let audioWorkletNode = null;
let frameTimer = null;
let pingTimer = null;
let playbackCtx = null;
let nextPlayTime = 0;
let running = false;
let sensors = null;
let sensorsGranted = false;

// Speech accumulator
let currentUtterance = "";
let speechFadeTimer = null;
let silentTimer = null;
let lastSpeechTime = 0;

// ==========================================
// STATUS HELPERS
// ==========================================

function setStatus(text, state) {
    statusText.textContent = text;
    statusDot.className = state || "";
}

function setStartStatus(text) {
    startStatus.textContent = text;
}

// ==========================================
// CAMERA
// ==========================================

async function startCamera() {
    mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment", width: { ideal: 640 }, height: { ideal: 480 } },
        audio: true,
    });
    videoEl.srcObject = mediaStream;
}

function captureFrame() {
    if (!mediaStream || !ws || ws.readyState !== WebSocket.OPEN) return;

    const track = mediaStream.getVideoTracks()[0];
    if (!track) return;

    canvasEl.width = 640;
    canvasEl.height = 480;
    const ctx = canvasEl.getContext("2d");
    ctx.drawImage(videoEl, 0, 0, 640, 480);

    const frameChange = sensors ? sensors.computeFrameChange(videoEl) : 0;

    canvasEl.toBlob((blob) => {
        if (!blob || !ws || ws.readyState !== WebSocket.OPEN) return;
        const reader = new FileReader();
        reader.onloadend = () => {
            const b64 = reader.result.split(",")[1];
            ws.send(JSON.stringify({
                type: "image",
                data: b64,
                frame_change: Math.round(frameChange * 100) / 100,
            }));
        };
        reader.readAsDataURL(blob);
    }, "image/jpeg", 0.85);
}

// ==========================================
// MICROPHONE (PCM 16kHz)
// ==========================================

async function startMicrophone() {
    audioContext = new AudioContext({ sampleRate: AUDIO_SAMPLE_RATE_IN });

    const workletCode = `
        class PcmProcessor extends AudioWorkletProcessor {
            process(inputs) {
                const input = inputs[0];
                if (input && input[0]) {
                    this.port.postMessage(input[0]);
                }
                return true;
            }
        }
        registerProcessor("pcm-processor", PcmProcessor);
    `;
    const blob = new Blob([workletCode], { type: "application/javascript" });
    const url = URL.createObjectURL(blob);
    await audioContext.audioWorklet.addModule(url);
    URL.revokeObjectURL(url);

    const source = audioContext.createMediaStreamSource(mediaStream);
    audioWorkletNode = new AudioWorkletNode(audioContext, "pcm-processor");

    let buffer = new Float32Array(0);

    audioWorkletNode.port.onmessage = (e) => {
        if (!ws || ws.readyState !== WebSocket.OPEN) return;

        const incoming = e.data;
        const merged = new Float32Array(buffer.length + incoming.length);
        merged.set(buffer);
        merged.set(incoming, buffer.length);
        buffer = merged;

        while (buffer.length >= AUDIO_CHUNK_SIZE) {
            const chunk = buffer.slice(0, AUDIO_CHUNK_SIZE);
            buffer = buffer.slice(AUDIO_CHUNK_SIZE);

            const pcm = new Int16Array(chunk.length);
            for (let i = 0; i < chunk.length; i++) {
                const s = Math.max(-1, Math.min(1, chunk[i]));
                pcm[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
            }

            const b64 = arrayBufferToBase64(pcm.buffer);
            ws.send(JSON.stringify({ type: "audio", data: b64 }));
        }
    };

    source.connect(audioWorkletNode);
    audioWorkletNode.connect(audioContext.destination);
}

// ==========================================
// AUDIO PLAYBACK (PCM 24kHz)
// ==========================================

function enqueueAudio(base64Pcm) {
    if (!playbackCtx) {
        playbackCtx = new AudioContext({ sampleRate: AUDIO_SAMPLE_RATE_OUT });
        nextPlayTime = 0;
    }

    const raw = base64ToArrayBuffer(base64Pcm);
    const int16 = new Int16Array(raw);
    const float32 = new Float32Array(int16.length);
    for (let i = 0; i < int16.length; i++) {
        float32[i] = int16[i] / 0x8000;
    }

    const buffer = playbackCtx.createBuffer(1, float32.length, AUDIO_SAMPLE_RATE_OUT);
    buffer.getChannelData(0).set(float32);

    const source = playbackCtx.createBufferSource();
    source.buffer = buffer;
    source.connect(playbackCtx.destination);

    const now = playbackCtx.currentTime;
    const startAt = Math.max(now, nextPlayTime);
    source.start(startAt);
    nextPlayTime = startAt + buffer.duration;
}

// ==========================================
// WEBSOCKET
// ==========================================

function connectWebSocket() {
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    const plugin = pluginSelect.value;
    const url = `${proto}//${location.host}/ws?plugin=${plugin}`;

    ws = new WebSocket(url);

    ws.onopen = () => {
        setStatus("Connected", "");
        frameTimer = setInterval(captureFrame, FRAME_INTERVAL_MS);
        sensors = new SensorStream(ws);
        pingTimer = setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: "ping", ts: performance.now() }));
            }
        }, 5000);

        // Show main UI
        startScreen.classList.add("hidden");
        cameraSection.style.display = "";
        brainPanel.style.display = "";
    };

    ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);

        if (msg.type === "audio") {
            enqueueAudio(msg.data);
        } else if (msg.type === "input_transcription") {
            // User speech — show briefly
            showSpeechUser(msg.text);
        } else if (msg.type === "output_transcription") {
            // Drishti speech — accumulate and show
            if (msg.text && msg.text.trim()) {
                currentUtterance += msg.text;
                showSpeech(currentUtterance);
            }
        } else if (msg.type === "turn_complete") {
            currentUtterance = "";
        } else if (msg.type === "brain_state") {
            renderBrainState(msg);
        } else if (msg.type === "pong") {
            const rtt = performance.now() - msg.client_ts;
            statusText.textContent = Math.round(rtt) + "ms";
        }
    };

    ws.onclose = () => {
        setStatus("Disconnected", "error");
        cleanup();
    };

    ws.onerror = (err) => {
        console.error("WebSocket error:", err);
        setStatus("Error", "error");
    };
}

// ==========================================
// BRAIN PANEL RENDERING
// ==========================================

const ENV_MAP = {
    'indoor_room': 'ROOM',
    'indoor_corridor': 'CORRIDOR',
    'indoor_stairs': 'STAIRS',
    'outdoor_path': 'OUTDOORS',
    'outdoor_crossing': 'CROSSING',
    'outdoor_open': 'OPEN AREA',
    'vehicle': 'VEHICLE',
    'elevator': 'ELEVATOR',
    'unknown': '\u2014',
};

function renderBrainState(state) {
    // Dimension bars
    const dims = state.dimensions || {};
    updateDim("vigilance", dims.vigilance || 0);
    updateDim("urgency", dims.urgency || 0);
    updateDim("confidence", dims.spatial_confidence || 0);
    updateDim("verbosity", dims.verbosity || 0);

    // Environment badge
    const envType = state.environment || "unknown";
    envBadge.textContent = ENV_MAP[envType] || envType.toUpperCase();

    if (envType === "indoor_stairs" || envType === "outdoor_crossing") {
        envBadge.style.background = "rgba(239, 68, 68, 0.2)";
        envBadge.style.borderColor = "rgba(239, 68, 68, 0.3)";
        envBadge.style.color = "#ef4444";
    } else if (envType.startsWith("outdoor")) {
        envBadge.style.background = "rgba(20, 184, 166, 0.2)";
        envBadge.style.borderColor = "rgba(20, 184, 166, 0.3)";
        envBadge.style.color = "#14b8a6";
    } else {
        envBadge.style.background = "rgba(108, 99, 255, 0.2)";
        envBadge.style.borderColor = "rgba(108, 99, 255, 0.3)";
        envBadge.style.color = "#6c63ff";
    }

    // Path status
    if (state.path_clear === false) {
        const blocker = state.path_blocked_by || "obstacle";
        pathStatus.textContent = "\u26A0 " + blocker;
        pathStatus.className = "info-value path-blocked";
    } else {
        pathStatus.textContent = "\u2713 Clear";
        pathStatus.className = "info-value path-clear";
    }

    // Goal
    const goals = state.active_goals || [];
    const explicit = goals.find(g => g.type === "explicit");
    if (explicit && explicit.target) {
        goalStatus.textContent = "\uD83C\uDFAF " + explicit.target;
        goalStatus.className = "info-value has-goal";
    } else {
        goalStatus.textContent = "\u2014";
        goalStatus.className = "info-value";
    }

    // Temporal validation
    const v = state.last_validation || {};
    if (v.status === "stale") {
        temporalDot.className = "stale";
        temporalText.textContent = "Dropped: " + (v.reason || "stale").substring(0, 50);
        temporalText.style.color = "var(--text-muted)";
    } else if (v.status === "imminent") {
        temporalDot.className = "imminent";
        const dist = v.remaining ? v.remaining.toFixed(1) + "m" : "";
        temporalText.textContent = "IMMINENT " + dist;
        temporalText.style.color = "var(--red)";
    } else if (v.status === "valid") {
        temporalDot.className = "valid";
        const dist = v.remaining ? v.remaining.toFixed(1) + "m ahead" : "";
        temporalText.textContent = dist || "Valid perception";
        temporalText.style.color = "var(--green)";
    } else {
        temporalDot.className = "idle";
        temporalText.textContent = "Monitoring...";
        temporalText.style.color = "var(--text-muted)";
    }

    // Flash brain panel on nudge
    if (state.last_nudge && state.last_nudge !== renderBrainState._prevNudge) {
        brainPanel.classList.remove("nudge-fired");
        void brainPanel.offsetWidth;
        brainPanel.classList.add("nudge-fired");
        renderBrainState._prevNudge = state.last_nudge;
    }
}
renderBrainState._prevNudge = "";

function updateDim(name, value) {
    const bar = document.getElementById("bar-" + name);
    const val = document.getElementById("val-" + name);
    if (bar) bar.style.width = (value * 100) + "%";
    if (val) val.textContent = value.toFixed(1);
}

// ==========================================
// SPEECH OVERLAY
// ==========================================

function showSpeech(text) {
    speechText.textContent = text;
    speechOverlay.querySelector(".label").textContent = "Drishti says";
    speechOverlay.classList.add("visible");
    silentIndicator.classList.remove("visible");
    lastSpeechTime = Date.now();

    if (speechFadeTimer) clearTimeout(speechFadeTimer);
    speechFadeTimer = setTimeout(() => {
        speechOverlay.classList.remove("visible");
    }, 5000);

    if (silentTimer) clearTimeout(silentTimer);
    silentTimer = setTimeout(() => {
        silentIndicator.classList.add("visible");
    }, 8000);
}

function showSpeechUser(text) {
    speechText.textContent = text;
    speechOverlay.querySelector(".label").textContent = "You said";
    speechOverlay.classList.add("visible");

    if (speechFadeTimer) clearTimeout(speechFadeTimer);
    speechFadeTimer = setTimeout(() => {
        speechOverlay.classList.remove("visible");
    }, 3000);
}

// ==========================================
// LIFECYCLE
// ==========================================

function cleanup() {
    if (frameTimer) { clearInterval(frameTimer); frameTimer = null; }
    if (pingTimer) { clearInterval(pingTimer); pingTimer = null; }
    if (sensors) { sensors.destroy(); sensors = null; }
    if (audioWorkletNode) { audioWorkletNode.disconnect(); audioWorkletNode = null; }
    if (audioContext) { audioContext.close(); audioContext = null; }
    nextPlayTime = 0;
}

async function requestSensorPermissions() {
    if (typeof DeviceMotionEvent !== "undefined" &&
        typeof DeviceMotionEvent.requestPermission === "function") {
        try {
            setStartStatus("Requesting sensor access...");
            const motionPerm = await DeviceMotionEvent.requestPermission();
            const orientPerm = await DeviceOrientationEvent.requestPermission();
            sensorsGranted = (motionPerm === "granted" && orientPerm === "granted");
        } catch (e) {
            console.warn("Sensor permission error (iOS):", e);
            sensorsGranted = false;
        }
    } else if ("DeviceMotionEvent" in window) {
        sensorsGranted = true;
    } else {
        sensorsGranted = false;
    }
}

async function start() {
    try {
        startBtn.disabled = true;
        setStartStatus("Starting...");

        await requestSensorPermissions();
        await startCamera();
        await startMicrophone();
        connectWebSocket();

        running = true;
    } catch (err) {
        console.error("Start failed:", err);
        setStartStatus("Error: " + err.message);
        startBtn.disabled = false;
    }
}

function stop() {
    running = false;
    if (ws) { ws.close(); ws = null; }
    cleanup();
    if (mediaStream) {
        mediaStream.getTracks().forEach((t) => t.stop());
        mediaStream = null;
    }
    videoEl.srcObject = null;

    // Show start screen again
    cameraSection.style.display = "none";
    brainPanel.style.display = "none";
    startScreen.classList.remove("hidden");
    startBtn.disabled = false;
    setStartStatus("");
}

startBtn.addEventListener("click", () => {
    if (running) {
        stop();
    } else {
        start();
    }
});

pluginSelect.addEventListener("mousedown", (e) => {
    if (running) e.preventDefault();
});

// ==========================================
// UTILITIES
// ==========================================

function arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = "";
    for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
}

function base64ToArrayBuffer(base64) {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
}
