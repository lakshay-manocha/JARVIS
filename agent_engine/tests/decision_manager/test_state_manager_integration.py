"""
===============================================================================
File Name   : test_state_manager_integration.py
Module      : Decision Manager / State Manager Integration Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Phase F:
    F.6 - StateManager Integration

Purpose:
    Verify that DecisionStateBridge correctly translates DecisionResult
    objects into legal StateManager runtime state transitions.

The bridge translates decisions into target execution states.

The StateManager remains the owner of:
    - Runtime state
    - State transition validation
    - State history

These tests intentionally follow the legal execution lifecycle defined by
StateTransitionPolicy.
===============================================================================
"""

from agent_engine.contracts.enums import ExecutionStatus
from agent_engine.decision_manager import (
    DecisionAction,
    DecisionResult,
    FailureType,
)
from agent_engine.integration.decision_state_bridge import (
    DecisionStateBridge,
)
from agent_engine.state_manager.state_manager import (
    StateManager,
)


# =============================================================================
# Test Helpers
# =============================================================================


def build_decision(
    *,
    task_id: int,
    action: DecisionAction,
    failure_type: FailureType = FailureType.NONE,
) -> DecisionResult:
    """
    Build a DecisionResult for integration testing.
    """

    return DecisionResult(
        action=action,
        task_id=task_id,
        reason=f"Test decision: {action.value}",
        attempt=1,
        max_retries=2,
        failure_type=failure_type,
    )


def create_bridge() -> tuple[StateManager, DecisionStateBridge]:
    """
    Create a fresh StateManager and DecisionStateBridge.
    """

    state_manager = StateManager()
    bridge = DecisionStateBridge(
        state_manager=state_manager,
    )

    return state_manager, bridge


def move_task_to_ready(
    state_manager: StateManager,
    task_id: int,
) -> None:
    """
    Move a registered task from PENDING to READY.

    This follows the legal StateTransitionPolicy lifecycle.
    """

    state_manager.set_state(
        task_id,
        ExecutionStatus.READY,
    )


def move_task_to_running(
    state_manager: StateManager,
    task_id: int,
) -> None:
    """
    Move a registered task through the normal execution lifecycle:

        PENDING -> READY -> RUNNING
    """

    move_task_to_ready(
        state_manager,
        task_id,
    )

    state_manager.set_state(
        task_id,
        ExecutionStatus.RUNNING,
    )


# =============================================================================
# COMPLETE
# =============================================================================


def test_complete_decision_updates_state_to_completed() -> None:
    """
    Verify:

        DecisionAction.COMPLETE
            ↓
        ExecutionStatus.COMPLETED

    The task must already be RUNNING because COMPLETED is only a legal
    transition from RUNNING.
    """

    state_manager, bridge = create_bridge()

    task_id = 1

    state_manager.register_task(task_id)
    move_task_to_running(
        state_manager,
        task_id,
    )

    decision = build_decision(
        task_id=task_id,
        action=DecisionAction.COMPLETE,
    )

    bridge.apply_decision(decision)

    assert (
        state_manager.get_status(task_id)
        == ExecutionStatus.COMPLETED
    )


# =============================================================================
# FAIL
# =============================================================================


def test_fail_decision_updates_state_to_failed() -> None:
    """
    Verify:

        DecisionAction.FAIL
            ↓
        ExecutionStatus.FAILED

    FAILED is a legal transition from RUNNING.
    """

    state_manager, bridge = create_bridge()

    task_id = 2

    state_manager.register_task(task_id)
    move_task_to_running(
        state_manager,
        task_id,
    )

    decision = build_decision(
        task_id=task_id,
        action=DecisionAction.FAIL,
        failure_type=FailureType.PERMANENT,
    )

    bridge.apply_decision(decision)

    assert (
        state_manager.get_status(task_id)
        == ExecutionStatus.FAILED
    )


# =============================================================================
# RETRY
# =============================================================================


def test_retry_decision_updates_state_to_retrying() -> None:
    """
    Verify:

        DecisionAction.RETRY
            ↓
        ExecutionStatus.RETRYING

    RETRYING is a recovery transition from FAILED, not directly from PENDING.
    """

    state_manager, bridge = create_bridge()

    task_id = 3

    state_manager.register_task(task_id)

    # First execution reaches FAILED.
    move_task_to_running(
        state_manager,
        task_id,
    )

    state_manager.set_state(
        task_id,
        ExecutionStatus.FAILED,
    )

    decision = build_decision(
        task_id=task_id,
        action=DecisionAction.RETRY,
        failure_type=FailureType.TRANSIENT,
    )

    bridge.apply_decision(decision)

    assert (
        state_manager.get_status(task_id)
        == ExecutionStatus.RETRYING
    )


# =============================================================================
# SKIP
# =============================================================================


