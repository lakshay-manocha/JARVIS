"""
Application lifecycle controller for M5-K.

This controller owns application-level lifecycle operations and delegates
the actual operating-system interaction to DesktopBackend.
"""

from __future__ import annotations

from agent_engine.registry.application_registry import ApplicationRegistry

from .desktop_backend import DesktopBackend


class ApplicationController:
    """
    Controls the lifecycle of registered applications.

    Responsibilities:
        - Normalize application names.
        - Validate application input.
        - Delegate lifecycle operations to DesktopBackend.

    This controller does not perform:
        - planning
        - scheduling
        - retry/fallback
        - process monitoring
        - window management
    """

    def __init__(self, backend: DesktopBackend) -> None:
        """
        Create an ApplicationController.

        Args:
            backend: Backend responsible for OS-level execution.
        """
        if not isinstance(backend, DesktopBackend):
            raise TypeError("backend must be a DesktopBackend.")

        self._backend = backend

    @property
    def backend(self) -> DesktopBackend:
        """Return the configured desktop backend."""
        return self._backend

    @staticmethod
    def _normalize(application: str) -> str:
        """
        Validate and normalize an application name.

        ApplicationRegistry is the single source of truth for supported
        application aliases.
        """
        if not isinstance(application, str) or not application.strip():
            raise ValueError(
                "application must be a non-empty string"
            )

        return ApplicationRegistry.normalize(application)

    def launch(self, application: str):
        """
        Launch an application.
        """
        normalized_application = self._normalize(application)

        return self._backend.launch_application(
            normalized_application
        )

    def close(self, application: str):
        """
        Gracefully close an application.
        """
        normalized_application = self._normalize(application)

        return self._backend.close_application(
            normalized_application
        )

    def restart(self, application: str):
        """
        Restart an application.
        """
        normalized_application = self._normalize(application)

        return self._backend.restart_application(
            normalized_application
        )

    def terminate(self, application: str):
        """
        Forcefully terminate an application.
        """
        normalized_application = self._normalize(application)

        return self._backend.terminate_application(
            normalized_application
        )