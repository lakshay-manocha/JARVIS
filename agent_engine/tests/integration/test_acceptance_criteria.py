"""
===============================================================================
File Name   : test_acceptance_criteria.py
Module      : Tests / Integration
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
Direct verification suite testing Integration Acceptance Criteria AC-01 to AC-12
as mandated by SRS Section 15.
===============================================================================
"""

from __future__ import annotations

from datetime import datetime, timezone
import pytest

from agent_engine.contracts.enums import ExecutionStatus
from agent_engine.decision_manager.models.decision import DecisionAction
from agent_engine.integration.adapters.model_a_adapter import ModelAAdapter
from agent_engine.integration.adapters.model_b_adapter import ModelBAdapter
from agent_engine.integration.environment.stored_state_mapper import StoredStateMapper
from agent_engine.integration.feature_flags import IntegrationFeatureFlags
from agent_engine.integration.guard.consistency_guard import (
    ConsistencyGuard,
    GuardAction,
    GuardStatus,
)
from agent_engine.integration.guard.deterministic_checker import (
    DeterministicStateChecker,
)
from agent_engine.integration.workflow_state_service import (
    WorkflowStateIntegrationService,
)
from agent_engine.state_manager.state_checkpoint import StateCheckpoint
from agent_engine.state_manager.state_manager import StateManager
from agent_engine.state_mismatch.state_mismatch_contract import (
    ResourceChange,
    ResourceType,
    StateMismatchQuery,
    StateSnapshot,
)
from agent_engine.workflow_memory.retrieval_contract import RetrievalQuery
from agent_engine.workflow_memory.workflow_record import WorkflowRecord
from agent_engine.workflow_memory.workflow_repository import WorkflowRepository


@pytest.fixture
def test_repository() -> WorkflowRepository:
    repo = WorkflowRepository()
    repo.save(
        WorkflowRecord(
            workflow_id="wf_001",
            goal="Process financial statements",
            domain="finance",
            overall_status="FAILED",
            graph={"nodes": [{"id": 1, "description": "Download PDF", "status": "COMPLETED"}, {"id": 2, "description": "Extract tables", "status": "FAILED"}]},
            current_state={"applications": ["Acrobat"]},
        )
    )
    return repo


# -----------------------------------------------------------------------------
# AC-01: Existing JARVIS works with both models disabled
# -----------------------------------------------------------------------------
def test_ac01_both_models_disabled_pipeline_safe(test_repository):
    flags = IntegrationFeatureFlags(
        model_a_enabled=False,
        model_b_enabled=False,
        consistency_guard_enabled=False,
    )
    service = WorkflowStateIntegrationService(
        workflow_repository=test_repository,
        feature_flags=flags,
    )

    # Model A advisory returns empty
    adv = service.retrieve_workflow_advisory("Process financial statements")
    assert not adv.has_advice

    # Verification passes through cleanly
    guard_res = service.verify_runtime_consistency(
        stored_state=StateSnapshot(applications=["Acrobat"]),
        current_state=StateSnapshot(applications=["Acrobat"]),
    )
    assert guard_res.can_proceed is True
    assert guard_res.status == GuardStatus.CONSISTENT


# -----------------------------------------------------------------------------
# AC-02: Model A can be enabled independently
# -----------------------------------------------------------------------------
def test_ac02_model_a_enabled_independently(test_repository):
    flags = IntegrationFeatureFlags(
        model_a_enabled=True,
        model_a_advisory_mode=True,
        model_b_enabled=False,
    )
    mock_pred = lambda query, current_state, candidate_workflows, top_k: {
        "query": query,
        "results": [{"workflow_id": "wf_001", "score": 0.95, "retrieved_node_ids": [2]}],
        "model_version": "v2.0",
    }
    adapter_a = ModelAAdapter(predictor_callable=mock_pred, feature_flags=flags)
    service = WorkflowStateIntegrationService(
        workflow_repository=test_repository,
        model_a_adapter=adapter_a,
        feature_flags=flags,
    )

    adv = service.retrieve_workflow_advisory("Process financial statements")
    assert adv.has_advice is True
    assert adv.matched_workflow_id == "wf_001"
    assert adv.continuation_node_ids == [2]


