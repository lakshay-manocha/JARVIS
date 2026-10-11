from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from PIL import Image

from .screen_backend import ScreenBackend, ScreenCaptureResult


class FakeScreenBackend(ScreenBackend):
    """
    Deterministic screen backend for unit tests.

    Does not access:
        - Windows screen
        - mouse
        - keyboard
        - EasyOCR
        - Qwen
    """

    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        image: Image.Image | None = None,
    ) -> None:

        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive")

        self.width = width
        self.height = height

        self.image = image or Image.new(
            "RGB",
            (width, height),
            "white",
        )

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def capture_screen(
        self,
        monitor: int | None = None,
        all_screens: bool = False,
    ) -> ScreenCaptureResult:

        if monitor is not None and monitor < 0:
            raise ValueError("monitor cannot be negative")

        if monitor is not None and all_screens:
            raise ValueError(
                "monitor and all_screens cannot be used together"
            )

        return ScreenCaptureResult(
            image=self.image.copy(),
            width=self.width,
            height=self.height,
            monitor=monitor,
            timestamp=self._timestamp(),
        )

    def capture_region(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> dict[str, Any]:

        if width <= 0:
            raise ValueError("width must be greater than zero")

        if height <= 0:
            raise ValueError("height must be greater than zero")

        if x < 0 or y < 0:
            raise ValueError("x and y cannot be negative")

        if x + width > self.width:
            raise ValueError("region exceeds screen width")

        if y + height > self.height:
            raise ValueError("region exceeds screen height")

        cropped = self.image.crop(
            (x, y, x + width, y + height)
        )

        return {
            "success": True,
            "image": cropped,
            "bbox": {
                "x": x,
                "y": y,
                "width": width,
                "height": height,
            },
            "screen_width": self.width,
            "screen_height": self.height,
        }

    def get_screen_size(
        self,
        monitor: int | None = None,
    ) -> dict[str, int]:

        if monitor is not None and monitor < 0:
            raise ValueError("monitor cannot be negative")

        return {
            "width": self.width,
            "height": self.height,
        }