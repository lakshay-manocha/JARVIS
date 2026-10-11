"""
===============================================================================
File Name   : test_decision_state_bridge.py
Module      : Integration Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Phase E-7:
    Decision Manager -> State Manager Integration

Tests:
    - COMPLETE decision updates state to COMPLETED
    - FAIL decision updates state to FAILED
    - RETRY decision updates state to RETRYING
    - SKIP decision updates state to SKIPPED
    - FALLBACK decision updates state to RUNNING
    - Invalid transitions are rejected
    - Invalid transitions do not modify runtime state
    - State history is recorded through the bridge
    - Multiple D -> E transitions work correctly
===============================================================================
"""

import pytest

from agent_engine.contracts.enums import ExecutionStatus
from agent_engine.decision_manager.models.decision import (
    DecisionAction,
    DecisionResult,
)
from agent_engine.state_manager.state_manager import StateManager
from agent_engine.state_manager.state_transitions import (
    InvalidStateTransitionError,
)
from agent_engine.integration.decision_state_bridge import (
    DecisionStateBridge,
)


# =============================================================================
# Helpers
# =============================================================================


def create_decision(
    task_id: int,
    action: DecisionAction,
) -> DecisionResult:
    """
    Create a minimal DecisionResult for bridge testing.
    """

    return DecisionResult(
        action=action,
        task_id=task_id,
        reason=f"Test decision: {action.value}",
        attempt=1,
        max_retries=3,
    )


def create_running_task(
    state_manager: StateManager,
    task_id: int = 1,
) -> None:
    """
    Register a task and move it into RUNNING state.
    """

    state_manager.register_task(task_id)

    state_manager.set_state(
        task_id,
        ExecutionStatus.READY,
    )

    state_manager.set_state(
        task_id,
        ExecutionStatus.RUNNING,
    )


# =============================================================================
# E-7.1 COMPLETE
# =============================================================================


def test_complete_decision_updates_state_to_completed():
    """
    COMPLETE decision must transition RUNNING -> COMPLETED.
    """

    state_manager = StateManager()
    bridge = DecisionStateBridge(state_manager)

    create_running_task(state_manager)

    decision = create_decision(
        task_id=1,
        action=DecisionAction.COMPLETE,
    )

    state = bridge.apply_decision(decision)

    assert state.status == ExecutionStatus.COMPLETED

    assert (
        state_manager.get_status(1)
        == ExecutionStatus.COMPLETED
    )


# =============================================================================
# E-7.2 FAIL
# =============================================================================


def test_fail_decision_updates_state_to_failed():
    """
    FAIL decision must transition RUNNING -> FAILED.
    """

    state_manager = StateManager()
    bridge = DecisionStateBridge(state_manager)

    create_running_task(state_manager)

    decision = create_decision(
        task_id=1,
        action=DecisionAction.FAIL,
    )

    state = bridge.apply_decision(decision)

    assert state.status == ExecutionStatus.FAILED

    assert (
        state_manager.get_status(1)
        == ExecutionStatus.FAILED
    )


# =============================================================================
# E-7.3 RETRY
# =============================================================================


def test_retry_decision_updates_failed_state_to_retrying():
    """
    RETRY decision must transition FAILED -> RETRYING.
    """

    state_manager = StateManager()
    bridge = DecisionStateBridge(state_manager)

    create_running_task(state_manager)

    state_manager.set_state(
        1,
        ExecutionStatus.FAILED,
    )

    decision = create_decision(
        task_id=1,
        action=DecisionAction.RETRY,
    )

    state = bridge.apply_decision(decision)

    assert state.status == ExecutionStatus.RETRYING

    assert (
        state_manager.get_status(1)
        == ExecutionStatus.RETRYING
    )


# =============================================================================
# E-7.4 SKIP
# =============================================================================


def test_skip_decision_updates_state_to_skipped():
    """
    SKIP decision must transition the task to SKIPPED.
    """

    state_manager = StateManager()
    bridge = DecisionStateBridge(state_manager)

    state_manager.register_task(1)

    state_manager.set_state(
        1,
        ExecutionStatus.READY,
    )

    decision = create_decision(
        task_id=1,
        action=DecisionAction.SKIP,
    )

    state = bridge.apply_decision(decision)

    assert state.status == ExecutionStatus.SKIPPED

    assert (
        state_manager.get_status(1)
        == ExecutionStatus.SKIPPED
    )


