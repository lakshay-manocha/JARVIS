"""
===============================================================================
File Name   : test_action_request_builder.py
Module      : Automation Engine Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Unit tests for ActionRequestBuilder.

These tests verify the M5-E.1 integration boundary between the Agent Brain
InterpretedTask model and the Automation Engine ActionRequest contract.

Author      : Team Agent
===============================================================================
"""

import pytest

from agent_engine.agent_brain.models.interpreted_task import InterpretedTask
from agent_engine.automation.integration.action_request_builder import (
    ActionRequestBuilder,
)
from agent_engine.contracts.action import ActionRequest
from agent_engine.contracts.enums import ActionCategory, ToolType


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def builder() -> ActionRequestBuilder:
    """Return a fresh ActionRequestBuilder."""
    return ActionRequestBuilder()


@pytest.fixture
def interpreted_task() -> InterpretedTask:
    """Return a valid browser task."""
    return InterpretedTask(
        task_id=1,
        original_text="Open example website",
        normalized_text="open example website",
        action="open_url",
        tool="browser_agent",
        parameters={
            "url": "https://example.com",
        },
        metadata={
            "source": "level_1",
        },
    )


# =============================================================================
# Basic Build Tests
# =============================================================================

def test_build_returns_action_request(
    builder,
    interpreted_task,
):
    """Builder should return an ActionRequest."""
    result = builder.build(interpreted_task)

    assert isinstance(result, ActionRequest)


def test_task_id_is_preserved(
    builder,
    interpreted_task,
):
    """Task ID should be copied unchanged."""
    result = builder.build(interpreted_task)

    assert result.task_id == 1


def test_action_is_preserved_and_normalized(
    builder,
):
    """Action should be normalized before entering Automation Engine."""
    task = InterpretedTask(
        task_id=1,
        original_text="Open website",
        normalized_text="open website",
        action="  OPEN_URL  ",
        tool="browser_agent",
    )

    result = builder.build(task)

    assert result.action == "open_url"


def test_tool_is_resolved(
    builder,
    interpreted_task,
):
    """Tool string should be converted into ToolType."""
    result = builder.build(interpreted_task)

    assert result.tool == ToolType.BROWSER

def test_mouse_tool_is_resolved(
    builder,
):
    """Mouse tool should resolve to ToolType.MOUSE."""

    task = InterpretedTask(
        task_id=1,
        original_text="Move mouse",
        normalized_text="move mouse",
        action="move_mouse",
        tool="mouse_agent",
    )
    result = builder.build(task)

    assert result.tool == ToolType.MOUSE

def test_browser_action_category_is_resolved(
    builder,
    interpreted_task,
):
    """Browser actions should receive the BROWSER category."""
    result = builder.build(interpreted_task)

    assert result.category == ActionCategory.BROWSER


# =============================================================================
# Parameter / Metadata Tests
# =============================================================================

def test_parameters_are_preserved(
    builder,
    interpreted_task,
):
    """Task parameters should be copied to ActionRequest."""
    result = builder.build(interpreted_task)

    assert result.parameters == {
        "url": "https://example.com",
    }


def test_metadata_is_preserved(
    builder,
    interpreted_task,
):
    """Task metadata should be copied to ActionRequest."""
    result = builder.build(interpreted_task)

    assert result.metadata == {
        "source": "level_1",
    }


def test_timeout_is_preserved(
    builder,
    interpreted_task,
):
    """Explicit timeout should be copied to ActionRequest."""
    result = builder.build(
        interpreted_task,
        timeout_seconds=30,
    )

    assert result.timeout_seconds == 30


# =============================================================================
# Validation Tests
# =============================================================================

def test_missing_action_is_rejected(
    builder,
):
    """A task without an action should be rejected."""
    task = InterpretedTask(
        task_id=1,
        original_text="Open website",
        normalized_text="open website",
        tool="browser_agent",
    )

    with pytest.raises(ValueError, match="valid action"):
        builder.build(task)


