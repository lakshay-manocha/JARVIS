"""
===============================================================================
File Name   : action.py
Module      : Contracts
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Defines the contracts used to represent an automation action.

An ActionRequest is the normalized execution request passed from the Agent
Engine toward the Automation Engine.

The contract separates:
    - What action should be executed
    - Which automation controller should execute it
    - Which parameters are required
    - Execution metadata

The contract contains no execution logic.

Author      : Team Agent
===============================================================================
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agent_engine.contracts.enums import (
    ActionCategory,
    ToolType,
)


class ActionRequest(BaseModel):
    """
    Represents one normalized automation action request.

    This is the contract between the Agent Engine and the Automation Engine.

    The ActionRequest describes WHAT should be executed.
    It does not execute the action itself.
    """

    # -------------------------------------------------------------------------
    # Task Identification
    # -------------------------------------------------------------------------

    task_id: int = Field(
        ...,
        description="Unique identifier of the originating task.",
    )

    # -------------------------------------------------------------------------
    # Action Definition
    # -------------------------------------------------------------------------

    action: str = Field(
        ...,
        min_length=1,
        description="Normalized action to be executed.",
    )

    category: ActionCategory = Field(
        ...,
        description="Logical category of the automation action.",
    )

    tool: ToolType = Field(
        ...,
        description="Automation controller responsible for the action.",
    )

    # -------------------------------------------------------------------------
    # Action Parameters
    # -------------------------------------------------------------------------

    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters required by the automation action.",
    )

    # -------------------------------------------------------------------------
    # Execution Configuration
    # -------------------------------------------------------------------------

    timeout_seconds: float | None = Field(
        default=None,
        gt=0,
        description="Maximum allowed execution time.",
    )

    # -------------------------------------------------------------------------
    # Metadata
    # -------------------------------------------------------------------------

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional non-execution metadata.",
    )

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )