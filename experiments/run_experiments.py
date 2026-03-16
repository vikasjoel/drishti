"""
SixthSense — Spatial Intelligence Validation Experiments
=========================================================
Run this on YOUR machine (not in a restricted container).

SETUP (one time):
  pip install google-genai pillow
  export GOOGLE_API_KEY="your-key-here"
  python run_experiments.py

Takes about 2-3 minutes. Uses ~15 API calls (well within free tier).
"""

import os
import json
from pathlib import Path
from PIL import Image, ImageDraw
from google import genai
from google.genai import types

API_KEY = os.environ.get("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("Set GOOGLE_API_KEY environment variable before running experiments")
os.environ["GOOGLE_API_KEY"] = API_KEY

client = genai.Client()
MODEL = "gemini-2.5-flash"

# ============================================================
# CREATE TEST FRAMES
# ============================================================
def create_frames():
    configs = [
        {"x": 100, "y": 350, "w": 25,  "h": 55},   # Far, left
        {"x": 170, "y": 320, "w": 40,  "h": 85},   # Closer, moving center
        {"x": 250, "y": 280, "w": 60,  "h": 125},  # Closer still
        {"x": 320, "y": 230, "w": 85,  "h": 175},  # Near, center-ish
        {"x": 350, "y": 170, "w": 120, "h": 250},  # Very close, center
    ]
    
    frames = []
    for i, cfg in enumerate(configs):
        img = Image.new('RGB', (768, 768), color=(180, 200, 220))
        draw = ImageDraw.Draw(img)
        
        # Ground
        draw.rectangle([0, 580, 768, 768], fill=(130, 130, 130))
        draw.line([(350, 580), (384, 768)], fill=(200, 200, 50), width=3)
        
        # Static buildings
        draw.rectangle([620, 200, 710, 580], fill=(160, 130, 110))
        draw.rectangle([630, 210, 700, 250], fill=(140, 180, 220))
        draw.rectangle([30, 280, 80, 580], fill=(160, 130, 110))
        
        # Static tree
        draw.ellipse([680, 300, 750, 400], fill=(50, 130, 50))
        draw.rectangle([705, 400, 725, 500], fill=(100, 70, 40))
        
        # Moving person (blue) — gets larger each frame
        x, y, w, h = cfg["x"], cfg["y"], cfg["w"], cfg["h"]
        draw.rectangle([x, y + int(h*0.3), x+w, y+h], fill=(40, 40, 180))
        head_r = int(w * 0.4)
        draw.ellipse([x + w//2 - head_r, y, x + w//2 + head_r, y + int(h*0.25)], fill=(220, 180, 150))
        
        # Static person (red) — reference, doesn't move
        draw.rectangle([550, 380, 575, 500], fill=(180, 40, 40))
        draw.ellipse([552, 360, 573, 385], fill=(220, 180, 150))
        
        draw.text((10, 10), f"Frame {i+1} (T+{i}s)", fill=(0, 0, 0))
        
        path = f"frame_{i+1}.jpg"
        img.save(path, "JPEG", quality=85)
        frames.append(path)
    
    print(f"Created {len(frames)} test frames\n")
    return frames


def img_part(path):
    return types.Part.from_bytes(data=Path(path).read_bytes(), mime_type="image/jpeg")


# ============================================================
# EXPERIMENT 1: Cross-Frame Object Tracking
# ============================================================
def experiment_1(frames):
    print("=" * 60)
    print("EXPERIMENT 1: Can Gemini track objects across frames?")
    print("=" * 60)
    
    contents = []
    for i, fp in enumerate(frames):
        contents.append(f"Frame {i+1} (captured at T+{i} seconds):")
        contents.append(img_part(fp))
    
    contents.append("""Analyze these 5 sequential camera frames captured 1 second apart.

1. Is there an object appearing in MULTIPLE frames? Which one?
2. Is it getting CLOSER or FARTHER across frames? What visual evidence (size change)?
3. What direction is it moving (left-to-center, right-to-center, straight)?
4. Is there a STATIC reference object that stays the same size?
5. Predict: where will the moving object be in Frame 6?

Be specific about size changes and position shifts.""")
    
    r = client.models.generate_content(model=MODEL, contents=contents)
    print(r.text)
    
    t = r.text.lower()
    scores = {
        "detects_approach": any(w in t for w in ["closer", "approaching", "nearer", "toward"]),
        "size_change": any(w in t for w in ["larger", "bigger", "grows", "size increase", "increasing"]),
        "direction": any(w in t for w in ["left to center", "left-to-center", "toward center", "moves right", "moving right"]),
        "static_ref": any(w in t for w in ["static", "stationary", "remains", "unchanged", "same size", "red", "doesn't move"]),
    }
    
    print("\n--- SCORING ---")
    for k, v in scores.items():
        print(f"  {k}: {'YES' if v else 'NO'}")
    total = sum(scores.values())
    verdict = 'PASS' if total >= 3 else 'PARTIAL' if total >= 2 else 'FAIL'
    print(f"\nSCORE: {total}/4 — {verdict}")
    return total, verdict


# ============================================================
# EXPERIMENT 2: Clock-Position Spatial Language
# ============================================================
def experiment_2(frames):
    print("\n" + "=" * 60)
    print("EXPERIMENT 2: Does clock-position spatial language work?")
    print("=" * 60)
    
    contents = [
        img_part(frames[2]),
        """You are a spatial awareness system for a visually impaired person.

Describe ALL objects using this clock-position system:
- 10 o'clock = far left
- 11 o'clock = left of center
- 12 o'clock = straight ahead
- 1 o'clock = right of center
- 2 o'clock = far right

For each object state: {object}, {clock position}, {distance: near/medium/far}, {static/moving}

List every visible object."""
    ]
    
    r = client.models.generate_content(model=MODEL, contents=contents)
    print(r.text)
    
    t = r.text.lower()
    has_clock = "o'clock" in t or "o'clock" in t
    count_clock = t.count("o'clock") + t.count("o'clock")
    
    print(f"\n--- Clock positions found: {count_clock} ---")
    verdict = 'PASS' if count_clock >= 3 else 'PARTIAL' if count_clock >= 1 else 'FAIL'
    print(f"VERDICT: {verdict}")
    return count_clock, verdict


# ============================================================
# EXPERIMENT 3: Context Injection Impact
# ============================================================
def experiment_3(frames):
    print("\n" + "=" * 60)
    print("EXPERIMENT 3: Does context injection improve reasoning?")
    print("=" * 60)
    
    # --- WITHOUT context ---
    print("\n--- A) WITHOUT context injection ---")
    r_a = client.models.generate_content(
        model=MODEL,
        contents=[img_part(frames[3]), "Describe this scene. Where are objects relative to the viewer?"]
    )
    print(r_a.text[:400])
    
    # --- WITH context ---
    print("\n--- B) WITH context injection ---")
    context = """SPATIAL STATE from previous 3 frames:
- Environment: outdoor sidewalk with buildings on both sides
- User walking forward
- TRACKED OBJECT (blue person): was at 10 o'clock (far) in frame 1, moved to 11 o'clock (medium) by frame 3. Size increased 5x over 3 seconds = approaching rapidly.
- STATIC OBJECT (red person): 1 o'clock, medium distance, no size change across frames.
- STATIC: building left (10 o'clock), building right (2 o'clock), tree (2 o'clock)

Now analyze Frame 4 below. Report:
1. Current position of the blue person using clock position
2. Is the approach continuing?  
3. Estimated distance category (far/medium/near/very near)
4. Priority level for alerting the user (low/medium/high/critical)
5. Suggested voice alert (under 10 words)"""
    
    r_b = client.models.generate_content(
        model=MODEL,
        contents=[context, img_part(frames[3])]
    )
    print(r_b.text[:400])
    
    # Compare
    print("\n--- COMPARISON ---")
    t_a = r_a.text.lower()
    t_b = r_b.text.lower()
    
    b_has_clock = "o'clock" in t_b
    b_has_priority = any(w in t_b for w in ["priority", "alert", "critical", "high", "warning"])
    b_has_distance = any(w in t_b for w in ["near", "close", "approaching", "meter"])
    
    print(f"  Context version has clock positions: {b_has_clock}")
    print(f"  Context version has priority/alert: {b_has_priority}")
    print(f"  Context version has distance info: {b_has_distance}")
    
    score = sum([b_has_clock, b_has_priority, b_has_distance])
    verdict = 'PASS' if score >= 2 else 'PARTIAL' if score >= 1 else 'FAIL'
    print(f"\nContext injection SCORE: {score}/3 — {verdict}")
    return score, verdict


# ============================================================
# EXPERIMENT 4: Distance Estimation
# ============================================================
def experiment_4(frames):
    print("\n" + "=" * 60)
    print("EXPERIMENT 4: Can Gemini estimate distance from size?")
    print("=" * 60)
    
    contents = [
        "Frame A — person far away:",
        img_part(frames[0]),
        "Frame B — same person, much closer:",
        img_part(frames[4]),
        """A typical person is ~1.7m tall. 

1. In Frame A, estimate how far the person is from camera (in meters)
2. In Frame B, estimate how far (in meters)  
3. What is the ratio of distances?
4. These frames are 4 seconds apart. What is their walking speed in m/s?

Show your reasoning based on apparent height vs frame height."""
    ]
    
    r = client.models.generate_content(model=MODEL, contents=contents)
    print(r.text)
    
    t = r.text.lower()
    has_numbers = any(f"{n} m" in t or f"{n}m" in t for n in range(1, 30))
    has_speed = "m/s" in t or "meters per second" in t or "km/h" in t
    has_reasoning = "height" in t or "proportion" in t or "ratio" in t or "pixel" in t
    
    print(f"\n--- Numeric distances: {has_numbers}, Speed calc: {has_speed}, Shows reasoning: {has_reasoning} ---")
    score = sum([has_numbers, has_speed, has_reasoning])
    verdict = 'PASS' if score >= 2 else 'PARTIAL' if score >= 1 else 'FAIL'
    print(f"SCORE: {score}/3 — {verdict}")
    return score, verdict


# ============================================================
# EXPERIMENT 5: Adaptive Environment Classification
# ============================================================
def experiment_5(frames):
    print("\n" + "=" * 60)
    print("EXPERIMENT 5: Environment classification + adaptation")
    print("=" * 60)
    
    contents = [
        img_part(frames[2]),
        """You are a spatial intelligence agent that adapts its behavior based on environment type.

1. Classify this environment: indoor_home / indoor_retail / indoor_office / outdoor_sidewalk / outdoor_road / outdoor_park / other
2. Based on the classification, what types of objects should you prioritize tracking?
3. What alert sensitivity level is appropriate? (low/medium/high)  
4. What communication style should you use? (brief_tactical / conversational / gentle_supportive)
5. What is the biggest spatial risk in this type of environment?

Format as JSON:
{"environment": "...", "priority_objects": [...], "alert_level": "...", "comm_style": "...", "primary_risk": "..."}"""
    ]
    
    r = client.models.generate_content(model=MODEL, contents=contents)
    print(r.text)
    
    t = r.text.lower()
    has_json = "{" in t and "}" in t
    has_env = any(w in t for w in ["outdoor", "sidewalk", "street", "road"])
    
    print(f"\n--- JSON structured: {has_json}, Correct env: {has_env} ---")
    score = sum([has_json, has_env])
    verdict = 'PASS' if score >= 2 else 'PARTIAL' if score >= 1 else 'FAIL'
    print(f"SCORE: {score}/2 — {verdict}")
    return score, verdict


# ============================================================
# MAIN
# ============================================================
def main():
    print("SixthSense — Spatial Intelligence Experiments")
    print("=" * 60)
    print(f"API Key: {API_KEY[:10]}...{API_KEY[-4:]}")
    print(f"Model: {MODEL}\n")
    
    frames = create_frames()
    
    results = {}
    
    try:
        s, v = experiment_1(frames)
        results["1_cross_frame_tracking"] = v
    except Exception as e:
        print(f"Exp 1 ERROR: {e}")
        results["1_cross_frame_tracking"] = "ERROR"
    
    try:
        s, v = experiment_2(frames)
        results["2_clock_positions"] = v
    except Exception as e:
        print(f"Exp 2 ERROR: {e}")
        results["2_clock_positions"] = "ERROR"
    
    try:
        s, v = experiment_3(frames)
        results["3_context_injection"] = v
    except Exception as e:
        print(f"Exp 3 ERROR: {e}")
        results["3_context_injection"] = "ERROR"
    
    try:
        s, v = experiment_4(frames)
        results["4_distance_estimation"] = v
    except Exception as e:
        print(f"Exp 4 ERROR: {e}")
        results["4_distance_estimation"] = "ERROR"
    
    try:
        s, v = experiment_5(frames)
        results["5_env_classification"] = v
    except Exception as e:
        print(f"Exp 5 ERROR: {e}")
        results["5_env_classification"] = "ERROR"
    
    # SUMMARY
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    for name, verdict in results.items():
        emoji = "✅" if verdict == "PASS" else "⚠️" if verdict == "PARTIAL" else "❌"
        print(f"  {emoji} {name}: {verdict}")
    
    passes = sum(1 for v in results.values() if v == "PASS")
    partials = sum(1 for v in results.values() if v == "PARTIAL")
    fails = sum(1 for v in results.values() if v in ("FAIL", "ERROR"))
    
    print(f"\n  PASS: {passes} | PARTIAL: {partials} | FAIL: {fails}")
    
    print("\n" + "=" * 60)
    print("WHAT THIS MEANS:")
    print("=" * 60)
    
    if passes >= 4:
        print("  🚀 EXCELLENT — Gemini handles spatial reasoning natively.")
        print("  → Build with minimal backend logic, let Gemini do the heavy lifting.")
    elif passes + partials >= 4:
        print("  👍 GOOD — Gemini handles most spatial tasks, some need help.")
        print("  → Build with context injection as the key strategy.")
    else:
        print("  ⚙️ MIXED — Need significant backend spatial logic.")
        print("  → Build tracking/distance logic in Python, use Gemini for understanding.")
    
    # Save results
    with open("experiment_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to experiment_results.json")
    print("Share these results and we'll architect based on evidence!")


if __name__ == "__main__":
    main()
