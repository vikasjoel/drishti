# CLAUDE.md — Drishti (दृष्टि) v3
## Build Instructions for Claude Code
## DEADLINE: March 16, 2026, 5:00 PM PT (3 days)

---

## WHAT EXISTS (Do NOT Rewrite)

The existing codebase has a WORKING Gemini Live session with camera+mic+audio streaming. These are PROVEN:

### Working Backend (`backend/`)
- `main.py` — FastAPI WebSocket server. Receives audio+frames from browser, forwards to Gemini Live, returns audio responses. KEEP and EXTEND.
- `gemini_session.py` — Gemini Live API session manager. Config:
  - Model: `gemini-live-2.5-flash-native-audio` (or `gemini-2.5-flash-native-audio-preview-12-2025`)
  - `enable_affective_dialog=True`, `proactivity={"proactive_audio": True}`
  - `input_audio_transcription={}`, `output_audio_transcription={}`
  - `context_window_compression` with `sliding_window`, `session_resumption`
  - `thinking_config` with `thinking_budget=0` (CRITICAL: >0 crashes with function calling + audio)
  - `media_resolution=LOW`
  - `send_realtime_input` for audio and frames (WORKS)
  - `send_client_content` with `turn_complete=True` for proactive speech injection (PROVEN WORKING)
- `system_prompt.py` — Spatial system prompt (needs v3 update)
- `domain_plugins.py` — Plugin configs: blind_navigation, security_monitor, elderly_care, universal

### Working Frontend (`frontend/`)
- `index.html` + `app.js` + `style.css` — PWA with getUserMedia camera+mic, WebSocket to backend, PCM audio playback, mode selector

### Proven Technical Facts
1. Proactive speech works via `send_client_content(turns=..., turn_complete=True)`
2. Function calling limited to ONE call per Live session (1/6 hit rate) — mechanical limit of native audio model. Use one-shot bootstrap only.
3. `thinking_budget` MUST be 0 with function calling + audio
4. Video frames via `send_realtime_input` are PASSIVE context — they never trigger speech. Only `send_client_content` with `turn_complete=True` or user voice triggers speech.

---

## v3 ARCHITECTURE — What to Build

### Three-Channel Perception
```
Camera Frame (every 1-2s)
  ├→ Channel 1: Cloud Vision API (REACTIVE, every frame)
  │   Returns: bounding boxes, labels, OCR. Fast (200-500ms), structured.
  ├→ Channel 2: Gemini generateContent (COGNITIVE, every 5-10s)  
  │   Returns: scene understanding JSON. Slower (1-3s), deeper.
  └→ Channel 3: Gemini Live API (VOICE ONLY, continuous)
      Receives alert injections from brain. Handles user conversation.
```

### The Brain Pipeline
```
Cloud Vision bboxes → SORT Tracker (Kalman+Hungarian) → persistent object IDs
  → Brain computes: size trends → urgency score
  → Decision: urgency > threshold? → inject alert into Gemini Live
  → Gemini Live speaks: "Person, 10 o'clock, close, approaching"
```

---

## FILES TO CREATE/MODIFY

### NEW Files:
- `backend/cloud_vision.py` — Cloud Vision API client (bboxes, labels, OCR)
- `backend/sort_tracker.py` — SORT tracker: KalmanBoxTracker + SORTTracker with Hungarian assignment via `scipy.optimize.linear_sum_assignment`
- `backend/brain.py` — World model + urgency computation + decision engine + self-correction detection
- `backend/cognitive_loop.py` — Gemini generateContent for periodic scene understanding (OPTIONAL for demo)
- `Dockerfile` — For Cloud Run deployment
- `deploy.sh` — Automated deployment script (+0.2 bonus points)

### MODIFY:
- `backend/main.py` — Integrate cloud_vision + tracker + brain into frame processing loop
- `backend/system_prompt.py` — v3 prompt (Gemini Live = voice only, brain does thinking)
- `frontend/index.html` — Add split-screen right panel showing brain state
- `frontend/app.js` — Handle `brain_state` WebSocket messages, render tracks/urgency/predictions
- `requirements.txt` — Add: `google-cloud-vision>=3.0.0`, `numpy>=1.24.0`, `scipy>=1.10.0`

---

## BUILD ORDER (Priority for 3-day deadline)

### Day 1: Core Pipeline
1. `backend/cloud_vision.py` — Send JPEG, get bboxes+labels+text back
2. `backend/sort_tracker.py` — Kalman filter prediction + Hungarian assignment
3. `backend/brain.py` — Urgency from size trends, alert formatting, self-correction
4. Update `backend/main.py` — Wire: frame → Cloud Vision → tracker → brain → alert injection
5. Test: Point camera at room, see alerts when person approaches

