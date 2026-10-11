"""
===============================================================================
File Name   : test_state_manager_transitions.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Phase E-3:
    StateManager transition enforcement.
===============================================================================
"""

import pytest

from agent_engine.contracts.enums import ExecutionStatus
from agent_engine.state_manager.state_manager import StateManager
from agent_engine.state_manager.state_transitions import (
    InvalidStateTransitionError,
)


@pytest.fixture
def manager() -> StateManager:
    manager = StateManager()
    manager.register_task(1)
    return manager


# =============================================================================
# Valid lifecycle
# =============================================================================


def test_task_can_follow_normal_execution_lifecycle(
    manager: StateManager,
) -> None:

    manager.set_state(1, ExecutionStatus.READY)
    manager.set_state(1, ExecutionStatus.RUNNING)
    manager.set_state(1, ExecutionStatus.COMPLETED)

    assert (
        manager.get_status(1)
        == ExecutionStatus.COMPLETED
    )


# =============================================================================
# Retry lifecycle
# =============================================================================


def test_task_can_follow_retry_lifecycle(
    manager: StateManager,
) -> None:

    manager.set_state(1, ExecutionStatus.READY)
    manager.set_state(1, ExecutionStatus.RUNNING)
    manager.set_state(1, ExecutionStatus.FAILED)
    manager.set_state(1, ExecutionStatus.RETRYING)
    manager.set_state(1, ExecutionStatus.RUNNING)
    manager.set_state(1, ExecutionStatus.COMPLETED)

    assert (
        manager.get_status(1)
        == ExecutionStatus.COMPLETED
    )


# =============================================================================
# Waiting lifecycle
# =============================================================================


def test_task_can_resume_from_waiting(
    manager: StateManager,
) -> None:

    manager.set_state(1, ExecutionStatus.READY)
    manager.set_state(1, ExecutionStatus.RUNNING)
    manager.set_state(1, ExecutionStatus.WAITING)
    manager.set_state(1, ExecutionStatus.RUNNING)

    assert (
        manager.get_status(1)
        == ExecutionStatus.RUNNING
    )


# =============================================================================
# Invalid transition
# =============================================================================


def test_invalid_transition_is_rejected(
    manager: StateManager,
) -> None:

    with pytest.raises(InvalidStateTransitionError):

        manager.set_state(
            1,
            ExecutionStatus.COMPLETED,
        )


def test_terminal_state_cannot_be_changed(
    manager: StateManager,
) -> None:

    manager.set_state(1, ExecutionStatus.CANCELLED)

    with pytest.raises(InvalidStateTransitionError):

        manager.set_state(
            1,
            ExecutionStatus.RUNNING,
        )
def test_pending_cannot_skip_ready(
    manager: StateManager,
) -> None:

    with pytest.raises(InvalidStateTransitionError):
        manager.set_state(
            1,
            ExecutionStatus.RUNNING,
        )

# =============================================================================
# update_state must also enforce transitions
# =============================================================================


def test_update_state_enforces_transition_rules(
    manager: StateManager,
) -> None:

    with pytest.raises(InvalidStateTransitionError):

        manager.update_state(
            1,
            status=ExecutionStatus.COMPLETED,
        )


def test_update_state_allows_valid_transition(
    manager: StateManager,
) -> None:

    state = manager.update_state(
        1,
        status=ExecutionStatus.READY,
        progress=10.0,
    )

    assert state.status == ExecutionStatus.READY
    assert state.progress == 10.0