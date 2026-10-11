"""
===============================================================================
File Name   : graph_validation_result.py
Module      : Agent Brain Models
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Represents the result of execution graph integrity validation.

The GraphValidationResult provides a structured representation of whether
an ExecutionGraph is valid and records any detected structural or dependency
integrity violations.

Author : Team JARVIS
===============================================================================
"""

from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field


class GraphValidationResult(BaseModel):
    """
    Represents the result of execution graph validation.
    """

    # ------------------------------------------------------------------
    # Validation Status
    # ------------------------------------------------------------------

    is_valid: bool = False

    # ------------------------------------------------------------------
    # Validation Statistics
    # ------------------------------------------------------------------

    node_count: int = Field(
        default=0,
        ge=0
    )

    edge_count: int = Field(
        default=0,
        ge=0
    )

    # ------------------------------------------------------------------
    # Validation Errors
    # ------------------------------------------------------------------

    errors: list[str] = Field(
        default_factory=list
    )

    # ------------------------------------------------------------------
    # Validation Warnings
    # ------------------------------------------------------------------

    warnings: list[str] = Field(
        default_factory=list
    )

    # ------------------------------------------------------------------
    # Validation Metadata
    # ------------------------------------------------------------------

    metadata: dict[str, Any] = Field(
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
    # Helper Properties
    # ------------------------------------------------------------------

    @property
    def error_count(self) -> int:
        """
        Returns the number of validation errors.
        """

        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """
        Returns the number of validation warnings.
        """

        return len(self.warnings)