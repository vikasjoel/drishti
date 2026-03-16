"""
MobileCameraTracker — size-only tracking for mobile camera plugins.

Mathematical insight: bounding box area (%) is invariant to camera rotation.
When you turn your head, objects shift in x,y but their angular size doesn't change.
Size only changes with forward/backward translation (shared across all objects)
or independent object approach.

Background growth = median of all growths = user's forward motion.
Independent growth = this object's growth - background = real approach signal.
"""

import logging
import time

from backend.logger import log_event

logger = logging.getLogger(__name__)


class MobileCameraTracker:
    def __init__(self):
        self.prev_frame_objects: dict = {}  # label -> {area_pct, center_x, center_y, ...}
        self.growth_histories: dict = {}    # label -> [growth_rate_per_frame]
        self.label_first_seen: dict = {}    # label -> timestamp
        self.label_frame_count: dict = {}   # label -> frames tracked
        self._frame_count = 0

    def analyze(self, current_objects: list[dict]) -> tuple[list[dict], float]:
        """
        Analyze current frame objects against previous frame.

        Returns:
            (results, background_growth) where results is a list of enriched
            track dicts and background_growth is the estimated camera motion.
        """
        self._frame_count += 1
        now = time.time()
        results = []
        all_growths = []
        matched = []

        for curr in current_objects:
            label = curr["label"].lower()
            prev = self.prev_frame_objects.get(label)

            # Track frame counts
            if label not in self.label_first_seen:
                self.label_first_seen[label] = now
                self.label_frame_count[label] = 0
            self.label_frame_count[label] += 1

            if prev:
                growth = curr["area_pct"] - prev["area_pct"]
                all_growths.append(growth)
                matched.append({
                    "label": label,
                    "area_pct": curr["area_pct"],
                    "center_x": curr["center_x"],
                    "center_y": curr.get("center_y", 0.5),
                    "growth": growth,
                    "prev_area": prev["area_pct"],
                    "confidence": curr.get("confidence", 0),
                    "bbox": curr.get("bbox", {}),
                    "frames_tracked": self.label_frame_count.get(label, 1),
                })

        # BACKGROUND GROWTH = median of all growths
        if len(all_growths) >= 2:
            all_growths_sorted = sorted(all_growths)
            background_growth = all_growths_sorted[len(all_growths_sorted) // 2]
        elif len(all_growths) == 1:
            background_growth = all_growths[0] * 0.5  # Conservative
        else:
            background_growth = 0.0

        # INDEPENDENT GROWTH = this object's growth MINUS background
        for obj in matched:
            independent_growth = obj["growth"] - background_growth

            # Growth acceleration
            history = self.growth_histories.get(obj["label"], [])
            history.append(independent_growth)
            if len(history) > 10:
                history = history[-10:]
            self.growth_histories[obj["label"]] = history

            acceleration = 0.0
            if len(history) >= 3:
                recent = history[-3:]
                rates = [recent[i] - recent[i - 1] for i in range(1, len(recent))]
                acceleration = sum(rates) / len(rates)

            is_approaching = (
                independent_growth > 1.5 and acceleration > 0.3
            )

            # Direction from center_x
            cx = obj["center_x"]
            if cx < 0.15:
                direction = "far left"
            elif cx < 0.30:
                direction = "to your left"
            elif cx < 0.42:
                direction = "ahead, slightly left"
            elif cx < 0.58:
                direction = "ahead"
            elif cx < 0.70:
                direction = "ahead, slightly right"
            elif cx < 0.85:
                direction = "to your right"
            else:
                direction = "far right"

            # Distance from area
            area = obj["area_pct"]
            if area > 15:
                distance = "very close"
            elif area > 8:
                distance = "close"
            elif area > 4:
                distance = "near"
            elif area > 2:
                distance = "medium"
            elif area > 0.5:
                distance = "far"
            else:
                distance = "very far"

            obj["independent_growth"] = round(independent_growth, 2)
            obj["acceleration"] = round(acceleration, 3)
            obj["is_independently_approaching"] = is_approaching
            obj["approaching"] = is_approaching
            obj["background_growth"] = round(background_growth, 2)
            obj["direction"] = direction
            obj["distance"] = distance
            obj["id"] = f"mob_{obj['label']}"
            obj["size_trend"] = round(independent_growth, 2)
            obj["is_stationary"] = (
                abs(independent_growth) < 0.5
                and abs(acceleration) < 0.2
                and obj["frames_tracked"] > 5
            )
            results.append(obj)

        # Also add unmatched objects (new this frame) with no growth data
        matched_labels = {obj["label"] for obj in matched}
        for curr in current_objects:
            label = curr["label"].lower()
            if label not in matched_labels:
                cx = curr["center_x"]
                area = curr["area_pct"]

                if cx < 0.30:
                    direction = "to your left"
                elif cx < 0.70:
                    direction = "ahead"
                else:
                    direction = "to your right"

                if area > 8:
                    distance = "close"
                elif area > 4:
                    distance = "near"
                else:
                    distance = "far"

                results.append({
                    "label": label,
                    "area_pct": area,
                    "center_x": curr["center_x"],
                    "center_y": curr.get("center_y", 0.5),
                    "growth": 0.0,
                    "independent_growth": 0.0,
                    "acceleration": 0.0,
                    "is_independently_approaching": False,
                    "approaching": False,
                    "background_growth": background_growth,
                    "direction": direction,
                    "distance": distance,
                    "id": f"mob_{label}",
                    "size_trend": 0.0,
                    "is_stationary": False,
                    "frames_tracked": 1,
                    "confidence": curr.get("confidence", 0),
                    "bbox": curr.get("bbox", {}),
                })

        # Update previous frame state
        self.prev_frame_objects = {
            obj["label"].lower(): obj for obj in current_objects
        }

        # Clean stale labels not seen in 30 frames
        stale_labels = [
            label for label, count in self.label_frame_count.items()
            if label not in self.prev_frame_objects
            and self._frame_count - count > 30
        ]
        for label in stale_labels:
            self.label_frame_count.pop(label, None)
            self.label_first_seen.pop(label, None)
            self.growth_histories.pop(label, None)

        log_event("mobile_tracker", "analyze", details={
            "frame": self._frame_count,
            "detections": len(current_objects),
            "matched": len(matched),
            "background_growth": round(background_growth, 2),
            "approaching_count": sum(1 for r in results if r["approaching"]),
        })

        return results, background_growth
