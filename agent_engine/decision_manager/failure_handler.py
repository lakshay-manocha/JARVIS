"""
===============================================================================
File Name   : failure_handler.py
Module      : Decision Manager
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Normalizes execution-layer failures into a structured ExecutionOutcome.

Phase F:
    F-1 - Failure Handling

The FailureHandler acts as the boundary between the execution/automation
layer and the Decision Manager.

It converts exceptions or uncontrolled execution failures into a validated
ExecutionOutcome so that the DecisionManager can make a deterministic
decision.

This module does NOT:
    - retry tasks,
    - execute fallback actions,
    - modify task state,
    - execute automation,
    - make retry/fallback decisions.

Those responsibilities belong to the RetryPolicy, FallbackPolicy,
StateManager, and Automation/Orchestration layers respectively.

Author      : Team Agent
===============================================================================
"""

from __future__ import annotations

from agent_engine.contracts.enums import ExecutionStatus

from agent_engine.decision_manager.models.execution_outcome import (
    ExecutionOutcome,
    FailureType,
)


class FailureHandler:
    """
    Normalizes execution failures into ExecutionOutcome objects.
    """

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def handle_exception(
        self,
        *,
        task_id: int,
        exception: Exception,
        attempt: int = 1,
        retry_count: int = 0,
        max_retries: int = 0,
        timeout_seconds: float | None = None,
        execution_time: float | None = None,
    ) -> ExecutionOutcome:
        """
        Convert an execution exception into a structured failure outcome.

        The handler does not decide whether the task should be retried.
        It only classifies and normalizes the failure.

        Parameters
        ----------
        task_id:
            ID of the task that failed.

        exception:
            Exception raised by the execution/automation layer.

        attempt:
            One-based execution attempt number.

        retry_count:
            Number of retries already consumed.

        max_retries:
            Maximum number of retries permitted.

        timeout_seconds:
            Configured timeout, if any.

        execution_time:
            Measured execution duration, if available.
        """

        failure_type = self.classify_exception(exception)

        return ExecutionOutcome(
            task_id=task_id,
            status=ExecutionStatus.FAILED,
            success=False,
            attempt=attempt,
            retry_count=retry_count,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
            execution_time=execution_time,
            timed_out=failure_type == FailureType.TIMEOUT,
            failure_type=failure_type,
            error_message=str(exception),
        )

    # -------------------------------------------------------------------------
    # Exception Classification
    # -------------------------------------------------------------------------

    def classify_exception(
        self,
        exception: Exception,
    ) -> FailureType:
        """
        Classify an execution exception.

        Classification is intentionally conservative.

        TimeoutError:
            TIMEOUT

        All other exceptions:
            UNKNOWN

        More specialized exception mappings can be introduced later when
        the automation agents define their concrete failure contracts.
        """

        if isinstance(exception, TimeoutError):
            return FailureType.TIMEOUT

        return FailureType.UNKNOWN

    # -------------------------------------------------------------------------
    # Existing Outcome Normalization
    # -------------------------------------------------------------------------

    def normalize_outcome(
        self,
        outcome: ExecutionOutcome,
    ) -> ExecutionOutcome:
        """
        Normalize an existing ExecutionOutcome.

        This method guarantees that a failed outcome has a meaningful
        failure classification.

        Existing timeout information is preserved and classified as
        TIMEOUT.

        An unclassified failure becomes UNKNOWN.

        The original object is never mutated.
        """

        normalized = outcome.model_copy(
            deep=True
        )

        # ---------------------------------------------------------------------
        # Timeout has highest classification priority.
        # ---------------------------------------------------------------------

        if (
            normalized.timed_out
            or (
                normalized.execution_time is not None
                and normalized.timeout_seconds is not None
                and normalized.execution_time
                > normalized.timeout_seconds
            )
        ):
            normalized.timed_out = True
            normalized.success = False
            normalized.status = ExecutionStatus.FAILED
            normalized.failure_type = FailureType.TIMEOUT

            return normalized

        # ---------------------------------------------------------------------
        # Successful outcome.
        # ---------------------------------------------------------------------

        if normalized.success:
            normalized.failure_type = FailureType.NONE
            normalized.status = ExecutionStatus.COMPLETED

            return normalized

        # ---------------------------------------------------------------------
        # Failed outcome without classification.
        # ---------------------------------------------------------------------

        if normalized.failure_type == FailureType.NONE:
            normalized.failure_type = FailureType.UNKNOWN

        normalized.status = ExecutionStatus.FAILED

        return normalized