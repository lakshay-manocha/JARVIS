"""
Fake desktop backend for M5-K testing.

This backend does not perform real operating-system automation.

Instead, it records every requested operation and returns a deterministic
result. It is used to test the Application & Window Automation Agent,
controllers, action routing, validation, and lifecycle behavior without
touching the real desktop.
"""

from __future__ import annotations

from typing import Any

from .desktop_backend import DesktopBackend


class FakeDesktopBackend(DesktopBackend):
    """
    Deterministic fake implementation of DesktopBackend.

    Every backend operation:
        1. Records the operation.
        2. Stores its parameters.
        3. Returns a predictable dictionary.

    No real application or window is opened, closed, resized, or moved.
    """

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def _record(
        self,
        operation: str,
        **parameters: Any,
    ) -> dict[str, Any]:
        call = {
            "operation": operation,
            "parameters": parameters,
        }

        self.calls.append(call)

        return {
            "operation": operation,
            "parameters": parameters,
            "backend": "fake",
        }

    def launch_application(
        self,
        application: str,
    ) -> dict[str, Any]:
        return self._record(
            "launch_application",
            application=application,
        )

    def close_application(
        self,
        application: str,
    ) -> dict[str, Any]:
        return self._record(
            "close_application",
            application=application,
        )

    def restart_application(
        self,
        application: str,
    ) -> dict[str, Any]:
        return self._record(
            "restart_application",
            application=application,
        )

    def terminate_application(
        self,
        application: str,
    ) -> dict[str, Any]:
        return self._record(
            "terminate_application",
            application=application,
        )

    def focus_window(
        self,
        application: str,
    ) -> dict[str, Any]:
        return self._record(
            "focus_window",
            application=application,
        )

    def switch_window(
        self,
        target: str,
    ) -> dict[str, Any]:
        return self._record(
            "switch_window",
            target=target,
        )

    def resize_window(
        self,
        application: str,
        width: int,
        height: int,
    ) -> dict[str, Any]:
        return self._record(
            "resize_window",
            application=application,
            width=width,
            height=height,
        )

    def position_window(
        self,
        application: str,
        x: int,
        y: int,
    ) -> dict[str, Any]:
        return self._record(
            "position_window",
            application=application,
            x=x,
            y=y,
        )