"""
===============================================================================
File Name   : test_state_manager_pause_resume.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Phase E-6:
    Pause / Resume.

Tests:
    - RUNNING -> PAUSED
    - PAUSED -> RUNNING
    - pause creates checkpoint
    - resume restores checkpoint runtime data
    - pause/resume history
    - invalid pause
    - invalid resume
    - STOPPED behavior
===============================================================================
"""

import pytest

from agent_engine.contracts.enums import ExecutionStatus
from agent_engine.state_manager.state_manager import StateManager
from agent_engine.state_manager.state_transitions import (
    InvalidStateTransitionError,
    StateTransitionPolicy,
)


# =============================================================================
# Pause
# =============================================================================


def test_pause_running_task_creates_checkpoint():
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

    checkpoint = manager.pause_task(1)

    assert checkpoint.task_id == 1
    assert checkpoint.status == ExecutionStatus.RUNNING
    assert manager.get_status(1) == ExecutionStatus.PAUSED


def test_pause_creates_checkpoint_before_paused_state():
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

    checkpoint = manager.pause_task(1)

    assert checkpoint.status == ExecutionStatus.RUNNING
    assert manager.get_status(1) == ExecutionStatus.PAUSED


def test_pause_records_history():
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

    manager.pause_task(1)

    history = manager.get_history(1)

    assert history[-1].from_status == ExecutionStatus.RUNNING
    assert history[-1].to_status == ExecutionStatus.PAUSED


def test_pause_rejects_non_running_task():
    manager = StateManager()

    manager.register_task(1)

    with pytest.raises(InvalidStateTransitionError):
        manager.pause_task(1)


# =============================================================================
# Resume
# =============================================================================


def test_resume_paused_task():
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

    manager.pause_task(1)

    manager.resume_task(1)

    assert manager.get_status(1) == ExecutionStatus.RUNNING


def test_resume_restores_checkpoint_runtime_data():
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

    manager.update_state(
        1,
        retry_count=2,
        progress=65.0,
        error_message="temporary error",
        error_code="TEMP_ERROR",
    )

    checkpoint = manager.pause_task(1)

    manager.update_state(
        1,
        retry_count=99,
        progress=10.0,
        error_message="modified",
        error_code="MODIFIED",
    )

    manager.resume_task(1)

    state = manager.get_state(1)

    assert state.status == ExecutionStatus.RUNNING
    assert state.retry_count == checkpoint.retry_count
    assert state.progress == checkpoint.progress
    assert state.error_message == checkpoint.error_message
    assert state.error_code == checkpoint.error_code


def test_resume_records_history():
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

    manager.pause_task(1)
    manager.resume_task(1)

    history = manager.get_history(1)

    assert history[-1].from_status == ExecutionStatus.PAUSED
    assert history[-1].to_status == ExecutionStatus.RUNNING


def test_resume_does_not_create_new_checkpoint():
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

    manager.pause_task(1)

    checkpoints_before = manager.get_checkpoints(1)

    manager.resume_task(1)

    checkpoints_after = manager.get_checkpoints(1)

    assert checkpoints_after == checkpoints_before


def test_resume_without_checkpoint_fails():
    manager = StateManager()

    manager.register_task(1)

    # Manually enter PAUSED to isolate the checkpoint requirement.
    manager._states[1].status = ExecutionStatus.PAUSED

    with pytest.raises(KeyError):
        manager.resume_task(1)


def test_resume_rejects_non_paused_task():
    manager = StateManager()

    manager.register_task(1)

    with pytest.raises(InvalidStateTransitionError):
        manager.resume_task(1)


# =============================================================================
# Stop
# =============================================================================


def test_running_task_can_be_stopped():
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

    manager.stop_task(1)

    assert manager.get_status(1) == ExecutionStatus.STOPPED


def test_paused_task_can_be_stopped():
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

    manager.pause_task(1)
    manager.stop_task(1)

    assert manager.get_status(1) == ExecutionStatus.STOPPED


def test_stopped_task_cannot_resume():
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

    manager.stop_task(1)

    with pytest.raises(InvalidStateTransitionError):
        manager.resume_task(1)


def test_stopped_task_is_terminal():
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

    manager.stop_task(1)

    with pytest.raises(InvalidStateTransitionError):
        manager.set_state(
            1,
            ExecutionStatus.RUNNING,
        )


# =============================================================================
# Transition policy
# =============================================================================


def test_pause_transition_is_valid():
    assert StateTransitionPolicy.can_transition(
        ExecutionStatus.RUNNING,
        ExecutionStatus.PAUSED,
    )


def test_resume_transition_is_valid():
    assert StateTransitionPolicy.can_transition(
        ExecutionStatus.PAUSED,
        ExecutionStatus.RUNNING,
    )


def test_stopped_is_terminal():
    assert (
        StateTransitionPolicy.allowed_transitions(
            ExecutionStatus.STOPPED,
        )
        == frozenset()
    )