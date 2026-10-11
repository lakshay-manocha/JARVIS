"""
===============================================================================
File Name   : interpreted_task.py
Module      : Agent Brain Models
Project     : JARVIS

Description:
Represents a task while it is being processed by the Agent Brain.

This object gradually evolves throughout the pipeline.

The task begins with raw and normalized text and is progressively enriched
with intent, action, tool, parameters, and metadata as it moves through the
Agent Brain pipeline.
===============================================================================
"""

from typing import Any

from pydantic import BaseModel, Field

from agent_engine.agent_brain.models.intent_result import IntentResult


class InterpretedTask(BaseModel):
    """
    Represents a single task inside the Agent Brain.
    """

    # ------------------------------------------------------------------
    # Task Identification
    # ------------------------------------------------------------------

    task_id: int

    # ------------------------------------------------------------------
    # Original Task Information
    # ------------------------------------------------------------------

    original_text: str

    normalized_text: str

    # ------------------------------------------------------------------
    # Intent Information
    # ------------------------------------------------------------------

    intent: IntentResult | None = None

    # ------------------------------------------------------------------
    # Resolved Action
    # ------------------------------------------------------------------

    action: str | None = None

    # ------------------------------------------------------------------
    # Selected Tool / Controller
    # ------------------------------------------------------------------

    tool: str | None = None

    # ------------------------------------------------------------------
    # Extracted / Resolved Parameters
    # ------------------------------------------------------------------

    parameters: dict[str, Any] = Field(
        default_factory=dict
    )

    # ------------------------------------------------------------------
    # Additional Metadata
    # ------------------------------------------------------------------

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )

    # ------------------------------------------------------------------
    # Pydantic Configuration
    # ------------------------------------------------------------------

    model_config = {
        "validate_assignment": True,
        "extra": "forbid"
    }