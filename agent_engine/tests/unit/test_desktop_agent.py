"""
Unit tests for the M5-K Application & Window Automation Agent.
"""

from __future__ import annotations

import pytest

from agent_engine.automation.agents.desktop.desktop_agent import (
    ApplicationWindowAutomationAgent,
)
from agent_engine.automation.agents.desktop.fake_desktop_backend import (
    FakeDesktopBackend,
)
from agent_engine.automation.models.lifecycle import AgentLifecycleState
from agent_engine.contracts.action import ActionRequest
from agent_engine.contracts.enums import ActionCategory, ToolType


@pytest.fixture
def backend() -> FakeDesktopBackend:
    return FakeDesktopBackend()


@pytest.fixture
def agent(
    backend: FakeDesktopBackend,
) -> ApplicationWindowAutomationAgent:
    return ApplicationWindowAutomationAgent(
        backend=backend
    )


def make_request(
    *,
    task_id: int,
    action: str,
    parameters: dict,
) -> ActionRequest:
    return ActionRequest(
        task_id=task_id,
        action=action,
        category=ActionCategory.APPLICATION,
        tool=ToolType.DESKTOP,
        parameters=parameters,
    )


# ----------------------------------------------------------------------
# Identity and capabilities
# ----------------------------------------------------------------------


def test_agent_identity(
    agent: ApplicationWindowAutomationAgent,
) -> None:
    assert agent.agent_id == "desktop_agent"

    assert (
        agent.name
        == "Application & Window Automation Agent"
    )

    assert agent.tool_type == ToolType.DESKTOP


def test_agent_supports_all_m5k_actions(
    agent: ApplicationWindowAutomationAgent,
) -> None:
    expected_actions = {
        "launch_application",
        "close_application",
        "restart_application",
        "terminate_application",
        "focus_window",
        "switch_window",
        "resize_window",
        "position_window",
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
        "launch_application",
        "close_application",
        "restart_application",
        "terminate_application",
        "focus_window",
        "switch_window",
        "resize_window",
        "position_window",
    ],
)
def test_can_execute_supported_actions(
    agent: ApplicationWindowAutomationAgent,
    action: str,
) -> None:
    request = make_request(
        task_id=1,
        action=action,
        parameters={},
    )

    assert agent.can_execute(request) is True


def test_cannot_execute_wrong_tool(
    agent: ApplicationWindowAutomationAgent,
) -> None:
    request = ActionRequest(
        task_id=1,
        action="launch_application",
        category=ActionCategory.APPLICATION,
        tool=ToolType.BROWSER,
        parameters={
            "application": "vscode",
        },
    )

    assert agent.can_execute(request) is False


def test_cannot_execute_wrong_category(
    agent: ApplicationWindowAutomationAgent,
) -> None:
    request = ActionRequest(
        task_id=1,
        action="launch_application",
        category=ActionCategory.BROWSER,
        tool=ToolType.DESKTOP,
        parameters={
            "application": "vscode",
        },
    )

    assert agent.can_execute(request) is False


# ----------------------------------------------------------------------
# Application actions
# ----------------------------------------------------------------------


def test_launch_application(
    agent: ApplicationWindowAutomationAgent,
    backend: FakeDesktopBackend,
) -> None:
    request = make_request(
        task_id=1,
        action="launch_application",
        parameters={
            "application": "VS Code",
        },
    )

    result = agent.execute(request)

    assert result.success is True
    assert result.action == "launch_application"

    assert backend.calls == [
        {
            "operation": "launch_application",
            "parameters": {
                "application": "vscode",
            },
        }
    ]


def test_close_application(
    agent: ApplicationWindowAutomationAgent,
    backend: FakeDesktopBackend,
) -> None:
    request = make_request(
        task_id=2,
        action="close_application",
        parameters={
            "application": "Microsoft Word",
        },
    )

    result = agent.execute(request)

    assert result.success is True

    assert backend.calls == [
        {
            "operation": "close_application",
            "parameters": {
                "application": "word",
            },
        }
    ]


def test_restart_application(
    agent: ApplicationWindowAutomationAgent,
    backend: FakeDesktopBackend,
) -> None:
    request = make_request(
        task_id=3,
        action="restart_application",
        parameters={
            "application": "VS Code",
        },
    )

    result = agent.execute(request)

    assert result.success is True

    assert backend.calls == [
        {
            "operation": "restart_application",
            "parameters": {
                "application": "vscode",
            },
        }
    ]


