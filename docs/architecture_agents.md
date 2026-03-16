# SixthSense — The Real Architecture
## A Self-Evolving Spatial World Model Built on Agentic Intelligence

---

## THE CORE IDEA (What Makes This $80K-Worthy)

Everyone else will build: Frame → Gemini → Description → Voice.
That's a science fair project.

We're building something fundamentally different:

**A spatial world model that lives inside Gemini's context window, 
managed by an agentic system that accumulates knowledge, recognizes 
patterns, makes predictions, and evolves its intelligence with every 
frame it processes.**

The context window IS the world model. Not just conversation history — 
a structured, evolving spatial representation of reality that gets 
richer, more accurate, and more predictive every second.

The agents don't just process frames. They MANAGE THE WORLD MODEL — 
deciding what to observe, how to structure knowledge, when to act, 
how to communicate, and how to improve.

---

## THE FIVE AGENTS — What Each One Actually THINKS About

### Agent 1: PERCEIVER
**Not just "describe this frame." It's "what changed in the world?"**

This agent uses Gemini's vision. But it's not stateless. It receives the 
current world model state and asks DIRECTED questions about each frame:

Frame 1 (no context): "What do I see? Classify everything."
Frame 5 (with context): "I know there's a person at 11 o'clock who was 
  approaching. Is that person still there? Closer? Also, I predicted 
  there might be a door ahead based on the corridor pattern — confirm?"

The Perceiver gets SMARTER because it asks better questions as the 
world model grows. It's not processing each frame from scratch — it's 
VALIDATING AND EXTENDING an existing model.

```
Input:  Raw frame + Current world model state
Output: Structured observation (what changed, what confirmed, what's new)

Thinks about:
- What do I expect to see based on the model? (prediction validation)
- What's actually there? (perception)
- What's different from what I expected? (surprise detection)
- What should I look more carefully at? (attention direction)
```

### Agent 2: WORLD MODELER
**This is the brain. The thing that makes SixthSense actually intelligent.**

It doesn't just store observations. It REASONS about space:

```
Input:  Perceiver's observation + Previous world state
Output: Updated world state with predictions and inferences

Thinks about:

SPATIAL GRAPH:
- Object permanence: "Person A left the frame at 2 o'clock 
  3 seconds ago. They didn't appear elsewhere. They're probably 
  still to my right, just outside camera view."
- Spatial relationships: "The shelf is next to the wall. 
  The wall has a door. The door leads somewhere I haven't seen yet."
- Layout inference: "I've been walking straight for 15 frames 
  and seeing shelves on both sides. This is an aisle. Aisles end. 
  There's probably a cross-aisle or wall ahead."

TEMPORAL PATTERNS:
- "In the last 30 seconds, 3 people have walked past from right 
  to left. This is a busy corridor with a dominant flow direction."
- "Object B has been stationary for 40 frames. It's furniture, 
  not a person. Reduce its alert priority."
- "The lighting changed gradually over 10 frames. We're 
  approaching a window or transitioning from indoor to outdoor."

PREDICTIONS:
- "Person A is approaching at ~1.5 m/s from 11 o'clock. 
  In 3 seconds they'll be at arm's reach at 12 o'clock."
- "Based on corridor length and walking speed, we'll reach 
  the end of this hallway in approximately 8 seconds."
- "The environment is getting noisier (audio). We may be 
  approaching a open/busy area."

CONFIDENCE TRACKING:
- Environment classification: outdoor_sidewalk (92% confident)
- Person A identity: same_person_tracked_for_12_frames (high confidence)
- Distance estimate to door: ~5 meters (medium confidence, 
  based on known door height proportions)
```

**The world model state is a living document:**

