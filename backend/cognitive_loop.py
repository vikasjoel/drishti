"""
Cognitive Loop — periodic deep scene analysis using Gemini generateContent.

Runs every INTERVAL seconds for:
- Environment type classification
- Scene transition detection
- Hazard detection that Cloud Vision might miss
- OCR verification
"""

import asyncio
import json
import logging
import os
import time

from google import genai
from google.genai import types

from backend.logger import log_event

logger = logging.getLogger(__name__)

COGNITIVE_INTERVAL = int(os.environ.get("COGNITIVE_LOOP_INTERVAL", "7"))

COGNITIVE_PROMPT = (
    "Analyze this scene for a spatial intelligence system helping a person navigate. "
    "Return JSON with these fields:\n"
    "- environment_type: string (e.g. 'hallway', 'kitchen', 'outdoor sidewalk', 'office')\n"
    "- hazards: array of strings (floor changes, wet surfaces, obstacles)\n"
    "- text_visible: array of strings (signs, labels, text you can read)\n"
    "- scene_description: string (one sentence describing the scene)\n"
    "- place_transition: 'same' if scene looks similar to recent frames, "
    "'new' if it's a clearly different space"
)


class CognitiveLoop:
    def __init__(self):
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY required for CognitiveLoop")
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"
        self.last_analysis_time = 0
        self.analysis_count = 0
        self.last_result: dict | None = None

    async def maybe_analyze(self, jpeg_bytes: bytes, frame_count: int) -> dict | None:
        """Run cognitive analysis if enough time has passed. Returns result or None."""
        now = time.time()
        if now - self.last_analysis_time < COGNITIVE_INTERVAL:
            return None

        self.last_analysis_time = now
        self.analysis_count += 1
        t0 = time.time()

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=[
                    types.Part.from_bytes(data=jpeg_bytes, mime_type="image/jpeg"),
                    COGNITIVE_PROMPT,
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )

            elapsed_ms = (time.time() - t0) * 1000
            result = json.loads(response.text)
            self.last_result = result

            log_event("cognitive", "analysis", details={
                "frame": frame_count,
                "call_number": self.analysis_count,
                "environment": result.get("environment_type", "unknown"),
                "hazards": len(result.get("hazards", [])),
                "texts": len(result.get("text_visible", [])),
                "transition": result.get("place_transition", "same"),
            }, latency_ms=elapsed_ms)

            return result

        except Exception as e:
            elapsed_ms = (time.time() - t0) * 1000
            log_event("cognitive", "error", message=str(e), latency_ms=elapsed_ms)
            return None
