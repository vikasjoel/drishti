"""
Drishti v4.2 World Model — the CONDUCTOR with temporal validation.
Decides WHEN Gemini speaks, not WHAT it says.
Every perception result is validated against user movement before firing.
"""
import time
import logging

from backend.goal_system import GoalSystem
from backend.speech_processing import SpeechEventDetector, ConversationInterpreter
from backend.temporal_validator import TemporalValidator
from backend.logger import log_event

logger = logging.getLogger("drishti.world_model")


class WorldModel:
    """
    The brain of Drishti v4.2. Absorbs sensor data, cognitive results,
    CV signals, and speech events. Outputs temporally-validated nudge decisions.
    """

    # Priority levels (P1 = highest)
    P1_CV_EMERGENCY = 1.0
    P2_SAFETY_ALERT = 0.9
    P3_APPROACHING_FAST = 0.8
    P4_ENVIRONMENT_CHANGE = 0.7
    P5_GOAL_MATCH = 0.65
    P6_NEW_OBSTACLE = 0.6
    P7_ORIENTATION_HELP = 0.5
    P8_PROACTIVE_INFO = 0.4
    P9_MEMORY_AUGMENT = 0.3

    VEHICLE_LABELS = {"bicycle", "car", "motorcycle", "vehicle", "bus", "truck"}

    def __init__(self, plugin_config):
        self.plugin_config = plugin_config

        # Dimensions
        self.vigilance = plugin_config.get("vigilance_baseline", 0.3)
        self.verbosity = plugin_config.get("verbosity_baseline", 0.2)
        self.urgency = 0.0
        self.spatial_confidence = 0.5

        # State
        self.frame_count = 0
        self.session_start = time.time()
        self.last_nudge_time = 0
        self.last_nudge_text = ""
        self.last_memory_injection = 0

        # Environment tracking
        self.environment = {}
        self._prev_env_type = None
        self._environment_just_changed = False
        self.path_ahead = {}
        self.known_objects = []
        self.text_signs = []
        self.transition = "same"

        # Sensor state
        self.user_state = {
            "movement": "stationary",
            "heading": 0,
            "step_count": 0,
            "distance_walked": 0,
            "on_stairs": False,
            "speed": 0,
        }

        # CV state
        self.cv_emergency = False
        self.cv_emergency_text = ""
        self.cv_tracks = []

        # Speech processing
        self.speech_detector = SpeechEventDetector()
        self.interpreter = ConversationInterpreter()

        # Goals
        self.goals = GoalSystem(plugin_config)

        # Behavioral overrides
        self.verbosity_override = None
        self.verbosity_override_until = 0

        # Correction tracking
        self.pending_corrections = []
        self.last_suggested_speech = None
        self.last_navigation_action = None

        # CV fast-path state
        self._pending_obstacle = None
        self._pending_emergency = None
        self.known_env_labels = set()  # ACCUMULATED from cognitive (not overwritten)
        self.landmarks = []

        # Temporal validation (v4.2)
        self.temporal = TemporalValidator()
        self._last_cognitive_snapshot = None
        self._last_cognitive_heading = 0
        self._last_cognitive_time = 0
        self._last_validation = None

        # Dedup — cooldown tracking per reason
        self._reason_last_fired = {}
        self._last_nudge_hash = None

    # --- Input absorbers ---

    def absorb_sensors(self, sensor_state):
        """Absorb processed sensor data from SensorProcessor."""
        if not sensor_state:
            return
        self.user_state.update(sensor_state)

    def absorb_cognitive(self, cognitive_result):
        """Absorb Gemini generateContent scene analysis."""
        if not cognitive_result:
            return

        # Store frame snapshot for temporal validation
        self._last_cognitive_snapshot = cognitive_result.get("frame_snapshot")
        if self._last_cognitive_snapshot:
            self._last_cognitive_heading = self._last_cognitive_snapshot.get("heading", 0)
        self._last_cognitive_time = time.time()

        new_env = cognitive_result.get("environment", {})
        new_env_type = new_env.get("type", "unknown")

        # Python-side transition detection
        if (self._prev_env_type is not None
                and new_env_type != "unknown"
                and new_env_type != self._prev_env_type):
            self._environment_just_changed = True
            self.transition = "entering_new"
            log_event("world_model", "transition_detected", details={
                "from": self._prev_env_type, "to": new_env_type,
            })
        else:
            self._environment_just_changed = False
            self.transition = "same"

        if new_env_type != "unknown":
            self._prev_env_type = new_env_type

        self.environment = new_env
        self.path_ahead = cognitive_result.get("path_ahead", {})
        if self.path_ahead.get("safety_alert"):
            self.path_ahead["_safety_alert_time"] = time.time()
        self.text_signs = cognitive_result.get("text_signs", [])
        self.last_suggested_speech = cognitive_result.get("suggested_speech")
        self.last_navigation_action = cognitive_result.get("navigation_action")

        # Update known objects
        new_objects = cognitive_result.get("objects", [])
        nav_relevant = [o for o in new_objects if o.get("navigation_relevant")]
        self.known_objects = nav_relevant

        # ACCUMULATE known_env_labels (union, not overwrite)
        new_labels = {
            o.get("what", "").lower() for o in new_objects
            if not o.get("navigation_relevant")
        }
        self.known_env_labels = self.known_env_labels | new_labels
        # Trim to prevent unbounded growth
        if len(self.known_env_labels) > 50:
            self.known_env_labels = set(list(self.known_env_labels)[-50:])

        # Update goals
        self.goals.update(
            self.environment, self.path_ahead,
            self.user_state, self.known_objects
        )
        matches = self.goals.check_goal_match(cognitive_result)
        for match in matches:
            goal = match["goal"]
            if goal.get("type") == "explicit":
                self.goals.mark_achieved(goal["id"])

        # Spatial confidence from cognitive freshness
        env_type = self.environment.get("type", "unknown")
        self.spatial_confidence = 0.3 if env_type == "unknown" else 0.7

        log_event("world_model", "absorb_cognitive", details={
            "environment": env_type,
            "path_clear": self.path_ahead.get("clear"),
            "objects": len(new_objects),
            "nav_relevant": len(nav_relevant),
            "transition": self.transition,
        })

    def absorb_cv(self, cv_result, plugin_config):
        """Cloud Vision -> vehicle emergency + obstacle detection + OCR."""
        if not cv_result:
            self.cv_emergency = False
            return

        frame_snapshot = cv_result.get("frame_snapshot")
        self.cv_emergency = False
        self.cv_emergency_text = ""
        tracks = []

        for obj in cv_result.get("objects", []):
            label = obj.get("label", "obstacle").lower()
            area = obj.get("area_pct", 0)
            cx = obj.get("center_x", 0.5)
            in_center = 0.30 < cx < 0.70
            tracks.append({"label": label, "area_pct": area})

            # Always skip "person" on mobile camera
            if plugin_config.get("camera_mode") == "mobile" and label == "person":
                continue

            # TIER 1: Vehicle emergency
            if label in self.VEHICLE_LABELS and in_center and area > 5:
                self._pending_emergency = {
                    "label": label, "area_pct": area,
                    "frame_snapshot": frame_snapshot,
                }
                self.cv_emergency = True
                self.cv_emergency_text = f"{label} very close"
                logger.warning(f"CV VEHICLE: {label} area={area:.1f}%")
                break

            # TIER 2: Large obstacle in center path
            if area > 12 and in_center and label not in self.known_env_labels:
                self._pending_obstacle = {
                    "label": label, "area_pct": area,
                    "frame_snapshot": frame_snapshot,
                }
                logger.info(f"CV OBSTACLE: {label} area={area:.1f}%")

        # TIER 3: OCR landmarks
        for text in cv_result.get("text", []):
            if text and len(text) > 2:
                existing = {l["text"] for l in self.landmarks}
                if text not in existing:
                    self.landmarks.append({
                        "text": text, "frame": self.frame_count,
                        "environment": self.environment.get("type", "unknown"),
                    })
        self.landmarks = self.landmarks[-20:]
        self.cv_tracks = tracks

    # --- Transcript handlers ---

    def on_input_transcript(self, text):
        self.speech_detector.on_input_transcript(text)

    def on_output_transcript(self, text):
        self.speech_detector.on_output_transcript(text)

    def on_turn_complete(self):
        exchange = self.speech_detector.on_turn_complete()
        if not exchange:
            return

        result = self.interpreter.interpret(
            exchange,
            world_model_landmarks=self.text_signs
        )

        if result.get("goal"):
            self.goals.add_explicit_goal(result["goal"])
            logger.info(f"Goal from speech: {result['goal'].get('target')}")

        if result.get("behavioral"):
            cmd = result["behavioral"]
            if cmd["command"] == "reduce_verbosity":
                self.verbosity_override = cmd["value"]
                self.verbosity_override_until = time.time() + cmd.get("duration", 120)
            elif cmd["command"] == "increase_verbosity":
                self.verbosity_override = cmd["value"]
                self.verbosity_override_until = time.time() + cmd.get("duration", 30)

    # --- Decision engine ---

    def decide(self):
        """
        Editorial decision with temporal validation.
        Every perception-based nudge is checked against user movement.
        Returns a nudge dict or None (silence).
        """
        self.frame_count += 1
        now = time.time()
        self._last_validation = None  # Reset per-frame
        self._compute_dimensions()

        # Check speech timeout
        timeout_exchange = self.speech_detector.check_timeout()
        if timeout_exchange:
            result = self.interpreter.interpret(timeout_exchange)
            if result.get("goal"):
                self.goals.add_explicit_goal(result["goal"])

        # Cooldown: shorter for urgent, imminent bypasses entirely
        since_nudge = now - self.last_nudge_time if self.last_nudge_time else 999
        min_cooldown = max(3.0, 6.0 - self.urgency * 3.0)
        cooldown_active = since_nudge < min_cooldown

        # Imminent obstacles bypass cooldown
        imminent_bypass = (self._last_validation
                          and self._last_validation.get("status") == "imminent")

        if cooldown_active and not imminent_bypass:
            return None

        # ==========================================
        # P1: CV VEHICLE EMERGENCY (temporal validated)
        # ==========================================
        if self._pending_emergency:
            emg = self._pending_emergency
            self._pending_emergency = None

            validation = self.temporal.validate({
                "frame_snapshot": emg.get("frame_snapshot"),
                "distance_estimate": self.temporal.estimate_distance_from_cv(
                    emg.get("area_pct", 15)),
            }, self.user_state)

            if validation["status"] != "stale":
                log_event("world_model", "temporal_valid", details={
                    "priority": "P1_vehicle", "status": validation["status"],
                    "reason": validation["reason"],
                })
                return self._emit_nudge(
                    priority=self.P1_CV_EMERGENCY,
                    text=f"[URGENT] {emg.get('label', 'vehicle')} ahead!",
                    end_of_turn=True,
                    reason="cv_emergency"
                )
            else:
                log_event("world_model", "temporal_stale", details={
                    "priority": "P1_vehicle", "reason": validation["reason"],
                })

        # ==========================================
        # P1.5: CV FAST OBSTACLE (temporal validated)
        # ==========================================
        if self._pending_obstacle:
            obs = self._pending_obstacle
            self._pending_obstacle = None

            validation = self.temporal.validate({
                "frame_snapshot": obs.get("frame_snapshot"),
                "distance_estimate": self.temporal.estimate_distance_from_cv(
                    obs.get("area_pct", 12)),
            }, self.user_state)

            self._last_validation = validation

            if validation["status"] == "stale":
                log_event("world_model", "temporal_stale", details={
                    "priority": "P2_obstacle", "label": obs.get("label"),
                    "reason": validation["reason"],
                })
            elif validation["status"] == "imminent":
                remaining = validation.get("remaining_distance", 1)
                steps = max(1, round(remaining / 0.7))
                log_event("world_model", "temporal_imminent", details={
                    "priority": "P2_obstacle", "label": obs.get("label"),
                    "remaining_m": remaining, "reason": validation["reason"],
                })
                return self._emit_nudge(
                    priority=self.P2_SAFETY_ALERT,
                    text=f"[URGENT] Stop! {obs.get('label', 'obstacle')} {steps} step ahead!",
                    end_of_turn=True,
                    reason="cv_obstacle"
                )
            elif self._fresh("cv_obstacle", 8):
                remaining = validation.get("remaining_distance", 2)
                steps = max(1, round(remaining / 0.7))
                log_event("world_model", "temporal_valid", details={
                    "priority": "P2_obstacle", "label": obs.get("label"),
                    "remaining_m": remaining, "reason": validation["reason"],
                })
                return self._emit_nudge(
                    priority=self.P6_NEW_OBSTACLE,
                    text=f"[Brief] {obs.get('label', 'obstacle')} about {steps} steps ahead.",
                    end_of_turn=True,
                    reason="cv_obstacle"
                )

        # ==========================================
        # P2: Safety alert from cognitive (temporal validated)
        # ==========================================
        safety = self.path_ahead.get("safety_alert")
        if safety:
            alert_age = now - self.path_ahead.get("_safety_alert_time", 0)
            if alert_age < 15:
                validation = self.temporal.validate({
                    "frame_snapshot": self._last_cognitive_snapshot,
                    "distance_estimate": self.temporal.estimate_distance_from_text(safety),
                }, self.user_state)

                if validation["status"] != "stale":
                    return self._emit_nudge(
                        priority=self.P2_SAFETY_ALERT,
                        text=f"SAFETY: {safety}",
                        end_of_turn=True,
                        reason="safety_alert"
                    )
                else:
                    log_event("world_model", "temporal_stale", details={
                        "priority": "P2_safety", "reason": validation["reason"],
                    })
                    self.path_ahead["safety_alert"] = None

        # P3: Fast-approaching object
        for obj in self.known_objects:
            if obj.get("toward_user") and obj.get("distance") in ("beside you", "1 step"):
                text = f"APPROACHING: {obj['what']} {obj.get('where', 'ahead')}, {obj['distance']}"
                return self._emit_nudge(
                    priority=self.P3_APPROACHING_FAST,
                    text=text,
                    end_of_turn=True,
                    reason="approaching_fast"
                )

        # ==========================================
        # P4: Environment transition (NOT distance-sensitive)
        # ==========================================
        if self._environment_just_changed:
            self._environment_just_changed = False
            env_desc = self.environment.get("description", "new area")
            surface = self.environment.get("surface", "")
            nav_action = self.last_navigation_action or ""
            text = f"ENVIRONMENT: {env_desc}"
            if surface and surface not in ("smooth", "paved"):
                text += f" Surface: {surface}."
            if nav_action:
                text += f" DIRECTION: {nav_action}"
                self.last_navigation_action = None
            return self._emit_nudge(
                priority=self.P4_ENVIRONMENT_CHANGE,
                text=text,
                end_of_turn=True,
                reason="environment_change"
            )

        # P5: Goal match
        top_goal = self.goals.get_top_goal()
        if top_goal and top_goal["type"] == "explicit":
            if self.goals.should_speak_about(top_goal["id"]):
                text = f"GOAL: Looking for {top_goal.get('target', '?')}. "
                for obj in self.known_objects:
                    target = top_goal.get("target", "").lower()
                    if target in obj.get("what", "").lower():
                        text += f"Found: {obj['what']} at {obj.get('where', 'nearby')}."
                        self.goals.mark_achieved(top_goal["id"])
                        self.goals.mark_mentioned(top_goal["id"])
                        return self._emit_nudge(
                            priority=self.P5_GOAL_MATCH,
                            text=text,
                            end_of_turn=True,
                            reason="goal_match"
                        )

        # ==========================================
        # P6: Path blocked from cognitive (temporal validated)
        # ==========================================
        if not self.path_ahead.get("clear", True):
            blocked_by = self.path_ahead.get("blocked_by", "obstacle")

            validation = self.temporal.validate({
                "frame_snapshot": self._last_cognitive_snapshot,
                "distance_estimate": self.temporal.estimate_distance_from_text(
                    self.last_suggested_speech or ""),
            }, self.user_state)

            self._last_validation = validation

            if validation["status"] == "stale":
                log_event("world_model", "temporal_stale", details={
                    "priority": "P6_blocked", "reason": validation["reason"],
                })
                self.path_ahead["clear"] = True  # Clear stale blockage
            elif validation["status"] == "imminent":
                remaining = validation.get("remaining_distance", 1)
                steps = max(1, round(remaining / 0.7))
                if self._fresh("path_blocked", 10):
                    return self._emit_nudge(
                        priority=self.P2_SAFETY_ALERT,
                        text=f"[URGENT] {blocked_by} {steps} step ahead! Go around.",
                        end_of_turn=True,
                        reason="obstacle"
                    )
            else:
                if self._fresh("path_blocked", 10):
                    remaining = validation.get("remaining_distance")
                    if remaining:
                        steps = max(1, round(remaining / 0.7))
                        dist_text = f" about {steps} steps ahead"
                    else:
                        dist_text = ""
                    return self._emit_nudge(
                        priority=self.P6_NEW_OBSTACLE,
                        text=f"PATH: Blocked by {blocked_by}{dist_text}.",
                        end_of_turn=True,
                        reason="obstacle"
                    )

        # P7: Orientation help (user just stopped)
        if self.user_state.get("just_stopped") and self.spatial_confidence > 0.5:
            env_type = self.environment.get("type", "unknown")
            if env_type != "unknown":
                return self._emit_nudge(
                    priority=self.P7_ORIENTATION_HELP,
                    text=f"CONTEXT: You've stopped. {self.environment.get('description', '')}",
                    end_of_turn=False,
                    reason="orientation"
                )

        # P7.5: Navigation action from cognitive (turn-by-turn directions)
        if self.last_navigation_action and self._fresh("nav_action", 6):
            text = f"NAVIGATE: {self.last_navigation_action}"
            self.last_navigation_action = None
            self.last_suggested_speech = None  # Don't also fire suggested_speech
            return self._emit_nudge(
                priority=self.P7_ORIENTATION_HELP,
                text=text,
                end_of_turn=True,
                reason="navigation_action"
            )

        # P8: Proactive info (suggested_speech from cognitive)
        since_spoke = now - self.last_nudge_time if self.last_nudge_time else 999
        if self.last_suggested_speech and since_spoke > 8:
            text = f"INFO: {self.last_suggested_speech}"
            self.last_suggested_speech = None
            return self._emit_nudge(
                priority=self.P8_PROACTIVE_INFO,
                text=text,
                end_of_turn=True,
                reason="proactive_info"
            )

        # Cold start fallback
        if self.last_nudge_time == 0 and (now - self.session_start) > 5:
            return self._emit_nudge(
                priority=self.P7_ORIENTATION_HELP,
                text="Session just started. Briefly orient the user about their immediate surroundings.",
                end_of_turn=True,
                reason="cold_start"
            )

        # P9: Memory augment (periodic context refresh)
        if (now - self.last_memory_injection) > 30:
            memory_text = self.compile_memory_injection()
            if memory_text:
                self.last_memory_injection = now
                return self._emit_nudge(
                    priority=self.P9_MEMORY_AUGMENT,
                    text=memory_text,
                    end_of_turn=False,
                    reason="memory_augment"
                )

        # LOW SPATIAL CONFIDENCE — force re-perception
        if (self.spatial_confidence < 0.2
                and self.user_state.get("movement") in ("walking", "slow_walk")
                and since_spoke > 10):
            return self._emit_nudge(
                priority=self.P8_PROACTIVE_INFO,
                text="You haven't assessed this area recently. "
                     "Briefly describe what you see ahead of the user.",
                end_of_turn=True,
                reason="confidence_low"
            )

        return None

    def _fresh(self, reason, cooldown_s):
        """Return True if this reason hasn't fired within cooldown_s seconds."""
        now = time.time()
        last = self._reason_last_fired.get(reason, 0)
        if (now - last) < cooldown_s:
            return False
        self._reason_last_fired[reason] = now
        return True

    def _emit_nudge(self, priority, text, end_of_turn, reason):
        """Create and record a nudge."""
        text_hash = hash(text)
        if text_hash == self._last_nudge_hash:
            return None
        self._last_nudge_hash = text_hash

        # Verbosity gate: suppress low-priority nudges when verbosity is low
        effective_verbosity = self.verbosity
        if self.verbosity_override is not None:
            if time.time() < self.verbosity_override_until:
                effective_verbosity = self.verbosity_override
            else:
                self.verbosity_override = None

        if priority < 0.7 and effective_verbosity < 0.2:
            return None

        self.last_nudge_time = time.time()
        self.last_nudge_text = text

        log_event("world_model", "nudge", details={
            "priority": priority,
            "reason": reason,
            "end_of_turn": end_of_turn,
            "text_preview": text[:80],
        })

        return {
            "text": text,
            "end_of_turn": end_of_turn,
            "priority": priority,
            "reason": reason,
        }

    def _compute_dimensions(self):
        """Recompute vigilance, verbosity, urgency, spatial_confidence."""
        now = time.time()

        # === SPATIAL CONFIDENCE (v4.2: temporal-aware) ===
        conf = 0.5
        cognitive_age = now - self._last_cognitive_time if self._last_cognitive_time else 999
        if cognitive_age < 3:
            conf += 0.3
        elif cognitive_age < 8:
            conf += 0.1
        elif cognitive_age > 15:
            conf -= 0.3

        if self.user_state.get("movement") == "stationary":
            conf += 0.2
        speed = self.user_state.get("speed", 0)
        if speed > 1.5:
            conf -= 0.2

        heading_delta_since_cog = abs(
            self.user_state.get("heading", 0) - self._last_cognitive_heading
        )
        if heading_delta_since_cog > 180:
            heading_delta_since_cog = 360 - heading_delta_since_cog
        if heading_delta_since_cog > 30:
            conf -= 0.3

        self.spatial_confidence = max(0.0, min(1.0, conf))

        # === VIGILANCE ===
        v = self.plugin_config.get("vigilance_baseline", 0.3)
        movement = self.user_state.get("movement", "stationary")
        if movement in ("walking", "running", "slow_walk"):
            v += 0.2
        if self.user_state.get("on_stairs"):
            v += 0.3
        if self._environment_just_changed:
            v += 0.15
        if self.spatial_confidence < 0.3:
            v += 0.3
        if speed > 0.5 and cognitive_age > 10:
            v += 0.2
        self.vigilance = max(0.0, min(1.0, v))

        # === VERBOSITY ===
        verb = self.plugin_config.get("verbosity_baseline", 0.2)
        if self._environment_just_changed:
            verb += 0.2
        if movement == "stationary" and self.user_state.get("just_stopped"):
            verb += 0.15
        if self.spatial_confidence < 0.2 and speed > 0.5:
            verb += 0.3
        self.verbosity = max(0.0, min(1.0, verb))

        # === URGENCY ===
        u = 0.0
        if not self.path_ahead.get("clear", True):
            u += 0.4
        if self.path_ahead.get("safety_alert"):
            u += 0.3
        if self.cv_emergency:
            u += 0.5
        for obj in self.known_objects:
            if obj.get("toward_user"):
                u += 0.2
        # Temporal: imminent obstacle boosts urgency
        if self._last_validation and self._last_validation.get("status") == "imminent":
            remaining = self._last_validation.get("remaining_distance", 2)
            if remaining is not None and remaining < 1.0:
                u = max(u, 0.9)
            elif remaining is not None and remaining < 2.0:
                u = max(u, 0.7)
        self.urgency = max(0.0, min(1.0, u))

    def compile_memory_injection(self):
        """Build periodic context refresh for Gemini Live (silent injection)."""
        parts = []

        env_type = self.environment.get("type", "unknown")
        if env_type != "unknown":
            parts.append(f"Environment: {self.environment.get('description', env_type)}")

        if not self.path_ahead.get("clear", True):
            parts.append(f"Path blocked by: {self.path_ahead.get('blocked_by', 'obstacle')}")

        movement = self.user_state.get("movement", "stationary")
        parts.append(f"User is {movement}")
        if self.user_state.get("on_stairs"):
            parts.append("On stairs")

        goal_context = self.goals.get_context_for_memory()
        if goal_context:
            parts.append(goal_context)

        if self.known_objects:
            obj_strs = [f"{o['what']} {o.get('where', '')}" for o in self.known_objects[:3]]
            parts.append(f"Nearby: {', '.join(obj_strs)}")

        if self.text_signs:
            parts.append(f"Signs: {', '.join(self.text_signs[:3])}")

        if not parts:
            return None

        return "SPATIAL CONTEXT UPDATE: " + ". ".join(parts) + "."

    def get_brain_state_for_ui(self):
        """Return state dict for frontend brain panel."""
        active_goals = self.goals.get_active_goals()[:3]
        return {
            "dimensions": {
                "vigilance": round(self.vigilance, 2),
                "verbosity": round(self.verbosity, 2),
                "urgency": round(self.urgency, 2),
                "spatial_confidence": round(self.spatial_confidence, 2),
            },
            "environment": self.environment.get("type", "unknown"),
            "path_clear": self.path_ahead.get("clear", True),
            "path_blocked_by": self.path_ahead.get("blocked_by"),
            "active_goals": [
                {
                    "id": g.get("id"),
                    "type": g.get("type"),
                    "priority": g.get("priority", 0),
                    "description": g.get("description", ""),
                    "target": g.get("target"),
                }
                for g in active_goals
            ],
            "last_nudge": self.last_nudge_text,
            "last_validation": {
                "status": self._last_validation.get("status") if self._last_validation else None,
                "remaining": self._last_validation.get("remaining_distance") if self._last_validation else None,
                "reason": self._last_validation.get("reason") if self._last_validation else None,
            },
            "frame_count": self.frame_count,
            "session_seconds": int(time.time() - self.session_start),
            "sensors_active": self.user_state.get("sensors_active", False),
        }
