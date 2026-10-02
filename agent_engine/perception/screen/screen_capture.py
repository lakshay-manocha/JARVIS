from __future__ import annotations

from typing import Any

from ...automation.agents.screen.screen_backend import (
    ScreenBackend,
    WindowsScreenBackend,
)


class ScreenCapture:
    """
    Compatibility facade for screen acquisition.

    Actual screen acquisition is delegated to ScreenBackend.
    """

    def __init__(
        self,
        backend: ScreenBackend | None = None,
    ) -> None:

        self.backend = backend or WindowsScreenBackend()

    def capture(
        self,
        monitor: int | None = None,
        all_screens: bool = False,
    ):
        return self.backend.capture_screen(
            monitor=monitor,
            all_screens=all_screens,
        )

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