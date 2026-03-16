"""
Cloud Vision API client for reactive perception.
Uses Application Default Credentials (ADC) via google-cloud-vision library.
Sends JPEG frames, gets back bounding boxes, labels, and OCR text.
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor

from google.cloud import vision

from backend.logger import log_event

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2)


class CloudVisionClient:
    def __init__(self):
        self.client = vision.ImageAnnotatorClient()
        self._call_count = 0

    def analyze_frame_sync(self, jpeg_bytes: bytes) -> dict:
        """Synchronous frame analysis — run in executor for async."""
        self._call_count += 1
        t0 = time.time()

        image = vision.Image(content=jpeg_bytes)

        try:
            objects_response = self.client.object_localization(image=image)
            text_response = self.client.text_detection(image=image)
        except Exception as e:
            elapsed_ms = (time.time() - t0) * 1000
            log_event("cloud_vision", "api_error", message=str(e),
                      latency_ms=elapsed_ms)
            return {"objects": [], "text": []}

        elapsed_ms = (time.time() - t0) * 1000

        objects = []
        for obj in objects_response.localized_object_annotations:
            verts = obj.bounding_poly.normalized_vertices
            if len(verts) < 4:
                continue
            x_min, y_min = verts[0].x, verts[0].y
            x_max, y_max = verts[2].x, verts[2].y
            w, h = x_max - x_min, y_max - y_min
            objects.append({
                "label": obj.name.lower(),
                "confidence": round(obj.score, 3),
                "bbox": {"x": round(x_min, 4), "y": round(y_min, 4),
                         "w": round(w, 4), "h": round(h, 4)},
                "center_x": round((x_min + x_max) / 2, 4),
                "center_y": round((y_min + y_max) / 2, 4),
                "area_pct": round(w * h * 100, 2),
            })

        texts = []
        if text_response.text_annotations:
            texts = [t.description for t in text_response.text_annotations[1:]]

        log_event("cloud_vision", "analyze_frame", details={
            "objects": len(objects),
            "texts": len(texts),
            "call_number": self._call_count,
        }, latency_ms=elapsed_ms)

        return {"objects": objects, "text": texts}

    async def analyze_frame(self, jpeg_bytes: bytes) -> dict:
        """Async wrapper — runs Cloud Vision in thread pool (non-blocking)."""
        return await asyncio.get_event_loop().run_in_executor(
            _executor, self.analyze_frame_sync, jpeg_bytes
        )
