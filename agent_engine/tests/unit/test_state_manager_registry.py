"""
===============================================================================
File Name   : test_state_manager_registry.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Phase E-2.3:
    State registry inspection and ownership.
===============================================================================
"""

import pytest

from agent_engine.contracts.enums import ExecutionStatus
from agent_engine.state_manager.state_manager import StateManager


# =============================================================================
# Registry inspection
# =============================================================================


def test_states_returns_registered_states() -> None:

    manager = StateManager()

    manager.register_task(1)
    manager.register_task(2)

    states = manager.states()

    assert set(states.keys()) == {1, 2}
    assert states[1].task_id == 1
    assert states[2].task_id == 2


def test_states_reflect_current_runtime_state() -> None:

    manager = StateManager()

    manager.register_task(1)

    manager.set_state(
        1,
        ExecutionStatus.READY,
    )

    manager.set_state(
        1,
        ExecutionStatus.RUNNING,
    )

    states = manager.states()

    assert states[1].status == ExecutionStatus.RUNNING


# =============================================================================
# Registry ownership
# =============================================================================


def test_states_mapping_is_read_only() -> None:

    manager = StateManager()

    manager.register_task(1)

    states = manager.states()

    with pytest.raises(TypeError):

        states[2] = manager.get_state(1)


def test_states_mapping_cannot_delete_entries() -> None:

    manager = StateManager()

    manager.register_task(1)

    states = manager.states()

    with pytest.raises(TypeError):

        del states[1]


# =============================================================================
# State objects remain accessible for inspection
# =============================================================================


def test_registered_state_can_be_read() -> None:

    manager = StateManager()

    manager.register_task(1)

    state = manager.states()[1]

    assert state.task_id == 1
    assert state.status == ExecutionStatus.PENDING


# =============================================================================
# Registry remains authoritative
# =============================================================================


def test_registry_remains_authoritative_after_failed_external_mutation() -> None:

    manager = StateManager()

    manager.register_task(1)

    states = manager.states()

    with pytest.raises(TypeError):

        states[2] = manager.get_state(1)

    assert manager.task_ids() == [1]
    assert manager.has_task(1) is True
    assert manager.has_task(2) is False