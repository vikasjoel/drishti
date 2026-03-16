"""
Structured logger for Drishti.
Writes JSON log entries to both console and logs/session.log.
Tracks stats and prints a summary every 30 seconds.
"""

import asyncio
import json
import logging
import os
import time
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "session.log"

_file_handler = None
_console_handler = None
_logger = None


def get_structured_logger() -> logging.Logger:
    global _logger, _file_handler, _console_handler
    if _logger:
        return _logger

    _logger = logging.getLogger("drishti.structured")
    _logger.setLevel(logging.DEBUG)
    _logger.propagate = False

    # Console: JSON for Cloud Logging compatibility
    _console_handler = logging.StreamHandler()
    _console_handler.setLevel(logging.DEBUG)
    _console_handler.setFormatter(_ConsoleJsonFormatter())
    _logger.addHandler(_console_handler)

    # File: JSON lines
    _file_handler = logging.FileHandler(LOG_FILE, mode="a")
    _file_handler.setLevel(logging.DEBUG)
    _file_handler.setFormatter(_JsonFormatter())
    _logger.addHandler(_file_handler)

    return _logger


class _JsonFormatter(logging.Formatter):
    def format(self, record):
        entry = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S.") + f"{int(record.msecs):03d}Z",
            "component": getattr(record, "component", "unknown"),
            "event_type": getattr(record, "event_type", "log"),
            "details": getattr(record, "details", {}),
        }
        latency = getattr(record, "latency_ms", None)
        if latency is not None:
            entry["latency_ms"] = round(latency, 1)
        if record.getMessage():
            entry["message"] = record.getMessage()
        return json.dumps(entry)


class _ConsoleJsonFormatter(logging.Formatter):
    """Single-line JSON for Cloud Logging (stderr capture)."""
    def format(self, record):
        entry = {
            "severity": record.levelname,
            "component": getattr(record, "component", "unknown"),
            "event": getattr(record, "event_type", "log"),
        }
        msg = record.getMessage()
        if msg:
            entry["message"] = msg
        details = getattr(record, "details", {})
        if details:
            entry["details"] = details
        latency = getattr(record, "latency_ms", None)
        if latency is not None:
            entry["latency_ms"] = round(latency, 1)
        return json.dumps(entry, separators=(",", ":"))


def log_event(component: str, event_type: str, message: str = "",
              details: dict | None = None, latency_ms: float | None = None):
    """Log a structured event."""
    logger = get_structured_logger()
    record = logger.makeRecord(
        name="drishti.structured",
        level=logging.INFO,
        fn="",
        lno=0,
        msg=message,
        args=(),
        exc_info=None,
    )
    record.component = component
    record.event_type = event_type
    record.details = details or {}
    record.latency_ms = latency_ms
    logger.handle(record)


# ── Stats tracker ──

class SessionStats:
    def __init__(self):
        self.reset()
        self._task = None

    def reset(self):
        self.start_time = time.time()
        self.frames_sent = 0
        self.audio_chunks_sent = 0
        self.audio_bytes_sent = 0
        self.gemini_responses = 0
        self.gemini_audio_chunks = 0
        self.gemini_transcriptions = 0
        self.proactive_responses = 0
        self.reactive_responses = 0
        self.silent_injections = 0
        self.context_injections = 0
        self.latencies: list[float] = []
        self._last_frame_time: float | None = None
        self._last_summary_time = time.time()

    def record_frame(self):
        self.frames_sent += 1
        self._last_frame_time = time.time()

    def record_audio_sent(self, size_bytes: int):
        self.audio_chunks_sent += 1
        self.audio_bytes_sent += size_bytes

    def record_gemini_audio(self):
        self.gemini_audio_chunks += 1
        self.gemini_responses += 1
        if self._last_frame_time:
            latency = (time.time() - self._last_frame_time) * 1000
            self.latencies.append(latency)

    def record_gemini_transcription(self, is_output: bool):
        self.gemini_transcriptions += 1
        if is_output:
            self.gemini_responses += 1

    def record_context_injection(self, has_speak_directive: bool):
        self.context_injections += 1
        if has_speak_directive:
            self.proactive_responses += 1
        else:
            self.silent_injections += 1

    @property
    def avg_latency_ms(self) -> float:
        if not self.latencies:
            return 0.0
        return sum(self.latencies) / len(self.latencies)

    @property
    def session_duration_s(self) -> int:
        return int(time.time() - self.start_time)

    def summary_dict(self) -> dict:
        return {
            "session_duration_s": self.session_duration_s,
            "frames_sent": self.frames_sent,
            "audio_chunks_sent": self.audio_chunks_sent,
            "audio_bytes_sent_kb": round(self.audio_bytes_sent / 1024, 1),
            "gemini_responses": self.gemini_responses,
            "gemini_audio_chunks": self.gemini_audio_chunks,
            "gemini_transcriptions": self.gemini_transcriptions,
            "context_injections": self.context_injections,
            "proactive_speak": self.proactive_responses,
            "silent_injections": self.silent_injections,
            "avg_latency_ms": round(self.avg_latency_ms, 1),
            "latency_samples": len(self.latencies),
        }

    def print_summary(self):
        s = self.summary_dict()
        log_event("stats", "summary", details=s,
                  message=(
                      f"STATS [{s['session_duration_s']}s] "
                      f"frames={s['frames_sent']} "
                      f"audio_out={s['audio_chunks_sent']} "
                      f"gemini_resp={s['gemini_responses']} "
                      f"ctx_inj={s['context_injections']} "
                      f"proactive={s['proactive_speak']} "
                      f"silent={s['silent_injections']} "
                      f"avg_lat={s['avg_latency_ms']}ms"
                  ))

    async def start_periodic_summary(self, interval: int = 30):
        """Start a background task that prints stats every `interval` seconds."""
        async def _loop():
            while True:
                await asyncio.sleep(interval)
                self.print_summary()
        self._task = asyncio.create_task(_loop())

    def stop_periodic_summary(self):
        if self._task:
            self._task.cancel()
            self._task = None


# Global stats instance per session — created fresh each connection
def new_session_stats() -> SessionStats:
    return SessionStats()
