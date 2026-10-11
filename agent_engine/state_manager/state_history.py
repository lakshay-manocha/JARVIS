"""
===============================================================================
File Name   : state_history.py
Module      : State Manager
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Defines immutable state history entries for executable tasks.

Phase E-4:
    State History.

The State History records actual runtime state transitions made through the
State Manager.

It does not perform transition validation. Transition validation remains the
responsibility of StateTransitionPolicy.
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from agent_engine.contracts.enums import ExecutionStatus


@dataclass(frozen=True)
class StateHistoryEntry:
    """
    Immutable record of a single task state transition.

    Attributes:
        task_id:
            Identifier of the task whose state changed.

        from_status:
            Previous execution status.

            None is used for the initial registration entry.

        to_status:
            New execution status.

        timestamp:
            Time at which the transition was recorded.
    """

    task_id: int
    from_status: ExecutionStatus | None
    to_status: ExecutionStatus
    timestamp: datetime