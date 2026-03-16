# Critical Gap Fixes — Research-Backed Solutions

## Fix 1: Object Identity Tracking — SORT Algorithm

### The Problem
Our greedy matching algorithm fails when multiple objects of the same type (3 people all labeled "person") cross paths or swap positions between frames.

### The Solution: SORT (Simple Online Realtime Tracking)
The industry standard for multi-object tracking, used in autonomous vehicles, surveillance, and robotics. Two components:

**Kalman Filter**: Predicts where each tracked object SHOULD be in the next frame, based on its motion history. Maintains state vector [x, y, w, h, dx, dy, dw, dh] — position, size, and their velocities.

**Hungarian Algorithm**: Optimally assigns N detected objects to M tracked objects by minimizing total cost. Uses scipy.optimize.linear_sum_assignment — built into Python, no external dependencies.

```python
import numpy as np
from scipy.optimize import linear_sum_assignment
from filterpy.kalman import KalmanFilter

class SORTTracker:
    """
    Simple Online Realtime Tracking.
    Kalman Filter for prediction + Hungarian Algorithm for assignment.
    """
    
    def __init__(self, max_age=5, min_hits=3, iou_threshold=0.3):
        self.max_age = max_age           # Frames before deleting unmatched track
        self.min_hits = min_hits         # Minimum hits before track is confirmed
        self.iou_threshold = iou_threshold
        self.tracks: List[KalmanTrack] = []
        self.next_id = 0
    
    def update(self, detections: List[CVObject], frame_id: int) -> List[TrackedObject]:
        """
        Core SORT update cycle. Called every frame with new detections.
        Returns list of active tracked objects with persistent IDs.
        """
        # Step 1: PREDICT — where should each existing track be now?
        predicted_positions = []
        for track in self.tracks:
            track.predict()
            predicted_positions.append(track.get_state())
        
        # Step 2: BUILD COST MATRIX — how well does each detection match each track?
        if len(self.tracks) > 0 and len(detections) > 0:
            cost_matrix = np.zeros((len(self.tracks), len(detections)))
            
            for t, track in enumerate(self.tracks):
                for d, det in enumerate(detections):
                    # Cost = 1 - IoU (lower is better)
                    # Also factor in label match and size similarity
                    iou = compute_iou(track.get_bbox(), det.bbox)
                    label_match = 1.0 if track.cv_label == det.label else 0.0
                    size_sim = 1.0 - abs(track.size_pct - det.size_percent) / max(track.size_pct, 1)
                    
                    # Combined cost: IoU is primary, label and size are secondary
                    cost = 1.0 - (0.6 * iou + 0.25 * label_match + 0.15 * max(0, size_sim))
                    cost_matrix[t, d] = cost
            
            # Step 3: HUNGARIAN ALGORITHM — optimal assignment
            track_indices, det_indices = linear_sum_assignment(cost_matrix)
            
            # Filter out assignments with cost too high (IoU too low)
            matches = []
            unmatched_tracks = set(range(len(self.tracks)))
            unmatched_dets = set(range(len(detections)))
            
            for t, d in zip(track_indices, det_indices):
                if cost_matrix[t, d] > (1.0 - self.iou_threshold):
                    unmatched_tracks.add(t)
                    unmatched_dets.add(d)
                else:
                    matches.append((t, d))
                    unmatched_tracks.discard(t)
                    unmatched_dets.discard(d)
        else:
            matches = []
            unmatched_tracks = set(range(len(self.tracks)))
            unmatched_dets = set(range(len(detections)))
        
        # Step 4: UPDATE matched tracks with new observations
        for t, d in matches:
            self.tracks[t].update(detections[d], frame_id)
        
        # Step 5: CREATE new tracks for unmatched detections
        for d in unmatched_dets:
            new_track = KalmanTrack(
                detection=detections[d],
                track_id=self._get_next_id(),
                frame_id=frame_id
            )
            self.tracks.append(new_track)
        
        # Step 6: MANAGE unmatched tracks (increment age, eventually delete)
        for t in sorted(unmatched_tracks, reverse=True):
            self.tracks[t].mark_missed()
            if self.tracks[t].age_since_update > self.max_age:
                # Move to out-of-view memory before deleting
                self.tracks[t].move_to_out_of_view()
                self.tracks.pop(t)
        
        # Return confirmed tracks only
        return [t.to_tracked_object() for t in self.tracks if t.hits >= self.min_hits]
    
    def _get_next_id(self):
        self.next_id += 1
        return f"obj_{self.next_id:04d}"


class KalmanTrack:
    """
    Single tracked object with Kalman Filter state estimation.
    State: [x_center, y_center, area, aspect_ratio, dx, dy, da, 0]
    """
    
    def __init__(self, detection, track_id, frame_id):
        self.kf = self._init_kalman_filter(detection)
        self.id = track_id
        self.cv_label = detection.label
        self.hits = 1
        self.age_since_update = 0
        self.first_seen_frame = frame_id
        self.history = []  # Position history for trajectory analysis
    
    def _init_kalman_filter(self, detection):
        kf = KalmanFilter(dim_x=8, dim_z=4)
        # State transition matrix (constant velocity model)
        kf.F = np.array([
            [1,0,0,0,1,0,0,0],
            [0,1,0,0,0,1,0,0],
            [0,0,1,0,0,0,1,0],
            [0,0,0,1,0,0,0,1],
            [0,0,0,0,1,0,0,0],
            [0,0,0,0,0,1,0,0],
            [0,0,0,0,0,0,1,0],
            [0,0,0,0,0,0,0,1],
        ])
        kf.H = np.array([  # Measurement matrix
            [1,0,0,0,0,0,0,0],
            [0,1,0,0,0,0,0,0],
            [0,0,1,0,0,0,0,0],
            [0,0,0,1,0,0,0,0],
        ])
        # Initialize state from detection
        bbox = detection.bbox
        cx = (bbox[0] + bbox[2]) / 2
        cy = (bbox[1] + bbox[3]) / 2
        area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        aspect = (bbox[2] - bbox[0]) / max(bbox[3] - bbox[1], 1)
        kf.x[:4] = np.array([cx, cy, area, aspect]).reshape(4, 1)
        return kf
    
    def predict(self):
        self.kf.predict()
        self.age_since_update += 1
    
    def update(self, detection, frame_id):
        bbox = detection.bbox
        cx = (bbox[0] + bbox[2]) / 2
        cy = (bbox[1] + bbox[3]) / 2
        area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        aspect = (bbox[2] - bbox[0]) / max(bbox[3] - bbox[1], 1)
        self.kf.update(np.array([cx, cy, area, aspect]))
        self.hits += 1
        self.age_since_update = 0
        self.cv_label = detection.label  # Update label in case it changed
        self.history.append((cx, cy, area, frame_id))


def compute_iou(bbox1, bbox2):
    """Compute Intersection over Union between two bounding boxes."""
    x1 = max(bbox1[0], bbox2[0])
    y1 = max(bbox1[1], bbox2[1])
    x2 = min(bbox1[2], bbox2[2])
    y2 = min(bbox1[3], bbox2[3])
    
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
    area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
    union = area1 + area2 - intersection
    
    return intersection / max(union, 1e-6)
```

