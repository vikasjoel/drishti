# SixthSense — The Operational Flow
## How the System Actually Thinks (Not Scene Description — Autonomous Intelligence)

---

## THE FUNDAMENTAL SHIFT IN THINKING

Wrong mental model:
```
Frame comes in → Describe scene → User hears description → Wait for next frame
```

Right mental model:
```
The system has an OBJECTIVE that it's pursuing every second.
Frames are EVIDENCE it uses to pursue that objective.
The objective SHIFTS based on what's happening.
The user is a PARTNER in the loop, not the trigger.
```

The system isn't describing the world. It's **navigating reality on behalf of the user** — continuously, autonomously, adapting its own goals in real-time.

---

## THE THREE NESTED LOOPS

The system doesn't run one loop. It runs THREE simultaneous loops at different speeds, like the human brain processes sensory data at multiple timescales:

### Loop 1: REACTIVE (Every frame — 1 second)
**"What's happening RIGHT NOW that needs attention?"**

```
For every frame:
├── Has any tracked object moved significantly?
│   ├── YES: Is it approaching? → Calculate urgency
│   │         Is it new? → Add to tracking
│   │         Did it disappear? → Move to memory
│   └── NO: Continue monitoring
│
├── Is there immediate risk?
│   ├── Approaching object on collision path → ALERT NOW
│   ├── Floor level change detected → WARN
│   ├── New obstacle in walking path → INFORM
│   └── None → Stay silent
│
├── Did user just speak?
│   ├── YES: Parse intent → respond contextually
│   └── NO: Continue autonomous operation
│
└── Update all object positions, distances, velocities
```

This loop runs FAST. It's the safety net. It doesn't think deeply — it reacts.

### Loop 2: COGNITIVE (Every 5-10 seconds)
**"What's the situation and what should I be doing?"**

This is where the OBJECTIVE shifts:

```
Every 5-10 seconds:
├── ASSESS ACTIVITY STATE: What is the user doing?
│   ├── WALKING → Objective: NAVIGATE
│   │   Focus: path ahead, obstacles, distances, direction changes
│   │   Communication: spatial guidance, proactive alerts
│   │
│   ├── STATIONARY + FACING OBJECTS → Objective: EXAMINE
│   │   Focus: what's in front, read text, identify items, details
│   │   Communication: descriptive, respond to queries
│   │   Switch resolution: LOW → HIGH (need detail now)
│   │
│   ├── STATIONARY + PEOPLE NEARBY → Objective: SOCIAL
│   │   Focus: who's approaching, are they speaking, body language
│   │   Communication: social cues, whispered spatial updates
│   │
│   ├── TRANSITIONING (indoor↔outdoor, aisle→open space) → Objective: ORIENT
│   │   Focus: new environment type, layout, key landmarks
│   │   Communication: announce transition, describe new space
│   │
│   ├── SEARCHING (user asked "where is X?") → Objective: FIND
│   │   Focus: scan for target object, check signs, spatial logic
│   │   Communication: guided search ("try turning right... not here... keep going")
│   │
│   └── WAITING (in queue, at traffic light, etc.) → Objective: MONITOR
│       Focus: queue movement, signal changes, time awareness
│       Communication: periodic updates, "queue moving", "light changed"
│
├── UPDATE ENVIRONMENT MODEL
│   ├── Has environment type changed?
│   ├── Has foot traffic pattern changed?
│   ├── Has lighting changed?
│   ├── What's the spatial layout learned so far?
│   └── What can I predict about what's ahead?
│
└── INJECT UPDATED CONTEXT into Gemini session
    (World model state, current objective, relevant parameters)
```

### Loop 3: REFLECTIVE (Every 30-60 seconds)
**"Am I doing a good job? How should I adjust?"**

```
Every 30-60 seconds:
├── REVIEW DECISION OUTCOMES
│   ├── Alerts given → User responses
│   │   "Person approaching" → User said "thanks" → GOOD, keep threshold
│   │   "Obstacle ahead" → User said "I know" → TOO SENSITIVE, raise threshold
│   │   (No alert) → User bumped into something → MISSED, lower threshold
│   │
│   ├── Descriptions given → User follow-ups
│   │   Short description → User asked "more detail" → INCREASE detail
│   │   Long description → User interrupted → DECREASE detail
│   │   Description → User asked follow-up → APPROPRIATE depth
│
├── RECALIBRATE USER MODEL
│   ├── Estimated walking speed (from scene flow across frames)
│   ├── Preferred alert frequency
│   ├── Preferred detail level
│   ├── Emotional state trend (getting stressed? relaxed? frustrated?)
│   ├── Common questions pattern (keeps asking about products? navigation?)
│
├── UPDATE ALERT THRESHOLDS per object type
│   ├── person_approaching: threshold = X (adjusted from outcomes)
│   ├── obstacle_in_path: threshold = Y
│   ├── environment_change: threshold = Z
│   ├── text_detected: threshold = W
│
└── GENERATE STRATEGIC PREDICTIONS
    ├── "Based on the store layout so far, dairy is likely on the perimeter"
    ├── "User has been walking 3 minutes, may be approaching store exit"
    ├── "Foot traffic increasing, might be entering a busier area"
    └── "User asked about 3 products — they're shopping with a list"
```

