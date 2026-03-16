"""
EXPERIMENT: The Optic Nerve
============================
Can Gemini Live API call a structured function based on what it sees
in video frames, giving our backend brain structured spatial data?

This is the single most important experiment for Drishti's architecture.

What we're testing:
1. Define report_spatial_observation as a function tool
2. Stream video frames via send_realtime_input
3. Periodically prompt Gemini to analyze frames and call the function
4. Check if we get structured JSON back via tool_call

Run: python experiment_optic_nerve.py
Requires: GOOGLE_API_KEY in .env or environment
"""

import asyncio
import base64
import json
import os
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# ─── Config ───────────────────────────────────────────────────────────
MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"

# The function Gemini should call — this is the "optic nerve"
SPATIAL_OBSERVATION_TOOL = {
    "function_declarations": [
        {
            "name": "report_spatial_observation",
            "description": (
                "Report structured spatial observations from the current camera frame. "
                "You MUST call this function every time you are asked to analyze a frame. "
                "Report ALL objects you see with their positions and sizes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "objects": {
                        "type": "array",
                        "description": "List of objects observed in the current frame",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {
                                    "type": "string",
                                    "description": "What the object is (e.g., 'person in blue shirt', 'wooden desk', 'door')"
                                },
                                "position_x": {
                                    "type": "number",
                                    "description": "Horizontal position in frame, 0.0=left edge, 0.5=center, 1.0=right edge"
                                },
                                "position_y": {
                                    "type": "number",
                                    "description": "Vertical position in frame, 0.0=top, 0.5=middle, 1.0=bottom"
                                },
                                "size_percent": {
                                    "type": "number",
                                    "description": "Approximate percentage of frame area this object occupies (0-100)"
                                },
                                "is_moving": {
                                    "type": "boolean",
                                    "description": "Whether the object appears to be in motion"
                                },
                                "clock_position": {
                                    "type": "string",
                                    "description": "Clock position from user perspective (e.g., '11 o clock', '12 o clock', '2 o clock')"
                                },
                                "distance_estimate": {
                                    "type": "string",
                                    "description": "Estimated distance: 'very_close', 'close', 'near', 'medium', 'far', 'very_far'"
                                }
                            },
                            "required": ["description", "position_x", "position_y", "size_percent"]
                        }
                    },
                    "environment_description": {
                        "type": "string",
                        "description": "Brief description of the overall environment/space visible"
                    },
                    "lighting": {
                        "type": "string",
                        "description": "Lighting condition: 'dark', 'dim', 'normal', 'bright'"
                    },
                    "frame_quality": {
                        "type": "number",
                        "description": "Quality of the frame for analysis, 0.0=unusable to 1.0=perfect"
                    },
                    "changes_detected": {
                        "type": "string",
                        "description": "What changed compared to previous observations, or 'first_observation' if this is the first"
                    }
                },
                "required": ["objects"]
            }
        }
    ]
}

SYSTEM_PROMPT = """You are a spatial perception system. Your job is to observe the camera feed 
and report structured spatial data through the report_spatial_observation function.

CRITICAL RULES:
1. When you receive a "SPATIAL SCAN" message, you MUST call report_spatial_observation 
   with structured data about what you see in the most recent camera frames.
2. Report EVERY visible object with its position in the frame (0.0-1.0 normalized).
3. Estimate distances using visual cues (object size relative to frame).
4. Note whether objects are moving based on comparison with previous frames.
5. Use clock positions (10-2 o'clock range) for directional reference.
6. Be precise about positions and sizes — these numbers feed a tracking system.
7. Do NOT speak audio unless specifically asked a question by the user.
8. ALWAYS call the function. Never respond with just audio when asked to scan."""

# ─── Experiment Runner ────────────────────────────────────────────────

