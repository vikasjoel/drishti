# Gemini Live API — Vision Deep Dive
## How Video/Image Input Integrates with Real-Time Voice

---

## 1. The Big Picture: Vision Is NOT a Separate API

This is the key insight most people miss: **vision in the Live API is not a separate call**. It flows through the **exact same WebSocket channel** as audio, using the exact same `send_realtime_input()` method. The model processes audio AND visual frames simultaneously in a single unified context.

```
┌──────────────┐     WebSocket (bidirectional)     ┌─────────────────────┐
│   YOUR APP   │ ─────────────────────────────────▶ │  GEMINI LIVE API    │
│              │   audio chunks (PCM 16kHz)         │                     │
│  Microphone ─┤   image frames (JPEG @ 1 FPS)     │  Single unified     │
│  Camera    ─┤   text messages                    │  model processes    │
│  Screen    ─┤                                    │  ALL modalities     │
│              │ ◀───────────────────────────────── │  simultaneously     │
│   Speaker  ◀─┤   audio response (PCM 24kHz)      │                     │
│   Text     ◀─┤   text response                   │                     │
│   Events   ◀─┤   function calls                  │                     │
└──────────────┘                                    └─────────────────────┘
```

**The model literally sees and hears at the same time.** You can ask "what am I holding?" while streaming video frames, and it responds via voice — all in one session.

---

## 2. Three Vision Input Sources

The Live API treats all vision inputs the same way — as JPEG image frames sent at intervals. But they come from three different sources:

### 2a. Camera Feed (Webcam / Phone Camera)
Capture frames from webcam using OpenCV or browser MediaCapture API, encode as JPEG, and stream at 1 FPS.

```python
# Python — Camera frame capture
import cv2
from google.genai import types

cap = cv2.VideoCapture(0)  # Open webcam

async def send_video_stream(session):
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 1. Resize to optimal resolution (768x768 max)
        frame = cv2.resize(frame, (768, 768))
        
        # 2. Encode as JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        
        # 3. Send as realtime input (SAME method as audio!)
        await session.send_realtime_input(
            media=types.Blob(
                data=buffer.tobytes(),
                mime_type="image/jpeg"
            )
        )
        
        # 4. Wait 1 second (1 FPS target)
        await asyncio.sleep(1.0)
    
    cap.release()
```

### 2b. Screen Sharing (Desktop / Browser Tab)
Capture screenshots using `mss` (Python) or `getDisplayMedia` (browser), encode as JPEG, send at 1 FPS.

```python
# Python — Screen capture
import mss
from PIL import Image
import io

sct = mss.mss()

async def send_screen_stream(session):
    while True:
        # Grab entire screen
        screenshot = sct.grab(sct.monitors[0])
        
        # Convert to PIL Image, resize, encode JPEG
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        img = img.resize((768, 768))
        
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=80)
        
        await session.send_realtime_input(
            media=types.Blob(
                data=buffer.getvalue(),
                mime_type="image/jpeg"
            )
        )
        
        await asyncio.sleep(1.0)
```

```javascript
// Browser — Screen capture using getDisplayMedia
const stream = await navigator.mediaDevices.getDisplayMedia({ video: true });
const track = stream.getVideoTracks()[0];
const imageCapture = new ImageCapture(track);

setInterval(async () => {
    const bitmap = await imageCapture.grabFrame();
    const canvas = document.createElement('canvas');
    canvas.width = 768;
    canvas.height = 768;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(bitmap, 0, 0, 768, 768);
    
    // Convert to base64 JPEG
    const base64Data = canvas.toDataURL('image/jpeg', 0.8)
        .split(',')[1];  // Strip data:image/jpeg;base64, prefix
    
    // Send through WebSocket to your backend → Gemini
    ws.send(JSON.stringify({
        realtime_input: {
            media_chunks: [{
                mime_type: "image/jpeg",
                data: base64Data
            }]
        }
    }));
}, 1000);  // Every 1 second
```

