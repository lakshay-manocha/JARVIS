from __future__ import annotations

from typing import Any

import pytest

from agent_engine.automation.agents.filesystem.directory_controller import (
    DirectoryController,
)
from agent_engine.automation.agents.filesystem.filesystem_backend import (
    FileSystemBackend,
)


class FakeFileSystemBackend(FileSystemBackend):
    """Test backend used to verify DirectoryController delegation."""

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

    def create_file(self, path: str) -> dict[str, Any]:
        return self._record("create_file", path=path)

    def delete_file(self, path: str) -> dict[str, Any]:
        return self._record("delete_file", path=path)

    def copy_file(
        self,
        source: str,
        destination: str,
    ) -> dict[str, Any]:
        return self._record(
            "copy_file",
            source=source,
            destination=destination,
        )

    def move_file(
        self,
        source: str,
        destination: str,
    ) -> dict[str, Any]:
        return self._record(
            "move_file",
            source=source,
            destination=destination,
        )

    def rename_file(
        self,
        path: str,
        new_name: str,
    ) -> dict[str, Any]:
        return self._record(
            "rename_file",
            path=path,
            new_name=new_name,
        )

    def get_file_metadata(
        self,
        path: str,
    ) -> dict[str, Any]:
        return self._record(
            "get_file_metadata",
            path=path,
        )

    def create_directory(self, path: str) -> dict[str, Any]:
        return self._record(
            "create_directory",
            path=path,
        )

    def delete_directory(self, path: str) -> dict[str, Any]:
        return self._record(
            "delete_directory",
            path=path,
        )

    def list_directory(self, path: str) -> dict[str, Any]:
        return self._record(
            "list_directory",
            path=path,
        )

    def path_exists(self, path: str) -> dict[str, Any]:
        return self._record(
            "path_exists",
            path=path,
        )


@pytest.fixture
def backend() -> FakeFileSystemBackend:
    return FakeFileSystemBackend()


@pytest.fixture
def controller(
    backend: FakeFileSystemBackend,
) -> DirectoryController:
    return DirectoryController(backend)


def test_controller_requires_filesystem_backend() -> None:
    with pytest.raises(TypeError, match="backend must be a FileSystemBackend"):
        DirectoryController(object())


def test_create_directory_delegates_to_backend(
    controller: DirectoryController,
    backend: FakeFileSystemBackend,
) -> None:
    result = controller.create_directory(
        r"  C:\Temp\NewFolder  "
    )

    assert result["operation"] == "create_directory"

    assert backend.calls == [
        {
            "operation": "create_directory",
            "parameters": {
                "path": r"C:\Temp\NewFolder",
            },
        }
    ]


def test_delete_directory_delegates_to_backend(
    controller: DirectoryController,
    backend: FakeFileSystemBackend,
) -> None:
    result = controller.delete_directory(
        r"C:\Temp\OldFolder"
    )

    assert result["operation"] == "delete_directory"

    assert backend.calls == [
        {
            "operation": "delete_directory",
            "parameters": {
                "path": r"C:\Temp\OldFolder",
            },
        }
    ]


def test_list_directory_delegates_to_backend(
    controller: DirectoryController,
    backend: FakeFileSystemBackend,
) -> None:
    result = controller.list_directory(
        r"C:\Temp"
    )

    assert result["operation"] == "list_directory"

    assert backend.calls == [
        {
            "operation": "list_directory",
            "parameters": {
                "path": r"C:\Temp",
            },
        }
    ]


def test_path_exists_delegates_to_backend(
    controller: DirectoryController,
    backend: FakeFileSystemBackend,
) -> None:
    result = controller.path_exists(
        r"C:\Temp\test.txt"
    )

    assert result["operation"] == "path_exists"

    assert backend.calls == [
        {
            "operation": "path_exists",
            "parameters": {
                "path": r"C:\Temp\test.txt",
            },
        }
    ]


@pytest.mark.parametrize(
    "method_name",
    [
        "create_directory",
        "delete_directory",
        "list_directory",
        "path_exists",
    ],
)
@pytest.mark.parametrize(
    "invalid_path",
    [
        None,
        "",
        "   ",
        123,
        True,
        False,
    ],
)
def test_directory_operations_reject_invalid_paths(
    controller: DirectoryController,
    method_name: str,
    invalid_path: object,
) -> None:
    method = getattr(controller, method_name)

    expected_exception = (
        TypeError
        if isinstance(invalid_path, (bool, int))
        or invalid_path is None
        else ValueError
    )

    with pytest.raises(expected_exception):
        method(invalid_path)


def test_create_directory_trims_path(
    controller: DirectoryController,
    backend: FakeFileSystemBackend,
) -> None:
    controller.create_directory(
        r"  C:\Temp\NewFolder  "
    )

    assert backend.calls == [
        {
            "operation": "create_directory",
            "parameters": {
                "path": r"C:\Temp\NewFolder",
            },
        }
    ]


def test_delete_directory_trims_path(
    controller: DirectoryController,
    backend: FakeFileSystemBackend,
) -> None:
    controller.delete_directory(
        r"  C:\Temp\OldFolder  "
    )

    assert backend.calls == [
        {
            "operation": "delete_directory",
            "parameters": {
                "path": r"C:\Temp\OldFolder",
            },
        }
    ]


def test_list_directory_trims_path(
    controller: DirectoryController,
    backend: FakeFileSystemBackend,
) -> None:
    controller.list_directory(
        r"  C:\Temp  "
    )

    assert backend.calls == [
        {
            "operation": "list_directory",
            "parameters": {
                "path": r"C:\Temp",
            },
        }
    ]


def test_path_exists_trims_path(
    controller: DirectoryController,
    backend: FakeFileSystemBackend,
) -> None:
    controller.path_exists(
        r"  C:\Temp\test.txt  "
    )

    assert backend.calls == [
        {
            "operation": "path_exists",
            "parameters": {
                "path": r"C:\Temp\test.txt",
            },
        }
    ]