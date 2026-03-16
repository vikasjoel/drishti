# Drishti (दृष्टि) — Complete Architecture Design
## Spatial Intelligence Framework for Real-Time World Modeling

**Version**: 2.0 — Post-Experiment Design  
**Date**: March 12, 2026  
**Status**: Architecture validated through experiments, ready for implementation

---

## Table of Contents

1. [The Idea](#1-the-idea)
2. [Architecture Overview](#2-architecture-overview)
3. [The Brain — Mapped to Human Cognition](#3-the-brain)
4. [Hybrid Perception System](#4-hybrid-perception)
5. [World Model — What It Contains](#5-world-model)
6. [Memory Architecture](#6-memory-architecture)
7. [Object Identity and Tracking](#7-object-identity)
8. [Temporal Intelligence](#8-temporal-intelligence)
9. [The Predict-Verify-Correct Loop](#9-predict-verify-correct)
10. [Three Nested Intelligence Loops](#10-three-loops)
11. [Decision Engine and Behavioral Dimensions](#11-decision-engine)
12. [Purpose, Goals, and Attention](#12-purpose-goals-attention)
13. [Communication Control](#13-communication-control)
14. [Domain Plugin System](#14-domain-plugins)
15. [Deployment Patterns — Self-Discovering vs Guided Setup](#15-deployment-patterns)
16. [Stationary Camera Use Cases](#16-stationary-use-cases)
17. [Session Lifecycle — Cold Start, Warm Start, Shutdown](#17-session-lifecycle)
18. [Place Recognition](#18-place-recognition)
19. [Memory Lifecycle — Decay, Pruning, Consolidation](#19-memory-lifecycle)
20. [Honest Limitations — What This Is and Isn't](#20-limitations)
21. [Data Structures](#21-data-structures)
22. [Synchronization Design](#22-synchronization)
23. [Scenario Walkthroughs](#23-scenarios)
24. [Stress Test: 100 Scenarios, 25 Gaps Fixed](#24-stress-test)
25. [Experiment Results](#25-experiments)
26. [Implementation Order](#26-implementation)
27. [Tech Stack](#27-tech-stack)
28. [Cost Model](#28-cost)

---

## 1. The Idea <a name="1-the-idea"></a>

Drishti is NOT a chatbot with a camera. It is NOT "send frame, get description."

Drishti demonstrates that you can construct a **functioning spatial world model** — with memory, temporal reasoning, prediction, and autonomous decision-making — by using a foundation model as the perception and communication interface, while the **intelligence architecture** lives as a structured computational system that mirrors how biological spatial cognition actually works.

The foundation model (Gemini) is the sensory cortex and the speech center. The backend is the hippocampus (spatial memory), the prefrontal cortex (planning and decisions), the cerebellum (temporal pattern learning), and the amygdala (urgency and emotional adaptation).

### The Core Cognitive Loop

No other hackathon project will build this: **PREDICT → PERCEIVE → COMPARE → CORRECT → LEARN**

Every other submission: PERCEIVE → DESCRIBE. See frame, say what's in it. That's a parrot with eyes.

Drishti: The agent maintains a BELIEF about what reality looks like right now — including things it can't currently see. Every cycle, it generates PREDICTIONS about what the next frame should contain. Then when perception arrives, it doesn't ask "what do you see?" It COMPARES perception against belief. The gap between belief and reality IS the intelligence signal.

### Why It's Worth $80K

1. **Perception through a foundation model** — not traditional CV, not just prompting, but using models as VERIFICATION engines against a structured belief state
2. **Persistent structured world model** — survives context compression, maintains object permanence, tracks temporal trajectories
3. **Predict-verify-correct loop** — the core mechanism of intelligence, running every second
4. **Emergent goals from purpose + state** — not coded behaviors, genuine autonomous agency
5. **Attention driven by prediction error** — focuses on what's SURPRISING, not what's visible
6. **Multi-domain through configuration, not code** — universal cognitive architecture

---

## 2. Architecture Overview <a name="2-architecture-overview"></a>

### The Three Components

```
┌─────────────────────────────────────────────────────────────┐
│                    PERCEPTION LAYER                          │
│                                                              │
│  ┌──────────────┐  ┌─────────────────┐  ┌────────────────┐ │
│  │ Cloud Vision  │  │ Gemini          │  │ Gemini Live    │ │
│  │ API           │  │ generateContent │  │ API            │ │
│  │               │  │                 │  │                │ │
│  │ Reactive:     │  │ Cognitive:      │  │ Voice:         │ │
│  │ 1-2s cycle    │  │ 5-10s cycle     │  │ Continuous     │ │
│  │ Bounding boxes│  │ Scene reasoning │  │ User speech    │ │
│  │ Labels, OCR   │  │ Relationships   │  │ Agent speech   │ │
│  │ Confidence    │  │ Predictions     │  │ Audio I/O      │ │
│  └──────┬───────┘  └───────┬─────────┘  └───────┬────────┘ │
│         │                   │                     │          │
└─────────┼───────────────────┼─────────────────────┼──────────┘
          │                   │                     │
          ▼                   ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                     THE BRAIN (Backend)                       │
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐  │
│  │ Temporal  │ │ Parietal │ │ Hippo-   │ │ Prefrontal    │  │
│  │ Lobe     │ │ Cortex   │ │ campus   │ │ Cortex        │  │
│  │          │ │          │ │          │ │               │  │
│  │ Object   │ │ Spatial  │ │ Cognitive│ │ Working memory│  │
│  │ identity │ │ math     │ │ map      │ │ Goals         │  │
│  │ matching │ │ Clock pos│ │ Episodic │ │ Decisions     │  │
│  │ Registry │ │ Distance │ │ memory   │ │ Inhibition    │  │
│  │ Confidence│ │ Trajector│ │ Landmarks│ │ Attention     │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────────┘  │
│                                                              │
│  ┌──────────┐ ┌──────────────────────────────────────────┐  │
│  │ Amygdala │ │ Cerebellum                               │  │
│  │          │ │                                           │  │
│  │ Fast     │ │ Temporal predictions, pattern detection   │  │
│  │ threat   │ │ Self-calibration, user calibration        │  │
│  │ detection│ │ Threshold adjustment from outcomes        │  │
│  └──────────┘ └──────────────────────────────────────────┘  │
│                                                              │
│                    WORLD MODEL                               │
│            (The belief state of reality)                      │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                  COMMUNICATION LAYER                          │
│                                                              │
│  Brain decides WHAT to say and WHEN                          │
│  Gemini Live speaks it naturally with emotion/tone           │
│  Brain decides to STAY SILENT (most of the time)             │
│                                                              │
│  95% of frames → brain says nothing                          │
│  The agent that speaks only when it matters is intelligent    │
└─────────────────────────────────────────────────────────────┘
```

### Information Flow

```
Camera (1 FPS)
  │
  ├──→ Cloud Vision API ──→ Bounding boxes, labels, OCR ──→ Brain (reactive)
  │                                                            │
  ├──→ Gemini generateContent ──→ Scene understanding JSON ──→ Brain (cognitive)
  │         (every 5-10s)                                      │
  ├──→ Gemini Live (send_realtime_input) ──→ Visual context    │
  │         for conversation                                   │
  │                                                            ▼
  │                                                     WORLD MODEL
  │                                                     updates + predictions
  │                                                            │
  │         ┌──────────────────────────────────────────────────┘
  │         │
  │         ▼
  │    Decision Engine
  │    "Should I speak? About what? How urgently?"
  │         │
  │         ▼ (only when brain decides)
  └──→ Gemini Live (send_client_content) ──→ Natural speech to user
       
User speaks ──→ Gemini Live transcription ──→ Brain receives intent
```

---

## 3. The Brain — Mapped to Human Cognition <a name="3-the-brain"></a>

### Temporal Lobe — Object Recognition and Memory

Receives: Structured data from Cloud Vision (bounding boxes, labels, confidence)  
Maintains: Object Registry — known entities with identity signatures  
Computes: Identity matching — "is this the SAME bottle I saw before?"  
Outputs: Matched object identities with confidence scores

When Cloud Vision reports "blue rectangular object at position (0.76, 0.54)", the Temporal Lobe matches it against the registry: "This matches obj_012, the Aquafina bottle first seen on the desk 2 minutes ago. Confidence 0.87."

When confidence is low (ambiguous match), it signals the attention system: "Need more data on this object. Ask the cognitive loop to look more carefully."

### Parietal Cortex — Spatial Computation

Receives: Bounding boxes with pixel coordinates from Cloud Vision  
Computes: Clock positions, distance estimates, trajectories, approach detection  
Outputs: Egocentric spatial model — everything relative to user

This is MATH, not language:

```python
# Pixel bbox [120, 180, 380, 560] on 768x768 frame
center_x = (120 + 380) / 2 / 768  # = 0.33 (left-of-center)
center_y = (180 + 560) / 2 / 768  # = 0.48 (middle)
size_pct = ((380-120) * (560-180)) / (768*768) * 100  # = 16.8%

# To clock position
clock = x_to_clock(center_x)  # 0.33 → "11 o'clock"
```

### Three-Tier Distance Estimation

**Tier 1 — Size Change Rate (calibration-free, always works)**. For approach detection — the critical safety use case — we don't need absolute distance. We need SIZE CHANGE RATE. If an object's bounding box area grew 50% in 2 seconds, it's approaching FAST regardless of absolute distance. No camera calibration needed.

```python
def compute_approach_urgency(self, obj):
    if len(obj.size_history) < 3:
        return 0.0
    recent = obj.size_history[-3:]
    dt = recent[-1][1] - recent[0][1]
    rate = (recent[-1][0] - recent[0][0]) / max(dt, 0.1)  # %/sec
    current_size = recent[-1][0]
    
    if rate <= 0: return 0.0  # Not approaching
    if current_size > 25 and rate > 5: return 0.95  # Very close, fast
    if current_size > 15 and rate > 3: return 0.7   # Close, approaching
    if rate > 5: return 0.5                          # Far but fast
    if rate > 2: return 0.3                          # Moderate
    return 0.1
```

**Tier 2 — Categorical Distance (lookup table, no calibration)**. Uses bounding box height as fraction of frame height. Calibrated for average phone camera FOV (~70°). Returns categories + step estimates, never false-precision meters.

```python
DISTANCE_CATEGORIES = [
    (0.60, "very_close", "1-2 steps"),
    (0.35, "close",      "3-4 steps"),
    (0.18, "near",       "5-8 steps"),
    (0.08, "medium",     "8-15 steps"),
    (0.03, "far",        "15-25 steps"),
    (0.00, "very_far",   "25+ steps"),
]
```

**Tier 3 — Gemini-Enhanced Distance (from cognitive loop)**. The cognitive loop asks Gemini to estimate distances using trained depth perception — perspective lines, relative sizes, occlusion ordering, atmospheric perspective. Most accurate but only updates every 5-10 seconds.

The system never claims precision it doesn't have: "close, about 3-4 steps" — not "2.7 meters."

### Hippocampus — Cognitive Map and Episodic Memory

Maintains two structures:

**Cognitive Map (Allocentric)**: A TOPOLOGICAL map — not pixel coordinates, but places connected by paths. "Entry → Corridor → Branch → Current aisle." This map is STABLE — it doesn't change when the user turns around. Nodes are places, edges are paths between them. Objects and landmarks are anchored to places.

**Episodic Memory**: Significant events anchored to places and times. Not every frame — just surprises, corrections, user interactions, and landmarks. "At the entrance: entered the store." "At aisle 2: person approached from left." "At the cross-aisle: sign says Dairy →"

Episodic events are spatially tagged: each episode knows WHERE in the cognitive map it happened.

### Prefrontal Cortex — Executive Function

The CEO of the brain. Receives HIGH-LEVEL summaries from all other areas. Maintains:

- **Working memory**: 5-7 most relevant items RIGHT NOW (active tracked objects + active goals + recent events)
- **Goals**: Persistent objectives that survive context compression
- **Decisions**: speak / stay silent / investigate / wait
- **INHIBITION**: Most important function — suppress irrelevant information from reaching the user

95% of perception data is SUPPRESSED. Only significant changes, approaching objects, decision points, and user-requested information gets through.

### Amygdala — Threat Detection

Fast path that BYPASSES normal decision flow. When Cloud Vision reports an object with rapidly increasing size (approaching fast), urgency spikes immediately. This triggers an alert without waiting for the cognitive loop, goal evaluation, or decision deliberation.

```
Perception → THREAT DETECTED → SPEAK NOW
```

Different from normal path:
```
Perception → World model → Goals → Decision → Speak (maybe)
```

### Cerebellum — Timing, Patterns, Calibration

Handles temporal patterns and self-calibration:

- Object trajectory extrapolation: "Person at current speed will reach me in 3 seconds"
- Environment rhythms: "People pass through here every 20 seconds"
- Self-calibration: "My distance estimates in this lighting are 20% too far"
- User calibration: "This user walks at 1.1 m/s, prefers concise alerts"
- Alert calibration: "Alerts at urgency 0.5 get acknowledged 80% of the time — good threshold"

---

## 4. Hybrid Perception System <a name="4-hybrid-perception"></a>

### Why Three Channels

Single-channel perception fails in different ways:

- **Cloud Vision alone**: Fast and structured, but no scene understanding. Knows "person" and "table" but not "person sitting at table eating in a restaurant."
- **Gemini generateContent alone**: Deep understanding, but 1-3s latency per call. Too slow for safety alerts.
- **Gemini Live alone**: Can see and speak, but function calling only works once per session (proven by experiment). Can't reliably output structured data.

The hybrid combines strengths: Cloud Vision for speed, Gemini for understanding, Live for voice.

### Channel 1: Cloud Vision API (Reactive Perception)

**Frequency**: Every 1-2 seconds  
**Latency**: 200-500ms  
**Cost**: ~$1.50 per 1000 images  
**Output**: Bounding boxes, labels, confidence scores, OCR text  

**What it provides to the brain**:
- OBJECT_LOCALIZATION: bounding boxes for all detected objects
- LABEL_DETECTION: what each object is (person, car, table, door)
- TEXT_DETECTION: OCR on signs, labels, screens
- FACE_DETECTION: presence of faces (not identity)

**What it CANNOT do**:
- Understand spatial relationships ("person is blocking the door")
- Infer activity ("person is walking toward you")
- Understand environment context ("this is a grocery store")
- Detect non-standard hazards ("wet floor", "glass wall")

**The brain's role**: Convert raw bounding boxes into spatial data (clock positions, distances, trajectories). Track objects across frames by position matching. Compute approach velocities from size trends.

### Channel 2: Gemini generateContent (Cognitive Perception)

**Frequency**: Every 5-10 seconds  
**Latency**: 1-3 seconds  
**Cost**: ~$0.001 per call  
**Output**: Structured JSON via response_schema

**What it provides to the brain**:
- Environment classification and layout understanding
- Object activity and behavior inference
- Spatial relationship reasoning
- Hazard detection (non-obvious hazards)
- Predictions for the next 5-10 seconds
- Verification/correction of brain's current beliefs

**Prompt structure** — shaped by current world model:

```
"Current world model: [brain state]
Verify or correct: [predictions]
Answer: [specific questions the brain needs resolved]
Respond as JSON with this schema: [response_schema]"
```

**Why response_schema matters**: Regular Gemini API supports `response_schema` — guaranteed JSON structure. No parsing needed. The brain gets exactly the fields it expects, every time. This is NOT available in the Live API.

### Channel 3: Gemini Live API (Voice)

**Connection**: Continuous WebSocket  
**Model**: gemini-2.5-flash-native-audio-preview-12-2025  
**Role**: Voice interface ONLY — does NO perception work

**What it does**:
- Receives user speech → transcription → brain
- Receives brain alerts → speaks them naturally to user
- Receives frames via send_realtime_input → visual context for Q&A
- One-shot function call at session start → initial scene inventory

**Configuration**:
```python
config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    system_instruction="You are the voice of Drishti...",
    realtime_input_config=types.RealtimeInputConfig(
        automatic_activity_detection=types.AutomaticActivityDetection(disabled=False),
        turn_coverage="TURN_INCLUDES_ALL_INPUT"
    ),
    proactivity={"proactive_audio": True},
    enable_affective_dialog=True,
    input_audio_transcription={},
    output_audio_transcription={},
    media_resolution=types.MediaResolution.MEDIA_RESOLUTION_LOW,
    context_window_compression=types.ContextWindowCompressionConfig(
        sliding_window=types.SlidingWindow(),
    ),
    thinking_config=types.ThinkingConfig(thinking_budget=0),  # Prevents crashes with function calling
)
```

**Critical settings proven by experiments**:
- `turn_coverage: TURN_INCLUDES_ALL_INPUT` — without this, Gemini ignores video frames when user is silent
- `thinking_budget: 0` — thinking + function calling on native audio causes 1011 crashes
- `context_window_compression` with `sliding_window` — required for sessions > 2 minutes (audio+video)

### How the One-Shot Function Call Works

At session start, Gemini Live performs one structured function call:

```python
SPATIAL_TOOL = {
    "function_declarations": [{
        "name": "report_spatial_observation",
        "description": "Report structured spatial observations from the current camera frame...",
        "parameters": {
            "type": "object",
            "properties": {
                "objects": { ... },  # Array of objects with positions, sizes, clock, distance
                "environment_description": { ... },
                "lighting": { ... },
                "frame_quality": { ... }
            }
        }
    }]
}
```

This bootstraps the brain with a rich initial scene inventory while Cloud Vision warms up. After this single call, Cloud Vision and generateContent take over as the continuous perception streams.

**Limitation confirmed by experiment**: The native audio model only calls functions ONCE per session. Hit rate was 1/6 in both v1 and v2 experiments despite varying prompts, NON_BLOCKING behavior, rich tool responses, and changing frames. This is a mechanical limitation of the model, not a prompting issue.

---

## 5. World Model — What It Contains <a name="5-world-model"></a>

The world model is: **"What the agent believes reality is, including everything it can't currently see."**

Current perception is what you see RIGHT NOW. The world model is what you BELIEVE is true about the ENTIRE world around you — behind you, around corners, in the next room, five minutes ago, five seconds from now.

### The Space (Topological Map)

Not coordinates. TOPOLOGY. Places connected by paths.

```
Entry (door) ─── Main Corridor ─── Junction
                      │                 ├── Left: Aisle 1
                      │                 ├── Center: Aisle 2 ← USER IS HERE
                      │                 └── Right: Aisle 3
                      │
                 Cross-Aisle ─── Checkout Area
```

Nodes are PLACES. Edges are PATHS. The agent knows where it IS in this structure, where it CAME FROM, and what it EXPECTS ahead based on the pattern.

### How the Topological Map BUILDS Itself

Full visual SLAM is massive overkill. Instead, the cognitive loop (Gemini generateContent) acts as a **scene transition detector**. Every cognitive cycle, Gemini analyzes the current frame and reports: "same place as before" or "new place — entered through a door/turn/stairs."

The map builds from TRANSITIONS, not pixel geometry:

```python
class TopologicalMapBuilder:
    """
    Builds map using Gemini as transition detector.
    No SLAM. Scene understanding from foundation model.
    """
    def process_cognitive_update(self, analysis: CognitiveAnalysis):
        if analysis.place_transition == "same":
            # Enrich current node with new landmarks/text
            self.current_node.update(analysis)
        
        elif analysis.place_transition == "new":
            # Create new node + edge from old place to new
            new_node = PlaceNode(
                description=analysis.environment,
                place_type=analysis.environment_type,
                text_signatures=analysis.detected_text,
                key_features=analysis.key_visual_features
            )
            edge = PlaceEdge(
                from_node=self.current_node.id,
                to_node=new_node.id,
                transition_type=analysis.transition_type,  # "door"/"turn"/"stairs"
                direction=analysis.transition_direction     # "left"/"right"/"up"
            )
            self.nodes[new_node.id] = new_node
            self.edges.append(edge)
            self.current_node = new_node
        
        elif analysis.place_transition == "returned":
            # Loop closure — recognize previously visited place
            matched = self.find_matching_node(analysis.key_visual_features)
            if matched:
                self.edges.append(PlaceEdge(self.current_node.id, matched.id, "loop_closure"))
                self.current_node = matched
```

The cognitive loop prompt includes `"place_transition": "same | new | returned"` in its response schema. Gemini naturally understands spatial transitions — it can tell a corridor from an aisle, detect doors, recognize when a scene matches a previous one. The topological map emerges from Gemini's scene understanding, not from pixel-level computation.

### Objects as Persistent Entities

Objects exist independently of being observed. Each entity has:

- **Identity**: What makes THIS object distinguishable from others
- **History**: Where it's been, how it's moved, when last confirmed
- **Predicted current state**: Even when not visible, where the brain believes it is
- **Relationships**: What is it near, what is it part of, who is carrying it
- **Behavioral expectations**: People move, furniture doesn't, doors open and close

Two fundamental categories:

**Static objects**: Furniture, walls, signs, shelves. Define the STRUCTURE of space. Once observed, stay put. Value: NAVIGATIONAL.

**Dynamic objects**: People, vehicles, animals, opening doors. Move THROUGH space. Require continuous tracking. Value: SAFETY and SOCIAL.

### The User as an Entity

The agent models the user:

- **Position**: Where in the cognitive map
- **Direction**: Which way they're facing (inferred from camera orientation)
- **Speed**: Walking pace (inferred from frame change rate)
- **State**: Moving/stationary/turning (inferred from frame similarity)
- **Intent**: Walking steadily (going somewhere), stopping and turning (searching), facing a shelf (examining)
- **Social state**: Alone, in conversation, on phone

### Uncertainty as First-Class Property

Everything has a confidence level:

- **High confidence (0.8-1.0)**: Currently visible, recently confirmed, multiple data sources agree
- **Medium confidence (0.5-0.8)**: Seen recently, position extrapolated, single data source
- **Low confidence (0.2-0.5)**: Not seen for a while, inferred, contradicted by one source
- **Very low (0.0-0.2)**: Old data, never directly observed, based on assumption

Uncertainty changes over time:
- Things seen 2 seconds ago: high confidence
- Things seen 30 seconds ago without re-confirmation: declining
- Things inferred but never directly observed: always lower than observed things

Uncertainty drives behavior:
- High confidence → act on it
- Medium confidence → verify it (direct attention)
- Low confidence → investigate or ignore
- Conflicting evidence → something is wrong, prioritize resolving

---

## 6. Memory Architecture <a name="6-memory-architecture"></a>

### Sensory Buffer (Gemini Context Window)

Raw "right now." Last 30-60 seconds of frames in Gemini Live's context. Volatile — context compression wipes it. This is NOT memory. This is just seeing.

### Working Memory (Brain — Active State)

Small, focused, constantly updating. The 5-7 items most relevant RIGHT NOW:

- Currently tracked dynamic objects with trajectories
- Active goals (1-3)
- Most recent user statement/intent
- Current environment classification
- Most recent alert and user response
- Current urgency level

### Episodic Memory (Brain — Event Timeline)

Not every frame. Just SIGNIFICANT events, in order, with spatial anchoring:

```python
Episode(
    timestamp=1710234567.89,
    frame_id=45,
    place="aisle_2",  # Anchored to cognitive map node
    event_type="person_approached",
    description="Person approached from 10 o'clock, passed on left",
    objects_involved=["person_1"],
    user_response="acknowledged",
    outcome="person passed safely"
)
```

Episodes are recorded when:
- Prediction fails (surprise)
- New object appears or tracked object disappears
- User asks a question or gives a response
- Environment changes (door crossed, turn detected)
- Alert was given
- Landmark detected (sign, distinctive feature)

### Spatial Memory (Brain — Cognitive Map)

The topological map of discovered space. Persists across context compression. Nodes are places with attached objects and landmarks. Edges are paths with traversal characteristics (narrow, wide, stairs, door).

Stored in backend Python structure. Cross-session persistence via Firestore.

### Object Memory (Brain — Identity Registry)

Registry of every uniquely identified object encountered:

```python
ObjectMemory(
    id="obj_012",
    description="Blue Aquafina bottle, ~25cm, cylindrical",
    signature_hash="blue_bottle_aquafina_25cm",  # Matchable signature
    first_seen=FrameRef(frame=34, timestamp=..., place="desk_area"),
    locations_seen=[
        (desk, "1 o'clock", frame_34),
        (table, "2 o'clock", frame_89)
    ],
    last_confirmed=FrameRef(frame=89, timestamp=...),
    confidence=0.82,
    is_static=True
)
```

### Semantic Memory (Brain — Learned Patterns)

Accumulated knowledge that transcends individual episodes:

- "In this type of space, people tend to approach from the left"
- "This user walks at about 1.1 m/s"
- "When brightness drops below 0.4, object detection becomes unreliable"
- "Static objects in this environment are stable — don't re-check frequently"

Cross-session persistence via Firestore. You don't start from zero next time.

---

## 7. Object Identity and Tracking <a name="7-object-identity"></a>

### How Identity Works

When Cloud Vision reports an object, the brain doesn't ask "what is this?" It asks "is this something I've seen before?"

Three matching criteria:

**Spatial continuity**: Is it where I'd expect? If the bottle was on the desk and I haven't moved, a bottle on the desk is probably the same one.

**Appearance consistency**: Does it LOOK the same? Same label from Cloud Vision, similar bounding box size, similar position.

**Temporal plausibility**: Does it make SENSE? A bottle 10 seconds later — very likely same. A bottle 3 hours later in a different building — unlikely.

### Matching Algorithm — SORT (Simple Online Realtime Tracking)

The industry standard for multi-object tracking, used in autonomous vehicles and surveillance. Two components: Kalman Filter for prediction (where SHOULD this object be?) and Hungarian Algorithm for optimal assignment (which detection IS which track?).

**Why not greedy matching?** With 3 people all labeled "person," greedy matching fails when they cross paths. Person A at 10 o'clock and Person B at 12 o'clock swap positions between frames — greedy assigns both wrong. The Hungarian Algorithm guarantees OPTIMAL global assignment.

```python
from scipy.optimize import linear_sum_assignment
from filterpy.kalman import KalmanFilter

class SORTTracker:
    """Kalman Filter prediction + Hungarian Algorithm assignment."""
    
    def __init__(self, max_age=5, min_hits=3, iou_threshold=0.3):
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.tracks: List[KalmanTrack] = []
        self.next_id = 0
    
    def update(self, detections: List[CVObject], frame_id: int):
        # Step 1: PREDICT — Kalman filter extrapolates each track
        for track in self.tracks:
            track.predict()
        
        # Step 2: BUILD COST MATRIX
        if self.tracks and detections:
            cost_matrix = np.zeros((len(self.tracks), len(detections)))
            for t, track in enumerate(self.tracks):
                for d, det in enumerate(detections):
                    iou = compute_iou(track.get_bbox(), det.bbox)
                    label_match = 1.0 if track.cv_label == det.label else 0.0
                    cost = 1.0 - (0.6 * iou + 0.25 * label_match + 0.15 * size_similarity)
                    cost_matrix[t, d] = cost
            
            # Step 3: HUNGARIAN ALGORITHM — optimal assignment
            track_idx, det_idx = linear_sum_assignment(cost_matrix)
            
            # Filter high-cost assignments (unrelated objects)
            matches, unmatched_tracks, unmatched_dets = filter_matches(
                track_idx, det_idx, cost_matrix, self.iou_threshold)
        
        # Step 4: UPDATE matched tracks
        for t, d in matches:
            self.tracks[t].update(detections[d], frame_id)
        
        # Step 5: CREATE new tracks for unmatched detections
        for d in unmatched_dets:
            self.tracks.append(KalmanTrack(detections[d], self._next_id(), frame_id))
        
        # Step 6: AGE unmatched tracks, delete if too old
        for t in unmatched_tracks:
            self.tracks[t].mark_missed()
            if self.tracks[t].age > self.max_age:
                self.tracks[t].move_to_out_of_view()
```

Each KalmanTrack maintains state [x, y, area, aspect_ratio, dx, dy, da, dr] — position, size, and their velocities. The Kalman filter predicts through occlusion: if a person goes behind a pillar, the filter predicts where they'll emerge. `scipy.optimize.linear_sum_assignment` is built into Python — no external dependencies beyond scipy.

### What Cloud Vision Provides vs What the Brain Tracks

Cloud Vision gives us per-frame:
- Bounding box coordinates (pixels)
- Object label (person, car, table, chair, etc.)
- Confidence score (0.0-1.0)
- Detected text (OCR)

Brain converts and ACCUMULATES:
- Normalized positions (0.0-1.0)
- Clock positions (computed from x-position)
- Distance estimates (computed from object size + type)
- Trajectories (position history across frames)
- Approach velocity (size trend across frames)
- Identity continuity (matching across frames)
- Object permanence (remembering when not visible)

---

## 8. Temporal Intelligence <a name="8-temporal-intelligence"></a>

Temporal intelligence isn't a separate layer. It's woven through EVERYTHING.

### Object Trajectories

Every tracked object has a position history:

```python
object.position_history = [
    (0.33, 0.50, t=0.0),
    (0.35, 0.50, t=1.0),
    (0.38, 0.49, t=2.0),
    (0.42, 0.48, t=3.0),
]
```

From this, the brain computes:
- **Velocity**: dx/dt = 0.03/s rightward, dy/dt = -0.007/s upward
- **Direction**: Moving right and slightly up → approaching from left
- **Prediction**: At t=4.0, should be at approximately (0.45, 0.47)

### Size Trends (Approach Detection)

```python
object.size_history = [
    (4.2%, t=0.0),
    (5.8%, t=1.0),
    (8.1%, t=2.0),
    (12.6%, t=3.0),
]
```

Size growth rate accelerating = object approaching at constant speed (perspective geometry). Brain computes estimated distance and time-to-arrival.

### Environmental Temporal Patterns

- "It's getting more crowded" — object count trending up
- "Lighting is dimming" — brightness trending down
- "People flow left-to-right here" — consistent motion direction
- "Someone passes every 20-30 seconds" — periodic pattern

### Session Temporal Arc

- Total distance walked (estimated from frame changes)
- Total time elapsed
- Number of alerts given and acknowledged
- Environment transitions: outdoor → door → indoor → elevator → different floor
- User's changing needs over time

### Confidence Decay

Everything fades without re-confirmation:

```python
def decay_confidence(self, time_since_confirmation):
    # Fast decay for dynamic objects (people, vehicles)
    if self.is_dynamic:
        half_life = 10.0  # Confidence halves every 10 seconds unseen
    else:
        half_life = 60.0  # Static objects decay slowly
    
    decay = 0.5 ** (time_since_confirmation / half_life)
    self.confidence *= decay
    
    if self.confidence < PRUNE_THRESHOLD:
        self.move_to_archived()  # Still in memory, but not actively tracked
```

---

## 9. The Predict-Verify-Correct Loop <a name="9-predict-verify-correct"></a>

This is the core mechanism of intelligence.

### Step 1: PREDICT

After processing frame N, the brain generates predictions for frame N+1:

```python
predictions = []
for obj in self.tracked_objects:
    pred_pos = obj.extrapolate_position(dt=1.0)
    pred_size = obj.extrapolate_size(dt=1.0)
    predictions.append(Prediction(
        object_id=obj.id,
        predicted_position=pred_pos,
        predicted_size=pred_size,
        confidence=obj.confidence * obj.trajectory_confidence
    ))

# Environmental predictions
predictions.append(Prediction(
    type="environment",
    prediction="lighting should remain stable",
    confidence=0.9
))
```

### Step 2: PERCEIVE

Frame N+1 arrives. Cloud Vision returns bounding boxes. Brain matches objects.

### Step 3: COMPARE

```python
for pred in predictions:
    actual = find_matching_observation(pred.object_id, current_observations)
    
    if actual is None:
        # Object predicted but NOT seen
        pred.result = "MISSING"
        # Could be: left frame, occluded, or prediction was wrong
        
    elif distance(pred.predicted_position, actual.position) < TOLERANCE:
        pred.result = "CONFIRMED"
        # Prediction was right — increase model confidence
        
    else:
        pred.result = "CORRECTED"
        pred.actual_position = actual.position
        pred.error = distance(pred.predicted_position, actual.position)
        # Prediction was wrong — update model
```

### Step 4: CORRECT

```python
if pred.result == "CONFIRMED":
    obj.confidence = min(1.0, obj.confidence + 0.05)
    obj.trajectory_confidence = min(1.0, obj.trajectory_confidence + 0.1)

elif pred.result == "CORRECTED":
    obj.position = pred.actual_position  # Update to reality
    obj.trajectory_confidence *= 0.7  # Trajectory model less reliable
    # Log as episodic event
    self.episodic_memory.add(PredictionFailure(pred, actual))

elif pred.result == "MISSING":
    obj.confidence *= 0.6  # Not confirmed but might still be there
    obj.frames_since_seen += 1
    if obj.frames_since_seen > PATIENCE:
        obj.move_to_out_of_view()  # Still tracked, lower priority
```

### Step 5: LEARN

The prediction errors are the learning signal:

```python
# Accumulate prediction errors for this object type
self.prediction_stats[obj.type].add_error(pred.error)

# If a particular object type is consistently mis-predicted,
# adjust the prediction model for that type
if self.prediction_stats["person"].mean_error > HIGH_ERROR:
    # People in this environment move more erratically than expected
    self.prediction_params["person"].uncertainty_factor *= 1.2
```

### What This Looks Like in Practice

```
Frame 45: Brain predicts person at (0.35, 0.50), size 16.8%
Frame 46: Cloud Vision says person at (0.38, 0.49), size 18.2%
  → CORRECTED: person moved more than predicted
  → Update trajectory: person is accelerating
  → New prediction for Frame 47: person at (0.42, 0.47), size 20.1%

Frame 47: Cloud Vision says person at (0.41, 0.48), size 19.8%
  → CONFIRMED (within tolerance)
  → Trajectory model now more reliable
  → Person is approaching — urgency rising
```

---

## 10. Three Nested Intelligence Loops <a name="10-three-loops"></a>

### Reactive Loop (~1-2 seconds)

**Driven by**: Cloud Vision API  
**Purpose**: Track objects, check urgency, process immediate threats  
**Operations**:
1. Receive Cloud Vision bounding boxes
2. Match against known objects (identity continuity)
3. Update positions, compute trajectories
4. Run predict-verify-compare against last cycle's predictions
5. Check amygdala path: anything approaching fast?
6. If urgency > threshold → push alert to Live session IMMEDIATELY
7. Generate predictions for next frame

**What it DOESN'T do**: Understand scenes, reason about relationships, plan.

### Cognitive Loop (~5-10 seconds)

**Driven by**: Gemini generateContent  
**Purpose**: Understand the environment, enrich the world model, generate intelligent predictions  
**Operations**:
1. Send current frame + world model state to Gemini
2. Receive scene understanding (environment type, activities, relationships, hazards)
3. Update environment model in hippocampus
4. Verify or correct the reactive loop's assumptions
5. Generate cognitive-level predictions ("person is heading toward the exit")
6. Detect hazards the reactive loop can't see (wet floor, glass wall, stairs)
7. Decide if an ambient update is worth mentioning to the user

**What it DOESN'T do**: Fast threat detection, frame-by-frame tracking.

### The Cognitive Loop Prompt — Fully Specified

```python
COGNITIVE_PROMPT = """
You are analyzing a camera frame for a spatial intelligence system.

CURRENT WORLD MODEL:
  Environment: {environment_type} — {environment_description}
  Current place: {current_place} (entered via {entry_direction})
  Tracking {num_objects} objects: {objects_summary}
  Recent places: {place_history}
  Brain predictions to verify: {predictions_to_verify}

Analyze the current frame. Respond ONLY as JSON matching this schema exactly.
"""

COGNITIVE_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "environment_type": {"type": "string"},
        "environment_description": {"type": "string"},
        "place_transition": {
            "type": "string",
            "enum": ["same", "new", "returned"]
        },
        "transition_type": {
            "type": "string",
            "enum": ["door", "turn_left", "turn_right", "stairs_up", "stairs_down",
                     "elevator", "boundary", "none"]
        },
        "transition_direction": {"type": "string"},
        "objects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "activity": {"type": "string"},
                    "distance_estimate": {"type": "string",
                        "enum": ["very_close", "close", "near", "medium", "far", "very_far"]},
                    "relationship": {"type": "string"},
                    "is_hazard": {"type": "boolean"}
                }
            }
        },
        "hazards": {"type": "array", "items": {"type": "string"}},
        "spatial_layout": {"type": "string"},
        "prediction_next_5s": {"type": "string"},
        "text_visible": {"type": "array", "items": {"type": "string"}},
        "key_visual_features": {"type": "array", "items": {"type": "string"}},
        "corrections": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["environment_type", "place_transition", "objects", "spatial_layout"]
}
```

This uses Gemini's `response_schema` parameter — guaranteed JSON structure, every time. The brain gets exactly the fields it expects with no parsing failures.

### Reflective Loop (~30-60 seconds)

**Driven by**: Brain's internal timer  
**Purpose**: Learn, calibrate, optimize  
**Algorithm**: Exponential Moving Averages on 5 key metrics, with parameter adjustment rules.

```python
class ReflectiveLoop:
    def __init__(self):
        self.prediction_accuracy = EMA(initial=0.5)     # How often predictions correct
        self.alert_response_rate = EMA(initial=0.5)      # User acknowledges alerts
        self.alert_dismissal_rate = EMA(initial=0.0)     # User ignores/dismisses
        self.communication_density = EMA(initial=0.0)    # Alerts per minute
        self.alert_threshold = 0.5
        self.verbosity_modifier = 1.0
    
    def run_cycle(self, brain_state):
        # 1. Update metrics from recent predictions and alerts
        recent_preds = brain_state.prediction_history[-30:]
        if recent_preds:
            accuracy = sum(1 for p in recent_preds if p.result == "CONFIRMED") / len(recent_preds)
            self.prediction_accuracy.update(accuracy)
        
        recent_alerts = brain_state.alert_history[-10:]
        if recent_alerts:
            ack = sum(1 for a in recent_alerts if a.user_response == "acknowledged")
            self.alert_response_rate.update(ack / len(recent_alerts))
            dismissed = sum(1 for a in recent_alerts if a.user_response == "dismissed")
            self.alert_dismissal_rate.update(dismissed / len(recent_alerts))
        
        # 2. Adjust alert threshold
        if self.alert_dismissal_rate.value > 0.5:
            self.alert_threshold = min(0.9, self.alert_threshold + 0.05)  # Too noisy → less sensitive
        elif self.alert_response_rate.value > 0.7:
            pass  # Well calibrated — don't change
        elif self.communication_density.value < 0.5:
            self.alert_threshold = max(0.2, self.alert_threshold - 0.03)  # Too quiet → more sensitive
        
        # 3. Adjust verbosity
        if self.communication_density.value > 3.0 and self.alert_dismissal_rate.value > 0.3:
            self.verbosity_modifier = max(0.5, self.verbosity_modifier - 0.1)
        
        # 4. Consolidate episodes → semantic patterns
        new_patterns = brain_state.episode_consolidator.get_recent_promotions()
        brain_state.semantic_memory.extend(new_patterns)
        
        # 5. Prune stale objects and low-relevance episodes
        brain_state.prune_stale_objects()
        brain_state.prune_low_relevance_episodes()

class EMA:
    """Exponential Moving Average — one line of math, online, no batch."""
    def __init__(self, initial=0.0, alpha=0.3):
        self.value = initial
        self.alpha = alpha
    def update(self, new_value):
        self.value = self.alpha * new_value + (1 - self.alpha) * self.value
```

Why EMA: ONE LINE of math (`value = α * new + (1-α) * old`), naturally forgets old data, no batch collection, α=0.3 means recent dominates but history still matters. Every parameter adjustment has a clear, explainable reason.

---

## 11. Decision Engine and Behavioral Dimensions <a name="11-decision-engine"></a>

### Seven Behavioral Dimensions (0.0 to 1.0)

**Vigilance**: How alert is the system? Parking lot = 0.8. Living room = 0.2.

**Verbosity**: How much does it say? Exploring new space = 0.7. Walking a known route = 0.2.

**Detail_focus**: How specific are descriptions? User asked "what's on the sign" = 1.0. Ambient monitoring = 0.3.

**Proactivity**: How often does it speak unprompted? New environment = 0.8. Stable environment = 0.2.

**Urgency**: How fast does it need to respond? Approaching vehicle = 1.0. Static scene = 0.1.

**Social_awareness**: Is the user in a social situation? In conversation = 0.9. Alone = 0.1.

**Exploration**: Is the user exploring or on a known route? First visit = 0.9. Daily commute = 0.1.

### Dimension Computation

Dimensions are COMPUTED from the world model, not set manually:

```python
def compute_vigilance(self):
    factors = [
        self.environment.hazard_level * 0.3,       # Parking lot = high
        self.dynamic_object_count / 10.0 * 0.2,    # More objects = more vigilant
        (1.0 - self.frame_quality) * 0.2,           # Bad visibility = more vigilant
        self.approaching_objects_count / 5.0 * 0.3, # Approaching objects = high
    ]
    return min(1.0, sum(factors))

def compute_urgency(self):
    if not self.tracked_objects:
        return 0.0
    # Highest urgency among all tracked objects
    max_urgency = 0.0
    for obj in self.tracked_objects:
        if obj.is_approaching:
            # Urgency based on time-to-contact
            ttc = obj.estimated_time_to_contact()
            if ttc < 2.0:
                max_urgency = max(max_urgency, 0.95)
            elif ttc < 5.0:
                max_urgency = max(max_urgency, 0.7)
            elif ttc < 10.0:
                max_urgency = max(max_urgency, 0.4)
    return max_urgency
```

### Decision Function

```python
def decide_action(self):
    if self.urgency > 0.8:
        # AMYGDALA PATH — immediate alert, bypass everything
        return Action.ALERT_URGENT
    
    if self.urgency > self.alert_threshold and self.cooldown_expired():
        # Standard alert
        if self.social_awareness > 0.7 and self.urgency < 0.7:
            return Action.WAIT_FOR_CONVERSATION_PAUSE
        return Action.ALERT_NORMAL
    
    if self.should_give_ambient_update():
        return Action.AMBIENT_UPDATE
    
    if self.user_asked_question:
        return Action.ANSWER_QUESTION
    
    return Action.STAY_SILENT  # Default — say nothing
```

### The Alert Threshold

Not fixed. Adjusts based on:
- Environment (lower in dangerous spaces)
- User preference (learned from dismissals vs acknowledgments)
- Recent history (if user dismissed 3 alerts in a row, raise threshold)
- Time of day / fatigue estimation

---

## 12. Purpose, Goals, and Attention <a name="12-purpose-goals-attention"></a>

### Purpose

Set by the domain plugin. Doesn't change during session.

- Navigation mode: "Keep this person spatially safe and informed"
- Security mode: "Detect and track all individuals, report anomalies"
- Shopping mode: "Help find products and navigate the store"

### Goals

Emerge from PURPOSE + WORLD STATE. Not coded — computed:

```python
def generate_goals(self):
    goals = []
    
    # From approaching objects
    for obj in self.tracked_approaching_objects():
        goals.append(Goal(
            type="track_approaching",
            target=obj.id,
            reason=f"{obj.description} approaching from {obj.clock_position}",
            urgency=obj.approach_urgency
        ))
    
    # From user intent
    if self.user_intent == "find_item":
        goals.append(Goal(
            type="find_item",
            target=self.user_target_item,
            reason="User asked where to find something",
            urgency=0.5
        ))
    
    # From environment changes
    if self.environment_just_changed:
        goals.append(Goal(
            type="reorient",
            reason="New environment — help user understand the space",
            urgency=0.6
        ))
    
    # From decision points
    if self.decision_point_detected:
        goals.append(Goal(
            type="help_choose_path",
            reason="Multiple paths available",
            urgency=0.5
        ))
    
    return sorted(goals, key=lambda g: g.urgency, reverse=True)
```

### Attention Direction

Given limited perception (1 FPS, 70° FOV, one camera), what does the brain FOCUS on?

Attention is driven by goals. The brain shapes the cognitive loop's prompt based on what it needs:

```python
def generate_cognitive_query(self):
    queries = []
    
    for goal in self.active_goals[:3]:  # Top 3 goals
        if goal.type == "track_approaching":
            queries.append(f"Is {goal.target_description} still approaching? Speed? Direction?")
        elif goal.type == "find_item":
            queries.append(f"Any signs or labels indicating {goal.target}?")
        elif goal.type == "reorient":
            queries.append("What kind of space is this? Exits? Layout?")
    
    # Always include surprise check
    queries.append("Anything unexpected or potentially hazardous not in my world model?")
    
    return queries
```

---

## 13. Communication Control <a name="13-communication-control"></a>

### The Brain Controls Speech

The Live session is Broca's area — speech production. It doesn't decide what to say. The brain decides:

```python
async def push_to_voice(self, message, urgency):
    if urgency >= 0.8:
        # CRITICAL — suppress VAD to prevent interruption
        await self.live_session.send_realtime_input(
            activity_end=types.ActivityEnd()
        )
    
    alert_text = f"SPATIAL ALERT — say this naturally: {message}"
    
    await self.live_session.send_client_content(
        turns={"role": "user", "parts": [{"text": alert_text}]},
        turn_complete=True
    )
```

### Live Session System Prompt

```
You are the voice of Drishti, a spatial awareness agent. 

ROLE: You receive SPATIAL ALERTS from the backend brain — speak them naturally 
to the user. You hear the user's voice — relay their questions to the backend.

RULES:
1. When you receive a SPATIAL ALERT, speak it concisely and clearly.
2. When the user asks a question, the backend will provide the answer — speak it.
3. You do NOT analyze video frames. You do NOT decide what to say.
4. The backend brain makes all decisions. You are the voice.
5. Adapt your tone: urgent alerts = sharp and clear. 
   Ambient updates = calm and natural. Answers = conversational.
6. Use clock positions and step counts: "Person, 11 o'clock, about 5 steps."
```

### State Injection (survives context compression)

Every 10-15 seconds, brain injects FULL current state:

```python
state = f"""
CURRENT SPATIAL STATE (replaces all previous):
Environment: {self.environment_description}
Tracking {len(self.tracked)} objects:
{self.format_tracked_objects()}
User: {self.user_state}
Recent: {self.last_3_events}
"""

await self.live_session.send_client_content(
    turns={"role": "user", "parts": [{"text": state}]},
    turn_complete=False  # Context only, don't trigger speech
)
```

Always FULL state, never deltas — survives compression.

### Handling User Questions

```
User: "What did I pass earlier?"
  → Live session transcribes
  → Brain receives question
  → Brain checks episodic memory: finds events anchored to places along user's path
  → Brain generates answer: "You passed a bakery sign on your right, and a water fountain on your left"
  → Brain pushes answer to Live session
  → Live session speaks naturally
```

---

## 14. Domain Plugin System <a name="14-domain-plugins"></a>

The cognitive architecture is UNIVERSAL. The intelligence engine — predict-verify loop, memory lifecycle, decision engine, reactive/cognitive/reflective loops — is domain-agnostic. Domain plugins configure WHAT the engine pays attention to, HOW it interprets observations, and WHERE it sends alerts.

### Full Plugin Structure

```python
@dataclass
class DomainPlugin:
    name: str
    purpose: str                        # The agent's mission
    
    # Camera configuration
    camera_type: str                    # "mobile" | "fixed_indoor" | "fixed_outdoor" | "ptz"
    camera_count: int                   # 1 for mobile/baby, N for factory
    
    # Spatial model
    spatial_model_type: str             # "egocentric" (mobile) | "zone_based" (fixed)
    zones: Optional[List[Zone]]         # Defined zones with rules (fixed cameras)
    exclusion_zones: Optional[List[Zone]]  # Zones that trigger alerts on entry
    
    # Tracking model
    tracking_model: str                 # "user_centric" | "single_subject" | "population" | "individual_behavioral"
    primary_subject: Optional[str]      # "user" | "baby" | "resident" | None
    track_objects_of_type: List[str]    # What objects matter
    max_tracked: int                    # Working memory limit for active tracking
    
    # Pattern learning
    pattern_time_scales: List[str]      # ["seconds", "minutes"] | ["hours", "days"] | ["minutes", "shifts"]
    baseline_learning_period: str       # How long before system is calibrated
    deviation_sensitivity: float        # How much deviation triggers concern
    
    # Urgency and alerts
    alert_threshold: float              # When to alert
    social_override_threshold: float    # When to interrupt conversation
    critical_events: List[CriticalEventDef]  # Domain-specific critical events
    urgency_rules: List[UrgencyRule]    # How urgency is computed
    dimension_weights: dict             # Weight adjustments for behavioral dimensions
    
    # Communication
    output_modalities: List[str]        # ["voice"] | ["push_notification"] | ["dashboard", "pa_system"]
    alert_recipients: List[str]         # Who gets alerts
    voice_enabled: bool                 # Whether voice I/O is used
    vocabulary: dict                    # Domain-specific language
    system_prompt_addendum: str         # Added to Live session prompt
    
    # Onboarding
    onboarding_type: str                # "self_discovering" | "guided_setup"
    
    # Privacy
    privacy_level: str                  # "maximum" | "high" | "standard"
    data_retention_days: int
    blur_faces: bool
```

### Mobile Camera Plugins

**Navigator (Blind Navigation)**

```python
navigator = DomainPlugin(
    name="Navigator",
    purpose="Keep the user spatially safe and informed",
    camera_type="mobile",
    camera_count=1,
    spatial_model_type="egocentric",
    zones=None,  # No predefined zones — everything relative to user
    tracking_model="user_centric",
    primary_subject="user",
    track_objects_of_type=["person", "vehicle", "door", "stairs", "obstacle", "sign"],
    max_tracked=7,
    pattern_time_scales=["seconds", "minutes"],
    baseline_learning_period="30_seconds",
    deviation_sensitivity=0.5,
    alert_threshold=0.5,
    social_override_threshold=0.7,
    critical_events=[
        CriticalEventDef("fast_approaching_object", urgency=0.95),
        CriticalEventDef("collision_course", urgency=1.0),
        CriticalEventDef("ground_hazard", urgency=0.7),
        CriticalEventDef("elevation_change", urgency=0.6),
    ],
    dimension_weights={"vigilance": 1.2, "social_awareness": 1.0},
    output_modalities=["voice"],
    alert_recipients=["user_earbuds"],
    voice_enabled=True,
    vocabulary={"approaching": "coming toward you", "receding": "moving away"},
    onboarding_type="self_discovering",
    privacy_level="standard",
    data_retention_days=30,
    blur_faces=False,
)
```

**Shopping Companion**

```python
shopping = DomainPlugin(
    name="Shopping Companion",
    purpose="Help find products and navigate the store",
    camera_type="mobile",
    camera_count=1,
    spatial_model_type="egocentric",
    tracking_model="user_centric",
    primary_subject="user",
    track_objects_of_type=["sign", "shelf_label", "product", "price_tag", "person", "cart"],
    max_tracked=7,
    pattern_time_scales=["seconds", "minutes"],
    baseline_learning_period="30_seconds",
    deviation_sensitivity=0.5,
    alert_threshold=0.6,
    social_override_threshold=0.8,
    critical_events=[
        CriticalEventDef("item_found", urgency=0.6),
        CriticalEventDef("cart_approaching", urgency=0.5),
    ],
    dimension_weights={"exploration": 1.3, "detail_focus": 1.2},
    output_modalities=["voice"],
    alert_recipients=["user_earbuds"],
    voice_enabled=True,
    vocabulary={"section": "department", "sign": "label"},
    onboarding_type="self_discovering",
    privacy_level="standard",
    data_retention_days=30,
    blur_faces=False,
)
```

### Stationary Camera Plugins

**Baby Guardian**

```python
baby_monitor = DomainPlugin(
    name="Baby Guardian",
    purpose="Monitor baby safety and sleep patterns",
    camera_type="fixed_indoor",
    camera_count=1,
    spatial_model_type="zone_based",
    zones=[
        Zone("crib", rules=["alert_if_subject_exits", "track_posture", "track_sleep_state"]),
        Zone("play_area", rules=["normal_activity_zone", "track_activity_level"]),
        Zone("floor_near_door", rules=["critical_if_baby_detected"]),
        Zone("window_area", rules=["critical_if_baby_detected"]),
    ],
    tracking_model="single_subject",
    primary_subject="baby",
    track_objects_of_type=["person_small", "toy", "blanket", "bottle"],
    max_tracked=5,
    pattern_time_scales=["hours", "days"],
    baseline_learning_period="7_days",
    deviation_sensitivity=0.4,
    alert_threshold=0.3,
    social_override_threshold=1.0,  # No social override — baby room
    critical_events=[
        CriticalEventDef("baby_out_of_crib", urgency=1.0),
        CriticalEventDef("baby_face_covered", urgency=0.9),
        CriticalEventDef("unusual_posture_prolonged", urgency=0.7),
        CriticalEventDef("crying_beyond_normal_duration", urgency=0.5),
        CriticalEventDef("baby_awake_unusual_time", urgency=0.4),
        CriticalEventDef("no_movement_prolonged", urgency=0.8),
    ],
    urgency_rules=[
        UrgencyRule("posture_change", "baby was lying, now standing in crib → 0.6"),
        UrgencyRule("zone_exit", "baby exits crib zone → 1.0"),
        UrgencyRule("face_obstruction", "blanket over face area → 0.9"),
        UrgencyRule("sleep_deviation", "awake 2+ hours before normal → 0.4"),
    ],
    dimension_weights={"vigilance": 1.5, "proactivity": 1.3},
    output_modalities=["push_notification", "in_app_alert"],
    alert_recipients=["parent_phone"],
    voice_enabled=False,
    vocabulary={"subject": "baby", "primary_zone": "crib"},
    onboarding_type="guided_setup",
    privacy_level="maximum",
    data_retention_days=30,
    blur_faces=False,
)
```

**Elder Guardian**

```python
elderly_care = DomainPlugin(
    name="Elder Guardian",
    purpose="Monitor elderly resident safety and daily routine",
    camera_type="fixed_indoor",
    camera_count=3,  # Living room, bedroom, kitchen
    spatial_model_type="zone_based",
    zones=[
        Zone("armchair", rules=["track_sitting_duration", "track_posture"]),
        Zone("bed", rules=["track_sleep_pattern", "track_entry_exit"]),
        Zone("kitchen_stove", rules=["alert_if_unattended_with_activity"]),
        Zone("bathroom_entrance", rules=["track_frequency", "track_duration"]),
        Zone("medicine_cabinet", rules=["track_schedule_compliance"]),
        Zone("entrance_door", rules=["track_visitors", "track_exits"]),
        Zone("floor_any", rules=["critical_if_person_lying"]),
    ],
    tracking_model="single_subject",
    primary_subject="resident",
    track_objects_of_type=["person", "walker", "wheelchair", "visitor"],
    max_tracked=5,
    pattern_time_scales=["hours", "days", "weeks"],
    baseline_learning_period="14_days",
    deviation_sensitivity=0.3,
    alert_threshold=0.3,
    social_override_threshold=1.0,
    critical_events=[
        CriticalEventDef("fall_detected", urgency=1.0),
        CriticalEventDef("prolonged_inactivity", urgency=0.7, params={"threshold_hours": 3}),
        CriticalEventDef("missed_medication_time", urgency=0.5),
        CriticalEventDef("unusual_night_activity", urgency=0.4),
        CriticalEventDef("unknown_visitor", urgency=0.4),
        CriticalEventDef("routine_deviation_multiday", urgency=0.6),
        CriticalEventDef("stove_unattended", urgency=0.8),
        CriticalEventDef("didnt_wake_by_expected_time", urgency=0.5),
    ],
    urgency_rules=[
        UrgencyRule("fall", "person on floor + no recovery in 30s → 1.0"),
        UrgencyRule("inactivity", "no movement > 3 hours while not in bed → 0.7"),
        UrgencyRule("stove_safety", "stove zone active + kitchen zone empty > 15 min → 0.8"),
        UrgencyRule("medication", "no cabinet interaction within 1 hour of usual time → 0.5"),
        UrgencyRule("sleep_deviation", "not in bed 2+ hours past usual bedtime → 0.4"),
    ],
    dimension_weights={"vigilance": 1.0, "proactivity": 0.8},
    output_modalities=["push_notification", "voice_in_room", "caregiver_dashboard"],
    alert_recipients=["family_app", "caregiver_app"],
    voice_enabled=True,  # Two-way: "Mrs. Sharma, are you doing alright?"
    vocabulary={"subject": "resident", "alert_tone": "gentle_concerned"},
    onboarding_type="guided_setup",
    privacy_level="high",
    data_retention_days=90,
    blur_faces=False,
)
```

**Factory Intelligence**

```python
factory_safety = DomainPlugin(
    name="Factory Intelligence",
    purpose="Worker safety, process flow monitoring, compliance",
    camera_type="fixed_indoor",
    camera_count=12,
    spatial_model_type="zone_based",
    zones=[
        Zone("station_A", rules=["track_cycle_time", "track_worker_posture"]),
        Zone("station_B", rules=["track_cycle_time", "track_worker_posture"]),
        Zone("station_C", rules=["track_cycle_time", "track_worker_posture"]),
        Zone("station_D", rules=["track_cycle_time", "track_worker_posture"]),
        Zone("aisle_main", rules=["track_traffic_flow", "track_forklift_pedestrian"]),
        Zone("loading_dock", rules=["track_vehicle_activity"]),
        Zone("chemical_storage", rules=["require_ppe_gloves_goggles"]),
        Zone("break_area", rules=["track_break_frequency"]),
    ],
    exclusion_zones=[
        Zone("press_machine_exclusion", rules=["critical_on_entry"], radius_meters=2.0),
        Zone("robot_arm_zone", rules=["critical_on_entry"], radius_meters=3.0),
    ],
    tracking_model="population",
    primary_subject=None,  # Track everyone equally
    track_objects_of_type=["person", "forklift", "pallet", "work_item", "ppe_helmet", "ppe_gloves"],
    max_tracked=50,
    pattern_time_scales=["minutes", "hours", "shifts"],
    baseline_learning_period="3_shifts",
    deviation_sensitivity=0.5,
    alert_threshold=0.4,
    social_override_threshold=1.0,
    critical_events=[
        CriticalEventDef("forklift_pedestrian_collision_predicted", urgency=1.0),
        CriticalEventDef("exclusion_zone_violation", urgency=0.9),
        CriticalEventDef("worker_fall", urgency=0.9),
        CriticalEventDef("ppe_violation_in_required_zone", urgency=0.7),
        CriticalEventDef("process_stall", urgency=0.5, params={"threshold_multiplier": 3.0}),
        CriticalEventDef("repetitive_motion_prolonged", urgency=0.4, params={"threshold_minutes": 30}),
        CriticalEventDef("unauthorized_off_hours_access", urgency=0.8),
    ],
    urgency_rules=[
        UrgencyRule("trajectory_collision", "two object trajectories intersect within 5s → 1.0"),
        UrgencyRule("zone_approach", "trajectory toward exclusion zone → urgency rises with proximity"),
        UrgencyRule("stall", "work_item stationary > 3x normal cycle time → 0.5"),
        UrgencyRule("ppe_check", "person in chemical zone without required PPE → 0.7"),
        UrgencyRule("off_hours", "person detected during off hours → 0.8"),
        UrgencyRule("ergonomic", "same posture > 30 minutes → 0.4"),
    ],
    dimension_weights={"vigilance": 1.5, "social_awareness": 0.1},
    output_modalities=["supervisor_display", "pa_system", "push_notification", "machine_api"],
    alert_recipients=["floor_supervisor", "safety_manager", "shift_lead"],
    voice_enabled=False,
    vocabulary={"person": "worker", "approaching": "heading toward"},
    onboarding_type="guided_setup",
    privacy_level="standard",
    data_retention_days=365,
    blur_faces=True,  # Worker privacy
)
```

---

## 15. Deployment Patterns — Self-Discovering vs Guided Setup <a name="15-deployment-patterns"></a>

Every deployment goes through three phases: DISCOVERY → BASELINE → MONITORING. But how the system enters these phases depends on whether a sighted operator is available.

### Two Onboarding Patterns

**Self-Discovering (Mobile Camera / Blind Navigation)**: No operator. The user can't see. The system figures out EVERYTHING on its own — environment type, what matters, what's dangerous, the layout. PURPOSE is pre-set ("keep me safe") but everything else is emergent.

**Guided Setup (Stationary Camera)**: A sighted operator is present for setup. They can see the screen, point at zones, confirm the system's proposals. The system does the heavy lifting — proposes zones, identifies objects, suggests monitoring rules — but the operator confirms and corrects.

### Three Deployment Phases

```python
class DeploymentPhase:
    DISCOVERY = "discovery"      # Understand the space
    BASELINE = "baseline"        # Learn what's normal
    MONITORING = "monitoring"    # Detect anomalies, maintain safety
```

### Phase 1: Discovery

**Self-Discovering Mode (Blind Navigation)**:

```python
async def run_self_discovery(self):
    """No operator. Discover everything silently."""
    
    # Boot sequence: stages 0-3 (10-15 seconds)
    await self.boot_sequence.wait_until_operational()
    
    # Cognitive loop has classified environment
    env = self.world_model.environment_type
    
    # Select plugin based on environment + stated purpose
    plugin = self.auto_select_plugin(
        user_purpose=self.user_stated_purpose,
        environment=env
    )
    self.world_model.configure(plugin)
    
    # Announce to user
    await self.push_to_voice(
        f"I can see we're in {env}. Tracking {len(self.tracked_objects)} objects. Ready.",
        urgency=0.3
    )
    
    # Skip baseline — pedestrian environments change too fast
    self.transition_to(DeploymentPhase.MONITORING)
```

**Guided Setup Mode (Stationary Camera)**:

```python
async def run_guided_discovery(self):
    """Operator present. System proposes, operator confirms."""
    
    # Step 1: Analyze scene with no prior model
    analysis = await self.cognitive_loop.analyze_fresh_scene(
        prompt="""Analyze this camera view for setting up a monitoring system.
        Return JSON: {
            "space_type": "description of space",
            "proposed_zones": [{"name", "description", "bbox", "monitoring_rules"}],
            "key_objects": ["list of important objects"],
            "suggested_monitoring": ["what to watch for"],
            "questions_for_operator": ["what to clarify"]
        }"""
    )
    
    # Step 2: Present proposal to operator
    # (via web app with Canvas overlay — see Zone Editor below)
    proposal = format_proposal(analysis)
    await self.communicate_to_operator(proposal)
    # Example output:
    # "I can see a room with a crib in the center, a changing table 
    #  on the right, and a play mat on the left. Is this a baby's room?"
    
    # Step 3: Operator confirms/corrects
    operator_response = await self.wait_for_operator_input()
    confirmed_config = self.apply_corrections(analysis, operator_response)
    # Operator might say: "Yes, and the area near the window is dangerous too"
    
    # Step 4: Initialize world model
    self.world_model.initialize_from_config(confirmed_config)
    
    # Step 5: Transition to baseline learning
    await self.communicate_to_operator(
        f"Setup complete. Monitoring {len(confirmed_config.zones)} zones. "
        f"I'll learn normal patterns over the next {self.plugin.baseline_learning_period}. "
        f"Safety alerts are active immediately."
    )
    self.transition_to(DeploymentPhase.BASELINE)
```

### Zone Configuration UI — Canvas Overlay Editor

For stationary cameras, the operator needs to SEE proposed zones on the live camera feed and adjust them visually. The setup app uses an HTML5 Canvas overlay:

```
┌─────────────────────────────────────────┐
│  CAMERA FEED (live)                      │
│                                          │
│  ┌──────────┐                            │
│  │ ZONE: Crib│  (blue overlay, 25% opacity)
│  │  ○drag    │  ← draggable corner handles
│  │   corners○│                           │
│  └──────────┘                            │
│                    ┌─────────────────┐   │
│                    │ ZONE: Play Area │   │
│                    │ (green overlay) │   │
│                    └─────────────────┘   │
│                                          │
│  [Accept Zones]  [Add Zone]  [Reset]     │
└─────────────────────────────────────────┘
```

The `ZoneEditor` component renders the camera feed on a canvas, draws Gemini's proposed zones as colored semi-transparent polygons, and lets the operator drag corners to adjust boundaries, tap to add/remove zones, and edit zone names and rules. Zone types have distinct colors: green (safe/normal), blue (monitored), red (danger/alert), orange (exclusion/forbidden).

When the operator confirms, zones are exported as normalized coordinates (0.0-1.0 range, resolution-independent) and saved to the domain plugin configuration. The same ZoneEditor works for baby rooms (crib zone, play zone, danger zone), elderly homes (chair zone, kitchen zone, bathroom zone), and factories (station zones, aisle zones, exclusion zones) — only colors, labels, and default rules differ per plugin.

### Phase 2: Baseline Learning

During baseline, the system watches and learns what NORMAL looks like. No alerts except for critical safety events.

```python
class BaselineLearner:
    def __init__(self, plugin):
        self.start_time = time.time()
        self.target_duration = parse_duration(plugin.baseline_learning_period)
        self.patterns_discovered = []
        self.confidence = 0.0
    
    def process_observation(self, world_model_state):
        """Called every cognitive cycle during baseline."""
        
        # Accumulate temporal patterns
        for zone in self.zones:
            zone.record_activity(
                occupancy=world_model_state.zone_occupancy(zone.name),
                time_of_day=current_time_of_day(),
                day_of_week=current_day_of_week()
            )
        
        # Track subject patterns (baby sleep schedule, elderly routine)
        if self.primary_subject:
            self.subject_tracker.record(
                state=world_model_state.subject_state,
                zone=world_model_state.subject_zone,
                timestamp=time.time()
            )
        
        # Check if baseline is complete
        elapsed = time.time() - self.start_time
        self.confidence = min(1.0, elapsed / self.target_duration)
        
        if self.confidence >= 0.8:
            self.extract_patterns()
    
    def extract_patterns(self):
        """Convert accumulated observations into semantic patterns."""
        patterns = []
        
        # Subject routine (elderly: "wakes 6-7am, tea at 7:30, chair by 8")
        if self.subject_tracker:
            routine = self.subject_tracker.extract_daily_routine()
            for event in routine:
                patterns.append(SemanticPattern(
                    pattern=f"Subject usually {event.description} at {event.typical_time}",
                    confidence=event.consistency,
                    supporting_evidence=event.observation_count
                ))
        
        # Zone patterns (factory: "Station A cycle time ~3 minutes")
        for zone in self.zones:
            zone_pattern = zone.extract_typical_activity()
            if zone_pattern:
                patterns.append(zone_pattern)
        
        self.patterns_discovered = patterns
    
    def report_to_operator(self):
        """Tell operator what was learned."""
        return (
            f"Baseline learning {self.confidence:.0%} complete. "
            f"Discovered {len(self.patterns_discovered)} patterns.\n"
            + "\n".join(f"  - {p.pattern}" for p in self.patterns_discovered[:10])
        )
```

**Baseline duration varies by domain:**

| Domain | Baseline Period | Why |
|---|---|---|
| Blind navigation | 30 seconds | Just spatial layout, pedestrian patterns change constantly |
| Baby monitor | 3-7 days | Need to learn sleep schedule, activity patterns |
| Elderly care | 7-14 days | Full daily routine, medication times, visitor patterns |
| Factory | 3 shifts | Production cycle, staffing pattern, traffic flow |

### Phase 3: Autonomous Monitoring

After baseline, the system monitors continuously. Every observation is compared against learned patterns. Deviations generate alerts. Patterns continue to be refined.

```python
class AutonomousMonitor:
    def evaluate_observation(self, current_state):
        """Called every reactive cycle during monitoring phase."""
        
        # Check critical safety (always, regardless of patterns)
        for critical in self.plugin.critical_events:
            if critical.check(current_state):
                self.alert(critical.urgency, critical.description)
                return
        
        # Check deviation from baseline patterns
        for pattern in self.semantic_memory:
            deviation = pattern.measure_deviation(current_state)
            if deviation > self.plugin.deviation_sensitivity:
                self.handle_deviation(pattern, deviation, current_state)
        
        # Check zone rules
        for zone in self.zones:
            violations = zone.check_rules(current_state)
            for v in violations:
                self.alert(v.urgency, v.description)
    
    def handle_deviation(self, pattern, deviation, current_state):
        """Decide what to do about a pattern deviation."""
        
        # First few deviations: note but don't alert (could be new normal)
        pattern.record_deviation(deviation)
        
        if pattern.deviation_is_persistent():
            # Pattern might be changing — alert operator
            self.alert(
                urgency=0.4,
                message=f"Pattern change: {pattern.pattern} — "
                        f"deviation for {pattern.consecutive_deviations} cycles"
            )
        elif deviation > 0.8:
            # Major single deviation — alert
            self.alert(
                urgency=0.6,
                message=f"Unusual: {pattern.describe_deviation(current_state)}"
            )
```

### Goal Engine Across Phases

```python
class GoalEngine:
    def generate_goals(self):
        if self.phase == DeploymentPhase.DISCOVERY:
            return [
                Goal("identify_environment", "Classify this space"),
                Goal("detect_zones", "Find meaningful spatial zones"),
                Goal("identify_key_objects", "What matters here"),
                Goal("propose_configuration", "Present setup to operator"),
            ]
        
        elif self.phase == DeploymentPhase.BASELINE:
            return [
                Goal("learn_temporal_patterns", "Build baseline of normal"),
                Goal("calibrate_thresholds", "What activity levels are normal"),
                Goal("detect_critical_safety", "Still alert on falls/collisions"),
                Goal("report_learning", "Tell operator what I've learned"),
            ]
        
        elif self.phase == DeploymentPhase.MONITORING:
            return [
                Goal("detect_deviations", "Alert on abnormal patterns"),
                Goal("track_safety", "Continuous safety monitoring"),
                Goal("refine_patterns", "Keep improving baseline"),
                Goal("periodic_summary", "Report to operator daily/weekly"),
            ]
```

---

## 16. Stationary Camera Use Cases <a name="16-stationary-use-cases"></a>

### What Changes with a Fixed Camera

| Aspect | Mobile Camera | Fixed Camera |
|---|---|---|
| Spatial model | Egocentric (clock positions, relative to user) | Zone-based (absolute positions in frame) |
| Camera moves | Yes (user walks) | No (fixed mount) |
| Background | Changes every frame | Stable — enables background subtraction |
| Distance estimation | From object size (unreliable) | From fixed perspective (calibratable) |
| Primary value | Real-time safety for user | Pattern learning + anomaly detection |
| Time scale | Seconds to minutes | Hours to weeks |
| "Normal" definition | Doesn't exist — every moment is new | Learned over days/weeks from patterns |

### Use Case: Baby Guardian

**What today's baby monitors give you**: Video feed you stare at. Cry detection. Motion alerts. The parent is the intelligence.

**What the world model adds**: The system UNDERSTANDS the baby's state, tracks patterns, predicts what should happen next, and alerts when reality deviates.

**Key scenarios the brain handles:**

**Baby standing in crib**: Not just "motion detected" — posture classification. Baby went from lying to standing. A 10-month-old standing in a crib might attempt to climb the railing. Urgency depends on age context (if provided during setup).

**Crying duration tracking**: Baby cries. System tracks duration. This baby usually self-soothes in 2 minutes. At 4 minutes, alert: "Baby has been crying for 4 minutes, longer than usual." At 8 minutes: elevated urgency.

**Sleep pattern deviation**: Baby usually wakes at 6am. Woke at 4am today. Informational alert. If this happens 3 days in a row, the system notes a pattern shift: "Baby's wake time has shifted earlier this week."

**Baby exits crib**: Object permanence + zone tracking. Baby was IN crib zone, now detected OUTSIDE. CRITICAL alert. A dumb motion detector can't distinguish "moving in crib" from "on the floor."

**Object interaction**: Baby threw the stuffed bear out of the crib. Bear detected leaving crib zone. Then baby cries. System connects: "Baby lost comfort object, then started crying. Probable cause."

**Predict-verify loop**: "Baby lay down 3 minutes ago after feeding. Based on pattern: should fall asleep within 10 minutes." At 12 minutes still moving → "Taking longer than usual to settle tonight."

### Use Case: Elder Guardian

**What today's systems give you**: Medical alert pendant (must be pressed). Occasional wellness check calls. Nothing proactive.

**What the world model adds**: Continuous understanding of the resident's routine, with alerts on meaningful deviations.

**Key scenarios:**

**Fall detection with context**: Not just "person on floor" — the brain knows WHERE (bathroom doorway = tripping hazard), WHEN (3am = nighttime bathroom trip), and WHAT HAPPENED BEFORE (was walking normally then suddenly on floor = fall, vs slowly lay down on floor = intentional). If on floor for 30+ seconds without getting up → CRITICAL alert with automatic call to caregiver.

**Daily routine monitoring across weeks**: System learns: wakes 6-7am, tea at 7:30, chair by 8, lunch at 12:30, nap 2-3pm, dinner at 6, bed by 10pm. One day mother doesn't get up until 9am — informational. Three days in a row sleeping until 10am — pattern shift alert: "Your mother's routine has shifted. She's been waking 2-3 hours later than usual this week."

**Stove safety**: Resident turned on stove (activity in kitchen stove zone), then went to living room. 20 minutes pass, no return to kitchen. Alert: "Stove may be on with nobody in the kitchen. Last kitchen activity was 20 minutes ago."

**Medication compliance**: System learns when resident visits medicine cabinet (8am and 8pm daily). Today, 9am and no cabinet visit. Gentle voice: "Mrs. Sharma, have you taken your morning medication?" If no cabinet visit by 10am → push alert to family.

**Visitor tracking**: System knows the usual visitors — caregiver (weekday mornings), daughter (weekends). Unknown person at the door on a Tuesday afternoon → informational alert to family: "Unfamiliar visitor at 2pm today."

**Two-way voice**: For non-emergency deviations, the system can speak directly to the resident: "You've been in your chair for 4 hours. Would you like to get up and walk around?" This requires the Live API voice session — the same architecture as blind navigation, but with a different purpose.

### Use Case: Factory Intelligence

**What today's factory cameras give you**: Recorded footage nobody watches. Specialized single-purpose systems (hard hat detection only, exclusion zone beams only). No holistic understanding.

**What the world model adds**: Understanding the RHYTHM of the factory floor and alerting when the rhythm breaks.

**Key scenarios:**

**Forklift-pedestrian conflict prediction**: Both tracked with trajectories. Brain computes: "Forklift heading south on Aisle 3 at 8 km/h. Worker stepping out of Station D into Aisle 3. Trajectories intersect in ~4 seconds." ALERT 4 seconds BEFORE the collision, not when the beam breaks. Graduated: approach warning → imminent collision → emergency stop signal to forklift.

**Exclusion zone with trajectory prediction**: Worker approaches Machine B. Today's system: alarm when they cross a line. World model: tracks trajectory and predicts "Worker heading toward Machine B exclusion zone. Time to boundary: 3 seconds" → preemptive warning. If worker stops at tool rack nearby (trajectory corrected) → no alarm. Eliminates false alarms that plague beam-break systems.

**Process flow monitoring**: Brain learns: parts spend ~3 minutes at Station A, ~4 minutes at Station B, ~2 minutes at Station C. Part at Station B for 12 minutes → "Process stall at Station B. Worker appears idle. This station has blocked downstream flow to Station C for 8 minutes." Supervisor gets actionable intelligence, not just "motion detected."

**PPE temporal compliance**: Not snapshot "is person wearing hard hat" — but "Worker at Station D removed gloves at 10:15am while working in chemical zone. Gloves required in this zone. PPE violation ongoing for 20 minutes." Temporal tracking transforms spot-check into continuous compliance.

**Ergonomic monitoring**: Cognitive loop (Gemini) analyzes worker posture: "Worker at Station A in repetitive bending motion for 45 minutes. Regulatory guidelines recommend breaks every 30 minutes." Alert to supervisor: "Recommend break for worker at Station A."

**Off-hours security**: 3am Sunday. Factory closed. Person detected. World model knows: cleaning crew at 6am, security rounds at 2am and 4am. This is neither. "Unauthorized person detected at 3am, moving toward equipment storage area."

### What These Use Cases Prove About the Architecture

**Detection Reliability Assessment (Honest)**:

| Detection Type | Method | Reliability | Works Because |
|---|---|---|---|
| Zone occupancy (in/out) | Cloud Vision bbox vs zone polygon | HIGH | Pure geometry — point-in-polygon |
| Object approaching | SORT tracker + size trend | HIGH | Math on bounding box sequences |
| Object dwell time | Timer on zone occupancy | HIGH | Simple counter |
| Person on floor (fall) | Bbox aspect ratio shift (tall→wide) + floor zone | MEDIUM-HIGH | Strong geometric signal |
| Posture classification | Gemini cognitive loop reasoning | MEDIUM | Needs multiple frames, 5-10s delay |
| Behavior inference | Gemini cognitive loop | MEDIUM | "Walking toward" vs "standing" |
| PPE detection | Cloud Vision label detection | LOW | Needs specialized models for production |
| Specific object identification | Gemini cognitive + Cloud Vision | MEDIUM | Works for distinctive objects, fails for generic |

**The pattern**: Zone-based detections (occupancy, violations, dwell time) are highly reliable because they're pure geometry on Cloud Vision bounding boxes. Posture/behavior detections need the cognitive loop and are medium reliability. Specialized detections (PPE, specific postures) need domain-specific models in production but Gemini approximates for demo.

**Fall detection algorithm** (works from Cloud Vision alone):

```python
def detect_fall(self, person_track):
    if len(person_track.aspect_ratio_history) < 6:
        return False
    was_upright = any(ar > 1.3 for ar in person_track.aspect_ratio_history[-6:-3])
    now_horizontal = all(ar < 0.9 for ar in person_track.aspect_ratio_history[-3:])
    on_floor = person_track.position_y > 0.7  # Lower 30% of frame
    return was_upright and now_horizontal and on_floor
```

The intelligence engine — predict-verify-correct, memory lifecycle, reactive/cognitive/reflective loops, decision engine — is the SAME across all six use cases (navigator, shopping, security, baby, elderly, factory). What changes per domain:

1. **Spatial model shape**: Egocentric (mobile) vs zone-based (fixed)
2. **What gets tracked**: One user, one baby, one resident, 50 workers + vehicles
3. **What counts as urgent**: Approaching person vs baby on floor vs trajectory collision
4. **Time scale of patterns**: Seconds (navigation) vs days (baby sleep) vs shifts (factory cycle)
5. **How alerts are delivered**: Voice vs push notification vs display + PA system
6. **Who receives alerts**: The user themselves vs remote caregiver vs floor supervisor
7. **Onboarding**: Self-discovering vs guided setup

---

## 17. Session Lifecycle — Cold Start, Warm Start, Shutdown <a name="17-session-lifecycle"></a>

### The Cold Start Problem

When the system boots, the world model is EMPTY. The first 10-15 seconds are dangerous — the system is building its model while the user may already be in a dynamic environment.

### Boot Sequence (4 Stages)

```python
class BootSequence:
    BLIND = 0        # T=0-0.5s — No data at all
    SEEING = 1       # T=0.5-3s — Bounding boxes arriving, no trajectories
    TRACKING = 2     # T=3-10s — Trajectories emerging, low confidence
    OPERATIONAL = 3  # T=10-15s — Reliable predictions, normal mode
    
    stage: int = BLIND
    stage_start_time: float
    
    def can_give_safety_alert(self) -> bool:
        if self.stage <= self.SEEING:
            return False  # Can't track motion yet
        return True       # Stage 2+: alerts with lower threshold
    
    def alert_threshold_modifier(self) -> float:
        if self.stage == self.TRACKING:
            return 0.7   # Lower threshold = more sensitive during boot
        return 1.0        # Normal operation
    
    def should_announce_status(self) -> bool:
        return self.stage < self.OPERATIONAL
```

**Stage 0 — BLIND (T=0-0.5s)**: No data. System announces: "Starting up. Give me a moment." Cannot provide any spatial information.

**Stage 1 — SEEING (T=0.5-3s)**: First Cloud Vision results arrive. Brain sees bounding boxes but has zero history. Can detect PRESENCE ("3 objects in the scene") but not BEHAVIOR (approaching? stationary?). The one-shot function call from the Live session fires here — if it succeeds, the brain gets a rich initial inventory (objects, positions, environment type) that accelerates boot significantly.

**Stage 2 — TRACKING (T=3-10s)**: 3-10 frames of data. Trajectories emerging but noisy. Brain can detect gross motion (something getting much bigger = definitely approaching) but can't predict precise speeds. Alert threshold is LOWER — false alarms acceptable while calibrating. First cognitive loop runs (~T=5-7s), environment classified.

**Stage 3 — OPERATIONAL (T=10-15s)**: Enough data for reliable trajectories. Predictions verified against reality. Confidence scores calibrated. System transitions to normal mode.

### Warm Start (Returning to Known Space)

When Firestore has data for a recognized place, boot is dramatically faster:

```
T=0s:    Session starts. First frame sent to Cloud Vision + cognitive loop.
T=0.5s:  Cloud Vision returns. OCR detects text ("Whole Foods #247").
         Place Recognition matches against Firestore → HIT.
T=0.7s:  Load cached data: cognitive map, landmarks, patterns, user profile.
         Brain ALREADY knows layout, traffic patterns, hazard zones.
T=1-2s:  Match current Cloud Vision objects against cached landmarks.
         Static objects confirmed → high confidence immediately.
T=2-3s:  Skip to Stage 2 or Stage 3. Only dynamic objects need fresh tracking.
```

Warm start cuts boot from 15 seconds to 2-3 seconds. The system announces: "I remember this space. [Place name]. The layout hasn't changed since last time."

### Session End and Persistence

**Detection**: Session ends when Live API disconnects, user says "goodbye", audio goes silent for 60+ seconds, or app is backgrounded.

**What SAVES to Firestore**:

```python
async def handle_session_end(self):
    # Consolidate episodes into semantic patterns
    new_patterns = self.consolidate_episodes()
    self.semantic_memory.extend(new_patterns)
    
    # Build/update place record
    place = self.current_place_record or PlaceRecord.create_new()
    place.cognitive_map = self.cognitive_map
    place.static_landmarks = self.extract_static_landmarks()
    place.semantic_patterns = self.semantic_memory
    place.text_signatures = self.collected_text_signatures
    place.description = self.world_model.environment_description
    place.visit_count += 1
    place.last_visited = datetime.now()
    place.total_time_spent += self.session_duration()
    
    # Save user profile
    self.user_profile.update_from_session(
        walking_speed=self.measured_walking_speed,
        alert_response_rate=self.alert_acknowledgment_rate,
        preferred_verbosity=self.inferred_verbosity_preference,
        threshold_calibration=self.current_alert_threshold
    )
    
    await self.firestore.save_place(place)
    await self.firestore.save_user_profile(self.user_profile)
    
    await self.push_to_voice(
        "Session ending. I've saved what I learned about this space.",
        urgency=0.3
    )
```

**What DIES with the session** (not persisted):
- Currently tracked dynamic objects (people are gone by next visit)
- Active goals (resolved or abandoned)
- Working memory contents (momentary)
- Uncommitted individual episodic events (too granular)
- Trajectory predictions (stale)
- Real-time urgency state

**What SAVES WITH EXPIRY** (useful but becomes stale):
- "Checkout line was long at 5pm" — relevant if next visit is similar time
- "Construction blocking aisle 3" — temporary, might resolve
- These get a `valid_until` timestamp and are pruned on next load

---

## 18. Place Recognition <a name="18-place-recognition"></a>

### The Problem

When the system starts, how does it know if it's in a place it's been before? Without GPS (unreliable indoors), without beacons, without pre-mapped spaces — only the camera feed.

### Three Recognition Signals

**Signal 1 — Text Matching (Fastest, Most Reliable)**

Cloud Vision OCR detects text in early frames: store names, aisle numbers, building placards, room numbers. Text is unique and unambiguous. "Whole Foods Market, Store #247" maps to exactly one place with high confidence.

**Signal 2 — Environment + Visual Feature Matching (Medium)**

Cognitive loop classifies environment ("grocery store, narrow aisles") and identifies visual features ("blue-green color scheme, wooden shelves"). Matched against stored environment signatures. Less unique — many grocery stores look similar — but combined with text fragments, confidence rises.

**Signal 3 — Scene Description Similarity (No Graph Matching)**

Instead of comparing topological graphs (NP-hard), compare SCENE DESCRIPTIONS as text strings. When the cognitive loop classifies a space, it generates: "narrow grocery aisle with cereal on left, fluorescent lighting, tile floor." Store this. On return, compare new description against stored descriptions using word-overlap similarity (Jaccard).

```python
def description_similarity(desc_a: str, desc_b: str) -> float:
    """Bag-of-words Jaccard similarity. No embeddings needed."""
    stop_words = {"the", "a", "an", "with", "and", "or", "in", "on", "at", "is"}
    words_a = set(desc_a.lower().split()) - stop_words
    words_b = set(desc_b.lower().split()) - stop_words
    if not words_a or not words_b: return 0.0
    return len(words_a & words_b) / len(words_a | words_b)
```

### Candidate Fusion

Multiple signals pointing to the same place compound confidence:

```python
class PlaceRecognition:
    def attempt_recognition(self, current_data) -> Optional[PlaceRecord]:
        candidates = []
        
        # Signal 1: Text matching
        for text in current_data.detected_text:
            matches = self.firestore.query_places_by_text(text.content)
            for m in matches:
                candidates.append({"place_id": m.id, "confidence": 0.9, "signal": "text"})
        
        # Signal 2: Environment signature
        if current_data.environment_type:
            matches = self.firestore.query_places_by_environment(
                current_data.environment_type, current_data.visual_features)
            for m in matches:
                candidates.append({"place_id": m.id, "confidence": 0.5, "signal": "environment"})
        
        # Signal 3: Scene description similarity (replaces NP-hard topology matching)
        if current_data.environment_description:
            recent_places = self.firestore.get_recent_places(limit=50)
            for place in recent_places:
                sim = description_similarity(
                    current_data.environment_description, place.description)
                if sim > 0.5:
                    candidates.append({"place_id": place.id, 
                                       "confidence": sim * 0.7, "signal": "description"})
        
        # Fuse: same place from multiple signals = compounded confidence
        fused = self.fuse_candidates(candidates)
        if fused and fused[0]["confidence"] > 0.75:
            return self.firestore.load_place(fused[0]["place_id"])
        return None  # New place
    
    def fuse_candidates(self, candidates):
        by_place = {}
        for c in candidates:
            pid = c["place_id"]
            if pid not in by_place:
                by_place[pid] = {"place_id": pid, "confidence": 0, "signals": []}
            by_place[pid]["signals"].append(c["signal"])
            # Probabilistic fusion: 1 - (1-a)(1-b)
            old = by_place[pid]["confidence"]
            new = c["confidence"]
            by_place[pid]["confidence"] = 1 - (1 - old) * (1 - new)
        return sorted(by_place.values(), key=lambda x: x["confidence"], reverse=True)
```

### What Gets Stored Per Place

```python
@dataclass
class PlaceRecord:
    place_id: str
    
    # Recognition signatures
    text_signatures: List[str]          # "Whole Foods", "Aisle 7", "Building 3"
    environment_type: str               # "grocery_store"
    visual_features: dict               # Color scheme, distinctive elements
    description: str                    # Full scene description for similarity matching
    
    # Spatial knowledge
    cognitive_map: TopologicalMap       # Nodes, edges, paths
    static_landmarks: List[LandmarkRecord]  # Signs, furniture, permanent features
    
    # Behavioral knowledge
    semantic_patterns: List[SemanticPattern]  # Traffic flow, timing patterns
    hazard_zones: List[HazardZone]      # Known hazard areas
    
    # Metadata
    visit_count: int
    first_visited: datetime
    last_visited: datetime
    total_time_spent: float             # Accumulated across visits
```

### The Returning User Experience

**Visit 1**: Cold start. 15 seconds to operational. Builds map from scratch. Saves to Firestore.

**Visit 2**: First frame → OCR "Whole Foods #247" → Firestore match → Load map, landmarks, patterns. "Welcome back. Last time you entered from the main door. Dairy was to the left." Operational in 2-3 seconds.

**Visit 10**: System knows this place intimately. Refined map, robust patterns. Can say: "This is your usual route. The yogurt section was rearranged since last visit — it moved two aisles over."

---

## 19. Memory Lifecycle — Decay, Pruning, Consolidation <a name="19-memory-lifecycle"></a>

### The Problem: Memory Without Forgetting Breaks

Without forgetting mechanisms:
- Episodic memory grows unboundedly (hundreds of events per session)
- Object registry accumulates every person ever seen (hundreds in a mall)
- Semantic patterns can't unlearn (wrong patterns persist forever)
- Conversation context is lost to compression (nuance disappears)

### Episodic Memory: Relevance Decay + Consolidation

Episodes don't all matter equally. Recent + surprising + user-referenced episodes matter most. Everything else fades.

### Episode Similarity — Fingerprinting (Not Clustering)

Complex clustering (DTW, k-means) requires batch collection, choosing k, tuning distance thresholds. Instead, each episode gets a FINGERPRINT from its key attributes. Episodes with matching fingerprints are "the same type of event."

```python
class EpisodeFingerprint:
    @staticmethod
    def compute(episode: Episode) -> str:
        """
        Fingerprint = event_type | place_type | time_bucket | direction
        Examples:
          "person_approached|grocery_aisle|afternoon|from_left"
          "object_appeared|parking_lot|morning|at_center"
        """
        return "|".join([
            episode.event_type,
            episode.place_type or "unknown",
            time_to_bucket(episode.timestamp),  # morning/afternoon/evening/night
            direction_to_bucket(episode.direction)
        ])
```

Fingerprinting is O(1) per episode. Counter check is O(1). Pattern promotion is immediate. No batching, no hyperparameters. A judge can read "person_approached|grocery_aisle|afternoon|from_left" and immediately understand what the system learned.

### Consolidation: Episodes → Semantic Patterns

```python
class EpisodeConsolidator:
    def __init__(self, promotion_threshold=3):
        self.fingerprint_counts: Dict[str, int] = {}
    
    def observe(self, episode: Episode) -> Optional[SemanticPattern]:
        fp = EpisodeFingerprint.compute(episode)
        self.fingerprint_counts[fp] = self.fingerprint_counts.get(fp, 0) + 1
        
        if self.fingerprint_counts[fp] >= self.promotion_threshold:
            # PROMOTE to semantic pattern
            parts = fp.split("|")
            pattern = SemanticPattern(
                pattern=f"{parts[0]} at {parts[1]} during {parts[2]} {parts[3]}",
                fingerprint=fp,
                confidence=min(0.9, 0.3 + 0.1 * self.fingerprint_counts[fp]),
                supporting_evidence=self.fingerprint_counts[fp],
                description=f"In {parts[1]}, {parts[0].replace('_', ' ')} "
                           f"tends to happen from the {parts[3].replace('from_', '')} "
                           f"during {parts[2]}"
            )
            self.fingerprint_counts[fp] = 0  # Reset — pattern now in semantic memory
            return pattern
        return None
```

```python
@dataclass
class Episode:
    timestamp: float
    event_type: str
    description: str
    place: str
    relevance: float = 1.0     # Starts high, decays
    was_surprising: bool = False
    user_referenced: bool = False
    occurrence_count: int = 1   # How many similar events
    
    def decay_relevance(self, time_elapsed):
        if self.was_surprising:
            half_life = 300    # Surprises persist 5 minutes
        elif self.user_referenced:
            half_life = 600    # User-referenced persist 10 minutes
        else:
            half_life = 60     # Normal episodes fade in 1 minute
        
        self.relevance *= 0.5 ** (time_elapsed / half_life)
    
    def should_consolidate(self):
        """If same event type occurred 3+ times, it becomes a semantic pattern."""
        return self.occurrence_count >= 3
```

**Consolidation**: When the same type of episode repeats (3+ times), it gets promoted to semantic memory as a PATTERN. "Person approached from left" happening 5 times → semantic pattern "In this environment, people tend to approach from the left." Individual episodes can then be forgotten.

### Object Registry: Tiered Storage

```python
class TieredObjectRegistry:
    active: Dict[str, TrackedObject]      # Max 7 — working memory
    recent: Dict[str, TrackedObject]      # Last 50 objects — fast lookup
    archived: Dict[str, TrackedObject]    # Older objects — slow lookup
    
    MAX_ACTIVE = 7
    MAX_RECENT = 50
    
    def promote_to_active(self, obj_id):
        """Object needs active tracking (approaching, user asked about it)."""
        if len(self.active) >= self.MAX_ACTIVE:
            # Demote least-urgent active object to recent
            least_urgent = min(self.active.values(), key=lambda o: o.urgency)
            self.recent[least_urgent.id] = least_urgent
            del self.active[least_urgent.id]
        
        obj = self.recent.pop(obj_id, None) or self.archived.pop(obj_id, None)
        if obj:
            self.active[obj.id] = obj
    
    def prune(self):
        """Remove low-relevance objects from all tiers."""
        # Active: never auto-prune (managed by promote/demote)
        # Recent: prune if confidence < 0.1
        for oid in list(self.recent):
            if self.recent[oid].confidence < 0.1:
                self.archived[oid] = self.recent.pop(oid)
        # Archived: prune if confidence < 0.01 AND not a landmark
        for oid in list(self.archived):
            obj = self.archived[oid]
            if obj.confidence < 0.01 and not obj.is_landmark:
                del self.archived[oid]  # Truly forgotten
```

### Semantic Memory: Counter-Evidence and Invalidation

Patterns can become wrong. Traffic flow changes. Construction ends. The system needs to UNLEARN.

```python
@dataclass
class SemanticPattern:
    pattern: str                    # "People approach from the left"
    confidence: float               # Current confidence
    supporting_evidence: int = 0    # Times confirmed
    contradicting_evidence: int = 0 # Times violated
    last_confirmed: float = 0.0
    
    def update(self, confirmed: bool):
        if confirmed:
            self.supporting_evidence += 1
            self.confidence = min(1.0, self.confidence + 0.05)
            self.last_confirmed = time.time()
        else:
            self.contradicting_evidence += 1
            self.confidence *= 0.8  # Contradictions hurt MORE than confirmations help
        
        # More contradictions than support → pattern is invalid
        if self.contradicting_evidence > self.supporting_evidence * 1.5:
            self.invalidate()
    
    def invalidate(self):
        self.confidence = 0.0
        # Optionally create INVERSE pattern
```

### Cognitive Map: Handling Revisits

When user revisits a place from a different direction, objects swap sides:

```python
class TopologicalMap:
    def handle_revisit(self, place_id, entry_direction):
        """User re-entered a known place from a different direction."""
        node = self.nodes[place_id]
        
        if node.last_entry_direction and entry_direction != node.last_entry_direction:
            # Calculate orientation difference
            angle_diff = entry_direction - node.last_entry_direction
            
            # Update all object positions relative to new orientation
            for obj in node.attached_objects:
                obj.relative_clock = rotate_clock(obj.relative_clock, angle_diff)
            
            node.last_entry_direction = entry_direction
```

### Conversation Context Preservation

The Live session's context window compresses over time. Conversational nuance gets lost. The brain maintains its own conversation log that gets re-injected:

```python
class ConversationLog:
    entries: List[ConversationEntry]  # Max 10 recent entries
    
    def add(self, speaker, text, emotional_tone=None):
        self.entries.append(ConversationEntry(
            timestamp=time.time(),
            speaker=speaker,         # "user" or "agent"
            text=text,
            emotional_tone=emotional_tone
        ))
        if len(self.entries) > 10:
            self.entries.pop(0)
    
    def format_for_injection(self):
        """Include in Live session state injection."""
        lines = ["CONVERSATION CONTEXT (recent):"]
        for e in self.entries[-5:]:  # Last 5 exchanges
            ago = int(time.time() - e.timestamp)
            tone = f" (tone: {e.emotional_tone})" if e.emotional_tone else ""
            lines.append(f"  {ago}s ago — {e.speaker}: \"{e.text}\"{tone}")
        return "\n".join(lines)
```

### Complete Memory Lifecycle

```
SESSION START (Cold):
  All memory empty → Boot Sequence stages 0-3 (15s)

SESSION START (Warm):
  Place recognized → Load from Firestore → Boot stages 0-2 (3s)
  Loaded: cognitive map, landmarks, patterns, user profile

DURING SESSION:
  Working memory: 5-7 active items, constantly refreshed
  Episodic memory: grows with relevance decay, consolidates to patterns
  Object registry: tiered (active 7 → recent 50 → archived → forgotten)
  Cognitive map: grows, handles revisits with orientation awareness
  Semantic memory: patterns accumulate, can be invalidated by counter-evidence
  Conversation log: last 10 exchanges, re-injected to Live session

SESSION END:
  Consolidate episodes → semantic patterns
  Save: cognitive map + landmarks + patterns + user profile
  Save with expiry: temporary observations (construction, events)
  Discard: dynamic objects, active goals, working memory, predictions
  
BETWEEN SESSIONS:
  Firestore holds: place records, user profile
  Nothing actively running
  Stale data pruned on next load (expired observations removed)
```

---

## 20. Honest Limitations — What This Is and Isn't <a name="20-limitations"></a>

### What This IS

A **pedestrian spatial awareness framework** that demonstrates genuine cognitive architecture principles. One camera, one user, walking speed, indoor/outdoor pedestrian spaces, real-time voice output, egocentric perspective.

The PRINCIPLES are general — predict-verify loops, layered memory, emergent goals, attention direction. These apply to any spatial intelligence system.

The IMPLEMENTATION is specific to the blind navigation / pedestrian awareness use case.

### What This IS NOT

**Not a general-purpose spatial intelligence system.** Change key assumptions and pieces break:

| Changed Assumption | What Breaks |
|---|---|
| Drone camera (aerial view) | Distance estimation from object size (calibrated for human height) |
| Wheelchair user | Motion pattern detection (assumes walking gait for turn/stop detection) |
| Vehicle at speed (>30 km/h) | Cloud Vision at 1 FPS misses everything (car covers 8+ meters between frames) |
| Fixed security camera | Entire egocentric model (clock positions, "behind me") meaningless |
| Multiple users on one device | User model confused by different voices, heights, speeds |
| Non-camera sensor (LIDAR, radar) | Perception pipeline hardcoded to visual bounding boxes |

### Known Weaknesses (Not Yet Addressed)

**Low light**: Cloud Vision performance degrades. No fallback to audio-only spatial awareness.

**Very fast objects**: At 1 FPS, objects moving >2 m/s between frames are hard to track reliably. Thrown objects, fast cyclists, running children — all potentially missed.

**Identical objects**: Two people in similar clothing at similar distances — the identity matching can't distinguish them. The brain might merge them into one tracked object or swap identities.

**Crowded scenes**: Cloud Vision may detect 20+ bounding boxes. The brain's 7-object active limit means 13 objects are deprioritized. In a dense crowd, the system switches to aggregate awareness ("crowded area, many people") rather than individual tracking.

**Non-visual hazards**: Wet floor (might be invisible to camera), low-hanging branch (above typical frame), uneven pavement (too subtle at LOW resolution), ice on ground. The cognitive loop can detect some of these through Gemini's reasoning, but it's unreliable.

**Context compression in Live session**: Despite re-injecting full state, the emotional and conversational nuance from 5+ minutes ago is lost. The agent may forget the user expressed frustration, or that they were looking for a specific item mentioned in passing.

### What Would Make It Genuinely General

- **Perception interface layer**: Abstract the sensor input so cameras, LIDAR, radar, IMU all feed into the same world model through adapters
- **Multi-perspective spatial model**: Support both egocentric (user-centered) and allocentric (map-centered) simultaneously, with configurable primary perspective
- **Variable frame rate**: Scale perception frequency based on movement speed and environment risk
- **Multi-user support**: Separate user models that can share spatial data
- **Multi-modal output**: Voice, haptic, visual display, machine-readable logs — configurable per domain
- **3D world model**: Elevation tracking, overhead obstacles, multi-floor buildings

---

## 21. Data Structures <a name="21-data-structures"></a>

### TrackedObject

```python
@dataclass
class TrackedObject:
    # Identity
    id: str                         # Unique ID (e.g., "obj_017")
    cv_label: str                   # Cloud Vision label ("person")
    description: str                # Rich description from Gemini ("person in blue shirt")
    signature: str                  # Matchable identity signature
    
    # Spatial (updated by Cloud Vision / reactive loop)
    position_x: float              # 0.0 (left) to 1.0 (right)
    position_y: float              # 0.0 (top) to 1.0 (bottom)
    size_percent: float            # % of frame area
    bbox: Tuple[int,int,int,int]   # Pixel bounding box
    clock_position: str            # "11 o'clock"
    distance_estimate: str         # "near", "medium", "far"
    
    # Temporal
    position_history: List[Tuple[float, float, float]]  # (x, y, timestamp)
    size_history: List[Tuple[float, float]]              # (size, timestamp)
    velocity: Tuple[float, float]  # (dx/dt, dy/dt)
    is_approaching: bool
    approach_rate: float           # Size change per second
    estimated_time_to_contact: Optional[float]
    
    # Confidence
    confidence: float              # Overall confidence (0.0-1.0)
    trajectory_confidence: float   # How reliable is the trajectory model
    identity_confidence: float     # How sure am I this is the same object
    
    # State
    first_seen: FrameRef
    last_confirmed: FrameRef
    frames_since_seen: int
    is_visible: bool               # Currently in frame
    is_static: bool                # Furniture vs person
    
    # Semantic (updated by Gemini generateContent / cognitive loop)
    activity: Optional[str]        # "walking", "standing", "sitting"
    relationship: Optional[str]    # "near the door", "blocking path"
    semantic_identity: Optional[str]  # "same person from earlier"
    
    # Tracking
    group_id: Optional[str]        # If part of a detected group
    occluded_by: Optional[str]     # If behind another object
    predicted_position: Optional[Tuple[float, float]]  # Where we think it is now
```

### WorldModel

```python
@dataclass
class WorldModel:
    # Objects
    tracked_objects: Dict[str, TrackedObject]
    out_of_view_objects: Dict[str, TrackedObject]  # Not visible but remembered
    object_registry: Dict[str, ObjectMemory]       # All ever-seen objects
    
    # Space
    cognitive_map: TopologicalMap
    current_place: str                              # Node in cognitive map
    user_facing_direction: float                    # Estimated compass direction
    
    # Environment
    environment_type: str                           # "grocery_aisle", "parking_lot"
    environment_description: str
    lighting: str                                   # "dark", "dim", "normal", "bright"
    noise_level: str
    
    # User
    user_position: Tuple[float, float]              # In cognitive map coordinates
    user_speed: float                               # m/s estimated
    user_state: str                                 # "walking", "stationary", "turning"
    user_intent: Optional[str]                      # "searching", "going_somewhere", "examining"
    user_social_state: str                          # "alone", "in_conversation", "on_phone"
    
    # Temporal
    session_start: float
    frames_processed: int
    distance_traveled_estimate: float               # meters
    spatial_context_version: int                     # Increments on transport/major reset
    
    # Confidence
    overall_confidence: float                       # How well do I understand this space
    last_full_cognitive_update: float               # When was last Gemini analysis
    
    # Goals
    active_goals: List[Goal]
    
    # Dimensions
    vigilance: float
    verbosity: float
    detail_focus: float
    proactivity: float
    urgency: float
    social_awareness: float
    exploration: float
    
    # History
    episodic_memory: List[Episode]
    prediction_history: List[PredictionResult]
    alert_history: List[Alert]
    
    # Synchronization
    last_cv_frame: int                              # Last Cloud Vision frame processed
    last_gemini_frame: int                          # Last Gemini frame processed
    _structural_lock: asyncio.Lock                  # For add/remove operations
```

### Perception Data (from Cloud Vision)

```python
@dataclass
class CloudVisionResult:
    frame_id: int
    timestamp: float
    objects: List[CVObject]         # Bounding boxes + labels + confidence
    text_detections: List[CVText]   # OCR results
    labels: List[str]               # Scene-level labels
    faces: List[CVFace]             # Face presence (not identity)
    processing_time_ms: float

@dataclass
class CVObject:
    label: str
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2 in pixels
    confidence: float
    # Computed by brain:
    center_x: float                  # Normalized 0.0-1.0
    center_y: float
    size_percent: float
```

### Cognitive Data (from Gemini generateContent)

```python
@dataclass 
class CognitiveAnalysis:
    frame_id: int
    timestamp: float
    environment: str                 # "grocery store aisle"
    layout: str                      # "narrow corridor with shelves on both sides"
    activities: List[ActivityObservation]  # What objects are doing
    relationships: List[SpatialRelationship]  # How objects relate
    hazards: List[HazardDetection]   # Non-obvious hazards
    predictions: List[str]           # What Gemini thinks happens next
    corrections: List[str]           # Where brain's model seems wrong
```

---

## 22. Synchronization Design <a name="22-synchronization"></a>

### Frame Distribution

Single frame produced by camera → sent simultaneously to:
1. Cloud Vision API (for reactive perception)
2. Gemini generateContent (every 5th-10th frame, for cognitive perception)
3. Gemini Live via send_realtime_input (for conversational visual context)

All three process the SAME frame. No frame identity confusion.

### Out-of-Order Protection

```python
class WorldModel:
    def process_reactive(self, cv_result: CloudVisionResult):
        if cv_result.frame_id <= self.last_cv_frame:
            return  # Reject stale data
        self.last_cv_frame = cv_result.frame_id
        # Process...
    
    def process_cognitive(self, analysis: CognitiveAnalysis):
        if analysis.frame_id <= self.last_gemini_frame:
            return  # Reject stale data
        self.last_gemini_frame = analysis.frame_id
        # Process...
```

### Channel Authority Separation

Cloud Vision is authoritative for: positions, sizes, bounding boxes, object count (WHERE things are).

Gemini generateContent is authoritative for: object meaning, relationships, scene understanding, hazard reasoning (WHAT things mean).

They update DIFFERENT fields of the same TrackedObject. No conflict.

### Conflict Resolution

When channels disagree:

```python
def resolve_conflict(self, cv_data, gemini_data):
    if cv_data.frame_id > gemini_data.frame_id:
        # CV is newer — trust CV for position
        self.update_position(cv_data)
        self.mark_needs_cognitive_recheck()
    else:
        # Gemini analyzed same or newer frame
        if gemini_data.says_object_not_real:
            self.lower_confidence(factor=0.5)  # Might be phantom
        else:
            self.update_semantics(gemini_data)
```

### State Injection to Live Session

Always inject FULL state, never deltas. Survives context compression:

```python
async def inject_state_to_live(self):
    """Called every 10-15 seconds. Full state replaces previous."""
    state = self.format_full_state()
    await self.live_session.send_client_content(
        turns={"role": "user", "parts": [{"text": state}]},
        turn_complete=False  # Context only
    )
```

### Race Condition Protection

```python
class WorldModel:
    async def add_object(self, obj):
        async with self._structural_lock:
            self.tracked_objects[obj.id] = obj
    
    async def remove_object(self, obj_id):
        async with self._structural_lock:
            del self.tracked_objects[obj_id]
    
    def update_position(self, obj_id, position):
        # No lock — atomic field update, safe in asyncio
        self.tracked_objects[obj_id].position_x = position[0]
        self.tracked_objects[obj_id].position_y = position[1]
```

### Critical Alert Delivery (VAD Override)

When user is in conversation and urgent alert is needed:

```python
if urgency >= 0.8:
    # Suppress VAD so user's speech doesn't interrupt alert
    await self.live_session.send_realtime_input(
        activity_end=types.ActivityEnd()
    )
    # Inject alert
    await self.live_session.send_client_content(
        turns={"role": "user", "parts": [{"text": urgent_alert}]},
        turn_complete=True
    )
```

### Error Recovery — Circuit Breaker Pattern

Three concurrent API connections will intermittently fail in production. The system uses circuit breakers with graceful degradation:

```python
class CircuitBreaker:
    """CLOSED (normal) → OPEN (failing) → HALF_OPEN (testing recovery)."""
    def __init__(self, name, failure_threshold=3, recovery_timeout=10):
        self.failure_count = 0
        self.state = "CLOSED"
    
    def record_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"  # Stop calling until recovery timeout
    
    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"
```

**Degradation hierarchy:**

| Level | What's Working | Capability |
|---|---|---|
| FULL | CV + Gemini Cognitive + Live | Complete spatial intelligence |
| DEGRADED-1 | Gemini Cognitive (faster) + Live | Slower tracking, still understands scenes |
| DEGRADED-2 | Live only | Single-session mode, transcript parsing |
| DEGRADED-3 | Local TTS only | Critical alerts via Web Speech API, offline |

Each channel fails and recovers independently. Losing Cloud Vision doesn't crash the voice session. Losing the cognitive loop doesn't stop reactive tracking. The system gets WORSE, not BROKEN.

The Live session auto-reconnects with session resumption. Cloud Vision and generateContent retry with exponential backoff. System status is injectable: "My vision is degraded right now — I might miss things."

---

## 23. Scenario Walkthroughs <a name="23-scenarios"></a>

### Scenario 1: Person Approaches in Grocery Aisle

**Timeline**: Person detected at T=0.4s (far, size 4.2%). Tracked through T=1.4s (5.8%), T=2.4s (8.1%), T=3.4s (12.6%). Urgency crosses threshold at T=3.4s. Alert pushed at T=3.41s. User hears "Person ahead, 12 o'clock, about 6 steps, approaching" at T=4.0s.

**Alert latency**: 0.6 seconds from threshold to user hearing. Acceptable.

**Cognitive loop enrichment**: At T=5.0s-6.8s, Gemini identifies "narrow grocery aisle, person walking at normal pace, limited space to step aside." Brain stores: narrow aisles → alert earlier in future.

**Result**: All systems work. No synchronization issues.

### Scenario 2: User Turns 180 Degrees

**Detection**: Rapid scene change detected in reactive loop. All tracked objects disappear simultaneously. Floor type and lighting remain same.

**Brain response**: PROVISIONAL interpretation: user turned (not door transition). All objects moved to "behind user" memory with inverted positions.

**Cognitive confirmation**: At T=5.0-6.5s, Gemini confirms "same corridor, opposite direction." Brain upgrades confidence.

**If Gemini DISAGREES**: "Different space, floor changed." Brain CORRECTS: previous space becomes separate zone in cognitive map. Previous objects archived.

**Key insight**: Provisional-then-confirm pattern. Reactive loop makes fast approximate decision. Cognitive loop validates or corrects within 3-5 seconds.

### Scenario 3: Vehicle Approaches While User in Conversation

**Critical timing**: Vehicle detected T=1.5s, tracked T=2.5-4.5s, alert at T=4.51s.

**Social tension**: User is talking to another person. Brain delays alert while urgency < 0.7 (social override threshold). When urgency hits 0.85, brain overrides social protocol.

**VAD problem**: User's ongoing speech could prevent Gemini from delivering alert. Fix: send `activity_end` before critical alerts.

**Alternative**: For urgency > 0.9, use local Web Speech API or alert tone — bypass Live session entirely.

**Result**: Works with VAD override hack. The social-vs-safety tension is handled by threshold comparison.

---

## 24. Stress Test: 100 Scenarios, 25 Gaps Fixed <a name="24-stress-test"></a>

### Critical Gaps (All addressed in architecture)

| # | Gap | Solution |
|---|-----|----------|
| G1 | Decision point detection | Brain detects multiple paths from Cloud Vision, generates help_choose_path goal |
| G2 | Elevation tracking (Z-axis) | Cognitive loop detects stairs/ramps; reactive loop tracks vertical bbox changes |
| G3 | Spatial context reset after transport | spatial_context_version increments; cognitive map adds new zone |
| G4 | Reflection/phantom filtering | Cognitive loop identifies reflective surfaces; brain filters phantom objects |
| G5 | Passive transport detection | Frame changes without walking motion → escalator/vehicle detected |
| G6 | Fast-object extrapolation | Amygdala path: size increase >50% in one frame → immediate alert |
| G7 | Boundary crossing detection | Door/gate in Cloud Vision → trigger immediate cognitive cycle |
| G8 | Attention budgeting | Max 7 tracked objects; prioritize by urgency; aggregate rest |
| G9 | Modality fallback | When frame_quality low, shift weight to audio properties from Live session |
| G10 | Vision reliability score | Cloud Vision confidence scores + brain's frame quality assessment |
| G11 | Persistent foreground filtering | Objects at constant frame position across many frames = user's body/carried items |
| G12 | Directional spatial memory | All memories tagged with orientation; swap "ahead" vs "behind" on turn |
| G13 | User mobility profile | Discovered from camera height, motion smoothness, speed patterns |
| G14 | Transparent barrier detection | Cognitive loop identifies glass; reactive loop notes phantom reflections |
| G15 | Passability assessment | Cognitive loop estimates gap width from frame context |
| G16 | Occlusion-aware tracking | Predicted position behind occluder; confidence decays until re-emergence |
| G17 | Group detection | Objects with correlated movement clustered; "group of 3" not 3 separate alerts |
| G18 | Vertical motion detection | Rapid downward bbox movement = falling object → high urgency |
| G19 | Landmark memory | Signs, distinctive features stored in episodic memory with spatial anchor |
| G20 | Session metrics | Counters: distance, time, frames, alerts, objects — survive compression |
| G21 | Head-height obstacles | Cognitive loop checks for above-ground hazards periodically |
| G22 | Following detection | Same object maintaining constant distance behind for >30 seconds |
| G23 | Queue/formation recognition | Cognitive loop identifies line formations; brain tracks user's position in queue |
| G24 | Rapid transition trigger | >3 major property changes between frames → immediate cognitive cycle |
| G25 | Ground hazard periodic scan | Cognitive loop includes ground-check in periodic queries |

### Observable Properties (Fed by Cloud Vision + Gemini)

```python
# From Cloud Vision (every 1-2 seconds)
frame_objects: List[CVObject]      # Bounding boxes, labels, confidence
frame_text: List[CVText]           # OCR results
frame_faces: int                   # Face count
frame_labels: List[str]            # Scene labels

# Computed by Brain from Cloud Vision
elevation_cue: str                 # flat / ascending / descending
ground_hazard_detected: bool
boundary_crossing: bool            # Door/gate in path
passable_gap_width: str            # narrow / normal / wide
frame_quality: float               # 0.0 to 1.0
persistent_foreground: List[str]   # Objects that never move relative to camera

# From Gemini generateContent (every 5-10 seconds)
environment_type: str
spatial_layout: str
object_activities: Dict[str, str]
hazards_detected: List[str]
reflective_surfaces: bool
transparent_barriers: bool
head_height_obstacles: bool

# Computed by Brain across time
objects_approaching: List[str]
following_pattern: Dict[str, bool]
group_formations: List[Group]
collective_behavior_change: bool
```

---

## 25. Experiment Results <a name="25-experiments"></a>

### Experiment 1: Optic Nerve v1

**Goal**: Can Gemini Live API call a structured function from video frame analysis?

**Result**: YES — 1/6 hit rate. First scan produced perfect structured JSON with 5 objects, accurate positions, clock positions, distances. Even read "EXIT" text.

**Key finding**: `thinking_budget=0` required — thinking + function calling on native audio crashes.

### Experiment 2: Optic Nerve v2

**Goal**: Fix 1/6 hit rate with predict-verify loop, NON_BLOCKING, WHEN_IDLE, varied prompts, changing frames.

**Result**: SAME 1/6 hit rate. Changes had no effect.

**Conclusion**: Native audio model mechanically limits function calling to one shot per session. This is NOT a prompting issue.

### Architecture Decision

Function calling provides ONE excellent initial scene inventory at session start. For continuous perception, use Cloud Vision API (reactive) + Gemini generateContent (cognitive). Live API handles voice only.

### Validation Experiments (Earlier Phase)

All 5 passed:
1. Cross-frame object tracking: Gemini maintains object identity across frames ✓
2. Clock-position spatial language: Consistent 10-2 o'clock descriptions ✓
3. Context injection impact: World state injection improves response specificity ✓
4. Distance estimation: Reasonable distance estimates from apparent object size ✓
5. Environment classification: Correctly identifies environment types ✓

---

## 26. Implementation Order <a name="26-implementation"></a>

### Phase 1: Perception Pipeline (Build First)

1. Cloud Vision API integration — send frames, receive bounding boxes
2. Brain spatial math — convert bboxes to clock positions, distances
3. Object matching across frames — basic position-based identity
4. Size trend computation — approach detection
5. Alert decision — urgency threshold → push to Live session

**Demo-able after Phase 1**: "Person approaching, 11 o'clock, 5 steps" — spoken proactively from real Cloud Vision data.

### Phase 2: World Model

6. Object registry — persistent identity across frames
7. Predict-verify loop — predictions generated and checked each cycle
8. Episodic memory — significant events logged with timestamps
9. Confidence system — scores that decay, update, and resolve conflicts
10. Topological map — places and paths, user's position in the map

### Phase 3: Cognitive Loop

11. Gemini generateContent integration — periodic scene understanding
12. Environment classification and enrichment
13. Hazard detection layer
14. Semantic memory — learned patterns

### Phase 4: Learning and Calibration

15. User response tracking — what alerts get acknowledged vs dismissed
16. Threshold adjustment from outcomes
17. Domain plugin switching
18. Cross-session persistence (Firestore)

### What the Demo Shows

The demo side panel (or debug view) displays the brain's state:

```
PREDICTED: person at (0.35, 0.50), size 16.8%
OBSERVED:  person at (0.38, 0.49), size 18.2%
VERDICT:   corrected — moving faster than expected
DECISION:  alert (urgency 0.73 > threshold 0.5)
→ SPEAKING: "Person, 11 o'clock, close, approaching"
```

Judges see a MIND reasoning, not a chatbot describing.

---

## 27. Tech Stack <a name="27-tech-stack"></a>

| Component | Technology | Purpose |
|---|---|---|
| Backend | Python 3.11+, FastAPI, uvicorn | Brain, world model, decision engine |
| Reactive perception | Google Cloud Vision API | Bounding boxes, labels, OCR |
| Cognitive perception | Gemini generateContent (2.5 Flash) | Scene understanding, reasoning |
| Voice | Gemini Live API (native audio model) | Speech I/O, conversation |
| Agent framework | Google ADK (optional) | Multi-agent orchestration |
| Frontend | HTML/JS PWA | Camera capture, audio, WebSocket |
| Audio | Web Audio API, PCM streaming | Mic input, speaker output |
| Persistence | Google Firestore | Cross-session memory, spatial maps |
| Deployment | Google Cloud Run | Hosting |

---

## 28. Cost Model <a name="28-cost"></a>

### Per Minute (Active Use)

| Component | Rate | Cost/min |
|---|---|---|
| Cloud Vision API | ~30 frames/min × $0.0015 | $0.045 |
| Gemini generateContent | ~6-12 calls/min × $0.001 | $0.006-0.012 |
| Gemini Live API | Continuous session | ~$0.008 |
| **Total** | | **~$0.06/min** |

### Extrapolated

- Per hour: ~$3.60
- Per day (8 hours): ~$28.80
- Per month (8hr/day): ~$860

### Hackathon

- Total development + demo cost: Under $5 on free tier
- Well within free tier limits for all services

### Optimization Paths for Production

- Frame skipping in stable environments (reduce Cloud Vision calls)
- Lower Cloud Vision frequency when nothing is changing
- Batch multiple frames in single generateContent call
- Context caching for Gemini calls with similar frames
- Target: $2-5/day for production use

---

## Summary

Drishti is a spatial intelligence framework that demonstrates genuine cognitive architecture for real-time spatial awareness. It uses foundation models (Gemini) as the perception and communication layer, while the intelligence — tracking, prediction, memory, decision-making, and learning — lives as a structured computational system in the backend that mirrors biological spatial cognition.

The architecture is validated through experiments, stress-tested against 100 scenarios with 25 gaps identified and resolved, and designed with full synchronization analysis across three parallel perception channels.

The key insight: the brain is the intelligence. Gemini is the eyes and the mouth. The world model is the belief state of reality. And the predict-verify-correct loop is what makes it think.
