"""
Tests for M5-J.10 - Dispatcher -> MouseAutomationAgent Integration.

These tests verify the complete dispatcher integration path using the real
MouseAutomationAgent while replacing its low-level MouseActions backend with
a controlled test double.

Architecture under test:

    InterpretedTask
          |
          v
    ActionRequestBuilder
          |
          v
    ActionRequest
          |
          v
    ToolAgentMapper
          |
          v
    MouseAutomationAgent
          |
          v
    Test MouseActions Backend

IMPORTANT:
    These tests do NOT perform real mouse movement or clicking.

Real physical mouse execution belongs to M5-J.11.
"""

from __future__ import annotations

from agent_engine.agent_brain.models.interpreted_task import (
    InterpretedTask,
)
from agent_engine.automation.agents.mouse.mouse_agent import (
    MouseAutomationAgent,
)
from agent_engine.automation.dispatcher.action_dispatcher import (
    AutomationActionDispatcher,
)
from agent_engine.automation.integration.action_request_builder import ActionRequestBuilder
from agent_engine.automation.models.execution_result import (
    AutomationExecutionResult,
)
from agent_engine.automation.registry.action_registry import (
    ActionRegistry,
)
from agent_engine.automation.registry.agent_registry import (
    AgentRegistry,
)
from agent_engine.automation.registry.tool_agent_mapper import (
    ToolAgentMapper,
)
from agent_engine.contracts.action import ActionRequest
from agent_engine.contracts.enums import (
    ActionCategory,
    ExecutionStatus,
    ToolType,
)
from agent_engine.decision_manager.models.execution_outcome import (
    FailureType,
)


# =============================================================================
# Test MouseActions Backend
# =============================================================================

class TestMouseActions:
    """
    Controlled MouseActions replacement for J.10 integration tests.

    This class records calls made by MouseAutomationAgent without touching
    the physical mouse.
    """

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def move_mouse(
        self,
        x,
        y,
    ):
        self.calls.append(
            {
                "action": "move_mouse",
                "x": x,
                "y": y,
            }
        )

        return "mouse moved"

    def click(
        self,
        button="left",
    ):
        self.calls.append(
            {
                "action": "click",
                "button": button,
            }
        )

        return "mouse clicked"

    def double_click(
        self,
        button="left",
    ):
        self.calls.append(
            {
                "action": "double_click",
                "button": button,
            }
        )

        return "mouse double clicked"

    def right_click(self):
        self.calls.append(
            {
                "action": "right_click",
            }
        )

        return "mouse right clicked"

    def mouse_down(
        self,
        button="left",
    ):
        self.calls.append(
            {
                "action": "mouse_down",
                "button": button,
            }
        )

        return "mouse button pressed"

    def mouse_up(
        self,
        button="left",
    ):
        self.calls.append(
            {
                "action": "mouse_up",
                "button": button,
            }
        )

        return "mouse button released"

    def scroll(
        self,
        dx=0,
        dy=0,
    ):
        self.calls.append(
            {
                "action": "scroll",
                "dx": dx,
                "dy": dy,
            }
        )

        return "mouse scrolled"


# =============================================================================
# Helpers
# =============================================================================

def create_mouse_task(
    *,
    task_id: int = 1,
    action: str = "move_mouse",
    parameters: dict | None = None,
) -> InterpretedTask:
    """
    Create an InterpretedTask targeting the real MouseAutomationAgent.
    """

    return InterpretedTask(
        task_id=task_id,
        original_text="Move the mouse",
        normalized_text="move the mouse",
        action=action,
        tool="mouse_agent",
        parameters=parameters or {},
    )


def create_mouse_dispatcher(
    mouse_actions: TestMouseActions,
) -> tuple[
    AutomationActionDispatcher,
    MouseAutomationAgent,
    ToolAgentMapper,
]:
    """
    Create a dispatcher configured with the real
    MouseAutomationAgent and the existing registry/mapper architecture.

    The MouseActions backend is injected so J.10 never performs
    physical mouse input.
    """

    # -------------------------------------------------------------------------
    # Create the shared AgentRegistry
    # -------------------------------------------------------------------------

    agent_registry = AgentRegistry()

    # -------------------------------------------------------------------------
    # Create the ToolAgentMapper using the SAME registry
    # -------------------------------------------------------------------------

    mapper = ToolAgentMapper(
        agent_registry
    )

    # -------------------------------------------------------------------------
    # Create the real MouseAutomationAgent
    # -------------------------------------------------------------------------

    mouse_agent = MouseAutomationAgent(
        actions=mouse_actions
    )

    # -------------------------------------------------------------------------
    # Register the SAME agent instance in the registry
    # -------------------------------------------------------------------------

    agent_registry.register(
        mouse_agent
    )

    # -------------------------------------------------------------------------
    # Register the SAME agent instance in the mapper
    # -------------------------------------------------------------------------

    mapper.register(
        ToolType.MOUSE,
        mouse_agent
    )

    # -------------------------------------------------------------------------
    # Create ActionDispatcher
    # -------------------------------------------------------------------------

    action_registry = ActionRegistry()

    dispatcher = AutomationActionDispatcher(
        action_registry,
        request_builder=ActionRequestBuilder(),
        tool_agent_mapper=mapper,
    )

    return (
        dispatcher,
        mouse_agent,
        mapper,
    )

