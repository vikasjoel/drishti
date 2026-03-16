"""
EXPERIMENT: Optic Nerve v2 — The Predict-Verify Loop
=====================================================
Fixes the 1/6 hit rate by making each function call part of
a conversation between perception (Gemini) and brain (backend).

Changes from v1:
1. NON_BLOCKING behavior on function declaration
2. Rich tool_response with predictions + questions for next scan
3. Each scan prompt is UNIQUE — references previous findings
4. Tests WHEN_IDLE scheduling instead of SILENT
5. Alternates between static and slightly modified frames
"""

import asyncio
import json
import os
import time
import random
from datetime import datetime

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"

# ─── The function tool — now with NON_BLOCKING ─────────────────────
SPATIAL_TOOL = {
    "function_declarations": [
        {
            "name": "report_spatial_observation",
            "description": (
                "Report structured spatial observations from the current camera frame. "
                "You MUST call this function EVERY time you receive a SPATIAL SCAN message. "
                "This function feeds a real-time spatial tracking system that depends on "
                "continuous updates. Even if the scene looks the same, CONFIRM positions — "
                "the tracking system needs continuous validation to maintain confidence. "
                "NEVER skip calling this function when asked to scan."
            ),
            "behavior": "NON_BLOCKING",
            "parameters": {
                "type": "object",
                "properties": {
                    "objects": {
                        "type": "array",
                        "description": "ALL objects in current frame — report every one, every time",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {
                                    "type": "string",
                                    "description": "What the object is"
                                },
                                "position_x": {
                                    "type": "number",
                                    "description": "Horizontal position 0.0=left to 1.0=right"
                                },
                                "position_y": {
                                    "type": "number",
                                    "description": "Vertical position 0.0=top to 1.0=bottom"
                                },
                                "size_percent": {
                                    "type": "number",
                                    "description": "Frame area percentage 0-100"
                                },
                                "clock_position": {
                                    "type": "string",
                                    "description": "Clock position 10-2 o'clock"
                                },
                                "distance_estimate": {
                                    "type": "string",
                                    "description": "very_close/close/near/medium/far/very_far"
                                },
                                "changed_since_last": {
                                    "type": "boolean",
                                    "description": "Has this object moved or changed since last scan?"
                                }
                            },
                            "required": ["description", "position_x", "position_y", "size_percent"]
                        }
                    },
                    "environment_description": {
                        "type": "string",
                        "description": "Brief description of the space"
                    },
                    "lighting": {
                        "type": "string",
                        "description": "dark/dim/normal/bright"
                    },
                    "frame_quality": {
                        "type": "number",
                        "description": "0.0 to 1.0"
                    },
                    "prediction_verification": {
                        "type": "object",
                        "description": "Verify predictions from the brain's last response",
                        "properties": {
                            "predictions_confirmed": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Which predictions from the brain were correct"
                            },
                            "predictions_wrong": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Which predictions were incorrect and what actually happened"
                            },
                            "surprises": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Anything unexpected not in the predictions"
                            }
                        }
                    }
                },
                "required": ["objects", "environment_description"]
            }
        }
    ]
}

SYSTEM_PROMPT = """You are a spatial perception system connected to a real-time tracking brain.

Your ONLY job: when you receive a SPATIAL SCAN message, call report_spatial_observation
with structured data about what you see in the camera frames.

CRITICAL RULES:
1. EVERY scan message MUST result in a function call. No exceptions.
2. The tracking brain DEPENDS on continuous data — even "nothing changed" is valuable data.
3. After each scan, the brain sends you PREDICTIONS about what the next frame should show.
   When you scan again, VERIFY those predictions: confirmed or wrong?
4. Report ALL objects every time. The brain uses position deltas to compute trajectories.
5. If the scene hasn't changed, confirm all positions — the brain needs confirmation
   to maintain confidence scores.
6. Do NOT speak audio in response to scan messages. ONLY call the function.
7. You may speak audio if the user asks you a direct voice question."""


