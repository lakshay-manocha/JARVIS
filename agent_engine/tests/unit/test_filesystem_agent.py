"""
Unit tests for the M5-L File-System Automation Agent.
"""

from __future__ import annotations

from typing import Any

import pytest

from agent_engine.automation.agents.filesystem.filesystem_agent import (
    FileSystemAutomationAgent,
)
from agent_engine.automation.agents.filesystem.filesystem_backend import (
    FileSystemBackend,
)
from agent_engine.automation.models.lifecycle import AgentLifecycleState
from agent_engine.contracts.action import ActionRequest
from agent_engine.contracts.enums import ActionCategory, ToolType


class FakeFileSystemBackend(FileSystemBackend):
    """
    Minimal fake backend for M5-L4 agent-level testing.

    This backend records calls instead of touching the real filesystem.

    A dedicated reusable fake backend will be introduced in M5-L5.
    """

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def create_file(self, path: str) -> dict[str, Any]:
        self.calls.append(
            {
                "operation": "create_file",
                "parameters": {
                    "path": path,
                },
            }
        )

        return {
            "created": True,
            "path": path,
        }

    def delete_file(self, path: str) -> dict[str, Any]:
        self.calls.append(
            {
                "operation": "delete_file",
                "parameters": {
                    "path": path,
                },
            }
        )

        return {
            "deleted": True,
            "path": path,
        }

    def copy_file(
        self,
        source: str,
        destination: str,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "operation": "copy_file",
                "parameters": {
                    "source": source,
                    "destination": destination,
                },
            }
        )

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
        self.calls.append(
            {
                "operation": "move_file",
                "parameters": {
                    "source": source,
                    "destination": destination,
                },
            }
        )

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
        self.calls.append(
            {
                "operation": "rename_file",
                "parameters": {
                    "path": path,
                    "new_name": new_name,
                },
            }
        )

        return {
            "renamed": True,
            "path": path,
            "new_name": new_name,
        }

    def get_file_metadata(
        self,
        path: str,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "operation": "get_file_metadata",
                "parameters": {
                    "path": path,
                },
            }
        )

        return {
            "path": path,
            "size": 100,
            "is_file": True,
        }

    def create_directory(
        self,
        path: str,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "operation": "create_directory",
                "parameters": {
                    "path": path,
                },
            }
        )

        return {
            "created": True,
            "path": path,
        }

    def delete_directory(
        self,
        path: str,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "operation": "delete_directory",
                "parameters": {
                    "path": path,
                },
            }
        )

        return {
            "deleted": True,
            "path": path,
        }

    def list_directory(
        self,
        path: str,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "operation": "list_directory",
                "parameters": {
                    "path": path,
                },
            }
        )

        return {
            "path": path,
            "entries": [],
        }

    def path_exists(
        self,
        path: str,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "operation": "path_exists",
                "parameters": {
                    "path": path,
                },
            }
        )

        return {
            "path": path,
            "exists": True,
        }


@pytest.fixture
def backend() -> FakeFileSystemBackend:
    return FakeFileSystemBackend()


@pytest.fixture
def agent(
    backend: FakeFileSystemBackend,
) -> FileSystemAutomationAgent:
    return FileSystemAutomationAgent(
        backend=backend
    )


def make_request(
    *,
    task_id: int,
    action: str,
    parameters: dict[str, Any],
) -> ActionRequest:
    return ActionRequest(
        task_id=task_id,
        action=action,
        category=ActionCategory.FILESYSTEM,
        tool=ToolType.FILESYSTEM,
        parameters=parameters,
    )


# ----------------------------------------------------------------------
# Identity and capabilities
# ----------------------------------------------------------------------


def test_agent_identity(
    agent: FileSystemAutomationAgent,
) -> None:
    assert agent.agent_id == "filesystem_agent"

    assert (
        agent.name
        == "File-System Automation Agent"
    )

    assert agent.tool_type == ToolType.FILESYSTEM


def test_agent_supports_all_m5l_actions(
    agent: FileSystemAutomationAgent,
) -> None:
    expected_actions = {
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

    assert agent.capabilities.all_actions() == frozenset(
        expected_actions
    )


# ----------------------------------------------------------------------
# can_execute
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "action",
    [
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
    ],
)
def test_can_execute_supported_actions(
    agent: FileSystemAutomationAgent,
    action: str,
) -> None:
    request = make_request(
        task_id=1,
        action=action,
        parameters={},
    )

    assert agent.can_execute(request) is True


def test_cannot_execute_wrong_tool(
    agent: FileSystemAutomationAgent,
) -> None:
    request = ActionRequest(
        task_id=1,
        action="create_file",
        category=ActionCategory.FILESYSTEM,
        tool=ToolType.DESKTOP,
        parameters={
            "path": "test.txt",
        },
    )

    assert agent.can_execute(request) is False


