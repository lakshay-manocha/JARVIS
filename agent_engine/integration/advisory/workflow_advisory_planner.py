"""
===============================================================================
File Name   : workflow_advisory_planner.py
Module      : Integration / Advisory
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
Implements Phase 6 Model A Advisory Planning integration.

Allows Model A retrieval output to provide additional planning context.
The context is strictly advisory:
- Existing Planner remains authoritative.
- Model A does NOT independently decide execution or mutate execution graphs.
===============================================================================
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from agent_engine.integration.adapters.model_a_adapter import ModelAAdapter
from agent_engine.integration.feature_flags import (
    IntegrationFeatureFlags,
    get_feature_flags,
)
from agent_engine.workflow_memory.retrieval_contract import RetrievalQuery
from agent_engine.workflow_memory.workflow_repository import WorkflowRepository

logger = logging.getLogger("jarvis.integration.advisory_planner")


@dataclass
class WorkflowAdvisoryContext:
    """
    Advisory information derived from historical workflow memory.
    """

    has_advice: bool = False
    matched_workflow_id: str | None = None
    relevance_score: float = 0.0
    continuation_node_ids: list[Any] = field(default_factory=list)
    suggested_nodes: list[dict[str, Any]] = field(default_factory=list)
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "has_advice": self.has_advice,
            "matched_workflow_id": self.matched_workflow_id,
            "relevance_score": self.relevance_score,
            "continuation_node_ids": self.continuation_node_ids,
            "suggested_nodes": self.suggested_nodes,
            "summary": self.summary,
            "metadata": self.metadata,
        }


class WorkflowAdvisoryPlanner:
    """
    Advisory planning bridge for Model A.

    Produces advisory context for JARVIS planning components without mutating
    the frozen baseline planner.
    """

    def __init__(
        self,
        adapter: ModelAAdapter,
        repository: WorkflowRepository,
        feature_flags: IntegrationFeatureFlags | None = None,
        min_relevance_threshold: float = 0.50,
    ) -> None:
        self.adapter = adapter
        self.repository = repository
        self._feature_flags = feature_flags
        self.min_relevance_threshold = min_relevance_threshold

    def _get_flags(self) -> IntegrationFeatureFlags:
        return self._feature_flags or get_feature_flags()

    def get_advisory_context(
        self,
        user_goal: str,
        current_state: dict[str, Any] | None = None,
        domain: str | None = None,
    ) -> WorkflowAdvisoryContext:
        """
        Query Model A for advisory historical context.

        Returns an empty WorkflowAdvisoryContext if:
        - Feature flags are off
        - Model A is not in advisory mode
        - No relevant workflow is found above min_relevance_threshold
        """
        flags = self._get_flags()

        if not flags.model_a_enabled or not flags.model_a_advisory_mode:
            return WorkflowAdvisoryContext(
                has_advice=False,
                summary="Advisory mode disabled by feature flags.",
            )

        query = RetrievalQuery(
            query=user_goal,
            domain=domain,
            top_k=1,
            min_score=self.min_relevance_threshold,
        )

        response = self.adapter.retrieve(
            query=query,
            repository=self.repository,
            current_state=current_state,
        )

        if not response.retrieval_performed or not response.results:
            return WorkflowAdvisoryContext(
                has_advice=False,
                summary="No relevant historical workflow found above threshold.",
            )

        top_result = response.results[0]
        wf_id = top_result.document.workflow_id
        record = self.repository.get(wf_id)

        continuation_node_ids = top_result.metadata.get(
            "retrieved_node_ids", []
        )

        suggested_nodes = []
        if record and "nodes" in record.graph:
            for node in record.graph.get("nodes", []):
                n_id = node.get("id") or node.get("node_id")
                if n_id in continuation_node_ids:
                    suggested_nodes.append(node)

        summary = (
            f"Advisory: Matching workflow '{wf_id}' with score {top_result.score:.2f}. "
            f"Suggested continuation node IDs: {continuation_node_ids}"
        )

        logger.info("[ADVISORY_PLANNING] %s", summary)

        return WorkflowAdvisoryContext(
            has_advice=True,
            matched_workflow_id=wf_id,
            relevance_score=top_result.score,
            continuation_node_ids=continuation_node_ids,
            suggested_nodes=suggested_nodes,
            summary=summary,
            metadata={
                "domain": top_result.document.domain,
                "overall_status": top_result.document.overall_status,
            },
        )