# =============================================================================
# E-7.5 FALLBACK
# =============================================================================


def test_fallback_decision_moves_task_to_running():
    """
    FALLBACK represents entry into recovery execution.

    The bridge must update the runtime state but must NOT execute
    the fallback action itself.
    """

    state_manager = StateManager()
    bridge = DecisionStateBridge(state_manager)

    create_running_task(state_manager)

    state_manager.set_state(
        1,
        ExecutionStatus.FAILED,
    )

    decision = create_decision(
        task_id=1,
        action=DecisionAction.FALLBACK,
    )

    state = bridge.apply_decision(decision)

    assert state.status == ExecutionStatus.RUNNING

    assert (
        state_manager.get_status(1)
        == ExecutionStatus.RUNNING
    )


# =============================================================================
# E-7.6 INVALID TRANSITION
# =============================================================================


def test_invalid_decision_transition_is_rejected():
    """
    The bridge must not bypass E-3 transition validation.

    COMPLETED -> RETRYING is invalid.
    """

    state_manager = StateManager()
    bridge = DecisionStateBridge(state_manager)

    create_running_task(state_manager)

    state_manager.set_state(
        1,
        ExecutionStatus.COMPLETED,
    )

    decision = create_decision(
        task_id=1,
        action=DecisionAction.RETRY,
    )

    with pytest.raises(InvalidStateTransitionError):
        bridge.apply_decision(decision)


# =============================================================================
# E-7.7 INVALID TRANSITION DOES NOT MODIFY STATE
# =============================================================================


def test_invalid_decision_does_not_modify_state():
    """
    A rejected D -> E transition must leave the runtime state unchanged.
    """

    state_manager = StateManager()
    bridge = DecisionStateBridge(state_manager)

    create_running_task(state_manager)

    state_manager.set_state(
        1,
        ExecutionStatus.COMPLETED,
    )

    previous_state = state_manager.get_status(1)

    decision = create_decision(
        task_id=1,
        action=DecisionAction.RETRY,
    )

    with pytest.raises(InvalidStateTransitionError):
        bridge.apply_decision(decision)

    assert (
        state_manager.get_status(1)
        == previous_state
        == ExecutionStatus.COMPLETED
    )


# =============================================================================
# E-7.8 HISTORY
# =============================================================================


def test_bridge_transition_is_recorded_in_history():
    """
    State transitions caused through the bridge must be recorded by
    StateManager history.
    """

    state_manager = StateManager()
    bridge = DecisionStateBridge(state_manager)

    create_running_task(state_manager)

    decision = create_decision(
        task_id=1,
        action=DecisionAction.FAIL,
    )

    bridge.apply_decision(decision)

    history = state_manager.get_history(1)

    assert history[-1].from_status == ExecutionStatus.RUNNING
    assert history[-1].to_status == ExecutionStatus.FAILED


# =============================================================================
# E-7.9 MULTI-STEP D -> E FLOW
# =============================================================================


def test_multiple_decisions_update_state_correctly():
    """
    Verify a realistic DecisionManager -> StateManager sequence:

        RUNNING
            ->
        FAILED
            ->
        RETRYING
    """

    state_manager = StateManager()
    bridge = DecisionStateBridge(state_manager)

    create_running_task(state_manager)

    fail_decision = create_decision(
        task_id=1,
        action=DecisionAction.FAIL,
    )

    bridge.apply_decision(fail_decision)

    assert (
        state_manager.get_status(1)
        == ExecutionStatus.FAILED
    )

    retry_decision = create_decision(
        task_id=1,
        action=DecisionAction.RETRY,
    )

    bridge.apply_decision(retry_decision)

    assert (
        state_manager.get_status(1)
        == ExecutionStatus.RETRYING
    )


# =============================================================================
# E-7.10 UNKNOWN TASK
# =============================================================================


def test_decision_for_unregistered_task_is_rejected():
    """
    The bridge must not silently create runtime state for an unknown task.
    """

    state_manager = StateManager()
    bridge = DecisionStateBridge(state_manager)

    decision = create_decision(
        task_id=999,
        action=DecisionAction.COMPLETE,
    )

    with pytest.raises(KeyError):
        bridge.apply_decision(decision)