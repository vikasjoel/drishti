# SixthSense Framework — Redesigned
## Nothing Hardcoded. Everything Discovered. Behavior Emerges.

---

## THE FUNDAMENTAL PRINCIPLE

The framework NEVER says "you are in a grocery store."
The framework says "I observe these properties, and based on 
these properties, here's how I should behave."

There are NO enums. NO predefined categories. NO switch statements.

There are only:
1. **Observable Properties** — what can be measured from signals
2. **Property Patterns** — combinations of properties that cluster together
3. **Behavioral Rules** — if properties match pattern → adjust behavior
4. **Emergent Understanding** — patterns accumulate into knowledge

The system doesn't classify. It UNDERSTANDS through accumulated evidence.

---

## LAYER 1: OBSERVABLE PROPERTIES (The Only Ground Truth)

These are the RAW things the system can observe. Nothing interpreted. Just measured.

### From Vision (each frame)
```
frame_properties = {
    # Geometry
    "open_space_ratio":       float,  # 0.0 (walls everywhere) → 1.0 (wide open)
    "ceiling_visible":        bool,   # Can see ceiling → indoor indicator
    "sky_visible":            bool,   # Can see sky → outdoor indicator
    "floor_type":             str,    # Gemini describes: tile, carpet, concrete, grass, asphalt
    "vertical_lines_dominant": bool,  # Corridors, aisles have strong vertical lines
    "depth_variation":        str,    # shallow (wall close), medium, deep (open space)
    
    # Objects (per object detected)
    "objects": [
        {
            "description":    str,    # Gemini's description: "person in blue shirt"
            "frame_position": {       # Where in the frame (0.0-1.0 normalized)
                "center_x":  float,
                "center_y":  float,
                "width_pct": float,   # Percentage of frame width
                "height_pct": float,  # Percentage of frame height
            },
            "apparent_size":  float,  # Area as percentage of frame
            "on_ground":      bool,   # Is it on the ground plane?
        }
    ],
    
    # Text
    "text_visible":           list[str],  # Any text detected
    
    # Lighting
    "brightness":             float,  # 0.0 (dark) → 1.0 (bright)
    "brightness_uniform":     bool,   # Even lighting vs. mixed
    "artificial_light":       bool,   # Fluorescent/LED indicators
    
    # Scene dynamics
    "frame_similarity_to_previous": float,  # 0.0 (completely different) → 1.0 (identical)
    "dominant_motion_direction":    str,    # Where most change is happening
}
```

### From Audio (continuous)
```
audio_properties = {
    "ambient_noise_level":    float,  # 0.0 (silent) → 1.0 (very loud)
    "noise_type":             str,    # Gemini describes: traffic, chatter, music, machines
    "echo_present":           bool,   # Echo suggests large indoor space
    "wind_detected":          bool,   # Wind suggests outdoor
    "speech_nearby":          bool,   # Other people talking
    "user_speaking":          bool,
    "user_voice_properties": {
        "pace":               str,    # slow, normal, fast
        "volume":             str,    # quiet, normal, loud
        "tone":               str,    # calm, tense, happy, frustrated (from affective dialog)
        "tremor":             bool,   # Voice shaking (distress indicator)
    },
}
```

### From Temporal (derived across frames)
```
temporal_properties = {
    "scene_change_rate":      float,  # How fast is the scene changing (0=static, 1=rapid)
    "camera_movement_speed":  float,  # Estimated from frame-to-frame shift
    "camera_movement_steady": bool,   # Steady = walking. Jerky = looking around
    "camera_direction_changing": bool, # User is turning
    "seconds_since_scene_change": float,
    "seconds_since_user_spoke":   float,
    "seconds_since_agent_spoke":  float,
}
```