### Day 2: Demo Features + Polish
6. Update frontend with split-screen brain panel (tracks, urgency meter, predictions)
7. Implement predict-verify display (predicted size vs actual size, green ✓ / red ✗)
8. Self-correction moment (object stationary for 10+ frames → reclassify)
9. Mode switch (Navigator ↔ Security — different system prompt addendum)
10. Deploy to Cloud Run + Firestore for one cross-session demo
11. Record 4-minute demo video

### Day 3: Submission + Bonus
12. Architecture diagram
13. Devpost description + README
14. Proof of Cloud deployment (screen recording)
15. Upload demo to YouTube
16. Blog post on Medium (+0.6 bonus points)
17. Submit on Devpost before 5 PM PT

---

## KEY CODE: Cloud Vision Integration

```python
# backend/cloud_vision.py
from google.cloud import vision

class CloudVisionClient:
    def __init__(self):
        self.client = vision.ImageAnnotatorClient()
    
    async def analyze_frame(self, jpeg_bytes: bytes) -> dict:
        image = vision.Image(content=jpeg_bytes)
        objects_response = self.client.object_localization(image=image)
        text_response = self.client.text_detection(image=image)
        
        objects = []
        for obj in objects_response.localized_object_annotations:
            verts = obj.bounding_poly.normalized_vertices
            x_min, y_min = verts[0].x, verts[0].y
            x_max, y_max = verts[2].x, verts[2].y
            w, h = x_max - x_min, y_max - y_min
            objects.append({
                "label": obj.name.lower(),
                "confidence": obj.score,
                "bbox": {"x": x_min, "y": y_min, "w": w, "h": h},
                "center_x": (x_min + x_max) / 2,
                "center_y": (y_min + y_max) / 2,
                "area_pct": w * h * 100,
            })
        
        texts = [t.description for t in text_response.text_annotations[1:]] if text_response.text_annotations else []
        return {"objects": objects, "text": texts}
```

## KEY CODE: SORT Tracker

```python
# backend/sort_tracker.py
import numpy as np
from scipy.optimize import linear_sum_assignment

class KalmanBoxTracker:
    count = 0
    def __init__(self, bbox):
        # bbox = [center_x, center_y, area_pct, aspect_ratio]
        self.id = KalmanBoxTracker.count; KalmanBoxTracker.count += 1
        self.state = np.array([bbox[0], bbox[1], bbox[2], bbox[3], 0, 0, 0], dtype=float)
        self.hits = 1; self.age = 0; self.time_since_update = 0
        self.size_history = [bbox[2]]; self.label = "unknown"
    
    def predict(self):
        self.state[:3] += self.state[4:7]
        self.age += 1; self.time_since_update += 1
        return self.state[:4]
    
    def update(self, bbox):
        alpha = 0.4
        for i in range(3):
            self.state[4+i] = alpha * (bbox[i] - self.state[i]) + (1-alpha) * self.state[4+i]
            self.state[i] = bbox[i]
        self.state[3] = bbox[3]
        self.hits += 1; self.time_since_update = 0
        self.size_history.append(bbox[2])
        if len(self.size_history) > 30: self.size_history = self.size_history[-30:]
    
    @property
    def size_trend(self):
        if len(self.size_history) < 3: return 0.0
        r = self.size_history[-5:]
        return (r[-1] - r[0]) / max(len(r)-1, 1) if len(r) >= 2 else 0.0
    
    @property
    def clock_position(self):
        x = self.state[0]
        for threshold, name in [(0.15,"9"),(0.3,"10"),(0.45,"11"),(0.55,"12"),(0.7,"1"),(0.85,"2")]:
            if x < threshold: return f"{name} o'clock"
        return "3 o'clock"

class SORTTracker:
    def __init__(self, max_age=10):
        self.max_age = max_age; self.trackers = []
    
    def update(self, detections):
        measurements = [[d["center_x"], d["center_y"], d["area_pct"],
                         d["bbox"]["w"]/max(d["bbox"]["h"],0.001)] for d in detections]
        
        predictions = [t.predict() for t in self.trackers]
        
        if predictions and measurements:
            cost = np.zeros((len(predictions), len(measurements)))
            for i, p in enumerate(predictions):
                for j, m in enumerate(measurements):
                    cost[i,j] = np.sqrt((p[0]-m[0])**2+(p[1]-m[1])**2) + abs(p[2]-m[2])/max(p[2],m[2],0.01)*0.5
            ri, ci = linear_sum_assignment(cost)
            matched_t, matched_d = set(), set()
            for r, c in zip(ri, ci):
                if cost[r,c] < 0.5:
                    self.trackers[r].update(measurements[c])
                    self.trackers[r].label = detections[c]["label"]
                    matched_t.add(r); matched_d.add(c)
            for j in range(len(measurements)):
                if j not in matched_d:
                    t = KalmanBoxTracker(measurements[j]); t.label = detections[j]["label"]
                    self.trackers.append(t)
        elif measurements:
            for j, m in enumerate(measurements):
                t = KalmanBoxTracker(m); t.label = detections[j]["label"]
                self.trackers.append(t)
        
        self.trackers = [t for t in self.trackers if t.time_since_update <= self.max_age]
        
        return [{"id": f"obj_{t.id}", "label": t.label, "clock": t.clock_position,
                 "approaching": t.size_trend > 0.3, "size_trend": round(t.size_trend,2),
                 "area_pct": round(t.state[2],1), "center_x": round(t.state[0],3),
                 "aspect_ratio": round(t.state[3],2), "frames_tracked": t.hits}
                for t in self.trackers if t.hits >= 2 or t.time_since_update == 0]
```