def test_skip_decision_updates_state_to_skipped() -> None:
    """
    Verify:

        DecisionAction.SKIP
            ↓
        ExecutionStatus.SKIPPED

    SKIPPED is a legal transition from READY.
    """

    state_manager, bridge = create_bridge()

    task_id = 4

    state_manager.register_task(task_id)

    move_task_to_ready(
        state_manager,
        task_id,
    )

    decision = build_decision(
        task_id=task_id,
        action=DecisionAction.SKIP,
        failure_type=FailureType.DEPENDENCY,
    )

    bridge.apply_decision(decision)

    assert (
        state_manager.get_status(task_id)
        == ExecutionStatus.SKIPPED
    )


# =============================================================================
# FALLBACK
# =============================================================================


def test_fallback_decision_moves_task_to_running() -> None:
    """
    Verify:

        FAILED
          ↓
        DecisionAction.FALLBACK
          ↓
        RUNNING

    Fallback is represented by the bridge as a transition back to RUNNING.

    The bridge does NOT execute the fallback action itself.
    """

    state_manager, bridge = create_bridge()

    task_id = 5

    state_manager.register_task(task_id)

    # Simulate the primary execution reaching FAILED.
    move_task_to_running(
        state_manager,
        task_id,
    )

    state_manager.set_state(
        task_id,
        ExecutionStatus.FAILED,
    )

    assert (
        state_manager.get_status(task_id)
        == ExecutionStatus.FAILED
    )

    decision = build_decision(
        task_id=task_id,
        action=DecisionAction.FALLBACK,
    )

    bridge.apply_decision(decision)

    assert (
        state_manager.get_status(task_id)
        == ExecutionStatus.RUNNING
    )


# =============================================================================
# STATE HISTORY
# =============================================================================


def test_state_manager_records_decision_driven_state_changes() -> None:
    """
    Verify that state changes caused through DecisionStateBridge are recorded
    by StateManager history.

    Expected lifecycle:

        PENDING
          ↓
        READY
          ↓
        RUNNING
          ↓
        FAILED
          ↓
        RUNNING

    The final RUNNING state represents fallback recovery.
    """

    state_manager, bridge = create_bridge()

    task_id = 6

    state_manager.register_task(task_id)

    # -------------------------------------------------------------------------
    # Primary execution lifecycle
    # -------------------------------------------------------------------------

    move_task_to_running(
        state_manager,
        task_id,
    )

    # -------------------------------------------------------------------------
    # Decision Manager decides FAIL
    # -------------------------------------------------------------------------

    fail_decision = build_decision(
        task_id=task_id,
        action=DecisionAction.FAIL,
        failure_type=FailureType.PERMANENT,
    )

    bridge.apply_decision(fail_decision)

    assert (
        state_manager.get_status(task_id)
        == ExecutionStatus.FAILED
    )

    # -------------------------------------------------------------------------
    # Decision Manager decides FALLBACK
    # -------------------------------------------------------------------------

    fallback_decision = build_decision(
        task_id=task_id,
        action=DecisionAction.FALLBACK,
    )

    bridge.apply_decision(fallback_decision)

    assert (
        state_manager.get_status(task_id)
        == ExecutionStatus.RUNNING
    )

    # -------------------------------------------------------------------------
    # Verify complete history
    # -------------------------------------------------------------------------

    history = state_manager.get_history(task_id)

    states = [
        entry.to_status
        for entry in history
    ]

    assert states == [
        ExecutionStatus.PENDING,
        ExecutionStatus.READY,
        ExecutionStatus.RUNNING,
        ExecutionStatus.FAILED,
        ExecutionStatus.RUNNING,
    ]


# =============================================================================
# BRIDGE RESPONSIBILITY
# =============================================================================


def test_bridge_only_updates_state() -> None:
    """
    Verify that DecisionStateBridge only translates the decision into a
    StateManager state update.

    It does not:
        - execute a task
        - retry a task
        - execute fallback automation
        - modify the DecisionResult
    """

    state_manager, bridge = create_bridge()

    task_id = 7

    state_manager.register_task(task_id)

    # RETRYING is reached from FAILED.
    move_task_to_running(
        state_manager,
        task_id,
    )

    state_manager.set_state(
        task_id,
        ExecutionStatus.FAILED,
    )

    decision = build_decision(
        task_id=task_id,
        action=DecisionAction.RETRY,
        failure_type=FailureType.TRANSIENT,
    )

    result = bridge.apply_decision(decision)

    assert (
        state_manager.get_status(task_id)
        == ExecutionStatus.RETRYING
    )

    # StateManager.set_state() returns TaskRuntimeState.
    assert result is not None

    # The decision itself must remain unchanged.
    assert decision.action == DecisionAction.RETRY
    assert decision.task_id == task_id