### 2c. Pre-recorded Video / File Upload
Extract frames from video files and send them as individual JPEG frames.

```python
# Extract frames from video file at 1 FPS
cap = cv2.VideoCapture("video.mp4")
fps = cap.get(cv2.CAP_PROP_FPS)
frame_interval = int(fps)  # 1 frame per second

frame_count = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break
    if frame_count % frame_interval == 0:
        frame = cv2.resize(frame, (768, 768))
        _, buffer = cv2.imencode('.jpg', frame)
        await session.send_realtime_input(
            media=types.Blob(data=buffer.tobytes(), mime_type="image/jpeg")
        )
    frame_count += 1
    await asyncio.sleep(1.0 / fps)  # Maintain timing
```

---

## 3. Critical Technical Specs for Vision

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Input frame rate** | 1 FPS recommended | API expects discrete image frames, not video stream |
| **Best resolution** | 768×768 native | Optimal balance of quality and token usage |
| **Format** | JPEG | Encoded as base64 Blob with `image/jpeg` mime type |
| **Token cost** | 258 tokens per frame (default) | At 1 FPS, that's 258 tokens/second of video |
| **Session limit (audio+video)** | ~2 minutes without compression | With context window compression → theoretically infinite |
| **Context window** | 128K tokens total | Shared between audio (25 tok/s), video (258 tok/s), text, and model output |
| **Media resolution config** | LOW / MEDIUM / HIGH | Controls tokens per frame; LOW reduces to ~100 tok/s of video |

### The Math That Matters

Without compression, at default resolution:
- Video: 258 tokens/sec × 120 seconds = **30,960 tokens** → 2 minutes fills ~31K tokens
- Audio: 25 tokens/sec × 120 seconds = **3,000 tokens** 
- Combined 2 min = ~34K tokens, leaving ~94K for context, system prompt, and model responses

**With LOW media resolution**: ~100 tokens/sec for video → extends to roughly 5-6 minutes before filling context

**With context window compression enabled**: Sessions can run indefinitely because the sliding window automatically truncates oldest frames.

---

## 4. The Media Resolution Setting (Hidden Power!)

This is one of the "hidden" APIs that gives you serious control:

```python
from google.genai import types

config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    # THIS controls how detailed the vision processing is
    media_resolution=types.MediaResolution.MEDIA_RESOLUTION_LOW,
)
```

Three levels:
- **LOW**: Fewer tokens per frame (~100 tok/s). Faster, cheaper, longer sessions. Good enough for "what's on screen" or "read this text".
- **MEDIUM**: Balanced. Default behavior.
- **HIGH**: Maximum detail per frame. Best for reading small text, identifying tiny objects, medical images.

**This is a key lever for hackathon optimization** — you can run LOW for general awareness and switch to HIGH only when you need detail.

---

## 5. Simultaneous Audio + Video: The Killer Pattern

This is where the real magic lives. You can stream BOTH audio AND image frames through the same session simultaneously:

```python
async def run_multimodal_session():
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        media_resolution=types.MediaResolution.MEDIA_RESOLUTION_LOW,
        enable_affective_dialog=True,  # Emotional awareness
        input_audio_transcription={},   # Transcribe what user says
        output_audio_transcription={},  # Transcribe what model says
    )
    
    async with client.aio.live.connect(model=model, config=config) as session:
        # Run three concurrent tasks:
        await asyncio.gather(
            send_audio(session),      # Mic → PCM audio chunks
            send_video(session),      # Camera → JPEG frames @ 1 FPS
            receive_responses(session) # Audio + transcripts back
        )
```

The model's responses are informed by EVERYTHING it's seeing and hearing. Ask "what color is that?" while pointing at something → it knows.

---

## 6. Sending Audio + Image in a Single Message

In the raw WebSocket protocol, you can bundle audio and image data in the **same message**:

```javascript
// Browser client → Backend → Gemini
// This sends BOTH audio AND a screen frame in one shot
const payload = {
    realtime_input: {
        media_chunks: [
            {
                mime_type: "audio/pcm",
                data: audioBase64    // Audio chunk
            },
            {
                mime_type: "image/jpeg",
                data: frameBase64    // Current screen/camera frame
            }
        ]
    }
};
webSocket.send(JSON.stringify(payload));
```

This is what the Google AI Studio "Stream Realtime" feature does under the hood — it bundles mic audio + screen/camera frames and sends them together.

---

## 7. Vision + Function Calling: The Action Layer

Here's where it gets really powerful for hackathon projects. The model can SEE something → decide to CALL A FUNCTION based on what it sees:

```python
# Example: Model sees a product via camera → looks up price
product_lookup = {
    "name": "lookup_product",
    "description": "Look up product info by name or description",
    "parameters": {
        "type": "object",
        "properties": {
            "product_name": {"type": "string"},
            "visual_description": {"type": "string"}
        }
    }
}

process_return = {
    "name": "process_return",
    "description": "Initiate a product return",
    "parameters": {
        "type": "object",
        "properties": {
            "product_id": {"type": "string"},
            "reason": {"type": "string"},
            "condition": {"type": "string"}
        }
    }
}

tools = [{"function_declarations": [product_lookup, process_return]}]

config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    tools=tools
)
```

**Flow**: User shows product to camera → model identifies it visually → calls `lookup_product` → gets price/details → speaks response → user says "I want to return it" → model calls `process_return` with the product info it saw.

---

## 8. Vision + Proactive Audio: The "Silent Watcher" Pattern

This is perhaps the most powerful combo for hackathon:

```python
config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    proactivity={'proactive_audio': True},   # Only speak when relevant
    media_resolution=types.MediaResolution.MEDIA_RESOLUTION_LOW,
    enable_affective_dialog=True,
)
```

The agent continuously watches the video stream but ONLY speaks up when:
- The user directly addresses it
- It sees something concerning/relevant
- The topic matches its system instruction

**Example use cases:**
- **Manufacturing QA**: Watches assembly line video, only alerts on defects
- **Cooking assistant**: Watches your cooking, only speaks when it notices something going wrong
- **Meeting co-pilot**: Watches presentation slides, only chimes in when asked or when data is relevant

---

## 9. Vision Input via send_client_content (Non-Realtime Path)

Besides `send_realtime_input`, you can also inject images via the **client content** path. This is useful for injecting reference images, documents, or context without real-time streaming:

```python
# Inject a reference image into conversation context
import base64

with open("reference_diagram.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

await session.send_client_content(
    turns={
        "role": "user",
        "parts": [
            {"text": "Here's the architecture diagram we're discussing:"},
            {"inline_data": {"mime_type": "image/jpeg", "data": image_data}}
        ]
    },
    turn_complete=True
)
```

This differs from `send_realtime_input` because:
- It's **ordered and deterministic** (realtime input is optimized for speed, not ordering)
- It **interrupts current model generation**
- It's treated as a **conversational turn**, not a continuous stream

---

## 10. What the Model CAN'T Do with Vision (Limitations)

- **No video output**: The Live API can process video IN but can only output audio or text, not generated video
- **No image generation in session**: Can't generate images during a Live session (but can trigger it via function calling to a separate Gemini image model)
- **1 FPS limit**: Fast-moving scenes may lose detail between frames
- **No object tracking**: Each frame is analyzed independently; the model doesn't track objects across frames like a CV system
- **Audio+video hurts function calling**: Google explicitly notes that audio inputs and outputs negatively impact function calling quality
- **Token budget pressure**: At 258 tokens/frame, video eats context fast. Must manage with LOW resolution or compression.

---

## 11. Advanced: Combining Live API Vision with Other Gemini APIs via Function Calling