## KEY CODE: Brain Decision Engine

```python
# backend/brain.py
import time

class Brain:
    def __init__(self, alert_threshold=0.5):
        self.alert_threshold = alert_threshold
        self.frame_count = 0; self.last_alert_time = 0; self.last_alert_text = ""
        self.predictions = {}; self.corrections = []
    
    def process(self, tracks, texts, labels):
        self.frame_count += 1; now = time.time()
        
        # Compute urgency per track
        max_urgency, best = 0.0, None
        for t in tracks:
            u = (0.4 if t["approaching"] else 0) + min(0.3, abs(t["size_trend"])*0.1)
            if t.get("area_pct",0) > 10: u += 0.2
            elif t.get("area_pct",0) > 5: u += 0.1
            if t["label"] in ("person","man","woman","child"): u += 0.1
            u = min(1.0, u)
            if u > max_urgency: max_urgency, best = u, t
        
        # Self-correction check
        correction = self._check_corrections(tracks)
        if correction:
            return {"action":"correction","text":correction,"urgency":0.3,"tracks":tracks}
        
        # Generate predictions for verify step
        self.predictions = {t["id"]: {"predicted_area": t["area_pct"]+t["size_trend"],
                                       "will_approach": t["approaching"]} for t in tracks}
        
        # Alert decision
        if best and max_urgency > self.alert_threshold and (now - self.last_alert_time) > 3.0:
            text = f"{best['label'].capitalize()}, {best['clock']}, approaching"
            if text != self.last_alert_text:
                self.last_alert_time = now; self.last_alert_text = text
                return {"action":"alert","text":text,"urgency":max_urgency,"tracks":tracks}
        
        return {"action":"silent","text":"","urgency":max_urgency,"tracks":tracks}
    
    def _check_corrections(self, tracks):
        for t in tracks:
            p = self.predictions.get(t["id"])
            if p and p["will_approach"] and not t["approaching"] and t["frames_tracked"] > 10:
                return f"I was tracking something at {t['clock']} as approaching, but it hasn't moved. Path is clear."
        return None
```

## KEY CODE: main.py Integration

In the frame handler, add after receiving frame:
```python
# After: frame_bytes = base64.b64decode(msg["data"])

# 1. Send to Gemini Live (passive context for conversation)
await gemini.send_frame(frame_bytes)

# 2. Send to Cloud Vision (reactive perception)
cv_result = await cloud_vision.analyze_frame(frame_bytes)

# 3. Track with SORT
tracks = tracker.update(cv_result["objects"])

# 4. Brain decides
decision = brain.process(tracks, cv_result["text"], cv_result.get("labels", []))

# 5. Alert injection
if decision["action"] == "alert":
    await gemini.send_text(f"SPATIAL ALERT: {decision['text']}. Tell the user naturally.")
elif decision["action"] == "correction":
    await gemini.send_text(f"SELF-CORRECTION: {decision['text']}. Admit the mistake naturally.")

# 6. Send brain state to frontend
await ws.send_json({"type": "brain_state", "tracks": decision["tracks"],
                     "urgency": decision["urgency"], "action": decision["action"],
                     "alert_text": decision["text"]})
```

## v3 System Prompt (Voice-Only Role)

```python
DRISHTI_SYSTEM_PROMPT = """
You are Drishti, a spatial intelligence voice companion.
Your backend brain tracks objects and computes urgency using computer vision.
You receive SPATIAL ALERTs — communicate them naturally.
When the user asks questions, answer using camera context you can see.
Use clock positions (10-2) for directions, step counts for distance.
Be concise for alerts (<10 words), conversational for descriptions.
When you receive SELF-CORRECTION, admit the mistake naturally.
"""
```

## SPLIT-SCREEN FRONTEND

Add right panel div in index.html. Receives `brain_state` messages:
```javascript
ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === "brain_state") {
        renderBrainPanel(msg.tracks, msg.urgency, msg.action, msg.alert_text);
    }
    // ... existing audio/transcript handlers
};
```

Render: track list with labels+clocks, urgency bar (color-coded), action status, prediction verify marks.

---

## ENVIRONMENT VARIABLES
```
GOOGLE_API_KEY=your_gemini_api_key
GOOGLE_CLOUD_PROJECT=your_gcp_project
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
PORT=8080
DEFAULT_PLUGIN=blind_navigation
```

## COMMANDS
```bash
pip install -r requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8080
# Deploy:
./deploy.sh
```
