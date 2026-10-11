"""
===============================================================================
File Name   : state_checkpoint.py
Module      : State Manager
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Defines immutable runtime state checkpoints for executable tasks.

Phase E-5:
    Checkpoint Handling.

A checkpoint is an immutable snapshot of a task's runtime state at a
particular point in execution.

Checkpoints are snapshots only. They do not perform state transition
validation or modify the State Manager.

Recovery validation remains the responsibility of StateTransitionPolicy.
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from agent_engine.contracts.enums import ExecutionStatus


@dataclass(frozen=True)
class StateCheckpoint:
    """
    Immutable snapshot of a task's runtime state.

    A checkpoint captures the complete runtime information required to
    restore a task to a previously recorded execution point.

    Attributes:
        task_id:
            Identifier of the task.

        status:
            Execution status at checkpoint creation.

        retry_count:
            Number of retries attempted at checkpoint creation.

        progress:
            Task completion percentage at checkpoint creation.

        started_at:
            Execution start timestamp.

        completed_at:
            Execution completion timestamp, if available.

        execution_time:
            Recorded execution time in seconds.

        error_message:
            Runtime error message, if available.

        error_code:
            Machine-readable runtime error code, if available.

        timestamp:
            Time at which the checkpoint was created.
    """

    task_id: int
    status: ExecutionStatus
    retry_count: int
    progress: float
    started_at: datetime | None
    completed_at: datetime | None
    execution_time: float | None
    error_message: str | None
    error_code: str | None
    timestamp: datetime