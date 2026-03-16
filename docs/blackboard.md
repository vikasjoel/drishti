# SixthSense — Complete Blackboard
## Everything We Know, Have, Don't Have, and Need to Solve

---

## SECTION A: WHAT WE'RE BUILDING (One Sentence)

A universal spatial intelligence layer built on Gemini Live API that turns any phone camera into a continuously-learning spatial awareness agent — tracking objects, estimating distance and direction, adapting to changing environments, and communicating through natural voice.

---

## SECTION B: TECHNOLOGY AVAILABLE TO US

### B1: Gemini Live API — What We Actually Get

| Capability | Details | Confirmed Working |
|-----------|---------|-------------------|
| Audio in (continuous) | 16-bit PCM, 16kHz, via WebSocket | Yes |
| Audio out (continuous) | 16-bit PCM, 24kHz | Yes |
| Video in (frames) | JPEG images, 1 FPS recommended, 768x768 optimal | Yes |
| Text in/out | Via send_client_content or mixed with audio | Yes |
| Previous frames in context | Model sees previous frames within context window | Yes — this is KEY |
| Affective dialog | Adapts tone to user emotion | Yes (v1alpha) |
| Proactive audio | Model decides when to speak | Yes (v1alpha, Preview) |
| VAD / Barge-in | User can interrupt anytime | Yes |
| Function calling | Model calls our functions | Yes (quality drops with audio) |
| Google Search grounding | Real-time web info | Yes |
| Audio transcription (in+out) | Text of what's said both ways | Yes |
| Thinking mode | Reasoning with token budget | Yes |
| Context window | 128K tokens | Yes |
| Context compression | Sliding window, theoretically infinite sessions | Yes |
| Session resumption | Reconnect with handle (valid 24hr) | Yes |
| Media resolution control | LOW / MEDIUM / HIGH | Yes |
| System instruction | Custom persona/behavior | Yes |
| 30+ HD voices | Selectable via speechConfig | Yes |
| 70 languages | Auto-detect, auto-switch | Yes |
| Ephemeral tokens | Secure client-side auth | Yes |

### B2: ADK (Agent Development Kit) — What We Get

| Capability | Details |
|-----------|---------|
| Multi-agent orchestration | Parent/child agent hierarchies |
| Sequential/Parallel/Loop workflows | Workflow agents for pipelines |
| LLM-driven routing | Dynamic delegation between agents |
| Function tools | Custom Python functions as agent tools |
| MCP tools | Model Context Protocol integration |
| Google Search tool | Built-in |
| Code execution tool | Sandbox execution |
| Built-in dev UI | Browser-based testing/debugging |
| ADK Streaming | Bidirectional audio/video with Live API |
| Session management | State persistence across invocations |
| Deployment | Cloud Run, Vertex AI Agent Engine |
| Languages | Python (most mature), TypeScript, Go, Java |

### B3: Google Cloud Services Available

| Service | Use For Us |
|---------|-----------|
| Cloud Run | Backend hosting (serverless, auto-scale) |
| Firestore | Spatial state persistence, user profiles |
| Cloud Storage | Frame archival if needed |
| Vertex AI | Model hosting if we need additional models |
| Cloud Logging | Session analytics, debugging |
| Cloud Pub/Sub | Event-driven alerts if multi-user |

### B4: Web Technologies (No Native App Needed)

| Tech | Purpose |
|------|---------|
| getUserMedia() | Camera + mic access in browser |
| WebSocket | Real-time bidirectional to backend |
| Web Audio API | Audio processing, Bluetooth routing |
| Canvas API | Frame capture, resize, JPEG encode |
| PWA / Service Worker | Offline fallback, installability |

---

## SECTION C: WHAT WE DON'T HAVE (Honest Limitations)

### C1: Hard Technical Limits

