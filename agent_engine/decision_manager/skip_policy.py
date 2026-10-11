"""
===============================================================================
File Name   : skip_policy.py
Module      : Decision Manager
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Implements dependency-aware skip decisions.

Phase D-4:
    Skip a task when one or more of its required dependencies have failed
    or have already been skipped.

The policy only makes a decision. It does not:
    - change task state,
    - execute tasks,
    - modify the execution graph,
    - dispatch actions.

Dependency relationships are obtained from the task's `depends_on` field.

Author      : Team Agent
===============================================================================
"""

from __future__ import annotations

from collections.abc import Mapping

from agent_engine.contracts.enums import ExecutionStatus
from agent_engine.contracts.task import Task

from agent_engine.decision_manager.models.decision import (
    DecisionAction,
    DecisionResult,
)

from agent_engine.decision_manager.models.execution_outcome import (
    FailureType,
)


class SkipPolicy:
    """
    Determines whether a task should be skipped because of dependency state.
    """

    # -------------------------------------------------------------------------
    # Dependency states that block execution
    # -------------------------------------------------------------------------

    BLOCKING_STATES = frozenset(
        {
            ExecutionStatus.FAILED,
        }
    )

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def should_skip(
        self,
        task: Task,
        task_states: Mapping[int, ExecutionStatus],
    ) -> bool:
        """
        Determine whether a task should be skipped.

        A task is skipped when at least one dependency is in a blocking
        execution state.

        Dependencies that are PENDING or RUNNING do not cause a skip.
        """

        if not task.depends_on:
            return False

        return any(
            task_states.get(dependency_id) in self.BLOCKING_STATES
            for dependency_id in task.depends_on
        )

    def get_blocking_dependencies(
        self,
        task: Task,
        task_states: Mapping[int, ExecutionStatus],
    ) -> list[int]:
        """
        Return the dependency IDs that are preventing task execution.

        Only dependencies in blocking states are returned.
        """

        if not task.depends_on:
            return []

        return [
            dependency_id
            for dependency_id in task.depends_on
            if task_states.get(dependency_id)
            in self.BLOCKING_STATES
        ]

    def evaluate(
        self,
        task: Task,
        task_states: Mapping[int, ExecutionStatus],
        attempt: int = 1,
    ) -> DecisionResult:
        """
        Produce a skip decision when a dependency blocks execution.

        If no dependency is blocking, the policy does not make an execution
        decision and raises no exception. Instead, it returns a neutral
        COMPLETE-style result indicating that dependency conditions are clear.

        The Decision Manager can use this result as part of its future
        orchestration logic.
        """

        blocking_dependencies = self.get_blocking_dependencies(
            task,
            task_states,
        )

        if not blocking_dependencies:
            return DecisionResult(
                action=DecisionAction.COMPLETE,
                task_id=task.id,
                reason="No failed dependencies are blocking task execution.",
                attempt=attempt,
                max_retries=task.retry,
                failure_type=FailureType.NONE,
            )

        dependency_text = ", ".join(
            str(dependency_id)
            for dependency_id in blocking_dependencies
        )

        return DecisionResult(
            action=DecisionAction.SKIP,
            task_id=task.id,
            reason=(
                "Task skipped because required dependency task(s) "
                f"failed: {dependency_text}."
            ),
            attempt=attempt,
            max_retries=task.retry,
            failure_type=FailureType.DEPENDENCY,
        )