"""
===============================================================================
File Name   : test_state_manager.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Tests for:

E-1:
    State Manager Foundation.
===============================================================================
"""

import pytest

from agent_engine.contracts.enums import ExecutionStatus
from agent_engine.state_manager import StateManager


# =============================================================================
# Registration
# =============================================================================


def test_register_task_initializes_pending_state() -> None:

    manager = StateManager()

    state = manager.register_task(1)

    assert state.task_id == 1
    assert state.status == ExecutionStatus.PENDING


def test_registering_same_task_is_idempotent() -> None:

    manager = StateManager()

    first = manager.register_task(1)
    second = manager.register_task(1)

    assert first is second
    assert manager.task_ids() == [1]


# =============================================================================
# State Access
# =============================================================================


def test_get_state_returns_registered_state() -> None:

    manager = StateManager()

    manager.register_task(1)

    state = manager.get_state(1)

    assert state.task_id == 1
    assert state.status == ExecutionStatus.PENDING


def test_get_status_returns_current_status() -> None:

    manager = StateManager()

    manager.register_task(1)

    manager.set_state(1, ExecutionStatus.READY)
    manager.set_state(1, ExecutionStatus.RUNNING)

    assert manager.get_status(1) == ExecutionStatus.RUNNING


def test_unknown_task_raises_key_error() -> None:

    manager = StateManager()

    with pytest.raises(KeyError):
        manager.get_state(999)


# =============================================================================
# State Mutation
# =============================================================================


def test_set_state_updates_status() -> None:

    manager = StateManager()

    manager.register_task(1)

    manager.set_state(1, ExecutionStatus.READY)

    state = manager.set_state(
        1,
        ExecutionStatus.RUNNING,
    )

    assert state.status == ExecutionStatus.RUNNING
    assert manager.get_status(1) == ExecutionStatus.RUNNING


def test_state_can_transition_to_completed() -> None:

    manager = StateManager()

    manager.register_task(1)

    manager.set_state(1, ExecutionStatus.READY)
    manager.set_state(1, ExecutionStatus.RUNNING)
    manager.set_state(1, ExecutionStatus.COMPLETED)

    assert manager.get_status(1) == ExecutionStatus.COMPLETED


def test_state_can_transition_to_failed() -> None:

    manager = StateManager()

    manager.register_task(1)

    manager.set_state(1, ExecutionStatus.READY)
    manager.set_state(1, ExecutionStatus.RUNNING)
    manager.set_state(1, ExecutionStatus.FAILED)

    assert manager.get_status(1) == ExecutionStatus.FAILED


# =============================================================================
# Registry
# =============================================================================


def test_has_task() -> None:

    manager = StateManager()

    assert manager.has_task(1) is False

    manager.register_task(1)

    assert manager.has_task(1) is True


def test_task_ids_returns_registered_tasks() -> None:

    manager = StateManager()

    manager.register_task(1)
    manager.register_task(2)
    manager.register_task(3)

    assert manager.task_ids() == [1, 2, 3]


# =============================================================================
# Removal
# =============================================================================


def test_remove_task() -> None:

    manager = StateManager()

    manager.register_task(1)

    manager.remove_task(1)

    assert manager.has_task(1) is False


def test_clear_removes_all_states() -> None:

    manager = StateManager()

    manager.register_task(1)
    manager.register_task(2)

    manager.clear()

    assert manager.task_ids() == []