"""
Unified goal management. Implicit + explicit goals in ONE priority list.
No separate modes. No mode switches.
"""
import time
import logging

from backend.implicit_goals import ImplicitGoalEngine

logger = logging.getLogger("drishti.goals")


class GoalSystem:
    def __init__(self, plugin_config):
        self.implicit_engine = ImplicitGoalEngine()
        self.implicit_goals = []
        self.explicit_goals = []
        self.mentioned_goals = {}
        self.plugin_config = plugin_config

    def update(self, environment, path, user_state, known_objects):
        """Recompute implicit goals from current situation."""
        self.implicit_goals = self.implicit_engine.compute(
            environment, path, user_state, known_objects, self.plugin_config
        )
        self._expire_explicit()

    def get_active_goals(self):
        all_goals = self.implicit_goals + [
            g for g in self.explicit_goals if not g.get("achieved")
        ]
        return sorted(all_goals, key=lambda g: g["priority"], reverse=True)

    def get_top_goal(self):
        active = self.get_active_goals()
        return active[0] if active else None

    def add_explicit_goal(self, goal):
        for existing in self.explicit_goals:
            if (existing.get("target") and goal.get("target") and
                    existing["target"].lower() == goal["target"].lower()):
                existing["last_referenced"] = time.time()
                return

        self.explicit_goals.append({
            **goal,
            "id": f"explicit_{int(time.time() * 1000) % 100000}",
            "type": "explicit",
            "priority": goal.get("priority", 0.7),
            "created": time.time(),
            "last_referenced": time.time(),
            "achieved": False,
        })
        logger.info(f"Explicit goal added: {goal.get('target', '?')}")

    def check_goal_match(self, cognitive_result):
        matches = []
        if not cognitive_result:
            return matches

        for goal in self.explicit_goals:
            if goal.get("achieved") or not goal.get("target"):
                continue
            target = goal["target"].lower()

            for obj in cognitive_result.get("objects", []):
                if target in obj.get("what", "").lower():
                    matches.append({"goal": goal, "evidence": obj, "priority": goal["priority"] + 0.2})

            for text in cognitive_result.get("text_signs", []):
                if target in text.lower():
                    matches.append({"goal": goal, "evidence": {"sign": text}, "priority": goal["priority"] + 0.3})

        if cognitive_result.get("path_ahead", {}).get("safety_alert"):
            matches.append({
                "goal": {"id": "safety", "type": "implicit"},
                "evidence": {"alert": cognitive_result["path_ahead"]["safety_alert"]},
                "priority": 1.0,
            })

        return sorted(matches, key=lambda m: m["priority"], reverse=True)

    def should_speak_about(self, goal_id):
        last = self.mentioned_goals.get(goal_id, 0)
        cooldown = 20 if "explicit" in str(goal_id) else 15
        return (time.time() - last) > cooldown

    def mark_mentioned(self, goal_id):
        self.mentioned_goals[goal_id] = time.time()

    def mark_achieved(self, goal_id):
        for g in self.explicit_goals:
            if g.get("id") == goal_id:
                g["achieved"] = True
                logger.info(f"Goal achieved: {g.get('target', '?')}")

    def _expire_explicit(self):
        cutoff = time.time() - 300
        self.explicit_goals = [
            g for g in self.explicit_goals
            if g.get("achieved") or g.get("last_referenced", 0) > cutoff
        ]

    def get_context_for_memory(self):
        active = self.get_active_goals()
        parts = []
        for g in active[:3]:
            if g["type"] == "explicit":
                parts.append(f"Looking for: {g.get('target', '?')}")
            elif g["priority"] > 0.7:
                parts.append(f"Focus: {g['description']}")
        return "; ".join(parts) if parts else ""
