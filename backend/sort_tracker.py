"""
SORT-style tracker: Kalman filter prediction + Hungarian assignment.
Maintains persistent object IDs across frames.
"""

import numpy as np
from scipy.optimize import linear_sum_assignment


class KalmanBoxTracker:
    """Tracks a single object with a simple Kalman-like state."""
    count = 0

    def __init__(self, bbox):
        # bbox = [center_x, center_y, area_pct, aspect_ratio]
        self.id = KalmanBoxTracker.count
        KalmanBoxTracker.count += 1
        # State: [cx, cy, area, aspect, dx, dy, da]
        self.state = np.array(
            [bbox[0], bbox[1], bbox[2], bbox[3], 0, 0, 0], dtype=float
        )
        self.hits = 1
        self.age = 0
        self.time_since_update = 0
        self.size_history = [bbox[2]]
        self.position_history = [(bbox[0], bbox[1])]
        self.label = "unknown"

    def predict(self):
        """Advance state by one step using velocity."""
        self.state[:3] += self.state[4:7]
        self.age += 1
        self.time_since_update += 1
        return self.state[:4]

    def update(self, bbox):
        """Update state from a matched detection."""
        alpha = 0.4
        for i in range(3):
            self.state[4 + i] = alpha * (bbox[i] - self.state[i]) + (1 - alpha) * self.state[4 + i]
            self.state[i] = bbox[i]
        self.state[3] = bbox[3]
        self.hits += 1
        self.time_since_update = 0
        self.size_history.append(bbox[2])
        if len(self.size_history) > 30:
            self.size_history = self.size_history[-30:]
        self.position_history.append((bbox[0], bbox[1]))
        if len(self.position_history) > 30:
            self.position_history = self.position_history[-30:]

    @property
    def size_trend(self):
        """Positive = approaching (getting bigger), negative = receding."""
        if len(self.size_history) < 3:
            return 0.0
        r = self.size_history[-5:]
        return (r[-1] - r[0]) / max(len(r) - 1, 1) if len(r) >= 2 else 0.0

    @property
    def spatial_direction(self):
        """Natural language direction — default for alerts."""
        x = self.state[0]
        if x < 0.15:
            return "far left"
        elif x < 0.30:
            return "to your left"
        elif x < 0.42:
            return "ahead, slightly left"
        elif x < 0.58:
            return "ahead"
        elif x < 0.70:
            return "ahead, slightly right"
        elif x < 0.85:
            return "to your right"
        else:
            return "far right"

    @property
    def clock_position(self):
        """Clock position — for disambiguation of multiple objects."""
        x = self.state[0]
        for threshold, name in [
            (0.15, "9"), (0.3, "10"), (0.45, "11"),
            (0.55, "12"), (0.7, "1"), (0.85, "2"),
        ]:
            if x < threshold:
                return f"{name} o'clock"
        return "3 o'clock"

    @property
    def distance_category(self):
        area = self.state[2]
        if area > 15:
            return "very close"
        elif area > 8:
            return "close"
        elif area > 4:
            return "near"
        elif area > 2:
            return "medium"
        elif area > 0.5:
            return "far"
        return "very far"

    @property
    def position_stability(self):
        """How much has this object's center_x moved across frames? Low = stationary."""
        if len(self.position_history) < 4:
            return 1.0
        recent = self.position_history[-6:]
        xs = [p[0] for p in recent]
        return max(xs) - min(xs)

    @property
    def is_likely_stationary(self):
        """Object hasn't moved laterally — user is walking toward it, not vice versa."""
        if len(self.position_history) < 5:
            return False
        return self.position_stability < 0.08 and abs(self.size_trend) < 1.5


class SORTTracker:
    """Multi-object tracker using SORT (Simple Online Realtime Tracking)."""

    def __init__(self, max_age=10, cost_threshold=0.5):
        self.max_age = max_age
        self.cost_threshold = cost_threshold
        self.trackers: list[KalmanBoxTracker] = []

    def update(self, detections: list[dict]) -> list[dict]:
        """
        Update tracker with new detections.

        Args:
            detections: list of dicts with center_x, center_y, area_pct, bbox

        Returns:
            list of track dicts with id, label, direction, clock, approaching, etc.
        """
        # Convert detections to measurement vectors
        measurements = []
        for d in detections:
            aspect = d["bbox"]["w"] / max(d["bbox"]["h"], 0.001)
            measurements.append([d["center_x"], d["center_y"], d["area_pct"], aspect])

        # Predict existing trackers
        predictions = [t.predict() for t in self.trackers]

        # Hungarian assignment
        if predictions and measurements:
            cost = np.zeros((len(predictions), len(measurements)))
            for i, p in enumerate(predictions):
                for j, m in enumerate(measurements):
                    pos_dist = np.sqrt((p[0] - m[0]) ** 2 + (p[1] - m[1]) ** 2)
                    size_dist = abs(p[2] - m[2]) / max(p[2], m[2], 0.01) * 0.5
                    cost[i, j] = pos_dist + size_dist

            ri, ci = linear_sum_assignment(cost)
            matched_t, matched_d = set(), set()
            for r, c in zip(ri, ci):
                if cost[r, c] < self.cost_threshold:
                    self.trackers[r].update(measurements[c])
                    self.trackers[r].label = detections[c]["label"]
                    matched_t.add(r)
                    matched_d.add(c)

            # New trackers for unmatched detections
            for j in range(len(measurements)):
                if j not in matched_d:
                    t = KalmanBoxTracker(measurements[j])
                    t.label = detections[j]["label"]
                    self.trackers.append(t)

        elif measurements:
            # No existing trackers — create all
            for j, m in enumerate(measurements):
                t = KalmanBoxTracker(m)
                t.label = detections[j]["label"]
                self.trackers.append(t)

        # Prune dead trackers
        self.trackers = [t for t in self.trackers if t.time_since_update <= self.max_age]

        # Return active tracks
        return [
            {
                "id": f"obj_{t.id}",
                "label": t.label,
                "direction": t.spatial_direction,
                "clock": t.clock_position,
                "distance": t.distance_category,
                "approaching": t.size_trend > 0.3,
                "size_trend": round(t.size_trend, 2),
                "area_pct": round(t.state[2], 1),
                "center_x": round(t.state[0], 3),
                "center_y": round(t.state[1], 3),
                "aspect_ratio": round(t.state[3], 2),
                "frames_tracked": t.hits,
                "is_stationary": t.is_likely_stationary,
            }
            for t in self.trackers
            if t.hits >= 2 or t.time_since_update == 0
        ]