# -----------------------------------------------------------------------------
# AC-03: Model B can be enabled independently
# -----------------------------------------------------------------------------
def test_ac03_model_b_enabled_independently():
    flags = IntegrationFeatureFlags(
        model_a_enabled=False,
        model_b_enabled=True,
        consistency_guard_enabled=True,
        warning_mode_enabled=True,
    )
    mock_b = lambda stored_state, current_state: {
        "mismatch": True,
        "probability": 0.75,
        "confidence": 0.75,
        "threshold": 0.30,
        "changed_resources": [],
        "model_version": "v1.0",
    }
    adapter_b = ModelBAdapter(classifier_callable=mock_b, feature_flags=flags)
    service = WorkflowStateIntegrationService(
        model_b_adapter=adapter_b,
        feature_flags=flags,
    )

    guard_res = service.verify_runtime_consistency(
        stored_state=StateSnapshot(applications=["VSCode"]),
        current_state=StateSnapshot(applications=[]),
    )
    assert guard_res.mismatch_detected is True
    assert guard_res.status == GuardStatus.WARNING


# -----------------------------------------------------------------------------
# AC-04: Model A failure does not crash baseline JARVIS
# -----------------------------------------------------------------------------
def test_ac04_model_a_failure_does_not_crash(test_repository):
    def failing_a(*args, **kwargs):
        raise RuntimeError("Model A internal failure")

    flags = IntegrationFeatureFlags(model_a_enabled=True, model_a_advisory_mode=True)
    adapter_a = ModelAAdapter(predictor_callable=failing_a, feature_flags=flags)
    service = WorkflowStateIntegrationService(
        workflow_repository=test_repository,
        model_a_adapter=adapter_a,
        feature_flags=flags,
    )

    adv = service.retrieve_workflow_advisory("Process financial statements")
    assert not adv.has_advice


# -----------------------------------------------------------------------------
# AC-05: Model B failure does not crash baseline JARVIS
# -----------------------------------------------------------------------------
def test_ac05_model_b_failure_does_not_crash():
    def failing_b(*args, **kwargs):
        raise RuntimeError("Model B out of memory")

    flags = IntegrationFeatureFlags(model_b_enabled=True, consistency_guard_enabled=True)
    adapter_b = ModelBAdapter(classifier_callable=failing_b, feature_flags=flags)
    service = WorkflowStateIntegrationService(
        model_b_adapter=adapter_b,
        feature_flags=flags,
    )

    # Should fall back gracefully to deterministic checker
    guard_res = service.verify_runtime_consistency(
        stored_state=StateSnapshot(applications=["VSCode"]),
        current_state=StateSnapshot(applications=["VSCode"]),
    )
    assert guard_res.status == GuardStatus.CONSISTENT
    assert guard_res.can_proceed is True


# -----------------------------------------------------------------------------
# AC-06 & AC-07: Model A advisory & Model B evidence roles preserved
# -----------------------------------------------------------------------------
def test_ac06_ac07_roles_and_boundaries():
    guard = ConsistencyGuard()
    assert hasattr(guard, "evaluate")
    # Guard evaluates without directly calling execution methods
    assert not hasattr(guard, "dispatch_action")
    assert not hasattr(guard, "execute_task")


# -----------------------------------------------------------------------------
# AC-08: Deterministic state differences available independently of ML
# -----------------------------------------------------------------------------
def test_ac08_deterministic_state_differences():
    stored = StateSnapshot(applications=["Chrome", "Python"])
    current = StateSnapshot(applications=["Chrome"])

    diffs = DeterministicStateChecker.check_differences(stored, current)
    assert len(diffs) == 1
    assert diffs[0].identifier == "Python"
    assert diffs[0].change == ResourceChange.MISSING


