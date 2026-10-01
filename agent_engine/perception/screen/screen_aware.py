"""
===============================================================================
File Name   : screen_aware.py
Module      : JARVIS Perception - Screen Awareness
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Context-aware desktop screen perception.

Pipeline:

    Query
      ↓
    Screenshot
      ↓
    EasyOCR
      │
      ├── Found → coordinates
      │
      └── Not Found
              ↓
          Qwen2-VL
              ↓
          coordinates

The Qwen2-VL model is loaded ONCE and reused for all future requests.
===============================================================================
"""

from __future__ import annotations

import threading
from time import perf_counter
from typing import Any

import numpy as np
import torch
from PIL import ImageGrab

import easyocr

from .grounding_model import ScreenGroundingModel


class ScreenAware:
    """
    Persistent screen perception engine.

    One instance owns:
        - EasyOCR model
        - Qwen2-VL model

    The expensive models are initialized only once.
    """

    def __init__(
        self,
        *,
        use_vlm: bool = True,
        use_ocr: bool = True,
    ) -> None:

        self.use_vlm = use_vlm
        self.use_ocr = use_ocr

        self._initialized = False
        self._initialization_lock = threading.Lock()

        self._ocr = None
        self._vlm = None

        self._stats = {
            "screenshots": 0,
            "ocr_requests": 0,
            "vlm_requests": 0,
            "ocr_hits": 0,
            "vlm_hits": 0,
            "misses": 0,
        }

    # =========================================================================
    # Initialization
    # =========================================================================

    def initialize(self) -> None:
        """
        Initialize perception models exactly once.

        Safe to call repeatedly.
        """

        if self._initialized:
            return

        with self._initialization_lock:

            if self._initialized:
                return

            print()
            print("=" * 70)
            print("JARVIS SCREEN AWARENESS INITIALIZATION")
            print("=" * 70)

            print(
                f"[SCREEN] CUDA available: "
                f"{torch.cuda.is_available()}"
            )

            if torch.cuda.is_available():
                print(
                    f"[SCREEN] GPU: "
                    f"{torch.cuda.get_device_name(0)}"
                )

            # -----------------------------------------------------------------
            # OCR
            # -----------------------------------------------------------------

            if self.use_ocr:

                print("[SCREEN] Loading EasyOCR...")

                self._ocr = easyocr.Reader(
                    ["en"],
                    gpu=torch.cuda.is_available(),
                    verbose=False,
                )

                print("[SCREEN] EasyOCR ready.")

            # -----------------------------------------------------------------
            # Vision-Language Model
            # -----------------------------------------------------------------

            if self.use_vlm:

                print(
                    "[SCREEN] Loading Qwen2-VL "
                    "Screen Grounding Model..."
                )

                self._vlm = ScreenGroundingModel()

                self._vlm.load()

                print(
                    "[SCREEN] Qwen2-VL loaded and "
                    "ready for reuse."
                )

            self._initialized = True

            print("[SCREEN] ScreenAware READY.")
            print("=" * 70)
            print()

    # =========================================================================
    # Screenshot
    # =========================================================================

    def screenshot(self):
        """
        Capture the current desktop.

        Returns:
            PIL.Image.Image
        """

        image = ImageGrab.grab()

        if image.mode != "RGB":
            image = image.convert("RGB")

        self._stats["screenshots"] += 1

        return image

    # =========================================================================
    # OCR
    # =========================================================================

    def _find_with_ocr(
        self,
        image,
        query: str,
    ) -> dict[str, Any] | None:

        if self._ocr is None:
            return None

        self._stats["ocr_requests"] += 1

        query_clean = query.lower().strip()

        if not query_clean:
            return None

        results = self._ocr.readtext(
            np.array(image)
        )

        for box, text, confidence in results:

            detected_text = text.strip()

            if not detected_text:
                continue

            detected_lower = detected_text.lower()

            # -------------------------------------------------------------
            # Matching strategy
            # -------------------------------------------------------------

            matched = (
                query_clean == detected_lower
                or query_clean in detected_lower
                or detected_lower in query_clean
            )

            if not matched:
                continue

            # -------------------------------------------------------------
            # Bounding box
            # -------------------------------------------------------------

            xs = [
                int(point[0])
                for point in box
            ]

            ys = [
                int(point[1])
                for point in box
            ]

            x1 = min(xs)
            y1 = min(ys)
            x2 = max(xs)
            y2 = max(ys)

            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            self._stats["ocr_hits"] += 1

            return {
                "found": True,
                "query": query,
                "text": detected_text,
                "x": center_x,
                "y": center_y,
                "coordinates": {
                    "x": center_x,
                    "y": center_y,
                },
                "bbox": [
                    x1,
                    y1,
                    x2,
                    y2,
                ],
                "confidence": float(confidence),
                "method": "OCR",
            }

        return None

    # =========================================================================
    # Qwen2-VL
    # =========================================================================

    def _find_with_vlm(
        self,
        image,
        query: str,
    ) -> dict[str, Any] | None:

        if self._vlm is None:
            return None

        self._stats["vlm_requests"] += 1

        # The current grounding_model implementation already handles
        # Qwen2-VL inference and coordinate extraction.

        result = self._vlm.locate(
            image,
            query,
        )

        if not result:
            return None

        if not result.get("found"):
            return None

        coordinates = result.get(
            "coordinates",
            {}
        )

        x = coordinates.get("x")
        y = coordinates.get("y")

        if x is None or y is None:
            return None

        self._stats["vlm_hits"] += 1

        return {
            "found": True,
            "query": query,
            "text": query,
            "x": int(x),
            "y": int(y),
            "coordinates": {
                "x": int(x),
                "y": int(y),
            },
            "bbox": result.get("bbox"),
            "confidence": result.get(
                "confidence",
                0.0,
            ),
            "method": "Qwen2-VL",
        }

    # =========================================================================
    # Public Locate API
    # =========================================================================

    def find(
        self,
        query: str,
    ) -> dict[str, Any]:

        start_time = perf_counter()

        if not isinstance(query, str):
            raise TypeError(
                "Screen query must be a string."
            )

        query = query.strip()

        if not query:
            raise ValueError(
                "Screen query cannot be empty."
            )

        self.initialize()

        image = self.screenshot()

        # ---------------------------------------------------------------------
        # FAST PATH: OCR
        # ---------------------------------------------------------------------

        if self.use_ocr:

            result = self._find_with_ocr(
                image,
                query,
            )

            if result is not None:

                result["latency"] = (
                    perf_counter() - start_time
                )

                return result

        # ---------------------------------------------------------------------
        # FALLBACK: Qwen2-VL
        # ---------------------------------------------------------------------

        if self.use_vlm:

            result = self._find_with_vlm(
                image,
                query,
            )

            if result is not None:

                result["latency"] = (
                    perf_counter() - start_time
                )

                return result

        # ---------------------------------------------------------------------
        # NOT FOUND
        # ---------------------------------------------------------------------

        self._stats["misses"] += 1

        return {
            "found": False,
            "query": query,
            "text": None,
            "x": None,
            "y": None,
            "coordinates": None,
            "bbox": None,
            "confidence": 0.0,
            "method": None,
            "latency": (
                perf_counter() - start_time
            ),
        }

    # =========================================================================
    # Convenience API
    # =========================================================================

    def locate(
        self,
        query: str,
    ) -> dict[str, Any]:
        """
        Alias for find().
        """

        return self.find(query)

    # =========================================================================
    # Warmup
    # =========================================================================

    def warmup(self) -> None:
        """
        Explicitly load all models before JARVIS begins normal operation.

        This is optional.

        If not called, initialization happens lazily during the first
        screen request.
        """

        self.initialize()

    # =========================================================================
    # Diagnostics
    # =========================================================================

    @property
    def stats(self) -> dict[str, int]:
        """
        Return perception statistics.
        """

        return dict(self._stats)

    @property
    def ready(self) -> bool:
        """
        Return whether ScreenAware has been initialized.
        """

        return self._initialized

    # =========================================================================
    # Cleanup
    # =========================================================================

    def cleanup(self) -> None:
        """
        Release screen perception models.

        Normally called only when shutting down JARVIS.
        """

        self._ocr = None
        self._vlm = None
        self._initialized = False

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        print("[SCREEN] ScreenAware cleaned up.")


# =============================================================================
# PROCESS-LEVEL SINGLETON
# =============================================================================

_screen_aware_instance: ScreenAware | None = None

_screen_aware_lock = threading.Lock()


def get_screen_aware() -> ScreenAware:
    """
    Return the process-wide ScreenAware instance.

    This is the key mechanism that prevents Qwen2-VL from being loaded
    repeatedly for every JARVIS request.
    """

    global _screen_aware_instance

    if _screen_aware_instance is None:

        with _screen_aware_lock:

            if _screen_aware_instance is None:

                _screen_aware_instance = ScreenAware()

    return _screen_aware_instance