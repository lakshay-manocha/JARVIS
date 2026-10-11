"""
Tests for the real Windows filesystem backend.

These tests operate on the actual filesystem, but only inside
temporary directories created by pytest/TEMP.

No project files, Desktop files, Documents, or user data are modified.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from agent_engine.automation.agents.filesystem.windows_filesystem_backend import (
    WindowsFileSystemBackend,
)


@pytest.fixture
def backend() -> WindowsFileSystemBackend:
    """Provide a fresh real Windows filesystem backend."""
    return WindowsFileSystemBackend()


@pytest.fixture
def temp_directory():
    """
    Provide an isolated temporary directory on the real filesystem.

    The directory and its contents are automatically removed after
    the test finishes.
    """
    with TemporaryDirectory() as directory:
        yield Path(directory)


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------


def test_backend_can_be_created():
    backend = WindowsFileSystemBackend()

    assert isinstance(backend, WindowsFileSystemBackend)


# ---------------------------------------------------------------------------
# create_file
# ---------------------------------------------------------------------------


def test_create_file(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    file_path = temp_directory / "test.txt"

    result = backend.create_file(str(file_path))

    assert result["created"] is True
    assert result["path"] == str(file_path)
    assert file_path.exists()
    assert file_path.is_file()


def test_create_existing_file_fails(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    file_path = temp_directory / "existing.txt"
    file_path.touch()

    with pytest.raises(FileExistsError):
        backend.create_file(str(file_path))


# ---------------------------------------------------------------------------
# delete_file
# ---------------------------------------------------------------------------


def test_delete_file(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    file_path = temp_directory / "delete.txt"
    file_path.touch()

    result = backend.delete_file(str(file_path))

    assert result["deleted"] is True
    assert result["path"] == str(file_path)
    assert not file_path.exists()


def test_delete_missing_file_fails(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    file_path = temp_directory / "missing.txt"

    with pytest.raises(FileNotFoundError):
        backend.delete_file(str(file_path))


def test_delete_directory_as_file_fails(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    directory_path = temp_directory / "directory"
    directory_path.mkdir()

    with pytest.raises(IsADirectoryError):
        backend.delete_file(str(directory_path))


# ---------------------------------------------------------------------------
# copy_file
# ---------------------------------------------------------------------------


def test_copy_file(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    source = temp_directory / "source.txt"
    destination = temp_directory / "copy.txt"

    source.write_text(
        "JARVIS filesystem test",
        encoding="utf-8",
    )

    result = backend.copy_file(
        str(source),
        str(destination),
    )

    assert result["copied"] is True
    assert result["source"] == str(source)
    assert result["destination"] == str(destination)

    assert source.exists()
    assert destination.exists()
    assert destination.read_text(encoding="utf-8") == (
        "JARVIS filesystem test"
    )


def test_copy_missing_source_fails(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    source = temp_directory / "missing.txt"
    destination = temp_directory / "copy.txt"

    with pytest.raises(FileNotFoundError):
        backend.copy_file(
            str(source),
            str(destination),
        )


def test_copy_directory_as_file_fails(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    source = temp_directory / "source_directory"
    destination = temp_directory / "copy.txt"

    source.mkdir()

    with pytest.raises(IsADirectoryError):
        backend.copy_file(
            str(source),
            str(destination),
        )


def test_copy_existing_destination_fails(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    source = temp_directory / "source.txt"
    destination = temp_directory / "destination.txt"

    source.write_text("source", encoding="utf-8")
    destination.write_text("destination", encoding="utf-8")

    with pytest.raises(FileExistsError):
        backend.copy_file(
            str(source),
            str(destination),
        )

    # Verify that the existing destination was not overwritten.
    assert destination.read_text(encoding="utf-8") == "destination"


# ---------------------------------------------------------------------------
# move_file
# ---------------------------------------------------------------------------


def test_move_file(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    source = temp_directory / "source.txt"
    destination = temp_directory / "moved.txt"

    source.write_text(
        "move test",
        encoding="utf-8",
    )

    result = backend.move_file(
        str(source),
        str(destination),
    )

    assert result["moved"] is True
    assert not source.exists()
    assert destination.exists()
    assert destination.read_text(encoding="utf-8") == "move test"


def test_move_missing_source_fails(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    source = temp_directory / "missing.txt"
    destination = temp_directory / "destination.txt"

    with pytest.raises(FileNotFoundError):
        backend.move_file(
            str(source),
            str(destination),
        )


def test_move_existing_destination_fails(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    source = temp_directory / "source.txt"
    destination = temp_directory / "destination.txt"

    source.write_text("source", encoding="utf-8")
    destination.write_text("destination", encoding="utf-8")

    with pytest.raises(FileExistsError):
        backend.move_file(
            str(source),
            str(destination),
        )

    # Verify that neither file was accidentally destroyed/overwritten.
    assert source.exists()
    assert destination.read_text(encoding="utf-8") == "destination"


# ---------------------------------------------------------------------------
# rename_file
# ---------------------------------------------------------------------------


def test_rename_file(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    source = temp_directory / "old_name.txt"
    source.write_text(
        "rename test",
        encoding="utf-8",
    )

    result = backend.rename_file(
        str(source),
        "new_name.txt",
    )

    destination = temp_directory / "new_name.txt"

    assert result["renamed"] is True
    assert result["path"] == str(source)
    assert result["new_name"] == "new_name.txt"
    assert result["new_path"] == str(destination)

    assert not source.exists()
    assert destination.exists()
    assert destination.read_text(encoding="utf-8") == "rename test"


def test_rename_missing_file_fails(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    source = temp_directory / "missing.txt"

    with pytest.raises(FileNotFoundError):
        backend.rename_file(
            str(source),
            "new_name.txt",
        )


def test_rename_existing_destination_fails(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    source = temp_directory / "source.txt"
    destination = temp_directory / "destination.txt"

    source.write_text("source", encoding="utf-8")
    destination.write_text("destination", encoding="utf-8")

    with pytest.raises(FileExistsError):
        backend.rename_file(
            str(source),
            "destination.txt",
        )

    assert source.exists()
    assert destination.read_text(encoding="utf-8") == "destination"


def test_rename_directory_as_file_fails(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    directory_path = temp_directory / "directory"
    directory_path.mkdir()

    with pytest.raises(IsADirectoryError):
        backend.rename_file(
            str(directory_path),
            "renamed",
        )


# ---------------------------------------------------------------------------
# get_file_metadata
# ---------------------------------------------------------------------------


def test_get_file_metadata(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    file_path = temp_directory / "metadata.txt"
    content = "JARVIS metadata test"

    file_path.write_text(
        content,
        encoding="utf-8",
    )

    result = backend.get_file_metadata(
        str(file_path)
    )

    assert result["path"] == str(file_path)
    assert result["size"] == len(content.encode("utf-8"))
    assert result["is_file"] is True
    assert result["is_directory"] is False

    assert isinstance(
        result["created_time"],
        float,
    )
    assert isinstance(
        result["modified_time"],
        float,
    )
    assert isinstance(
        result["accessed_time"],
        float,
    )


def test_get_metadata_for_missing_file_fails(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    file_path = temp_directory / "missing.txt"

    with pytest.raises(FileNotFoundError):
        backend.get_file_metadata(
            str(file_path)
        )


def test_get_metadata_for_directory_fails(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    directory_path = temp_directory / "directory"
    directory_path.mkdir()

    with pytest.raises(IsADirectoryError):
        backend.get_file_metadata(
            str(directory_path)
        )


# ---------------------------------------------------------------------------
# create_directory
# ---------------------------------------------------------------------------


def test_create_directory(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    directory_path = temp_directory / "new_directory"

    result = backend.create_directory(
        str(directory_path)
    )

    assert result["created"] is True
    assert result["path"] == str(directory_path)
    assert directory_path.exists()
    assert directory_path.is_dir()


def test_create_existing_directory_fails(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    directory_path = temp_directory / "existing"

    directory_path.mkdir()

    with pytest.raises(FileExistsError):
        backend.create_directory(
            str(directory_path)
        )


def test_create_directory_where_file_exists_fails(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    file_path = temp_directory / "existing.txt"
    file_path.touch()

    with pytest.raises(FileExistsError):
        backend.create_directory(
            str(file_path)
        )


# ---------------------------------------------------------------------------
# delete_directory
# ---------------------------------------------------------------------------


def test_delete_empty_directory(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    directory_path = temp_directory / "empty_directory"
    directory_path.mkdir()

    result = backend.delete_directory(
        str(directory_path)
    )

    assert result["deleted"] is True
    assert result["path"] == str(directory_path)
    assert not directory_path.exists()


def test_delete_missing_directory_fails(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    directory_path = temp_directory / "missing"

    with pytest.raises(FileNotFoundError):
        backend.delete_directory(
            str(directory_path)
        )


def test_delete_non_empty_directory_fails(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    directory_path = temp_directory / "non_empty"
    directory_path.mkdir()

    file_path = directory_path / "file.txt"
    file_path.touch()

    with pytest.raises(OSError):
        backend.delete_directory(
            str(directory_path)
        )

    assert directory_path.exists()
    assert file_path.exists()


def test_delete_file_as_directory_fails(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    file_path = temp_directory / "file.txt"
    file_path.touch()

    with pytest.raises(NotADirectoryError):
        backend.delete_directory(
            str(file_path)
        )


# ---------------------------------------------------------------------------
# list_directory
# ---------------------------------------------------------------------------


def test_list_empty_directory(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    directory_path = temp_directory / "empty"
    directory_path.mkdir()

    result = backend.list_directory(
        str(directory_path)
    )

    assert result["path"] == str(directory_path)
    assert result["entries"] == []


def test_list_directory_returns_direct_children(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    directory_path = temp_directory / "root"
    directory_path.mkdir()

    (directory_path / "file.txt").touch()
    (directory_path / "Documents").mkdir()

    result = backend.list_directory(
        str(directory_path)
    )

    assert result["entries"] == [
        "Documents",
        "file.txt",
    ]


def test_list_directory_includes_nested_directory_as_single_entry(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    directory_path = temp_directory / "root"
    nested_directory = directory_path / "Documents"
    nested_file = nested_directory / "nested.txt"

    nested_directory.mkdir(parents=True)
    nested_file.touch()

    result = backend.list_directory(
        str(directory_path)
    )

    assert result["entries"] == [
        "Documents",
    ]


def test_list_missing_directory_fails(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    directory_path = temp_directory / "missing"

    with pytest.raises(FileNotFoundError):
        backend.list_directory(
            str(directory_path)
        )


def test_list_file_as_directory_fails(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    file_path = temp_directory / "file.txt"
    file_path.touch()

    with pytest.raises(NotADirectoryError):
        backend.list_directory(
            str(file_path)
        )


# ---------------------------------------------------------------------------
# path_exists
# ---------------------------------------------------------------------------


def test_path_exists_for_file(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    file_path = temp_directory / "file.txt"
    file_path.touch()

    result = backend.path_exists(
        str(file_path)
    )

    assert result["path"] == str(file_path)
    assert result["exists"] is True


def test_path_exists_for_directory(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    directory_path = temp_directory / "directory"
    directory_path.mkdir()

    result = backend.path_exists(
        str(directory_path)
    )

    assert result["path"] == str(directory_path)
    assert result["exists"] is True


def test_path_exists_for_missing_path(
    backend: WindowsFileSystemBackend,
    temp_directory: Path,
):
    missing_path = temp_directory / "does_not_exist"

    result = backend.path_exists(
        str(missing_path)
    )

    assert result["path"] == str(missing_path)
    assert result["exists"] is False