# -----------------------------------------------------------------------------
# AC-09: Consistency Guard operates according to explicit policy
# -----------------------------------------------------------------------------
def test_ac09_guard_explicit_policy():
    flags = IntegrationFeatureFlags(
        consistency_guard_enabled=True,
        controlled_blocking_enabled=True,
    )
    guard = ConsistencyGuard(feature_flags=flags, replan_probability_threshold=0.85)

    # Moderate mismatch -> RECOVER
    from agent_engine.state_mismatch.state_mismatch_contract import StateMismatchResult
    res_mod = StateMismatchResult(
        mismatch=True, probability=0.60, confidence=0.60, threshold=0.30,
        changed_resources=[], model_version="test"
    )
    assert guard.evaluate(res_mod).recommended_action == GuardAction.RECOVER

    # Severe mismatch -> REPLAN
    res_sev = StateMismatchResult(
        mismatch=True, probability=0.90, confidence=0.90, threshold=0.30,
        changed_resources=[], model_version="test"
    )
    assert guard.evaluate(res_sev).recommended_action == GuardAction.REPLAN


# -----------------------------------------------------------------------------
# AC-10: Logging mode does not modify execution
# -----------------------------------------------------------------------------
def test_ac10_logging_mode_does_not_modify_execution():
    flags = IntegrationFeatureFlags(
        consistency_guard_enabled=True,
        warning_mode_enabled=False,
        controlled_blocking_enabled=False,
    )
    guard = ConsistencyGuard(feature_flags=flags)
    from agent_engine.state_mismatch.state_mismatch_contract import StateMismatchResult
    res = StateMismatchResult(
        mismatch=True, probability=0.80, confidence=0.80, threshold=0.30,
        changed_resources=[], model_version="test"
    )

    eval_res = guard.evaluate(res)
    assert eval_res.can_proceed is True
    assert eval_res.recommended_action == GuardAction.PROCEED


# -----------------------------------------------------------------------------
# AC-11: Warning mode does not unexpectedly block execution
# -----------------------------------------------------------------------------
def test_ac11_warning_mode_does_not_block():
    flags = IntegrationFeatureFlags(
        consistency_guard_enabled=True,
        warning_mode_enabled=True,
        controlled_blocking_enabled=False,
    )
    guard = ConsistencyGuard(feature_flags=flags)
    from agent_engine.state_mismatch.state_mismatch_contract import StateMismatchResult
    res = StateMismatchResult(
        mismatch=True, probability=0.75, confidence=0.75, threshold=0.30,
        changed_resources=[], model_version="test"
    )

    eval_res = guard.evaluate(res)
    assert eval_res.can_proceed is True
    assert eval_res.status == GuardStatus.WARNING
    assert eval_res.recommended_action == GuardAction.WARN


# -----------------------------------------------------------------------------
# AC-12: Controlled blocking/replanning occurs only through Decision pathway
# -----------------------------------------------------------------------------
def test_ac12_decision_manager_pathway():
    state_mgr = StateManager()
    state_mgr.register_task(101)
    state_mgr.set_state(101, ExecutionStatus.READY)
    state_mgr.set_state(101, ExecutionStatus.RUNNING)
    state_mgr.set_state(101, ExecutionStatus.FAILED)

    flags = IntegrationFeatureFlags(
        model_b_enabled=True,
        consistency_guard_enabled=True,
        controlled_blocking_enabled=True,
    )
    service = WorkflowStateIntegrationService(
        state_manager=state_mgr,
        feature_flags=flags,
    )

    # 1. Moderate mismatch -> Guard recommends RECOVER -> Decision Manager issues RETRY -> Bridge applies RETRYING
    mock_b = lambda stored_state, current_state: {
        "mismatch": True,
        "probability": 0.60,
        "confidence": 0.60,
        "threshold": 0.30,
        "changed_resources": [{"type": "APPLICATION", "identifier": "Chrome", "change": "MISSING"}],
        "model_version": "v1.0",
    }
    adapter_b = ModelBAdapter(classifier_callable=mock_b, feature_flags=flags)
    service = WorkflowStateIntegrationService(
        model_b_adapter=adapter_b,
        state_manager=state_mgr,
        feature_flags=flags,
    )

    guard_res = service.verify_runtime_consistency(
        stored_state=StateSnapshot(applications=["Chrome"]),
        current_state=StateSnapshot(applications=[]),
    )
    decision = service.apply_guard_decision(task_id=101, guard_result=guard_res, attempt=1, max_retries=3)

    assert decision.action == DecisionAction.RETRY
    task_state = state_mgr.get_state(task_id=101)
    assert task_state.status == ExecutionStatus.RETRYING
