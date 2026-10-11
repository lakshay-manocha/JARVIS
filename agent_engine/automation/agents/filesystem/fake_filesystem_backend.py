"""
Fake filesystem backend for JARVIS testing.

This backend implements FileSystemBackend entirely in memory.
It does not access the real operating-system filesystem.

Purpose:
    - Unit testing
    - Agent testing
    - Controller testing
    - Dispatcher testing
    - End-to-end fake automation testing
"""

from __future__ import annotations

from pathlib import PurePath
from typing import Any

from .filesystem_backend import FileSystemBackend


class FakeFileSystemBackend(FileSystemBackend):
    """
    In-memory implementation of FileSystemBackend.

    The backend maintains separate in-memory representations for:

        files
        directories

    No real filesystem operation is performed.
    """

    def __init__(self) -> None:
        self._files: dict[str, dict[str, Any]] = {}
        self._directories: set[str] = set()

        self.calls: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_path(path: str) -> str:
        """
        Normalize a filesystem path for deterministic fake-backend
        behavior.

        The fake backend does not resolve the path against the real
        filesystem.
        """
        normalized = str(PurePath(path))

        if normalized == ".":
            normalized = "."

        return normalized

    def _record_call(
        self,
        operation: str,
        parameters: dict[str, Any],
    ) -> None:
        """Record an operation for test verification."""
        self.calls.append(
            {
                "operation": operation,
                "parameters": parameters,
            }
        )

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    def create_file(
        self,
        path: str,
    ) -> dict[str, Any]:
        path = self._normalize_path(path)

        self._record_call(
            "create_file",
            {
                "path": path,
            },
        )

        if path in self._files:
            raise FileExistsError(
                f"File already exists: {path}"
            )

        self._files[path] = {
            "path": path,
            "size": 0,
            "is_file": True,
        }

        return {
            "created": True,
            "path": path,
        }

    def delete_file(
        self,
        path: str,
    ) -> dict[str, Any]:
        path = self._normalize_path(path)

        self._record_call(
            "delete_file",
            {
                "path": path,
            },
        )

        if path not in self._files:
            raise FileNotFoundError(
                f"File does not exist: {path}"
            )

        del self._files[path]

        return {
            "deleted": True,
            "path": path,
        }

    def copy_file(
        self,
        source: str,
        destination: str,
    ) -> dict[str, Any]:
        source = self._normalize_path(source)
        destination = self._normalize_path(destination)

        self._record_call(
            "copy_file",
            {
                "source": source,
                "destination": destination,
            },
        )

        if source not in self._files:
            raise FileNotFoundError(
                f"Source file does not exist: {source}"
            )

        if destination in self._files:
            raise FileExistsError(
                f"Destination file already exists: {destination}"
            )

        source_metadata = self._files[source].copy()

        source_metadata["path"] = destination

        self._files[destination] = source_metadata

        return {
            "copied": True,
            "source": source,
            "destination": destination,
        }

    def move_file(
        self,
        source: str,
        destination: str,
    ) -> dict[str, Any]:
        source = self._normalize_path(source)
        destination = self._normalize_path(destination)

        self._record_call(
            "move_file",
            {
                "source": source,
                "destination": destination,
            },
        )

        if source not in self._files:
            raise FileNotFoundError(
                f"Source file does not exist: {source}"
            )

        if destination in self._files:
            raise FileExistsError(
                f"Destination file already exists: {destination}"
            )

        metadata = self._files.pop(source)

        metadata["path"] = destination

        self._files[destination] = metadata

        return {
            "moved": True,
            "source": source,
            "destination": destination,
        }

    def rename_file(
        self,
        path: str,
        new_name: str,
    ) -> dict[str, Any]:
        path = self._normalize_path(path)

        self._record_call(
            "rename_file",
            {
                "path": path,
                "new_name": new_name,
            },
        )

        if path not in self._files:
            raise FileNotFoundError(
                f"File does not exist: {path}"
            )

        parent = str(PurePath(path).parent)

        if parent == ".":
            new_path = new_name
        else:
            new_path = str(
                PurePath(parent) / new_name
            )

        new_path = self._normalize_path(new_path)

        if new_path in self._files:
            raise FileExistsError(
                f"Destination file already exists: {new_path}"
            )

        metadata = self._files.pop(path)

        metadata["path"] = new_path

        self._files[new_path] = metadata

        return {
            "renamed": True,
            "path": path,
            "new_name": new_name,
            "new_path": new_path,
        }

    def get_file_metadata(
        self,
        path: str,
    ) -> dict[str, Any]:
        path = self._normalize_path(path)

        self._record_call(
            "get_file_metadata",
            {
                "path": path,
            },
        )

        if path not in self._files:
            raise FileNotFoundError(
                f"File does not exist: {path}"
            )

        return self._files[path].copy()

    # ------------------------------------------------------------------
    # Directory operations
    # ------------------------------------------------------------------

    def create_directory(
        self,
        path: str,
    ) -> dict[str, Any]:
        path = self._normalize_path(path)

        self._record_call(
            "create_directory",
            {
                "path": path,
            },
        )

        if path in self._directories:
            raise FileExistsError(
                f"Directory already exists: {path}"
            )

        self._directories.add(path)

        return {
            "created": True,
            "path": path,
        }

    def delete_directory(
        self,
        path: str,
    ) -> dict[str, Any]:
        path = self._normalize_path(path)

        self._record_call(
            "delete_directory",
            {
                "path": path,
            },
        )

        if path not in self._directories:
            raise FileNotFoundError(
                f"Directory does not exist: {path}"
            )

        # Recursive deletion is intentionally not supported.
        child_prefix = f"{path}{PurePath('/')}"

        for directory in self._directories:
            if directory != path and directory.startswith(
                child_prefix
            ):
                raise OSError(
                    f"Directory is not empty: {path}"
                )

        for file_path in self._files:
            if file_path.startswith(child_prefix):
                raise OSError(
                    f"Directory is not empty: {path}"
                )

        self._directories.remove(path)

        return {
            "deleted": True,
            "path": path,
        }

    def list_directory(
        self,
        path: str,
    ) -> dict[str, Any]:
        path = self._normalize_path(path)

        self._record_call(
            "list_directory",
            {
                "path": path,
            },
        )

        if path not in self._directories:
            raise FileNotFoundError(
                f"Directory does not exist: {path}"
            )

        entries: set[str] = set()

        # Windows filesystem paths use "\" as the separator.
        parent_prefix = f"{path}\\"

        for directory in self._directories:
            if directory.startswith(parent_prefix):
                relative = directory[len(parent_prefix):]

                # Only include direct children.
                if relative and "\\" not in relative:
                    entries.add(relative)

        for file_path in self._files:
            if file_path.startswith(parent_prefix):
                relative = file_path[len(parent_prefix):]

                # Only include direct children.
                if relative and "\\" not in relative:
                    entries.add(relative)

        return {
            "path": path,
            "entries": sorted(entries),
        }

    def path_exists(
        self,
        path: str,
    ) -> dict[str, Any]:
        path = self._normalize_path(path)

        self._record_call(
            "path_exists",
            {
                "path": path,
            },
        )

        exists = (
            path in self._files
            or path in self._directories
        )

        return {
            "path": path,
            "exists": exists,
        }