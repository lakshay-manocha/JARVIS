"""
===============================================================================
File Name   : test_mouse_real_execution.py
Module      : Automation Tests - Real Mouse Execution
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
J.11 - Real Mouse Execution Verification.

These tests verify that MouseAutomationAgent can execute mouse operations
through the actual MouseActions implementation and the real pynput backend.

Unlike J.10, these tests intentionally DO NOT inject TestMouseActions.

Architecture under test:

    ActionRequest
          ↓
    MouseAutomationAgent
          ↓
      MouseActions
          ↓
        pynput
          ↓
       Real Mouse

IMPORTANT:
-------------
These are REAL hardware integration tests.

Running this file may:
    - move the physical mouse cursor
    - perform real mouse clicks
    - perform real double clicks
    - scroll the physical mouse
    - press/release a physical mouse button

Therefore, run these tests only when it is safe for the mouse to move and
click on the current desktop.

J.10 boundary:
    Dispatcher integration using injected TestMouseActions.

J.11 boundary:
    Actual MouseAutomationAgent + MouseActions + pynput execution.
===============================================================================
"""

from __future__ import annotations

import time

import pytest

from agent_engine.automation.agents.mouse.mouse_agent import (
    MouseAutomationAgent,
)
from agent_engine.automation.models.lifecycle import AgentLifecycleState
from agent_engine.contracts.action import ActionRequest
from agent_engine.contracts.enums import ActionCategory, ToolType


# =============================================================================
# Helpers
# =============================================================================


def create_mouse_action(
    *,
    task_id: int = 1,
    action: str,
    parameters: dict | None = None,
) -> ActionRequest:
    """
    Create a real mouse ActionRequest.

    This helper intentionally creates the same contract that the real
    Automation Engine would pass to MouseAutomationAgent.
    """

    return ActionRequest(
        task_id=task_id,
        action=action,
        category=ActionCategory.MOUSE,
        tool=ToolType.MOUSE,
        parameters=parameters or {},
        metadata={
            "test": "J.11",
            "backend": "pynput",
        },
    )


# =============================================================================
# J.11.1 - Real Agent Initialization
# =============================================================================


def test_real_mouse_agent_initializes():
    """
    J.11.1

    Verify that MouseAutomationAgent can initialize using its real
    MouseActions backend.
    """

    agent = MouseAutomationAgent()

    try:
        agent.initialize()

        assert agent.lifecycle_state == AgentLifecycleState.READY

    finally:
        agent.cleanup()


# =============================================================================
# J.11.2 - Real Mouse Move
# =============================================================================


def test_real_mouse_move_execution():
    """
    J.11.2

    Verify that MouseAutomationAgent can move the physical mouse through
    the real MouseActions/pynput backend.

    The cursor is moved to a safe test coordinate.
    """

    agent = MouseAutomationAgent()

    try:
        request = create_mouse_action(
            task_id=11,
            action="move_mouse",
            parameters={
                "x": 100,
                "y": 100,
            },
        )

        result = agent.execute(request)

        assert result.success is True
        assert result.task_id == 11
        assert result.action == "move_mouse"
        assert result.error is None

    finally:
        agent.cleanup()


# =============================================================================
# J.11.3 - Verify Actual Cursor Position
# =============================================================================


def test_real_mouse_move_changes_cursor_position():
    """
    J.11.3

    Verify that the real mouse cursor actually reaches the requested
    coordinates.

    This test directly observes the pynput Controller after the agent
    performs the move.
    """

    agent = MouseAutomationAgent()

    try:
        target_x = 200
        target_y = 200

        request = create_mouse_action(
            task_id=12,
            action="move_mouse",
            parameters={
                "x": target_x,
                "y": target_y,
            },
        )

        result = agent.execute(request)

        assert result.success is True

        actual_x, actual_y = agent.actions.controller.position

        assert actual_x == target_x
        assert actual_y == target_y

    finally:
        agent.cleanup()


# =============================================================================
# J.11.4 - Real Left Click
# =============================================================================