```json
{
  "session": {
    "frame_count": 47,
    "duration_seconds": 47,
    "world_model_version": 14
  },
  
  "environment": {
    "type": "indoor_retail_aisle",
    "confidence": 0.94,
    "evolution": [
      {"frame": 1, "classification": "indoor_unknown", "confidence": 0.4},
      {"frame": 5, "classification": "indoor_retail", "confidence": 0.7},
      {"frame": 12, "classification": "indoor_retail_aisle", "confidence": 0.94}
    ],
    "inferred_layout": {
      "structure": "parallel_aisles",
      "current_aisle_direction": "north",
      "estimated_aisle_remaining": "8_steps",
      "cross_aisle_expected": true
    },
    "dynamics": {
      "foot_traffic": "moderate",
      "dominant_flow": "left_to_right",
      "noise_level": "increasing"
    }
  },
  
  "objects": {
    "active": [
      {
        "id": "person_A",
        "type": "person",
        "tracking_confidence": 0.95,
        "first_seen_frame": 31,
        "last_seen_frame": 47,
        "trajectory": [
          {"frame": 31, "clock": "10:00", "distance": "far", "size_pct": 1.8},
          {"frame": 35, "clock": "10:30", "distance": "medium", "size_pct": 3.2},
          {"frame": 40, "clock": "11:00", "distance": "medium-near", "size_pct": 5.1},
          {"frame": 47, "clock": "11:30", "distance": "near", "size_pct": 8.7}
        ],
        "velocity": "approaching_moderate",
        "predicted_position_frame_50": {"clock": "12:00", "distance": "very_near"},
        "risk_level": "medium"
      }
    ],
    "persistent_static": [
      {
        "id": "shelf_left",
        "type": "retail_shelf",
        "clock": "9:30-10:30",
        "distance": "near_constant",
        "frames_tracked": 40,
        "content_observed": ["cereal_boxes", "snack_packages"]
      }
    ],
    "remembered_but_not_visible": [
      {
        "id": "person_B",
        "type": "person",
        "last_seen_frame": 28,
        "last_position": {"clock": "2:00", "distance": "far"},
        "exit_direction": "right",
        "note": "Walked past on the right, likely still ahead-right"
      }
    ]
  },
  
  "user_model": {
    "movement": {
      "speed": "moderate_walk",
      "direction": "forward",
      "pattern": "straight_line_with_occasional_head_turn",
      "estimated_speed_mps": 1.1
    },
    "communication": {
      "preferred_detail": "medium",
      "last_spoke": "12s_ago",
      "recent_queries": ["what_section_is_this", "where_is_dairy"],
      "response_to_alerts": "acknowledges_briefly",
      "emotional_state": "calm_focused"
    },
    "learned_preferences": {
      "alerts_responded_positively": ["person_approaching", "section_change"],
      "alerts_dismissed": ["static_object_description"],
      "asks_frequently_about": ["product_locations", "what_section"]
    }
  },
  
  "decision_history": [
    {"frame": 35, "action": "alert", "content": "Person approaching from left", 
     "user_response": "acknowledged", "outcome": "appropriate"},
    {"frame": 22, "action": "ambient", "content": "Entering cereal aisle", 
     "user_response": "asked_for_more_detail", "outcome": "too_brief"},
    {"frame": 15, "action": "alert", "content": "Shelf end approaching", 
     "user_response": "I_know", "outcome": "unnecessary"}
  ]
}
```

### Agent 3: DECISION MAKER
**Not just priority ranking. Contextual reasoning about WHAT TO DO.**

This agent doesn't have simple rules. It REASONS:

```
Input:  World model state + Use case config + Decision history
Output: Decision (action, content, timing, urgency)

Thinks about:

WHAT'S WORTH SAYING:
- "Person A is approaching, but I already alerted about them 
  at frame 35 and user acknowledged. Is there new information? 
  Yes — they're much closer now. Update alert with new distance."
- "The aisle is ending. I alerted about shelf-end before and 
  user said 'I know.' But this is a DIFFERENT aisle end. 
  Alert because the context is new even if the concept is familiar."
- "The user asked about dairy 30 seconds ago. I now see a sign 
  that says 'Dairy' at 1 o'clock. This is HIGH priority because 
  it directly answers their previous question — even though a sign 
  is normally low priority."

TIMING:
- "User is currently listening to my previous response. 
  Queue this, don't interrupt."
- "I haven't spoken in 15 seconds. User might wonder if I'm 
  still active. Provide a brief ambient update."
- "Two things need attention simultaneously. Prioritize the 
  approaching person over the scene description."

ADAPTATION FROM HISTORY:
- "User dismissed my last 'shelf approaching' alert. 
  Increase threshold for static obstacle alerts."
- "User asked for more detail after my brief section update. 
  Next time, give medium detail for location changes."
- "User responds positively to person-approaching alerts. 
  Keep that threshold where it is."
```

### Agent 4: COMMUNICATOR
**Not just text-to-speech. An adaptive communication system.**

