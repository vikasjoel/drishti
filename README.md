# Drishti (दृष्टि) — Spatial Intelligence for the Visually Impaired

> **Gemini Live Agent Challenge 2026 Submission**
>
> A real-time spatial awareness system that turns any phone camera into an intelligent navigation companion for blind users — powered by Gemini Live API.

**Live Demo**: [https://drishti-whn43ovjpq-uc.a.run.app](https://drishti-whn43ovjpq-uc.a.run.app)

---

## The Problem

2.2 billion people worldwide have vision impairment. Existing AI solutions describe scenes after the fact — "I see a chair." But a blind person walking needs **real-time spatial intelligence**: "Stop! Chair 1 step ahead — step 2 steps right to go around it."

The gap isn't seeing. It's **understanding space, time, and movement together**.

## What Drishti Does

Drishti is a voice companion that gives **turn-by-turn walking directions** to blind users through their phone camera and speaker. It doesn't just describe — it thinks, tracks, predicts, and guides.

**Key behaviors:**
- "Turn left in 2 steps, stairs going down"
- "Continue straight for 10 more steps"
- "Stop! Chair directly ahead, 1 step"
- Silence when the path is safe (silence = safety)
- Responds to questions in the user's language (Hindi, English, etc.)

## Architecture: The Conductor Model

Drishti uses a three-channel perception architecture where **Python decides WHEN Gemini speaks, not WHAT**.

**[View Interactive Architecture Diagram →](docs/architecture.html)** *(open locally or on GitHub Pages)*

```
Phone Camera (1 FPS) + Microphone + Sensors
    │
    │ WebSocket (JSON)
    ▼
┌─────────────────────────────────────────────────────────┐
│  Python Backend (FastAPI on Cloud Run)                   │
│                                                          │
│  Channel 1: Cloud Vision API ──► Object Detection        │
│    (every 3rd frame, 200ms)      Bounding boxes, labels  │
│                                                          │
│  Channel 2: Gemini generateContent ──► Scene Analysis    │
│    (event-driven, 2-3s)              Rich JSON: env,     │
│                                      path, navigation    │
│                                                          │
│  Channel 3: Gemini Live API ──► Voice I/O                │
│    (continuous)                   Speaks to user,         │
│                                  hears questions          │
│                                                          │
│  ┌─────────────────────────────────────────────────┐     │
│  │  World Model (the BRAIN)                         │     │
│  │  - Absorbs: sensors, CV, cognitive, speech       │     │
│  │  - Temporal Validator: is this still relevant?    │     │
│  │  - 9-priority nudge system (P1→P9)               │     │
│  │  - 4 dimensions: vigilance, urgency,             │     │
│  │    spatial_confidence, verbosity                  │     │
│  │  - Goal system (explicit + implicit)             │     │
│  │  - Decides: speak, stay silent, or inject context │     │
│  └─────────────────────────────────────────────────┘     │
│                                                          │
│  Output: nudge ──► Gemini Live speaks to user            │
│          OR silence (deliberate decision)                 │
└─────────────────────────────────────────────────────────┘
```

### Why Three Channels?

| Channel | Purpose | Latency | Cost |
|---------|---------|---------|------|
| **Cloud Vision** | Fast object detection, emergency tripwire (vehicles, large obstacles) | 200ms | Low |
| **Gemini generateContent** | Deep scene understanding, navigation actions, environment classification | 2-3s | Medium |
| **Gemini Live** | Voice conversation, natural speech output, user questions | Real-time | Continuous |

### The Temporal Validation Innovation (v4.2)

The core insight: **perception results are about the PAST**. By the time Cloud Vision detects a chair (200ms) or Gemini analyzes a scene (3s), the user has **moved**. They may have already walked past the obstacle, or turned away from it.

Every frame is **stamped** with a sensor snapshot (heading, step count, speed). Before any alert fires, the Temporal Validator checks:

- Has the user **turned away** (heading changed >45 degrees)? → **Drop it** (stale)
- Has the user **walked past** it (distance moved > obstacle distance)? → **Drop it** (stale)
- Is the obstacle **less than 1.5m ahead**? → **URGENT alert** (imminent)
- Otherwise → **Normal alert** (valid)

This eliminates the false-positive problem that plagues all camera-based navigation systems.

## Gemini Live API Features Used

| Feature | How Drishti Uses It |
|---------|-------------------|
| **Native audio I/O** | Natural voice conversation — user asks questions, Drishti responds |
| **Video frame input** | 1 FPS camera stream for continuous spatial awareness |
| **Affective dialog** | Adapts tone — calm for safe paths, urgent for dangers |
| **Proactive audio** | System-initiated speech via `send_client_content(turn_complete=True)` |
| **Input/output transcription** | Speech-to-text for goal extraction and UI display |
| **Context window compression** | Long sessions without losing spatial state |
| **generateContent** | Separate cognitive perception channel for deep scene analysis |
| **Multi-language** | Responds in user's language (tested with Hindi + English) |

## Tech Stack

- **Gemini Live API** — `gemini-2.5-flash-native-audio-preview-12-2025` for voice
- **Gemini generateContent** — `gemini-2.5-flash` for cognitive scene analysis
- **Google Cloud Vision API** — Fast object detection and OCR
- **Python / FastAPI** — Backend server with WebSocket
- **Google Cloud Run** — Serverless deployment
- **HTML/JS PWA** — Frontend (works on any phone browser, no app install)

## Project Structure

```
drishti/
├── backend/
│   ├── main.py                 # FastAPI WebSocket server, v4.2 pipeline
│   ├── gemini_session.py       # Gemini Live API session manager
│   ├── cognitive_perception.py # Gemini generateContent scene analysis
│   ├── cognitive_trigger.py    # Event-driven cognitive call decisions
│   ├── cloud_vision.py         # Google Cloud Vision API client
│   ├── world_model.py          # The BRAIN — 9-priority nudge system
│   ├── temporal_validator.py   # v4.2 — validates perception vs movement
│   ├── sensor_processor.py     # Phone sensor processing + snapshots
│   ├── goal_system.py          # Explicit + implicit goal management
│   ├── implicit_goals.py       # Context-derived navigation goals
│   ├── speech_processing.py    # Speech event detection + interpretation
│   ├── plugins.py              # Plugin configs (blind_nav, baby, elderly, security)
│   ├── system_prompt.py        # Gemini Live voice prompt
│   ├── frame_quality.py        # Frame quality gate
│   └── logger.py               # Structured JSON logging + session stats
├── frontend/
│   ├── index.html              # Demo-ready UI with brain dashboard
│   ├── app.js                  # Camera, mic, WebSocket, brain panel rendering
│   ├── sensors.js              # Phone sensor capture + step detection
│   ├── style.css
│   └── manifest.json           # PWA manifest
├── docs/
│   ├── ARCHITECTURE.md         # Detailed architecture documentation
│   └── ...
├── Dockerfile                  # Cloud Run container
├── deploy.sh                   # One-command Cloud Run deployment
├── requirements.txt
└── .env.example
```

## Reproducible Testing — Step by Step

### Option A: Try the Live Demo (Easiest)

1. **Open on your phone**: Visit [https://drishti-whn43ovjpq-uc.a.run.app](https://drishti-whn43ovjpq-uc.a.run.app) on your phone's browser (Chrome on Android or Safari on iOS)
2. **Grant permissions**: Tap "Allow" for camera, microphone, and motion sensors when prompted
3. **Select mode**: Choose "Blind Navigation" from the mode selector (default)
4. **Tap Start**: The camera feed appears full-screen with a brain dashboard below
5. **Walk around**: Point your phone camera forward as if you're walking. Hold it at chest height, rear camera facing ahead
6. **Listen**: Drishti will speak turn-by-turn directions through your phone speaker:
   - "Continue straight" when path is clear
   - "Turn left in 2 steps" at corridors
   - "Stop! Chair ahead" for obstacles
   - Silence means the path is safe — this is intentional
7. **Ask questions**: Speak naturally — "What's in front of me?" or "Where are the stairs?" — Drishti responds conversationally
8. **Watch the brain panel**: Scroll down to see real-time system intelligence (environment type, urgency bars, path status, temporal validation)

**Best test scenarios:**
- Walk through a hallway with turns
- Approach furniture or obstacles
- Walk up/down stairs
- Walk toward a person

> **Note**: Use headphones/earbuds for the best experience — the phone speaker works but earbuds prevent echo from the microphone picking up Drishti's voice.

### Option B: Run Locally

```bash
# 1. Clone
git clone https://github.com/vikasjoel/drishti.git
cd drishti

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API keys
cp .env.example .env
# Edit .env and add:
#   GOOGLE_API_KEY=your_gemini_api_key (paid tier recommended)
#   GOOGLE_CLOUD_PROJECT=your_gcp_project_id

# 4. Set up Cloud Vision credentials (for object detection)
#   Download a GCP service account JSON with Vision API enabled
#   Set: GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# 5. Run the server
uvicorn backend.main:app --host 0.0.0.0 --port 8080

# 6. Open on your phone (must be on the same WiFi network)
#   Find your computer's local IP: ifconfig | grep inet
#   On phone browser, go to: http://<your-computer-ip>:8080
#   IMPORTANT: Camera/mic require HTTPS in production,
#   but localhost/local-IP works over HTTP for testing
```

### Option C: Deploy to Cloud Run

```bash
# Set environment variables in deploy.sh, then:
chmod +x deploy.sh
./deploy.sh
```

### What to Expect During Testing

| Time | What Happens |
|------|-------------|
| 0-3s | Connection establishes, camera feed appears |
| 3-5s | First cognitive analysis runs, Drishti greets you |
| 5-10s | Environment detected (room, corridor, stairs), first navigation direction |
| Ongoing | Directions every 3-6s when scene changes; silence when path is safe |
| On obstacle | "Stop! [object] ahead" with avoidance directions |
| On question | Natural voice response about the scene |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Gemini API key (paid tier recommended for rate limits) |
| `GOOGLE_CLOUD_PROJECT` | Yes | GCP project ID (for Cloud Vision) |
| `GOOGLE_APPLICATION_CREDENTIALS` | For Cloud Vision | Path to service account JSON |
| `DEFAULT_PLUGIN` | No | Plugin to use (default: `blind_navigation`) |
| `COGNITIVE_MODEL` | No | Model for generateContent (default: `gemini-2.5-flash`) |
| `LOG_LEVEL` | No | Logging level (default: `INFO`) |

## Plugin System

Drishti is a **universal spatial intelligence framework**. Swap a plugin config to change the entire behavior:

| Plugin | Use Case | Behavior |
|--------|----------|----------|
| `blind_navigation` | Visually impaired user walking | Turn-by-turn directions, obstacle alerts, silence = safe |
| `baby_monitor` | Stationary camera watching baby | Alert on unusual movement, boundary approach |
| `elderly_care` | Stationary camera for elderly | Fall detection, prolonged stillness alerts |
| `security` | Stationary security camera | Person detection, zone intrusion alerts |

## How the World Model Decides

The 9-priority nudge system ensures the most important information gets through:

| Priority | Trigger | Example |
|----------|---------|---------|
| P1 (1.0) | Vehicle emergency | "Stop! Car ahead!" |
| P2 (0.9) | Safety alert / imminent obstacle | "Stop! Chair 1 step ahead!" |
| P3 (0.8) | Fast-approaching object | "Person approaching, 10 o'clock" |
| P4 (0.7) | Environment transition | "You've reached the stairs. Surface: stairs_down." |
| P5 (0.65) | Goal match | "Found the elevator — ahead on your right." |
| P6 (0.6) | New obstacle | "Table about 3 steps ahead." |
| P7 (0.5) | Navigation action / orientation | "Turn left in 2 steps." |
| P8 (0.4) | Proactive info | "Path is clear. Hallway ahead." |
| P9 (0.3) | Memory augment (silent) | Context refresh for Gemini Live |

## Demo UI

The frontend shows a **live brain dashboard** that demonstrates the system's intelligence:

- **Camera feed** with speech overlay ("Drishti says: Turn left in 2 steps")
- **Environment badge** — changes from ROOM → STAIRS → CORRIDOR as user walks
- **4 dimension bars** — Alertness, Urgency, Confidence, Voice (animated in real-time)
- **Path status** — Clear / Blocked with obstacle name
- **Temporal validation** — Shows "IMMINENT 0.8m" (pulsing red) or "Dropped: user turned 62 degrees" (gray)
- **"SAFE — PATH CLEAR"** indicator appears when the system is intentionally silent

## Performance (Rev 19)

| Metric | Value |
|--------|-------|
| Cognitive latency (generateContent) | 1.8–4.0s avg |
| Cloud Vision latency | 130–300ms |
| Gemini Live connection | ~100ms |
| Frames processed | 1 FPS |
| Nudges per 2-min session | ~14 (10 proactive, 4 silent) |
| Temporal stale drops | ~30% of perceptions correctly filtered |
| End-to-end (see obstacle → speak) | 2-4 seconds |

## Team

Built by Vikas Joel for the Gemini Live Agent Challenge 2026.

## License

MIT
