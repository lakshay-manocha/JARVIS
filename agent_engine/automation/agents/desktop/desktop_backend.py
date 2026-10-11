"""
Desktop backend contract for M5-K.

This module defines the interface between the JARVIS desktop/application
automation layer and the underlying operating system.

The backend is intentionally kept separate from the AutomationAgent so
that OS-specific implementation details do not leak into the agent layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class DesktopBackend(ABC):
    """
    Abstract backend contract for application and window automation.

    M5-K exposes eight operations:

    Application lifecycle:
        - launch_application
        - close_application
        - restart_application
        - terminate_application

    Window management:
        - focus_window
        - switch_window
        - resize_window
        - position_window
    """

    # ------------------------------------------------------------------
    # Application lifecycle operations
    # ------------------------------------------------------------------

    @abstractmethod
    def launch_application(self, application: str) -> Any:
        """
        Launch the requested application.
        """
        raise NotImplementedError

    @abstractmethod
    def close_application(self, application: str) -> Any:
        """
        Gracefully close the requested application.
        """
        raise NotImplementedError

    @abstractmethod
    def restart_application(self, application: str) -> Any:
        """
        Restart the requested application.
        """
        raise NotImplementedError

    @abstractmethod
    def terminate_application(self, application: str) -> Any:
        """
        Forcefully terminate the requested application.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Window management operations
    # ------------------------------------------------------------------

    @abstractmethod
    def focus_window(self, application: str) -> Any:
        """
        Bring the application's window into focus.
        """
        raise NotImplementedError

    @abstractmethod
    def switch_window(self, target: str) -> Any:
        """
        Switch the active window to the requested target.
        """
        raise NotImplementedError

    @abstractmethod
    def resize_window(
        self,
        application: str,
        width: int,
        height: int,
    ) -> Any:
        """
        Resize the application's window.
        """
        raise NotImplementedError

    @abstractmethod
    def position_window(
        self,
        application: str,
        x: int,
        y: int,
    ) -> Any:
        """
        Move the application's window to the requested screen position.
        """
        raise NotImplementedError