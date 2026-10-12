
from __future__ import annotations

import time
from typing import Any, Protocol

from ...automation.agents.screen.screen_backend import (
    ScreenBackend,
    WindowsScreenBackend,
)


class OCRProvider(Protocol):
    """Interface implemented by OCR engines such as EasyOCR."""

    def readtext(self, image: Any) -> list[Any]:
        ...


class GroundingProvider(Protocol):
    """Interface implemented by visual grounding models."""

    def locate(self, image: Any, query: str) -> Any:
        ...



class VisibleElementsResult(list[dict[str, Any]]):
    """List-compatible result with dictionary-style metadata access."""

    def __init__(
        self,
        elements: list[dict[str, Any]],
        *,
        method: str,
        latency_ms: float,
        screen: dict[str, Any],
    ) -> None:
        super().__init__(elements)
        self._metadata = {
            "success": True,
            "elements": self,
            "count": len(self),
            "method": method,
            "latency_ms": latency_ms,
            "screen": screen,
        }

    def __getitem__(self, key: int | slice | str) -> Any:
        if isinstance(key, str):
            return self._metadata[key]
        return super().__getitem__(key)

    def get(self, key: str, default: Any = None) -> Any:
        return self._metadata.get(key, default)


class ScreenAware:
    """
    Screen perception layer.

    Responsibilities:
        - Screen capture through the configured backend.
        - OCR and text matching.
        - Visual grounding.
        - Visible-element detection.
        - Bounding-box normalization and validation.

    Non-responsibilities:
        - Mouse and keyboard execution.
        - Planning and decision-making.
        - Dispatching automation actions.

    Heavy OCR and vision models are loaded lazily.
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
    # Initialization
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Initialize the screen backend if it supports initialization."""
        initialize_backend = getattr(self.backend, "initialize", None)

        if callable(initialize_backend):
            initialize_backend()

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
        return self.backend.get_screen_size(monitor=monitor)

    # ------------------------------------------------------------------
    # OCR
    # ------------------------------------------------------------------

    def _get_ocr(self) -> OCRProvider:
        """Load EasyOCR only when OCR is first required."""
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
        """Locate text on the current screen using OCR."""
        if not text or not text.strip():
            raise ValueError("text must not be empty")

        start = time.perf_counter()
        capture = self.capture_screen()

        results = self._get_ocr().readtext(capture["image"])

        target = text if case_sensitive else text.lower()

        for result in results:
            if not isinstance(result, (tuple, list)) or len(result) < 3:
                continue

            polygon, detected_text, raw_confidence = result[:3]
            detected_text = str(detected_text)

            comparison = (
                detected_text
                if case_sensitive
                else detected_text.lower()
            )

            if target not in comparison:
                continue

            try:
                bbox = self._polygon_to_bbox(polygon)
                self._validate_bbox(
                    bbox,
                    capture["width"],
                    capture["height"],
                )
                confidence = float(raw_confidence)
            except (TypeError, ValueError, IndexError, KeyError):
                continue

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
        """Load the grounding model only when visual grounding is needed."""
        if self._grounding_model is None:
            from .grounding_model import ScreenGroundingModel

            self._grounding_model = ScreenGroundingModel()

        return self._grounding_model

    def locate_element(
        self,
        query: str,
    ) -> dict[str, Any]:
        """Locate a UI element described by a natural-language query."""
        if not query or not query.strip():
            raise ValueError("query must not be empty")

        start = time.perf_counter()
        capture = self.capture_screen()

        model = self._get_grounding_model()
        raw_result = model.locate(capture["image"], query)

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
        center = self._bbox_center(bbox)

        return {
            "found": True,
            "query": query,
            "coordinates": center,
            "center": center,
            "bbox": bbox,
            "confidence": parsed.get("confidence"),
            "method": parsed.get("method", "vlm"),
            "latency_ms": self._latency(start),
        }

    # ------------------------------------------------------------------
    # Visible-element detection
    # ------------------------------------------------------------------

    def detect_visible_elements(
        self,
        element_types: list[str] | None = None,
    ) -> VisibleElementsResult:
        """
        Detect visible UI elements and return a structured result.

        If an already-loaded grounding model provides semantic element
        detection, use it. Otherwise, fall back to OCR text regions.

        OCR regions are classified as "text"; OCR alone does not reliably
        determine whether a region is a button, icon, or other UI control.
        """
        start = time.perf_counter()
        capture = self.capture_screen()

        image = capture["image"]
        model = self._grounding_model

        raw_elements: Any = None
        method = "vision"

        # Do not load a heavy vision model just to enumerate visible text.
        detector = (
            getattr(model, "detect_visible_elements", None)
            if model is not None
            else None
        )

        if callable(detector):
            raw_elements = detector(image)

        # Use OCR when semantic detection is unavailable or returns no data.
        if raw_elements is None:
            method = "ocr"
            raw_elements = []

            for item in self._get_ocr().readtext(image):
                if not isinstance(item, (tuple, list)) or len(item) < 3:
                    continue

                polygon, raw_text, raw_confidence = item[:3]
                text = str(raw_text)

                if not text.strip():
                    continue

                try:
                    bbox = self._polygon_to_bbox(polygon)
                    self._validate_bbox(
                        bbox,
                        capture["width"],
                        capture["height"],
                    )
                    confidence = float(raw_confidence)
                except (TypeError, ValueError, IndexError, KeyError):
                    continue

                raw_elements.append(
                    {
                        "type": "text",
                        "text": text,
                        "bbox": bbox,
                        "confidence": confidence,
                        "method": "ocr",
                    }
                )

        # Accept either a list of elements or a dictionary containing them.
        if isinstance(raw_elements, dict):
            raw_elements = raw_elements.get("elements", [])

        if not isinstance(raw_elements, (list, tuple)):
            raw_elements = []

        allowed_types = (
            {item.strip().lower() for item in element_types if item.strip()}
            if element_types is not None
            else None
        )

        elements: list[dict[str, Any]] = []

        for item in raw_elements:
            try:
                parsed = self._normalise_grounding_result(
                    item,
                    capture["width"],
                    capture["height"],
                )
            except (TypeError, ValueError, IndexError, KeyError):
                continue

            if parsed is None:
                continue

            element_type = str(parsed.get("type", "unknown")).lower()

            if allowed_types and element_type not in allowed_types:
                continue

            bbox = parsed["bbox"]

            elements.append(
                {
                    "type": element_type,
                    "text": parsed.get("text"),
                    "bbox": bbox,
                    "center": self._bbox_center(bbox),
                    "confidence": parsed.get("confidence"),
                    "method": parsed.get("method", method),
                }
            )

        return VisibleElementsResult(
            elements,
            method=method,
            latency_ms=self._latency(start),
            screen={
                "width": capture["width"],
                "height": capture["height"],
                "monitor": capture.get("monitor"),
            },
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _polygon_to_bbox(
        polygon: Any,
    ) -> dict[str, int]:
        """Convert an OCR polygon into an axis-aligned bounding box."""
        if not isinstance(polygon, (list, tuple)) or not polygon:
            raise ValueError("OCR polygon must contain points")

        xs: list[int] = []
        ys: list[int] = []

        for point in polygon:
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                raise ValueError("Invalid OCR polygon point")

            xs.append(int(float(point[0])))
            ys.append(int(float(point[1])))

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
            raise ValueError(
                "Bounding box contains negative coordinates"
            )

        if x2 < x1 or y2 < y1:
            raise ValueError(
                "Bounding box coordinates are reversed"
            )

        if x2 > screen_width or y2 > screen_height:
            raise ValueError(
                "Bounding box exceeds screen dimensions"
            )

    @classmethod
    def _normalise_grounding_result(
        cls,
        result: Any,
        screen_width: int,
        screen_height: int,
    ) -> dict[str, Any] | None:
        """Normalize supported grounding results into a common format."""
        if result is None:
            return None

        if isinstance(result, dict):
            bbox = result.get("bbox")

            if bbox is None:
                return None

            normalized_bbox = cls._normalise_bbox(
                bbox,
                screen_width,
                screen_height,
            )

            cls._validate_bbox(
                normalized_bbox,
                screen_width,
                screen_height,
            )

            return {
                **result,
                "bbox": normalized_bbox,
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
        """Normalize a bounding box expressed as a dict or four values."""
        if isinstance(bbox, dict):
            try:
                x1 = bbox["x1"]
                y1 = bbox["y1"]
                x2 = bbox["x2"]
                y2 = bbox["y2"]
            except KeyError as exc:
                raise ValueError(
                    "Bounding box dictionary must contain x1, y1, x2, y2"
                ) from exc

        elif isinstance(bbox, (list, tuple)):
            if len(bbox) != 4:
                raise ValueError(
                    "Bounding box must contain four values"
                )

            x1, y1, x2, y2 = bbox

        else:
            raise ValueError("Unsupported bounding box format")

        values = [float(x1), float(y1), float(x2), float(y2)]

        if not all(value == value for value in values):
            raise ValueError("Bounding box contains NaN")

        # Interpret coordinates as 0–1000 normalized values only when
        # they exceed the corresponding pixel dimensions.
        if (
            all(0 <= value <= 1000 for value in values)
            and (
                values[2] > screen_width
                or values[3] > screen_height
            )
        ):
            x1, y1, x2, y2 = (
                int(values[0] * screen_width / 1000),
                int(values[1] * screen_height / 1000),
                int(values[2] * screen_width / 1000),
                int(values[3] * screen_height / 1000),
            )
        else:
            x1, y1, x2, y2 = (int(value) for value in values)

        return {
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
        }

    @staticmethod
    def _latency(start: float) -> float:
        return round(
            (time.perf_counter() - start) * 1000,
            2,
        )


_screen_aware: ScreenAware | None = None


def get_screen_aware() -> ScreenAware:
    """Return the shared ScreenAware instance."""
    global _screen_aware

    if _screen_aware is None:
        _screen_aware = ScreenAware()

    return _screen_aware