def test_terminate_application(
    agent: ApplicationWindowAutomationAgent,
    backend: FakeDesktopBackend,
) -> None:
    request = make_request(
        task_id=4,
        action="terminate_application",
        parameters={
            "application": "Notepad",
        },
    )

    result = agent.execute(request)

    assert result.success is True

    assert backend.calls == [
        {
            "operation": "terminate_application",
            "parameters": {
                "application": "notepad",
            },
        }
    ]


# ----------------------------------------------------------------------
# Window actions
# ----------------------------------------------------------------------


def test_focus_window(
    agent: ApplicationWindowAutomationAgent,
    backend: FakeDesktopBackend,
) -> None:
    request = make_request(
        task_id=5,
        action="focus_window",
        parameters={
            "application": "VS Code",
        },
    )

    result = agent.execute(request)

    assert result.success is True

    assert backend.calls == [
        {
            "operation": "focus_window",
            "parameters": {
                "application": "vscode",
            },
        }
    ]


def test_switch_window(
    agent: ApplicationWindowAutomationAgent,
    backend: FakeDesktopBackend,
) -> None:
    request = make_request(
        task_id=6,
        action="switch_window",
        parameters={
            "target": "Microsoft Word",
        },
    )

    result = agent.execute(request)

    assert result.success is True

    assert backend.calls == [
        {
            "operation": "switch_window",
            "parameters": {
                "target": "Microsoft Word",
            },
        }
    ]


def test_resize_window(
    agent: ApplicationWindowAutomationAgent,
    backend: FakeDesktopBackend,
) -> None:
    request = make_request(
        task_id=7,
        action="resize_window",
        parameters={
            "application": "VS Code",
            "width": 1200,
            "height": 800,
        },
    )

    result = agent.execute(request)

    assert result.success is True

    assert backend.calls == [
        {
            "operation": "resize_window",
            "parameters": {
                "application": "vscode",
                "width": 1200,
                "height": 800,
            },
        }
    ]


def test_position_window(
    agent: ApplicationWindowAutomationAgent,
    backend: FakeDesktopBackend,
) -> None:
    request = make_request(
        task_id=8,
        action="position_window",
        parameters={
            "application": "VS Code",
            "x": 100,
            "y": 50,
        },
    )

    result = agent.execute(request)

    assert result.success is True

    assert backend.calls == [
        {
            "operation": "position_window",
            "parameters": {
                "application": "vscode",
                "x": 100,
                "y": 50,
            },
        }
    ]


# ----------------------------------------------------------------------
# Parameter validation
# ----------------------------------------------------------------------


def test_missing_application_parameter(
    agent: ApplicationWindowAutomationAgent,
) -> None:
    request = make_request(
        task_id=9,
        action="launch_application",
        parameters={},
    )

    result = agent.execute(request)

    assert result.success is False
    assert result.has_error
    assert "application" in result.error.lower()


def test_missing_resize_width(
    agent: ApplicationWindowAutomationAgent,
) -> None:
    request = make_request(
        task_id=10,
        action="resize_window",
        parameters={
            "application": "VS Code",
            "height": 800,
        },
    )

    result = agent.execute(request)

    assert result.success is False
    assert "width" in result.error.lower()


def test_invalid_resize_dimension(
    agent: ApplicationWindowAutomationAgent,
) -> None:
    request = make_request(
        task_id=11,
        action="resize_window",
        parameters={
            "application": "VS Code",
            "width": -100,
            "height": 800,
        },
    )

    result = agent.execute(request)

    assert result.success is False
    assert "width" in result.error.lower()


def test_invalid_position_coordinate(
    agent: ApplicationWindowAutomationAgent,
) -> None:
    request = make_request(
        task_id=12,
        action="position_window",
        parameters={
            "application": "VS Code",
            "x": "100",
            "y": 50,
        },
    )

    result = agent.execute(request)

    assert result.success is False
    assert "x" in result.error.lower()


# ----------------------------------------------------------------------
# Lifecycle
# ----------------------------------------------------------------------


def test_agent_initializes_on_first_execution(
    agent: ApplicationWindowAutomationAgent,
) -> None:
    assert agent.lifecycle_state == AgentLifecycleState.CREATED

    request = make_request(
        task_id=13,
        action="launch_application",
        parameters={
            "application": "VS Code",
        },
    )

    result = agent.execute(request)

    assert result.success is True
    assert agent.lifecycle_state == AgentLifecycleState.READY


def test_agent_cleanup(
    agent: ApplicationWindowAutomationAgent,
) -> None:
    agent.initialize()

    assert agent.lifecycle_state == AgentLifecycleState.READY

    agent.cleanup()

    assert agent.lifecycle_state == AgentLifecycleState.CLEANED