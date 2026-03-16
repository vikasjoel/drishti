"""
Drishti v4 backend — FastAPI app with WebSocket endpoint.
Conductor model: Python decides WHEN Gemini speaks, not WHAT.
Gemini Live = VOICE, Gemini generateContent = EYES, WorldModel = MIND.
"""

import asyncio
import base64
import json
import logging
import os
import time

from starlette.websockets import WebSocketState
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.gemini_session import GeminiLiveSession
from backend.cloud_vision import CloudVisionClient
from backend.cognitive_perception import GeminiCognitive
from backend.cognitive_trigger import CognitiveTrigger
from backend.sensor_processor import SensorProcessor
from backend.world_model import WorldModel
from backend.plugins import PLUGINS
from backend.frame_quality import is_frame_good
from backend.logger import log_event, new_session_stats

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Drishti v4")

# Serve frontend static files
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/manifest.json")
async def manifest():
    return FileResponse(os.path.join(FRONTEND_DIR, "manifest.json"))


async def _safe_ws_send(ws: WebSocket, data: dict):
    """Send JSON to WebSocket only if still connected."""
    try:
        if ws.client_state == WebSocketState.CONNECTED:
            await ws.send_text(json.dumps(data))
    except Exception:
        pass


async def _safe_gemini_send(gemini, text: str, end_of_turn: bool = True):
    """Send text to Gemini only if still connected."""
    try:
        await gemini.send_text_context(text, end_of_turn=end_of_turn)
    except Exception:
        pass


def _get_plugin_config(name: str) -> dict:
    """Return full plugin config dict."""
    return PLUGINS.get(name, PLUGINS.get("blind_navigation"))


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    log_event("main", "client_connected")

    plugin_name = ws.query_params.get(
        "plugin", os.environ.get("DEFAULT_PLUGIN", "blind_navigation")
    )
    plugin = _get_plugin_config(plugin_name)
    voice = plugin["voice"]
    addendum = plugin["addendum"]

    log_event("main", "plugin_selected", details={
        "plugin": plugin_name,
        "voice": voice,
        "camera_mode": plugin["camera_mode"],
    })

    # Initialize components
    gemini = GeminiLiveSession(voice=voice, plugin_addendum=addendum)
    world_model = WorldModel(plugin)
    sensor_processor = SensorProcessor()
    cognitive_trigger = CognitiveTrigger()
    cloud_vision = CloudVisionClient()

    # Cognitive perception (Gemini generateContent for scene analysis)
    try:
        cognitive = GeminiCognitive()
    except ValueError:
        cognitive = None
        log_event("main", "cognitive_disabled", message="No API key")

    stats = new_session_stats()
    receive_task = None

    try:
        await gemini.connect()
        await stats.start_periodic_summary(interval=30)

        receive_task = asyncio.create_task(
            _forward_gemini_to_client(gemini, ws, world_model, stats)
        )

        await _forward_client_to_gemini(
            ws, gemini, world_model, cloud_vision, cognitive,
            cognitive_trigger, sensor_processor, plugin, stats,
        )

    except WebSocketDisconnect:
        log_event("main", "client_disconnected")
    except Exception as e:
        log_event("main", "websocket_error", message=str(e))
    finally:
        stats.print_summary()
        stats.stop_periodic_summary()
        if receive_task:
            receive_task.cancel()
        await gemini.disconnect()
        try:
            await ws.close()
        except Exception:
            pass


