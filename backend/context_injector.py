"""
Context Injector — converts world model state + changes into text
injected into Gemini's context window every 5 frames.

This is the core feedback loop: it tells Gemini what WE know about the world,
what changed, and whether to speak proactively.
"""

from backend.world_model import WorldModel
from backend.perception_director import PerceptionDirector


class ContextInjector:
    def __init__(self):
        self.perception_director = PerceptionDirector()
        self._injection_count = 0

    def generate(self, world_model: WorldModel) -> str:
        """Generate a spatial state update for injection into Gemini context."""
        self._injection_count += 1
        snapshot = world_model.get_snapshot()
        changes = world_model.get_changes_since_last()
        perception_query = self.perception_director.generate_query(world_model)

        parts = []

        # Header
        parts.append(
            f"=== DRISHTI SPATIAL STATE UPDATE (frame {snapshot['frame']}, "
            f"{snapshot['session_seconds']}s into session) ==="
        )

        # Current tracked objects
        if snapshot["active_objects"]:
            parts.append(f"\nTRACKING {len(snapshot['active_objects'])} objects:")
            for obj_str in snapshot["active_objects"]:
                parts.append(f"  * {obj_str}")
        else:
            parts.append("\nNo objects currently tracked.")

        # Remembered objects (out of view)
        if snapshot["out_of_view"]:
            parts.append(f"\nREMEMBERED (out of view):")
            for obj_str in snapshot["out_of_view"]:
                parts.append(f"  * {obj_str}")

        # Environment
        if snapshot["environment"]:
            parts.append(f"\nENVIRONMENT: {'; '.join(snapshot['environment'])}")

        # Landmarks
        if snapshot["landmarks"]:
            parts.append(f"\nLANDMARKS: {', '.join(snapshot['landmarks'])}")

        # Changes since last injection — this drives proactive speech
        parts.append("\n--- CHANGES SINCE LAST UPDATE ---")

        speak_proactively = False
        proactive_reasons = []

        if changes["new_objects"]:
            parts.append(f"NEW objects appeared: {'; '.join(changes['new_objects'])}")
            speak_proactively = True
            proactive_reasons.append("new objects entered the scene")

        if changes["lost_objects"]:
            parts.append(f"LOST from view: {'; '.join(changes['lost_objects'])}")

        if changes["approaching"]:
            parts.append(f"APPROACHING (getting closer): {'; '.join(changes['approaching'])}")
            speak_proactively = True
            proactive_reasons.append("objects are approaching the user")

        if changes["environment_changed"]:
            parts.append("ENVIRONMENT has changed (new space or conditions)")
            speak_proactively = True
            proactive_reasons.append("the environment changed")

        if not any([changes["new_objects"], changes["lost_objects"],
                    changes["approaching"], changes["environment_changed"]]):
            parts.append("No significant changes.")

        # Proactive speech directive
        parts.append("\n--- COMMUNICATION DIRECTIVE ---")
        if speak_proactively:
            reasons_str = " and ".join(proactive_reasons)
            parts.append(
                f"SPEAK NOW: {reasons_str}. "
                f"Use a brief, spatial alert format: what, clock position, distance, movement. "
                f"Keep it under 15 words for urgent items."
            )
        else:
            parts.append(
                "STAY SILENT unless the user speaks to you. "
                "Nothing has changed enough to warrant proactive speech."
            )

        # Perception focus for next frames
        parts.append(f"\n--- PERCEPTION FOCUS (next frames) ---\n{perception_query}")

        parts.append("\n=== END STATE UPDATE ===")

        return "\n".join(parts)