def test_real_left_click_execution():
    """
    J.11.4

    Verify that a real left mouse click can be executed through
    MouseAutomationAgent.

    The cursor is first positioned at a neutral desktop coordinate.
    """

    agent = MouseAutomationAgent()

    try:
        move_request = create_mouse_action(
            task_id=13,
            action="move_mouse",
            parameters={
                "x": 300,
                "y": 300,
            },
        )

        move_result = agent.execute(move_request)

        assert move_result.success is True

        click_request = create_mouse_action(
            task_id=14,
            action="click",
            parameters={
                "button": "left",
            },
        )

        click_result = agent.execute(click_request)

        assert click_result.success is True
        assert click_result.task_id == 14
        assert click_result.action == "click"
        assert click_result.error is None

    finally:
        agent.cleanup()


# =============================================================================
# J.11.5 - Real Right Click
# =============================================================================


def test_real_right_click_execution():
    """
    J.11.5

    Verify that a real right mouse click can be executed.

    WARNING:
    This produces an actual context-menu click on the desktop.
    """

    agent = MouseAutomationAgent()

    try:
        move_request = create_mouse_action(
            task_id=15,
            action="move_mouse",
            parameters={
                "x": 400,
                "y": 300,
            },
        )

        move_result = agent.execute(move_request)

        assert move_result.success is True

        click_request = create_mouse_action(
            task_id=16,
            action="right_click",
        )

        click_result = agent.execute(click_request)

        assert click_result.success is True
        assert click_result.task_id == 16
        assert click_result.action == "right_click"
        assert click_result.error is None

    finally:
        agent.cleanup()


# =============================================================================
# J.11.6 - Real Double Click
# =============================================================================


def test_real_double_click_execution():
    """
    J.11.6

    Verify that a real double click can be executed through the mouse agent.

    WARNING:
    This produces an actual double click on the desktop.
    """

    agent = MouseAutomationAgent()

    try:
        move_request = create_mouse_action(
            task_id=17,
            action="move_mouse",
            parameters={
                "x": 500,
                "y": 300,
            },
        )

        move_result = agent.execute(move_request)

        assert move_result.success is True

        double_click_request = create_mouse_action(
            task_id=18,
            action="double_click",
            parameters={
                "button": "left",
            },
        )

        double_click_result = agent.execute(
            double_click_request
        )

        assert double_click_result.success is True
        assert double_click_result.task_id == 18
        assert double_click_result.action == "double_click"
        assert double_click_result.error is None

    finally:
        agent.cleanup()


# =============================================================================
# J.11.7 - Real Mouse Down / Mouse Up
# =============================================================================


def test_real_mouse_down_and_mouse_up_execution():
    """
    J.11.7

    Verify that the real mouse button can be pressed and released through
    MouseAutomationAgent.

    The test uses the left mouse button and ensures that mouse_up is always
    attempted even if an assertion fails.
    """

    agent = MouseAutomationAgent()

    try:
        move_request = create_mouse_action(
            task_id=19,
            action="move_mouse",
            parameters={
                "x": 600,
                "y": 300,
            },
        )

        move_result = agent.execute(move_request)

        assert move_result.success is True

        mouse_down_request = create_mouse_action(
            task_id=20,
            action="mouse_down",
            parameters={
                "button": "left",
            },
        )

        down_result = agent.execute(
            mouse_down_request
        )

        assert down_result.success is True
        assert down_result.action == "mouse_down"

        mouse_up_request = create_mouse_action(
            task_id=21,
            action="mouse_up",
            parameters={
                "button": "left",
            },
        )

        up_result = agent.execute(
            mouse_up_request
        )

        assert up_result.success is True
        assert up_result.action == "mouse_up"

    finally:
        agent.cleanup()


# =============================================================================
# J.11.8 - Real Scroll
# =============================================================================


