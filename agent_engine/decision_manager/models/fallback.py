"""
===============================================================================
File Name   : fallback.py
Module      : Decision Manager Models
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Defines the data structures used by the fallback/recovery policy.

Phase D-5:
    Fallback / Recovery.

The model represents a recovery option without executing it.
===============================================================================
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class FallbackOption(BaseModel):
    """
    Represents one possible recovery option for a failed task.
    """

    id: str = Field(
        ...,
        description="Unique identifier for the fallback option.",
    )

    action: str = Field(
        ...,
        description="Alternative action to execute.",
    )

    tool: str | None = Field(
        default=None,
        description="Optional alternative automation tool.",
    )

    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters required by the fallback action.",
    )

    priority: int = Field(
        default=1,
        ge=1,
        description="Priority of this fallback option.",
    )

    description: str = Field(
        default="",
        description="Human-readable description of the recovery action.",
    )

    class Config:
        extra = "forbid"


class FallbackDecision(BaseModel):
    """
    Represents the recovery decision made by the fallback policy.
    """

    task_id: int

    fallback_available: bool

    selected_fallback: FallbackOption | None = None

    reason: str

    class Config:
        extra = "forbid"