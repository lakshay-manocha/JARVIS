"""
===============================================================================
File Name   : execution_outcome.py
Module      : Decision Manager Models
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Defines the structured result of one execution attempt of one task.

Phase D:
    D-0 - Execution outcome contract
    D-1 - Retry support
    D-2 - Timeout handling

Author      : Team Agent
===============================================================================
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from agent_engine.contracts.enums import ExecutionStatus


class FailureType(str, Enum):
    """
    Classification of task execution failures.
    """

    NONE = "NONE"

    TRANSIENT = "TRANSIENT"

    TIMEOUT = "TIMEOUT"

    PERMANENT = "PERMANENT"

    VALIDATION = "VALIDATION"

    DEPENDENCY = "DEPENDENCY"

    UNKNOWN = "UNKNOWN"


class ExecutionOutcome(BaseModel):
    """
    Represents the outcome of one execution attempt of one task.

    Retry semantics:

        retry_count:
            Number of retries already consumed.

        max_retries:
            Maximum number of additional retries permitted.

    Timeout semantics:

        timeout_seconds:
            Configured execution timeout.

        execution_time:
            Actual execution duration.

        timed_out:
            Explicit timeout indication from the execution layer.
    """

    # -------------------------------------------------------------------------
    # Task Identification
    # -------------------------------------------------------------------------

    task_id: int = Field(
        ...,
        description="Unique identifier of the executed task.",
    )

    # -------------------------------------------------------------------------
    # Execution Result
    # -------------------------------------------------------------------------

    status: ExecutionStatus = Field(
        ...,
        description="Runtime execution status.",
    )

    success: bool = Field(
        ...,
        description="Whether the execution attempt succeeded.",
    )

    # -------------------------------------------------------------------------
    # Attempt Information
    # -------------------------------------------------------------------------

    attempt: int = Field(
        ...,
        ge=1,
        description="One-based execution attempt number.",
    )

    retry_count: int = Field(
        default=0,
        ge=0,
        description="Number of retries already consumed.",
    )

    max_retries: int = Field(
        default=0,
        ge=0,
        description="Maximum number of additional retries permitted.",
    )

    # -------------------------------------------------------------------------
    # Timeout Information
    # -------------------------------------------------------------------------

    timeout_seconds: float | None = Field(
        default=None,
        gt=0,
        description="Configured maximum execution time in seconds.",
    )

    execution_time: float | None = Field(
        default=None,
        ge=0,
        description="Actual execution duration in seconds.",
    )

    timed_out: bool = Field(
        default=False,
        description="Whether the execution exceeded its configured timeout.",
    )

    # -------------------------------------------------------------------------
    # Failure Information
    # -------------------------------------------------------------------------

    failure_type: FailureType = Field(
        default=FailureType.NONE,
        description="Normalized failure classification.",
    )

    error_message: str | None = Field(
        default=None,
        description="Human-readable execution error.",
    )

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )