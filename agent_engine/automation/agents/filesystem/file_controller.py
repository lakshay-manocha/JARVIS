from __future__ import annotations

from typing import Any

from agent_engine.automation.agents.filesystem.filesystem_backend import (
    FileSystemBackend,
)


class FileController:
    """
    Controller for file-level automation operations.

    The controller is responsible for:
    - validating file-related parameters
    - delegating operations to FileSystemBackend

    It does not perform filesystem operations directly.
    """

    def __init__(self, backend: FileSystemBackend) -> None:
        if not isinstance(backend, FileSystemBackend):
            raise TypeError("backend must be a FileSystemBackend.")

        self._backend = backend

    def create_file(self, path: str) -> dict[str, Any]:
        """Create a file at the specified path."""
        normalized_path = self._validate_path(path)
        return self._backend.create_file(normalized_path)

    def delete_file(self, path: str) -> dict[str, Any]:
        """Delete a file at the specified path."""
        normalized_path = self._validate_path(path)
        return self._backend.delete_file(normalized_path)

    def copy_file(
        self,
        source: str,
        destination: str,
    ) -> dict[str, Any]:
        """Copy a file from source to destination."""
        normalized_source = self._validate_path(source, field_name="source")
        normalized_destination = self._validate_path(
            destination,
            field_name="destination",
        )

        return self._backend.copy_file(
            normalized_source,
            normalized_destination,
        )

    def move_file(
        self,
        source: str,
        destination: str,
    ) -> dict[str, Any]:
        """Move a file from source to destination."""
        normalized_source = self._validate_path(source, field_name="source")
        normalized_destination = self._validate_path(
            destination,
            field_name="destination",
        )

        return self._backend.move_file(
            normalized_source,
            normalized_destination,
        )

    def rename_file(
        self,
        path: str,
        new_name: str,
    ) -> dict[str, Any]:
        """Rename a file while keeping it in the same directory."""
        normalized_path = self._validate_path(path)
        normalized_name = self._validate_file_name(new_name)

        return self._backend.rename_file(
            normalized_path,
            normalized_name,
        )

    def get_file_metadata(
        self,
        path: str,
    ) -> dict[str, Any]:
        """Retrieve metadata for a file."""
        normalized_path = self._validate_path(path)
        return self._backend.get_file_metadata(normalized_path)

    @staticmethod
    def _validate_path(
        path: str,
        *,
        field_name: str = "path",
    ) -> str:
        """
        Validate and normalize a filesystem path.

        Path normalization beyond whitespace trimming is intentionally
        left to the backend so that the controller remains platform
        independent.
        """
        if isinstance(path, bool) or not isinstance(path, str):
            raise TypeError(f"{field_name} must be a string.")

        normalized_path = path.strip()

        if not normalized_path:
            raise ValueError(f"{field_name} cannot be empty.")

        return normalized_path

    @staticmethod
    def _validate_file_name(new_name: str) -> str:
        """
        Validate a new filename.

        The value must contain only a filename and must not represent
        another filesystem path.
        """
        if isinstance(new_name, bool) or not isinstance(new_name, str):
            raise TypeError("new_name must be a string.")

        normalized_name = new_name.strip()

        if not normalized_name:
            raise ValueError("new_name cannot be empty.")

        if normalized_name in {".", ".."}:
            raise ValueError("new_name must be a valid filename.")

        if "/" in normalized_name or "\\" in normalized_name:
            raise ValueError(
                "new_name must contain only a filename, not a path."
            )

        return normalized_name