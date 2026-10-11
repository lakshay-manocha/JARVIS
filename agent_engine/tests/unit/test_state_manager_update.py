"""
===============================================================================
File Name   : test_state_manager_update.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Phase E-2.2:
    Runtime state update API.
===============================================================================
"""

from datetime import datetime

import pytest

from agent_engine.contracts.enums import ExecutionStatus
from agent_engine.state_manager.state_manager import StateManager


# =============================================================================
# Helpers
# =============================================================================


@pytest.fixture
def manager() -> StateManager:
    manager = StateManager()
    manager.register_task(1)
    return manager


# =============================================================================
# Progress
# =============================================================================


def test_update_progress(manager: StateManager) -> None:

    state = manager.update_state(
        1,
        progress=50.0,
    )

    assert state.progress == 50.0
    assert manager.get_state(1).progress == 50.0


# =============================================================================
# Retry count
# =============================================================================


def test_update_retry_count(manager: StateManager) -> None:

    state = manager.update_state(
        1,
        retry_count=2,
    )

    assert state.retry_count == 2


# =============================================================================
# Timing information
# =============================================================================


def test_update_timing_information(manager: StateManager) -> None:

    started = datetime.now()
    completed = datetime.now()

    state = manager.update_state(
        1,
        started_at=started,
        completed_at=completed,
        execution_time=12.5,
    )

    assert state.started_at == started
    assert state.completed_at == completed
    assert state.execution_time == 12.5


# =============================================================================
# Error information
# =============================================================================


def test_update_error_information(manager: StateManager) -> None:

    state = manager.update_state(
        1,
        error_message="Browser failed",
        error_code="BROWSER_ERROR",
    )

    assert state.error_message == "Browser failed"
    assert state.error_code == "BROWSER_ERROR"


# =============================================================================
# Multiple fields
# =============================================================================


def test_update_multiple_fields(manager: StateManager) -> None:

    manager.set_state(
        1,
        ExecutionStatus.READY,
    )

    state = manager.update_state(
        1,
        status=ExecutionStatus.RUNNING,
        progress=40.0,
        retry_count=1,
        execution_time=5.5,
    )

    assert state.status == ExecutionStatus.RUNNING
    assert state.progress == 40.0
    assert state.retry_count == 1
    assert state.execution_time == 5.5


# =============================================================================
# Preserve unspecified fields
# =============================================================================


def test_update_preserves_unspecified_fields(
    manager: StateManager,
) -> None:

    manager.update_state(
        1,
        progress=75.0,
    )

    state = manager.get_state(1)

    assert state.progress == 75.0
    assert state.retry_count == 0
    assert state.status == ExecutionStatus.PENDING
    assert state.started_at is None
    assert state.completed_at is None


# =============================================================================
# Unknown task
# =============================================================================


def test_update_unknown_task_raises_key_error(
    manager: StateManager,
) -> None:

    with pytest.raises(KeyError):

        manager.update_state(
            999,
            progress=50.0,
        )


# =============================================================================
# Invalid progress
# =============================================================================


def test_invalid_progress_is_rejected(
    manager: StateManager,
) -> None:

    with pytest.raises(ValueError):

        manager.update_state(
            1,
            progress=150.0,
        )


# =============================================================================
# Invalid retry count
# =============================================================================


def test_invalid_retry_count_is_rejected(
    manager: StateManager,
) -> None:

    with pytest.raises(ValueError):

        manager.update_state(
            1,
            retry_count=-1,
        )


# =============================================================================
# Unknown field
# =============================================================================


def test_unknown_field_is_rejected(
    manager: StateManager,
) -> None:

    with pytest.raises(ValueError):

        manager.update_state(
            1,
            unknown_field="invalid",
        )