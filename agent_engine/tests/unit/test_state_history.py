"""
===============================================================================
File Name   : test_state_history.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Phase E-4:
    State History.

Tests:
    - Initial history creation
    - Transition history
    - Ordered history
    - Retry history
    - Waiting history
    - Invalid transition history protection
    - Idempotent transition protection
    - update_state() history integration
    - History immutability
    - Unknown task handling
    - Task removal
    - Registry clearing
===============================================================================
"""

import pytest

from agent_engine.contracts.enums import ExecutionStatus
from agent_engine.state_manager.state_history import StateHistoryEntry
from agent_engine.state_manager.state_manager import StateManager
from agent_engine.state_manager.state_transitions import (
    InvalidStateTransitionError,
)


# =============================================================================
# Helpers
# =============================================================================


@pytest.fixture
def manager() -> StateManager:
    manager = StateManager()
    manager.register_task(1)
    return manager


# =============================================================================
# Initial history
# =============================================================================


def test_register_task_creates_initial_history_entry() -> None:

    manager = StateManager()

    manager.register_task(1)

    history = manager.get_history(1)

    assert len(history) == 1

    entry = history[0]

    assert isinstance(entry, StateHistoryEntry)
    assert entry.task_id == 1
    assert entry.from_status is None
    assert entry.to_status == ExecutionStatus.PENDING


def test_registering_same_task_does_not_duplicate_history() -> None:

    manager = StateManager()

    manager.register_task(1)
    first_history = manager.get_history(1)

    manager.register_task(1)
    second_history = manager.get_history(1)

    assert len(first_history) == 1
    assert len(second_history) == 1


# =============================================================================
# Normal lifecycle
# =============================================================================


def test_history_records_normal_lifecycle(
    manager: StateManager,
) -> None:

    manager.set_state(1, ExecutionStatus.READY)
    manager.set_state(1, ExecutionStatus.RUNNING)
    manager.set_state(1, ExecutionStatus.COMPLETED)

    history = manager.get_history(1)

    assert len(history) == 4

    assert history[0].from_status is None
    assert history[0].to_status == ExecutionStatus.PENDING

    assert history[1].from_status == ExecutionStatus.PENDING
    assert history[1].to_status == ExecutionStatus.READY

    assert history[2].from_status == ExecutionStatus.READY
    assert history[2].to_status == ExecutionStatus.RUNNING

    assert history[3].from_status == ExecutionStatus.RUNNING
    assert history[3].to_status == ExecutionStatus.COMPLETED


# =============================================================================
# Retry lifecycle
# =============================================================================


def test_history_records_retry_lifecycle(
    manager: StateManager,
) -> None:

    manager.set_state(1, ExecutionStatus.READY)
    manager.set_state(1, ExecutionStatus.RUNNING)
    manager.set_state(1, ExecutionStatus.FAILED)
    manager.set_state(1, ExecutionStatus.RETRYING)
    manager.set_state(1, ExecutionStatus.RUNNING)
    manager.set_state(1, ExecutionStatus.COMPLETED)

    history = manager.get_history(1)

    statuses = [entry.to_status for entry in history]

    assert statuses == [
        ExecutionStatus.PENDING,
        ExecutionStatus.READY,
        ExecutionStatus.RUNNING,
        ExecutionStatus.FAILED,
        ExecutionStatus.RETRYING,
        ExecutionStatus.RUNNING,
        ExecutionStatus.COMPLETED,
    ]


# =============================================================================
# Waiting lifecycle
# =============================================================================


def test_history_records_waiting_and_resume(
    manager: StateManager,
) -> None:

    manager.set_state(1, ExecutionStatus.READY)
    manager.set_state(1, ExecutionStatus.RUNNING)
    manager.set_state(1, ExecutionStatus.WAITING)
    manager.set_state(1, ExecutionStatus.RUNNING)

    history = manager.get_history(1)

    statuses = [entry.to_status for entry in history]

    assert statuses == [
        ExecutionStatus.PENDING,
        ExecutionStatus.READY,
        ExecutionStatus.RUNNING,
        ExecutionStatus.WAITING,
        ExecutionStatus.RUNNING,
    ]


# =============================================================================
# Cancellation
# =============================================================================