### Per-Object Temporal (derived across frames for tracked objects)
```
object_temporal_properties = {
    "object_id":              str,    # Assigned when first tracked
    "frames_tracked":         int,    # How many frames we've seen this
    "size_trend":             float,  # Positive = growing (approaching), negative = shrinking
    "position_trend_x":      float,  # Moving left (-) or right (+) in frame
    "position_trend_y":      float,  # Moving up (-) or down (+) in frame  
    "speed_of_change":        float,  # How fast are size/position changing
    "is_moving":              bool,   # Has position/size changed significantly
    "frames_since_last_seen": int,    # 0 = visible now, >0 = out of frame
    "predicted_still_exists": bool,   # Object permanence — we think it's still there
    "predicted_current_position": dict, # Where we think it is now (even if not visible)
}
```

---

## LAYER 2: PROPERTY PATTERNS (Emergent Groupings)

The system DISCOVERS patterns. It doesn't have hardcoded environments.

### How Pattern Discovery Works

The Cognitive Loop (every 5-10 seconds) looks at accumulated properties and asks Gemini:

```
"Given these observed properties over the last N frames:
- open_space_ratio has been: [0.2, 0.2, 0.3, 0.2, 0.2]
- ceiling_visible: True for 100% of frames
- sky_visible: False for 100% of frames
- floor_type observations: ['tile', 'tile', 'tile']
- vertical_lines_dominant: True for 80% of frames
- objects detected: shelves (persistent), products (persistent), 
  people (intermittent, moving), carts (intermittent)
- text visible: ['Aisle 7', 'Cereal', 'Special Offer']
- brightness: consistently 0.7
- artificial_light: True
- echo_present: False
- ambient noise: moderate, type='chatter'

What kind of space is this? What behavior properties does this 
environment suggest? What should I watch for?

Respond as JSON with discovered properties, not categories."
```

Gemini responds with DISCOVERED properties, not labels:

```json
{
  "discovered_environment_properties": {
    "enclosure": "fully_enclosed",
    "structure": "linear_passage_with_items_on_sides",
    "purpose_indicators": ["product_shelving", "price_labels", "aisle_numbering"],
    "movement_pattern": "linear_forward_or_backward",
    "typical_hazards": ["other_people", "carts", "items_on_floor", "aisle_intersections"],
    "navigation_strategy": "follow_passage_to_end_then_choose_direction",
    "expected_ahead": "passage_continues_or_ends_at_cross_passage"
  },
  "suggested_behaviors": {
    "watch_for": ["people_approaching_from_ahead", "carts_crossing", "items_protruding_from_shelves"],
    "useful_information": ["text_on_shelves_indicates_product_sections", "aisle_numbers_help_wayfinding"],
    "communication_relevance": "user_likely_wants_product_information_and_navigation_cues"
  }
}
```

**No label "grocery store aisle" needed.** The system understands through properties:
- It's a linear passage → follow it
- Items on sides → can be examined
- Other people move through → track them
- Text indicates sections → read and announce when relevant

If the system encounters a warehouse aisle, library stack, or hospital corridor — the SAME property patterns will partially match, and behavior will naturally adapt. No new code needed.

### Property Pattern Memory

Over the session, discovered patterns accumulate:

```python
class PropertyPatternMemory:
    """
    Stores discovered environment patterns.
    NOT a lookup table. A growing understanding.
    """
    
    def __init__(self):
        self.observations = []     # Raw property snapshots
        self.patterns = []         # Discovered patterns
        self.transitions = []      # Observed pattern changes
        self.predictions = []      # What we expect based on patterns
    
    def add_observation(self, properties: dict, frame_id: int):
        self.observations.append({
            "frame": frame_id,
            "properties": properties,
            "timestamp": time.time()
        })
    
    def discover_patterns(self):
        """
        Ask Gemini to find patterns in accumulated observations.
        This runs every 10-15 seconds.
        """
        recent = self.observations[-15:]  # Last 15 frames
        
        # Gemini finds patterns across these observations
        # Returns: what's consistent, what's changing, what's predicted
        pass
    
    def detect_transition(self, new_properties, old_pattern):
        """
        Properties changed significantly → pattern is transitioning.
        NOT a hardcoded transition. Detected from property deltas.
        """
        deltas = self.compute_property_deltas(new_properties, old_pattern)
        significant_changes = [d for d in deltas if d.magnitude > threshold]
        
        if significant_changes:
            return PropertyTransition(
                changed_properties=significant_changes,
                likely_meaning=None,  # Gemini will interpret
                frame=self.current_frame
            )
        return None
```