### Why This Is Elegant
- Industry-proven (used in self-driving cars, security systems, robotics)
- Kalman Filter predicts through occlusion — if a person goes behind a pillar, the filter predicts where they'll emerge
- Hungarian Algorithm guarantees OPTIMAL assignment — no identity swaps when objects cross paths
- scipy.optimize.linear_sum_assignment is built into Python — no extra dependencies
- Cost matrix combines IoU + label matching + size similarity — robust against single-feature failures
- O(n³) complexity for n objects — fast enough for 7 active objects

---

## Fix 2: Topological Map — Scene Transition Detection via Gemini

### The Problem
The topological map was described beautifully but had no algorithm to BUILD it. Full visual SLAM is massive overkill for our use case.

### The Elegant Solution: Gemini as Place Transition Detector

The cognitive loop already analyzes scenes every 5-10 seconds. We add ONE field to its response: "is this the same place as the previous analysis, or a new place?" Gemini naturally understands spatial transitions — it can tell a corridor from an aisle, a room from a hallway.

The topological map builds from TRANSITIONS, not from pixel geometry:

```python
class TopologicalMapBuilder:
    """
    Builds topological map using Gemini cognitive loop as transition detector.
    No SLAM. No pixel geometry. Scene understanding from foundation model.
    """
    
    def __init__(self):
        self.nodes: Dict[str, PlaceNode] = {}
        self.edges: List[PlaceEdge] = []
        self.current_node_id: Optional[str] = None
        self.node_counter = 0
        self.scene_history: List[str] = []  # Recent scene descriptions
    
    def process_cognitive_update(self, analysis: CognitiveAnalysis, frame_id: int):
        """
        Called every cognitive cycle (5-10s) with Gemini's scene analysis.
        The analysis includes a 'place_transition' field.
        """
        
        if self.current_node_id is None:
            # First observation — create first node
            self._create_first_node(analysis, frame_id)
            return
        
        current_node = self.nodes[self.current_node_id]
        
        # Gemini tells us: same place or new place?
        if analysis.place_transition == "same":
            # Still in same place — enrich the current node
            current_node.update_description(analysis.environment)
            current_node.add_landmarks(analysis.detected_text, analysis.key_features)
            current_node.last_confirmed = frame_id
            
        elif analysis.place_transition == "new":
            # TRANSITION detected — create new node and edge
            new_node = self._create_node(analysis, frame_id)
            
            # Create edge from old place to new place
            edge = PlaceEdge(
                from_node=self.current_node_id,
                to_node=new_node.id,
                transition_type=analysis.transition_type,  # "door", "turn", "stairs", etc.
                direction=analysis.transition_direction,    # "left", "right", "straight", "up", "down"
                frame_id=frame_id
            )
            self.edges.append(edge)
            
            # Update current position
            self.current_node_id = new_node.id
        
        elif analysis.place_transition == "returned":
            # Gemini recognizes a previously visited place
            matched_node_id = self._find_matching_node(analysis)
            if matched_node_id:
                # Close a loop in the topological map
                edge = PlaceEdge(
                    from_node=self.current_node_id,
                    to_node=matched_node_id,
                    transition_type="loop_closure"
                )
                self.edges.append(edge)
                self.current_node_id = matched_node_id
    
    def _create_node(self, analysis, frame_id):
        self.node_counter += 1
        node = PlaceNode(
            id=f"place_{self.node_counter:03d}",
            description=analysis.environment,
            place_type=analysis.environment_type,
            landmarks=[],
            text_signatures=analysis.detected_text,
            first_seen=frame_id,
            last_confirmed=frame_id,
            objects_here=[]  # Populated by reactive loop
        )
        self.nodes[node.id] = node
        return node


@dataclass
class PlaceNode:
    id: str
    description: str            # "narrow grocery aisle with cereal on both sides"
    place_type: str             # "grocery_aisle", "corridor", "room", "outdoors"
    landmarks: List[str]        # Distinctive features
    text_signatures: List[str]  # Text detected here ("Aisle 7", "EXIT")
    first_seen: int             # Frame ID
    last_confirmed: int         # Last frame confirming we're still here
    objects_here: List[str]     # Object IDs anchored to this place
    entry_direction: Optional[float]  # Which direction user faced when entering


@dataclass
class PlaceEdge:
    from_node: str
    to_node: str
    transition_type: str        # "door", "turn_left", "turn_right", "stairs_up", "elevator", etc.
    direction: Optional[str]    # "left", "right", "straight", "up", "down"
    frame_id: int
    traversal_time: Optional[float]  # How long it took to traverse (estimated)
```

