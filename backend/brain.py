"""
Brain — decision engine for Drishti v3.1.
Computes urgency, formats structured narrator's notes,
detects scene changes, filters by relevance,
generates predict-verify results, and provides reassurance.

v3.1 changes:
- Alert format is structured narrator's notes, not REPEAT EXACTLY
- Works with both MobileCameraTracker and SORTTracker outputs
- Uses independent_growth when available (mobile tracker)
"""

import time

from backend.logger import log_event

# Labels that always get reported for navigation safety
ALWAYS_REPORT_LABELS = {
    "person", "man", "woman", "child", "people", "pedestrian",
    "stairs", "staircase", "step", "curb",
    "door", "gate", "entrance", "exit",
    "car", "vehicle", "truck", "bicycle", "motorcycle",
    "dog", "cat", "animal",
}

# Labels for objects that never move
INHERENTLY_STATIONARY = {
    "window", "wall", "door", "doorway", "ceiling", "floor",
    "shelf", "bookshelf", "cabinet", "counter", "sink",
    "tv", "television", "monitor", "screen", "mirror",
    "painting", "picture", "frame", "clock",
    "light", "lamp", "chandelier", "fan",
    "curtain", "blind", "rug", "carpet",
    "table", "desk", "chair", "couch", "sofa", "bed",
    "refrigerator", "oven", "microwave", "toilet",
}

# Path-blocking detection (independent of tracker)
def is_path_blocked(objects: list[dict]) -> dict | None:
    """Is there anything large directly ahead?"""
    for obj in objects:
        if (obj.get("area_pct", 0) > 12
                and 0.30 < obj.get("center_x", 0.5) < 0.70
                and obj.get("center_y", 0.5) > 0.3):
            return obj
    return None


def _distance_from_area(area_pct: float) -> str:
    if area_pct > 20:
        return "very close"
    elif area_pct > 10:
        return "close"
    elif area_pct > 5:
        return "near"
    elif area_pct > 2:
        return "medium distance"
    elif area_pct > 0.5:
        return "far"
    return "very far"


