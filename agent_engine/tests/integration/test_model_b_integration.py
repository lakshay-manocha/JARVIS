"""
===============================================================================
File Name   : test_model_b_integration.py
Module      : Tests / Integration
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
Unit & integration tests for:
- Phase 8 (Environment Snapshot Collector)
- Phase 9 (Stored-State Mapper)
- Phase 10 (Model B Adapter)
- Phase 11 (Deterministic State Checker)
===============================================================================
"""

from __future__ import annotations

from datetime import datetime, timezone
import pytest

from agent_engine.contracts.enums import ExecutionStatus
from agent_engine.integration.adapters.model_b_adapter import ModelBAdapter
from agent_engine.integration.environment.snapshot_collector import (
    EnvironmentSnapshotCollector,
)
from agent_engine.integration.environment.stored_state_mapper import (
    StoredStateMapper,
)
from agent_engine.integration.feature_flags import IntegrationFeatureFlags
from agent_engine.integration.guard.deterministic_checker import (
    DeterministicStateChecker,
)
from agent_engine.state_manager.state_checkpoint import StateCheckpoint
from agent_engine.state_mismatch.state_mismatch_contract import (
    ChangedResource,
    ResourceChange,
    ResourceType,
    StateMismatchQuery,
    StateSnapshot,
)


# =============================================================================
# Phase 8: Environment Snapshot Collector Tests
# =============================================================================

def test_snapshot_collector_with_explicit_values():
    collector = EnvironmentSnapshotCollector()
    snapshot = collector.capture_snapshot(
        applications=["Chrome", "VSCode"],
        files=["/path/to/script.py"],
        browser_tabs=["https://example.com"],
        processes=["code /path/to/script.py"],
        completed_subtasks=["subtask_1"],
    )

    assert snapshot.applications == ["Chrome", "VSCode"]
    assert snapshot.files == ["/path/to/script.py"]
    assert snapshot.browser_tabs == ["https://example.com"]
    assert snapshot.processes == ["code /path/to/script.py"]
    assert snapshot.completed_subtasks == ["subtask_1"]
    assert "app:chrome" in snapshot.resource_identities
    assert "file:/path/to/script.py" in snapshot.resource_identities


def test_snapshot_collector_missing_defaults_to_not_available():
    collector = EnvironmentSnapshotCollector()
    snapshot = collector.capture_snapshot()

    assert snapshot.applications == "NOT_AVAILABLE"
    assert snapshot.files == "NOT_AVAILABLE"
    assert snapshot.browser_tabs == "NOT_AVAILABLE"
    assert snapshot.processes == "NOT_AVAILABLE"
    assert snapshot.completed_subtasks == "NOT_AVAILABLE"


def test_snapshot_collector_provider_error_handled_safely():
    def failing_provider():
        raise PermissionError("Access denied by OS")

    collector = EnvironmentSnapshotCollector(application_provider=failing_provider)
    snapshot = collector.capture_snapshot()

    assert snapshot.applications == "NOT_AVAILABLE"


# =============================================================================
# Phase 9: Stored-State Mapper Tests
# =============================================================================

def test_stored_state_mapper_from_checkpoint():
    checkpoint = StateCheckpoint(
        task_id=42,
        status=ExecutionStatus.COMPLETED,
        retry_count=0,
        progress=1.0,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        execution_time=1.5,
        error_message=None,
        error_code=None,
        timestamp=datetime.now(timezone.utc),
    )

    payload = {
        "applications": ["VSCode"],
        "files": ["main.py"],
    }

    snapshot = StoredStateMapper.from_checkpoint(checkpoint, payload)

    assert snapshot.applications == ["VSCode"]
    assert snapshot.files == ["main.py"]
    assert snapshot.browser_tabs == "NOT_AVAILABLE"
    assert snapshot.completed_subtasks == ["task_42"]


def test_stored_state_mapper_from_dict():
    data = {
        "applications": ["Excel"],
        "files": ["sheet.xlsx"],
        "browser_tabs": "NOT_AVAILABLE",
    }
    snapshot = StoredStateMapper.from_dict(data)

    assert snapshot.applications == ["Excel"]
    assert snapshot.files == ["sheet.xlsx"]
    assert snapshot.browser_tabs == "NOT_AVAILABLE"
    assert "app:excel" in snapshot.resource_identities