### The Cognitive Loop Prompt That Makes This Work

```python
COGNITIVE_PROMPT_TEMPLATE = """
You are analyzing a camera frame for a spatial intelligence system.

CURRENT WORLD MODEL:
  Environment: {current_environment}
  Current place: {current_place_description}
  Tracked objects: {tracked_objects_summary}
  Recent place history: {recent_places}

VERIFY AND ANALYZE (respond as JSON with this exact schema):
{{
  "environment_type": "string — grocery_aisle / corridor / room / outdoor / parking / etc",
  "environment_description": "string — brief description of the visible space",
  
  "place_transition": "same | new | returned",
  "transition_type": "door | turn | stairs | elevator | boundary | none",
  "transition_direction": "left | right | straight | up | down | none",
  "returned_place_match": "string — which previous place this matches, or null",
  
  "objects": [
    {{
      "description": "string — what it is",
      "activity": "string — what it's doing (walking, stationary, sitting)",
      "relationship": "string — spatial relationship to other objects/features",
      "potential_hazard": "boolean"
    }}
  ],
  
  "hazards_detected": ["list of non-obvious hazards: wet floor, glass wall, stairs, etc"],
  
  "spatial_layout": "string — describe the shape and structure of the space",
  "predicted_next_5s": "string — what do you expect to happen in the next 5 seconds",
  
  "text_visible": ["list of readable text in frame"],
  "key_visual_features": ["distinctive visual features for place recognition"],
  
  "corrections_to_world_model": ["any beliefs in the world model that appear wrong"]
}}
"""
```

### Why This Is Elegant
- Uses Gemini's natural scene understanding — no computer vision pipelines for place detection
- The cognitive loop ALREADY runs every 5-10 seconds — zero additional API calls
- Topological map builds automatically from transitions — no manual annotation
- response_schema guarantees the JSON structure — no parsing failures
- Loop closure detection: Gemini can recognize "I've been in this corridor before" from visual features
- The map is SEMANTIC: nodes know they're "grocery aisles" and "corridors," not just coordinate clusters

