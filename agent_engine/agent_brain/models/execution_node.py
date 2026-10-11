"""
===============================================================================
File Name   : execution_node.py
Module      : Agent Brain Models
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Represents a single executable node within the execution graph.

Each ExecutionNode wraps an InterpretedTask and stores all planning and runtime
information required by the Planner and Dispatcher.

Execution nodes are connected together to form a Directed Acyclic Graph (DAG),
allowing JARVIS to determine execution order, dependencies, retries, and
parallel execution opportunities.

Author      : Team JARVIS
===============================================================================
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from agent_engine.agent_brain.models.interpreted_task import InterpretedTask
from agent_engine.contracts.enums import (
    ExecutionStatus,
    Priority,
)


class ExecutionNode(BaseModel):
    """
    Represents a single node inside the execution graph.
    """

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    node_id: int

    # ------------------------------------------------------------------
    # Task
    # ------------------------------------------------------------------

    task: InterpretedTask

    # ------------------------------------------------------------------
    # Graph Relationships
    # ------------------------------------------------------------------

    parents: list[int] = Field(
        default_factory=list
    )

    children: list[int] = Field(
        default_factory=list
    )

    # ------------------------------------------------------------------
    # Planning Information
    # ------------------------------------------------------------------

    priority: Priority = Priority.MEDIUM

    # ------------------------------------------------------------------
    # Runtime State
    # ------------------------------------------------------------------

    status: ExecutionStatus = ExecutionStatus.PENDING

    retry_count: int = Field(
        default=0,
        ge=0
    )

    max_retries: int = Field(
        default=3,
        ge=0
    )

    # ------------------------------------------------------------------
    # Runtime Metadata
    # ------------------------------------------------------------------

    estimated_duration: float | None = None

    controller_output: Any | None = None

    execution_metadata: dict[str, Any] = Field(
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

    def add_parent(self, parent_id: int) -> None:
        """
        Adds a parent dependency if it does not already exist.
        """

        if parent_id not in self.parents:
            self.parents.append(parent_id)


    def add_child(self, child_id: int) -> None:
        """
        Adds a child dependency if it does not already exist.
        """

        if child_id not in self.children:
            self.children.append(child_id)

    @property
    def dependency_count(self) -> int:
        """
        Returns the number of unresolved parent dependencies.
        """

        return len(self.parents)

    @property
    def is_ready(self) -> bool:
        """
        Returns whether the node is ready for execution.
        """

        return (
            self.status == ExecutionStatus.READY
        )

    @property
    def is_completed(self) -> bool:
        """
        Returns whether execution has completed successfully.
        """

        return (
            self.status == ExecutionStatus.COMPLETED
        )