```
Input:  Decision + User emotional state + Communication history
Output: Voice response (or silence)

Thinks about:

WHAT TO SAY:
- Alert format: "Person, 11 o'clock, close, approaching" (terse)
- vs Description: "You're entering the dairy section. Milk 
  is usually along the back wall." (conversational)
- vs Guidance: "Walk forward about 10 steps, then the dairy 
  coolers should be on your right." (directional)

HOW TO SAY IT:
- User sounds frustrated → shorter, more direct, calmer tone
- User sounds curious → more descriptive, inviting questions
- User hasn't spoken in a while → gentle prompt, not demanding
- Emergency → override all style rules, be direct and urgent

WHAT NOT TO SAY:
- Don't repeat what was just said
- Don't describe things user already acknowledged knowing
- Don't give unnecessary detail in busy/stressful moments
- Don't speak over the user (respect barge-in)

LANGUAGE ADAPTATION:
- User has been speaking Hindi → respond in Hindi
- User switches to English → switch seamlessly
- Technical terms → simplify for accessibility
- Clock positions → always, never "left/right" alone
```

### Agent 5: LEARNER (The Meta-Agent)
**This is what makes SixthSense genuinely intelligent over time.**

The Learner doesn't process frames. It processes THE SYSTEM ITSELF:

```
Input:  All agent outputs + User responses + Outcomes
Output: Updated parameters for all other agents

Thinks about:

PERCEPTION LEARNING:
- "The Perceiver keeps missing the step-down at the end of aisles. 
  Add 'floor level changes' to its priority observation list."
- "The Perceiver correctly identified 3 people in a row. 
  Person detection is reliable in this lighting."

WORLD MODEL LEARNING:
- "Indoor retail environments have a consistent structure. 
  After seeing 3 aisles, infer the pattern for the rest."
- "Distance estimation was off by ~30% for glass objects 
  (reflections confuse size judgment). Add a correction factor."

DECISION LEARNING:
- "Alert threshold for 'person approaching' is well-calibrated — 
  user acknowledges 80% of these alerts. Keep it."
- "Alert threshold for 'static obstacle' is too sensitive — 
  user dismisses 60% of these. Raise threshold."
- "User asks about locations frequently. Be more proactive 
  about announcing section/area changes."

COMMUNICATION LEARNING:
- "User prefers responses under 8 words for alerts."
- "User asks follow-up questions 40% of the time after 
  descriptions. Anticipate by including one extra detail."
- "User's walking speed is ~1.1 m/s. Calibrate step 
  estimates to this (1 step ≈ 0.65m for this user)."

CROSS-SESSION LEARNING (if persistent storage available):
- "User visits this grocery store regularly. Load the 
  layout model from last visit as starting context."
- "User's preferences are stable: prefers brief alerts, 
  asks about food sections, walks at 1.1 m/s."
```

---

## HOW THE AGENTS INTERACT (The Loop)

This is NOT a simple pipeline. It's a FEEDBACK LOOP with multiple cycles:

```
                    ┌──────────────────────────────┐
                    │     LEARNER (Meta-Agent)       │
                    │  Observes everything, updates  │
                    │  parameters for all agents     │
                    └───────┬──────────┬─────────────┘
                            │          │
                    updates │          │ updates
                    params  │          │ params
                            ▼          ▼
┌──────────┐    ┌──────────────┐    ┌────────────┐    ┌──────────────┐
│          │    │              │    │            │    │              │
│PERCEIVER │───▶│ WORLD MODELER│───▶│ DECISION   │───▶│COMMUNICATOR  │
│          │    │              │    │ MAKER      │    │              │
│ Extracts │    │ Updates the  │    │ Reasons    │    │ Speaks or    │
│ spatial  │    │ world model  │    │ about what │    │ stays silent │
│ data from│    │ Predicts     │    │ to do and  │    │              │
│ frames   │    │ Infers       │    │ when       │    │ Adapts to    │
│          │    │ Tracks       │    │            │    │ emotion +    │
│ Asks     │    │              │    │ Learns     │    │ preference   │
│ DIRECTED │    │ Maintains    │    │ from past  │    │              │
│ questions│    │ object       │    │ decisions  │    │              │
│ based on │    │ permanence   │    │            │    │              │
│ current  │    │              │    │            │    │              │
│ model    │    │              │    │            │    │              │
└──────────┘    └──────────────┘    └────────────┘    └──────────────┘
     ▲                                                       │
     │                                                       │
     │              ┌──────────────────┐                     │
     │              │   USER RESPONSE   │                     │
     └──────────────│  (voice / action  │◀────────────────────┘
                    │   / silence)      │
                    └──────────────────┘
     
     The user's response feeds back into:
     - Perceiver (what to look for next)
     - World Model (user behavior data)  
     - Decision Maker (was this alert useful?)
     - Communicator (adjust style)
     - Learner (update all parameters)
```

**Key insight: The loop runs at TWO speeds:**

**Fast loop (every frame, ~1 second):**
Perceiver → World Modeler → Decision Maker → Communicator
This handles real-time awareness.