class WorldModelBrain:
    """
    Simulated backend brain that processes observations
    and generates predictions for the next scan.
    """

    def __init__(self):
        self.observations = []
        self.tracked_objects = {}
        self.scan_count = 0
        self.predictions = []

    def process_observation(self, args):
        """Process a tool call and generate predictions for next scan."""
        self.scan_count += 1
        self.observations.append(args)

        objects = args.get("objects", [])

        # Update tracked objects
        for obj in objects:
            desc = obj.get("description", "unknown")
            key = desc[:30]  # Simple identity by description

            if key in self.tracked_objects:
                prev = self.tracked_objects[key]
                # Compute position delta
                dx = obj.get("position_x", 0) - prev.get("position_x", 0)
                dy = obj.get("position_y", 0) - prev.get("position_y", 0)
                ds = obj.get("size_percent", 0) - prev.get("size_percent", 0)
                obj["_dx"] = dx
                obj["_dy"] = dy
                obj["_ds"] = ds

            self.tracked_objects[key] = obj

        # Generate predictions for next scan
        predictions = []
        questions = []

        for key, obj in self.tracked_objects.items():
            desc = obj.get("description", "unknown")
            px = obj.get("position_x", 0.5)
            py = obj.get("position_y", 0.5)
            sz = obj.get("size_percent", 5)

            dx = obj.get("_dx", 0)
            dy = obj.get("_dy", 0)
            ds = obj.get("_ds", 0)

            if abs(dx) > 0.02 or abs(dy) > 0.02:
                # Object was moving — predict continued movement
                pred_x = round(px + dx, 2)
                pred_y = round(py + dy, 2)
                pred_sz = round(sz + ds, 1)
                predictions.append(
                    f"'{desc}' was moving — predict position ({pred_x}, {pred_y}), size {pred_sz}%"
                )
                questions.append(
                    f"Has '{desc}' continued moving in the same direction?"
                )
            else:
                # Object was static — predict same position
                predictions.append(
                    f"'{desc}' should still be at ({px}, {py}), size ~{sz}%"
                )

        # Always add a surprise-check question
        questions.append("Are there any NEW objects that weren't in the previous scan?")
        questions.append("Has the lighting or environment changed?")

        self.predictions = predictions

        return {
            "result": "observation_processed",
            "objects_tracked": len(self.tracked_objects),
            "scan_number": self.scan_count,
            "brain_predictions": predictions[:5],
            "verify_next_scan": questions[:4],
            "confidence_status": "high" if self.scan_count > 1 else "building",
            "message": f"Brain updated. Tracking {len(self.tracked_objects)} objects. "
                       f"Next scan should verify {len(predictions)} predictions."
        }

    def generate_scan_prompt(self, scan_number):
        """Generate a UNIQUE scan prompt based on current brain state."""

        if scan_number == 1:
            return (
                "SPATIAL SCAN #1 -- INITIAL OBSERVATION: "
                "This is the first scan. Call report_spatial_observation with "
                "every object you see in the camera frame. Report positions, "
                "sizes, clock positions, and distances. Set changed_since_last "
                "to false for all objects since this is the first observation."
            )

        # Build prompt from brain state
        parts = [f"SPATIAL SCAN #{scan_number} -- VERIFICATION REQUIRED:"]

        if self.predictions:
            parts.append("The tracking brain made these PREDICTIONS. Verify each one:")
            for i, pred in enumerate(self.predictions[:4], 1):
                parts.append(f"  P{i}: {pred}")

        parts.append("")
        parts.append(
            "Call report_spatial_observation NOW. For each object: report current "
            "position and size. In prediction_verification, state which predictions "
            "were confirmed and which were wrong. Report any SURPRISES -- objects that "
            "appeared or disappeared unexpectedly."
        )

        # Add variety to prevent caching
        parts.append(f"[scan_time={time.time():.0f}]")

        return "\n".join(parts)


