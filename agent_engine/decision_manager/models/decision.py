"""
===============================================================================
File Name   : decision.py
Module      : Decision Manager Models
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Defines the unified decision result returned by the Decision Manager.

DecisionAction is intentionally separate from ExecutionStatus.

The Decision Manager decides what should happen next.
The State Manager / Orchestrator will later apply that decision.

Phase D:
    D-1 - Retry Policy
    D-2 - Timeout Handling
    D-3 - Failure Strategy
    D-4 - Skip Policy
    D-5 - Fallback / Recovery
    D-6 - Unified DecisionResult

Author      : Team Agent
===============================================================================
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from agent_engine.decision_manager.models.execution_outcome import (
    FailureType,
)
from agent_engine.decision_manager.models.fallback import (
    FallbackOption,
)


class DecisionAction(str, Enum):
    """
    Possible decisions produced by the Decision Manager.
    """
    CONTINUE = "CONTINUE"

    COMPLETE = "COMPLETE"

    RETRY = "RETRY"

    FALLBACK = "FALLBACK"

    SKIP = "SKIP"

    FAIL = "FAIL"

    ABORT = "ABORT"


class DecisionResult(BaseModel):
    """
    Unified structured result produced by the Decision Manager.

    The result describes what should happen next. It does not execute
    the selected action.

    D-6 establishes this model as the common decision contract for
    all Decision Manager policies.
    """

    action: DecisionAction = Field(
        ...,
        description="Decision selected for the task.",
    )

    task_id: int = Field(
        ...,
        description="Task for which the decision was generated.",
    )

    reason: str = Field(
        ...,
        min_length=1,
        description="Reason for the selected decision.",
    )

    attempt: int = Field(
        ...,
        ge=1,
        description="Current execution attempt.",
    )

    max_retries: int = Field(
        default=0,
        ge=0,
        description="Configured maximum number of retries.",
    )

    retry_delay: float | None = Field(
        default=None,
        ge=0,
        description="Optional retry delay in seconds.",
    )

    fallback_task_id: int | None = Field(
        default=None,
        description=(
            "Optional ID of a fallback task when recovery is represented "
            "as another executable task."
        ),
    )

    selected_fallback: FallbackOption | None = Field(
        default=None,
        description=(
            "Selected fallback option for a FALLBACK decision."
        ),
    )

    failure_type: FailureType = Field(
        default=FailureType.NONE,
        description=(
            "Failure classification associated with the decision."
        ),
    )

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )