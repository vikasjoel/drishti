"""
Perception Director — generates focused questions for Gemini
about what to look for in each frame, based on current world state.
"""

from backend.world_model import WorldModel


class PerceptionDirector:
    def generate_query(self, world_model: WorldModel) -> str:
        """
        Build a directed perception prompt that tells Gemini
        exactly what to look for and report on in the current frame.
        """
        parts = []
        frame = world_model.frame_count

        # Track existing objects
        if world_model.active_objects:
            parts.append("TRACK these objects from previous frames:")
            for obj in world_model.active_objects:
                parts.append(
                    f"  - {obj.description} was at {obj.clock_position}, "
                    f"{obj.distance_category}. Is it still there? Has it moved?"
                )

        # Look for returning objects
        if world_model.out_of_view:
            recent_lost = world_model.out_of_view[-2:]
            descs = [o.description for o in recent_lost]
            parts.append(f"LOOK FOR objects that left view recently: {', '.join(descs)}")

        # General spatial scan
        parts.append(
            "SCAN the frame and report:\n"
            "  1. Any NEW objects not listed above (people, vehicles, obstacles, furniture)\n"
            "  2. Floor level changes (steps, curbs, ramps)\n"
            "  3. Visible text (signs, labels, displays)\n"
            "  4. Path ahead — is it clear or obstructed?\n"
            "  5. Overall environment type and lighting"
        )

        # Validate predictions
        approaching = [o for o in world_model.active_objects if o.size_trend > 0.5]
        if approaching:
            names = [o.description for o in approaching]
            parts.append(
                f"URGENT CHECK: {', '.join(names)} were approaching — "
                f"confirm current position and speed."
            )

        return "\n".join(parts)