---

## HOW THE OBJECTIVE SHIFTS (The Key Innovation)

This is what makes SixthSense NOT a scene describer. The system has a **dynamic objective** that changes based on evidence:

```
TIME    EVIDENCE                          OBJECTIVE SHIFT
─────────────────────────────────────────────────────────────
0:00    First frame. Unknown space.       → ORIENT (classify, scan)
0:05    Indoor retail detected.           → ORIENT (map layout)
0:10    User starts walking.              → NAVIGATE (path, obstacles)
0:25    User stops at shelf.              → EXAMINE (read, identify)
0:30    User asks "where is dairy?"       → FIND (search for dairy)
0:35    User starts walking again.        → FIND + NAVIGATE (combined)
0:48    "Dairy" sign detected.            → FIND (announce target found!)
0:50    User at dairy section.            → EXAMINE (read labels, prices)
1:05    Person approaches user.           → SOCIAL (who, what do they want?)
1:10    Person speaks to user.            → SOCIAL (listen, context)
1:15    Person walks away.               → back to EXAMINE
1:30    User starts walking toward exit.  → NAVIGATE (guide out)
1:45    Environment transition detected.  → ORIENT (outdoor, new rules)
```

The PERCEIVER asks different questions depending on the current objective:

| Objective | Perceiver Asks About | Ignores |
|-----------|---------------------|---------|
| NAVIGATE | Path ahead, obstacles, distances, doors, stairs, people in path | Product labels, colors, fine text |
| EXAMINE | Text, labels, products, fine details, colors | Things behind user, distant objects |
| FIND | Specific target object, signs, directional cues | Irrelevant products, static furniture |
| SOCIAL | People's positions, approach direction, whether they're facing user | Distant objects, scenery |
| ORIENT | Room shape, exits, key landmarks, lighting, environment type | Small objects, text, products |
| MONITOR | Changes in queue/signal/situation, time progression | Static background, details |

This is **active perception** — the system focuses its attention based on what it needs to know right now, not processing everything equally.

---

## THE FLOW DIAGRAM (Complete)

```
                         ┌─────────────────────────────┐
                         │     REFLECTIVE LOOP          │
                         │     (every 30-60s)           │
                         │                              │
                         │  • Review outcomes            │
                         │  • Adjust thresholds          │
                         │  • Recalibrate user model     │
                         │  • Strategic predictions      │
                         │                              │
                         └──────────┬──────────────────┘
                                    │ updates parameters
                                    ▼
┌────────────┐          ┌─────────────────────────────┐
│            │          │     COGNITIVE LOOP            │
│   CAMERA   │          │     (every 5-10s)            │
│   FRAME    │          │                              │
│  (1 FPS)   │────┐     │  • Assess activity state      │
│            │    │     │  • SHIFT OBJECTIVE            │
└────────────┘    │     │  • Update environment model   │
                  │     │  • Inject context to Gemini   │
┌────────────┐    │     │  • Direct Perceiver attention  │
│            │    │     │                              │
│   USER     │    │     └──────────┬──────────────────┘
│   AUDIO    │────┤                │ sets objective
│  (contin.) │    │                ▼
│            │    │     ┌─────────────────────────────┐
└────────────┘    │     │     REACTIVE LOOP             │
                  │     │     (every frame, 1s)         │
                  ├────▶│                              │
                  │     │  • Track object movements     │
                  │     │  • Check risks / urgency      │
                  │     │  • Process user speech         │
                  │     │  • Update positions/distances  │
                  │     │                              │
                  │     └──────────┬──────────────────┘
                  │                │
                  │                ▼ 
                  │     ┌─────────────────────────────┐
                  │     │     DECISION + COMMUNICATION  │
                  │     │                              │
                  │     │  IF urgent risk → ALERT       │
                  │     │  IF objective fulfilled → SAY  │
                  │     │  IF user asked → RESPOND       │
                  │     │  IF ambient needed → UPDATE    │
                  │     │  ELSE → STAY SILENT            │
                  │     │                              │
                  │     └──────────┬──────────────────┘
                  │                │
                  │                ▼
                  │     ┌─────────────────────────────┐
                  │     │     VOICE OUTPUT (or silence) │
                  │     │                              │
                  │     │  Adapted to:                  │
                  │     │  • Current objective           │
                  │     │  • User emotional state        │
                  │     │  • Learned preferences         │
                  │     │  • Urgency level               │
                  │     │                              │
                  │     └──────────┬──────────────────┘
                  │                │
                  │                ▼
                  │     ┌─────────────────────────────┐
                  │     │     USER RESPONSE             │
                  │     │  (speaks, acts, or silence)   │
                  │     │                              │
                  │     │  Feeds back to ALL loops:     │
                  │     │  • Reactive: new input         │
                  │     │  • Cognitive: intent signals   │
                  │     │  • Reflective: outcome data    │
                  └─────└──────────────────────────────┘
```

