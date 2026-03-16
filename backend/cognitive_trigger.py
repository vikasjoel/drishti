"""
Decides WHEN to call Gemini generateContent.
Uses phone sensors + frame change + CV delta. NOT a fixed timer.
"""
import time
import logging

logger = logging.getLogger("drishti.trigger")


class CognitiveTrigger:
    MIN_INTERVAL = 5    # Never faster than 5 seconds
    MAX_INTERVAL = 30   # Always at least every 30 seconds

    def __init__(self):
        self.last_call_time = 0
        self.call_count = 0
        self.consecutive_failures = 0
        self.backoff_until = 0

    def should_call(self, sensors, frame_change, cv_has_new_priority, is_cold_start=False):
        """Returns True if generateContent should be called NOW."""
        now = time.time()
        elapsed = now - self.last_call_time

        # Backoff after repeated failures (e.g. 429 rate limits)
        if now < self.backoff_until:
            return False

        # Cold start: always call on first frame
        if is_cold_start:
            return True

        # Hard minimum interval
        if elapsed < self.MIN_INTERVAL:
            return False

        # TRIGGER 1: Body turn (not head turn)
        if sensors.get("is_body_turn") and not sensors.get("is_head_turn"):
            logger.info("Cognitive trigger: body turn")
            return True

        # TRIGGER 2: User stopped after walking
        if sensors.get("just_stopped") and sensors.get("was_walking"):
            logger.info("Cognitive trigger: user stopped")
            return True

        # TRIGGER 3: Entering or leaving stairs
        if sensors.get("entering_stairs") or sensors.get("leaving_stairs"):
            logger.info("Cognitive trigger: elevation change")
            return True

        # TRIGGER 4: Major visual change + not head turn
        if frame_change > 0.50 and not sensors.get("is_head_turn"):
            logger.info(f"Cognitive trigger: frame change {frame_change:.2f}")
            return True

        # TRIGGER 5: New priority object from Cloud Vision
        if cv_has_new_priority:
            logger.info("Cognitive trigger: CV new priority object")
            return True

        # TRIGGER 6: Speed category changed
        if sensors.get("speed_category_changed"):
            logger.info("Cognitive trigger: speed category changed")
            return True

        # TRIGGER 7: Gradual change accumulated over time
        if frame_change > 0.25 and elapsed > 8 and sensors.get("movement") == "walking":
            logger.info("Cognitive trigger: gradual change while walking")
            return True

        # TRIGGER 8: Max interval
        if elapsed > self.MAX_INTERVAL:
            logger.info("Cognitive trigger: max interval")
            return True

        return False

    def force_call_if_needed(self, spatial_confidence, user_movement, elapsed):
        """
        Force cognitive call when brain detects low spatial confidence.
        This is the brain's self-correcting mechanism.
        """
        if (spatial_confidence < 0.2
                and user_movement in ("walking", "slow_walk")
                and elapsed > 5):
            logger.info("Cognitive trigger: LOW spatial_confidence, forcing re-perception")
            return True
        return False

    def record_call(self, success=True):
        self.last_call_time = time.time()
        self.call_count += 1
        if success:
            self.consecutive_failures = 0
            self.backoff_until = 0
        else:
            self.consecutive_failures += 1
            # Exponential backoff: 10s, 20s, 40s, 60s max
            delay = min(60, 10 * (2 ** (self.consecutive_failures - 1)))
            self.backoff_until = time.time() + delay
            logger.warning(f"Cognitive call failed ({self.consecutive_failures}x), backing off {delay}s")
