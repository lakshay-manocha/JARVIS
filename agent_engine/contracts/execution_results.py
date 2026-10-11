"""
===============================================================================
File Name   : execution_result.py
Module      : Contracts
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Defines the output contract returned by the Agent Engine after executing an
Execution Plan.

The ExecutionResult model contains the final execution status, task statistics,
execution metrics, logs, and errors. It is the standardized response shared
with the Memory Module, Voice Module, UI, and Analytics systems.

Author      : Team Agent
===============================================================================
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

from agent_engine.contracts.enums import ResultStatus


class TaskError(BaseModel):
    """
    Represents an error encountered while executing a task.
    """

    task_id: int = Field(
        ...,
        description="Identifier of the failed task."
    )

    action: str = Field(
        ...,
        description="Action that failed."
    )

    message: str = Field(
        ...,
        description="Detailed error message."
    )


class ExecutionMetrics(BaseModel):
    """
    Runtime execution metrics.
    """

    total_tasks: int = Field(default=0)

    completed_tasks: int = Field(default=0)

    failed_tasks: int = Field(default=0)

    skipped_tasks: int = Field(default=0)

    retry_count: int = Field(default=0)

    execution_time: float = Field(
        default=0.0,
        description="Total execution time in seconds."
    )


class ExecutionResult(BaseModel):
    """
    Final execution response returned by the Agent Engine.
    """

    # ---------------------------------------------------------------------
    # Request Information
    # ---------------------------------------------------------------------

    request_id: str

    status: ResultStatus

    # ---------------------------------------------------------------------
    # Runtime
    # ---------------------------------------------------------------------

    started_at: datetime

    completed_at: datetime

    # ---------------------------------------------------------------------
    # Metrics
    # ---------------------------------------------------------------------

    metrics: ExecutionMetrics

    # ---------------------------------------------------------------------
    # Logs
    # ---------------------------------------------------------------------

    logs: List[str] = Field(default_factory=list)

    # ---------------------------------------------------------------------
    # Errors
    # ---------------------------------------------------------------------

    errors: List[TaskError] = Field(default_factory=list)

    class Config:
        validate_assignment = True
        extra = "forbid"