class Brain:
    def __init__(self, alert_threshold=0.4, cooldown_seconds=4.0):
        self.alert_threshold = alert_threshold
        self.cooldown_seconds = cooldown_seconds
        self.frame_count = 0
        self.last_alert_time = 0
        self.last_alert_text = ""
        self.last_reassurance_time = 0
        self.predictions: dict = {}
        self.corrections: list = []
        self.alerted_stationary: set = set()
        self.corrected_objects: set = set()
        self.reported_objects: dict = {}  # {track_id: timestamp_first_reported}
        self.report_once_cooldown = 30.0
        self.current_track_ids: set = set()
        self.prev_track_ids: set = set()

    def _is_relevant(self, track: dict) -> bool:
        """
        Tier 1: Always — approaching, path blockers, navigation-critical labels
        Tier 2: Report once — stationary objects close enough to matter
        Tier 3: Never report proactively
        """
        track_id = track.get("id", "")
        label = track.get("label", "").lower()
        approaching = track.get("approaching", False)
        area = track.get("area_pct", 0)
        center_x = track.get("center_x", 0.5)
        frames_tracked = track.get("frames_tracked", 0)
        now = time.time()

        # TIER 1: Always report
        if approaching and area > 3:
            return True
        if label in ALWAYS_REPORT_LABELS and area > 3:
            return True
        if 0.30 <= center_x <= 0.70 and area > 12:
            return True

        # TIER 2: Report once, then suppress for cooldown
        if area > 5 and frames_tracked >= 3:
            if track_id not in self.reported_objects:
                self.reported_objects[track_id] = now
                return True
            elif (now - self.reported_objects[track_id]) > self.report_once_cooldown:
                self.reported_objects[track_id] = now
                return True
            else:
                return False

        # TIER 3: Don't report
        return False

    def _compute_urgency(self, track: dict) -> float:
        track_id = track.get("id", "")
        label = track.get("label", "").lower()
        approaching = track.get("approaching", False)
        size_trend = track.get("size_trend", 0)
        area = track.get("area_pct", 0)
        frames_tracked = track.get("frames_tracked", 0)
        center_x = track.get("center_x", 0.5)
        is_stationary = track.get("is_stationary", False)

        # Use independent_growth if available (from MobileCameraTracker)
        independent_growth = track.get("independent_growth", None)
        acceleration = track.get("acceleration", 0)

        # Inherently stationary objects: report once at low urgency
        if label in INHERENTLY_STATIONARY:
            if track_id in self.reported_objects:
                return 0.0
            return 0.15

        # SORT/mobile-detected stationary objects: report once
        if is_stationary and frames_tracked > 5:
            if track_id in self.reported_objects:
                return 0.0
            else:
                return min(0.3, area * 0.02)

        u = 0.0

        # Mobile tracker path: use independent_growth + acceleration
        if independent_growth is not None:
            if independent_growth > 1.5 and acceleration > 0.3:
                u += 0.5  # Strong independent approach signal
            elif independent_growth > 1.0:
                u += 0.3
            elif independent_growth > 0.5:
                u += 0.15
        else:
            # SORT tracker path: use size_trend
            if approaching and size_trend > 0.3:
                u += 0.4
                u += min(0.3, size_trend * 0.15)

        # Close + approaching
        if approaching:
            if area > 20:
                u += 0.3
            elif area > 10:
                u += 0.2
            elif area > 5:
                u += 0.1

        # New object blocking path (first 5 frames)
        if frames_tracked < 5 and area > 8 and 0.30 <= center_x <= 0.70:
            u += 0.3

        # People
        if label in ("person", "man", "woman", "child", "people", "pedestrian"):
            u += 0.1

        # Navigation-critical
        if label in ("stairs", "staircase", "curb", "step"):
            u += 0.2

        # Stationary penalty: tracked 8+ frames and NOT approaching
        if not approaching and frames_tracked > 8:
            u *= 0.05

        return min(1.0, u)

    def process(self, tracks: list[dict], texts: list[str]) -> dict:
        self.frame_count += 1
        now = time.time()

        # --- Scene change detection ---
        self.prev_track_ids = self.current_track_ids.copy()
        self.current_track_ids = {t.get("id", "") for t in tracks}

        if self.prev_track_ids:
            survived = self.current_track_ids & self.prev_track_ids
            survival_rate = len(survived) / len(self.prev_track_ids)
            if survival_rate < 0.5 and len(self.prev_track_ids) >= 3:
                self.last_alert_text = ""
                log_event("brain", "scene_change", details={
                    "prev_tracks": len(self.prev_track_ids),
                    "survived": len(survived),
                    "survival_rate": round(survival_rate, 2),
                })
                return {
                    "action": "scene_change",
                    "text": "",
                    "urgency": 0.0,
                    "tracks": self._annotate_tracks(tracks),
                    "texts": texts,
                    "verify": [],
                }

        # --- Predict-verify ---
        verify_results = []
        for t in tracks:
            pred = self.predictions.get(t.get("id"))
            if pred:
                predicted_area = pred["predicted_area"]
                actual_area = t.get("area_pct", 0)
                error = abs(predicted_area - actual_area)
                verify_results.append({
                    "id": t.get("id", ""),
                    "label": t.get("label", ""),
                    "predicted_area": round(predicted_area, 1),
                    "actual_area": round(actual_area, 1),
                    "predicted_approach": pred["will_approach"],
                    "actual_approach": t.get("approaching", False),
                    "verdict": "confirmed" if error < 1.5 else "corrected",
                })

        # --- Compute urgency (only relevant tracks) ---
        max_urgency = 0.0
        best_track = None

        for t in tracks:
            if not self._is_relevant(t):
                continue
            u = self._compute_urgency(t)
            if u > max_urgency:
                max_urgency = u
                best_track = t

        # --- Path blocked check (independent of tracking) ---
        blocker = is_path_blocked(tracks)
        if blocker and max_urgency < 0.5:
            blocker_u = 0.6  # Path blockers always urgent
            if blocker_u > max_urgency:
                max_urgency = blocker_u
                best_track = blocker

        # --- Self-correction check ---
        correction = self._check_corrections(tracks)
        if correction:
            self.corrections.append(correction)
            log_event("brain", "self_correction", details={"text": correction})
            return {
                "action": "correction",
                "text": correction,
                "urgency": 0.3,
                "tracks": self._annotate_tracks(tracks),
                "texts": texts,
                "verify": verify_results,
            }

        # --- Generate predictions for next frame ---
        self.predictions = {}
        for t in tracks:
            trend = t.get("independent_growth", t.get("size_trend", 0))
            self.predictions[t.get("id", "")] = {
                "predicted_area": round(t.get("area_pct", 0) + trend, 1),
                "will_approach": t.get("approaching", False),
            }

        # --- Clean up stale state ---
        self.alerted_stationary &= self.current_track_ids
        self.corrected_objects &= self.current_track_ids
        if self.frame_count % 100 == 0:
            active_ids = self.current_track_ids
            self.reported_objects = {
                k: v for k, v in self.reported_objects.items()
                if k in active_ids or (now - v) < 60
            }

        # --- Alert decision ---
        if (
            best_track
            and max_urgency > self.alert_threshold
            and (now - self.last_alert_time) > self.cooldown_seconds
        ):
            # Don't re-alert stationary objects already mentioned
            if not best_track.get("approaching") and best_track.get("id", "") in self.alerted_stationary:
                pass
            else:
                text = self._format_alert(best_track)
                if text != self.last_alert_text:
                    self.last_alert_time = now
                    self.last_alert_text = text
                    if not best_track.get("approaching"):
                        self.alerted_stationary.add(best_track.get("id", ""))
                    log_event("brain", "alert", details={
                        "text": text, "urgency": round(max_urgency, 2),
                        "track_id": best_track.get("id", ""),
                        "approaching": best_track.get("approaching", False),
                        "frames_tracked": best_track.get("frames_tracked", 0),
                    })
                    return {
                        "action": "alert",
                        "text": text,
                        "urgency": max_urgency,
                        "tracks": self._annotate_tracks(tracks),
                        "texts": texts,
                        "verify": verify_results,
                    }

        # --- Reassurance: clear ahead ---
        if (
            (now - self.last_alert_time) > 8.0
            and (now - self.last_reassurance_time) > 12.0
            and tracks
        ):
            path_blocked = any(
                t.get("approaching")
                or (t.get("area_pct", 0) > 10 and 0.35 < t.get("center_x", 0.5) < 0.65)
                for t in tracks
            )
            if not path_blocked:
                self.last_reassurance_time = now
                return {
                    "action": "reassurance",
                    "text": "Path ahead is clear",
                    "urgency": 0.05,
                    "tracks": self._annotate_tracks(tracks),
                    "texts": texts,
                    "verify": verify_results,
                }

        return {
            "action": "silent",
            "text": "",
            "urgency": max_urgency,
            "tracks": self._annotate_tracks(tracks),
            "texts": texts,
            "verify": verify_results,
        }

    def _annotate_tracks(self, tracks: list[dict]) -> list[dict]:
        """Add relevance flag to each track for frontend rendering."""
        result = []
        for t in tracks:
            t_copy = dict(t)
            t_copy["relevant"] = self._is_relevant(t)
            result.append(t_copy)
        return result

    def _format_alert(self, track: dict) -> str:
        """Structured narrator's note — Gemini decides how to say it."""
        label = track.get("label", "obstacle")
        direction = track.get("direction", "ahead")
        center_x = track.get("center_x", 0.5)
        area = track.get("area_pct", 0)
        approaching = track.get("approaching", False)
        distance = track.get("distance", _distance_from_area(area))

        parts = [f"SPATIAL UPDATE: {label} detected {direction}"]
        parts.append(f"distance: {distance}")

        if approaching:
            independent = track.get("independent_growth")
            if independent and independent > 2.0:
                parts.append("moving toward you quickly")
            elif approaching:
                parts.append("approaching")

        # Object directly ahead AND close -> give step guidance
        if 0.35 <= center_x <= 0.65 and area > 8:
            parts.append("blocking your path")
            if center_x < 0.5:
                parts.append("step right to avoid")
            else:
                parts.append("step left to avoid")

        return ". ".join(parts) + "."

    def _check_corrections(self, tracks: list[dict]) -> str | None:
        if not self.predictions:
            return None
        for t in tracks:
            track_id = t.get("id", "")
            if track_id in self.corrected_objects:
                continue
            pred = self.predictions.get(track_id)
            if not pred:
                continue
            if pred["will_approach"] and not t.get("approaching") and t.get("frames_tracked", 0) > 10:
                self.corrected_objects.add(track_id)
                label = t.get("label", "object")
                direction = t.get("direction", "ahead")
                return (
                    f"CORRECTION: {label} at {direction} was reported as approaching "
                    f"but is actually stationary. Path is clear on that side."
                )
        return None