---

## LAYER 3: BEHAVIORAL DIMENSIONS (Not States — Continuous Scales)

Instead of discrete states, behavior exists on CONTINUOUS DIMENSIONS:

```
BEHAVIORAL_DIMENSIONS = {
    
    "vigilance": {
        # 0.0 = completely relaxed monitoring
        # 1.0 = maximum alertness, tracking everything
        driven_by: [
            "number_of_moving_objects",
            "speed_of_approaching_objects",
            "environment_complexity",
            "user_emotional_tension",
            "recent_near_miss_events",
        ],
        affects: [
            "how_many_objects_tracked_actively",
            "how_quickly_alerts_are_triggered",
            "how_much_attention_to_periphery",
        ]
    },
    
    "verbosity": {
        # 0.0 = complete silence
        # 1.0 = continuous narration
        driven_by: [
            "user_preference_learned",
            "environment_complexity",
            "how_much_is_changing",
            "user_emotional_state",
            "time_since_last_spoke",
            "user_explicitly_asked_for_more_or_less",
        ],
        affects: [
            "how_often_agent_speaks_unprompted",
            "how_detailed_descriptions_are",
            "whether_ambient_updates_are_given",
        ]
    },
    
    "detail_focus": {
        # 0.0 = broad scene awareness (wide view, general)
        # 1.0 = narrow detail focus (close up, specific)
        driven_by: [
            "user_is_stationary_and_facing_close_object",
            "user_asked_about_specific_thing",
            "camera_steady_on_one_area",
            "text_detected_that_might_need_reading",
        ],
        affects: [
            "media_resolution_setting",
            "what_perceiver_asks_about",
            "whether_OCR_is_prioritized",
        ]
    },
    
    "proactivity": {
        # 0.0 = only respond when asked
        # 1.0 = constantly volunteering information
        driven_by: [
            "use_case_config_base_level",
            "user_feedback_on_proactive_alerts",
            "how_dynamic_the_environment_is",
            "user_activity_level",
        ],
        affects: [
            "proactive_audio_sensitivity",
            "whether_to_announce_new_objects",
            "whether_to_announce_environment_changes",
        ]
    },
    
    "urgency": {
        # 0.0 = nothing time-sensitive
        # 1.0 = immediate action needed
        driven_by: [
            "approaching_object_velocity",
            "proximity_of_nearest_risk",
            "floor_level_change_detected",
            "user_appears_disoriented",
        ],
        affects: [
            "communication_speed_and_brevity",
            "whether_to_interrupt_current_speech",
            "tone_of_voice",
        ]
    },
    
    "social_awareness": {
        # 0.0 = ignore social context
        # 1.0 = fully socially aware
        driven_by: [
            "people_nearby",
            "someone_approaching_user",
            "conversation_detected",
            "user_facing_person",
        ],
        affects: [
            "voice_volume",
            "whether_to_pause_during_nearby_conversation",
            "whether_to_announce_people",
        ]
    },
    
    "exploration": {
        # 0.0 = following known path, no curiosity
        # 1.0 = actively mapping and discovering
        driven_by: [
            "environment_is_new",
            "layout_knowledge_is_low",
            "user_asked_about_surroundings",
            "user_appears_to_be_searching",
        ],
        affects: [
            "how_much_attention_to_signs_and_landmarks",
            "whether_to_build_spatial_memory",
            "whether_to_announce_layout_discoveries",
        ]
    },
}
```

