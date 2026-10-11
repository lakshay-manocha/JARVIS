"""Phase 2 hardening and Phase 3 runtime-integration regression tests."""

from __future__ import annotations

import math
from unittest.mock import Mock

import pytest

from agent_engine.contracts.enums import ExecutionStatus
from agent_engine.decision_manager.models.decision import DecisionAction
from agent_engine.integration.adapters.model_a_adapter import ModelAAdapter
from agent_engine.integration.adapters.model_b_adapter import ModelBAdapter
from agent_engine.integration.feature_flags import (
    IntegrationFeatureFlags,
    get_feature_flags,
    reset_feature_flags,
)
from agent_engine.integration.guard.consistency_guard import (
    ConsistencyGuard,
    GuardAction,
    GuardStatus,
)
from agent_engine.integration.workflow_state_service import WorkflowStateIntegrationService
from agent_engine.state_manager.state_manager import StateManager
from agent_engine.state_mismatch.state_mismatch_contract import (
    StateMismatchQuery,
    StateSnapshot,
)
from agent_engine.workflow_memory.retrieval_contract import RetrievalQuery
from agent_engine.workflow_memory.workflow_record import WorkflowRecord
from agent_engine.workflow_memory.workflow_repository import WorkflowRepository


@pytest.mark.parametrize(
    ("enabled", "logging_mode", "advisory_mode", "expected"),
    [
        (False, False, False, False),
        (False, True, False, False),
        (False, False, True, False),
        (False, True, True, False),
        (True, False, False, False),
        (True, True, False, True),
        (True, False, True, True),
        (True, True, True, True),
    ],
)
def test_model_a_active_flag_truth_table(enabled, logging_mode, advisory_mode, expected):
    flags = IntegrationFeatureFlags(
        model_a_enabled=enabled,
        model_a_logging_mode=logging_mode,
        model_a_advisory_mode=advisory_mode,
    )
    assert flags.is_model_a_active() is expected


def test_model_a_disabled_modes_do_not_call_predictor():
    called = False

    def predictor(**kwargs):
        nonlocal called
        called = True
        return {"results": []}

    flags = IntegrationFeatureFlags(
        model_a_enabled=True,
        model_a_logging_mode=False,
        model_a_advisory_mode=False,
    )
    repo = WorkflowRepository()
    repo.save(WorkflowRecord(
        workflow_id="wf_one",
        goal="Open editor",
        domain="desktop",
        overall_status="COMPLETED",
        graph={"nodes": []},
        current_state={},
    ))
    result = ModelAAdapter(
        predictor_callable=predictor, feature_flags=flags
    ).retrieve(RetrievalQuery(query="Open editor"), repo)

    assert not called
    assert result.retrieval_performed is False
    assert result.metadata["reason"] == "FEATURE_MODES_DISABLED"


@pytest.mark.parametrize(
    "bad_output",
    [
        None,
        [],
        {"results": "not-a-list"},
        {"results": [None]},
        {"results": [{"workflow_id": "wf_one", "score": float("nan")}]},
        {"results": [{"workflow_id": "wf_one", "score": 1.5}]},
    ],
)
def test_model_a_malformed_output_fails_safe(bad_output):
    flags = IntegrationFeatureFlags(
        model_a_enabled=True,
        model_a_logging_mode=False,
        model_a_advisory_mode=True,
    )
    repo = WorkflowRepository()
    repo.save(WorkflowRecord(
        workflow_id="wf_one",
        goal="Open editor",
        domain="desktop",
        overall_status="COMPLETED",
        graph={"nodes": []},
        current_state={},
    ))
    adapter = ModelAAdapter(
        predictor_callable=lambda **kwargs: bad_output,
        feature_flags=flags,
    )

    result = adapter.retrieve(RetrievalQuery(query="Open editor"), repo)
    assert result.retrieval_performed is False
    assert result.results == []
    assert result.metadata["reason"] == "MALFORMED_OUTPUT"


