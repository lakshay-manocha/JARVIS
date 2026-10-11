"""
===============================================================================
File Name   : test_state_transitions.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Phase E-3:
    State transition validation.
===============================================================================
"""

import pytest

from agent_engine.contracts.enums import ExecutionStatus
from agent_engine.state_manager.state_transitions import (
    InvalidStateTransitionError,
    StateTransitionPolicy,
)


# =============================================================================
# Legal transitions
# =============================================================================


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (
            ExecutionStatus.PENDING,
            ExecutionStatus.READY,
        ),
        (
            ExecutionStatus.PENDING,
            ExecutionStatus.CANCELLED,
        ),
        (
            ExecutionStatus.READY,
            ExecutionStatus.RUNNING,
        ),
        (
            ExecutionStatus.READY,
            ExecutionStatus.CANCELLED,
        ),
        (
            ExecutionStatus.RUNNING,
            ExecutionStatus.WAITING,
        ),
        (
            ExecutionStatus.RUNNING,
            ExecutionStatus.COMPLETED,
        ),
        (
            ExecutionStatus.RUNNING,
            ExecutionStatus.FAILED,
        ),
        (
            ExecutionStatus.RUNNING,
            ExecutionStatus.CANCELLED,
        ),
        (
            ExecutionStatus.WAITING,
            ExecutionStatus.RUNNING,
        ),
        (
            ExecutionStatus.WAITING,
            ExecutionStatus.CANCELLED,
        ),
        (
            ExecutionStatus.FAILED,
            ExecutionStatus.RETRYING,
        ),
        (
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
        ),
        (
            ExecutionStatus.RETRYING,
            ExecutionStatus.RUNNING,
        ),
        (
            ExecutionStatus.RETRYING,
            ExecutionStatus.FAILED,
        ),
        (
            ExecutionStatus.RETRYING,
            ExecutionStatus.CANCELLED,
        ),
    ],
)
def test_legal_transition(
    current: ExecutionStatus,
    target: ExecutionStatus,
) -> None:

    assert StateTransitionPolicy.can_transition(
        current,
        target,
    ) is True

    StateTransitionPolicy.validate_transition(
        current,
        target,
    )


# =============================================================================
# Same-state transition
# =============================================================================


@pytest.mark.parametrize(
    "status",
    list(ExecutionStatus),
)
def test_same_state_transition_is_allowed(
    status: ExecutionStatus,
) -> None:

    assert StateTransitionPolicy.can_transition(
        status,
        status,
    ) is True


# =============================================================================
# Illegal transitions
# =============================================================================


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (
            ExecutionStatus.PENDING,
            ExecutionStatus.COMPLETED,
        ),
        (
            ExecutionStatus.PENDING,
            ExecutionStatus.RUNNING,
        ),
        (
            ExecutionStatus.READY,
            ExecutionStatus.COMPLETED,
        ),
        (
            ExecutionStatus.RUNNING,
            ExecutionStatus.READY,
        ),
        (
            ExecutionStatus.COMPLETED,
            ExecutionStatus.RUNNING,
        ),
        (
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
        ),
        (
            ExecutionStatus.CANCELLED,
            ExecutionStatus.RUNNING,
        ),
        (
            ExecutionStatus.CANCELLED,
            ExecutionStatus.PENDING,
        ),
        (
            ExecutionStatus.FAILED,
            ExecutionStatus.COMPLETED,
        ),
    ],
)
def test_illegal_transition(
    current: ExecutionStatus,
    target: ExecutionStatus,
) -> None:

    assert StateTransitionPolicy.can_transition(
        current,
        target,
    ) is False

    with pytest.raises(InvalidStateTransitionError):

        StateTransitionPolicy.validate_transition(
            current,
            target,
        )


# =============================================================================
# Terminal states
# =============================================================================


def test_completed_is_terminal() -> None:

    assert (
        StateTransitionPolicy.allowed_transitions(
            ExecutionStatus.COMPLETED,
        )
        == frozenset()
    )


def test_cancelled_is_terminal() -> None:

    assert (
        StateTransitionPolicy.allowed_transitions(
            ExecutionStatus.CANCELLED,
        )
        == frozenset()
    )


# =============================================================================
# Allowed transition inspection
# =============================================================================


def test_allowed_transitions_for_failed_state():
    allowed = StateTransitionPolicy.allowed_transitions(
        ExecutionStatus.FAILED
    )

    assert allowed == frozenset({
        ExecutionStatus.RETRYING,
        ExecutionStatus.RUNNING,
        ExecutionStatus.CANCELLED,
    })
    
def test_running_can_transition_to_paused():
    assert StateTransitionPolicy.can_transition(
        ExecutionStatus.RUNNING,
        ExecutionStatus.PAUSED,
    )


def test_paused_can_transition_to_running():
    assert StateTransitionPolicy.can_transition(
        ExecutionStatus.PAUSED,
        ExecutionStatus.RUNNING,
    )


def test_paused_can_transition_to_stopped():
    assert StateTransitionPolicy.can_transition(
        ExecutionStatus.PAUSED,
        ExecutionStatus.STOPPED,
    )


def test_running_can_transition_to_stopped():
    assert StateTransitionPolicy.can_transition(
        ExecutionStatus.RUNNING,
        ExecutionStatus.STOPPED,
    )


def test_stopped_is_terminal():
    assert StateTransitionPolicy.allowed_transitions(
        ExecutionStatus.STOPPED
    ) == frozenset()


def test_completed_cannot_resume():
    assert not StateTransitionPolicy.can_transition(
        ExecutionStatus.COMPLETED,
        ExecutionStatus.RUNNING,
    )


def test_stopped_cannot_resume():
    assert not StateTransitionPolicy.can_transition(
        ExecutionStatus.STOPPED,
        ExecutionStatus.RUNNING,
    )