"""
Gemini Live API session manager.
Handles bidirectional streaming: audio/video in, audio out.
"""

import asyncio
import logging
import os
import time
from typing import AsyncGenerator, Optional

from google import genai
from google.genai import types

from backend.system_prompt import DRISHTI_SYSTEM_PROMPT
from backend.logger import log_event

logger = logging.getLogger(__name__)

LIVE_MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"


def build_live_config(voice: str = "Kore", plugin_addendum: str = "") -> types.LiveConnectConfig:
    system_prompt = DRISHTI_SYSTEM_PROMPT
    if plugin_addendum:
        system_prompt += f"\n\n{plugin_addendum}"

    return types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction=system_prompt,
        enable_affective_dialog=True,
        proactivity={"proactive_audio": True},
        input_audio_transcription={},
        output_audio_transcription={},
        media_resolution=types.MediaResolution.MEDIA_RESOLUTION_LOW,
        # Fix 1: Include all input (video frames) in turns, not just during speech
        realtime_input_config=types.RealtimeInputConfig(
            automatic_activity_detection=types.AutomaticActivityDetection(
                disabled=False,
            ),
            turn_coverage="TURN_INCLUDES_ALL_INPUT",
        ),
        thinking_config=types.ThinkingConfig(thinking_budget=0),
        # Fix 2: Compression + resumption for sessions longer than 2 minutes
        context_window_compression=types.ContextWindowCompressionConfig(
            sliding_window=types.SlidingWindow(),
        ),
        session_resumption=types.SessionResumptionConfig(),
        speech_config={
            "voice_config": {"prebuilt_voice_config": {"voice_name": voice}}
        },
    )


class GeminiLiveSession:
    """Manages a single Gemini Live API session with audio/video streaming."""

    def __init__(self, voice: str = "Kore", plugin_addendum: str = ""):
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")

        self.client = genai.Client(
            api_key=api_key,
            http_options={"api_version": "v1alpha"},
        )
        self.config = build_live_config(voice=voice, plugin_addendum=plugin_addendum)
        self._ctx_manager = None
        self.session = None
        self._running = False

    async def connect(self):
        """Establish connection to Gemini Live API."""
        t0 = time.time()
        log_event("gemini", "connecting", details={"model": LIVE_MODEL})
        self._ctx_manager = self.client.aio.live.connect(
            model=LIVE_MODEL, config=self.config
        )
        self.session = await self._ctx_manager.__aenter__()
        self._running = True
        log_event("gemini", "connected", latency_ms=(time.time() - t0) * 1000)

    async def disconnect(self):
        """Close the Gemini Live session."""
        self._running = False
        if self._ctx_manager:
            try:
                await self._ctx_manager.__aexit__(None, None, None)
            except Exception as e:
                log_event("gemini", "disconnect_error", message=str(e))
            self._ctx_manager = None
            self.session = None
        log_event("gemini", "disconnected")

    async def send_audio(self, audio_data: bytes):
        """Send raw PCM audio chunk to Gemini."""
        if not self.session:
            return
        t0 = time.time()
        await self.session.send_realtime_input(
            audio=types.Blob(data=audio_data, mime_type="audio/pcm;rate=16000")
        )
        log_event("gemini", "send_audio", details={
            "size_bytes": len(audio_data),
        }, latency_ms=(time.time() - t0) * 1000)

    async def send_image(self, jpeg_data: bytes):
        """Send a JPEG frame to Gemini."""
        if not self.session:
            return
        t0 = time.time()
        await self.session.send_realtime_input(
            media=types.Blob(data=jpeg_data, mime_type="image/jpeg")
        )
        log_event("gemini", "send_image", details={
            "size_bytes": len(jpeg_data),
        }, latency_ms=(time.time() - t0) * 1000)

    async def send_text_context(self, text: str, end_of_turn: bool = False):
        """Inject text context into the session (for spatial state updates)."""
        if not self.session:
            return
        t0 = time.time()
        await self.session.send_client_content(
            turns=types.Content(role="user", parts=[types.Part(text=text)]),
            turn_complete=end_of_turn,
        )
        log_event("gemini", "send_text_context", details={
            "text_length": len(text),
            "text_preview": text[:150],
            "turn_complete": end_of_turn,
        }, latency_ms=(time.time() - t0) * 1000)

    async def receive_responses(self) -> AsyncGenerator[dict, None]:
        """
        Yield response events from Gemini.
        Each yielded dict has a 'type' key:
          - 'audio': raw PCM bytes in 'data'
          - 'input_transcription': user speech transcription in 'text'
          - 'output_transcription': agent speech transcription in 'text'
          - 'tool_call': function call in 'call'
          - 'turn_complete': signals end of a turn
        """
        if not self.session:
            return

        while self._running:
            try:
                async for response in self.session.receive():
                    server_content = response.server_content
                    tool_call = response.tool_call

                    if tool_call:
                        log_event("gemini", "recv_tool_call", details={
                            "call": str(tool_call)[:200],
                        })
                        yield {"type": "tool_call", "call": tool_call}
                        continue

                    if not server_content:
                        continue

                    if (
                        server_content.input_transcription
                        and server_content.input_transcription.text
                    ):
                        text = server_content.input_transcription.text
                        log_event("gemini", "recv_input_transcription", details={
                            "text": text[:100],
                        })
                        yield {"type": "input_transcription", "text": text}

                    if (
                        server_content.output_transcription
                        and server_content.output_transcription.text
                    ):
                        text = server_content.output_transcription.text
                        log_event("gemini", "recv_output_transcription", details={
                            "text": text[:100],
                        })
                        yield {"type": "output_transcription", "text": text}

                    if server_content.model_turn:
                        for part in server_content.model_turn.parts:
                            if part.inline_data:
                                log_event("gemini", "recv_audio", details={
                                    "size_bytes": len(part.inline_data.data),
                                })
                                yield {
                                    "type": "audio",
                                    "data": part.inline_data.data,
                                }

                    if getattr(server_content, "interrupted", False):
                        log_event("gemini", "recv_interrupted")

                    if getattr(server_content, "session_resumption_update", None):
                        log_event("gemini", "recv_session_resumption")

                    if server_content.turn_complete:
                        log_event("gemini", "recv_turn_complete")
                        yield {"type": "turn_complete"}

            except Exception as e:
                if self._running:
                    log_event("gemini", "recv_error", message=str(e))
                break
