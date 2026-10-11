from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class FileSystemBackend(ABC):
    """
    Abstract backend contract for JARVIS file-system automation.

    This contract defines the filesystem operations that can be
    implemented by fake or real filesystem backends.

    The backend is intentionally independent of:
    - AutomationAgent
    - ActionRequest
    - Dispatcher
    - Retry / timeout / fallback logic

    Higher layers are responsible for orchestration and execution
    policy.
    """

    @abstractmethod
    def create_file(self, path: str) -> dict[str, Any]:
        """
        Create an empty file at the specified path.
        """
        raise NotImplementedError

    @abstractmethod
    def delete_file(self, path: str) -> dict[str, Any]:
        """
        Delete a file at the specified path.
        """
        raise NotImplementedError

    @abstractmethod
    def copy_file(
        self,
        source: str,
        destination: str,
    ) -> dict[str, Any]:
        """
        Copy a file from source to destination.
        """
        raise NotImplementedError

    @abstractmethod
    def move_file(
        self,
        source: str,
        destination: str,
    ) -> dict[str, Any]:
        """
        Move a file from source to destination.
        """
        raise NotImplementedError

    @abstractmethod
    def rename_file(
        self,
        path: str,
        new_name: str,
    ) -> dict[str, Any]:
        """
        Rename a file while keeping it in the same directory.
        """
        raise NotImplementedError

    @abstractmethod
    def get_file_metadata(
        self,
        path: str,
    ) -> dict[str, Any]:
        """
        Retrieve metadata for a file.
        """
        raise NotImplementedError

    @abstractmethod
    def create_directory(self, path: str) -> dict[str, Any]:
        """
        Create a directory at the specified path.
        """
        raise NotImplementedError

    @abstractmethod
    def delete_directory(self, path: str) -> dict[str, Any]:
        """
        Delete a directory.

        Recursive deletion is not implied by this contract.
        """
        raise NotImplementedError

    @abstractmethod
    def list_directory(self, path: str) -> dict[str, Any]:
        """
        List entries contained in a directory.
        """
        raise NotImplementedError

    @abstractmethod
    def path_exists(self, path: str) -> dict[str, Any]:
        """
        Check whether a filesystem path exists.
        """
        raise NotImplementedError