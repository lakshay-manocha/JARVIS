"""
===============================================================================
File Name   : test_keyboard_agent_integration.py
Module      : Automation Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
M5-I integration test.

Verifies that the real KeyboardAutomationAgent can execute a keyboard
ActionRequest through the existing Automation Engine integration layer.

Validated execution path:

    InterpretedTask
        ↓
    ActionRequestBuilder
        ↓
    ActionRequest
        ↓
    ToolAgentMapper
        ↓
    AgentRegistry
        ↓
    KeyboardAutomationAgent
        ↓
    KeyboardActions Test Double
        ↓
    AutomationExecutionResult
        ↓
    ExecutionResultIntegrator
        ↓
    ExecutionOutcome

The test does NOT send real keyboard input to the operating system.

The real KeyboardAutomationAgent is used, while its low-level KeyboardActions
dependency is replaced by a controlled test double.

This validates the M5-I agent integration without introducing unsafe
side effects during automated testing.

Author : Team JARVIS
===============================================================================
"""

from __future__ import annotations

from typing import Any

from agent_engine.agent_brain.models.interpreted_task import (
    InterpretedTask,
)

from agent_engine.automation.agents.keyboard.keyboard_agent import (
    KeyboardAutomationAgent,
)

from agent_engine.automation.dispatcher.action_dispatcher import (
    AutomationActionDispatcher,
)

from agent_engine.automation.integration.action_request_builder import (
    ActionRequestBuilder,
)

from agent_engine.automation.integration.execution_result_integrator import (
    ExecutionResultIntegrator,
)

from agent_engine.automation.models.lifecycle import AgentLifecycleState
from agent_engine.automation.registry.action_registry import (
    ActionRegistry,
)

from agent_engine.automation.registry.agent_registry import (
    AgentRegistry,
)

from agent_engine.automation.registry.tool_agent_mapper import (
    ToolAgentMapper,
)

from agent_engine.contracts.enums import (
    ExecutionStatus,
    ToolType,
)


# =============================================================================
# Keyboard Actions Test Double
# =============================================================================


class IntegrationKeyboardActions:
    """
    Controlled keyboard action implementation used for integration testing.

    It preserves the interface expected by KeyboardAutomationAgent while
    preventing any real keyboard input from being generated.
    """

    def __init__(self) -> None:
        self.calls: list[
            tuple[str, Any]
        ] = []

        self.release_all_calls = 0

    # -------------------------------------------------------------------------
    # Keyboard Actions
    # -------------------------------------------------------------------------

    def type_text(
        self,
        text: str,
    ) -> None:

        self.calls.append(
            (
                "type_text",
                text,
            )
        )

    def press_key(
        self,
        key: str,
    ) -> None:

        self.calls.append(
            (
                "press_key",
                key,
            )
        )

    def hotkey(
        self,
        keys: list[str] | tuple[str, ...],
    ) -> None:

        self.calls.append(
            (
                "hotkey",
                list(keys),
            )
        )

    def key_down(
        self,
        key: str,
    ) -> None:

        self.calls.append(
            (
                "key_down",
                key,
            )
        )

    def key_up(
        self,
        key: str,
    ) -> None:

        self.calls.append(
            (
                "key_up",
                key,
            )
        )

    def release_all(self) -> None:

        self.release_all_calls += 1


# =============================================================================
# Test Fixtures / Setup Helpers
# =============================================================================


def create_keyboard_agent_setup() -> tuple[
    KeyboardAutomationAgent,
    IntegrationKeyboardActions,
    AgentRegistry,
    ToolAgentMapper,
    AutomationActionDispatcher,
]:
    """
    Create the complete Keyboard Agent integration stack.

    The real KeyboardAutomationAgent is used.

    Only its low-level keyboard dependency is replaced with a controlled
    test double.
    """

    # -------------------------------------------------------------------------
    # Keyboard Action Layer
    # -------------------------------------------------------------------------

    keyboard_actions = IntegrationKeyboardActions()

    # -------------------------------------------------------------------------
    # Real M5-I Keyboard Agent
    # -------------------------------------------------------------------------

    keyboard_agent = KeyboardAutomationAgent(
        actions=keyboard_actions,
    )

    # -------------------------------------------------------------------------
    # Agent Registry
    # -------------------------------------------------------------------------

    agent_registry = AgentRegistry()

    agent_registry.register(
        keyboard_agent,
    )

    # -------------------------------------------------------------------------
    # Tool → Agent Mapping
    # -------------------------------------------------------------------------

    tool_agent_mapper = ToolAgentMapper(
        agent_registry,
    )

    tool_agent_mapper.register(
        ToolType.KEYBOARD,
        keyboard_agent,
    )

    # -------------------------------------------------------------------------
    # Automation Dispatcher
    # -------------------------------------------------------------------------

    dispatcher = AutomationActionDispatcher(
        ActionRegistry(),
        request_builder=ActionRequestBuilder(),
        tool_agent_mapper=tool_agent_mapper,
        result_integrator=ExecutionResultIntegrator(),
    )

    return (
        keyboard_agent,
        keyboard_actions,
        agent_registry,
        tool_agent_mapper,
        dispatcher,
    )