---

## HOW SPATIAL + TEMPORAL + DISTANCE + OBJECT ID ALL FIT

These are NOT separate features. They feed INTO the objective-driven system:

**NAVIGATE objective uses:**
- Spatial: Clock positions for obstacles and path
- Distance: Step counts to next landmark/obstacle  
- Temporal: Object velocity (approaching/receding)
- Object ID: What IS the obstacle (person vs pole vs cart)

**EXAMINE objective uses:**
- Spatial: Where exactly on the shelf (clock position + height)
- Distance: "Within arm's reach" vs "one step forward"
- Temporal: Not used much (things are static when examining)
- Object ID: Product recognition, text reading, label parsing

**FIND objective uses:**
- Spatial: Direction to search next
- Distance: How far to target ("about 15 steps ahead")
- Temporal: Tracking movement through space toward goal
- Object ID: Matching target description ("dairy sign", "blue package")

**SOCIAL objective uses:**
- Spatial: Person's clock position and facing direction
- Distance: Approaching or stationary, how close
- Temporal: Approaching speed, time to reach user
- Object ID: Person vs other, single vs group

**ORIENT objective uses:**
- Spatial: Room/space dimensions, exit locations
- Distance: How large is this space
- Temporal: How environment changes as user rotates/walks
- Object ID: Landmarks, signs, key features

All five capabilities are ALWAYS running. But the OBJECTIVE determines which ones get priority and how they're communicated.

---

## HOW THE WORLD MODEL EVOLVES (Not Just Accumulation — Understanding)

Frame 1: Raw data
```
{objects: [{type: "unknown_rectangle", position: "center", size: "small"}]}
```

Frame 5: Classified
```
{objects: [{type: "person", id: "A", position: "11 o'clock", 
            distance: "far", confidence: 0.8}],
 environment: {type: "indoor", confidence: 0.6}}
```

Frame 15: Tracked with history
```
{objects: [{type: "person", id: "A", 
            position: "11:30", distance: "medium",
            trajectory: "approaching_from_left",
            velocity: "1.2 m/s",
            predicted_position_T+3: "12 o'clock, near",
            frames_tracked: 10, confidence: 0.95}],
 environment: {type: "indoor_retail_aisle", confidence: 0.94,
               layout: {aisle_direction: "forward", 
                        estimated_length: "20_steps",
                        shelves: "both_sides"}}}
```

Frame 30: INFERRED knowledge (things the system FIGURED OUT, not just saw)
```
{inferences: [
   "This store has parallel aisles running north-south",
   "Each aisle is approximately 20 steps long",
   "Cross-aisles connect them at each end",
   "Foot traffic flows predominantly left-to-right at cross-aisles",
   "User is shopping (stopping at shelves, asking about products)",
   "User walks at approximately 1.1 m/s, step length ~0.65m",
   "User prefers brief alerts, asks for detail when interested"
]}
```

Frame 50: PREDICTIVE knowledge
```
{predictions: [
   "User is 3 aisles into the store. Based on typical layout, 
    perimeter products (dairy, meat, produce) are likely at the 
    store edges, not in center aisles.",
   "User's walking pattern suggests they're heading toward the 
    end of this aisle. They'll need to decide left or right.",
   "Foot traffic will likely increase as we approach the deli 
    area (based on noise and people flow direction).",
   "User has asked about 4 products — they seem to have a 
    shopping list. Should I ask if they want help finding 
    the next item?"
]}
```

**THIS is the world model evolving. Not just "I see more things." The system UNDERSTANDS the space, the user, and the situation — and it PREDICTS what comes next.**

---

## WHY THIS IS NOT A SCENE DESCRIBER

A scene describer says: "I see a person on the left, shelves on both sides, and a floor."

SixthSense says: "Person approaching from your left, about 8 steps away, moving at walking speed. You'll cross paths in about 5 seconds. Also, the cereal aisle ends in about 12 steps — I'll let you know when we're near the cross-aisle so you can turn toward dairy."

The difference:
- Scene description is PASSIVE and PRESENT-TENSE
- SixthSense is ACTIVE, PREDICTIVE, GOAL-ORIENTED, and ADAPTIVE

It's not watching the world. It's UNDERSTANDING the world and ACTING on that understanding.
