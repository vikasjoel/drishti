"""
Processes conversation exchanges to extract goals and behavioral commands.
Key insight: parse GEMINI'S response, not user's garbled speech.
"""
import re
import time
import logging

logger = logging.getLogger("drishti.speech")


class SpeechEventDetector:
    """Accumulates transcript fragments. Emits complete exchanges on turn_complete."""

    def __init__(self):
        self.user_fragments = []
        self.gemini_fragments = []
        self.user_last_spoke = 0
        self.gemini_last_spoke = 0

    def on_input_transcript(self, text):
        self.user_fragments.append(text)
        self.user_last_spoke = time.time()

    def on_output_transcript(self, text):
        self.gemini_fragments.append(text)
        self.gemini_last_spoke = time.time()

    def on_turn_complete(self):
        user_text = " ".join(self.user_fragments).strip()
        gemini_text = " ".join(self.gemini_fragments).strip()
        self.user_fragments = []
        self.gemini_fragments = []

        if user_text or gemini_text:
            return {"user_said": user_text, "gemini_said": gemini_text, "ts": time.time()}
        return None

    def check_timeout(self):
        """Force processing if turn hasn't completed in 10 seconds."""
        if self.user_fragments or self.gemini_fragments:
            last = max(self.user_last_spoke, self.gemini_last_spoke)
            if last > 0 and (time.time() - last) > 10:
                return self.on_turn_complete()
        return None


class ConversationInterpreter:
    """Extracts goals and behavioral commands from exchanges."""

    DIRECTION_PATTERNS = [
        r"to your (?:left|right)", r"\d+ (?:steps?|meters?)",
        r"turn (?:left|right)", r"straight ahead",
    ]

    LOCATION_PATTERNS = [
        r"(metro|station|bus|shop|cafe|restaurant|hotel|hospital|toilet|bathroom|exit|entrance|stairs|door|gate)",
    ]

    SILENCE_WORDS = {"be quiet", "stop talking", "enough", "bas", "chup", "band karo", "shh"}
    DESCRIBE_WORDS = {"describe", "tell me more", "what's around", "kya hai", "batao", "dekhkar batao", "where am i"}

    def interpret(self, exchange, world_model_landmarks=None):
        user = (exchange.get("user_said") or "").lower()
        gemini = (exchange.get("gemini_said") or "").lower()

        result = {"goal": None, "behavioral": None, "topic": "general", "memory_relevant": False}

        # GOAL: parse Gemini's response for directions/locations
        gave_directions = any(re.search(p, gemini) for p in self.DIRECTION_PATTERNS)
        location = None
        for p in self.LOCATION_PATTERNS:
            m = re.search(p, gemini)
            if m:
                location = m.group(1)
                break

        if not location:
            for p in self.LOCATION_PATTERNS:
                m = re.search(p, user)
                if m:
                    location = m.group(1)
                    break

        if gave_directions and location:
            result["goal"] = {"target": location, "confidence": 0.9, "priority": 0.7}
        elif location:
            result["goal"] = {"target": location, "confidence": 0.6, "priority": 0.7}

        # BEHAVIORAL: from user's speech
        for cmd in self.SILENCE_WORDS:
            if cmd in user:
                result["behavioral"] = {"command": "reduce_verbosity", "value": 0.1, "duration": 120}
                break
        for cmd in self.DESCRIBE_WORDS:
            if cmd in user:
                result["behavioral"] = {"command": "increase_verbosity", "value": 0.8, "duration": 30}
                break

        # MEMORY: check against landmarks
        if world_model_landmarks:
            for lm in world_model_landmarks:
                lm_lower = lm.get("text", "").lower()
                if any(w in user for w in lm_lower.split() if len(w) > 3):
                    result["memory_relevant"] = True
                    break

        # TOPIC
        topic_map = {
            "navigation": ["left", "right", "ahead", "turn", "direction", "steps"],
            "environment": ["room", "street", "path", "stairs", "where am i"],
            "person": ["person", "someone", "people"],
            "obstacle": ["blocked", "obstacle", "careful"],
        }
        for topic, kws in topic_map.items():
            if any(kw in gemini for kw in kws):
                result["topic"] = topic
                break

        return result