# =============================================================================
# Phase 11: Deterministic State Checker Tests
# =============================================================================

def test_deterministic_checker_detects_missing_and_added():
    stored = StateSnapshot(
        applications=["Chrome", "VSCode"],
        files=["model.py"],
        browser_tabs=["https://portal.internal"],
        processes="NOT_AVAILABLE",
        completed_subtasks="NOT_AVAILABLE",
    )
    current = StateSnapshot(
        applications=["Chrome", "Slack"],  # VSCode missing, Slack added
        files=["model.py", "output.csv"],  # output.csv added
        browser_tabs="NOT_AVAILABLE",
        processes="NOT_AVAILABLE",
        completed_subtasks="NOT_AVAILABLE",
    )

    diffs = DeterministicStateChecker.check_differences(stored, current)

    missing_apps = [
        d for d in diffs
        if d.type == ResourceType.APPLICATION and d.change == ResourceChange.MISSING
    ]
    added_apps = [
        d for d in diffs
        if d.type == ResourceType.APPLICATION and d.change == ResourceChange.ADDED
    ]
    added_files = [
        d for d in diffs
        if d.type == ResourceType.FILE and d.change == ResourceChange.ADDED
    ]

    assert any(d.identifier == "VSCode" for d in missing_apps)
    assert any(d.identifier == "Slack" for d in added_apps)
    assert any(d.identifier == "output.csv" for d in added_files)


def test_deterministic_checker_no_differences():
    stored = StateSnapshot(applications=["Chrome"], files=["file.txt"])
    current = StateSnapshot(applications=["Chrome"], files=["file.txt"])

    diffs = DeterministicStateChecker.check_differences(stored, current)
    assert len(diffs) == 0


# =============================================================================
# Phase 10: Model B Adapter Tests
# =============================================================================

def test_model_b_adapter_flag_off_uses_deterministic_fallback():
    flags = IntegrationFeatureFlags(model_b_enabled=False)
    adapter = ModelBAdapter(feature_flags=flags)

    query = StateMismatchQuery(
        stored_state=StateSnapshot(applications=["VSCode"]),
        current_state=StateSnapshot(applications=["Chrome"]),
    )
    result = adapter.check_mismatch(query)

    assert result.mismatch is True
    assert result.confidence == 1.0
    assert len(result.changed_resources) > 0
    assert "deterministic-fallback" in result.model_version


def test_model_b_adapter_inference_success():
    def mock_classifier(stored_state: dict, current_state: dict):
        return {
            "mismatch": True,
            "probability": 0.82,
            "confidence": 0.82,
            "threshold": 0.30,
            "changed_resources": [
                {"type": "APPLICATION", "identifier": "VSCode", "change": "MISSING"}
            ],
            "model_version": "Mock-ModelB-v1.0",
        }

    flags = IntegrationFeatureFlags(model_b_enabled=True)
    adapter = ModelBAdapter(classifier_callable=mock_classifier, feature_flags=flags)

    query = StateMismatchQuery(
        stored_state=StateSnapshot(applications=["VSCode"]),
        current_state=StateSnapshot(applications=[]),
    )
    result = adapter.check_mismatch(query)

    assert result.mismatch is True
    assert result.probability == 0.82
    assert result.threshold == 0.30
    assert any(r.identifier == "VSCode" and r.change == ResourceChange.MISSING for r in result.changed_resources)


def test_model_b_adapter_exception_handled_safely():
    def failing_classifier(*args, **kwargs):
        raise ValueError("Model corrupted")

    flags = IntegrationFeatureFlags(model_b_enabled=True)
    adapter = ModelBAdapter(classifier_callable=failing_classifier, feature_flags=flags)

    query = StateMismatchQuery(
        stored_state=StateSnapshot(applications=["VSCode"]),
        current_state=StateSnapshot(applications=[]),
    )
    result = adapter.check_mismatch(query)

    # Must fail-safe to deterministic difference without crashing
    assert result.mismatch is True
    assert "error-fallback" in result.model_version