def test_model_a_logging_flag_suppresses_retrieval_telemetry(monkeypatch):
    flags = IntegrationFeatureFlags(
        model_a_enabled=True,
        model_a_logging_mode=False,
        model_a_advisory_mode=True,
    )
    repo = WorkflowRepository()
    repo.save(WorkflowRecord(
        workflow_id="wf_one",
        goal="Open editor",
        domain="desktop",
        overall_status="COMPLETED",
        graph={"nodes": []},
        current_state={},
    ))
    adapter = ModelAAdapter(
        predictor_callable=lambda **kwargs: {
            "results": [{"workflow_id": "wf_one", "score": 0.9}],
            "model_version": "test",
        },
        feature_flags=flags,
    )
    telemetry = Mock()
    monkeypatch.setattr(adapter, "_log_operation", telemetry)

    result = adapter.retrieve(RetrievalQuery(query="Open editor"), repo)
    assert result.retrieval_performed is True
    telemetry.assert_not_called()


def _mismatch_query():
    return StateMismatchQuery(
        stored_state=StateSnapshot(applications=["VSCode"]),
        current_state=StateSnapshot(applications=[]),
    )


@pytest.mark.parametrize(
    "bad_output",
    [
        None,
        [],
        {"mismatch": True, "probability": 1.2, "confidence": 0.8, "threshold": 0.3},
        {"mismatch": True, "probability": float("nan"), "confidence": 0.8, "threshold": 0.3},
        {"mismatch": True, "probability": 0.8, "confidence": -0.1, "threshold": 0.3},
        {"mismatch": "yes", "probability": 0.8, "confidence": 0.8, "threshold": 0.3},
        {"mismatch": True, "probability": 0.8, "confidence": 0.8, "threshold": 0.3,
         "changed_resources": "not-a-list"},
    ],
)
def test_model_b_malformed_output_uses_deterministic_fallback(bad_output):
    flags = IntegrationFeatureFlags(model_b_enabled=True, model_b_logging_mode=False)
    adapter = ModelBAdapter(
        classifier_callable=lambda **kwargs: bad_output,
        feature_flags=flags,
    )

    result = adapter.check_mismatch(_mismatch_query())
    assert result.mismatch is True
    assert result.probability == 1.0
    assert result.confidence == 1.0
    assert "malformed-output-fallback" in result.model_version
    assert any(item.identifier == "VSCode" for item in result.changed_resources)


def test_model_b_missing_predictor_assets_falls_back_to_deterministic_evidence(tmp_path):
    flags = IntegrationFeatureFlags(model_b_enabled=True, model_b_logging_mode=False)
    adapter = ModelBAdapter(
        model_dir=str(tmp_path / "missing-model-assets"),
        feature_flags=flags,
    )
    result = adapter.check_mismatch(_mismatch_query())

    assert result.mismatch is True
    assert result.probability == 1.0
    assert "fallback" in result.model_version
    assert any(item.identifier == "VSCode" for item in result.changed_resources)


def test_model_b_threshold_configuration_is_validated():
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        ModelBAdapter(threshold=math.nan)


def test_model_b_logging_flag_suppresses_inference_telemetry(monkeypatch):
    flags = IntegrationFeatureFlags(model_b_enabled=True, model_b_logging_mode=False)
    adapter = ModelBAdapter(
        classifier_callable=lambda **kwargs: {
            "mismatch": True,
            "probability": 0.7,
            "confidence": 0.8,
            "threshold": 0.3,
            "changed_resources": [],
            "model_version": "test-model",
        },
        feature_flags=flags,
    )
    telemetry = Mock()
    monkeypatch.setattr(adapter, "_log_inference", telemetry)

    result = adapter.check_mismatch(_mismatch_query())
    assert result.mismatch is True
    telemetry.assert_not_called()


