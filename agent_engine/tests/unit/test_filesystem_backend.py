import inspect

from agent_engine.automation.agents.filesystem.filesystem_backend import (
    FileSystemBackend,
)


def test_filesystem_backend_is_abstract():
    assert inspect.isabstract(FileSystemBackend)


def test_filesystem_backend_declares_all_required_operations():
    expected_methods = {
        "create_file",
        "delete_file",
        "copy_file",
        "move_file",
        "rename_file",
        "get_file_metadata",
        "create_directory",
        "delete_directory",
        "list_directory",
        "path_exists",
    }

    for method_name in expected_methods:
        assert hasattr(FileSystemBackend, method_name)
        assert getattr(FileSystemBackend, method_name).__isabstractmethod__