def test_missing_tool_is_rejected(
    builder,
):
    """A task without a tool should be rejected."""
    task = InterpretedTask(
        task_id=1,
        original_text="Open website",
        normalized_text="open website",
        action="open_url",
    )

    with pytest.raises(ValueError, match="valid tool"):
        builder.build(task)


def test_invalid_tool_is_rejected(
    builder,
):
    """An unsupported tool should be rejected."""
    task = InterpretedTask(
        task_id=1,
        original_text="Open website",
        normalized_text="open website",
        action="open_url",
        tool="unknown_agent",
    )

    with pytest.raises(ValueError, match="Unsupported automation tool"):
        builder.build(task)


def test_invalid_task_type_is_rejected(
    builder,
):
    """Builder should only accept InterpretedTask objects."""
    with pytest.raises(TypeError, match="InterpretedTask"):
        builder.build(
            {
                "task_id": 1,
                "action": "open_url",
            }
        )


# =============================================================================
# Category Resolution Tests
# =============================================================================

@pytest.mark.parametrize(
    ("action", "expected_category"),
    [
        # Browser
        ("open_url", ActionCategory.BROWSER),
        ("search", ActionCategory.BROWSER),

        # Keyboard
        ("type_text", ActionCategory.KEYBOARD),
        ("press_key", ActionCategory.KEYBOARD),

        # Mouse
        ("move_mouse", ActionCategory.MOUSE),
        ("click", ActionCategory.MOUSE),
        ("double_click", ActionCategory.MOUSE),
        ("right_click", ActionCategory.MOUSE),
        ("mouse_down", ActionCategory.MOUSE),
        ("mouse_up", ActionCategory.MOUSE),
        ("scroll", ActionCategory.MOUSE),

        # Screen
        ("take_screenshot", ActionCategory.SCREEN),
        ("capture_screen", ActionCategory.SCREEN),
        ("capture_region", ActionCategory.SCREEN),
        ("get_screen_size", ActionCategory.SCREEN),
        ("locate_text", ActionCategory.SCREEN),
        ("locate_element", ActionCategory.SCREEN),
        ("detect_visible_elements", ActionCategory.SCREEN),

        # Filesystem — M5-L
        ("create_file", ActionCategory.FILESYSTEM),
        ("delete_file", ActionCategory.FILESYSTEM),
        ("copy_file", ActionCategory.FILESYSTEM),
        ("move_file", ActionCategory.FILESYSTEM),
        ("rename_file", ActionCategory.FILESYSTEM),
        ("get_file_metadata", ActionCategory.FILESYSTEM),
        ("create_directory", ActionCategory.FILESYSTEM),
        ("delete_directory", ActionCategory.FILESYSTEM),
        ("list_directory", ActionCategory.FILESYSTEM),
        ("path_exists", ActionCategory.FILESYSTEM),
        # Application fallback
        ("open_application", ActionCategory.APPLICATION),
    ],
)

def test_action_category_mapping(
    builder,
    action,
    expected_category,
):
    """Supported Level-1 actions should map to the expected category."""

    task = InterpretedTask(
        task_id=1,
        original_text=action,
        normalized_text=action,
        action=action,
        tool="browser_agent",
    )

    result = builder.build(task)

    assert result.category == expected_category

def test_mouse_action_request_is_built_correctly(
    builder,
):
    """Mouse task should be converted into a valid mouse ActionRequest."""

    task = InterpretedTask(
        task_id=10,
        original_text="Move mouse to 500, 300",
        normalized_text="move mouse to 500, 300",
        action="move_mouse",
        tool="mouse_agent",
        parameters={
            "x": 500,
            "y": 300,
        },
        metadata={
            "source": "m5_j",
        },
    )

    result = builder.build(task)

    assert isinstance(result, ActionRequest)

    assert result.task_id == 10
    assert result.action == "move_mouse"
    assert result.category == ActionCategory.MOUSE
    assert result.tool == ToolType.MOUSE

    assert result.parameters == {
        "x": 500,
        "y": 300,
    }

    assert result.metadata == {
        "source": "m5_j",
    }