This is the **hidden architecture pattern** that wins hackathons:

```
User speaks + shows camera → Live API (sees + hears)
    ↓ function call
Gemini 3 Pro Image (generates/edits image based on what was seen)
    ↓ result
Live API speaks back "Here's what I created based on what you showed me"
```

The Live API can orchestrate OTHER Gemini APIs through function calling:
- **Gemini 3 Pro Image** ("Nano Banana"): Generate or edit images
- **Veo**: Generate video clips
- **Google Search**: Ground visual observations in real-time web data
- **Cloud Vision API**: For specialized OCR, label detection, etc.

```python
# Function that Live API can call to generate an image
generate_image_tool = {
    "name": "generate_image",
    "description": "Generate an image based on a description or modify an existing image",
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "What to generate"},
            "refers_to_camera": {"type": "boolean", "description": "Whether to base it on what the camera sees"}
        }
    }
}
```

Your function handler would then call `gemini-3-pro-image-preview` with `generateContent` and return the result. The Live API will describe the generated image via voice.

---

## 12. Production Architecture for Vision-Enabled Agent

```
┌─────────────────────────────────────────────────────────┐
│                    BROWSER / MOBILE APP                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ Mic      │  │ Camera/  │  │ UI (React/Angular)   │  │
│  │ (audio)  │  │ Screen   │  │ - Transcripts        │  │
│  │          │  │ (frames) │  │ - Generated images   │  │
│  └────┬─────┘  └────┬─────┘  │ - Status indicators  │  │
│       │              │        └──────────────────────┘  │
│       └──────┬───────┘                                  │
│              ▼                                          │
│     WebSocket to Backend                                │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              BACKEND (Cloud Run on GCP)                  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  WebSocket Handler (FastAPI / Express)           │    │
│  │  - Receives audio + frames from client           │    │
│  │  - Forwards to Gemini Live API via WebSocket     │    │
│  │  - Handles function call results                 │    │
│  │  - Returns audio + text to client                │    │
│  └───────────┬─────────────────────┬───────────────┘    │
│              │                     │                     │
│              ▼                     ▼                     │
│  ┌───────────────────┐  ┌──────────────────────┐       │
│  │ Gemini Live API   │  │ Function Handlers     │       │
│  │ (WebSocket)       │  │ - Firestore CRUD      │       │
│  │ - Native audio    │  │ - Cloud Vision API    │       │
│  │ - Vision frames   │  │ - Gemini Image Gen    │       │
│  │ - Tool calls      │  │ - External APIs       │       │
│  └───────────────────┘  └──────────────────────┘       │
└─────────────────────────────────────────────────────────┘
```

---

## 13. Summary: Vision Capabilities Cheat Sheet

| What You Can Do | How |
|----------------|-----|
| Stream webcam in real-time | `send_realtime_input(media=Blob(jpeg))` at 1 FPS |
| Stream screen share | Same as above, capture with mss/getDisplayMedia |
| Bundle audio + image together | Both in `media_chunks` array in one message |
| Control vision quality/cost | `media_resolution`: LOW / MEDIUM / HIGH |
| Extend video sessions | `context_window_compression` with sliding window |
| Act on what's seen | Function calling with visual context |
| Silent watching mode | Proactive audio — only responds when relevant |
| Inject reference images | `send_client_content` with inline_data |
| Generate images from vision | Function call → Gemini 3 Pro Image API |
| Get text of what model sees | `output_audio_transcription` + TEXT modality |

---

## Next Steps

Now that we know exactly how vision works, we can design a project that **maximally leverages the vision + voice + function calling combo**. The strongest projects will use:

1. **Real-time camera/screen input** (not just audio)
2. **Function calling triggered by visual observation**
3. **Proactive audio** for natural "only speak when needed" behavior
4. **Context window compression** for longer sessions
5. **Media resolution switching** (LOW for ambient, HIGH for detail moments)
