"""
Plugin configurations for Drishti v4.
Each plugin defines behavior baselines, priority labels, and voice addendum.
"""

PLUGINS = {
    "blind_navigation": {
        "name": "blind_navigation",
        "voice": "Kore",
        "camera_mode": "mobile",
        "vigilance_baseline": 0.3,
        "verbosity_baseline": 0.2,
        "priority_labels": ["person", "vehicle", "bicycle", "motorcycle", "car", "bus", "truck"],
        "cv_emergency_threshold": 15,
        "addendum": (
            "User is visually impaired. Safety is critical. "
            "Clock positions and step counts. Concise alerts. Silence when safe."
        ),
    },
    "baby_monitor": {
        "name": "baby_monitor",
        "voice": "Aoede",
        "camera_mode": "stationary",
        "vigilance_baseline": 0.4,
        "verbosity_baseline": 0.1,
        "priority_labels": ["person", "baby", "child"],
        "cv_emergency_threshold": 20,
        "addendum": (
            "Monitoring baby/child. Alert on: unusual movement, "
            "baby near boundary, unfamiliar person. Calm tone."
        ),
    },
    "elderly_care": {
        "name": "elderly_care",
        "voice": "Aoede",
        "camera_mode": "stationary",
        "vigilance_baseline": 0.35,
        "verbosity_baseline": 0.15,
        "priority_labels": ["person", "fall"],
        "cv_emergency_threshold": 20,
        "addendum": (
            "Monitoring elderly person. Alert on: falls, prolonged "
            "stillness, leaving zone. Warm, respectful tone."
        ),
    },
    "security": {
        "name": "security",
        "voice": "Fenrir",
        "camera_mode": "stationary",
        "vigilance_baseline": 0.5,
        "verbosity_baseline": 0.3,
        "priority_labels": ["person", "vehicle"],
        "cv_emergency_threshold": 10,
        "addendum": (
            "Security monitoring. Alert on any person entering, "
            "movement in exclusion zone. Professional tone."
        ),
    },
}