def test_history_records_cancellation(
    manager: StateManager,
) -> None:

    manager.set_state(1, ExecutionStatus.READY)
    manager.set_state(1, ExecutionStatus.CANCELLED)

    history = manager.get_history(1)

    assert history[-1].from_status == ExecutionStatus.READY
    assert history[-1].to_status == ExecutionStatus.CANCELLED


# =============================================================================
# Invalid transitions
# =============================================================================


def test_invalid_transition_does_not_create_history_entry(
    manager: StateManager,
) -> None:

    initial_history = manager.get_history(1)

    with pytest.raises(InvalidStateTransitionError):
        manager.set_state(
            1,
            ExecutionStatus.RUNNING,
        )

    history = manager.get_history(1)

    assert len(history) == len(initial_history)
    assert history == initial_history


# =============================================================================
# Idempotent transitions
# =============================================================================


def test_same_state_transition_does_not_create_duplicate_history(
    manager: StateManager,
) -> None:

    manager.set_state(1, ExecutionStatus.READY)

    history_before = manager.get_history(1)

    manager.set_state(1, ExecutionStatus.READY)

    history_after = manager.get_history(1)

    assert len(history_before) == 2
    assert len(history_after) == 2
    assert history_before == history_after


# =============================================================================
# update_state integration
# =============================================================================


def test_update_state_records_status_transition(
    manager: StateManager,
) -> None:

    manager.update_state(
        1,
        status=ExecutionStatus.READY,
    )

    manager.update_state(
        1,
        status=ExecutionStatus.RUNNING,
    )

    history = manager.get_history(1)

    assert [entry.to_status for entry in history] == [
        ExecutionStatus.PENDING,
        ExecutionStatus.READY,
        ExecutionStatus.RUNNING,
    ]


def test_update_state_without_status_does_not_create_history(
    manager: StateManager,
) -> None:

    history_before = manager.get_history(1)

    manager.update_state(
        1,
        progress=50.0,
        retry_count=1,
    )

    history_after = manager.get_history(1)

    assert history_after == history_before


# =============================================================================
# History timestamps
# =============================================================================


def test_history_entries_have_timestamps(
    manager: StateManager,
) -> None:

    manager.set_state(1, ExecutionStatus.READY)

    history = manager.get_history(1)

    assert history[0].timestamp is not None
    assert history[1].timestamp is not None


def test_history_timestamps_are_ordered(
    manager: StateManager,
) -> None:

    manager.set_state(1, ExecutionStatus.READY)
    manager.set_state(1, ExecutionStatus.RUNNING)
    manager.set_state(1, ExecutionStatus.COMPLETED)

    history = manager.get_history(1)

    timestamps = [entry.timestamp for entry in history]

    assert timestamps == sorted(timestamps)


# =============================================================================
# History immutability
# =============================================================================


def test_history_returns_immutable_sequence(
    manager: StateManager,
) -> None:

    history = manager.get_history(1)

    assert isinstance(history, tuple)

    with pytest.raises(AttributeError):
        history.append("invalid")  # type: ignore[attr-defined]


def test_history_entries_are_immutable(
    manager: StateManager,
) -> None:

    history = manager.get_history(1)

    with pytest.raises(AttributeError):
        history[0].to_status = ExecutionStatus.RUNNING  # type: ignore[misc]


def test_history_mapping_is_read_only(
    manager: StateManager,
) -> None:

    history = manager.history()

    with pytest.raises(TypeError):
        history[2] = ()  # type: ignore[index]


# =============================================================================
# Unknown task
# =============================================================================


def test_get_history_unknown_task_raises_key_error() -> None:

    manager = StateManager()

    with pytest.raises(KeyError):
        manager.get_history(999)


# =============================================================================
# Removal
# =============================================================================


def test_remove_task_removes_history() -> None:

    manager = StateManager()

    manager.register_task(1)
    manager.set_state(1, ExecutionStatus.READY)

    manager.remove_task(1)

    assert manager.has_task(1) is False

    with pytest.raises(KeyError):
        manager.get_history(1)


# =============================================================================
# Clear
# =============================================================================


def test_clear_removes_all_history() -> None:

    manager = StateManager()

    manager.register_task(1)
    manager.register_task(2)

    manager.set_state(1, ExecutionStatus.READY)
    manager.set_state(2, ExecutionStatus.READY)

    manager.clear()

    assert manager.task_ids() == []
    assert manager.history() == {}