# =============================================================================
# J.10 - Real MouseAutomationAgent Resolution
# =============================================================================

def test_dispatcher_resolves_real_mouse_agent():
    """
    Dispatcher should resolve the real MouseAutomationAgent through
    ToolAgentMapper when the request targets ToolType.MOUSE.
    """

    mouse_actions = TestMouseActions()

    dispatcher, mouse_agent, mapper = create_mouse_dispatcher(
        mouse_actions
    )

    task = create_mouse_task(
        action="move_mouse",
        parameters={
            "x": 100,
            "y": 200,
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    resolved_agent = mapper.resolve(
        ToolType.MOUSE
    )

    assert resolved_agent is mouse_agent
    assert resolved_agent.agent_id == "mouse_agent"
    assert resolved_agent.tool_type == ToolType.MOUSE

    assert result.success is True
    assert result.status == ExecutionStatus.COMPLETED


# =============================================================================
# J.10 - Mouse Action Routing
# =============================================================================

def test_dispatcher_routes_move_mouse_to_real_mouse_agent():
    """
    Dispatcher should route a move_mouse request to the real
    MouseAutomationAgent.
    """

    mouse_actions = TestMouseActions()

    dispatcher, _, _ = create_mouse_dispatcher(
        mouse_actions
    )

    task = create_mouse_task(
        task_id=10,
        action="move_mouse",
        parameters={
            "x": 300,
            "y": 400,
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.success is True
    assert result.status == ExecutionStatus.COMPLETED

    assert mouse_actions.calls == [
        {
            "action": "move_mouse",
            "x": 300,
            "y": 400,
        }
    ]


def test_dispatcher_routes_click_to_real_mouse_agent():
    """
    Dispatcher should route a click request to the real
    MouseAutomationAgent.
    """

    mouse_actions = TestMouseActions()

    dispatcher, _, _ = create_mouse_dispatcher(
        mouse_actions
    )

    task = create_mouse_task(
        task_id=11,
        action="click",
        parameters={
            "button": "left",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.success is True
    assert result.status == ExecutionStatus.COMPLETED

    assert mouse_actions.calls == [
        {
            "action": "click",
            "button": "left",
        }
    ]


# =============================================================================
# J.10 - ActionRequest Propagation
# =============================================================================

def test_dispatcher_passes_correct_action_request_to_mouse_agent():
    """
    Dispatcher should construct and propagate the correct ActionRequest
    through ToolAgentMapper to MouseAutomationAgent.
    """

    mouse_actions = TestMouseActions()

    dispatcher, mouse_agent, _ = create_mouse_dispatcher(
        mouse_actions
    )

    task = create_mouse_task(
        task_id=42,
        action="move_mouse",
        parameters={
            "x": 500,
            "y": 600,
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.success is True

    # The real MouseAutomationAgent delegates to the injected backend.
    assert mouse_actions.calls == [
        {
            "action": "move_mouse",
            "x": 500,
            "y": 600,
        }
    ]

    # Verify the request independently by constructing the same request
    # expected by the dispatcher path.
    request = ActionRequest(
        task_id=42,
        action="move_mouse",
        tool=ToolType.MOUSE,
        category=ActionCategory.MOUSE,
        parameters={
            "x": 500,
            "y": 600,
        },
    )

    assert mouse_agent.can_execute(
        request
    ) is True


# =============================================================================
# J.10 - Mouse Agent Capability Validation
# =============================================================================

def test_dispatcher_rejects_unsupported_mouse_action():
    """
    Dispatcher should not execute an action that the real
    MouseAutomationAgent does not support.
    """

    mouse_actions = TestMouseActions()

    dispatcher, _, _ = create_mouse_dispatcher(
        mouse_actions
    )

    task = create_mouse_task(
        action="unsupported_mouse_action",
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.status == ExecutionStatus.FAILED
    assert result.success is False
    assert result.failure_type == FailureType.VALIDATION

    assert mouse_actions.calls == []


# =============================================================================
# J.10 - Parameter Propagation
# =============================================================================

def test_dispatcher_preserves_mouse_parameters():
    """
    Mouse parameters should survive the complete dispatcher integration
    path without modification.
    """

    mouse_actions = TestMouseActions()

    dispatcher, _, _ = create_mouse_dispatcher(
        mouse_actions
    )

    task = create_mouse_task(
        task_id=20,
        action="move_mouse",
        parameters={
            "x": 123,
            "y": 456,
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.success is True

    assert mouse_actions.calls[0]["x"] == 123
    assert mouse_actions.calls[0]["y"] == 456


def test_dispatcher_preserves_click_button_parameter():
    """
    Click button parameters should reach MouseActions unchanged.
    """

    mouse_actions = TestMouseActions()

    dispatcher, _, _ = create_mouse_dispatcher(
        mouse_actions
    )

    task = create_mouse_task(
        task_id=21,
        action="click",
        parameters={
            "button": "right",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.success is True

    assert mouse_actions.calls == [
        {
            "action": "click",
            "button": "right",
        }
    ]


# =============================================================================
# J.10 - AutomationExecutionResult Integration
# =============================================================================

def test_dispatcher_converts_mouse_execution_result_to_success_outcome():
    """
    Successful MouseAutomationAgent execution should propagate through the
    dispatcher and become a successful ExecutionOutcome.
    """

    mouse_actions = TestMouseActions()

    dispatcher, _, _ = create_mouse_dispatcher(
        mouse_actions
    )

    task = create_mouse_task(
        task_id=30,
        action="double_click",
        parameters={
            "button": "left",
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert isinstance(
        result,
        object,
    )

    assert result.task_id == 30
    assert result.status == ExecutionStatus.COMPLETED
    assert result.success is True
    assert result.attempt == 1
    assert result.failure_type == FailureType.NONE

    assert mouse_actions.calls == [
        {
            "action": "double_click",
            "button": "left",
        }
    ]


# =============================================================================
# J.10 - Multiple Mouse Actions
# =============================================================================

def test_dispatcher_routes_multiple_mouse_actions():
    """
    Dispatcher should correctly route different supported mouse actions
    through the same real MouseAutomationAgent.
    """

    mouse_actions = TestMouseActions()

    dispatcher, _, _ = create_mouse_dispatcher(
        mouse_actions
    )

    tasks = [
        create_mouse_task(
            task_id=31,
            action="move_mouse",
            parameters={
                "x": 10,
                "y": 20,
            },
        ),
        create_mouse_task(
            task_id=32,
            action="click",
            parameters={
                "button": "left",
            },
        ),
        create_mouse_task(
            task_id=33,
            action="right_click",
        ),
        create_mouse_task(
            task_id=34,
            action="scroll",
            parameters={
                "dx": 0,
                "dy": 5,
            },
        ),
    ]

    results = []

    for task in tasks:
        results.append(
            dispatcher.dispatch(
                task,
                attempt=1,
            )
        )

    assert all(
        result.success is True
        for result in results
    )

    assert [
        result.status
        for result in results
    ] == [
        ExecutionStatus.COMPLETED,
        ExecutionStatus.COMPLETED,
        ExecutionStatus.COMPLETED,
        ExecutionStatus.COMPLETED,
    ]

    assert mouse_actions.calls == [
        {
            "action": "move_mouse",
            "x": 10,
            "y": 20,
        },
        {
            "action": "click",
            "button": "left",
        },
        {
            "action": "right_click",
        },
        {
            "action": "scroll",
            "dx": 0,
            "dy": 5,
        },
    ]


# =============================================================================
# J.10 - No Physical Mouse Requirement
# =============================================================================

def test_j10_does_not_require_physical_mouse_execution():
    """
    J.10 must operate entirely through the injected MouseActions test
    backend.

    This explicitly protects the J.10/J.11 boundary:
        J.10 -> integration verification
        J.11 -> real physical mouse execution
    """

    mouse_actions = TestMouseActions()

    dispatcher, mouse_agent, _ = create_mouse_dispatcher(
        mouse_actions
    )

    task = create_mouse_task(
        task_id=40,
        action="move_mouse",
        parameters={
            "x": 700,
            "y": 800,
        },
    )

    result = dispatcher.dispatch(
        task,
        attempt=1,
    )

    assert result.success is True
    assert mouse_agent.agent_id == "mouse_agent"

    # The action was handled by our controlled backend rather than the
    # real pynput Controller.
    assert mouse_actions.calls == [
        {
            "action": "move_mouse",
            "x": 700,
            "y": 800,
        }
    ]