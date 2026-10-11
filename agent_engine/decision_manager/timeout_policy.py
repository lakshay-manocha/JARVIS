"""
===============================================================================
File Name   : timeout_policy.py
Module      : Decision Manager
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Handles timeout detection for individual task executions.

Phase D-2:
    1. Detect timeout using explicit timeout information.
    2. Detect timeout using execution_time > timeout_seconds.
    3. Normalize timeout failures to FailureType.TIMEOUT.
    4. Keep timeout detection separate from retry decisions.

This module does NOT:
    - retry tasks,
    - execute tasks,
    - modify Task objects,
    - start or stop timers,
    - modify runtime state.

The actual timer/cancellation mechanism belongs to the future execution
and orchestration layers.

Author      : Team Agent
===============================================================================
"""

from agent_engine.contracts.enums import ExecutionStatus

from agent_engine.decision_manager.models.execution_outcome import (
    ExecutionOutcome,
    FailureType,
)


class TimeoutPolicy:
    """
    Determines whether a task execution has timed out.
    """

    def is_timeout(
        self,
        outcome: ExecutionOutcome,
    ) -> bool:
        """
        Determine whether the execution should be classified as a timeout.

        A timeout is detected when either:

            1. timed_out is explicitly True

        OR

            2. execution_time exceeds timeout_seconds.
        """

        # ---------------------------------------------------------------------
        # Explicit timeout reported by execution layer
        # ---------------------------------------------------------------------

        if outcome.timed_out:
            return True

        # ---------------------------------------------------------------------
        # Infer timeout from measured execution time
        # ---------------------------------------------------------------------

        if (
            outcome.execution_time is not None
            and outcome.timeout_seconds is not None
            and outcome.execution_time > outcome.timeout_seconds
        ):
            return True

        return False

    def normalize(
        self,
        outcome: ExecutionOutcome,
    ) -> ExecutionOutcome:
        """
        Normalize timeout information in an ExecutionOutcome.

        If a timeout is detected:

            timed_out     → True
            failure_type  → TIMEOUT
            success       → False
            status        → FAILED

        The original outcome object is not mutated. A validated copy is
        returned instead.
        """

        if not self.is_timeout(outcome):
            return outcome.model_copy(deep=True)

        normalized = outcome.model_copy(
            update={
                "timed_out": True,
                "success": False,
                "status": ExecutionStatus.FAILED,
                "failure_type": FailureType.TIMEOUT,
            },
            deep=True,
        )

        return normalized