**Every frame, these dimensions are RECALCULATED** from current properties. There's no discrete "entering NAVIGATE state." Instead, vigilance goes up, detail_focus goes down, proactivity adjusts, and behavior EMERGES from the combination.

---

## LAYER 4: THE GOAL SYSTEM (Emergent, Not Assigned)

Goals aren't assigned from a list. They EMERGE from property patterns + behavioral dimensions + user signals.

### How Goals Emerge

```python
class GoalEngine:
    """
    Goals are not predefined. They emerge from the situation.
    """
    
    def __init__(self):
        self.active_goals = []
        self.completed_goals = []
        self.pending_user_intents = []
    
    def evaluate_goals(self, properties, dimensions, user_signals):
        """
        Called every cognitive cycle. Determines what the system
        should be trying to achieve RIGHT NOW.
        """
        
        new_goals = []
        
        # --- SAFETY GOALS (always evaluated first) ---
        for obj in properties.tracked_objects:
            if obj.size_trend > 0 and obj.speed_of_change > threshold:
                # Something is approaching fast
                new_goals.append(Goal(
                    type="track_and_warn",
                    target=obj.object_id,
                    urgency=calculate_urgency(obj),
                    reason=f"Object approaching: size_trend={obj.size_trend}, "
                           f"speed={obj.speed_of_change}",
                    success_condition="object stops approaching OR user acknowledges",
                ))
        
        # --- USER-REQUESTED GOALS ---
        for intent in user_signals.recent_intents:
            if intent.type == "find_something":
                new_goals.append(Goal(
                    type="search",
                    target=intent.target_description,
                    urgency=0.5,
                    reason=f"User asked: '{intent.raw_text}'",
                    success_condition="target found and announced",
                    strategy="scan_frames_for_match + check_signs + use_layout_knowledge",
                ))
            elif intent.type == "describe_something":
                new_goals.append(Goal(
                    type="describe",
                    target=intent.target_description or "current_scene",
                    urgency=0.6,
                    reason=f"User asked: '{intent.raw_text}'",
                    success_condition="description delivered and user satisfied",
                ))
            elif intent.type == "navigate_to":
                new_goals.append(Goal(
                    type="guide",
                    target=intent.destination,
                    urgency=0.5,
                    reason=f"User wants to go to: '{intent.destination}'",
                    success_condition="user reaches destination",
                    strategy="use_signs + layout_knowledge + spatial_memory",
                ))
        
        # --- SITUATION-EMERGENT GOALS ---
        
        # Environment is new/unknown → goal to understand it
        if properties.pattern_confidence < 0.5:
            new_goals.append(Goal(
                type="understand_environment",
                urgency=0.4,
                reason="Low confidence in environment understanding",
                success_condition="pattern_confidence > 0.8",
            ))
        
        # User has been silent and stationary for a while
        if (properties.seconds_since_user_spoke > 30 and 
            properties.camera_movement_speed < 0.1):
            new_goals.append(Goal(
                type="check_in",
                urgency=0.2,
                reason="User has been quiet and still for 30s",
                success_condition="user responds or situation changes",
            ))
        
        # Something interesting detected that user might want to know
        if properties.text_visible and self.text_seems_relevant():
            new_goals.append(Goal(
                type="inform",
                content=f"Relevant text detected: {properties.text_visible}",
                urgency=0.3,
                reason="Text detected that matches user's likely interests",
                success_condition="information delivered",
            ))
        
        # User seems lost (turning around, slow movement, hesitation)
        if self.detect_disorientation(properties):
            new_goals.append(Goal(
                type="assist_orientation",
                urgency=0.6,
                reason="User movement pattern suggests disorientation",
                success_condition="user resumes confident movement",
                strategy="describe_surroundings + offer_help",
            ))
        
        # --- PRIORITIZE AND MERGE ---
        self.active_goals = self.merge_and_prioritize(
            existing=self.active_goals,
            new=new_goals
        )
    
    def merge_and_prioritize(self, existing, new):
        """
        Merge new goals with existing. Don't duplicate.
        Higher urgency takes priority.
        Remove completed goals.
        """
        all_goals = existing + new
        
        # Remove duplicates (same type + same target)
        deduplicated = self.deduplicate(all_goals)
        
        # Remove completed
        active = [g for g in deduplicated if not g.is_completed()]
        
        # Sort by urgency
        active.sort(key=lambda g: g.urgency, reverse=True)
        
        return active
```

