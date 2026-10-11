"""
===============================================================================
File Name   : fallback_policy.py
Module      : Decision Manager
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Implements fallback and recovery decision logic.

Phase D-5:
    Fallback / Recovery.

Phase D-6:
    Returns the unified DecisionResult contract.

The policy selects the highest-priority available fallback option.

The policy does NOT execute the fallback.
===============================================================================
"""

from __future__ import annotations

from collections.abc import Sequence

from agent_engine.contracts.task import Task

from agent_engine.decision_manager.models.decision import (
    DecisionAction,
    DecisionResult,
)

from agent_engine.decision_manager.models.execution_outcome import (
    FailureType,
)

from agent_engine.decision_manager.models.fallback import (
    FallbackOption,
)


class FallbackPolicy:
    """
    Determines whether a failed task has a viable fallback.
    """

    def select_fallback(
        self,
        task: Task,
        fallback_options: Sequence[FallbackOption] | None = None,
        attempt: int = 1,
    ) -> DecisionResult:
        """
        Select the highest-priority fallback option.

        If a fallback is available:
            → FALLBACK

        If no fallback is available:
            → FAIL

        The policy only produces a decision. It does not execute
        the fallback action.
        """

        options = list(fallback_options or [])

        # ---------------------------------------------------------------------
        # No fallback available
        # ---------------------------------------------------------------------

        if not options:
            return DecisionResult(
                action=DecisionAction.FAIL,
                task_id=task.id,
                reason="No fallback option is available for the task.",
                attempt=attempt,
                max_retries=task.retry,
                failure_type=FailureType.NONE,
            )

        # ---------------------------------------------------------------------
        # Select highest-priority fallback.
        #
        # Lower priority number = higher priority.
        # ---------------------------------------------------------------------

        selected = min(
            options,
            key=lambda option: option.priority,
        )

        return DecisionResult(
            action=DecisionAction.FALLBACK,
            task_id=task.id,
            reason=(
                f"Fallback option '{selected.id}' selected "
                f"for task {task.id}."
            ),
            attempt=attempt,
            max_retries=task.retry,
            selected_fallback=selected,
            failure_type=FailureType.NONE,
        )