class OpticNerveExperiment:
    def __init__(self):
        self.client = genai.Client(http_options={"api_version": "v1alpha"})
        # Also try v1beta if v1alpha fails:
        # self.client = genai.Client(http_options={"api_version": "v1beta"})
        self.results = []
        self.frame_count = 0
        self.scan_count = 0
        self.tool_calls_received = 0
        self.audio_responses = 0
        self.errors = []
        
    async def run(self, duration_seconds=60, scan_interval=5):
        """
        Run the experiment.
        
        Args:
            duration_seconds: How long to run (default 60s)
            scan_interval: How often to send SPATIAL SCAN prompt (default every 5 frames)
        """
        print("=" * 60)
        print("EXPERIMENT: The Optic Nerve")
        print("=" * 60)
        print(f"Duration: {duration_seconds}s")
        print(f"Scan interval: every {scan_interval} frames")
        print(f"Model: {MODEL}")
        print()
        
        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            system_instruction=SYSTEM_PROMPT,

            # The critical tool definition
            tools=[SPATIAL_OBSERVATION_TOOL],

            # Must see frames even when user is silent
            realtime_input_config=types.RealtimeInputConfig(
                automatic_activity_detection=types.AutomaticActivityDetection(
                    disabled=False
                ),
                turn_coverage="TURN_INCLUDES_ALL_INPUT"
            ),

            # Transcription so we can see what Gemini says
            output_audio_transcription={},

            # Disable thinking to avoid 1011 crash with function calls
            thinking_config=types.ThinkingConfig(thinking_budget=0),

            # Low res for speed
            media_resolution=types.MediaResolution.MEDIA_RESOLUTION_LOW,

            # Compression for longer sessions
            context_window_compression=types.ContextWindowCompressionConfig(
                sliding_window=types.SlidingWindow(),
            ),
        )
        
        print("Connecting to Gemini Live API...")
        
        try:
            async with self.client.aio.live.connect(model=MODEL, config=config) as session:
                print("✓ Connected!")
                print()
                print("Starting frame + scan loop...")
                print("(In real app, frames come from camera. Here we'll use a test image.)")
                print()
                
                # Create a simple test frame (or load one)
                test_frame = self._create_test_frame()
                
                start_time = time.time()
                receive_task = asyncio.create_task(self._receive_loop(session))
                
                try:
                    while time.time() - start_time < duration_seconds:
                        self.frame_count += 1
                        
                        # Send frame
                        await session.send_realtime_input(
                            media=types.Blob(
                                data=test_frame,
                                mime_type="image/jpeg"
                            )
                        )
                        
                        # Every scan_interval frames, send SPATIAL SCAN
                        if self.frame_count % scan_interval == 0:
                            self.scan_count += 1
                            scan_prompt = (
                                f"SPATIAL SCAN #{self.scan_count}: "
                                f"Analyze the current camera frame. "
                                f"Call report_spatial_observation with structured data "
                                f"about every object you see, their positions, sizes, "
                                f"and any changes from previous scans."
                            )
                            
                            print(f"\n[Frame {self.frame_count}] Sending SPATIAL SCAN #{self.scan_count}...")
                            
                            await session.send_client_content(
                                turns={"role": "user", "parts": [{"text": scan_prompt}]},
                                turn_complete=True
                            )
                        
                        # Wait ~1 second (simulate 1 FPS)
                        await asyncio.sleep(1.0)
                    
                finally:
                    receive_task.cancel()
                    try:
                        await receive_task
                    except asyncio.CancelledError:
                        pass
                
                self._print_results()
                
        except Exception as e:
            print(f"\n✗ Connection error: {e}")
            self.errors.append(str(e))
            self._print_results()
    
    async def _receive_loop(self, session):
        """Listen for responses from Gemini."""
        try:
            async for response in session.receive():
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                
                # Check for tool calls (THE KEY THING WE'RE TESTING)
                if response.tool_call:
                    self.tool_calls_received += 1
                    for fc in response.tool_call.function_calls:
                        print(f"\n{'='*60}")
                        print(f"[{timestamp}] ✓ TOOL CALL RECEIVED! #{self.tool_calls_received}")
                        print(f"  Function: {fc.name}")
                        print(f"  Args: {json.dumps(fc.args, indent=2)[:500]}")
                        print(f"{'='*60}")
                        
                        self.results.append({
                            "type": "tool_call",
                            "scan_number": self.scan_count,
                            "frame": self.frame_count,
                            "function": fc.name,
                            "args": fc.args,
                            "timestamp": timestamp
                        })
                        
                        # Send tool response back (SILENT — don't trigger speech)
                        function_response = types.FunctionResponse(
                            id=fc.id,
                            name=fc.name,
                            response={
                                "result": "observation_recorded",
                                "world_model_updated": True,
                                "scheduling": "SILENT"  # Don't speak about this
                            }
                        )
                        await session.send_tool_response(
                            function_responses=[function_response]
                        )
                
                # Check for audio
                if response.data is not None:
                    self.audio_responses += 1
                    if self.audio_responses % 10 == 1:
                        print(f"  [audio chunk #{self.audio_responses}]")

                # Check for text and transcripts in server_content
                if hasattr(response, 'server_content') and response.server_content:
                    sc = response.server_content
                    # Text response (TEXT modality)
                    if sc.model_turn:
                        for part in sc.model_turn.parts:
                            if part.text:
                                print(f"  [Gemini text]: {part.text[:200]}")
                                self.results.append({
                                    "type": "text",
                                    "text": part.text,
                                    "timestamp": timestamp
                                })
                    # Audio transcripts
                    if hasattr(sc, 'output_transcription') and sc.output_transcription:
                        text = sc.output_transcription.text
                        if text and text.strip():
                            print(f"  [Gemini said]: {text.strip()}")
                            self.results.append({
                                "type": "speech",
                                "text": text.strip(),
                                "timestamp": timestamp
                            })
                    if hasattr(sc, 'input_transcription') and sc.input_transcription:
                        text = sc.input_transcription.text
                        if text and text.strip():
                            print(f"  [User heard as]: {text.strip()}")
                    if sc.turn_complete:
                        print(f"  [turn complete]")
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"\n  [Receive error]: {e}")
            self.errors.append(str(e))
    
    def _create_test_frame(self):
        """
        Create a test JPEG frame.
        In the real app, this comes from the camera.
        Here we create a simple image or use a file if available.
        """
        try:
            # Try to use PIL to create a test image
            from PIL import Image, ImageDraw, ImageFont
            import io
            
            img = Image.new('RGB', (768, 768), color=(200, 200, 200))
            draw = ImageDraw.Draw(img)
            
            # Draw some objects to detect
            # A "person" (rectangle with circle head)
            draw.rectangle([280, 200, 380, 550], fill=(50, 50, 150))  # body
            draw.ellipse([295, 140, 365, 210], fill=(200, 150, 130))  # head
            
            # A "desk" 
            draw.rectangle([500, 400, 720, 450], fill=(139, 90, 43))  # desk top
            draw.rectangle([510, 450, 530, 600], fill=(110, 70, 30))  # leg
            draw.rectangle([690, 450, 710, 600], fill=(110, 70, 30))  # leg
            
            # A "door" on the right
            draw.rectangle([680, 100, 760, 500], fill=(160, 120, 80))  # door
            draw.ellipse([740, 290, 755, 310], fill=(200, 180, 50))   # handle
            
            # A "bottle" on the desk
            draw.rectangle([590, 360, 620, 400], fill=(30, 100, 200))  # bottle
            
            # Floor
            draw.rectangle([0, 600, 768, 768], fill=(180, 170, 160))
            
            # Text label "EXIT" near door
            try:
                draw.text((690, 80), "EXIT", fill=(255, 0, 0))
            except:
                pass
            
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=75)
            frame_bytes = buf.getvalue()
            
            print(f"✓ Created test frame: {len(frame_bytes)} bytes")
            print("  Objects in frame: person (center-left), desk (right), door (far right), bottle (on desk)")
            
            # Save for reference
            img.save("test_frame_reference.jpg")
            print("  Saved to test_frame.jpg for reference")
            
            return frame_bytes
            
        except ImportError:
            # Fallback: create minimal valid JPEG
            print("  (PIL not available, using minimal test frame)")
            # Minimal 1x1 white JPEG
            return base64.b64decode(
                "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////"
                "////////////////////////////////////////////////////////////////"
                "2wBDAf//////////////////////"
                "////////////////////////////////////////////////////////////////"
                "wAARCAABAAEDASIAAhEBAxEB/8QAFAABAAAAAAAAAAAAAAAAAAAACf/"
                "EABQQAAAAAAAAAAAAAAAAAAAAAP/aAAwDAQACEQMRAD8AVQP/2Q=="
            )
    
    def _print_results(self):
        """Print experiment summary."""
        print()
        print("=" * 60)
        print("EXPERIMENT RESULTS")
        print("=" * 60)
        print(f"Frames sent:           {self.frame_count}")
        print(f"Spatial scans sent:    {self.scan_count}")
        print(f"Tool calls received:   {self.tool_calls_received}")
        print(f"Audio responses:       {self.audio_responses} chunks")
        print(f"Errors:                {len(self.errors)}")
        print()
        
        if self.tool_calls_received > 0:
            print("✓✓✓ SUCCESS: THE OPTIC NERVE WORKS! ✓✓✓")
            print(f"  Gemini called report_spatial_observation {self.tool_calls_received} times")
            print(f"  Hit rate: {self.tool_calls_received}/{self.scan_count} scans")
            print()
            print("  This means:")
            print("  - Gemini CAN analyze video frames and return structured JSON")
            print("  - The backend brain CAN receive real spatial data to compute on")
            print("  - The predict-verify cognitive loop IS viable")
            print("  - Object tracking with real positions IS possible")
        elif self.scan_count > 0:
            print("✗ FAILURE: Gemini did NOT call the function")
            print(f"  Sent {self.scan_count} scan prompts but got 0 tool calls")
            if self.audio_responses > 0:
                print("  Gemini responded with AUDIO instead of function calls")
                print("  This means the function calling isn't triggering from video analysis")
            print()
            print("  Possible fixes to try:")
            print("  1. Make system prompt more explicit about ALWAYS calling the function")
            print("  2. Try behavior: NON_BLOCKING on the function declaration")
            print("  3. Test without audio modality (TEXT only) to isolate the issue")
            print("  4. Function calling degrades with audio — may need dual-session approach")
        else:
            print("  No scans were sent (experiment may have failed to connect)")
        
        # Save results
        results_path = "optic_nerve_results.json"
        with open(results_path, 'w') as f:
            json.dump({
                "experiment": "optic_nerve",
                "timestamp": datetime.now().isoformat(),
                "config": {
                    "model": MODEL,
                    "scan_interval": 5,
                    "turn_coverage": "TURN_INCLUDES_ALL_INPUT"
                },
                "metrics": {
                    "frames_sent": self.frame_count,
                    "scans_sent": self.scan_count,
                    "tool_calls_received": self.tool_calls_received,
                    "audio_responses": self.audio_responses,
                    "errors": len(self.errors)
                },
                "tool_call_results": [r for r in self.results if r["type"] == "tool_call"],
                "speech_results": [r for r in self.results if r["type"] == "speech"],
                "errors": self.errors
            }, f, indent=2)
        
        print(f"\nFull results saved to: {results_path}")


# ─── Main ─────────────────────────────────────────────────────────────

async def main():
    experiment = OpticNerveExperiment()
    
    # Run for 30 seconds, scan every 5 frames (every 5 seconds)
    # This gives us ~6 scan opportunities
    await experiment.run(duration_seconds=30, scan_interval=5)


if __name__ == "__main__":
    asyncio.run(main())
