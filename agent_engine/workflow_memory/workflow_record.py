"""
===============================================================================
File Name   : workflow_record.py
Module      : Workflow Memory
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
Defines the workflow-level record used by the historical workflow memory
layer.

A WorkflowRecord represents one completed, failed, or otherwise terminal
workflow snapshot. It is separate from TaskRuntimeState and StateHistory.

The record is designed to be compatible with Model A's workflow retrieval
input format.
===============================================================================
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class WorkflowRecord(BaseModel):
    """
    Represents one historical workflow snapshot.

    This model stores workflow-level information and does not control execution.
    """

    # -------------------------------------------------------------------------
    # Workflow Identity
    # -------------------------------------------------------------------------

    workflow_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier of the historical workflow.",
    )

    # -------------------------------------------------------------------------
    # Workflow Description
    # -------------------------------------------------------------------------

    goal: str = Field(
        ...,
        min_length=1,
        description="High-level objective of the workflow.",
    )

    domain: str = Field(
        ...,
        min_length=1,
        description="Workflow domain, such as desktop, browser, or filesystem.",
    )

    # -------------------------------------------------------------------------
    # Workflow Execution Information
    # -------------------------------------------------------------------------

    overall_status: str = Field(
        ...,
        min_length=1,
        description="Final or recorded workflow status.",
    )

    # -------------------------------------------------------------------------
    # Model A-Compatible Workflow Graph
    # -------------------------------------------------------------------------

    graph: dict[str, Any] = Field(
        default_factory=lambda: {"nodes": []},
        description="Workflow graph in Model A-compatible format.",
    )

    # -------------------------------------------------------------------------
    # Environment Context
    # -------------------------------------------------------------------------

    current_state: dict[str, Any] = Field(
        default_factory=dict,
        description="Relevant environment state at workflow capture time.",
    )

    # -------------------------------------------------------------------------
    # Additional Information
    # -------------------------------------------------------------------------

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional workflow metadata.",
    )

    # -------------------------------------------------------------------------
    # Timestamps
    # -------------------------------------------------------------------------

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Time when the workflow record was created.",
    )

    completed_at: datetime | None = Field(
        default=None,
        description="Time when workflow execution completed, if available.",
    )

    # -------------------------------------------------------------------------
    # Pydantic Configuration
    # -------------------------------------------------------------------------

    model_config = {
        "validate_assignment": True,
        "extra": "forbid",
    }