| Limitation | Impact | Severity |
|-----------|--------|----------|
| **1 FPS video to Gemini** | Can't track objects moving >5 m/s between frames | HIGH for fast traffic, LOW for indoor/pedestrian |
| **Latency 320ms-800ms typical, spikes to 5-15s** | Delay between seeing and speaking | MEDIUM — not instant |
| **No true depth sensor** | Can't measure absolute distance | HIGH — must approximate |
| **Single camera, no rear view** | Blind to everything behind/beside camera FOV (~70°) | HIGH — fundamental physics |
| **128K context window** | At 258 tok/frame + 25 tok/s audio, fills in ~2 min (video) | MEDIUM — compression helps |
| **Audio+video hurts function calling** | Function calls less reliable during active A/V | MEDIUM |
| **No cross-frame object tracking built into Gemini** | We must prompt it to reason across frames | UNKNOWN — this is our experiment |
| **Battery drain** | Camera + WebSocket + audio = heavy drain | MEDIUM — manageable with LOW res |
| **Network required** | No internet = no function | HIGH for outdoor, LOW for WiFi environments |
| **Proactive audio is Preview** | May be unreliable | MEDIUM — we add our own logic layer |
| **Gemini spatial reasoning is documented as weak** | Can describe but struggles with precise positions | HIGH — our prompting must compensate |
| **No image output** | Can't show user anything visual (this is for voice) | N/A — our users may be blind |
| **Hallucination possible** | May describe objects that aren't there | HIGH for safety scenarios |
| **Scale ambiguity** | Small near vs large far is indistinguishable | MEDIUM — use known-object anchors |
| **Low light degrades everything** | Noisy images, bad recognition | MEDIUM |

### C2: What We Must Prove (Unknowns)

These are things nobody has tested. They are our RESEARCH QUESTIONS:

1. **Can Gemini reason about object movement across sequential frames in its context window?**
   - If YES → spatial-temporal tracking works natively
   - If NO → we need to extract positions ourselves and inject as text

2. **Can Gemini estimate relative distance changes using object size across frames?**
   - If YES → approach/recede detection works
   - If NO → we need frame-differencing math on backend

3. **Does proactive audio work reliably enough for a spatial awareness use case?**
   - If YES → agent stays silent and speaks only when needed
   - If NO → we implement our own priority/silence logic

4. **Can we maintain useful spatial state across context window compression?**
   - If YES → long sessions work
   - If NO → spatial memory resets periodically

5. **Does the system prompt reliably produce clock-position spatial language?**
   - If YES → consistent spatial communication
   - If NO → need post-processing of model output

---

## SECTION D: THE AGENT ARCHITECTURE

### D1: The Four-Agent Pipeline (ADK Multi-Agent)

```
┌─────────────────────────────────────────────────────┐
│              COORDINATOR AGENT (Parent)               │
│  Orchestrates the loop, manages state, routes tasks  │
│                                                       │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌────────┐│
│  │OBSERVER │→│ SPATIAL  │→│REASONER │→│ VOICE  ││
│  │         │  │ MODELER  │  │         │  │ ACTOR  ││
│  └─────────┘  └──────────┘  └─────────┘  └────────┘│
│       ↑                                      │       │
│       └──────── Feedback Loop ───────────────┘       │
└─────────────────────────────────────────────────────┘
```

### D2: Each Agent's Role

**OBSERVER Agent**
- Input: Raw JPEG frame from camera
- Job: Extract structured observations
- Output: JSON with objects detected, approximate positions (left/center/right, top/bottom), scene type, text visible, changes from previous observation
- Key: This is what Gemini Live API does with each frame — we PROMPT it to output structured spatial data
- System prompt focus: "For every frame, identify all objects with their position in the frame (left-third, center-third, right-third) and relative size (small/medium/large). Note any text visible. Classify scene type."

**SPATIAL MODELER Agent**
- Input: Observer's structured output + previous spatial state
- Job: Build and maintain the evolving spatial graph
- Output: Updated spatial state with object tracking, velocity estimates, predictions
- Key logic:
  - Object appeared in frame-center at size 5% → now at 12% → APPROACHING
  - Object was in left-third → now in center-third → MOVING RIGHT relative to user
  - Same object type at similar position across 3 frames → TRACKED object, assign ID
  - Object disappeared from frame → PASSED or EXITED
  - New object appeared → ENTERED scene
- This agent works with TEXT — it receives structured data and reasons about it
- Can run as a separate Gemini call (non-Live, fast, cheap) or as logic in backend code

**REASONER Agent**
- Input: Current spatial state + use case config + decision history
- Job: Decide what action to take RIGHT NOW
- Output: Priority-ranked action list
- Decision framework:
  ```
  PRIORITY 1 (IMMEDIATE): Approaching object on collision path
  PRIORITY 2 (ALERT): New significant object entered scene  
  PRIORITY 3 (INFORM): User asked a question → answer it
  PRIORITY 4 (AMBIENT): Scene changed significantly → brief update
  PRIORITY 5 (SILENT): Nothing noteworthy → say nothing
  ```
