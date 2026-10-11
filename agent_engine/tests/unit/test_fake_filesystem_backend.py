"""
Unit tests for the M5-L5 Fake Filesystem Backend.
"""

from __future__ import annotations

import pytest

from agent_engine.automation.agents.filesystem.fake_filesystem_backend import (
    FakeFileSystemBackend,
)


@pytest.fixture
def backend() -> FakeFileSystemBackend:
    return FakeFileSystemBackend()


# ----------------------------------------------------------------------
# Initial state
# ----------------------------------------------------------------------


def test_backend_initial_state(
    backend: FakeFileSystemBackend,
) -> None:
    assert backend.calls == []


# ----------------------------------------------------------------------
# File creation
# ----------------------------------------------------------------------


def test_create_file(
    backend: FakeFileSystemBackend,
) -> None:
    result = backend.create_file(
        "C:\\Temp\\test.txt"
    )

    assert result == {
        "created": True,
        "path": "C:\\Temp\\test.txt",
    }

    assert backend.path_exists(
        "C:\\Temp\\test.txt"
    )["exists"] is True


def test_create_duplicate_file_fails(
    backend: FakeFileSystemBackend,
) -> None:
    backend.create_file(
        "C:\\Temp\\test.txt"
    )

    with pytest.raises(FileExistsError):
        backend.create_file(
            "C:\\Temp\\test.txt"
        )


# ----------------------------------------------------------------------
# File deletion
# ----------------------------------------------------------------------


def test_delete_file(
    backend: FakeFileSystemBackend,
) -> None:
    path = "C:\\Temp\\test.txt"

    backend.create_file(path)

    result = backend.delete_file(path)

    assert result == {
        "deleted": True,
        "path": path,
    }

    assert backend.path_exists(path)["exists"] is False


def test_delete_missing_file_fails(
    backend: FakeFileSystemBackend,
) -> None:
    with pytest.raises(FileNotFoundError):
        backend.delete_file(
            "C:\\Temp\\missing.txt"
        )


# ----------------------------------------------------------------------
# File copy
# ----------------------------------------------------------------------


def test_copy_file(
    backend: FakeFileSystemBackend,
) -> None:
    source = "C:\\Temp\\source.txt"
    destination = "C:\\Temp\\copy.txt"

    backend.create_file(source)

    result = backend.copy_file(
        source,
        destination,
    )

    assert result == {
        "copied": True,
        "source": source,
        "destination": destination,
    }

    assert backend.path_exists(source)["exists"] is True
    assert backend.path_exists(destination)["exists"] is True


def test_copy_missing_file_fails(
    backend: FakeFileSystemBackend,
) -> None:
    with pytest.raises(FileNotFoundError):
        backend.copy_file(
            "C:\\Temp\\missing.txt",
            "C:\\Temp\\copy.txt",
        )


def test_copy_existing_destination_fails(
    backend: FakeFileSystemBackend,
) -> None:
    source = "C:\\Temp\\source.txt"
    destination = "C:\\Temp\\destination.txt"

    backend.create_file(source)
    backend.create_file(destination)

    with pytest.raises(FileExistsError):
        backend.copy_file(
            source,
            destination,
        )


# ----------------------------------------------------------------------
# File move
# ----------------------------------------------------------------------


def test_move_file(
    backend: FakeFileSystemBackend,
) -> None:
    source = "C:\\Temp\\source.txt"
    destination = "C:\\Temp\\moved.txt"

    backend.create_file(source)

    result = backend.move_file(
        source,
        destination,
    )

    assert result == {
        "moved": True,
        "source": source,
        "destination": destination,
    }

    assert backend.path_exists(source)["exists"] is False
    assert backend.path_exists(destination)["exists"] is True


def test_move_missing_file_fails(
    backend: FakeFileSystemBackend,
) -> None:
    with pytest.raises(FileNotFoundError):
        backend.move_file(
            "C:\\Temp\\missing.txt",
            "C:\\Temp\\moved.txt",
        )


def test_move_existing_destination_fails(
    backend: FakeFileSystemBackend,
) -> None:
    source = "C:\\Temp\\source.txt"
    destination = "C:\\Temp\\destination.txt"

    backend.create_file(source)
    backend.create_file(destination)

    with pytest.raises(FileExistsError):
        backend.move_file(
            source,
            destination,
        )


# ----------------------------------------------------------------------
# File rename
# ----------------------------------------------------------------------


def test_rename_file(
    backend: FakeFileSystemBackend,
) -> None:
    path = "C:\\Temp\\old.txt"
    new_name = "new.txt"
    expected_path = "C:\\Temp\\new.txt"

    backend.create_file(path)

    result = backend.rename_file(
        path,
        new_name,
    )

    assert result == {
        "renamed": True,
        "path": path,
        "new_name": new_name,
        "new_path": expected_path,
    }

    assert backend.path_exists(path)["exists"] is False
    assert backend.path_exists(
        expected_path
    )["exists"] is True


def test_rename_missing_file_fails(
    backend: FakeFileSystemBackend,
) -> None:
    with pytest.raises(FileNotFoundError):
        backend.rename_file(
            "C:\\Temp\\missing.txt",
            "new.txt",
        )


def test_rename_existing_destination_fails(
    backend: FakeFileSystemBackend,
) -> None:
    path = "C:\\Temp\\old.txt"
    destination = "C:\\Temp\\new.txt"

    backend.create_file(path)
    backend.create_file(destination)

    with pytest.raises(FileExistsError):
        backend.rename_file(
            path,
            "new.txt",
        )


# ----------------------------------------------------------------------
# File metadata
# ----------------------------------------------------------------------


