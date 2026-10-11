"""
===============================================================================
File Name   : demo_dispatcher.py
Module      : Dispatcher / Agent Brain Demonstration
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Development dispatcher used to demonstrate the Agent Brain execution
boundary without implementing Automation Engine functionality.

This dispatcher DOES NOT:
    - open applications
    - control the browser
    - perform mouse/keyboard actions
    - execute real external automation

It DOES:
    - receive an already-planned InterpretedTask
    - produce a normalized ExecutionOutcome
    - demonstrate that AgentOrchestrator reaches the dispatcher boundary
    - allow Decision Manager and State Manager integration to be exercised

Module 5 will later replace this implementation with the real Automation
Engine dispatcher.
===============================================================================
"""

from __future__ import annotations

from datetime import datetime, timezone

from agent_engine.agent_brain.models.interpreted_task import InterpretedTask
from agent_engine.contracts.enums import ExecutionStatus
from agent_engine.decision_manager.models.execution_outcome import (
    ExecutionOutcome,
)


class DemoDispatcher:
    """
    Non-automation dispatcher used for Agent Brain demonstration.

    It represents the execution boundary only. No external application or
    environment is modified.
    """

    def __init__(self) -> None:
        self.calls: list[tuple[int, int]] = []

    def dispatch(
        self,
        task: InterpretedTask,
        *,
        attempt: int,
        timeout_seconds: float | None = None,
    ) -> ExecutionOutcome:
        """
        Receive one planned task and return a successful execution outcome.

        The returned outcome is real and is consumed by the existing
        DecisionManager and DecisionStateBridge.
        """

        started = datetime.now(timezone.utc)

        self.calls.append((task.task_id, attempt))

        execution_time = (
            datetime.now(timezone.utc) - started
        ).total_seconds()

        return ExecutionOutcome(
            task_id=task.task_id,
            status=ExecutionStatus.COMPLETED,
            success=True,
            attempt=attempt,
            retry_count=max(attempt - 1, 0),
            max_retries=0,
            execution_time=execution_time,
        )