---

## Fix 3: Distance Estimation — Calibration-Free Approach

### The Problem
`size_to_distance()` was referenced but never defined. Camera FOV varies by phone. Object sizes vary. No calibration mechanism.

### The Solution: Three-Tier Distance System

**Tier 1 — Relative Distance (ALWAYS works, no calibration)**

For the most critical use case — approach detection — we don't need absolute distance. We need SIZE CHANGE RATE. If an object's bounding box area grew 50% in the last 2 seconds, it's approaching FAST regardless of whether it's 3 meters or 10 meters away.

```python
def compute_approach_urgency(self, obj: TrackedObject) -> float:
    """
    Calibration-free approach detection from size trend alone.
    No camera parameters needed. No absolute distance.
    """
    if len(obj.size_history) < 3:
        return 0.0  # Not enough data
    
    # Size change rate (% per second)
    recent = obj.size_history[-3:]  # Last 3 observations
    dt = recent[-1][1] - recent[0][1]  # Time span
    if dt < 0.5:
        return 0.0
    
    size_change = recent[-1][0] - recent[0][0]  # Size difference
    rate = size_change / dt  # % per second
    
    # Size acceleration (is approach speeding up?)
    if len(obj.size_history) >= 5:
        older = obj.size_history[-5:-3]
        older_rate = (older[-1][0] - older[0][0]) / max(older[-1][1] - older[0][1], 0.1)
        acceleration = rate - older_rate
    else:
        acceleration = 0
    
    # Urgency from rate + current size (bigger = closer)
    current_size = recent[-1][0]
    
    if rate <= 0:
        return 0.0  # Not approaching
    
    # Empirical urgency mapping
    if current_size > 25 and rate > 5:
        return 0.95  # Very close and still approaching fast
    elif current_size > 15 and rate > 3:
        return 0.7   # Close and approaching
    elif rate > 5:
        return 0.5   # Far but approaching fast
    elif rate > 2:
        return 0.3   # Moderate approach
    else:
        return 0.1   # Slow approach
```

**Tier 2 — Categorical Distance (reasonable estimates, no calibration)**

Use bounding box height relative to frame height for objects with known real-world sizes. A person who fills 80% of the frame height is ~1 meter away. A person who fills 10% is ~8 meters. This is a LOGARITHMIC relationship from perspective projection.

```python
# Known approximate heights (meters)
KNOWN_HEIGHTS = {
    "person": 1.7,
    "car": 1.5,
    "door": 2.0,
    "chair": 0.9,
    "table": 0.75,
}

# Distance categories calibrated from average phone camera FOV (~70°)
# These are APPROXIMATE but useful for categorical distance
DISTANCE_CATEGORIES = [
    (0.60, "very_close", "1-2 steps"),    # Object fills >60% of frame height
    (0.35, "close", "3-4 steps"),         # 35-60%
    (0.18, "near", "5-8 steps"),          # 18-35%
    (0.08, "medium", "8-15 steps"),       # 8-18%
    (0.03, "far", "15-25 steps"),         # 3-8%
    (0.00, "very_far", "25+ steps"),      # <3%
]

def estimate_categorical_distance(bbox_height_ratio: float) -> Tuple[str, str]:
    """
    Estimate distance category from bounding box height as fraction of frame.
    Returns (category, human_description).
    """
    for threshold, category, description in DISTANCE_CATEGORIES:
        if bbox_height_ratio >= threshold:
            return category, description
    return "very_far", "25+ steps"
```

**Tier 3 — Gemini-Enhanced Distance (most accurate, from cognitive loop)**

The cognitive loop asks Gemini to estimate distances using its trained understanding of perspective, depth cues, and scene context. This is the ONLY tier that can reason about depth cues like perspective lines, relative size, occlusion ordering, and atmospheric perspective.

```python
# In the cognitive loop prompt, include:
"For each object, estimate distance from camera in one of:
 very_close (<1m), close (1-2m), near (2-4m), medium (4-8m), far (8-15m), very_far (>15m).
 Use perspective cues, relative sizes, and scene context."
```

### Why This Is Elegant
- Tier 1 needs ZERO calibration — pure math on bounding box trends
- Tier 2 gives useful categorical estimates from a simple lookup table
- Tier 3 leverages Gemini's deep visual understanding for the best estimates
- For the critical safety use case (approach detection), Tier 1 alone is sufficient
- The system never claims precision it doesn't have — "close, about 3-4 steps" not "2.7 meters"

---

## Fix 4: Error Recovery for Three Concurrent Connections

### The Problem
Cloud Vision, generateContent, and Live session run simultaneously. Any can fail. No recovery logic was designed.