def test_get_file_metadata(
    backend: FakeFileSystemBackend,
) -> None:
    path = "C:\\Temp\\test.txt"

    backend.create_file(path)

    metadata = backend.get_file_metadata(path)

    assert metadata == {
        "path": path,
        "size": 0,
        "is_file": True,
    }


def test_get_missing_file_metadata_fails(
    backend: FakeFileSystemBackend,
) -> None:
    with pytest.raises(FileNotFoundError):
        backend.get_file_metadata(
            "C:\\Temp\\missing.txt"
        )


# ----------------------------------------------------------------------
# Directory creation
# ----------------------------------------------------------------------


def test_create_directory(
    backend: FakeFileSystemBackend,
) -> None:
    path = "C:\\Temp\\JARVIS"

    result = backend.create_directory(path)

    assert result == {
        "created": True,
        "path": path,
    }

    assert backend.path_exists(path)["exists"] is True


def test_create_duplicate_directory_fails(
    backend: FakeFileSystemBackend,
) -> None:
    path = "C:\\Temp\\JARVIS"

    backend.create_directory(path)

    with pytest.raises(FileExistsError):
        backend.create_directory(path)


# ----------------------------------------------------------------------
# Directory deletion
# ----------------------------------------------------------------------


def test_delete_directory(
    backend: FakeFileSystemBackend,
) -> None:
    path = "C:\\Temp\\JARVIS"

    backend.create_directory(path)

    result = backend.delete_directory(path)

    assert result == {
        "deleted": True,
        "path": path,
    }

    assert backend.path_exists(path)["exists"] is False


def test_delete_missing_directory_fails(
    backend: FakeFileSystemBackend,
) -> None:
    with pytest.raises(FileNotFoundError):
        backend.delete_directory(
            "C:\\Temp\\Missing"
        )


def test_delete_non_empty_directory_fails(
    backend: FakeFileSystemBackend,
) -> None:
    directory = "C:\\Temp\\JARVIS"
    file_path = "C:\\Temp\\JARVIS\\test.txt"

    backend.create_directory(directory)
    backend.create_file(file_path)

    with pytest.raises(OSError):
        backend.delete_directory(directory)


# ----------------------------------------------------------------------
# Directory listing
# ----------------------------------------------------------------------


def test_list_empty_directory(
    backend: FakeFileSystemBackend,
) -> None:
    path = "C:\\Temp\\JARVIS"

    backend.create_directory(path)

    result = backend.list_directory(path)

    assert result == {
        "path": path,
        "entries": [],
    }


def test_list_directory_returns_direct_children(
    backend: FakeFileSystemBackend,
) -> None:
    directory = "C:\\Temp\\JARVIS"

    backend.create_directory(directory)
    backend.create_file(
        "C:\\Temp\\JARVIS\\alpha.txt"
    )
    backend.create_file(
        "C:\\Temp\\JARVIS\\beta.txt"
    )
    backend.create_directory(
        "C:\\Temp\\JARVIS\\Documents"
    )

    result = backend.list_directory(directory)

    assert result["path"] == directory

    assert result["entries"] == [
        "Documents",
        "alpha.txt",
        "beta.txt",
    ]


def test_list_directory_does_not_include_nested_entries(
    backend: FakeFileSystemBackend,
) -> None:
    directory = "C:\\Temp\\JARVIS"

    backend.create_directory(directory)
    backend.create_directory(
        "C:\\Temp\\JARVIS\\Documents"
    )
    backend.create_file(
        "C:\\Temp\\JARVIS\\Documents\\nested.txt"
    )

    result = backend.list_directory(directory)

    assert result["entries"] == [
        "Documents",
    ]


def test_list_missing_directory_fails(
    backend: FakeFileSystemBackend,
) -> None:
    with pytest.raises(FileNotFoundError):
        backend.list_directory(
            "C:\\Temp\\Missing"
        )


# ----------------------------------------------------------------------
# Path existence
# ----------------------------------------------------------------------


def test_path_exists_for_file(
    backend: FakeFileSystemBackend,
) -> None:
    path = "C:\\Temp\\test.txt"

    backend.create_file(path)

    result = backend.path_exists(path)

    assert result == {
        "path": path,
        "exists": True,
    }


def test_path_exists_for_directory(
    backend: FakeFileSystemBackend,
) -> None:
    path = "C:\\Temp\\JARVIS"

    backend.create_directory(path)

    result = backend.path_exists(path)

    assert result == {
        "path": path,
        "exists": True,
    }


def test_path_exists_for_missing_path(
    backend: FakeFileSystemBackend,
) -> None:
    result = backend.path_exists(
        "C:\\Temp\\missing.txt"
    )

    assert result == {
        "path": "C:\\Temp\\missing.txt",
        "exists": False,
    }


# ----------------------------------------------------------------------
# Call tracking
# ----------------------------------------------------------------------


def test_backend_records_operations(
    backend: FakeFileSystemBackend,
) -> None:
    file_path = "C:\\Temp\\test.txt"

    backend.create_file(file_path)
    backend.get_file_metadata(file_path)
    backend.path_exists(file_path)

    assert backend.calls == [
        {
            "operation": "create_file",
            "parameters": {
                "path": file_path,
            },
        },
        {
            "operation": "get_file_metadata",
            "parameters": {
                "path": file_path,
            },
        },
        {
            "operation": "path_exists",
            "parameters": {
                "path": file_path,
            },
        },
    ]


# ----------------------------------------------------------------------
# Fake backend isolation
# ----------------------------------------------------------------------


def test_backend_does_not_require_real_filesystem(
    backend: FakeFileSystemBackend,
) -> None:
    path = "C:\\This\\Path\\Does\\Not\\Need\\To\\Exist\\test.txt"

    result = backend.create_file(path)

    assert result["created"] is True
    assert backend.path_exists(path)["exists"] is True