from __future__ import annotations

from typing import Any

import pytest

from agent_engine.automation.agents.filesystem.file_controller import (
    FileController,
)
from agent_engine.automation.agents.filesystem.filesystem_backend import (
    FileSystemBackend,
)


class FakeFileSystemBackend(FileSystemBackend):
    """Test backend used to verify FileController delegation."""

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
        return self._record("create_directory", path=path)

    def delete_directory(self, path: str) -> dict[str, Any]:
        return self._record("delete_directory", path=path)

    def list_directory(self, path: str) -> dict[str, Any]:
        return self._record("list_directory", path=path)

    def path_exists(self, path: str) -> dict[str, Any]:
        return self._record("path_exists", path=path)


@pytest.fixture
def backend() -> FakeFileSystemBackend:
    return FakeFileSystemBackend()


@pytest.fixture
def controller(
    backend: FakeFileSystemBackend,
) -> FileController:
    return FileController(backend)


def test_controller_requires_filesystem_backend() -> None:
    with pytest.raises(TypeError, match="backend must be a FileSystemBackend"):
        FileController(object())


def test_create_file_delegates_to_backend(
    controller: FileController,
    backend: FakeFileSystemBackend,
) -> None:
    result = controller.create_file("  C:\\Temp\\test.txt  ")

    assert result["operation"] == "create_file"
    assert backend.calls == [
        {
            "operation": "create_file",
            "parameters": {
                "path": r"C:\Temp\test.txt",
            },
        }
    ]


def test_delete_file_delegates_to_backend(
    controller: FileController,
    backend: FakeFileSystemBackend,
) -> None:
    result = controller.delete_file(r"C:\Temp\test.txt")

    assert result["operation"] == "delete_file"
    assert backend.calls == [
        {
            "operation": "delete_file",
            "parameters": {
                "path": r"C:\Temp\test.txt",
            },
        }
    ]


def test_copy_file_delegates_to_backend(
    controller: FileController,
    backend: FakeFileSystemBackend,
) -> None:
    result = controller.copy_file(
        r"C:\Temp\source.txt",
        r"C:\Temp\backup\source.txt",
    )

    assert result["operation"] == "copy_file"
    assert backend.calls == [
        {
            "operation": "copy_file",
            "parameters": {
                "source": r"C:\Temp\source.txt",
                "destination": r"C:\Temp\backup\source.txt",
            },
        }
    ]


def test_move_file_delegates_to_backend(
    controller: FileController,
    backend: FakeFileSystemBackend,
) -> None:
    result = controller.move_file(
        r"C:\Temp\source.txt",
        r"C:\Temp\archive\source.txt",
    )

    assert result["operation"] == "move_file"
    assert backend.calls == [
        {
            "operation": "move_file",
            "parameters": {
                "source": r"C:\Temp\source.txt",
                "destination": r"C:\Temp\archive\source.txt",
            },
        }
    ]


def test_rename_file_delegates_to_backend(
    controller: FileController,
    backend: FakeFileSystemBackend,
) -> None:
    result = controller.rename_file(
        r"C:\Temp\source.txt",
        "renamed.txt",
    )

    assert result["operation"] == "rename_file"
    assert backend.calls == [
        {
            "operation": "rename_file",
            "parameters": {
                "path": r"C:\Temp\source.txt",
                "new_name": "renamed.txt",
            },
        }
    ]


def test_get_file_metadata_delegates_to_backend(
    controller: FileController,
    backend: FakeFileSystemBackend,
) -> None:
    result = controller.get_file_metadata(r"C:\Temp\source.txt")

    assert result["operation"] == "get_file_metadata"
    assert backend.calls == [
        {
            "operation": "get_file_metadata",
            "parameters": {
                "path": r"C:\Temp\source.txt",
            },
        }
    ]


@pytest.mark.parametrize(
    "method_name",
    [
        "create_file",
        "delete_file",
        "get_file_metadata",
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
def test_single_path_operations_reject_invalid_paths(
    controller: FileController,
    method_name: str,
    invalid_path: object,
) -> None:
    method = getattr(controller, method_name)

    expected_exception = (
        TypeError
        if isinstance(invalid_path, (bool, int)) or invalid_path is None
        else ValueError
    )

    with pytest.raises(expected_exception):
        method(invalid_path)


@pytest.mark.parametrize(
    "method_name",
    [
        "copy_file",
        "move_file",
    ],
)
def test_copy_and_move_reject_invalid_source(
    controller: FileController,
    method_name: str,
) -> None:
    method = getattr(controller, method_name)

    with pytest.raises(ValueError):
        method(
            "   ",
            r"C:\Temp\destination.txt",
        )


@pytest.mark.parametrize(
    "method_name",
    [
        "copy_file",
        "move_file",
    ],
)
def test_copy_and_move_reject_invalid_destination(
    controller: FileController,
    method_name: str,
) -> None:
    method = getattr(controller, method_name)

    with pytest.raises(ValueError):
        method(
            r"C:\Temp\source.txt",
            "   ",
        )


@pytest.mark.parametrize(
    "invalid_name",
    [
        None,
        "",
        "   ",
        ".",
        "..",
        r"C:\Temp\file.txt",
        r"folder\file.txt",
        "folder/file.txt",
        123,
        True,
    ],
)
def test_rename_rejects_invalid_filename(
    controller: FileController,
    invalid_name: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        controller.rename_file(
            r"C:\Temp\source.txt",
            invalid_name,
        )


def test_path_values_are_trimmed(
    controller: FileController,
    backend: FakeFileSystemBackend,
) -> None:
    controller.copy_file(
        r"  C:\Temp\source.txt  ",
        r"  C:\Temp\destination.txt  ",
    )

    assert backend.calls == [
        {
            "operation": "copy_file",
            "parameters": {
                "source": r"C:\Temp\source.txt",
                "destination": r"C:\Temp\destination.txt",
            },
        }
    ]


def test_rename_filename_is_trimmed(
    controller: FileController,
    backend: FakeFileSystemBackend,
) -> None:
    controller.rename_file(
        r"C:\Temp\source.txt",
        "  renamed.txt  ",
    )

    assert backend.calls == [
        {
            "operation": "rename_file",
            "parameters": {
                "path": r"C:\Temp\source.txt",
                "new_name": "renamed.txt",
            },
        }
    ]