### Goal Completion and Learning

```python
class Goal:
    def __init__(self, type, urgency, reason, success_condition, **kwargs):
        self.type = type
        self.urgency = urgency
        self.reason = reason
        self.success_condition = success_condition
        self.created_at = time.time()
        self.progress = 0.0
        self.outcome = None  # Will be: succeeded / failed / abandoned / superseded
        self.kwargs = kwargs
    
    def evaluate_completion(self, current_properties, user_response):
        """Check if goal has been achieved."""
        # This is where Gemini evaluates:
        # "Given the goal '{self.type}' with success condition 
        #  '{self.success_condition}', and current properties, 
        #  has this goal been met?"
        pass
    
    def record_outcome(self, outcome, context):
        """
        Record how this goal ended. This feeds the learning system.
        
        The system learns:
        - "Goals of type 'track_and_warn' at urgency 0.3 are often 
           dismissed → maybe raise the urgency threshold"
        - "Goals of type 'search' typically take 20-30 seconds in 
           this environment → set expectations accordingly"
        - "User frequently creates 'find' goals for food items → 
           maybe scan for food-related signs proactively"
        """
        self.outcome = outcome
        self.completed_at = time.time()
        self.duration = self.completed_at - self.created_at
```

---

## LAYER 5: THE PERCEPTION DIRECTOR (What to Look For)

The Perceiver doesn't process every frame the same way. The active goals + behavioral dimensions DIRECT what it focuses on:

```python
class PerceptionDirector:
    """
    Generates the perception query for each frame based on
    current goals, dimensions, and accumulated knowledge.
    """
    
    def generate_perception_query(self, frame, goals, dimensions, memory):
        """
        Instead of "describe this frame" (dumb),
        generate a DIRECTED question (smart).
        """
        
        query_parts = []
        
        # Base: always track known objects
        if memory.tracked_objects:
            tracked_descriptions = [
                f"Object '{obj.id}' ({obj.description}) was last at "
                f"frame position ({obj.last_x:.1f}, {obj.last_y:.1f}), "
                f"size {obj.last_size_pct:.1f}%"
                for obj in memory.tracked_objects
                if obj.frames_since_last_seen < 10
            ]
            query_parts.append(
                f"TRACK these objects — find them and report new position and size:\n"
                + "\n".join(tracked_descriptions)
            )
        
        # High vigilance → scan for new moving things
        if dimensions.vigilance > 0.5:
            query_parts.append(
                "SCAN for any NEW objects not previously tracked, "
                "especially moving ones. Report position and apparent size."
            )
        
        # Active search goal → look for specific target
        search_goals = [g for g in goals if g.type == "search"]
        for sg in search_goals:
            query_parts.append(
                f"SEARCH for: {sg.target}. Check all visible text, "
                f"signs, and objects for matches or related indicators."
            )
        
        # High detail_focus → read text carefully
        if dimensions.detail_focus > 0.7:
            query_parts.append(
                "READ all visible text carefully. Report exact content."
            )
        
        # High exploration → describe environment structure
        if dimensions.exploration > 0.5:
            query_parts.append(
                "DESCRIBE the spatial structure: How open is this space? "
                "What's the layout? Where are exits/paths? Any landmarks?"
            )
        
        # High social_awareness → focus on people
        if dimensions.social_awareness > 0.5:
            query_parts.append(
                "PEOPLE focus: How many? Where? Approaching or stationary? "
                "Facing the camera (toward user) or away?"
            )
        
        # Safety always → floor and path
        if dimensions.vigilance > 0.3:
            query_parts.append(
                "PATH check: Any floor level changes, wet surface, "
                "obstacles in the walking path, or edges/drops?"
            )
        
        # Compose into single directed perception prompt
        return "\n\n".join(query_parts)
```

