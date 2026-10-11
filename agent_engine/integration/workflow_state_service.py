"""
===============================================================================
File Name   : workflow_state_service.py
Module      : Integration
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
Master integration service combining Model A, Model B, Consistency Guard,
and Decision Manager / State Manager into a unified, safe runtime pipeline.

Enforces:
- Advisory-only behavior for Model A
- Evidence-only behavior for Model B
- Policy enforcement through Consistency Guard
- Authoritative execution through Decision Manager & DecisionStateBridge
- Fail-safe operation under feature flags
===============================================================================
"""

from __future__ import annotations

import logging
from typing import Any

from agent_engine.decision_manager.models.decision import (
    DecisionAction,
    DecisionResult,
)
from agent_engine.integration.adapters.model_a_adapter import ModelAAdapter
from agent_engine.integration.adapters.model_b_adapter import ModelBAdapter
from agent_engine.integration.advisory.workflow_advisory_planner import (
    WorkflowAdvisoryContext,
    WorkflowAdvisoryPlanner,
)
from agent_engine.integration.decision_state_bridge import DecisionStateBridge
from agent_engine.integration.environment.snapshot_collector import (
    EnvironmentSnapshotCollector,
)
from agent_engine.integration.environment.stored_state_mapper import (
    StoredStateMapper,
)
from agent_engine.integration.feature_flags import (
    IntegrationFeatureFlags,
    get_feature_flags,
)
from agent_engine.integration.guard.consistency_guard import (
    ConsistencyGuard,
    GuardAction,
    GuardEvaluationResult,
    GuardStatus,
)
from agent_engine.state_manager.state_checkpoint import StateCheckpoint
from agent_engine.state_manager.state_manager import StateManager
from agent_engine.state_mismatch.state_mismatch_contract import (
    StateMismatchQuery,
    StateMismatchResult,
    StateSnapshot,
)
from agent_engine.workflow_memory.workflow_repository import WorkflowRepository

logger = logging.getLogger("jarvis.integration.service")


class WorkflowStateIntegrationService:
    """
    Unified Integration Service coordinating Model A, Model B, and Consistency Guard.
    """

    def __init__(
        self,
        workflow_repository: WorkflowRepository | None = None,
        model_a_adapter: ModelAAdapter | None = None,
        model_b_adapter: ModelBAdapter | None = None,
        snapshot_collector: EnvironmentSnapshotCollector | None = None,
        consistency_guard: ConsistencyGuard | None = None,
        state_manager: StateManager | None = None,
        decision_bridge: DecisionStateBridge | None = None,
        feature_flags: IntegrationFeatureFlags | None = None,
    ) -> None:
        self.flags = feature_flags or get_feature_flags()
        self.workflow_repository = workflow_repository or WorkflowRepository()
        self.model_a_adapter = model_a_adapter or ModelAAdapter(feature_flags=self.flags)
        self.model_b_adapter = model_b_adapter or ModelBAdapter(feature_flags=self.flags)
        self.snapshot_collector = snapshot_collector or EnvironmentSnapshotCollector()
        self.consistency_guard = consistency_guard or ConsistencyGuard(feature_flags=self.flags)
        self.state_manager = state_manager
        self.decision_bridge = (
            decision_bridge
            if decision_bridge is not None
            else (DecisionStateBridge(self.state_manager) if self.state_manager else None)
        )
        self.advisory_planner = WorkflowAdvisoryPlanner(
            adapter=self.model_a_adapter,
            repository=self.workflow_repository,
            feature_flags=self.flags,
        )

    # -------------------------------------------------------------------------
    # Model A: Goal-Conditioned Workflow Retrieval & Advisory
    # -------------------------------------------------------------------------

    def retrieve_workflow_advisory(
        self,
        user_goal: str,
        current_state: dict[str, Any] | None = None,
        domain: str | None = None,
    ) -> WorkflowAdvisoryContext:
        """
        Query Model A for workflow memory advisory context.
        """
        return self.advisory_planner.get_advisory_context(
            user_goal=user_goal,
            current_state=current_state,
            domain=domain,
        )

    # -------------------------------------------------------------------------
    # Model B & Guard: State Verification & Safety Gate
    # -------------------------------------------------------------------------

    def verify_runtime_consistency(
        self,
        stored_state: StateSnapshot | StateCheckpoint | dict[str, Any],
        current_state: StateSnapshot | dict[str, Any] | None = None,
        target_workflow_id: str | None = None,
        continuation_node_ids: list[Any] | None = None,
    ) -> GuardEvaluationResult:
        """
        Verify runtime environment compatibility before continuing or resuming.
        """
        # Convert stored state
        if isinstance(stored_state, StateCheckpoint):
            stored_snapshot = StoredStateMapper.from_checkpoint(stored_state)
        elif isinstance(stored_state, dict):
            stored_snapshot = StoredStateMapper.from_dict(stored_state)
        else:
            stored_snapshot = stored_state

        # Convert current state or capture live snapshot
        if current_state is None:
            current_snapshot = self.snapshot_collector.capture_snapshot()
        elif isinstance(current_state, dict):
            current_snapshot = StoredStateMapper.from_dict(current_state)
        else:
            current_snapshot = current_state

        # Query Model B Mismatch Adapter
        mismatch_query = StateMismatchQuery(
            stored_state=stored_snapshot,
            current_state=current_snapshot,
        )
        mismatch_result: StateMismatchResult = self.model_b_adapter.check_mismatch(
            mismatch_query
        )

        # Evaluate through Consistency Guard
        guard_result: GuardEvaluationResult = self.consistency_guard.evaluate(
            mismatch_result=mismatch_result,
            stored_state=stored_snapshot,
            current_state=current_snapshot,
            target_workflow_id=target_workflow_id,
            continuation_node_ids=continuation_node_ids,
        )

        return guard_result

    # -------------------------------------------------------------------------
    # Decision Bridge: Map Guard Action to JARVIS Decision Manager
    # -------------------------------------------------------------------------

    def apply_guard_decision(
        self,
        task_id: int,
        guard_result: GuardEvaluationResult,
        attempt: int = 1,
        max_retries: int = 3,
    ) -> DecisionResult:
        """
        Translate a GuardEvaluationResult into a DecisionResult.

        CONTINUE decisions are returned without applying a state transition.
        The frozen DecisionStateBridge and StateManager remain unchanged.
        """
        action = guard_result.recommended_action

        if action in (GuardAction.PROCEED, GuardAction.WARN):
            decision_action = DecisionAction.CONTINUE

        elif action == GuardAction.RECOVER:
            decision_action = (
                DecisionAction.RETRY
                if attempt < max_retries
                else DecisionAction.FALLBACK
            )

        elif action in (GuardAction.REPLAN, GuardAction.BLOCK):
            decision_action = DecisionAction.FAIL

        else:
            decision_action = DecisionAction.FAIL

        decision = DecisionResult(
            action=decision_action,
            task_id=task_id,
            reason=(
                guard_result.reason
                or f"Consistency Guard: {guard_result.status.value}"
            ),
            attempt=attempt,
            max_retries=max_retries,
        )

        # CONTINUE is intentionally a no-op at the state-transition boundary.
        # It must not be translated into COMPLETED by the bridge.
        if (
            self.decision_bridge is not None
            and decision_action != DecisionAction.CONTINUE
        ):
            try:
                self.decision_bridge.apply_decision(decision)
            except Exception:
                logger.warning(
                    "DecisionStateBridge could not apply decision to task %d",
                    task_id,
                    exc_info=True,
                )

        return decision