def test_disabled_guard_does_not_turn_model_b_evidence_into_runtime_blocking():
    flags = IntegrationFeatureFlags(
        model_b_enabled=False,
        consistency_guard_enabled=False,
        warning_mode_enabled=True,
        controlled_blocking_enabled=True,
    )
    service = WorkflowStateIntegrationService(feature_flags=flags)
    guard_result = service.verify_runtime_consistency(
        stored_state=StateSnapshot(applications=["VSCode"]),
        current_state=StateSnapshot(applications=["Chrome"]),
    )

    assert guard_result.mismatch_detected is True
    assert guard_result.recommended_action == GuardAction.PROCEED
    assert guard_result.can_proceed is True
    decision = service.apply_guard_decision(task_id=501, guard_result=guard_result)
    assert decision.action == DecisionAction.CONTINUE


def test_model_a_advisory_does_not_mutate_historical_workflow_graph():
    flags = IntegrationFeatureFlags(
        model_a_enabled=True,
        model_a_logging_mode=False,
        model_a_advisory_mode=True,
        model_b_enabled=False,
    )
    repo = WorkflowRepository()
    original_graph = {
        "nodes": [
            {"id": 1, "description": "Open browser", "status": "COMPLETED"},
            {"id": 2, "description": "Read page", "status": "COMPLETED"},
        ]
    }
    repo.save(WorkflowRecord(
        workflow_id="wf_browser",
        goal="Open browser and read page",
        domain="browser",
        overall_status="COMPLETED",
        graph=original_graph,
        current_state={},
    ))
    adapter = ModelAAdapter(
        predictor_callable=lambda **kwargs: {
            "results": [
                {"workflow_id": "wf_browser", "score": 0.95, "retrieved_node_ids": [2]}
            ],
            "model_version": "test-model-a",
        },
        feature_flags=flags,
    )
    service = WorkflowStateIntegrationService(
        workflow_repository=repo,
        model_a_adapter=adapter,
        feature_flags=flags,
    )

    advisory = service.retrieve_workflow_advisory("Read a page")
    assert advisory.has_advice is True
    assert advisory.continuation_node_ids == [2]
    assert repo.get("wf_browser").graph == original_graph


def test_model_b_guard_decision_updates_runtime_state_and_history():
    flags = IntegrationFeatureFlags(
        model_b_enabled=True,
        model_b_logging_mode=False,
        consistency_guard_enabled=True,
        warning_mode_enabled=False,
        controlled_blocking_enabled=True,
    )
    state_manager = StateManager()
    state_manager.register_task(701)
    state_manager.set_state(701, ExecutionStatus.READY)
    state_manager.set_state(701, ExecutionStatus.RUNNING)
    state_manager.set_state(701, ExecutionStatus.FAILED)

    adapter = ModelBAdapter(
        classifier_callable=lambda **kwargs: {
            "mismatch": True,
            "probability": 0.65,
            "confidence": 0.65,
            "threshold": 0.30,
            "changed_resources": [],
            "model_version": "test-model-b",
        },
        feature_flags=flags,
    )
    service = WorkflowStateIntegrationService(
        model_b_adapter=adapter,
        state_manager=state_manager,
        feature_flags=flags,
    )
    guard_result = service.verify_runtime_consistency(
        stored_state=StateSnapshot(applications=["VSCode"]),
        current_state=StateSnapshot(applications=[]),
    )

    assert guard_result.recommended_action == GuardAction.RECOVER
    decision = service.apply_guard_decision(
        task_id=701,
        guard_result=guard_result,
        attempt=1,
        max_retries=3,
    )
    assert decision.action == DecisionAction.RETRY
    assert state_manager.get_state(701).status == ExecutionStatus.RETRYING
    history = state_manager.get_history(701)
    assert history
    assert history[-1].to_status == ExecutionStatus.RETRYING