# =============================================================================
# M5-K Application & Window Automation Integration Tests
# =============================================================================

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
def test_m5_k_actions_resolve_to_desktop_application_contract(
    builder,
    action,
):
    """
    M5-K application/window actions should resolve to the
    APPLICATION category and DESKTOP automation tool.
    """

    task = InterpretedTask(
        task_id=100,
        original_text=action,
        normalized_text=action,
        action=action,
        tool="desktop_agent",
    )

    result = builder.build(task)

    assert isinstance(result, ActionRequest)

    assert result.action == action
    assert result.category == ActionCategory.APPLICATION
    assert result.tool == ToolType.DESKTOP


def test_m5_k_launch_application_request(
    builder,
):
    """Launch application parameters should be preserved."""

    task = InterpretedTask(
        task_id=101,
        original_text="Launch Notepad",
        normalized_text="launch notepad",
        action="launch_application",
        tool="desktop_agent",
        parameters={
            "application": "notepad",
        },
        metadata={
            "source": "m5_k",
        },
    )

    result = builder.build(task)

    assert result.task_id == 101
    assert result.action == "launch_application"
    assert result.category == ActionCategory.APPLICATION
    assert result.tool == ToolType.DESKTOP

    assert result.parameters == {
        "application": "notepad",
    }

    assert result.metadata == {
        "source": "m5_k",
    }


def test_m5_k_resize_window_request(
    builder,
):
    """Resize window parameters should be preserved exactly."""

    task = InterpretedTask(
        task_id=102,
        original_text="Resize Notepad window",
        normalized_text="resize notepad window",
        action="resize_window",
        tool="desktop_agent",
        parameters={
            "application": "notepad",
            "width": 1200,
            "height": 800,
        },
        metadata={
            "source": "m5_k",
        },
    )

    result = builder.build(
        task,
        timeout_seconds=30,
    )

    assert result.task_id == 102
    assert result.action == "resize_window"
    assert result.category == ActionCategory.APPLICATION
    assert result.tool == ToolType.DESKTOP

    assert result.parameters == {
        "application": "notepad",
        "width": 1200,
        "height": 800,
    }

    assert result.timeout_seconds == 30

    assert result.metadata == {
        "source": "m5_k",
    }


def test_m5_k_position_window_request(
    builder,
):
    """Position window parameters should be preserved exactly."""

    task = InterpretedTask(
        task_id=103,
        original_text="Move Notepad window",
        normalized_text="move notepad window",
        action="position_window",
        tool="desktop_agent",
        parameters={
            "application": "notepad",
            "x": 100,
            "y": 50,
        },
        metadata={
            "source": "m5_k",
        },
    )

    result = builder.build(task)

    assert result.task_id == 103
    assert result.action == "position_window"
    assert result.category == ActionCategory.APPLICATION
    assert result.tool == ToolType.DESKTOP

    assert result.parameters == {
        "application": "notepad",
        "x": 100,
        "y": 50,
    }

    assert result.metadata == {
        "source": "m5_k",
    }

def test_m5_l_filesystem_action_request_is_built_correctly(builder):
    """M5-L filesystem task should produce a valid ActionRequest."""

    task = InterpretedTask(
        task_id=101,
        original_text="create a file",
        normalized_text="create a file",
        action="create_file",
        tool="filesystem_agent",
        parameters={
            "path": r"C:\temp\jarvis_test.txt",
        },
        metadata={
            "source": "m5_l",
        },
    )

    result = builder.build(
        task,
        timeout_seconds=15.0,
    )

    assert result.task_id == 101
    assert result.action == "create_file"
    assert result.tool == ToolType.FILESYSTEM
    assert result.category == ActionCategory.FILESYSTEM
    assert result.parameters == {
        "path": r"C:\temp\jarvis_test.txt",
    }
    assert result.metadata == {
        "source": "m5_l",
    }
    assert result.timeout_seconds == 15.0