def test_cannot_execute_wrong_category(
    agent: FileSystemAutomationAgent,
) -> None:
    request = ActionRequest(
        task_id=1,
        action="create_file",
        category=ActionCategory.APPLICATION,
        tool=ToolType.FILESYSTEM,
        parameters={
            "path": "test.txt",
        },
    )

    assert agent.can_execute(request) is False


def test_cannot_execute_unsupported_action(
    agent: FileSystemAutomationAgent,
) -> None:
    request = make_request(
        task_id=1,
        action="unknown_filesystem_action",
        parameters={},
    )

    assert agent.can_execute(request) is False


# ----------------------------------------------------------------------
# File actions
# ----------------------------------------------------------------------


def test_create_file(
    agent: FileSystemAutomationAgent,
    backend: FakeFileSystemBackend,
) -> None:
    request = make_request(
        task_id=1,
        action="create_file",
        parameters={
            "path": "C:\\Temp\\test.txt",
        },
    )

    result = agent.execute(request)

    assert result.success is True
    assert result.action == "create_file"

    assert backend.calls == [
        {
            "operation": "create_file",
            "parameters": {
                "path": "C:\\Temp\\test.txt",
            },
        }
    ]


def test_delete_file(
    agent: FileSystemAutomationAgent,
    backend: FakeFileSystemBackend,
) -> None:
    request = make_request(
        task_id=2,
        action="delete_file",
        parameters={
            "path": "C:\\Temp\\test.txt",
        },
    )

    result = agent.execute(request)

    assert result.success is True

    assert backend.calls == [
        {
            "operation": "delete_file",
            "parameters": {
                "path": "C:\\Temp\\test.txt",
            },
        }
    ]


def test_copy_file(
    agent: FileSystemAutomationAgent,
    backend: FakeFileSystemBackend,
) -> None:
    request = make_request(
        task_id=3,
        action="copy_file",
        parameters={
            "source": "C:\\Temp\\source.txt",
            "destination": "C:\\Temp\\copy.txt",
        },
    )

    result = agent.execute(request)

    assert result.success is True

    assert backend.calls == [
        {
            "operation": "copy_file",
            "parameters": {
                "source": "C:\\Temp\\source.txt",
                "destination": "C:\\Temp\\copy.txt",
            },
        }
    ]


def test_move_file(
    agent: FileSystemAutomationAgent,
    backend: FakeFileSystemBackend,
) -> None:
    request = make_request(
        task_id=4,
        action="move_file",
        parameters={
            "source": "C:\\Temp\\source.txt",
            "destination": "C:\\Temp\\moved.txt",
        },
    )

    result = agent.execute(request)

    assert result.success is True

    assert backend.calls == [
        {
            "operation": "move_file",
            "parameters": {
                "source": "C:\\Temp\\source.txt",
                "destination": "C:\\Temp\\moved.txt",
            },
        }
    ]


def test_rename_file(
    agent: FileSystemAutomationAgent,
    backend: FakeFileSystemBackend,
) -> None:
    request = make_request(
        task_id=5,
        action="rename_file",
        parameters={
            "path": "C:\\Temp\\old.txt",
            "new_name": "new.txt",
        },
    )

    result = agent.execute(request)

    assert result.success is True

    assert backend.calls == [
        {
            "operation": "rename_file",
            "parameters": {
                "path": "C:\\Temp\\old.txt",
                "new_name": "new.txt",
            },
        }
    ]


def test_get_file_metadata(
    agent: FileSystemAutomationAgent,
    backend: FakeFileSystemBackend,
) -> None:
    request = make_request(
        task_id=6,
        action="get_file_metadata",
        parameters={
            "path": "C:\\Temp\\test.txt",
        },
    )

    result = agent.execute(request)

    assert result.success is True
    assert result.output["path"] == "C:\\Temp\\test.txt"
    assert result.output["is_file"] is True

    assert backend.calls == [
        {
            "operation": "get_file_metadata",
            "parameters": {
                "path": "C:\\Temp\\test.txt",
            },
        }
    ]


# ----------------------------------------------------------------------
# Directory actions
# ----------------------------------------------------------------------


def test_create_directory(
    agent: FileSystemAutomationAgent,
    backend: FakeFileSystemBackend,
) -> None:
    request = make_request(
        task_id=7,
        action="create_directory",
        parameters={
            "path": "C:\\Temp\\JARVIS",
        },
    )

    result = agent.execute(request)

    assert result.success is True

    assert backend.calls == [
        {
            "operation": "create_directory",
            "parameters": {
                "path": "C:\\Temp\\JARVIS",
            },
        }
    ]


def test_delete_directory(
    agent: FileSystemAutomationAgent,
    backend: FakeFileSystemBackend,
) -> None:
    request = make_request(
        task_id=8,
        action="delete_directory",
        parameters={
            "path": "C:\\Temp\\JARVIS",
        },
    )

    result = agent.execute(request)

    assert result.success is True

    assert backend.calls == [
        {
            "operation": "delete_directory",
            "parameters": {
                "path": "C:\\Temp\\JARVIS",
            },
        }
    ]


