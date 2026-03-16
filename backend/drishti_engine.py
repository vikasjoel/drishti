"""
Drishti Engine v3.1 — the core intelligence loop.

Runs alongside the WebSocket forwarding:
- Every frame: advances the world model
- Every 5 frames: injects spatial context into Gemini
- Every 30 seconds: re-injects spatial memory
- Processes transcriptions to update the world model
"""

import logging

from backend.world_model import WorldModel
from backend.spatial_summary import SpatialSummary
from backend.gemini_session import GeminiLiveSession
from backend.logger import log_event

logger = logging.getLogger(__name__)

CONTEXT_INJECTION_INTERVAL = 5   # passive context every 5 frames
FORCED_EVAL_INTERVAL = 30        # forced turn_complete every N frames


class DrishtiEngine:
    def __init__(self, gemini_session: GeminiLiveSession,
                 spatial_summary: SpatialSummary,
                 forced_eval_interval: int = FORCED_EVAL_INTERVAL):
        self.session = gemini_session
        self.world_model = WorldModel()
        self.spatial_summary = spatial_summary
        self.forced_eval_interval = forced_eval_interval
        self.stats = None

        # Brain state (set externally by main.py after brain.process())
        self._brain_tracks: list[dict] = []
        self._brain_urgency: float = 0.0
        self._brain_action: str = "none"

    def set_brain_state(self, tracks: list[dict], urgency: float, action: str):
        """Update engine with latest brain state for context injection."""
        self._brain_tracks = tracks
        self._brain_urgency = urgency
        self._brain_action = action

    def _build_track_context(self, frame: int) -> str:
        """Build context text from tracker tracks (single source of truth)."""
        tracks = self._brain_tracks
        urgency = self._brain_urgency
        action = self._brain_action

        env = self.spatial_summary.environment_type
        env_str = f"Environment: {env}" if env != "unknown" else ""

        parts = [
            f"--- SPATIAL STATE (Frame {frame}) ---",
        ]

        if env_str:
            parts.append(env_str)

        if tracks:
            relevant = [t for t in tracks if t.get("relevant", True)]
            if relevant:
                parts.append(f"Tracking {len(relevant)} objects:")
                for t in relevant[:7]:
                    direction = t.get("direction", "ahead")
                    label = t.get("label", "?")
                    distance = t.get("distance", "")
                    if t.get("approaching"):
                        status = "approaching"
                    elif t.get("is_stationary"):
                        status = "stationary"
                    else:
                        status = ""
                    line = f"  - {label}: {direction}, {distance}"
                    if status:
                        line += f", {status}"
                    parts.append(line)
            else:
                parts.append("Objects in view but none requiring attention.")
        else:
            parts.append("No objects detected.")

        parts.append(f"Urgency: {urgency:.1f} | Action: {action}")
        parts.append("---")

        return "\n".join(parts)

    async def on_frame(self, jpeg_bytes: bytes):
        """Called each time a camera frame arrives (~1/s)."""
        self.world_model.new_frame()
        frame = self.world_model.frame_count

        # Send the frame to Gemini (passive context)
        await self.session.send_image(jpeg_bytes)

        # Every 5 frames: inject spatial state from brain's tracker
        if frame % CONTEXT_INJECTION_INTERVAL == 0:
            context = self._build_track_context(frame)
            log_event("engine", "context_injection", details={
                "frame": frame,
                "context_length": len(context),
                "active_objects": len(self._brain_tracks),
                "out_of_view": len(self.world_model.out_of_view),
            })
            if self.stats:
                self.stats.record_context_injection(False)
            await self.session.send_text_context(context, end_of_turn=False)

        # Every 30 seconds: re-inject spatial memory (survives context compression)
        if self.spatial_summary.should_inject():
            memory_text = self.spatial_summary.to_injection_text()
            log_event("engine", "memory_injection", details={
                "frame": frame,
                "text_length": len(memory_text),
            })
            await self.session.send_text_context(memory_text, end_of_turn=False)

        # Every N frames: forced evaluation (only if brain hasn't spoken recently)
        if frame % self.forced_eval_interval == 0:
            if self._brain_action == "silent":
                log_event("engine", "forced_eval", details={
                    "frame": frame,
                    "interval": self.forced_eval_interval,
                })
                await self.session.send_text_context(
                    "VISUAL CHECK — describe what you see briefly, only if something "
                    "important that the spatial updates haven't mentioned. "
                    "If nothing new, stay silent.",
                    end_of_turn=True,
                )

    def on_output_transcription(self, text: str):
        """Process what Gemini said — extract spatial observations for the world model."""
        lower = text.lower()

        env_keywords = ["corridor", "hallway", "room", "open area", "outdoor",
                        "indoor", "stairway", "elevator", "parking", "sidewalk",
                        "intersection", "doorway", "kitchen", "bedroom", "bathroom"]
        for kw in env_keywords:
            if kw in lower:
                self.world_model.report_environment(kw)

        if "sign" in lower or "exit" in lower or "entrance" in lower:
            for word in ["exit", "entrance", "sign", "door", "gate"]:
                if word in lower:
                    self.world_model.report_landmark(word)

    def on_input_transcription(self, text: str):
        """Process what the user said."""
        log_event("engine", "user_speech", details={"text": text[:200]})
