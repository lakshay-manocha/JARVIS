"""
===============================================================================
File Name   : test_state_manager_checkpoints.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Phase E-5:
    Checkpoint Handling.

Tests checkpoint creation, snapshot isolation, retrieval, recovery,
immutability, task ownership, and cleanup.
===============================================================================
"""

from datetime import datetime

import pytest

from agent_engine.contracts.enums import ExecutionStatus
from agent_engine.state_manager.state_checkpoint import StateCheckpoint
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
# Checkpoint Creation
# =============================================================================


def test_create_checkpoint_captures_current_state(
    manager: StateManager,
) -> None:

    started = datetime.now()

    manager.set_state(1, ExecutionStatus.READY)
    manager.set_state(1, ExecutionStatus.RUNNING)

    manager.update_state(
        1,
        retry_count=2,
        progress=65.0,
        started_at=started,
        execution_time=12.5,
        error_message="temporary error",
        error_code="TEMP_ERROR",
    )

    checkpoint = manager.create_checkpoint(1)

    assert checkpoint.task_id == 1
    assert checkpoint.status == ExecutionStatus.RUNNING
    assert checkpoint.retry_count == 2
    assert checkpoint.progress == 65.0
    assert checkpoint.started_at == started
    assert checkpoint.execution_time == 12.5
    assert checkpoint.error_message == "temporary error"
    assert checkpoint.error_code == "TEMP_ERROR"


def test_checkpoint_has_creation_timestamp(
    manager: StateManager,
) -> None:

    before = datetime.now()

    checkpoint = manager.create_checkpoint(1)

    after = datetime.now()

    assert before <= checkpoint.timestamp <= after


# =============================================================================
# Snapshot Isolation
# =============================================================================


def test_checkpoint_is_snapshot_not_live_state(
    manager: StateManager,
) -> None:

    manager.set_state(1, ExecutionStatus.READY)
    manager.set_state(1, ExecutionStatus.RUNNING)

    manager.update_state(
        1,
        progress=25.0,
    )

    checkpoint = manager.create_checkpoint(1)

    manager.update_state(
        1,
        progress=90.0,
    )

    assert checkpoint.progress == 25.0
    assert manager.get_state(1).progress == 90.0


def test_checkpoint_objects_are_immutable(
    manager: StateManager,
) -> None:

    checkpoint = manager.create_checkpoint(1)

    with pytest.raises(Exception):

        checkpoint.progress = 50.0


# =============================================================================
# Checkpoint Retrieval
# =============================================================================


def test_get_checkpoint_returns_latest_checkpoint(
    manager: StateManager,
) -> None:

    manager.create_checkpoint(1)

    manager.set_state(1, ExecutionStatus.READY)

    second = manager.create_checkpoint(1)

    latest = manager.get_checkpoint(1)

    assert latest is second
    assert latest.status == ExecutionStatus.READY


def test_get_checkpoints_returns_all_checkpoints(
    manager: StateManager,
) -> None:

    first = manager.create_checkpoint(1)

    manager.set_state(1, ExecutionStatus.READY)

    second = manager.create_checkpoint(1)

    checkpoints = manager.get_checkpoints(1)

    assert checkpoints == (first, second)


def test_checkpoint_order_is_creation_order(
    manager: StateManager,
) -> None:

    first = manager.create_checkpoint(1)

    manager.set_state(1, ExecutionStatus.READY)

    second = manager.create_checkpoint(1)

    manager.set_state(1, ExecutionStatus.RUNNING)

    third = manager.create_checkpoint(1)

    assert manager.get_checkpoints(1) == (
        first,
        second,
        third,
    )


# =============================================================================
# Checkpoint Registry Ownership
# =============================================================================


def test_checkpoints_mapping_is_read_only(
    manager: StateManager,
) -> None:

    manager.create_checkpoint(1)

    checkpoints = manager.checkpoints()

    with pytest.raises(TypeError):

        checkpoints[2] = checkpoints[1]


def test_checkpoint_sequence_is_immutable(
    manager: StateManager,
) -> None:

    manager.create_checkpoint(1)

    checkpoints = manager.get_checkpoints(1)

    with pytest.raises(AttributeError):

        checkpoints.append(checkpoints[0])


# =============================================================================
# Multiple Tasks
# =============================================================================


def test_checkpoints_are_isolated_between_tasks(
    manager: StateManager,
) -> None:

    manager.register_task(2)

    checkpoint_one = manager.create_checkpoint(1)
    checkpoint_two = manager.create_checkpoint(2)

    assert manager.get_checkpoints(1) == (checkpoint_one,)
    assert manager.get_checkpoints(2) == (checkpoint_two,)

    assert checkpoint_one.task_id == 1
    assert checkpoint_two.task_id == 2


# =============================================================================
# Missing Checkpoints
# =============================================================================


