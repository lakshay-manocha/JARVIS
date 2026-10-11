"""
===============================================================================
File Name   : processing_context.py
Module      : Agent Brain Models
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Represents the live processing context shared across every module of the
Agent Brain.

Unlike the LLMPlan, which is immutable, the ProcessingContext evolves as the
request passes through validation, interpretation, planning, and scheduling.

Author : Team Agent
===============================================================================
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from agent_engine.agent_brain.models.request_metadata import RequestMetadata
from uuid import uuid4
from agent_engine.agent_brain.models.interpreted_task import InterpretedTask
from agent_engine.agent_brain.models.graph_validation_result import (
    GraphValidationResult,
)

from pydantic import BaseModel, Field

from agent_engine.agent_brain.models.llm_plan import LLMPlan
from agent_engine.contracts.enums import ProcessingStage


class ProcessingContext(BaseModel):
    """
    Shared context passed between every Agent Brain module.
    """

    # ---------------------------------------------------------------------
    # Request Information
    # ---------------------------------------------------------------------

    request_id: str = Field(
        default_factory=lambda: str(uuid4())
    )

    received_at: datetime = Field(
        default_factory=datetime.utcnow
    )

    # ---------------------------------------------------------------------
    # Original Input
    # ---------------------------------------------------------------------

    llm_plan: LLMPlan

    # ---------------------------------------------------------------------
    # Processing Information
    # ---------------------------------------------------------------------

    current_stage: ProcessingStage = ProcessingStage.INITIALIZED

    metadata: RequestMetadata = Field(
        default_factory=RequestMetadata
    )

    # ---------------------------------------------------------------------
    # Runtime Logs
    # ---------------------------------------------------------------------

    processing_logs: list[str] = Field(
        default_factory=list
    )

    # ---------------------------------------------------------------------
    # Enriched Information (filled later)
    # ---------------------------------------------------------------------

    interpreted_tasks: list[InterpretedTask] = Field(
        default_factory=list
    )
    
    execution_graph: Any | None = None
    graph_validation_result: GraphValidationResult | None = None

    execution_plan: Any | None = None

    model_config = {
        "validate_assignment": True,
        "extra": "forbid"
    }

    def log(self, message: str) -> None:
        """
        Adds a processing log entry.
        """

        timestamp = datetime.utcnow().strftime("%H:%M:%S")

        self.processing_logs.append(
            f"[{timestamp}] {message}"
        )