**Slow loop (every 10-15 seconds):**
Learner analyzes accumulated data → updates all agent parameters
This handles adaptation and improvement.

---

## HOW THIS RUNS TECHNICALLY

### The Gemini Live API Session
- Handles audio in/out continuously
- Receives frames at 1 FPS
- Has the SPATIAL SYSTEM PROMPT defining behavior
- Contains the evolving world model in its context window

### The Agent Layer (ADK)
- Coordinator Agent orchestrates the loop
- Sub-agents don't each call Gemini separately (that would be slow/expensive)
- Instead, the agents are LOGICAL roles within the system:
  - Perceiver = Gemini's frame processing (guided by system prompt)
  - World Modeler = Context injection engine (Python code that structures the state)
  - Decision Maker = Priority logic (Python code that evaluates what to say)
  - Communicator = Gemini's voice output (shaped by system prompt + context)
  - Learner = Background analysis (Python code that adjusts parameters)

### The Context Window as World Model
The 128K context window contains:
1. System prompt (agent behavior rules) — ~2K tokens
2. Recent frames (last 30-60 seconds at 258 tok/frame) — ~8-15K tokens
3. Structured world state injection — ~2-4K tokens
4. Audio history — variable
5. Decision/response history — ~1-2K tokens

Total active context: ~15-25K tokens, well within 128K limit.
Context compression kicks in for longer sessions, preserving the 
structured state while dropping old raw frames.

### The State Machine

```python
class SpatialWorldModel:
    """The evolving intelligence of SixthSense."""
    
    def __init__(self, use_case_config):
        self.config = use_case_config
        self.frame_count = 0
        self.environment = EnvironmentModel()
        self.objects = ObjectTracker()
        self.user = UserModel()
        self.decisions = DecisionHistory()
        self.learner = AdaptiveParameters()
    
    def process_perceiver_output(self, observation):
        """World Modeler: Update state from new observation."""
        self.frame_count += 1
        
        # Update object tracking
        for obj in observation.objects:
            tracked = self.objects.match_to_existing(obj)
            if tracked:
                tracked.update_trajectory(obj)
                tracked.recalculate_velocity()
                tracked.predict_future_position()
            else:
                self.objects.add_new(obj)
        
        # Mark objects not seen as "out of view" (not deleted)
        self.objects.mark_unseen_objects(observation.frame_id)
        
        # Update environment understanding
        self.environment.update(observation.scene_type, observation.lighting, 
                               observation.noise_level)
        self.environment.infer_layout(self.objects.static_objects)
        
        # Update user movement model
        self.user.update_movement(observation.camera_motion_estimate)
    
    def should_speak(self):
        """Decision Maker: Evaluate what, if anything, to say."""
        alerts = []
        
        # Check each tracked object against thresholds
        for obj in self.objects.active:
            if obj.is_approaching and obj.risk_level >= self.learner.alert_threshold:
                alerts.append(SpatialAlert(
                    priority=1,
                    content=f"{obj.type}, {obj.clock_position}, "
                            f"{obj.distance}, approaching",
                    reasoning=f"Tracked for {obj.frames_tracked} frames, "
                              f"velocity={obj.velocity}"
                ))
        
        # Check for environment transitions
        if self.environment.transition_detected:
            alerts.append(SpatialAlert(
                priority=2,
                content=self.environment.transition_description,
                reasoning="Environment type changed"
            ))
        
        # Check if user's previous question is now answerable
        if self.user.pending_query and self.can_answer_query():
            alerts.append(SpatialAlert(
                priority=2,
                content=self.generate_query_answer(),
                reasoning="Answering user's earlier question"
            ))
        
        # Ambient update if nothing else and silence too long
        if not alerts and self.user.silence_duration > self.learner.ambient_interval:
            alerts.append(SpatialAlert(
                priority=4,
                content=self.generate_ambient_summary(),
                reasoning="Periodic ambient update"
            ))
        
        return sorted(alerts, key=lambda a: a.priority)
    
    def generate_context_injection(self):
        """Create the structured text to inject into Gemini's context."""
        return f"""
--- WORLD STATE v{self.frame_count} ---
ENV: {self.environment.type} ({self.environment.confidence:.0%})
LAYOUT: {self.environment.layout_summary}
TRACKING {len(self.objects.active)} objects:
{self.objects.compact_summary()}
REMEMBERED (out of view): {len(self.objects.remembered)}
USER: {self.user.movement_summary}, emotion={self.user.emotional_state}
PREDICTIONS: {self.generate_predictions()}
LEARNED: alert_threshold={self.learner.alert_threshold}, 
  preferred_detail={self.learner.detail_level}
---"""
    
    def learn_from_response(self, user_response, alert_given):
        """Learner: Adapt based on what happened."""
        if user_response == "acknowledged":
            self.learner.reinforce(alert_given.type, "good")
        elif user_response == "dismissed" or user_response == "i_know":
            self.learner.adjust_threshold(alert_given.type, "raise")
        elif user_response == "what" or user_response == "more_detail":
            self.learner.adjust_threshold(alert_given.type, "lower")
            self.learner.increase_detail_level()
        elif user_response == "silence" and alert_given.priority <= 2:
            # User didn't respond to important alert — maybe didn't hear?
            self.learner.note_possible_miss(alert_given)
```