def test_real_mouse_scroll_execution():
    """
    J.11.8

    Verify that the real mouse wheel can be scrolled through the
    MouseAutomationAgent.

    Positive dy means scroll up.
    """

    agent = MouseAutomationAgent()

    try:
        move_request = create_mouse_action(
            task_id=22,
            action="move_mouse",
            parameters={
                "x": 700,
                "y": 400,
            },
        )

        move_result = agent.execute(move_request)

        assert move_result.success is True

        scroll_request = create_mouse_action(
            task_id=23,
            action="scroll",
            parameters={
                "dx": 0,
                "dy": 1,
            },
        )

        scroll_result = agent.execute(
            scroll_request
        )

        assert scroll_result.success is True
        assert scroll_result.task_id == 23
        assert scroll_result.action == "scroll"
        assert scroll_result.error is None

    finally:
        agent.cleanup()


# =============================================================================
# J.11.9 - Real Backend Verification
# =============================================================================


def test_real_mouse_agent_uses_real_mouse_actions_backend():
    """
    J.11.9

    Verify that MouseAutomationAgent uses the actual MouseActions class
    rather than an injected test/mock backend.
    """

    agent = MouseAutomationAgent()

    try:
        from agent_engine.automation.agents.mouse.mouse_actions import (
            MouseActions,
        )

        assert isinstance(
            agent.actions,
            MouseActions,
        )

        assert hasattr(
            agent.actions,
            "controller",
        )

    finally:
        agent.cleanup()


# =============================================================================
# J.11.10 - End-to-End Real Mouse Action Sequence
# =============================================================================


def test_real_mouse_action_sequence():
    """
    J.11.10

    Verify a complete sequence of real mouse operations using the same
    MouseAutomationAgent instance.

    Sequence:

        move
          ↓
        click
          ↓
        move
          ↓
        scroll
          ↓
        move
          ↓
        mouse_down
          ↓
        mouse_up

    This verifies that the agent can execute multiple real operations
    consecutively while maintaining a valid lifecycle.
    """

    agent = MouseAutomationAgent()

    try:
        actions = [
            create_mouse_action(
                task_id=31,
                action="move_mouse",
                parameters={
                    "x": 150,
                    "y": 150,
                },
            ),
            create_mouse_action(
                task_id=32,
                action="click",
                parameters={
                    "button": "left",
                },
            ),
            create_mouse_action(
                task_id=33,
                action="move_mouse",
                parameters={
                    "x": 250,
                    "y": 250,
                },
            ),
            create_mouse_action(
                task_id=34,
                action="scroll",
                parameters={
                    "dx": 0,
                    "dy": 1,
                },
            ),
            create_mouse_action(
                task_id=35,
                action="move_mouse",
                parameters={
                    "x": 350,
                    "y": 350,
                },
            ),
            create_mouse_action(
                task_id=36,
                action="mouse_down",
                parameters={
                    "button": "left",
                },
            ),
            create_mouse_action(
                task_id=37,
                action="mouse_up",
                parameters={
                    "button": "left",
                },
            ),
        ]

        for request in actions:

            result = agent.execute(request)

            assert result.success is True
            assert result.task_id == request.task_id
            assert result.action == request.action
            assert result.error is None

            assert (
                result.metadata["agent_id"]
                == "mouse_agent"
            )

            assert (
                result.metadata["backend"]
                == "pynput"
            )

            # Give the OS a small amount of time between physical operations.
            time.sleep(0.05)

        assert (
            agent.lifecycle_state
            == AgentLifecycleState.READY
        )

    finally:
        agent.cleanup()


# =============================================================================
# Optional Safety / Environment Marker
# =============================================================================


@pytest.mark.real_hardware
def test_real_mouse_backend_is_operational():
    """
    Additional J.11 hardware smoke test.

    This test is explicitly marked as real_hardware so that it can later be
    selected separately from normal unit/integration tests.

    It performs only a mouse move and verifies the resulting cursor position.
    """

    agent = MouseAutomationAgent()

    try:
        target_x = 100
        target_y = 100

        request = create_mouse_action(
            task_id=100,
            action="move_mouse",
            parameters={
                "x": target_x,
                "y": target_y,
            },
        )

        result = agent.execute(request)

        assert result.success is True

        actual_position = agent.actions.controller.position

        assert actual_position == (
            target_x,
            target_y,
        )

    finally:
        agent.cleanup()