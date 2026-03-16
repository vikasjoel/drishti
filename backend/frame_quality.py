"""
Frame quality gate — skip Cloud Vision calls on low-quality frames.
"""

import logging
import os

from backend.logger import log_event

logger = logging.getLogger(__name__)

CV_MIN_FRAME_SIZE = int(os.environ.get("CV_MIN_FRAME_SIZE", "10000"))


def is_frame_good(jpeg_bytes: bytes) -> bool:
    """Check if a frame meets minimum quality for Cloud Vision analysis."""
    size = len(jpeg_bytes)
    if size < CV_MIN_FRAME_SIZE:
        log_event("frame_quality", "skipped", details={
            "size_bytes": size,
            "min_required": CV_MIN_FRAME_SIZE,
        })
        return False
    return True
