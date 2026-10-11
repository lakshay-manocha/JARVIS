"""
===============================================================================
File Name   : failure_strategy.py
Module      : Decision Manager
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Defines the failure handling strategy for non-successful task execution.

Phase D-3:
    - Permanent failures
    - Validation failures
    - Dependency failures
    - Unknown failures

The strategy does not execute recovery actions.
It only returns the appropriate decision.

Author      : Team Agent
===============================================================================
"""

from agent_engine.decision_manager.models.decision import (
    DecisionAction,
    DecisionResult,
)

from agent_engine.decision_manager.models.execution_outcome import (
    ExecutionOutcome,
    FailureType,
)


class FailureStrategy:
    """
    Determines the appropriate decision for non-retryable failures.
    """

    def evaluate(
        self,
        outcome: ExecutionOutcome,
    ) -> DecisionResult:
        """
        Evaluate a non-retryable execution failure.

        Current D-3 policy:

            PERMANENT
                → FAIL

            VALIDATION
                → FAIL

            DEPENDENCY
                → SKIP

            UNKNOWN
                → FAIL

        TRANSIENT and TIMEOUT are intentionally handled by RetryPolicy.
        """

        if outcome.failure_type == FailureType.DEPENDENCY:
            return DecisionResult(
                action=DecisionAction.SKIP,
                task_id=outcome.task_id,
                reason="Task dependency failed.",
                attempt=outcome.attempt,
                max_retries=outcome.max_retries,
                failure_type=outcome.failure_type,
            )

        if outcome.failure_type == FailureType.PERMANENT:
            return DecisionResult(
                action=DecisionAction.FAIL,
                task_id=outcome.task_id,
                reason="Permanent failure cannot be recovered by retrying.",
                attempt=outcome.attempt,
                max_retries=outcome.max_retries,
                failure_type=outcome.failure_type,
            )

        if outcome.failure_type == FailureType.VALIDATION:
            return DecisionResult(
                action=DecisionAction.FAIL,
                task_id=outcome.task_id,
                reason="Task validation failed.",
                attempt=outcome.attempt,
                max_retries=outcome.max_retries,
                failure_type=outcome.failure_type,
            )

        return DecisionResult(
            action=DecisionAction.FAIL,
            task_id=outcome.task_id,
            reason="Task failed with an unhandled failure type.",
            attempt=outcome.attempt,
            max_retries=outcome.max_retries,
            failure_type=outcome.failure_type,
        )