- Learning behavior: If user says "I know" after an alert → raise threshold for that object type. If user says "what?" → lower threshold, speak more. If user asks "what's around me?" frequently → increase ambient updates.
- Use case plugin loads here — different priority rules for blind/security/elderly

**VOICE ACTOR Agent**
- Input: Reasoner's decision + spatial state
- Job: Communicate to user via Gemini Live API audio output
- Output: Spoken response in spatial language
- Communication format:
  ```
  For alerts:  "{object}, {clock position}, {distance}, {movement}"
  Example:     "Person, 11 o'clock, close, approaching"
  
  For descriptions: Natural conversational response
  Example:     "You're in a wide aisle. Shelves on both sides. 
                End of the aisle is about 20 steps ahead."
  
  For answers:  Direct response to user question
  Example:     "That's a Kellogg's Corn Flakes box. 
                The expiry date says March 2027."
  ```
- Adapts tone via affective dialog — calm when user is stressed, brief when user is confident

### D3: The Learning Loop (Context Evolution)

The "self-training" happens through an evolving context state:

```
Frame 1:  "I see an indoor space. Fluorescent lights. Shelves visible."
          → State: {environment: "indoor_retail", confidence: 0.6}

Frame 5:  "Aisles confirmed. Products on shelves. Shopping carts visible."
          → State: {environment: "indoor_retail", confidence: 0.95,
                    layout: "parallel_aisles"}

Frame 10: "User has been walking straight. Shelves passing on both sides."
          → State: {user_movement: "forward", speed: "walking",
                    current_context: "in_aisle"}

Frame 15: "Aisle ends. Open space ahead. Checkout counters visible."
          → State: {current_context: "approaching_aisle_end",
                    prediction: "checkout_area_ahead"}

Frame 20: User asks "where's the dairy section?"
          → Agent: "Based on what I've seen, we've passed cereal and 
             snacks aisles. Dairy is typically at the perimeter. 
             I'd suggest turning right at the end of this aisle, 
             about 10 steps ahead."
```

