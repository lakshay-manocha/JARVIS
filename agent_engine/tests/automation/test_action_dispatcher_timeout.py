"""
===============================================================================
File Name   : test_action_dispatcher_timeout.py
Module      : Automation Engine Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Tests timeout propagation through the AutomationActionDispatcher.

Phase F:
    F-3 - Timeout Handling

Coverage:
    - Timeout configuration reaches the ActionRequest
    - Timeout configuration is preserved in ExecutionOutcome
    - Execution duration is measured
    - Successful execution within timeout remains successful
    - TimeoutPolicy can normalize a duration-based timeout

Author : Team Agent
===============================================================================
"""

from agent_engine.agent_brain.models.interpreted_task import InterpretedTask
from agent_engine.automation.dispatcher.action_dispatcher import (
    AutomationActionDispatcher,
)
from agent_engine.automation.registry.action_registry import ActionRegistry
from agent_engine.contracts.enums import ExecutionStatus, ToolType
from agent_engine.decision_manager.models.execution_outcome import (
    FailureType,
)
from agent_engine.decision_manager.timeout_policy import TimeoutPolicy


# =============================================================================
# Helpers
# =============================================================================


def build_task(
    *,
    task_id: int = 1,
    action: str = "open",
    tool: str = "browser_agent",
    parameters: dict | None = None,
) -> InterpretedTask:
    """
    Build a minimal valid InterpretedTask for dispatcher timeout testing.
    """

    return InterpretedTask(
        task_id=task_id,
        original_text="Open https://example.com",
        normalized_text="open https://example.com",
        action=action,
        tool=tool,
        parameters=parameters or {},
        metadata={},
    )

def build_registry() -> ActionRegistry:
    """
    Build a registry containing a deterministic test action.
    """

    registry = ActionRegistry()

    registry.register(
        "open",
        lambda **kwargs: {
            "success": True,
            "parameters": kwargs,
        },
    )

    return registry


# =============================================================================
# Timeout Propagation
# =============================================================================


def test_dispatcher_preserves_timeout_configuration():
    """
    The timeout supplied to dispatch() must be preserved in the
    returned ExecutionOutcome.
    """

    registry = build_registry()

    dispatcher = AutomationActionDispatcher(
        registry
    )

    task = build_task()

    outcome = dispatcher.dispatch(
        task,
        attempt=1,
        timeout_seconds=5.0,
    )

    assert outcome.timeout_seconds == 5.0


def test_dispatcher_measures_execution_time():
    """
    Dispatcher must record a non-negative execution duration.
    """

    registry = build_registry()

    dispatcher = AutomationActionDispatcher(
        registry
    )

    task = build_task()

    outcome = dispatcher.dispatch(
        task,
        attempt=1,
        timeout_seconds=5.0,
    )

    assert outcome.execution_time is not None
    assert outcome.execution_time >= 0


def test_successful_execution_within_timeout_remains_successful():
    """
    A successful action completing within its configured timeout must
    remain COMPLETED and must not be classified as TIMEOUT.
    """

    registry = build_registry()

    dispatcher = AutomationActionDispatcher(
        registry
    )

    task = build_task()

    outcome = dispatcher.dispatch(
        task,
        attempt=1,
        timeout_seconds=5.0,
    )

    assert outcome.success is True
    assert outcome.status == ExecutionStatus.COMPLETED
    assert outcome.timed_out is False
    assert outcome.failure_type == FailureType.NONE


# =============================================================================
# Timeout Policy Integration
# =============================================================================


def test_dispatcher_outcome_can_be_normalized_as_timeout():
    """
    If the measured execution time exceeds the configured timeout,
    TimeoutPolicy must normalize the outcome to TIMEOUT.

    The dispatcher itself only measures execution time; timeout
    classification remains the responsibility of TimeoutPolicy.
    """

    registry = build_registry()

    dispatcher = AutomationActionDispatcher(
        registry
    )

    task = build_task()

    outcome = dispatcher.dispatch(
        task,
        attempt=1,
        timeout_seconds=5.0,
    )

    # Simulate an execution duration exceeding the configured timeout.
    timeout_outcome = outcome.model_copy(
        update={
            "success": False,
            "status": ExecutionStatus.FAILED,
            "execution_time": 6.0,
            "timed_out": False,
            "failure_type": FailureType.NONE,
        },
        deep=True,
    )

    normalized = TimeoutPolicy().normalize(
        timeout_outcome
    )

    assert normalized.success is False
    assert normalized.status == ExecutionStatus.FAILED
    assert normalized.timed_out is True
    assert normalized.failure_type == FailureType.TIMEOUT
    assert normalized.timeout_seconds == 5.0