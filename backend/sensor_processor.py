"""
Enhanced sensor processor for Drishti v4.2.
Processes raw phone sensors into contextual user state.
Provides SNAPSHOTS for frame stamping.
"""
import time
import logging

logger = logging.getLogger("drishti.sensors")


class SensorProcessor:
    def __init__(self):
        self.prev = {
            "movement": "unknown", "heading": 0, "vertical": "level",
            "speed": 0, "step_count": 0,
        }
        self.total_steps = 0
        self.distance_walked = 0.0
        self.phone_orientation = "unknown"
        self.sensors_received = False

    def process(self, raw):
        """
        Process 1Hz sensor summary from browser.
        Returns rich contextual state with transitions.
        """
        self.sensors_received = True

        # Speed (best available source)
        speed = self._best_speed(raw)

        # Movement classification
        if speed < 0.15:
            movement = "stationary"
        elif speed < 0.5:
            movement = "slow_walk"
        elif speed < 2.0:
            movement = "walking"
        elif speed < 5.0:
            movement = "running"
        else:
            movement = "vehicle"

        # Heading & turns
        heading = raw.get("heading", 0)
        heading_delta = abs(raw.get("heading_delta", 0))
        rotation_rate = raw.get("rotation_rate", 0)

        is_head_turn = rotation_rate > 60 and heading_delta < 20
        is_body_turn = heading_delta > 30 and not is_head_turn

        # Vertical motion
        vertical = self._detect_vertical(raw)

        # Phone orientation
        beta = raw.get("beta", 0)
        self.phone_orientation = self._detect_phone_orientation(beta)

        # Step count & distance
        new_steps = raw.get("step_count", self.total_steps) - self.total_steps
        if new_steps > 0:
            self.total_steps = raw.get("step_count", self.total_steps)
            self.distance_walked += new_steps * 0.7
        elif movement in ("walking", "slow_walk") and speed > 0.3:
            self.distance_walked += speed * 1.0

        # Indoor/outdoor hint
        gps_accuracy = raw.get("gps_accuracy")
        likely_outdoor = gps_accuracy is not None and gps_accuracy < 15

        # Transitions
        prev = self.prev

        state = {
            "movement": movement,
            "speed": speed,
            "heading": heading,
            "heading_delta": heading_delta,
            "vertical": vertical,
            "step_count": self.total_steps,
            "distance_walked": self.distance_walked,
            "phone_orientation": self.phone_orientation,
            "likely_outdoor": likely_outdoor,
            "gps": {
                "lat": raw.get("gps_lat"),
                "lon": raw.get("gps_lon"),
                "accuracy": gps_accuracy,
                "speed": raw.get("gps_speed"),
                "heading": raw.get("gps_heading"),
                "altitude": raw.get("gps_altitude"),
            },
            "timestamp": time.time(),
            "sensors_active": raw.get("sensors_active", False),

            # Transitions
            "just_stopped": prev["movement"] in ("walking", "slow_walk") and movement == "stationary",
            "was_walking": prev["movement"] in ("walking", "slow_walk"),
            "just_started_walking": prev["movement"] == "stationary" and movement in ("walking", "slow_walk"),
            "is_head_turn": is_head_turn,
            "is_body_turn": is_body_turn,
            "entering_stairs": prev["vertical"] == "level" and vertical in ("ascending", "descending"),
            "leaving_stairs": prev["vertical"] in ("ascending", "descending") and vertical == "level",
            "on_stairs": vertical in ("ascending", "descending"),
            "speed_category_changed": movement != prev["movement"],
        }

        self.prev = {
            "movement": movement, "heading": heading, "vertical": vertical,
            "speed": speed, "step_count": self.total_steps,
        }

        return state

    def get_snapshot(self):
        """
        Returns a FROZEN snapshot of current sensor state.
        Used to STAMP frames at the moment of capture.
        This snapshot travels WITH the frame through CV and cognitive pipelines.
        """
        return {
            "capture_time": time.time(),
            "speed": self.prev.get("speed", 0),
            "heading": self.prev.get("heading", 0),
            "step_count": self.total_steps,
            "distance_walked": self.distance_walked,
            "movement": self.prev.get("movement", "unknown"),
            "vertical": self.prev.get("vertical", "level"),
        }

    def get_current_state(self):
        """Return last known state for trigger checks between sensor updates."""
        return self.prev

    def _best_speed(self, raw):
        """Best speed estimate: GPS > step-based > accel-based."""
        gps_speed = raw.get("gps_speed")
        if gps_speed is not None and gps_speed > 0.5:
            return gps_speed

        step_count = raw.get("step_count", 0)
        prev_steps = self.prev.get("step_count", 0)
        new_steps = step_count - prev_steps
        if new_steps > 0:
            return new_steps * 0.7

        accel_variance = raw.get("accel_variance", 0)
        if accel_variance > 2.0:
            return 1.0

        return 0.0

    def _detect_vertical(self, raw):
        """Detect stairs from accelerometer pattern."""
        accel_z = raw.get("accel_gravity_z", 9.81)
        accel_variance = raw.get("accel_variance", 0)

        if accel_variance > 2.0:
            if accel_z > 10.3:
                return "ascending"
            elif accel_z < 9.3:
                return "descending"

        if accel_variance < 0.5:
            if accel_z > 10.5:
                return "ascending"
            elif accel_z < 9.0:
                return "descending"

        return "level"

    def _detect_phone_orientation(self, beta):
        """How is user carrying the phone?"""
        beta_abs = abs(beta)
        if beta_abs < 20:
            return "flat"
        elif beta_abs < 50:
            return "angled"
        elif beta_abs < 80:
            return "chest_mount"
        else:
            return "upright"
