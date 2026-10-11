from __future__ import annotations

from typing import Any

from agent_engine.automation.agents.filesystem.filesystem_backend import (
    FileSystemBackend,
)


class DirectoryController:
    """
    Controller for directory-level automation operations.

    The controller is responsible for:
    - validating directory-related parameters
    - delegating operations to FileSystemBackend

    It does not perform filesystem operations directly.
    """

    def __init__(self, backend: FileSystemBackend) -> None:
        if not isinstance(backend, FileSystemBackend):
            raise TypeError("backend must be a FileSystemBackend.")

        self._backend = backend

    def create_directory(self, path: str) -> dict[str, Any]:
        """Create a directory at the specified path."""
        normalized_path = self._validate_path(path)

        return self._backend.create_directory(normalized_path)

    def delete_directory(self, path: str) -> dict[str, Any]:
        """
        Delete a directory at the specified path.

        Recursive deletion is not implied by this controller.
        The backend determines the concrete deletion behavior.
        """
        normalized_path = self._validate_path(path)

        return self._backend.delete_directory(normalized_path)

    def list_directory(self, path: str) -> dict[str, Any]:
        """List entries contained in a directory."""
        normalized_path = self._validate_path(path)

        return self._backend.list_directory(normalized_path)

    def path_exists(self, path: str) -> dict[str, Any]:
        """Check whether a filesystem path exists."""
        normalized_path = self._validate_path(path)

        return self._backend.path_exists(normalized_path)

    @staticmethod
    def _validate_path(
        path: str,
        *,
        field_name: str = "path",
    ) -> str:
        """
        Validate and normalize a filesystem path.

        Path normalization beyond whitespace trimming is intentionally
        left to the backend so that the controller remains
        platform independent.
        """
        if isinstance(path, bool) or not isinstance(path, str):
            raise TypeError(f"{field_name} must be a string.")

        normalized_path = path.strip()

        if not normalized_path:
            raise ValueError(f"{field_name} cannot be empty.")

        return normalized_path