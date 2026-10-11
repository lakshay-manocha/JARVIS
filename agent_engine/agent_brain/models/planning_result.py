"""
===============================================================================
File Name   : planning_result.py
Module      : Agent Brain Models
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Represents the complete output produced by the Planner.

The PlanningResult bundles together the generated execution graph,
execution order, and planning metadata before it is transformed into
the final ExecutionPlan contract consumed by the Automation Engine.

Author : Team JARVIS
===============================================================================
"""
from datetime import datetime
from pydantic import BaseModel, Field
from agent_engine.agent_brain.models.execution_graph import ExecutionGraph

class PlanningResult(BaseModel):

    graph: ExecutionGraph

    is_valid: bool = True

    execution_order: list[int] = Field(
        default_factory=list
    )

    parallel_groups: list[list[int]] = Field(
        default_factory=list
    )

    total_steps: int = 0

    estimated_time: float = 0.0

    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )

    planner_name: str = "RuleBasedPlanner"

    planner_version: str = "1.0"

    planning_notes: list[str] = Field(
        default_factory=list
    )

    model_config = {
        "validate_assignment": True,
        "extra": "forbid"
    }

    def add_note(self, note: str):

        self.planning_notes.append(note)