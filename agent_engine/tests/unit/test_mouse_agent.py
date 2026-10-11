"""
===============================================================================
File Name   : test_mouse_agent.py
Module      : Automation Agents - Mouse Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Unit tests for MouseAutomationAgent.

The tests validate:
    - Agent identity
    - Agent capabilities
    - ActionRequest compatibility
    - Capability validation
    - Mouse action execution
    - Required parameter validation
    - Invalid action handling
    - Cleanup lifecycle

Low-level mouse operations are replaced with FakeMouseActions so that
the tests do NOT move or click the real mouse.

===============================================================================
"""

from agent_engine.automation.agents.mouse.mouse_agent import (
    MouseAutomationAgent,
)
from agent_engine.automation.models.execution_result import (
    AutomationExecutionResult,
)
from agent_engine.contracts.action import ActionRequest
from agent_engine.contracts.enums import (
    ActionCategory,
    ToolType,
)


# =============================================================================
# Fake Mouse Actions
# =============================================================================

class FakeMouseActions:
    """
    Fake low-level mouse backend used for unit testing.

    This prevents the tests from interacting with the real mouse.
    """

    def __init__(self):
        self.calls = []

    def move_mouse(self, x, y):
        self.calls.append(
            ("move_mouse", x, y)
        )

    def click(self, button="left"):
        self.calls.append(
            ("click", button)
        )

    def double_click(self, button="left"):
        self.calls.append(
            ("double_click", button)
        )

    def right_click(self):
        self.calls.append(
            ("right_click",)
        )

    def mouse_down(self, button="left"):
        self.calls.append(
            ("mouse_down", button)
        )

    def mouse_up(self, button="left"):
        self.calls.append(
            ("mouse_up", button)
        )

    def scroll(self, dx=0, dy=0):
        self.calls.append(
            ("scroll", dx, dy)
        )


# =============================================================================
# Request Helper
# =============================================================================

def make_request(
    action,
    parameters,
):
    """
    Create a valid mouse ActionRequest.
    """

    return ActionRequest(
        task_id=1,
        action=action,
        category=ActionCategory.MOUSE,
        tool=ToolType.MOUSE,
        parameters=parameters,
    )


# =============================================================================
# Identity Tests
# =============================================================================

def test_mouse_agent_identity():

    actions = FakeMouseActions()

    agent = MouseAutomationAgent(
        actions=actions
    )

    assert agent.agent_id == "mouse_agent"
    assert agent.tool_type == ToolType.MOUSE
    assert agent.name == "Mouse Automation Agent"


# =============================================================================
# Capability Tests
# =============================================================================

def test_mouse_agent_capabilities():

    actions = FakeMouseActions()

    agent = MouseAutomationAgent(
        actions=actions
    )

    assert agent.supports("move_mouse")
    assert agent.supports("click")
    assert agent.supports("double_click")
    assert agent.supports("right_click")
    assert agent.supports("mouse_down")
    assert agent.supports("mouse_up")
    assert agent.supports("scroll")

    assert not agent.supports("type_text")
    assert not agent.supports("press_key")


# =============================================================================
# can_execute Tests
# =============================================================================

def test_can_execute_mouse_action():

    actions = FakeMouseActions()

    agent = MouseAutomationAgent(
        actions=actions
    )

    request = make_request(
        "move_mouse",
        {
            "x": 500,
            "y": 300,
        },
    )

    assert agent.can_execute(request)


def test_can_execute_rejects_keyboard_action():

    actions = FakeMouseActions()

    agent = MouseAutomationAgent(
        actions=actions
    )

    request = ActionRequest(
        task_id=1,
        action="press_key",
        category=ActionCategory.KEYBOARD,
        tool=ToolType.KEYBOARD,
        parameters={
            "key": "enter",
        },
    )

    assert not agent.can_execute(request)


def test_can_execute_rejects_unsupported_action():

    actions = FakeMouseActions()

    agent = MouseAutomationAgent(
        actions=actions
    )

    request = make_request(
        "type_text",
        {
            "text": "Hello",
        },
    )

    assert not agent.can_execute(request)


# =============================================================================
# Move Mouse Execution
# =============================================================================

def test_move_mouse_execution():

    actions = FakeMouseActions()

    agent = MouseAutomationAgent(
        actions=actions
    )

    request = make_request(
        "move_mouse",
        {
            "x": 500,
            "y": 300,
        },
    )

    result = agent.execute(request)

    assert isinstance(
        result,
        AutomationExecutionResult,
    )

    assert result.success is True
    assert result.task_id == 1
    assert result.action == "move_mouse"

    assert actions.calls == [
        (
            "move_mouse",
            500,
            300,
        )
    ]


# =============================================================================
# Click Execution
# =============================================================================

def test_click_execution():

    actions = FakeMouseActions()

    agent = MouseAutomationAgent(
        actions=actions
    )

    request = make_request(
        "click",
        {
            "button": "left",
        },
    )

    result = agent.execute(request)

    assert isinstance(
        result,
        AutomationExecutionResult,
    )

    assert result.success is True

    assert actions.calls == [
        (
            "click",
            "left",
        )
    ]


def test_click_execution_uses_default_button():

    actions = FakeMouseActions()

    agent = MouseAutomationAgent(
        actions=actions
    )

    request = make_request(
        "click",
        {},
    )

    result = agent.execute(request)

    assert result.success is True

    assert actions.calls == [
        (
            "click",
            "left",
        )
    ]


# =============================================================================
# Double Click Execution
# =============================================================================