def test_list_directory(
    agent: FileSystemAutomationAgent,
    backend: FakeFileSystemBackend,
) -> None:
    request = make_request(
        task_id=9,
        action="list_directory",
        parameters={
            "path": "C:\\Temp",
        },
    )

    result = agent.execute(request)

    assert result.success is True
    assert result.output["entries"] == []

    assert backend.calls == [
        {
            "operation": "list_directory",
            "parameters": {
                "path": "C:\\Temp",
            },
        }
    ]


def test_path_exists(
    agent: FileSystemAutomationAgent,
    backend: FakeFileSystemBackend,
) -> None:
    request = make_request(
        task_id=10,
        action="path_exists",
        parameters={
            "path": "C:\\Temp\\test.txt",
        },
    )

    result = agent.execute(request)

    assert result.success is True
    assert result.output["exists"] is True

    assert backend.calls == [
        {
            "operation": "path_exists",
            "parameters": {
                "path": "C:\\Temp\\test.txt",
            },
        }
    ]


# ----------------------------------------------------------------------
# Parameter validation
# ----------------------------------------------------------------------


def test_missing_create_file_path(
    agent: FileSystemAutomationAgent,
) -> None:
    request = make_request(
        task_id=11,
        action="create_file",
        parameters={},
    )

    result = agent.execute(request)

    assert result.success is False
    assert result.has_error
    assert "path" in result.error.lower()


def test_missing_copy_source(
    agent: FileSystemAutomationAgent,
) -> None:
    request = make_request(
        task_id=12,
        action="copy_file",
        parameters={
            "destination": "C:\\Temp\\copy.txt",
        },
    )

    result = agent.execute(request)

    assert result.success is False
    assert result.has_error
    assert "source" in result.error.lower()


def test_missing_copy_destination(
    agent: FileSystemAutomationAgent,
) -> None:
    request = make_request(
        task_id=13,
        action="copy_file",
        parameters={
            "source": "C:\\Temp\\source.txt",
        },
    )

    result = agent.execute(request)

    assert result.success is False
    assert result.has_error
    assert "destination" in result.error.lower()


def test_missing_rename_name(
    agent: FileSystemAutomationAgent,
) -> None:
    request = make_request(
        task_id=14,
        action="rename_file",
        parameters={
            "path": "C:\\Temp\\old.txt",
        },
    )

    result = agent.execute(request)

    assert result.success is False
    assert result.has_error
    assert "new_name" in result.error.lower()


def test_invalid_rename_name(
    agent: FileSystemAutomationAgent,
) -> None:
    request = make_request(
        task_id=15,
        action="rename_file",
        parameters={
            "path": "C:\\Temp\\old.txt",
            "new_name": "folder\\new.txt",
        },
    )

    result = agent.execute(request)

    assert result.success is False
    assert result.has_error
    assert "filename" in result.error.lower()


def test_missing_directory_path(
    agent: FileSystemAutomationAgent,
) -> None:
    request = make_request(
        task_id=16,
        action="create_directory",
        parameters={},
    )

    result = agent.execute(request)

    assert result.success is False
    assert result.has_error
    assert "path" in result.error.lower()


# ----------------------------------------------------------------------
# Failure handling
# ----------------------------------------------------------------------


def test_backend_failure_returns_failed_result(
    agent: FileSystemAutomationAgent,
    backend: FakeFileSystemBackend,
) -> None:
    def failing_create_file(
        path: str,
    ) -> dict[str, Any]:
        raise RuntimeError("simulated filesystem failure")

    backend.create_file = failing_create_file  # type: ignore[method-assign]

    request = make_request(
        task_id=17,
        action="create_file",
        parameters={
            "path": "C:\\Temp\\failure.txt",
        },
    )

    result = agent.execute(request)

    assert result.success is False
    assert result.has_error
    assert "simulated filesystem failure" in result.error

    assert (
        result.metadata["failure_type"]
        == "UNKNOWN"
    )

    assert (
        result.metadata["agent_id"]
        == "filesystem_agent"
    )


# ----------------------------------------------------------------------
# Lifecycle
# ----------------------------------------------------------------------


def test_agent_initializes_on_first_execution(
    agent: FileSystemAutomationAgent,
) -> None:
    assert (
        agent.lifecycle_state
        == AgentLifecycleState.CREATED
    )

    request = make_request(
        task_id=18,
        action="create_file",
        parameters={
            "path": "C:\\Temp\\test.txt",
        },
    )

    result = agent.execute(request)

    assert result.success is True

    assert (
        agent.lifecycle_state
        == AgentLifecycleState.READY
    )


def test_agent_cleanup(
    agent: FileSystemAutomationAgent,
) -> None:
    agent.initialize()

    assert (
        agent.lifecycle_state
        == AgentLifecycleState.READY
    )

    agent.cleanup()

    assert (
        agent.lifecycle_state
        == AgentLifecycleState.CLEANED
    )