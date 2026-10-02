from __future__ import annotations

import time
from typing import Any, Protocol

from ...automation.agents.screen.screen_backend import (
    ScreenBackend,
    WindowsScreenBackend,
)


class OCRProvider(Protocol):

    def readtext(self, image: Any) -> list[Any]:
        ...


class GroundingProvider(Protocol):

    def locate(
        self,
        image: Any,
        query: str,
    ) -> Any:
        ...

    def detect_visible_elements(
        self,
        image: Any,
    ) -> Any:
        ...


class ScreenAware:
    """
    Screen perception layer.

    Responsibilities:
        - screen capture through backend
        - OCR
        - text matching
        - visual grounding
        - visible element detection
        - coordinate validation

    Non-responsibilities:
        - mouse
        - keyboard
        - planning
        - decision making
    """

    def __init__(
        self,
        backend: ScreenBackend | None = None,
        ocr: OCRProvider | None = None,
        grounding_model: GroundingProvider | None = None,
    ) -> None:

        self.backend = backend or WindowsScreenBackend()

        self._ocr = ocr
        self._grounding_model = grounding_model

    # ------------------------------------------------------------------
    # Lightweight screen operations
    # ------------------------------------------------------------------

    def capture_screen(
        self,
        monitor: int | None = None,
        all_screens: bool = False,
    ) -> dict[str, Any]:

        result = self.backend.capture_screen(
            monitor=monitor,
            all_screens=all_screens,
        )

        return {
            "success": True,
            "image": result.image,
            "width": result.width,
            "height": result.height,
            "monitor": result.monitor,
            "timestamp": result.timestamp,
        }

    def capture_region(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> dict[str, Any]:

        return self.backend.capture_region(
            x=x,
            y=y,
            width=width,
            height=height,
        )

    def get_screen_size(
        self,
        monitor: int | None = None,
    ) -> dict[str, int]:

        return self.backend.get_screen_size(
            monitor=monitor
        )

    # ------------------------------------------------------------------
    # OCR
    # ------------------------------------------------------------------

    def _get_ocr(self) -> OCRProvider:

        if self._ocr is None:
            import easyocr

            self._ocr = easyocr.Reader(
                ["en"],
                gpu=True,
            )

        return self._ocr

    def locate_text(
        self,
        text: str,
        case_sensitive: bool = False,
    ) -> dict[str, Any]:

        if not text or not text.strip():
            raise ValueError("text must not be empty")

        start = time.perf_counter()

        capture = self.capture_screen()

        image = capture["image"]

        ocr = self._get_ocr()

        results = ocr.readtext(image)

        target = text if case_sensitive else text.lower()

        for result in results:

            if len(result) < 3:
                continue

            polygon = result[0]
            detected_text = str(result[1])
            confidence = float(result[2])

            comparison = (
                detected_text
                if case_sensitive
                else detected_text.lower()
            )

            if target not in comparison:
                continue

            bbox = self._polygon_to_bbox(polygon)

            self._validate_bbox(
                bbox,
                capture["width"],
                capture["height"],
            )

            center = self._bbox_center(bbox)

            return {
                "found": True,
                "text": detected_text,
                "bbox": bbox,
                "center": center,
                "coordinates": center,
                "confidence": confidence,
                "method": "ocr",
                "latency_ms": self._latency(start),
            }

        return {
            "found": False,
            "text": text,
            "coordinates": None,
            "center": None,
            "bbox": None,
            "confidence": None,
            "method": "ocr",
            "latency_ms": self._latency(start),
        }

    # ------------------------------------------------------------------
    # Visual grounding
    # ------------------------------------------------------------------

    def _get_grounding_model(self) -> GroundingProvider:

        if self._grounding_model is None:

            from .grounding_model import ScreenGroundingModel

            self._grounding_model = ScreenGroundingModel()

        return self._grounding_model

    def locate_element(
        self,
        query: str,
    ) -> dict[str, Any]:

        if not query or not query.strip():
            raise ValueError("query must not be empty")

        start = time.perf_counter()

        capture = self.capture_screen()

        image = capture["image"]

        model = self._get_grounding_model()

        raw_result = model.locate(
            image,
            query,
        )

        parsed = self._normalise_grounding_result(
            raw_result,
            capture["width"],
            capture["height"],
        )

        if parsed is None:
            return {
                "found": False,
                "query": query,
                "coordinates": None,
                "center": None,
                "bbox": None,
                "confidence": None,
                "method": "vlm",
                "latency_ms": self._latency(start),
            }

        bbox = parsed["bbox"]

        return {
            "found": True,
            "query": query,
            "coordinates": self._bbox_center(bbox),
            "center": self._bbox_center(bbox),
            "bbox": bbox,
            "confidence": parsed.get("confidence"),
            "method": "vlm",
            "latency_ms": self._latency(start),
        }

    # ------------------------------------------------------------------
    # Visible elements
    # ------------------------------------------------------------------

    def detect_visible_elements(self) -> list[dict[str, Any]]:

        start = time.perf_counter()

        capture = self.capture_screen()

        model = self._get_grounding_model()

        if not hasattr(model, "detect_visible_elements"):
            raise NotImplementedError(
                "Grounding model does not support "
                "detect_visible_elements()"
            )

        raw_elements = model.detect_visible_elements(
            capture["image"]
        )

        if raw_elements is None:
            return []

        elements: list[dict[str, Any]] = []

        for element in raw_elements:

            parsed = self._normalise_grounding_result(
                element,
                capture["width"],
                capture["height"],
            )

            if parsed is None:
                continue

            bbox = parsed["bbox"]

            elements.append(
                {
                    "type": parsed.get("type", "unknown"),
                    "text": parsed.get("text"),
                    "bbox": bbox,
                    "center": self._bbox_center(bbox),
                    "confidence": parsed.get("confidence"),
                    "method": parsed.get(
                        "method",
                        "vision",
                    ),
                    "latency_ms": self._latency(start),
                }
            )

        return elements

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _polygon_to_bbox(
        polygon: Any,
    ) -> dict[str, int]:

        xs = [int(point[0]) for point in polygon]
        ys = [int(point[1]) for point in polygon]

        return {
            "x1": min(xs),
            "y1": min(ys),
            "x2": max(xs),
            "y2": max(ys),
        }

    @staticmethod
    def _bbox_center(
        bbox: dict[str, int],
    ) -> dict[str, int]:

        return {
            "x": (bbox["x1"] + bbox["x2"]) // 2,
            "y": (bbox["y1"] + bbox["y2"]) // 2,
        }

    @staticmethod
    def _validate_bbox(
        bbox: dict[str, int],
        screen_width: int,
        screen_height: int,
    ) -> None:

        x1 = bbox["x1"]
        y1 = bbox["y1"]
        x2 = bbox["x2"]
        y2 = bbox["y2"]

        if x1 < 0 or y1 < 0:
            raise ValueError("Bounding box contains negative coordinates")

        if x2 < x1 or y2 < y1:
            raise ValueError("Bounding box coordinates are reversed")

        if x2 > screen_width:
            raise ValueError("Bounding box exceeds screen width")

        if y2 > screen_height:
            raise ValueError("Bounding box exceeds screen height")

    @classmethod
    def _normalise_grounding_result(
        cls,
        result: Any,
        screen_width: int,
        screen_height: int,
    ) -> dict[str, Any] | None:

        if result is None:
            return None

        if isinstance(result, dict):

            bbox = result.get("bbox")

            if bbox is None:
                return None

            bbox = cls._normalise_bbox(
                bbox,
                screen_width,
                screen_height,
            )

            cls._validate_bbox(
                bbox,
                screen_width,
                screen_height,
            )

            return {
                **result,
                "bbox": bbox,
            }

        if isinstance(result, (list, tuple)) and len(result) == 4:

            bbox = cls._normalise_bbox(
                result,
                screen_width,
                screen_height,
            )

            cls._validate_bbox(
                bbox,
                screen_width,
                screen_height,
            )

            return {
                "bbox": bbox,
                "confidence": None,
                "method": "vlm",
            }

        return None

    @staticmethod
    def _normalise_bbox(
        bbox: Any,
        screen_width: int,
        screen_height: int,
    ) -> dict[str, int]:

        if isinstance(bbox, dict):

            x1 = bbox["x1"]
            y1 = bbox["y1"]
            x2 = bbox["x2"]
            y2 = bbox["y2"]

        elif isinstance(bbox, (list, tuple)):

            if len(bbox) != 4:
                raise ValueError("Bounding box must contain four values")

            x1, y1, x2, y2 = bbox

        else:
            raise ValueError("Unsupported bounding box format")

        values = [
            float(x1),
            float(y1),
            float(x2),
            float(y2),
        ]

        # Explicit 0-1000 normalized coordinate handling.
        if all(0 <= value <= 1000 for value in values):
            if (
                max(values) <= 1000
                and (
                    values[2] > screen_width
                    or values[3] > screen_height
                )
            ):
                x1 = int(values[0] * screen_width / 1000)
                y1 = int(values[1] * screen_height / 1000)
                x2 = int(values[2] * screen_width / 1000)
                y2 = int(values[3] * screen_height / 1000)

                return {
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                }

        return {
            "x1": int(x1),
            "y1": int(y1),
            "x2": int(x2),
            "y2": int(y2),
        }

    @staticmethod
    def _latency(start: float) -> float:
        return round(
            (time.perf_counter() - start) * 1000,
            2,
        )


_screen_aware: ScreenAware | None = None


def get_screen_aware() -> ScreenAware:

    global _screen_aware

    if _screen_aware is None:
        _screen_aware = ScreenAware()

    return _screen_aware