def test_get_checkpoint_without_checkpoint_raises_key_error(
    manager: StateManager,
) -> None:

    with pytest.raises(KeyError):

        manager.get_checkpoint(1)


def test_get_checkpoint_for_unknown_task_raises_key_error(
    manager: StateManager,
) -> None:

    with pytest.raises(KeyError):

        manager.get_checkpoint(999)


def test_get_checkpoints_for_unknown_task_raises_key_error(
    manager: StateManager,
) -> None:

    with pytest.raises(KeyError):

        manager.get_checkpoints(999)


# =============================================================================
# Checkpoint Recovery
# =============================================================================


def test_restore_checkpoint_restores_runtime_fields(
    manager: StateManager,
) -> None:

    manager.set_state(1, ExecutionStatus.READY)
    manager.set_state(1, ExecutionStatus.RUNNING)

    manager.update_state(
        1,
        retry_count=1,
        progress=40.0,
        execution_time=10.0,
        error_message="temporary",
        error_code="TEMP",
    )

    checkpoint = manager.create_checkpoint(1)

    manager.update_state(
        1,
        progress=90.0,
        retry_count=3,
        execution_time=30.0,
        error_message="changed",
        error_code="CHANGED",
    )

    restored = manager.restore_checkpoint(
        1,
        checkpoint,
    )

    assert restored.status == ExecutionStatus.RUNNING
    assert restored.retry_count == 1
    assert restored.progress == 40.0
    assert restored.execution_time == 10.0
    assert restored.error_message == "temporary"
    assert restored.error_code == "TEMP"


def test_restore_checkpoint_preserves_checkpoint_snapshot(
    manager: StateManager,
) -> None:

    manager.set_state(1, ExecutionStatus.READY)
    manager.set_state(1, ExecutionStatus.RUNNING)

    manager.update_state(
        1,
        progress=30.0,
    )

    checkpoint = manager.create_checkpoint(1)

    manager.update_state(
        1,
        progress=80.0,
    )

    manager.restore_checkpoint(
        1,
        checkpoint,
    )

    assert checkpoint.progress == 30.0
    assert manager.get_state(1).progress == 30.0


# =============================================================================
# Recovery and E-3 Enforcement
# =============================================================================


def test_restore_checkpoint_rejects_wrong_task(
    manager: StateManager,
) -> None:

    manager.register_task(2)

    checkpoint = manager.create_checkpoint(1)

    with pytest.raises(ValueError):

        manager.restore_checkpoint(
            2,
            checkpoint,
        )


def test_restore_same_status_checkpoint_is_allowed(
    manager: StateManager,
) -> None:

    manager.set_state(1, ExecutionStatus.READY)

    checkpoint = manager.create_checkpoint(1)

    manager.update_state(
        1,
        progress=75.0,
    )

    restored = manager.restore_checkpoint(
        1,
        checkpoint,
    )

    assert restored.status == ExecutionStatus.READY
    assert restored.progress == checkpoint.progress


# =============================================================================
# History Integration
# =============================================================================


def test_restore_status_change_records_history(
    manager: StateManager,
) -> None:

    manager.set_state(1, ExecutionStatus.READY)

    checkpoint = manager.create_checkpoint(1)

    manager.set_state(1, ExecutionStatus.RUNNING)

    history_before = manager.get_history(1)

    manager.restore_checkpoint(
        1,
        checkpoint,
    )

    history_after = manager.get_history(1)

    assert len(history_after) == len(history_before) + 1

    assert history_after[-1].from_status == ExecutionStatus.RUNNING
    assert history_after[-1].to_status == ExecutionStatus.READY


def test_restore_same_status_does_not_create_history_entry(
    manager: StateManager,
) -> None:

    manager.set_state(1, ExecutionStatus.READY)

    checkpoint = manager.create_checkpoint(1)

    history_before = manager.get_history(1)

    manager.restore_checkpoint(
        1,
        checkpoint,
    )

    history_after = manager.get_history(1)

    assert history_after == history_before


# =============================================================================
# Cleanup
# =============================================================================


def test_remove_task_removes_checkpoints(
    manager: StateManager,
) -> None:

    manager.create_checkpoint(1)

    manager.remove_task(1)

    assert not manager.has_task(1)

    with pytest.raises(KeyError):

        manager.get_checkpoints(1)


def test_clear_removes_all_checkpoints(
    manager: StateManager,
) -> None:

    manager.register_task(2)

    manager.create_checkpoint(1)
    manager.create_checkpoint(2)

    manager.clear()

    assert manager.task_ids() == []
    assert manager.checkpoints() == {}


# =============================================================================
# Registration Integration
# =============================================================================


def test_registering_existing_task_does_not_create_checkpoint(
    manager: StateManager,
) -> None:

    manager.create_checkpoint(1)

    existing = manager.register_task(1)

    assert existing.task_id == 1
    assert len(manager.get_checkpoints(1)) == 1