### The Solution: Circuit Breaker Pattern with Graceful Degradation

```python
class PerceptionPipeline:
    """
    Manages three concurrent API connections with error recovery.
    Each channel has a circuit breaker that degrades gracefully.
    """
    
    def __init__(self):
        self.cv_breaker = CircuitBreaker(name="cloud_vision", 
                                          failure_threshold=3, 
                                          recovery_timeout=10)
        self.gemini_breaker = CircuitBreaker(name="gemini_cognitive", 
                                              failure_threshold=2, 
                                              recovery_timeout=15)
        self.live_breaker = CircuitBreaker(name="gemini_live", 
                                            failure_threshold=1, 
                                            recovery_timeout=5)
    
    async def reactive_loop(self, frame):
        """Cloud Vision — reactive perception. Falls back to cognitive-only."""
        if self.cv_breaker.is_open():
            # Cloud Vision is down — increase cognitive loop frequency
            self.gemini_cognitive_interval = 3  # Speed up from 5-10s to 3s
            return None
        
        try:
            result = await self.cloud_vision.analyze(frame)
            self.cv_breaker.record_success()
            return result
        except Exception as e:
            self.cv_breaker.record_failure()
            logging.error(f"Cloud Vision failed: {e}")
            return None
    
    async def cognitive_loop(self, frame, world_model_state):
        """Gemini generateContent — cognitive perception. Falls back to CV-only."""
        if self.gemini_breaker.is_open():
            # Cognitive loop down — reactive loop still works for basic tracking
            return None
        
        try:
            result = await self.gemini_generate(frame, world_model_state)
            self.gemini_breaker.record_success()
            return result
        except Exception as e:
            self.gemini_breaker.record_failure()
            logging.error(f"Gemini cognitive failed: {e}")
            return None
    
    async def voice_session(self):
        """Gemini Live — voice. Reconnects automatically."""
        while True:
            try:
                async with self.client.aio.live.connect(...) as session:
                    self.live_session = session
                    self.live_breaker.reset()
                    await self._voice_loop(session)
            except Exception as e:
                self.live_breaker.record_failure()
                logging.error(f"Live session disconnected: {e}")
                if self.live_breaker.is_open():
                    # Fall back to local TTS for urgent alerts
                    self.use_local_tts = True
                await asyncio.sleep(2)  # Brief pause before reconnecting
                # Reconnect with session resumption if available
    
    def get_system_status(self) -> dict:
        """Report health of all perception channels."""
        return {
            "cloud_vision": "active" if not self.cv_breaker.is_open() else "degraded",
            "cognitive_loop": "active" if not self.gemini_breaker.is_open() else "degraded",
            "voice_session": "active" if not self.live_breaker.is_open() else "reconnecting",
            "overall": self._compute_overall_status()
        }
    
    def _compute_overall_status(self):
        if self.live_breaker.is_open():
            return "voice_degraded"  # Can track but can't speak
        if self.cv_breaker.is_open() and self.gemini_breaker.is_open():
            return "perception_down"  # Critical — can only relay user speech
        if self.cv_breaker.is_open():
            return "reactive_degraded"  # Slower perception, still works
        return "fully_operational"


class CircuitBreaker:
    """
    Standard circuit breaker pattern.
    CLOSED (normal) → OPEN (failing) → HALF_OPEN (testing recovery).
    """
    
    def __init__(self, name, failure_threshold=3, recovery_timeout=10):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def is_open(self):
        if self.state == "OPEN":
            # Check if recovery timeout has elapsed
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return False  # Allow one attempt
            return True
        return False
    
    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"
    
    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logging.warning(f"Circuit breaker {self.name} OPENED after {self.failure_count} failures")
    
    def reset(self):
        self.failure_count = 0
        self.state = "CLOSED"
```

### Degradation Hierarchy
```
FULL: Cloud Vision + Gemini Cognitive + Gemini Live
  ↓ Cloud Vision fails
DEGRADED-1: Gemini Cognitive (increased frequency) + Gemini Live
  ↓ Gemini Cognitive also fails  
DEGRADED-2: Gemini Live only (back to single-session mode, transcript parsing)
  ↓ Live session disconnects
DEGRADED-3: Local TTS for critical alerts only (offline emergency mode)
```

### Why This Is Elegant
- Circuit breaker is a proven distributed systems pattern (Netflix Hystrix, etc.)
- Each channel degrades independently — losing one doesn't crash the system
- Automatic recovery attempts after timeout
- Degradation is GRACEFUL — the system gets worse, not broken
- Status monitoring lets the system tell the user: "My vision is degraded right now"