async def _forward_client_to_gemini(
    ws: WebSocket, gemini: GeminiLiveSession,
    world_model: WorldModel, cloud_vision: CloudVisionClient,
    cognitive, cognitive_trigger: CognitiveTrigger,
    sensor_processor: SensorProcessor, plugin: dict, stats,
):
    """Read messages from browser WebSocket, process through v4 pipeline."""
    frame_count = 0
    last_frame_jpeg = None
    frame_change_score = 0.0
    cv_has_priority = False

    while True:
        raw = await ws.receive_text()
        msg = json.loads(raw)
        msg_type = msg.get("type")

        if msg_type == "audio":
            audio_bytes = base64.b64decode(msg["data"])
            stats.record_audio_sent(len(audio_bytes))
            await gemini.send_audio(audio_bytes)

        elif msg_type == "image":
            jpeg_bytes = base64.b64decode(msg["data"])
            frame_count += 1
            stats.record_frame()

            # STAMP this frame with current sensor state (v4.2)
            frame_snapshot = sensor_processor.get_snapshot()
            frame_snapshot["frame_change"] = msg.get("frame_change", 0.0)

            # 1. Send frame to Gemini Live (passive visual context)
            await gemini.send_image(jpeg_bytes)

            # Frame quality gate
            if not is_frame_good(jpeg_bytes):
                continue

            # 2. Frame change detection
            frame_change_score = msg.get("frame_change", 0.0)

            # 3. CV Emergency tripwire (every 3rd frame to save cost)
            if frame_count % 3 == 0:
                try:
                    cv_result = await cloud_vision.analyze_frame(jpeg_bytes)
                    cv_result["frame_snapshot"] = frame_snapshot  # attach stamp
                    world_model.absorb_cv(cv_result, plugin)
                    cv_has_priority = any(
                        obj.get("label") in plugin.get("priority_labels", [])
                        and obj.get("area_pct", 0) > plugin.get("cv_emergency_threshold", 15)
                        for obj in cv_result.get("objects", [])
                    )
                except Exception as e:
                    log_event("main", "cv_error", message=str(e))
                    cv_has_priority = False

            # 4. Cognitive perception (event-driven, not on timer)
            sensor_state = sensor_processor.get_current_state()
            is_cold_start = frame_count <= 3

            cog_should_call = cognitive and cognitive_trigger.should_call(
                sensors=sensor_state,
                frame_change=frame_change_score,
                cv_has_new_priority=cv_has_priority,
                is_cold_start=is_cold_start,
            )

            # Low spatial confidence forces re-perception
            if not cog_should_call and cognitive:
                cog_should_call = cognitive_trigger.force_call_if_needed(
                    world_model.spatial_confidence,
                    world_model.user_state.get("movement", "unknown"),
                    time.time() - cognitive.last_call_time,
                )

            if cog_should_call:
                try:
                    cog_result = await cognitive.analyze(jpeg_bytes)
                    if cog_result:
                        cog_result["frame_snapshot"] = frame_snapshot  # attach stamp
                        world_model.absorb_cognitive(cog_result)
                        cognitive_trigger.record_call(success=True)
                    else:
                        cognitive_trigger.record_call(success=False)
                except Exception as e:
                    cognitive_trigger.record_call(success=False)
                    log_event("main", "cognitive_error", message=str(e))

            # 5. World Model decides
            nudge = world_model.decide()

            # 6. Execute nudge
            if nudge:
                await _safe_gemini_send(
                    gemini, nudge["text"], end_of_turn=nudge["end_of_turn"]
                )
                stats.record_context_injection(
                    has_speak_directive=nudge["end_of_turn"]
                )
                log_event("main", "nudge_sent", details={
                    "priority": nudge["priority"],
                    "reason": nudge["reason"],
                    "end_of_turn": nudge["end_of_turn"],
                    "text": nudge["text"][:100],
                })

            # 7. Send brain state to frontend
            brain_state = world_model.get_brain_state_for_ui()
            brain_state["frame"] = frame_count
            await _safe_ws_send(ws, {
                "type": "brain_state",
                **brain_state,
            })

            last_frame_jpeg = jpeg_bytes

        elif msg_type == "sensors":
            # Phone sensor data from sensors.js (v4.2: flat fields, not nested)
            sensor_state = sensor_processor.process(msg)
            world_model.absorb_sensors(sensor_state)

        elif msg_type == "text":
            await gemini.send_text_context(
                msg["text"], end_of_turn=msg.get("end_of_turn", True)
            )

        elif msg_type == "mode_switch":
            new_plugin_name = msg.get("plugin", "blind_navigation")
            new_plugin = _get_plugin_config(new_plugin_name)
            plugin = new_plugin
            log_event("main", "mode_switch", details={"new_plugin": new_plugin_name})
            await gemini.send_text_context(
                f"SYSTEM: Switching to {new_plugin_name.replace('_', ' ').title()} mode. "
                f"{new_plugin['addendum']}\nAdapt your communication style immediately.",
                end_of_turn=False,
            )
            # Re-initialize world model with new plugin
            world_model = WorldModel(new_plugin)
            await _safe_ws_send(ws, {
                "type": "mode_switched",
                "plugin": new_plugin_name,
            })

        elif msg_type == "ping":
            await _safe_ws_send(ws, {
                "type": "pong",
                "client_ts": msg.get("ts", 0),
            })


async def _forward_gemini_to_client(
    gemini: GeminiLiveSession, ws: WebSocket,
    world_model: WorldModel, stats,
):
    """Read responses from Gemini, forward to browser, feed transcriptions to WorldModel."""
    try:
        async for event in gemini.receive_responses():
            etype = event["type"]

            if etype == "audio":
                data_b64 = base64.b64encode(event["data"]).decode("ascii")
                stats.record_gemini_audio()
                await _safe_ws_send(ws, {
                    "type": "audio",
                    "data": data_b64,
                })

            elif etype == "input_transcription":
                world_model.on_input_transcript(event["text"])
                stats.record_gemini_transcription(is_output=False)
                await _safe_ws_send(ws, {
                    "type": "input_transcription",
                    "text": event["text"],
                })

            elif etype == "output_transcription":
                world_model.on_output_transcript(event["text"])
                stats.record_gemini_transcription(is_output=True)
                await _safe_ws_send(ws, {
                    "type": "output_transcription",
                    "text": event["text"],
                })

            elif etype == "turn_complete":
                world_model.on_turn_complete()
                await _safe_ws_send(ws, {"type": "turn_complete"})

    except Exception as e:
        log_event("main", "gemini_forward_ended", message=str(e))
