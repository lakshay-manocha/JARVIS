"""Contracts produced by the Phase F orchestration layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agent_engine.agent_brain.models.planning_result import PlanningResult
from agent_engine.agent_brain.models.processing_context import ProcessingContext
from agent_engine.contracts.enums import ResultStatus
from agent_engine.decision_manager.models.decision import DecisionResult
from agent_engine.decision_manager.models.execution_outcome import ExecutionOutcome
from agent_engine.agent_brain.models.validation_result import ValidationResult


@dataclass(slots=True)
class OrchestrationResult:
    """Complete result of one Agent Engine request."""

    request_id: str
    status: ResultStatus
    context: ProcessingContext
    validation: ValidationResult
    planning_result: PlanningResult | None = None
    outcomes: list[ExecutionOutcome] = field(default_factory=list)
    decisions: list[DecisionResult] = field(default_factory=list)
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def successful_tasks(self) -> int:
        return sum(1 for outcome in self.outcomes if outcome.success)

    @property
    def failed_tasks(self) -> int:
        return sum(1 for outcome in self.outcomes if not outcome.success)
