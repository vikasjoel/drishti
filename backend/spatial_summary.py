"""
SpatialSummary — persistent Python-side spatial memory.

Survives Gemini context window compression by being re-injected
every INJECTION_INTERVAL seconds as a compact text summary.
"""

import time
import logging

from backend.logger import log_event

logger = logging.getLogger(__name__)

INJECTION_INTERVAL = 30  # seconds


class SpatialSummary:
    def __init__(self):
        self.environment_type = "unknown"
        self.stable_objects: dict = {}  # label -> {direction, distance, area_pct, approaching}
        self.landmarks: list = []  # Notable text observations (signs, shops)
        self.recent_alerts: list = []  # Last 5 alerts with timestamps
        self.session_metrics = {
            "frames_processed": 0,
            "alerts_sent": 0,
            "corrections_made": 0,
            "scene_changes": 0,
            "reassurances": 0,
            "session_start": time.time(),
        }
        self.places_visited: list = []
        self.last_injection_time = 0

    def update_from_tracks(self, tracks: list[dict], cv_result: dict):
        """Update persistent memory from tracker output."""
        self.session_metrics["frames_processed"] += 1

        for track in tracks:
            label = track.get("label", "")
            frames = track.get("frames_tracked", 0)
            if frames >= 3:
                self.stable_objects[label] = {
                    "direction": track.get("direction", "ahead"),
                    "distance": track.get("distance", "unknown"),
                    "area_pct": track.get("area_pct", 0),
                    "approaching": track.get("approaching", False),
                }

        # Expire objects not seen in current tracks
        current_labels = {t.get("label", "") for t in tracks}
        stale = [k for k in self.stable_objects if k not in current_labels]
        for k in stale:
            del self.stable_objects[k]

        # Store OCR text as landmarks
        if cv_result.get("text"):
            for text in cv_result["text"][:3]:
                if len(text) > 2 and text not in [l["text"] for l in self.landmarks]:
                    self.landmarks.append({
                        "text": text,
                        "frame": self.session_metrics["frames_processed"],
                    })
            self.landmarks = self.landmarks[-20:]

    def update_from_cognitive(self, cognitive_result: dict):
        """Update from Gemini generateContent scene analysis."""
        if not cognitive_result:
            return
        new_env = cognitive_result.get("environment_type", "")
        if new_env and new_env != self.environment_type:
            self.session_metrics["scene_changes"] += 1
            self.places_visited.append({
                "from": self.environment_type,
                "to": new_env,
                "frame": self.session_metrics["frames_processed"],
            })
            self.environment_type = new_env

            log_event("spatial_summary", "environment_change", details={
                "from": self.places_visited[-1]["from"],
                "to": new_env,
            })

    def record_alert(self, text: str, urgency: float):
        """Record an alert that was sent."""
        self.session_metrics["alerts_sent"] += 1
        self.recent_alerts.append({
            "text": text,
            "urgency": round(urgency, 2),
            "time": time.time(),
        })
        self.recent_alerts = self.recent_alerts[-5:]

    def record_correction(self):
        self.session_metrics["corrections_made"] += 1

    def record_reassurance(self):
        self.session_metrics["reassurances"] += 1

    def should_inject(self) -> bool:
        """Check if enough time has passed for a memory re-injection."""
        return (time.time() - self.last_injection_time) >= INJECTION_INTERVAL

    def to_injection_text(self) -> str:
        """
        Compact text for injection into Gemini Live context.
        Must be SHORT — every token counts toward 128K limit.
        """
        self.last_injection_time = time.time()
        lines = ["--- SPATIAL MEMORY ---"]
        lines.append(f"Env: {self.environment_type}")

        if self.stable_objects:
            obj_strs = []
            for label, info in list(self.stable_objects.items())[:8]:
                status = " approaching" if info.get("approaching") else ""
                obj_strs.append(f"{label}@{info['direction']},{info['distance']}{status}")
            lines.append(f"Objects: {'; '.join(obj_strs)}")

        if self.landmarks:
            recent_landmarks = [l["text"] for l in self.landmarks[-5:]]
            lines.append(f"Signs: {', '.join(recent_landmarks)}")

        if self.recent_alerts:
            last = self.recent_alerts[-1]
            lines.append(f"Last alert: \"{last['text']}\" ({last['urgency']})")

        if self.places_visited:
            route = " > ".join([p["to"] for p in self.places_visited[-5:]])
            lines.append(f"Route: {route}")

        m = self.session_metrics
        duration = int(time.time() - m["session_start"])
        lines.append(
            f"Session: {duration}s, {m['frames_processed']}f, "
            f"{m['alerts_sent']}alerts, {m['corrections_made']}fixes"
        )
        lines.append("--- END MEMORY ---")

        text = "\n".join(lines)

        log_event("spatial_summary", "injection", details={
            "text_length": len(text),
            "stable_objects": len(self.stable_objects),
            "landmarks": len(self.landmarks),
            "environment": self.environment_type,
        })

        return text
