"""
SpeechManager — coordinates alert injection to prevent speech pile-up.

Rules:
1. Only ONE alert in flight at a time
2. Estimate speech duration from text length
3. Higher urgency pre-empts lower urgency
4. Same alert not repeated within cooldown
"""

import time
import logging

from backend.logger import log_event

logger = logging.getLogger(__name__)


class SpeechManager:
    def __init__(self, cooldown_seconds: float = 10.0):
        self.last_injection_time = 0.0
        self.last_injection_text = ""
        self.last_injection_urgency = 0.0
        self.estimated_speech_end = 0.0
        self.alert_cooldowns: dict = {}  # alert_text -> last_sent_time
        self.COOLDOWN_SECONDS = cooldown_seconds
        self.WORDS_PER_SECOND = 2.5
        self.injections_sent = 0
        self.injections_blocked = 0

    def should_inject(self, text: str, urgency: float) -> bool:
        """Decide whether this alert should be sent NOW."""
        now = time.time()

        # Don't repeat same alert within cooldown
        if text in self.alert_cooldowns:
            if now - self.alert_cooldowns[text] < self.COOLDOWN_SECONDS:
                log_event("speech_manager", "blocked_cooldown", details={
                    "text": text[:80],
                    "seconds_remaining": round(
                        self.COOLDOWN_SECONDS - (now - self.alert_cooldowns[text]), 1
                    ),
                })
                self.injections_blocked += 1
                return False

        # If Gemini is still speaking previous alert
        if now < self.estimated_speech_end:
            # Only interrupt if new alert is significantly more urgent
            if urgency < self.last_injection_urgency + 0.2:
                log_event("speech_manager", "blocked_speaking", details={
                    "text": text[:80],
                    "urgency": round(urgency, 2),
                    "prev_urgency": round(self.last_injection_urgency, 2),
                    "speech_remaining_s": round(self.estimated_speech_end - now, 1),
                })
                self.injections_blocked += 1
                return False

        return True

    def record_injection(self, text: str, urgency: float):
        """Record that we sent an alert."""
        now = time.time()
        word_count = len(text.split())
        estimated_duration = word_count / self.WORDS_PER_SECOND + 1.0

        self.last_injection_time = now
        self.last_injection_text = text
        self.last_injection_urgency = urgency
        self.estimated_speech_end = now + estimated_duration
        self.alert_cooldowns[text] = now
        self.injections_sent += 1

        # Clean old cooldowns
        self.alert_cooldowns = {
            k: v for k, v in self.alert_cooldowns.items()
            if now - v < 60
        }

        log_event("speech_manager", "injected", details={
            "text": text[:80],
            "urgency": round(urgency, 2),
            "est_duration_s": round(estimated_duration, 1),
            "total_sent": self.injections_sent,
            "total_blocked": self.injections_blocked,
        })
