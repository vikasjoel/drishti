"""
Gemini generateContent — the REAL perception system.
Returns rich structured JSON about the scene.
Called event-driven by CognitiveTrigger, NOT on a timer.
"""
import json
import logging
import os
import time

from google import genai
from google.genai import types

from backend.logger import log_event

logger = logging.getLogger("drishti.cognitive")

COGNITIVE_PROMPT = """You are the perception system for Drishti, a spatial intelligence assistant helping a blind person navigate.

Analyze this camera frame. Return ONLY a JSON object with these fields:

{
  "environment": {
    "type": "<indoor_room|indoor_corridor|indoor_stairs|outdoor_path|outdoor_open|outdoor_crossing|vehicle|elevator|unknown>",
    "description": "one sentence describing the space",
    "lighting": "<good|dim|dark|glare>",
    "surface": "<smooth|paved|gravel|grass|stairs_up|stairs_down|wet|uneven>"
  },
  "path_ahead": {
    "clear": true,
    "blocked_by": null,
    "width": "<narrow|normal|wide>",
    "hazards": [],
    "safety_alert": null
  },
  "navigation_action": "turn left in 2 steps, stairs going down",
  "objects": [
    {
      "what": "person",
      "where": "ahead, slightly left",
      "distance": "about 5 meters",
      "moving": true,
      "toward_user": true,
      "navigation_relevant": true
    }
  ],
  "text_signs": [],
  "transition": "<same|entering_new|leaving>",
  "suggested_speech": null
}

RULES:
- navigation_action: THE MOST IMPORTANT FIELD. A turn-by-turn direction for a blind person. Examples: "continue straight", "turn left after 2 steps", "stop, wall ahead", "step 2 steps right to avoid chair", "stairs turning left ahead", "you reached the landing, turn right". Always provide this — it should be an ACTION the user can follow, not a description.
- navigation_relevant = TRUE for: anything in the direct walking path ahead (within 3 meters, center of frame), people, vehicles, stairs, doors, walls or barriers the user would walk into, significant obstacles
- navigation_relevant = FALSE for: objects clearly on the sides that don't affect the walking path, background elements, decorations not in the path
- path_ahead.clear should be FALSE if there is any wall, obstacle, or barrier within approximately 2 meters directly ahead of the camera. A path is only "clear" if the user can walk straight forward for at least 3 steps without hitting anything.
- safety_alert ONLY for immediate dangers (collision risk, drop-off, traffic). null otherwise.
- suggested_speech: what you'd tell a blind person RIGHT NOW. Give DIRECTIONS not descriptions. "Turn left after 3 steps" not "There is a hallway to the left." Under 10 words for urgent, under 25 for informational. Only null if scene is completely unchanged.
- Use ONLY these environment types: indoor_room, indoor_corridor, indoor_stairs, outdoor_path, outdoor_open, outdoor_crossing, vehicle, elevator, unknown
- Distance in real-world estimates: "beside you", "1 step", "a few steps", "5 meters", "far"
- path_ahead.clear is critical — can the user walk straight forward safely?"""


class GeminiCognitive:
    def __init__(self, model=None):
        self.model = model or os.environ.get("COGNITIVE_MODEL", "gemini-2.5-flash")

        # Use the same API key as Gemini Live session.
        # NOTE: Do NOT use GOOGLE_GENAI_USE_VERTEXAI env var — it pollutes
        # the genai global state and breaks the Gemini Live session (404).
        # The cognitive client uses the API key directly. If you need Vertex AI,
        # pass vertexai=True explicitly here only, NOT via env var.
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY required for GeminiCognitive")
        self.client = genai.Client(api_key=api_key)
        logger.info("GeminiCognitive using API key")
        self.call_count = 0
        self.last_result = None
        self.last_call_time = 0

    async def analyze(self, jpeg_bytes):
        """
        Call generateContent with the frame.
        Returns parsed JSON or None on error.
        """
        self.call_count += 1
        self.last_call_time = time.time()
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
                    temperature=0.1,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                )
            )

            elapsed_ms = (time.time() - t0) * 1000
            result = json.loads(response.text)
            self.last_result = result

            log_event("cognitive", "analysis", details={
                "call_number": self.call_count,
                "environment": result.get("environment", {}).get("type", "?"),
                "path_clear": result.get("path_ahead", {}).get("clear", "?"),
                "objects": len(result.get("objects", [])),
                "transition": result.get("transition", "?"),
                "suggested_speech": result.get("suggested_speech"),
            }, latency_ms=elapsed_ms)

            return result

        except json.JSONDecodeError as e:
            elapsed_ms = (time.time() - t0) * 1000
            log_event("cognitive", "json_error", message=str(e), latency_ms=elapsed_ms)
            return None
        except Exception as e:
            elapsed_ms = (time.time() - t0) * 1000
            log_event("cognitive", "error", message=str(e), latency_ms=elapsed_ms)
            return None
