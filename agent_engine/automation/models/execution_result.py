"""
===============================================================================
File Name   : execution_result.py
Module      : Automation Engine - Models
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Defines the standardized result returned by an Automation Agent after an
action execution attempt.

AutomationExecutionResult represents the immediate outcome of an automation
operation.

It provides:
    - Task identification
    - Action identification
    - Success/failure information
    - Execution output
    - Execution timing
    - Error information
    - Execution metadata

This model represents the result produced by the Automation Engine.

It does NOT:
    - perform retries
    - make fallback decisions
    - modify task state
    - perform planning
    - interpret natural language
    - communicate directly with the LLM

Those responsibilities belong to the Decision Manager, State Manager,
Agent Brain, and orchestration components respectively.

Author      : Team JARVIS
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# =============================================================================
# Automation Execution Result
# =============================================================================

@dataclass(frozen=True)
class AutomationExecutionResult:
    """
    Standardized result returned by an Automation Agent.

    The result describes what happened during a single automation execution
    attempt.

    It is intentionally independent of Decision Manager policies such as
    retry and fallback.
    """

    # -------------------------------------------------------------------------
    # Identification
    # -------------------------------------------------------------------------

    task_id: int

    action: str

    # -------------------------------------------------------------------------
    # Execution Status
    # -------------------------------------------------------------------------

    success: bool

    # -------------------------------------------------------------------------
    # Execution Output
    # -------------------------------------------------------------------------

    output: Any = None

    # -------------------------------------------------------------------------
    # Error Information
    # -------------------------------------------------------------------------

    error: str | None = None

    # -------------------------------------------------------------------------
    # Timing
    # -------------------------------------------------------------------------

    execution_time: float | None = None

    # -------------------------------------------------------------------------
    # Metadata
    # -------------------------------------------------------------------------

    metadata: dict[str, Any] = field(default_factory=dict)

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def __post_init__(self) -> None:
        """
        Validate and normalize the execution result.
        """

        if self.task_id < 0:
            raise ValueError(
                "task_id cannot be negative."
            )

        if not isinstance(self.action, str):
            raise TypeError(
                "action must be a string."
            )

        normalized_action = self.action.strip().lower()

        if not normalized_action:
            raise ValueError(
                "action cannot be empty."
            )

        object.__setattr__(
            self,
            "action",
            normalized_action,
        )

        if not isinstance(self.success, bool):
            raise TypeError(
                "success must be a boolean."
            )

        if self.execution_time is not None:
            if self.execution_time < 0:
                raise ValueError(
                    "execution_time cannot be negative."
                )

        if self.success and self.error is not None:
            raise ValueError(
                "A successful execution result cannot contain an error."
            )

    # -------------------------------------------------------------------------
    # Convenience Properties
    # -------------------------------------------------------------------------

    @property
    def failed(self) -> bool:
        """
        Return whether the execution failed.
        """

        return not self.success

    @property
    def has_output(self) -> bool:
        """
        Return whether execution produced an output value.
        """

        return self.output is not None

    @property
    def has_error(self) -> bool:
        """
        Return whether an execution error is present.
        """

        return self.error is not None