def test_double_click_execution():

    actions = FakeMouseActions()

    agent = MouseAutomationAgent(
        actions=actions
    )

    request = make_request(
        "double_click",
        {
            "button": "left",
        },
    )

    result = agent.execute(request)

    assert result.success is True

    assert actions.calls == [
        (
            "double_click",
            "left",
        )
    ]


# =============================================================================
# Right Click Execution
# =============================================================================

def test_right_click_execution():

    actions = FakeMouseActions()

    agent = MouseAutomationAgent(
        actions=actions
    )

    request = make_request(
        "right_click",
        {},
    )

    result = agent.execute(request)

    assert result.success is True

    assert actions.calls == [
        (
            "right_click",
        )
    ]


# =============================================================================
# Mouse Down Execution
# =============================================================================

def test_mouse_down_execution():

    actions = FakeMouseActions()

    agent = MouseAutomationAgent(
        actions=actions
    )

    request = make_request(
        "mouse_down",
        {
            "button": "left",
        },
    )

    result = agent.execute(request)

    assert result.success is True

    assert actions.calls == [
        (
            "mouse_down",
            "left",
        )
    ]


def test_mouse_down_execution_uses_default_button():

    actions = FakeMouseActions()

    agent = MouseAutomationAgent(
        actions=actions
    )

    request = make_request(
        "mouse_down",
        {},
    )

    result = agent.execute(request)

    assert result.success is True

    assert actions.calls == [
        (
            "mouse_down",
            "left",
        )
    ]


# =============================================================================
# Mouse Up Execution
# =============================================================================

def test_mouse_up_execution():

    actions = FakeMouseActions()

    agent = MouseAutomationAgent(
        actions=actions
    )

    request = make_request(
        "mouse_up",
        {
            "button": "left",
        },
    )

    result = agent.execute(request)

    assert result.success is True

    assert actions.calls == [
        (
            "mouse_up",
            "left",
        )
    ]


def test_mouse_up_execution_uses_default_button():

    actions = FakeMouseActions()

    agent = MouseAutomationAgent(
        actions=actions
    )

    request = make_request(
        "mouse_up",
        {},
    )

    result = agent.execute(request)

    assert result.success is True

    assert actions.calls == [
        (
            "mouse_up",
            "left",
        )
    ]


# =============================================================================
# Scroll Execution
# =============================================================================

def test_scroll_execution():

    actions = FakeMouseActions()

    agent = MouseAutomationAgent(
        actions=actions
    )

    request = make_request(
        "scroll",
        {
            "dx": 0,
            "dy": 5,
        },
    )

    result = agent.execute(request)

    assert result.success is True

    assert actions.calls == [
        (
            "scroll",
            0,
            5,
        )
    ]


def test_scroll_execution_uses_default_values():

    actions = FakeMouseActions()

    agent = MouseAutomationAgent(
        actions=actions
    )

    request = make_request(
        "scroll",
        {},
    )

    result = agent.execute(request)

    assert result.success is True

    assert actions.calls == [
        (
            "scroll",
            0,
            0,
        )
    ]


# =============================================================================
# Required Parameter Validation
# =============================================================================

def test_move_mouse_missing_x_returns_failure():

    actions = FakeMouseActions()

    agent = MouseAutomationAgent(
        actions=actions
    )

    request = make_request(
        "move_mouse",
        {
            "y": 300,
        },
    )

    result = agent.execute(request)

    assert result.success is False
    assert "x" in result.error.lower()

    assert actions.calls == []


def test_move_mouse_missing_y_returns_failure():

    actions = FakeMouseActions()

    agent = MouseAutomationAgent(
        actions=actions
    )

    request = make_request(
        "move_mouse",
        {
            "x": 500,
        },
    )

    result = agent.execute(request)

    assert result.success is False
    assert "y" in result.error.lower()

    assert actions.calls == []


# =============================================================================
# Capability Failure During Execution
# =============================================================================

def test_unsupported_action_returns_failure():

    actions = FakeMouseActions()

    agent = MouseAutomationAgent(
        actions=actions
    )

    request = make_request(
        "type_text",
        {
            "text": "Hello",
        },
    )

    result = agent.execute(request)

    assert result.success is False
    assert "cannot execute" in result.error.lower()

    assert actions.calls == []


# =============================================================================
# Lifecycle / Cleanup
# =============================================================================

def test_cleanup_from_created_state():

    actions = FakeMouseActions()

    agent = MouseAutomationAgent(
        actions=actions
    )

    agent.cleanup()

    assert agent.lifecycle_state.value == "cleaned"


def test_initialize_and_cleanup():

    actions = FakeMouseActions()

    agent = MouseAutomationAgent(
        actions=actions
    )

    agent.initialize()

    assert agent.lifecycle_state.value == "ready"

    agent.cleanup()

    assert agent.lifecycle_state.value == "cleaned"


def test_execution_initializes_agent_lazily():

    actions = FakeMouseActions()

    agent = MouseAutomationAgent(
        actions=actions
    )

    assert agent.lifecycle_state.value == "created"

    request = make_request(
        "click",
        {},
    )

    result = agent.execute(request)

    assert result.success is True
    assert agent.lifecycle_state.value == "ready"


# =============================================================================
# Metadata Test
# =============================================================================

def test_mouse_agent_metadata():

    actions = FakeMouseActions()

    agent = MouseAutomationAgent(
        actions=actions
    )

    metadata = agent.metadata

    assert metadata["agent_id"] == "mouse_agent"
    assert metadata["agent_type"] == "mouse"
    assert metadata["backend"] == "pynput"
    assert metadata["version"] == "M5-J"