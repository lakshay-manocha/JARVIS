from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from PIL import ImageGrab


@dataclass(frozen=True)
class ScreenCaptureResult:
    """Immutable result of a screen capture operation."""

    image: Any
    width: int
    height: int
    monitor: int | None
    timestamp: str


class ScreenBackend(ABC):
    """
    Backend contract for acquiring screen pixels.

    This class is responsible ONLY for screen acquisition.
    It must not perform OCR, VLM reasoning, mouse movement,
    keyboard input, or task planning.
    """

    @abstractmethod
    def capture_screen(
        self,
        monitor: int | None = None,
        all_screens: bool = False,
    ) -> ScreenCaptureResult:
        """Capture the requested screen."""
        raise NotImplementedError

    @abstractmethod
    def capture_region(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> dict[str, Any]:
        """Capture a rectangular region."""
        raise NotImplementedError

    @abstractmethod
    def get_screen_size(
        self,
        monitor: int | None = None,
    ) -> dict[str, int]:
        """Return screen dimensions."""
        raise NotImplementedError


class WindowsScreenBackend(ScreenBackend):
    """
    Windows screen backend using Pillow ImageGrab.

    Coordinate contract:
        Coordinates are expressed in actual screen pixels.

    Current implementation:
        get_screen_size() returns the primary/virtual capture size
        exposed by ImageGrab.

    Multi-monitor:
        all_screens=True requests the complete virtual desktop where
        supported by Pillow.
    """

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def capture_screen(
        self,
        monitor: int | None = None,
        all_screens: bool = False,
    ) -> ScreenCaptureResult:

        if monitor is not None and (
            not isinstance(monitor, int) or monitor < 0
        ):
            raise ValueError("monitor must be None or a non-negative integer")

        if monitor is not None and all_screens:
            raise ValueError(
                "monitor and all_screens cannot be used together"
            )

        # Pillow's ImageGrab does not expose a universal monitor-selection
        # API across all Windows environments. The backend therefore uses
        # all_screens for the virtual desktop and primary capture otherwise.
        kwargs = {}

        if all_screens:
            kwargs["all_screens"] = True

        image = ImageGrab.grab(**kwargs)

        width, height = image.size

        return ScreenCaptureResult(
            image=image,
            width=width,
            height=height,
            monitor=monitor,
            timestamp=self._timestamp(),
        )

    def get_screen_size(
        self,
        monitor: int | None = None,
    ) -> dict[str, int]:

        if monitor is not None and (
            not isinstance(monitor, int) or monitor < 0
        ):
            raise ValueError("monitor must be None or a non-negative integer")

        image = ImageGrab.grab()

        width, height = image.size

        return {
            "width": width,
            "height": height,
        }

    def capture_region(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> dict[str, Any]:

        self._validate_region(x, y, width, height)

        screen = self.get_screen_size()

        screen_width = screen["width"]
        screen_height = screen["height"]

        if x + width > screen_width:
            raise ValueError(
                f"Region exceeds screen width: "
                f"x={x}, width={width}, screen_width={screen_width}"
            )

        if y + height > screen_height:
            raise ValueError(
                f"Region exceeds screen height: "
                f"y={y}, height={height}, screen_height={screen_height}"
            )

        image = ImageGrab.grab(
            bbox=(x, y, x + width, y + height)
        )

        return {
            "success": True,
            "image": image,
            "bbox": {
                "x": x,
                "y": y,
                "width": width,
                "height": height,
            },
            "screen_width": screen_width,
            "screen_height": screen_height,
        }

    @staticmethod
    def _validate_region(
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> None:

        if not isinstance(x, int) or not isinstance(y, int):
            raise ValueError("x and y must be integers")

        if not isinstance(width, int) or not isinstance(height, int):
            raise ValueError("width and height must be integers")

        if width <= 0:
            raise ValueError("width must be greater than zero")

        if height <= 0:
            raise ValueError("height must be greater than zero")

        if x < 0 or y < 0:
            raise ValueError("x and y cannot be negative")