"""
Real Windows filesystem backend for JARVIS.

This backend performs actual filesystem operations on Windows.

It implements the FileSystemBackend contract using Python's
standard filesystem libraries.

Safety principles:
    - No shell commands are used.
    - Existing files are not silently overwritten.
    - Directory deletion is non-recursive.
    - Filesystem policy remains outside this backend.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from .filesystem_backend import FileSystemBackend


class WindowsFileSystemBackend(FileSystemBackend):
    """
    Real Windows implementation of FileSystemBackend.

    This backend directly interacts with the Windows filesystem.
    """

    @staticmethod
    def _path(path: str) -> Path:
        """
        Convert a validated path string into a Path object.
        """
        return Path(path)

    @staticmethod
    def _ensure_destination_does_not_exist(
        destination: Path,
    ) -> None:
        """
        Prevent accidental overwrite of an existing destination.
        """
        if destination.exists():
            raise FileExistsError(
                f"Destination already exists: {destination}"
            )

    def create_file(self, path: str) -> dict[str, Any]:
        file_path = self._path(path)

        if file_path.exists():
            raise FileExistsError(
                f"File already exists: {file_path}"
            )

        file_path.touch()

        return {
            "created": True,
            "path": str(file_path),
        }

    def delete_file(self, path: str) -> dict[str, Any]:
        file_path = self._path(path)

        if not file_path.exists():
            raise FileNotFoundError(
                f"File does not exist: {file_path}"
            )

        if not file_path.is_file():
            raise IsADirectoryError(
                f"Path is not a file: {file_path}"
            )

        file_path.unlink()

        return {
            "deleted": True,
            "path": str(file_path),
        }

    def copy_file(
        self,
        source: str,
        destination: str,
    ) -> dict[str, Any]:
        source_path = self._path(source)
        destination_path = self._path(destination)

        if not source_path.exists():
            raise FileNotFoundError(
                f"Source file does not exist: {source_path}"
            )

        if not source_path.is_file():
            raise IsADirectoryError(
                f"Source path is not a file: {source_path}"
            )

        self._ensure_destination_does_not_exist(
            destination_path
        )

        shutil.copy2(
            source_path,
            destination_path,
        )

        return {
            "copied": True,
            "source": str(source_path),
            "destination": str(destination_path),
        }

    def move_file(
        self,
        source: str,
        destination: str,
    ) -> dict[str, Any]:
        source_path = self._path(source)
        destination_path = self._path(destination)

        if not source_path.exists():
            raise FileNotFoundError(
                f"Source file does not exist: {source_path}"
            )

        if not source_path.is_file():
            raise IsADirectoryError(
                f"Source path is not a file: {source_path}"
            )

        self._ensure_destination_does_not_exist(
            destination_path
        )

        shutil.move(
            str(source_path),
            str(destination_path),
        )

        return {
            "moved": True,
            "source": str(source_path),
            "destination": str(destination_path),
        }

    def rename_file(
        self,
        path: str,
        new_name: str,
    ) -> dict[str, Any]:
        file_path = self._path(path)

        if not file_path.exists():
            raise FileNotFoundError(
                f"File does not exist: {file_path}"
            )

        if not file_path.is_file():
            raise IsADirectoryError(
                f"Path is not a file: {file_path}"
            )

        destination_path = file_path.with_name(new_name)

        self._ensure_destination_does_not_exist(
            destination_path
        )

        file_path.rename(destination_path)

        return {
            "renamed": True,
            "path": str(file_path),
            "new_name": new_name,
            "new_path": str(destination_path),
        }

    def get_file_metadata(
        self,
        path: str,
    ) -> dict[str, Any]:
        file_path = self._path(path)

        if not file_path.exists():
            raise FileNotFoundError(
                f"File does not exist: {file_path}"
            )

        if not file_path.is_file():
            raise IsADirectoryError(
                f"Path is not a file: {file_path}"
            )

        stat = file_path.stat()

        return {
            "path": str(file_path),
            "size": stat.st_size,
            "is_file": True,
            "is_directory": False,
            "created_time": stat.st_ctime,
            "modified_time": stat.st_mtime,
            "accessed_time": stat.st_atime,
        }

    def create_directory(
        self,
        path: str,
    ) -> dict[str, Any]:
        directory_path = self._path(path)

        if directory_path.exists():
            raise FileExistsError(
                f"Path already exists: {directory_path}"
            )

        directory_path.mkdir()

        return {
            "created": True,
            "path": str(directory_path),
        }

    def delete_directory(
        self,
        path: str,
    ) -> dict[str, Any]:
        directory_path = self._path(path)

        if not directory_path.exists():
            raise FileNotFoundError(
                f"Directory does not exist: {directory_path}"
            )

        if not directory_path.is_dir():
            raise NotADirectoryError(
                f"Path is not a directory: {directory_path}"
            )

        # rmdir() is intentionally used instead of shutil.rmtree().
        # This guarantees non-recursive deletion.
        directory_path.rmdir()

        return {
            "deleted": True,
            "path": str(directory_path),
        }

    def list_directory(
        self,
        path: str,
    ) -> dict[str, Any]:
        directory_path = self._path(path)

        if not directory_path.exists():
            raise FileNotFoundError(
                f"Directory does not exist: {directory_path}"
            )

        if not directory_path.is_dir():
            raise NotADirectoryError(
                f"Path is not a directory: {directory_path}"
            )

        entries = sorted(
            entry.name
            for entry in directory_path.iterdir()
        )

        return {
            "path": str(directory_path),
            "entries": entries,
        }

    def path_exists(
        self,
        path: str,
    ) -> dict[str, Any]:
        filesystem_path = self._path(path)

        return {
            "path": str(filesystem_path),
            "exists": filesystem_path.exists(),
        }