def test_controlled_blocking_replan_path_reaches_failure_state():
    flags = IntegrationFeatureFlags(
        model_b_enabled=True,
        model_b_logging_mode=False,
        consistency_guard_enabled=True,
        controlled_blocking_enabled=True,
    )
    state_manager = StateManager()
    state_manager.register_task(702)
    state_manager.set_state(702, ExecutionStatus.READY)
    state_manager.set_state(702, ExecutionStatus.RUNNING)

    adapter = ModelBAdapter(
        classifier_callable=lambda **kwargs: {
            "mismatch": True,
            "probability": 0.92,
            "confidence": 0.92,
            "threshold": 0.30,
            "changed_resources": [],
            "model_version": "test-model-b",
        },
        feature_flags=flags,
    )
    service = WorkflowStateIntegrationService(
        model_b_adapter=adapter,
        state_manager=state_manager,
        feature_flags=flags,
    )
    guard_result = service.verify_runtime_consistency(
        stored_state=StateSnapshot(applications=["VSCode"]),
        current_state=StateSnapshot(applications=[]),
    )
    assert guard_result.recommended_action == GuardAction.REPLAN
    decision = service.apply_guard_decision(task_id=702, guard_result=guard_result)

    assert decision.action == DecisionAction.FAIL
    assert state_manager.get_state(702).status == ExecutionStatus.FAILED


@pytest.mark.parametrize(
    ("model_b_enabled", "expected"),
    [(False, False), (True, True)],
)
def test_model_b_active_flag_truth_table(model_b_enabled, expected):
    flags = IntegrationFeatureFlags(model_b_enabled=model_b_enabled)
    assert flags.is_model_b_active() is expected


@pytest.mark.parametrize(
    ("guard_enabled", "expected"),
    [(False, False), (True, True)],
)
def test_guard_active_flag_truth_table(guard_enabled, expected):
    flags = IntegrationFeatureFlags(consistency_guard_enabled=guard_enabled)
    assert flags.is_guard_active() is expected


def test_environment_feature_flags_parse_and_reset(monkeypatch):
    with monkeypatch.context() as env:
        env.setenv("JARVIS_MODEL_A_ENABLED", "YES")
        env.setenv("JARVIS_MODEL_A_LOGGING_MODE", "off")
        env.setenv("JARVIS_MODEL_A_ADVISORY_MODE", "true")
        env.setenv("JARVIS_MODEL_B_ENABLED", "1")
        env.setenv("JARVIS_MODEL_B_LOGGING_MODE", "false")
        env.setenv("JARVIS_CONSISTENCY_GUARD_ENABLED", "on")
        env.setenv("JARVIS_WARNING_MODE_ENABLED", "no")
        env.setenv("JARVIS_CONTROLLED_BLOCKING_ENABLED", "true")

        flags = reset_feature_flags()
        assert flags.model_a_enabled is True
        assert flags.model_a_logging_mode is False
        assert flags.model_a_advisory_mode is True
        assert flags.model_b_enabled is True
        assert flags.model_b_logging_mode is False
        assert flags.consistency_guard_enabled is True
        assert flags.warning_mode_enabled is False
        assert flags.controlled_blocking_enabled is True
        assert get_feature_flags() is flags

    reset_feature_flags()


def test_model_b_disabled_does_not_call_predictor():
    called = False

    def classifier(**kwargs):
        nonlocal called
        called = True
        raise AssertionError("Disabled Model B must not run inference.")

    flags = IntegrationFeatureFlags(model_b_enabled=False)
    result = ModelBAdapter(
        classifier_callable=classifier, feature_flags=flags
    ).check_mismatch(_mismatch_query())

    assert called is False
    assert result.mismatch is True
    assert "deterministic-fallback" in result.model_version


def test_deterministic_difference_cannot_be_overruled_by_negative_model_label():
    flags = IntegrationFeatureFlags(model_b_enabled=True, model_b_logging_mode=False)
    adapter = ModelBAdapter(
        classifier_callable=lambda **kwargs: {
            "mismatch": False,
            "probability": 0.05,
            "confidence": 0.9,
            "threshold": 0.3,
            "changed_resources": [],
            "model_version": "test-model-b",
        },
        feature_flags=flags,
    )
    result = adapter.check_mismatch(_mismatch_query())

    assert result.mismatch is True
    assert any(item.identifier == "VSCode" for item in result.changed_resources)
