"""
===============================================================================
File Name   : dependency_result.py
Module      : Agent Brain Models
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Defines the structured result produced by the dependency detection module.

A DependencyResult represents the relationship between two interpreted tasks
and stores whether the second task depends on the first task.

This model will be consumed by the Graph Builder when replacing the current
simple sequential dependency logic with real dependency detection.

Author : Team JARVIS
===============================================================================
"""

from __future__ import annotations
from agent_engine.contracts.dependency_types import DependencyType
from pydantic import BaseModel, Field


class DependencyResult(BaseModel):
    """
    Represents the dependency relationship between two tasks.
    """

    # ------------------------------------------------------------------
    # Task Identity
    # ------------------------------------------------------------------

    parent_task_id: int = Field(
        ...,
        ge=1
    )

    child_task_id: int = Field(
        ...,
        ge=1
    )

    # ------------------------------------------------------------------
    # Dependency Decision
    # ------------------------------------------------------------------

    depends_on: bool = False

    # ------------------------------------------------------------------
    # Confidence
    # ------------------------------------------------------------------

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0
    )

    # ------------------------------------------------------------------
    # Explanation
    # ------------------------------------------------------------------

    reason: str = ""

    # ------------------------------------------------------------------
    # Dependency Type
    # ------------------------------------------------------------------

    dependency_type: DependencyType = DependencyType.NONE

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    metadata: dict[str, str] = Field(
        default_factory=dict
    )

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    model_config = {
        "validate_assignment": True,
        "extra": "forbid"
    }

    # ------------------------------------------------------------------
    # Helper Methods
    # ------------------------------------------------------------------

    @property
    def is_dependency(self) -> bool:
        """
        Returns True when the child task depends on the parent task.
        """

        return self.depends_on

    def to_dict(self) -> dict:
        """
        Serialize dependency result into a dictionary.
        """

        return self.model_dump()