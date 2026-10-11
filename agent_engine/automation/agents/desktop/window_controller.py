"""
Window-management controller for M5-K.

This controller owns window activation, switching, resizing, and
positioning operations. OS-specific implementation is delegated to
DesktopBackend.
"""

from __future__ import annotations

from agent_engine.registry.application_registry import ApplicationRegistry

from .desktop_backend import DesktopBackend


class WindowController:
    """
    Controls application-window operations.

    Responsibilities:
        - Validate window-operation parameters.
        - Normalize registered application names.
        - Delegate operations to DesktopBackend.

    This controller does not perform:
        - planning
        - scheduling
        - retry/fallback
        - process monitoring
        - application lifecycle management
        - keyboard/mouse automation
    """

    def __init__(self, backend: DesktopBackend) -> None:
        """
        Create a WindowController.

        Args:
            backend: Backend responsible for OS-level window operations.
        """
        if not isinstance(backend, DesktopBackend):
            raise TypeError("backend must be a DesktopBackend.")

        self._backend = backend

    @property
    def backend(self) -> DesktopBackend:
        """Return the configured desktop backend."""
        return self._backend

    @staticmethod
    def _normalize_application(application: str) -> str:
        """
        Validate and normalize an application name.
        """
        if not isinstance(application, str) or not application.strip():
            raise ValueError(
                "application must be a non-empty string"
            )

        return ApplicationRegistry.normalize(application)

    @staticmethod
    def _validate_target(target: str) -> str:
        """
        Validate a window-switch target.
        """
        if not isinstance(target, str) or not target.strip():
            raise ValueError(
                "target must be a non-empty string"
            )

        return target.strip()

    @staticmethod
    def _validate_dimension(
        value: int,
        parameter_name: str,
    ) -> int:
        """
        Validate a positive integer window dimension.
        """
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(
                f"{parameter_name} must be a positive integer"
            )

        if value <= 0:
            raise ValueError(
                f"{parameter_name} must be a positive integer"
            )

        return value

    @staticmethod
    def _validate_coordinate(
        value: int,
        parameter_name: str,
    ) -> int:
        """
        Validate a window coordinate.

        Coordinates may be positive, zero, or negative because a window
        can legitimately be positioned on a monitor whose coordinate
        space extends beyond the primary display.
        """
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(
                f"{parameter_name} must be an integer"
            )

        return value

    def focus(self, application: str):
        """
        Bring the specified application's window into focus.
        """
        normalized_application = self._normalize_application(application)

        return self._backend.focus_window(
            normalized_application
        )

    def switch(self, target: str):
        """
        Switch the active window to the requested target.
        """
        normalized_target = self._validate_target(target)

        return self._backend.switch_window(
            normalized_target
        )

    def resize(
        self,
        application: str,
        width: int,
        height: int,
    ):
        """
        Resize an application's window.
        """
        normalized_application = self._normalize_application(application)

        validated_width = self._validate_dimension(
            width,
            "width",
        )

        validated_height = self._validate_dimension(
            height,
            "height",
        )

        return self._backend.resize_window(
            normalized_application,
            validated_width,
            validated_height,
        )

    def position(
        self,
        application: str,
        x: int,
        y: int,
    ):
        """
        Position an application's window.
        """
        normalized_application = self._normalize_application(application)

        validated_x = self._validate_coordinate(
            x,
            "x",
        )

        validated_y = self._validate_coordinate(
            y,
            "y",
        )

        return self._backend.position_window(
            normalized_application,
            validated_x,
            validated_y,
        )