# =============================================================================
# Test Task
# =============================================================================


def create_keyboard_task(
    *,
    task_id: int = 1,
    action: str = "type_text",
    parameters: dict[str, Any] | None = None,
) -> InterpretedTask:
    """
    Create an InterpretedTask representing a keyboard automation action.

    The task is constructed at the Agent Brain → Automation Engine boundary,
    because the current Agent Brain semantic resolver does not yet define
    keyboard intents.
    """

    return InterpretedTask(
        task_id=task_id,
        original_text="Type Hello JARVIS",
        normalized_text="type hello jarvis",
        action=action,
        tool=ToolType.KEYBOARD.value,
        parameters=(
            dict(parameters)
            if parameters is not None
            else {
                "text": "Hello JARVIS",
            }
        ),
    )


# =============================================================================
# M5-I — Registry Integration
# =============================================================================


def test_keyboard_agent_can_be_registered() -> None:
    """
    KeyboardAutomationAgent must satisfy the AgentRegistry contract.
    """

    (
        keyboard_agent,
        _,
        agent_registry,
        _,
        _,
    ) = create_keyboard_agent_setup()

    resolved = agent_registry.get(
        keyboard_agent.agent_id,
    )

    assert resolved is keyboard_agent

    assert resolved.agent_id == "keyboard_agent"


# =============================================================================
# M5-I — Tool → Agent Mapping
# =============================================================================


def test_keyboard_tool_resolves_to_keyboard_agent() -> None:
    """
    ToolType.KEYBOARD must resolve to KeyboardAutomationAgent.
    """

    (
        keyboard_agent,
        _,
        _,
        tool_agent_mapper,
        _,
    ) = create_keyboard_agent_setup()

    resolved = tool_agent_mapper.resolve(
        ToolType.KEYBOARD,
    )

    assert resolved is keyboard_agent

    assert resolved.tool_type == ToolType.KEYBOARD

    assert resolved.agent_id == "keyboard_agent"


# =============================================================================
# M5-I — Keyboard Agent Capability
# =============================================================================


def test_keyboard_agent_accepts_type_text_request() -> None:
    """
    KeyboardAutomationAgent must accept a valid type_text ActionRequest.
    """

    (
        keyboard_agent,
        _,
        _,
        _,
        _,
    ) = create_keyboard_agent_setup()

    task = create_keyboard_task()

    request = ActionRequestBuilder().build(
        task,
        timeout_seconds=30.0,
    )

    assert keyboard_agent.can_execute(
        request,
    ) is True


# =============================================================================
# M5-I — Complete Dispatcher Integration
# =============================================================================


def test_keyboard_agent_executes_through_dispatcher() -> None:
    """
    Verify the complete Keyboard Agent integration path.

    This is the primary M5-I integration test.
    """

    (
        keyboard_agent,
        keyboard_actions,
        _,
        tool_agent_mapper,
        dispatcher,
    ) = create_keyboard_agent_setup()

    # -------------------------------------------------------------------------
    # Stage 1 — Create Interpreted Task
    # -------------------------------------------------------------------------

    task = create_keyboard_task()

    # -------------------------------------------------------------------------
    # Stage 2 — Verify Tool Mapping
    # -------------------------------------------------------------------------

    assert (
        tool_agent_mapper.resolve(
            ToolType.KEYBOARD,
        )
        is keyboard_agent
    )

    # -------------------------------------------------------------------------
    # Stage 3 — Dispatch Through Automation Engine
    # -------------------------------------------------------------------------

    outcome = dispatcher.dispatch(
        task,
        attempt=1,
        timeout_seconds=30.0,
    )

    # -------------------------------------------------------------------------
    # Stage 4 — Verify Execution Outcome
    # -------------------------------------------------------------------------

    assert outcome is not None

    assert outcome.task_id == 1

    assert outcome.status == ExecutionStatus.COMPLETED

    assert outcome.success is True

    assert outcome.attempt == 1

    # -------------------------------------------------------------------------
    # Stage 5 — Verify Real Keyboard Agent Was Used
    # -------------------------------------------------------------------------

    assert keyboard_agent.agent_id == "keyboard_agent"

    assert keyboard_agent.tool_type == ToolType.KEYBOARD

    # -------------------------------------------------------------------------
    # Stage 6 — Verify Low-Level Keyboard Operation
    # -------------------------------------------------------------------------

    assert keyboard_actions.calls == [
        (
            "type_text",
            "Hello JARVIS",
        )
    ]


# =============================================================================
# M5-I — Keyboard Agent Lifecycle
# =============================================================================


def test_keyboard_agent_lifecycle_after_dispatch() -> None:
    """
    Verify that successful execution leaves the Keyboard Agent ready
    for subsequent tasks.
    """

    (
        keyboard_agent,
        _,
        _,
        _,
        dispatcher,
    ) = create_keyboard_agent_setup()

    task = create_keyboard_task()

    outcome = dispatcher.dispatch(
        task,
        attempt=1,
        timeout_seconds=30.0,
    )

    assert outcome.success is True

    assert (
        keyboard_agent.lifecycle_state
        == AgentLifecycleState.READY
    )