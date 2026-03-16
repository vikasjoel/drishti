"""
ImplicitGoalEngine — Goals that emerge from the environment.
No user speech needed. Always running.
"""


class ImplicitGoalEngine:
    def compute(self, environment, path, user_state, known_objects, plugin_config):
        goals = []
        camera_mode = plugin_config.get("camera_mode", "mobile")

        if camera_mode == "mobile":
            goals = self._mobile_goals(environment, path, user_state, known_objects)
        else:
            goals = self._stationary_goals(environment, known_objects, plugin_config)

        return sorted(goals, key=lambda g: g["priority"], reverse=True)

    def _mobile_goals(self, environment, path, user_state, known_objects):
        goals = []

        # ALWAYS ACTIVE
        goals.append({
            "id": "safe_navigation", "type": "implicit",
            "priority": 0.5, "description": "Keep user safe on path",
        })

        env_type = environment.get("type", "unknown")

        # STAIRS
        if env_type == "indoor_stairs" or user_state.get("on_stairs"):
            goals.append({
                "id": "stair_navigation", "type": "implicit",
                "priority": 0.9, "description": "Guide through staircase",
            })

        # CROSSING
        if env_type == "outdoor_crossing":
            goals.append({
                "id": "crossing_navigation", "type": "implicit",
                "priority": 0.95, "description": "Navigate road crossing safely",
            })

        # CROWDED
        desc = environment.get("description", "").lower()
        if "crowd" in desc or "market" in desc or "busy" in desc:
            goals.append({
                "id": "crowd_navigation", "type": "implicit",
                "priority": 0.6, "description": "Navigate crowded space",
            })

        # PATH BLOCKED
        if not path.get("clear", True):
            goals.append({
                "id": "obstacle_avoidance", "type": "implicit",
                "priority": 0.8,
                "description": f"Path blocked by {path.get('blocked_by', 'something')}",
            })

        # HAZARDS
        for hazard in path.get("hazards", []):
            goals.append({
                "id": f"hazard_{hazard}", "type": "implicit",
                "priority": 0.7, "description": f"Floor hazard: {hazard}",
            })

        # USER STOPPED
        if user_state.get("just_stopped") and user_state.get("was_walking"):
            goals.append({
                "id": "orientation_assist", "type": "implicit",
                "priority": 0.6, "description": "User stopped — may need help",
            })

        # VEHICLE MODE
        if user_state.get("movement") == "vehicle":
            goals.append({
                "id": "vehicle_mode", "type": "implicit",
                "priority": 0.3, "description": "In vehicle — macro awareness only",
            })

        # SENSOR: entering stairs (before cognitive confirms)
        if user_state.get("entering_stairs"):
            goals.append({
                "id": "stair_entry_sensor", "type": "implicit",
                "priority": 0.95, "description": "Sensors detect stairs",
            })

        return goals

    def _stationary_goals(self, environment, known_objects, plugin_config):
        goals = []
        plugin_name = plugin_config.get("name", "security")

        if plugin_name == "baby_monitor":
            goals.append({
                "id": "monitor_baby", "type": "implicit",
                "priority": 0.6, "description": "Monitor baby safety",
            })
            for obj in known_objects:
                if obj.get("what", "").lower() in ("baby", "child", "infant"):
                    if obj.get("navigation_relevant"):
                        goals.append({
                            "id": "baby_boundary", "type": "implicit",
                            "priority": 0.9, "description": "Baby near boundary",
                        })

        elif plugin_name == "elderly_care":
            goals.append({
                "id": "monitor_elderly", "type": "implicit",
                "priority": 0.5, "description": "Monitor elderly safety",
            })
            has_person = any(o.get("what", "").lower() in ("person", "man", "woman")
                            for o in known_objects)
            if not has_person:
                goals.append({
                    "id": "person_missing", "type": "implicit",
                    "priority": 0.7, "description": "No person visible",
                })

        elif plugin_name == "security":
            goals.append({
                "id": "perimeter_watch", "type": "implicit",
                "priority": 0.5, "description": "Monitor for entry",
            })
            for obj in known_objects:
                if obj.get("what", "").lower() == "person" and obj.get("navigation_relevant"):
                    goals.append({
                        "id": "intruder_alert", "type": "implicit",
                        "priority": 0.9,
                        "description": f"Person detected: {obj.get('where', 'in frame')}",
                    })

        return goals
