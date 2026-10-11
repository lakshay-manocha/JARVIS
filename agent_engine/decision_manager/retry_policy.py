"""
===============================================================================
File Name   : retry_policy.py
Module      : Decision Manager
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Implements the deterministic retry policy for task execution failures.

Phase D-1:
    1. Retry transient failures.
    2. Retry timeout failures.
    3. Respect the configured maximum retry count.
    4. Never retry permanent failures.
    5. Never retry validation failures.
    6. Never retry dependency failures.
    7. Never retry unknown failures.

This module only decides whether another attempt should be made.

It does NOT:
    - execute the task,
    - modify task state,
    - call controllers,
    - call the dispatcher,
    - start timers.

Author      : Team Agent
===============================================================================
"""

from agent_engine.contracts.enums import ExecutionStatus

from agent_engine.decision_manager.models.decision import (
    DecisionAction,
    DecisionResult,
)

from agent_engine.decision_manager.models.execution_outcome import (
    ExecutionOutcome,
    FailureType,
)


class RetryPolicy:
    """
    Deterministic policy responsible for retry decisions.
    """

    # -------------------------------------------------------------------------
    # Retryable failure classifications
    # -------------------------------------------------------------------------

    RETRYABLE_FAILURES = frozenset(
        {
            FailureType.TRANSIENT,
            FailureType.TIMEOUT,
        }
    )

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def evaluate(
        self,
        outcome: ExecutionOutcome,
    ) -> DecisionResult:
        """
        Evaluate one execution outcome.

        Decision order:

            1. Successful execution
                → COMPLETE

            2. Non-retryable failure
                → FAIL

            3. Retryable failure with retries remaining
                → RETRY

            4. Retryable failure with no retries remaining
                → FAIL

        Retry semantics:

            retry_count < max_retries
                → retry is allowed

            retry_count >= max_retries
                → retry is not allowed
        """

        # ---------------------------------------------------------------------
        # Case 1: Successful execution
        # ---------------------------------------------------------------------

        if outcome.success or outcome.status == ExecutionStatus.COMPLETED:
            return DecisionResult(
                action=DecisionAction.COMPLETE,
                task_id=outcome.task_id,
                reason="Task execution completed successfully.",
                attempt=outcome.attempt,
                max_retries=outcome.max_retries,
                failure_type=FailureType.NONE,
            )

        # ---------------------------------------------------------------------
        # Case 2: Failure is not retryable
        # ---------------------------------------------------------------------

        if outcome.failure_type not in self.RETRYABLE_FAILURES:
            return DecisionResult(
                action=DecisionAction.FAIL,
                task_id=outcome.task_id,
                reason=(
                    f"Failure type '{outcome.failure_type.value}' "
                    "is not retryable."
                ),
                attempt=outcome.attempt,
                max_retries=outcome.max_retries,
                failure_type=outcome.failure_type,
            )

        # ---------------------------------------------------------------------
        # Case 3: Retryable failure but retry limit exhausted
        # ---------------------------------------------------------------------

        if outcome.retry_count >= outcome.max_retries:
            return DecisionResult(
                action=DecisionAction.FAIL,
                task_id=outcome.task_id,
                reason="Maximum retry attempts exhausted.",
                attempt=outcome.attempt,
                max_retries=outcome.max_retries,
                failure_type=outcome.failure_type,
            )

        # ---------------------------------------------------------------------
        # Case 4: Retryable failure and retry available
        # ---------------------------------------------------------------------

        return DecisionResult(
            action=DecisionAction.RETRY,
            task_id=outcome.task_id,
            reason=(
                f"Failure type '{outcome.failure_type.value}' "
                "is retryable and retry attempts remain."
            ),
            attempt=outcome.attempt,
            max_retries=outcome.max_retries,
            failure_type=outcome.failure_type,
        )