async def run_experiment():
    client = genai.Client(http_options={"api_version": "v1alpha"})
    brain = WorldModelBrain()

    results = {
        "frames_sent": 0,
        "scans_sent": 0,
        "tool_calls": 0,
        "audio_chunks": 0,
        "speech_texts": [],
        "tool_call_data": [],
        "errors": [],
        "scan_details": []
    }

    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction=SYSTEM_PROMPT,
        tools=[SPATIAL_TOOL],
        realtime_input_config=types.RealtimeInputConfig(
            automatic_activity_detection=types.AutomaticActivityDetection(
                disabled=False
            ),
            turn_coverage="TURN_INCLUDES_ALL_INPUT"
        ),
        proactivity={"proactive_audio": True},
        enable_affective_dialog=True,
        input_audio_transcription={},
        output_audio_transcription={},
        media_resolution=types.MediaResolution.MEDIA_RESOLUTION_LOW,
        context_window_compression=types.ContextWindowCompressionConfig(
            sliding_window=types.SlidingWindow(),
        ),
        # CRITICAL: no thinking — thinking + function calling crashes
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    )

    # Create test frames — MULTIPLE variants to simulate change
    frames = create_test_frames()

    print("=" * 60)
    print("EXPERIMENT: Optic Nerve v2 -- Predict-Verify Loop")
    print("=" * 60)
    print(f"Frames prepared: {len(frames)} variants")
    print("Connecting...")

    try:
        async with client.aio.live.connect(model=MODEL, config=config) as session:
            print("Connected")
            print()

            receive_task = asyncio.create_task(
                receive_loop(session, results, brain)
            )

            start = time.time()
            frame_count = 0
            scan_count = 0

            try:
                while time.time() - start < 45:  # 45 seconds
                    frame_count += 1
                    results["frames_sent"] = frame_count

                    # Alternate frames to simulate scene changes
                    frame_idx = min(frame_count // 8, len(frames) - 1)
                    frame_data = frames[frame_idx]

                    # Send frame
                    await session.send_realtime_input(
                        video=types.Blob(
                            data=frame_data,
                            mime_type="image/jpeg"
                        )
                    )

                    # Every 7 frames (~7 seconds), send scan
                    if frame_count % 7 == 0:
                        scan_count += 1
                        results["scans_sent"] = scan_count

                        # Generate UNIQUE prompt from brain state
                        prompt = brain.generate_scan_prompt(scan_count)

                        print(f"\n{'~'*50}")
                        print(f"[Frame {frame_count}] SCAN #{scan_count}")
                        print(f"Prompt: {prompt[:120]}...")

                        results["scan_details"].append({
                            "scan": scan_count,
                            "frame": frame_count,
                            "prompt_preview": prompt[:200]
                        })

                        await session.send_client_content(
                            turns={"role": "user", "parts": [{"text": prompt}]},
                            turn_complete=True
                        )

                        # Give extra time for function call to process
                        await asyncio.sleep(0.5)

                    await asyncio.sleep(1.0)

            finally:
                receive_task.cancel()
                try:
                    await receive_task
                except asyncio.CancelledError:
                    pass

    except Exception as e:
        print(f"\nError: {e}")
        results["errors"].append(str(e))

    # Print results
    print()
    print("=" * 60)
    print("RESULTS -- OPTIC NERVE v2")
    print("=" * 60)
    print(f"Frames sent:         {results['frames_sent']}")
    print(f"Scans sent:          {results['scans_sent']}")
    print(f"Tool calls received: {results['tool_calls']}")
    print(f"Audio chunks:        {results['audio_chunks']}")
    print(f"Gemini spoke:        {len(results['speech_texts'])} times")
    print(f"Errors:              {len(results['errors'])}")
    print()

    hit_rate = results['tool_calls'] / max(results['scans_sent'], 1)

    if results["tool_calls"] > 0:
        print(f"HIT RATE: {results['tool_calls']}/{results['scans_sent']} = {hit_rate:.0%}")
        print()

        if hit_rate >= 0.7:
            print("*** EXCELLENT -- Predict-verify loop works reliably ***")
        elif hit_rate >= 0.4:
            print("** GOOD -- Significant improvement over v1 (was 17%) **")
        elif hit_rate > 0.17:
            print("* IMPROVED -- Better than v1 but needs more tuning *")
        else:
            print("-> SAME AS V1 -- The fixes didn't help, need different approach")

        print()
        print("Tool call details:")
        for i, tc in enumerate(results["tool_call_data"], 1):
            obj_count = len(tc.get("objects", []))
            env = tc.get("environment_description", "?")[:60]
            verif = tc.get("prediction_verification", {})
            confirmed = len(verif.get("predictions_confirmed", []))
            wrong = len(verif.get("predictions_wrong", []))
            surprises = len(verif.get("surprises", []))
            print(f"  Scan {i}: {obj_count} objects, env='{env}'")
            if confirmed or wrong or surprises:
                print(f"    Predictions: {confirmed} confirmed, {wrong} wrong, {surprises} surprises")
    else:
        print("No function calls received")
        if results["speech_texts"]:
            print("Gemini spoke instead:")
            for t in results["speech_texts"][:5]:
                print(f'  "{t}"')

    if results["errors"]:
        print(f"\nErrors: {results['errors']}")

    # Save
    with open("optic_nerve_v2_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nSaved to optic_nerve_v2_results.json")


async def receive_loop(session, results, brain):
    """Listen for Gemini responses — process tool calls through the brain."""
    try:
        async for response in session.receive():
            ts = datetime.now().strftime("%H:%M:%S")

            # TOOL CALL
            if response.tool_call:
                for fc in response.tool_call.function_calls:
                    results["tool_calls"] += 1
                    results["tool_call_data"].append(fc.args)

                    # Print what was found
                    print(f"\n  * TOOL CALL #{results['tool_calls']} at {ts}")
                    if fc.args and "objects" in fc.args:
                        for obj in fc.args["objects"]:
                            desc = obj.get("description", "?")[:35]
                            px = obj.get("position_x", "?")
                            py = obj.get("position_y", "?")
                            sz = obj.get("size_percent", "?")
                            chg = obj.get("changed_since_last", "?")
                            print(f"    {desc}: ({px},{py}) size={sz}% changed={chg}")

                    if fc.args and "prediction_verification" in fc.args:
                        pv = fc.args["prediction_verification"]
                        if pv:
                            conf = pv.get("predictions_confirmed", [])
                            wrong = pv.get("predictions_wrong", [])
                            surp = pv.get("surprises", [])
                            if conf:
                                print(f"    Confirmed: {conf}")
                            if wrong:
                                print(f"    Wrong: {wrong}")
                            if surp:
                                print(f"    Surprises: {surp}")

                    # BRAIN PROCESSES THE OBSERVATION
                    brain_response = brain.process_observation(fc.args)

                    print(f"    Brain: tracking {brain_response['objects_tracked']} objects")
                    print(f"    Predictions for next scan: {len(brain_response['brain_predictions'])}")

                    # Send rich tool response WITH predictions
                    try:
                        resp = types.FunctionResponse(
                            id=fc.id,
                            name=fc.name,
                            response={
                                **brain_response,
                                "scheduling": "WHEN_IDLE"
                            }
                        )
                        await session.send_tool_response(
                            function_responses=[resp]
                        )
                    except Exception as e:
                        print(f"    (tool response error: {e})")

            # Audio
            if response.data is not None:
                results["audio_chunks"] += 1

            # Transcripts
            if hasattr(response, 'server_content') and response.server_content:
                sc = response.server_content
                if hasattr(sc, 'output_transcription') and sc.output_transcription:
                    text = sc.output_transcription.text
                    if text and text.strip():
                        results["speech_texts"].append(text.strip())
                        print(f"  [Gemini said]: \"{text.strip()[:80]}\"")

    except asyncio.CancelledError:
        pass
    except Exception as e:
        results["errors"].append(f"receive: {str(e)}")
        print(f"  [Receive error]: {e}")


def create_test_frames():
    """
    Create MULTIPLE test frames with slight variations
    to simulate a changing scene.
    """
    try:
        from PIL import Image, ImageDraw
        import io

        frames = []

        variations = [
            {"person_x": 250, "bottle": True,  "ball": False, "label": "base scene"},
            {"person_x": 290, "bottle": True,  "ball": False, "label": "person moved right"},
            {"person_x": 330, "bottle": True,  "ball": True,  "label": "ball appeared"},
            {"person_x": 370, "bottle": False, "ball": True,  "label": "person moved more, bottle gone"},
        ]

        for var in variations:
            img = Image.new('RGB', (768, 768), color=(200, 200, 200))
            draw = ImageDraw.Draw(img)

            px = var["person_x"]

            # Person
            draw.rectangle([px, 180, px+120, 560], fill=(50, 50, 150))
            draw.ellipse([px+25, 120, px+95, 190], fill=(200, 150, 130))

            # Desk
            draw.rectangle([480, 380, 700, 430], fill=(139, 90, 43))
            draw.rectangle([490, 430, 515, 580], fill=(110, 70, 30))
            draw.rectangle([670, 430, 695, 580], fill=(110, 70, 30))

            # Door
            draw.rectangle([680, 80, 760, 480], fill=(160, 120, 80))
            draw.ellipse([740, 270, 755, 290], fill=(200, 180, 50))

            # Bottle (conditional)
            if var["bottle"]:
                draw.rectangle([570, 340, 600, 380], fill=(30, 100, 200))

            # Ball (conditional)
            if var["ball"]:
                draw.ellipse([150, 550, 200, 600], fill=(220, 30, 30))

            # Floor
            draw.rectangle([0, 580, 768, 768], fill=(180, 170, 160))

            # Window
            draw.rectangle([100, 50, 400, 250], fill=(170, 200, 220))
            draw.rectangle([95, 45, 405, 55], fill=(120, 100, 80))

            # EXIT sign
            try:
                draw.text((690, 60), "EXIT", fill=(255, 0, 0))
            except Exception:
                pass

            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=75)
            frames.append(buf.getvalue())

            print(f"  Frame {len(frames)}: {var['label']} ({len(buf.getvalue())} bytes)")

        # Save first and last for reference
        Image.open(io.BytesIO(frames[0])).save("frame_v2_first.jpg")
        Image.open(io.BytesIO(frames[-1])).save("frame_v2_last.jpg")

        return frames

    except ImportError:
        print("PIL not installed -- run: pip install Pillow")
        return [bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46,
            0x49, 0x46, 0x00, 0x01, 0x01, 0x00, 0x00, 0x01,
            0x00, 0x01, 0x00, 0x00, 0xFF, 0xD9
        ])]


if __name__ == "__main__":
    asyncio.run(run_experiment())