**Every frame gets a DIFFERENT question** based on current goals and dimensions. The system's attention is always directed, never wasteful.

---

## LAYER 6: THE DECISION ENGINE (When and What to Communicate)

```python
class DecisionEngine:
    """
    Decides what to say, when, and how — based on goals,
    dimensions, and the communication queue.
    """
    
    def evaluate(self, goals, dimensions, perception_result, memory):
        """
        Returns: Action (speak / stay_silent / queue_for_later)
        """
        
        candidates = []
        
        # Check each active goal — does it need communication?
        for goal in goals:
            action = goal.needs_communication(perception_result, memory)
            if action:
                candidates.append(action)
        
        if not candidates:
            # Nothing from goals. Check if ambient update is warranted.
            if self.ambient_update_warranted(dimensions):
                candidates.append(Action(
                    type="ambient_update",
                    content=self.generate_ambient(perception_result, memory),
                    urgency=0.1
                ))
        
        if not candidates:
            return Action(type="stay_silent")
        
        # Pick highest urgency
        best = max(candidates, key=lambda a: a.urgency)
        
        # But check: should we actually speak?
        if self.should_suppress(best, dimensions):
            return Action(type="queue", original=best, reason=self.suppress_reason)
        
        return best
    
    def should_suppress(self, action, dimensions):
        """
        Sometimes the right thing is to NOT speak even though
        there's something to say.
        """
        # Don't speak over the user
        if dimensions.user_is_speaking:
            self.suppress_reason = "user_speaking"
            return True
        
        # Don't speak if we JUST spoke (give user breathing room)
        if dimensions.seconds_since_agent_spoke < 2 and action.urgency < 0.8:
            self.suppress_reason = "too_soon_after_last_speech"
            return True
        
        # Don't speak during detected conversation nearby
        if dimensions.social_awareness > 0.7 and action.urgency < 0.7:
            self.suppress_reason = "social_situation"
            return True
        
        return False
    
    def shape_communication(self, action, dimensions, user_model):
        """
        Shape HOW to say it based on behavioral dimensions.
        """
        # Urgency high → short, direct
        if dimensions.urgency > 0.7:
            action.style = "terse"
            action.max_words = 8
        
        # User is frustrated → be calm and clear
        elif user_model.emotional_trend == "frustrated":
            action.style = "calm_supportive"
            action.max_words = 15
        
        # User is curious → be descriptive
        elif user_model.emotional_trend == "curious":
            action.style = "descriptive"
            action.max_words = 40
        
        # Default → based on learned preference
        else:
            action.style = user_model.preferred_style
            action.max_words = user_model.preferred_length
        
        return action
```

---

## LAYER 7: THE LEARNING SYSTEM (Continuous Self-Improvement)

