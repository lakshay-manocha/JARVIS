"""
===============================================================================
File Name   : execution_result_integrator.py
Module      : Automation Engine - Integration
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Provides the M5-G.11 integration boundary between the Automation Engine
execution result model and the existing Agent Brain / Decision Manager
execution outcome model.

Flow:

    AutomationAgent
          ↓
    AutomationExecutionResult
          ↓
    ExecutionResultIntegrator
          ↓
    ExecutionOutcome
          ↓
    DecisionManager
          ↓
    DecisionStateBridge
          ↓
    StateManager

Responsibilities:
    - Convert AutomationExecutionResult into ExecutionOutcome
    - Preserve task identification
    - Preserve execution timing
    - Preserve error information
    - Preserve timeout information
    - Preserve execution attempt information
    - Normalize success/failure status
    - Map automation failure information to FailureType

The integrator does NOT:
    - perform retries
    - select fallbacks
    - modify task state
    - call DecisionManager
    - call StateManager
    - execute automation actions

Author : Team Automation
===============================================================================
"""

from __future__ import annotations

from typing import Any

from agent_engine.automation.models.execution_result import (
    AutomationExecutionResult,
)
from agent_engine.contracts.enums import ExecutionStatus
from agent_engine.decision_manager.models.execution_outcome import (
    ExecutionOutcome,
    FailureType,
)


class ExecutionResultIntegrator:
    """
    Converts AutomationExecutionResult into the existing ExecutionOutcome
    contract used by the Decision Manager.

    This class is deliberately kept separate from the Dispatcher so that
    result translation remains an explicit architectural boundary.
    """

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def integrate(
        self,
        result: AutomationExecutionResult,
        *,
        attempt: int,
        max_retries: int = 0,
        timeout_seconds: float | None = None,
    ) -> ExecutionOutcome:
        """
        Convert an AutomationExecutionResult into an ExecutionOutcome.

        Args:
            result:
                Result returned by an AutomationAgent.

            attempt:
                One-based execution attempt number.

            max_retries:
                Maximum number of additional retries permitted by the
                execution context.

            timeout_seconds:
                Configured execution timeout.

        Returns:
            Normalized ExecutionOutcome.

        Raises:
            TypeError:
                If result is not an AutomationExecutionResult.

            ValueError:
                If attempt or max_retries are invalid.
        """

        if not isinstance(
            result,
            AutomationExecutionResult,
        ):
            raise TypeError(
                "result must be an AutomationExecutionResult."
            )

        if attempt < 1:
            raise ValueError(
                "attempt must be greater than or equal to 1."
            )

        if max_retries < 0:
            raise ValueError(
                "max_retries cannot be negative."
            )

        retry_count = max(
            attempt - 1,
            0,
        )

        timed_out = self._resolve_timed_out(
            result
        )

        failure_type = self._resolve_failure_type(
            result,
            timed_out=timed_out,
        )

        if result.success:
            status = ExecutionStatus.COMPLETED
            error_message = None
        else:
            status = ExecutionStatus.FAILED
            error_message = result.error

        return ExecutionOutcome(
            task_id=result.task_id,
            status=status,
            success=result.success,
            attempt=attempt,
            retry_count=retry_count,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
            execution_time=result.execution_time,
            timed_out=timed_out,
            failure_type=failure_type,
            error_message=error_message,
        )

    # -------------------------------------------------------------------------
    # Timeout Resolution
    # -------------------------------------------------------------------------

    @staticmethod
    def _resolve_timed_out(
        result: AutomationExecutionResult,
    ) -> bool:
        """
        Determine whether the automation result represents a timeout.

        AutomationExecutionResult intentionally remains lightweight, so
        timeout information can be supplied through metadata by an
        automation agent.

        Supported metadata values:

            {
                "timed_out": True
            }

        or:

            {
                "failure_type": "TIMEOUT"
            }
        """

        metadata: dict[str, Any] = result.metadata

        if metadata.get("timed_out") is True:
            return True

        failure_type = metadata.get(
            "failure_type"
        )

        if isinstance(
            failure_type,
            FailureType,
        ):
            return failure_type == FailureType.TIMEOUT

        if isinstance(
            failure_type,
            str,
        ):
            return (
                failure_type.strip().upper()
                == FailureType.TIMEOUT.value
            )

        return False

    # -------------------------------------------------------------------------
    # Failure Classification
    # -------------------------------------------------------------------------

    @staticmethod
    def _resolve_failure_type(
        result: AutomationExecutionResult,
        *,
        timed_out: bool,
    ) -> FailureType:
        """
        Resolve the normalized FailureType for an automation result.

        Explicit failure information supplied by the Automation Agent through
        metadata takes precedence.

        If no explicit failure type is supplied:
            success → NONE
            timeout → TIMEOUT
            failure → UNKNOWN
        """

        if result.success:
            return FailureType.NONE

        if timed_out:
            return FailureType.TIMEOUT

        failure_type = result.metadata.get(
            "failure_type"
        )

        if isinstance(
            failure_type,
            FailureType,
        ):
            return failure_type

        if isinstance(
            failure_type,
            str,
        ):
            normalized = failure_type.strip().upper()

            try:
                return FailureType(normalized)
            except ValueError:
                return FailureType.UNKNOWN

        return FailureType.UNKNOWN