"""
===============================================================================
File Name   : test_state_manager_registration.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Phase E-2.1:
    Batch Task Registration.
===============================================================================
"""

from agent_engine.contracts.enums import ExecutionStatus
from agent_engine.state_manager.state_manager import StateManager


# =============================================================================
# Basic batch registration
# =============================================================================


def test_register_multiple_tasks() -> None:
    manager = StateManager()

    states = manager.register_tasks([1, 2, 3])

    assert len(states) == 3
    assert manager.task_ids() == [1, 2, 3]


# =============================================================================
# Initial state
# =============================================================================


def test_registered_tasks_start_as_pending() -> None:
    manager = StateManager()

    manager.register_tasks([1, 2, 3])

    assert manager.get_status(1) == ExecutionStatus.PENDING
    assert manager.get_status(2) == ExecutionStatus.PENDING
    assert manager.get_status(3) == ExecutionStatus.PENDING


# =============================================================================
# Idempotency
# =============================================================================


def test_duplicate_registration_preserves_existing_state() -> None:
    manager = StateManager()

    manager.register_tasks([1, 2, 3])

    manager.set_state(
        2,
        ExecutionStatus.RUNNING,
    )

    manager.register_tasks([1, 2, 3])

    assert manager.get_status(1) == ExecutionStatus.PENDING
    assert manager.get_status(2) == ExecutionStatus.RUNNING
    assert manager.get_status(3) == ExecutionStatus.PENDING


# =============================================================================
# Partial duplicate registration
# =============================================================================


def test_batch_registration_preserves_existing_and_adds_new_tasks() -> None:
    manager = StateManager()

    manager.register_tasks([1, 2])

    manager.set_state(
        1,
        ExecutionStatus.RUNNING,
    )

    manager.register_tasks([1, 2, 3, 4])

    assert manager.get_status(1) == ExecutionStatus.RUNNING
    assert manager.get_status(2) == ExecutionStatus.PENDING
    assert manager.get_status(3) == ExecutionStatus.PENDING
    assert manager.get_status(4) == ExecutionStatus.PENDING


# =============================================================================
# Returned states
# =============================================================================


def test_register_tasks_returns_runtime_states() -> None:
    manager = StateManager()

    states = manager.register_tasks([10, 20])

    assert states[0].task_id == 10
    assert states[1].task_id == 20

    assert states[0].status == ExecutionStatus.PENDING
    assert states[1].status == ExecutionStatus.PENDING


# =============================================================================
# Empty registration
# =============================================================================


def test_register_empty_task_list() -> None:
    manager = StateManager()

    states = manager.register_tasks([])

    assert states == []
    assert manager.task_ids() == []