```python
class LearningSystem:
    """
    Observes everything. Adjusts everything. No hardcoded rules.
    """
    
    def __init__(self):
        self.outcome_log = []
        self.parameter_adjustments = {}
        self.discovered_preferences = {}
        self.environment_knowledge = {}
    
    def observe_outcome(self, action_taken, user_response, context):
        """Every action and its outcome is recorded."""
        self.outcome_log.append({
            "action": action_taken,
            "response": user_response,
            "context": context,
            "timestamp": time.time()
        })
    
    def run_learning_cycle(self):
        """
        Every 30-60 seconds, analyze outcomes and adjust.
        
        This uses Gemini to reason about patterns:
        "Given these recent actions and user responses, 
         what should I adjust about my behavior?"
        """
        recent_outcomes = self.outcome_log[-20:]
        
        # Ask Gemini to analyze patterns
        analysis_prompt = f"""
        Review these recent actions and user responses:
        {json.dumps(recent_outcomes, indent=2)}
        
        What patterns do you see? What should be adjusted?
        
        Consider:
        - Are alerts being acknowledged or dismissed?
        - Is the user asking for more or less detail?
        - Are there repeated questions suggesting unmet needs?
        - Is the communication timing appropriate?
        - What does the user seem to care about most?
        
        Respond with specific parameter adjustments as JSON:
        {{
            "vigilance_adjustment": float (-0.2 to +0.2),
            "verbosity_adjustment": float (-0.2 to +0.2),
            "proactivity_adjustment": float (-0.2 to +0.2),
            "detail_focus_adjustment": float (-0.2 to +0.2),
            "discovered_preferences": [list of new things learned],
            "suggested_behavior_changes": [list of changes]
        }}
        """
        
        # Apply adjustments to behavioral dimensions
        # This is REAL learning — the system's behavior genuinely 
        # changes based on accumulated evidence
```

---

## HOW IT ALL CONNECTS (The Complete Flow)

```
EVERY FRAME (1 second):
│
├─ 1. OBSERVE: Measure all observable properties from frame + audio
│
├─ 2. TRACK: Update tracked objects (position, size, trends)
│
├─ 3. DIRECT PERCEPTION: Based on current goals + dimensions,
│     ask Gemini SPECIFIC questions about this frame
│     (not "describe this" but "where is object X now? any new threats?")
│
├─ 4. UPDATE PROPERTIES: New measurements refine all property values
│
├─ 5. RECALCULATE DIMENSIONS: vigilance, verbosity, detail_focus,
│     proactivity, urgency, social_awareness, exploration
│     (continuous values, not discrete states)
│
├─ 6. EVALUATE GOALS: Do current goals still apply? Any new goals
│     emerged from properties? Any goals completed?
│
├─ 7. DECIDE: Based on goals + dimensions + user state,
│     what action to take? Speak? Stay silent? Queue?
│
├─ 8. COMMUNICATE (if decided): Shape the message based on
│     dimensions (urgency → terse, curious → detailed)
│
└─ 9. RECORD: Log the action and wait for user response

EVERY 5-10 SECONDS (Cognitive cycle):
│
├─ 1. DISCOVER PATTERNS: Ask Gemini to find patterns in
│     accumulated properties
│
├─ 2. INJECT CONTEXT: Updated world model state into Gemini session
│
├─ 3. GENERATE PREDICTIONS: What's likely coming next?
│
└─ 4. DIRECT NEXT PERCEPTION CYCLE: Adjust what to look for

EVERY 30-60 SECONDS (Learning cycle):
│
├─ 1. ANALYZE OUTCOMES: What worked, what didn't?
│
├─ 2. ADJUST DIMENSIONS: Shift behavioral baselines
│
├─ 3. UPDATE USER MODEL: Refined understanding of preferences
│
└─ 4. EVOLVE GOALS: New latent goals from observed patterns
```

---

## WHY THIS IS A FRAMEWORK

A domain plugin ONLY needs to specify:

```python
class MyDomainPlugin:
    def initial_dimension_biases(self):
        """Starting point for behavioral dimensions."""
        return {
            "vigilance": 0.7,      # Start attentive
            "proactivity": 0.8,    # Be proactive
            "verbosity": 0.4,      # Not too chatty
            # ... other dimensions
        }
    
    def priority_properties(self):
        """What object/environment properties matter most."""
        return [
            "approaching_objects",
            "floor_level_changes", 
            "text_on_signs",
        ]
    
    def communication_preferences(self):
        """How to communicate."""
        return {
            "spatial_format": "clock_positions",
            "distance_format": "steps",
            "voice": "Kore",
        }
```

That's it. ~20 lines. Everything else — discovery, tracking, goals, 
decisions, learning — is the framework. The plugin just biases the 
starting behavior. The system evolves from there.

New domain? New plugin. Same framework. Zero changes to core code.
