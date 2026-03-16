"""
Temporal validator for Drishti v4.2.
Checks whether a perception result is still relevant
given user movement since the frame was captured.

Uses sensor snapshots — no GPS precision needed.
Works indoor and outdoor.
"""
import time
import logging
import re

logger = logging.getLogger("drishti.temporal")


class TemporalValidator:

    # Distance estimation from CV bounding box area percentage
    AREA_TO_DISTANCE = [
        (5, 4.0),
        (8, 3.0),
        (12, 2.0),
        (15, 1.5),
        (20, 1.0),
        (30, 0.5),
        (50, 0.2),
    ]

    # Distance estimation from cognitive text descriptions
    DISTANCE_KEYWORDS = [
        ("directly ahead", 0.5),
        ("right here", 0.3),
        ("right in front", 0.5),
        ("within 1 step", 0.7),
        ("1 step", 0.7),
        ("2 steps", 1.4),
        ("3 steps", 2.1),
        ("a few steps", 2.5),
        ("4 steps", 2.8),
        ("5 steps", 3.5),
        ("1 meter", 1.0),
        ("2 meter", 2.0),
        ("3 meter", 3.0),
        ("5 meter", 5.0),
        ("10 meter", 10.0),
        ("beside", 0.3),
        ("near", 1.0),
        ("far", 8.0),
    ]

    def validate(self, perception, current_sensors):
        """
        Check if a perception result is still relevant.

        Args:
            perception: dict with:
                - frame_snapshot: sensor state when frame was captured
                - distance_estimate: float (meters) or None
            current_sensors: current sensor state from sensor_processor

        Returns: dict with:
            - status: "stale" | "imminent" | "valid"
            - remaining_distance: float or None
            - confidence: 0-1
            - reason: str (for logging)
        """
        snap = perception.get("frame_snapshot")
        if not snap or not snap.get("capture_time"):
            return {
                "status": "valid",
                "remaining_distance": perception.get("distance_estimate"),
                "confidence": 0.4,
                "reason": "no frame snapshot available"
            }

        now = time.time()
        elapsed = now - snap["capture_time"]

        # Very fresh — always valid
        if elapsed < 0.3:
            return {
                "status": "valid",
                "remaining_distance": perception.get("distance_estimate"),
                "confidence": 0.9,
                "reason": f"very fresh ({elapsed:.1f}s)"
            }

        # Compute distance moved and heading change
        distance_moved = self._compute_distance_moved(snap, current_sensors, elapsed)
        heading_delta = self._compute_heading_change(snap, current_sensors)

        # User turned > 45° — obstacle no longer "ahead"
        if heading_delta > 45:
            return {
                "status": "stale",
                "remaining_distance": None,
                "confidence": 0.8,
                "reason": f"user turned {heading_delta:.0f} since frame capture"
            }

        obstacle_distance = perception.get("distance_estimate")

        if obstacle_distance is None:
            if elapsed > 5:
                return {
                    "status": "stale",
                    "remaining_distance": None,
                    "confidence": 0.3,
                    "reason": f"no distance estimate, {elapsed:.1f}s old"
                }
            return {
                "status": "valid",
                "remaining_distance": None,
                "confidence": 0.5,
                "reason": f"no distance estimate but fresh ({elapsed:.1f}s)"
            }

        remaining = obstacle_distance - distance_moved

        # User clearly PASSED the obstacle
        if remaining < -0.5:
            return {
                "status": "stale",
                "remaining_distance": remaining,
                "confidence": 0.9,
                "reason": f"user moved {distance_moved:.1f}m past obstacle at {obstacle_distance:.1f}m"
            }

        # User approximately AT the obstacle
        if remaining < 0.3:
            return {
                "status": "imminent",
                "remaining_distance": max(0.2, remaining),
                "confidence": 0.6,
                "reason": f"user approximately at obstacle (remaining {remaining:.1f}m)"
            }

        # IMMINENT: obstacle less than 1.5m ahead
        if remaining < 1.5:
            return {
                "status": "imminent",
                "remaining_distance": remaining,
                "confidence": 0.8,
                "reason": f"obstacle {remaining:.1f}m ahead, urgent"
            }

        # VALID: obstacle still ahead at safe distance
        return {
            "status": "valid",
            "remaining_distance": remaining,
            "confidence": 0.7,
            "reason": f"obstacle {remaining:.1f}m ahead (was {obstacle_distance:.1f}m, moved {distance_moved:.1f}m)"
        }

    def _compute_distance_moved(self, snapshot, current, elapsed):
        """Estimate how far user moved since frame snapshot."""
        # Method 1: Step count delta x stride (most reliable indoor)
        snap_steps = snapshot.get("step_count", 0)
        current_steps = current.get("step_count", 0)
        step_delta = current_steps - snap_steps
        if step_delta > 0:
            return step_delta * 0.7

        # Method 2: GPS speed x elapsed (reliable outdoor)
        snap_speed = snapshot.get("speed", 0)
        if snap_speed > 0.3:
            return snap_speed * elapsed

        # Method 3: Distance walked odometer delta
        snap_dist = snapshot.get("distance_walked", 0)
        current_dist = current.get("distance_walked", 0)
        odo_delta = current_dist - snap_dist
        if odo_delta > 0.1:
            return odo_delta

        # Method 4: Currently moving, assume 1 m/s
        if current.get("movement") in ("walking", "slow_walk") and elapsed > 0.5:
            return 1.0 * elapsed

        # Stationary
        return 0.0

    def _compute_heading_change(self, snapshot, current):
        """Compute how much user turned since frame capture."""
        heading_then = snapshot.get("heading", 0)
        heading_now = current.get("heading", 0)
        delta = abs(heading_now - heading_then)
        if delta > 180:
            delta = 360 - delta
        return delta

    def estimate_distance_from_cv(self, area_pct):
        """Estimate obstacle distance from CV bounding box area percentage."""
        if not area_pct or area_pct <= 0:
            return None

        prev_area, prev_dist = 0, 6.0
        for area, dist in self.AREA_TO_DISTANCE:
            if area_pct <= area:
                if prev_area == 0:
                    return dist
                frac = (area_pct - prev_area) / (area - prev_area)
                return prev_dist + frac * (dist - prev_dist)
            prev_area, prev_dist = area, dist

        return 0.2  # Very large area = very close

    def estimate_distance_from_text(self, text):
        """Estimate obstacle distance from cognitive speech/description text."""
        if not text:
            return None
        text_lower = text.lower()
        for keyword, distance in self.DISTANCE_KEYWORDS:
            if keyword in text_lower:
                return distance

        m = re.search(r'(\d+)\s*(?:m\b|meter)', text_lower)
        if m:
            return float(m.group(1))

        return None