---

## WHAT MAKES THIS PROFOUND

### 1. The Context Window as World Model
Nobody has proposed using an LLM's context window as a structured, 
evolving spatial world model. The context isn't conversation history — 
it's a LIVING REPRESENTATION OF REALITY that gets enriched with 
every observation.

### 2. Directed Perception
The Perceiver doesn't blindly describe each frame. It asks QUESTIONS 
based on the current model. "Is the person I've been tracking still 
at 11 o'clock?" This is attention-driven perception — the system 
focuses on what MATTERS, not everything visible.

### 3. Object Permanence
When something leaves the frame, it's not deleted. The model 
REMEMBERS it was there and PREDICTS where it might be now. Just 
like a human brain maintains awareness of things behind you.

### 4. Predictive Spatial Intelligence
The system doesn't just describe the present. It PREDICTS the future.
"Based on trajectory, this person will be at your 12 o'clock in 
3 seconds." "Based on corridor length, you'll reach a junction 
in about 8 steps."

### 5. Self-Calibrating Behavior
The Learner adjusts all parameters based on real user responses. 
After 5 minutes of use, the system has adapted to this specific 
user's preferences, walking speed, alert sensitivity, and 
communication style.

### 6. Universal Platform Through Use Case Plugins
The entire intelligent system is domain-agnostic. The same world 
model, the same agents, the same learning loop — just different 
priority rules and communication styles per use case.

---

## THE DEMO NARRATIVE (What Judges See)

**"Watch the world model evolve in real time."**

Show a split screen:
- LEFT: Camera feed (what the system sees)
- RIGHT: Live world model state (JSON updating in real-time)
- BOTTOM: Transcript of what the system says and why

Frame 1-5: "Classifying environment... indoor space... confidence growing..."
Frame 10: "Indoor retail aisle confirmed (94%). Tracking 2 people, 1 shelf unit."
Frame 20: "Person A approaching from left. Alert threshold met. Speaking."
          → Voice: "Person, 11 o'clock, approaching."
Frame 25: User says "I know"
          → Learner: "User dismissed person-approaching alert. Adjusting."
Frame 30: Another person approaches.
          → Decision: "Similar to last alert which user dismissed. But this 
             person is on a collision path (different from last time). Alert."
          → Voice: "Another person, 12 o'clock, heading straight toward you."
Frame 40: User asks "Where's the dairy?"
          → Queued as pending query. Actively searching in frames.
Frame 48: Sign reading "Dairy" detected at 1 o'clock.
          → "The dairy section is at 1 o'clock, about 15 steps ahead."
          → (Answering the query from 8 seconds ago — TEMPORAL INTELLIGENCE)
Frame 55: Switch to security mode. Same camera.
          → Completely different behavior. Logging people, tracking movements,
             tactical communication style.
          → "New individual entered at 10 o'clock. Moving toward center.
             Second individual stationary at 2 o'clock. No anomalies."

**The judge sees: The same engine, radically different intelligence 
based on use case. And the intelligence EVOLVED during the demo — 
it learned from the user's responses in real time.**

---

## NOT A 12TH GRADE PROJECT BECAUSE:

1. Novel architecture: Context window as spatial world model (publishable concept)
2. Five-agent agentic loop with self-calibration (beyond current ADK examples)
3. Object permanence in a vision system (cognitive science principle implemented in AI)
4. Predictive spatial intelligence from sequential frames (research frontier)
5. Universal platform with domain plugins (not a single-use app)
6. Self-evolving parameters from user feedback (real learning, not just prompting)
7. Maximizes every Gemini Live API feature simultaneously (affective + proactive + 
   vision + function calling + thinking + transcription + compression + resumption)
8. Addresses 2.2B+ affected people across multiple domains
9. Directly extends Google's "world model" research agenda
10. Demonstrates capabilities that DON'T EXIST in any product today — 
    not Astra, not Seeing AI, not Be My Eyes, not anything.