The agent gets SMARTER with every frame because:
1. Environment classification improves (more evidence)
2. User movement model refines (observed walking speed, turning patterns)
3. Spatial map grows (what's been seen and where)
4. Communication calibrates (user feedback shapes response style)

### D4: The Context Injection Strategy

This is critical. We inject the spatial state INTO Gemini's context as structured text:

```python
# Every N frames, inject updated state as a system-level context
spatial_context = f"""
CURRENT SPATIAL STATE (auto-updated):
- Environment: {state.environment_type} (confidence: {state.confidence})
- User movement: {state.user_direction} at {state.user_speed}
- Active tracked objects: {json.dumps(state.active_objects)}
- Recent path: {state.path_summary}
- Objects passed: {state.passed_objects}
- Frames analyzed: {state.frame_count}
- Time in session: {state.session_duration}
- User communication preference: {state.user_pref}

RULES:
- Only speak for Priority 1-2 unless user asks
- Use clock positions for directions
- Use step counts for distance (1 step ≈ 0.7m)
- Track objects across frames by position and size changes
"""

await session.send_client_content(
    turns={"role": "user", "parts": [{"text": spatial_context}]},
    turn_complete=False  # Don't trigger response, just update context
)
```

This injection happens alongside the video frames. Gemini now has BOTH the raw visual information AND the structured spatial context. This dual input is what makes it reason spatially.

---

## SECTION E: THE WEB APP ARCHITECTURE

```
┌──────────────────────────────────────────────────┐
│            USER'S PHONE (Browser PWA)             │
│                                                    │
│  ┌──────────┐  ┌───────────┐  ┌────────────────┐ │
│  │ Camera   │  │ Mic       │  │ Bluetooth      │ │
│  │ (getUserM│  │ (audio    │  │ Earbuds        │ │
│  │  edia)   │  │  capture) │  │ (audio out)    │ │
│  └────┬─────┘  └─────┬─────┘  └───────┬────────┘ │
│       │              │                 │          │
│  ┌────▼──────────────▼─────────────────▼────────┐ │
│  │        WebSocket Client (JS)                  │ │
│  │  • Captures frames at 1 FPS (Canvas→JPEG)     │ │
│  │  • Captures audio chunks (PCM 16kHz)          │ │
│  │  • Receives audio response → plays to earbuds │ │
│  │  • Minimal UI (big start/stop button)         │ │
│  │  • Accessible (screen reader compatible)      │ │
│  └──────────────────┬───────────────────────────┘ │
└─────────────────────┼────────────────────────────┘
                      │ WebSocket
                      ▼
┌──────────────────────────────────────────────────┐
│          BACKEND (Cloud Run - Python)              │
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │            WebSocket Handler                  │ │
│  │  • Receives frames + audio from client        │ │
│  │  • Manages Gemini Live API session            │ │
│  │  • Runs Agent Pipeline (ADK)                  │ │
│  │  • Maintains Spatial State (in-memory)        │ │
│  │  • Returns audio to client                    │ │
│  └──────────────┬───────────────────────────────┘ │
│                 │                                  │
│  ┌──────────────▼───────────────────────────────┐ │
│  │         GEMINI LIVE API SESSION               │ │
│  │  • Model: gemini-2.5-flash-native-audio-     │ │
│  │          preview-12-2025                      │ │
│  │  • Config:                                    │ │
│  │    - response_modalities: ["AUDIO"]           │ │
│  │    - enable_affective_dialog: true            │ │
│  │    - proactivity: {proactive_audio: true}     │ │
│  │    - input_audio_transcription: {}            │ │
│  │    - output_audio_transcription: {}           │ │
│  │    - media_resolution: LOW (default)          │ │
│  │    - context_window_compression:              │ │
│  │        {sliding_window: {}}                   │ │
│  │    - thinking_config: {thinking_budget: 512}  │ │
│  │  • System instruction: [SPATIAL AGENT PROMPT] │ │
│  │  • Tools: [function declarations]             │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │         SPATIAL STATE MANAGER                 │ │
│  │  (Python - runs alongside Gemini session)     │ │
│  │                                               │ │
│  │  • Parses Gemini's spatial observations       │ │
│  │  • Maintains object tracking across frames    │ │
│  │  • Calculates velocity/direction changes      │ │
│  │  • Generates context injection text           │ │
│  │  • Manages use case plugin configuration      │ │
│  │  • Logs decision history for learning loop    │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │         FUNCTION TOOLS                        │ │
│  │  • get_location() → GPS/address               │ │
│  │  • search_nearby(query) → Google Maps/Search  │ │
│  │  • read_text(image_region) → OCR focus         │ │
│  │  • get_weather() → conditions affecting nav    │ │
│  │  • emergency_call() → trigger SOS              │ │
│  │  • log_spatial_event() → Firestore             │ │
│  │  • switch_resolution(level) → LOW/HIGH toggle  │ │
│  └──────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

---

## SECTION F: WHAT WE MUST BUILD (Task List)

### F1: Web App (Frontend)
- [ ] HTML page with camera/mic access
- [ ] WebSocket connection to backend
- [ ] Frame capture at 1 FPS (Canvas → JPEG → base64)
- [ ] Audio capture (PCM 16kHz)
- [ ] Audio playback (PCM 24kHz → speakers/Bluetooth)
- [ ] Minimal accessible UI (big button, status indicator)
- [ ] Use case selector (blind/security/elderly/custom)

### F2: Backend (Python on Cloud Run)
- [ ] WebSocket server (FastAPI or raw websockets)
- [ ] Gemini Live API session management
- [ ] Frame forwarding (client → Gemini)
- [ ] Audio forwarding (bidirectional)
- [ ] Spatial State Manager class
- [ ] Context injection loop
- [ ] Function tool handlers
- [ ] Session resumption handling
- [ ] Use case plugin loader

### F3: The System Prompt (Critical)
- [ ] Spatial observation instructions
- [ ] Clock-position communication format
- [ ] Multi-frame reasoning instructions
- [ ] Priority framework
- [ ] Adaptive communication rules
- [ ] Use case-specific behavioral rules

### F4: ADK Agent Structure
- [ ] Coordinator agent definition
- [ ] Sub-agent definitions (Observer, Modeler, Reasoner, Actor)
- [ ] Workflow pipeline (Sequential for each frame cycle)
- [ ] Tool definitions
- [ ] Session/state management

### F5: Demo Setup
- [ ] Demo scenario scripted and rehearsed
- [ ] Video recording (under 4 minutes)
- [ ] Architecture diagram
- [ ] README with spin-up instructions
- [ ] GCP deployment proof (Cloud Run console screenshot)

---

## SECTION G: THE CRITICAL EXPERIMENTS TO RUN FIRST

Before building everything, we need to validate the unknowns. Run these experiments in order:

### Experiment 1: Can Gemini track objects across frames?
- Send 5 sequential frames where a person walks closer
- System prompt: "Describe what changed between frames. Is the person closer or farther?"
- SUCCESS = Gemini correctly identifies approach
- FAILURE = We need manual size-tracking logic on backend

### Experiment 2: Does clock-position prompting work?
- Send a frame with objects at various positions
- System prompt: "Describe objects using clock positions (10-2 o'clock)"
- SUCCESS = Consistent clock-position output
- FAILURE = We map pixel positions to clock positions ourselves

### Experiment 3: Does context injection improve spatial reasoning?
- Run same frames WITH and WITHOUT spatial state injection
- Compare quality of spatial descriptions
- SUCCESS = Injection significantly improves accuracy
- FAILURE = We rely more on Gemini's native vision + our backend logic

### Experiment 4: Proactive audio behavior test
- Stream frames with gradual scene changes
- Test if model speaks unprompted at the right moments
- SUCCESS = Model alerts on significant changes, stays silent otherwise
- FAILURE = We implement explicit trigger logic on backend

### Experiment 5: End-to-end latency test
- Measure time from frame capture → spatial alert spoken
- TARGET: Under 3 seconds for indoor/pedestrian scenarios
- If >5 seconds → need to optimize pipeline

---

## SECTION H: WHAT MAKES THIS WIN

### H1: Technical Novelty
- First demonstration of Gemini Live API doing spatial-temporal reasoning across sequential frames
- First agentic spatial intelligence layer with self-evolving context
- First use of proactive audio for spatial awareness alerts
- First universal middleware approach — same engine, different plugins

### H2: Google Alignment
- Directly implements Google's "world model" vision
- Extends Project Astra from general assistant to spatial intelligence
- Uses ADK multi-agent architecture as intended
- Uses maximum Gemini Live API features (affective + proactive + vision + function calling + thinking + transcription)
- Deployable on Google Cloud end-to-end

### H3: Scale and Impact
- 2.2B people with vision impairment (primary use case)
- Warehouse/logistics ($400B+ industry, safety-critical)
- Elderly care (1B+ people over 60)
- Security/surveillance ($300B+ market)
- Any domain needing spatial awareness through a camera

### H4: What Judges Will Remember
- "The agent that builds a world model in real-time and gets smarter every second"
- "Same engine, plug in a use case — blind navigation, security monitoring, elderly care"
- "They showed Gemini doing spatial reasoning across frames — nobody has done that before"

---

## SECTION I: HONEST RISK ASSESSMENT

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Gemini CAN'T track across frames | 30% | High | Backend manual tracking as fallback |
| Latency too high for usable demo | 20% | High | Pre-record parts of demo, show live for conversation |
| Proactive audio doesn't trigger right | 40% | Medium | Backend forces model to respond via text injection |
| Context window fills too fast | 20% | Medium | Aggressive compression + shorter demo |
| Judges think it's "just another blind assistant" | 15% | High | Lead with platform pitch, blind is one demo |
| Can't deploy to Cloud Run in time | 10% | High | Run locally, show GCP proof via API calls |
| Frame quality too low for object recognition | 15% | Medium | Use well-lit indoor environment for demo |

---

## SECTION J: TIMELINE ESTIMATE

| Phase | Tasks | Time |
|-------|-------|------|
| Validate | Run 5 experiments above | Day 1-2 |
| Build core | Web app + backend + Gemini session | Day 2-4 |
| Build agents | ADK pipeline + spatial state manager | Day 4-6 |
| System prompt | Engineer and iterate the spatial prompt | Day 3-6 (parallel) |
| Integration | Connect everything end-to-end | Day 6-7 |
| Demo | Record video, write description, diagram | Day 7-8 |
| Polish | README, deployment proof, cleanup | Day 8-9 |
| Submit | Final review and submit | Day 9-10 |

---

## SECTION K: THE NAME

**SixthSense** — A spatial intelligence layer that gives any camera the power to understand, track, and communicate the physical world through natural voice.

Tagline: "See the world. Know the space. Stay aware."
