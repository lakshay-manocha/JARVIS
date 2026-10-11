"""
===============================================================================
File Name   : test_consistency_guard.py
Module      : Tests / Integration
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
Unit & integration tests for:
- Phase 12: Consistency Guard
- Phase 13: Logging-Only Guard
- Phase 14: Warning Mode
- Phase 15: Controlled Blocking / Replanning
===============================================================================
"""

from __future__ import annotations

import pytest

from agent_engine.integration.feature_flags import IntegrationFeatureFlags
from agent_engine.integration.guard.consistency_guard import (
    ConsistencyGuard,
    GuardAction,
    GuardStatus,
)
from agent_engine.state_mismatch.state_mismatch_contract import (
    ChangedResource,
    ResourceChange,
    ResourceType,
    StateMismatchResult,
)


@pytest.fixture
def mismatch_result_moderate() -> StateMismatchResult:
    return StateMismatchResult(
        mismatch=True,
        probability=0.65,
        confidence=0.65,
        threshold=0.30,
        changed_resources=[
            ChangedResource(
                type=ResourceType.APPLICATION,
                identifier="Chrome",
                change=ResourceChange.MISSING,
            )
        ],
        model_version="Test-ModelB-v1.0",
    )


@pytest.fixture
def mismatch_result_severe() -> StateMismatchResult:
    return StateMismatchResult(
        mismatch=True,
        probability=0.92,
        confidence=0.92,
        threshold=0.30,
        changed_resources=[
            ChangedResource(
                type=ResourceType.APPLICATION,
                identifier="Chrome",
                change=ResourceChange.MISSING,
            ),
            ChangedResource(
                type=ResourceType.FILE,
                identifier="dataset.csv",
                change=ResourceChange.MISSING,
            ),
        ],
        model_version="Test-ModelB-v1.0",
    )


@pytest.fixture
def consistent_result() -> StateMismatchResult:
    return StateMismatchResult(
        mismatch=False,
        probability=0.10,
        confidence=0.90,
        threshold=0.30,
        changed_resources=[],
        model_version="Test-ModelB-v1.0",
    )


def test_guard_disabled_allows_continuation(mismatch_result_moderate):
    flags = IntegrationFeatureFlags(consistency_guard_enabled=False)
    guard = ConsistencyGuard(feature_flags=flags)

    result = guard.evaluate(mismatch_result_moderate)
    assert result.can_proceed is True
    assert result.status == GuardStatus.CONSISTENT
    assert result.recommended_action == GuardAction.PROCEED


def test_guard_consistent_state(consistent_result):
    flags = IntegrationFeatureFlags(consistency_guard_enabled=True)
    guard = ConsistencyGuard(feature_flags=flags)

    result = guard.evaluate(consistent_result)
    assert result.can_proceed is True
    assert result.status == GuardStatus.CONSISTENT
    assert result.recommended_action == GuardAction.PROCEED
    assert not result.mismatch_detected


def test_phase_13_logging_only_mode(mismatch_result_moderate):
    # Logging-only: Guard is enabled, but Warning and Blocking are disabled
    flags = IntegrationFeatureFlags(
        consistency_guard_enabled=True,
        warning_mode_enabled=False,
        controlled_blocking_enabled=False,
    )
    guard = ConsistencyGuard(feature_flags=flags)

    result = guard.evaluate(mismatch_result_moderate)
    # Execution continues without disruption
    assert result.can_proceed is True
    assert result.status == GuardStatus.CONSISTENT
    assert result.recommended_action == GuardAction.PROCEED
    assert result.mismatch_detected is True
    assert "Logging-Only" in result.reason


def test_phase_14_warning_mode(mismatch_result_moderate):
    # Warning mode enabled, but Controlled Blocking disabled
    flags = IntegrationFeatureFlags(
        consistency_guard_enabled=True,
        warning_mode_enabled=True,
        controlled_blocking_enabled=False,
    )
    guard = ConsistencyGuard(feature_flags=flags)

    result = guard.evaluate(mismatch_result_moderate)
    # Generates warning, but does not block execution
    assert result.can_proceed is True
    assert result.status == GuardStatus.WARNING
    assert result.recommended_action == GuardAction.WARN
    assert result.mismatch_detected is True
    assert len(result.recovery_hints) > 0


def test_phase_15_controlled_blocking_recovery(mismatch_result_moderate):
    # Controlled Blocking enabled: moderate mismatch triggers targeted RECOVER
    flags = IntegrationFeatureFlags(
        consistency_guard_enabled=True,
        controlled_blocking_enabled=True,
    )
    guard = ConsistencyGuard(feature_flags=flags, replan_probability_threshold=0.85)

    result = guard.evaluate(mismatch_result_moderate)
    assert result.can_proceed is False
    assert result.status == GuardStatus.MISMATCH
    assert result.recommended_action == GuardAction.RECOVER
    assert "Chrome" in result.recovery_hints[0]


def test_phase_15_controlled_blocking_replan_required(mismatch_result_severe):
    # Controlled Blocking enabled: severe mismatch (0.92 >= 0.85) triggers REPLAN
    flags = IntegrationFeatureFlags(
        consistency_guard_enabled=True,
        controlled_blocking_enabled=True,
    )
    guard = ConsistencyGuard(feature_flags=flags, replan_probability_threshold=0.85)

    result = guard.evaluate(mismatch_result_severe)
    assert result.can_proceed is False
    assert result.status == GuardStatus.REPLAN_REQUIRED
    assert result.recommended_action == GuardAction.REPLAN


@pytest.mark.parametrize(
    ("probability", "expected_status", "expected_action"),
    [
        (0.8499, GuardStatus.MISMATCH, GuardAction.RECOVER),
        (0.8500, GuardStatus.REPLAN_REQUIRED, GuardAction.REPLAN),
        (0.8501, GuardStatus.REPLAN_REQUIRED, GuardAction.REPLAN),
    ],
)
def test_controlled_blocking_replan_threshold_boundary(
    mismatch_result_moderate,
    probability,
    expected_status,
    expected_action,
):
    """Verify recovery/replanning behavior around the exact threshold."""
    flags = IntegrationFeatureFlags(
        consistency_guard_enabled=True,
        warning_mode_enabled=False,
        controlled_blocking_enabled=True,
    )
    guard = ConsistencyGuard(
        feature_flags=flags,
        replan_probability_threshold=0.85,
    )

    result_data = mismatch_result_moderate.model_dump()
    result_data["probability"] = probability
    result_data["confidence"] = probability
    result = StateMismatchResult(**result_data)

    evaluation = guard.evaluate(result)

    assert evaluation.status == expected_status
    assert evaluation.recommended_action == expected_action
    assert evaluation.can_proceed is False


def test_controlled_blocking_takes_precedence_over_warning(
    mismatch_result_moderate,
):
    """When both modes are enabled, controlled blocking determines the action."""
    flags = IntegrationFeatureFlags(
        consistency_guard_enabled=True,
        warning_mode_enabled=True,
        controlled_blocking_enabled=True,
    )
    guard = ConsistencyGuard(
        feature_flags=flags,
        replan_probability_threshold=0.85,
    )

    result = guard.evaluate(mismatch_result_moderate)

    assert result.status == GuardStatus.MISMATCH
    assert result.recommended_action == GuardAction.RECOVER
    assert result.can_proceed is False
