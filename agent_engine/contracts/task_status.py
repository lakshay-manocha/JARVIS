"""
===============================================================================
File Name   : task_status.py
Module      : Contracts
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Defines the runtime state of a task during execution.

Unlike the Task model, which contains static information received from the
LLM, this model stores dynamic information that changes while the Agent
Engine executes the workflow.

The Scheduler, Dispatcher, Controllers, Monitoring module and Result
Generator continuously update this object throughout execution.

Author      : Team Agent
===============================================================================
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from agent_engine.contracts.enums import ExecutionStatus


class TaskRuntimeState(BaseModel):
    """
    Represents the live execution state of a task.

    This object is created by the Agent Engine when execution starts and
    updated throughout the task lifecycle.
    """

    # -------------------------------------------------------------------------
    # Task Identification
    # -------------------------------------------------------------------------

    task_id: int = Field(
        ...,
        description="Unique identifier of the associated task."
    )

    # -------------------------------------------------------------------------
    # Runtime Status
    # -------------------------------------------------------------------------

    status: ExecutionStatus = Field(
        default=ExecutionStatus.PENDING,
        description="Current execution state of the task."
    )

    # -------------------------------------------------------------------------
    # Retry Information
    # -------------------------------------------------------------------------

    retry_count: int = Field(
        default=0,
        ge=0,
        description="Number of retries attempted."
    )

    # -------------------------------------------------------------------------
    # Progress Tracking
    # -------------------------------------------------------------------------

    progress: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Task completion percentage."
    )

    # -------------------------------------------------------------------------
    # Timing Information
    # -------------------------------------------------------------------------

    started_at: datetime | None = Field(
        default=None,
        description="Timestamp when execution started."
    )

    completed_at: datetime | None = Field(
        default=None,
        description="Timestamp when execution completed."
    )

    execution_time: float | None = Field(
        default=None,
        ge=0,
        description="Execution time in seconds."
    )

    # -------------------------------------------------------------------------
    # Error Information
    # -------------------------------------------------------------------------

    error_message: str | None = Field(
        default=None,
        description="Error message if execution fails."
    )

    error_code: str | None = Field(
        default=None,
        description="Machine-readable error code."
    )

    class Config:
        validate_assignment = True
        extra = "forbid"