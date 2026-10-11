
"""Regression tests for Consistency Guard to Decision Manager mapping."""

from unittest.mock import Mock

import pytest

from agent_engine.decision_manager.models.decision import (
    DecisionAction,
)
from agent_engine.integration.guard.consistency_guard import (
    GuardAction,
    GuardEvaluationResult,
    GuardStatus,
)
from agent_engine.integration.workflow_state_service import (
    WorkflowStateIntegrationService,
)


@pytest.fixture
def service_with_mock_bridge():
    """Create the integration service with a mocked decision bridge."""
    bridge = Mock()
    service = WorkflowStateIntegrationService(
        decision_bridge=bridge,
    )
    return service, bridge


def make_guard_result(action: GuardAction) -> GuardEvaluationResult:
    """Build a minimal valid guard result for a requested action."""
    return GuardEvaluationResult(
        status=(
            GuardStatus.WARNING
            if action == GuardAction.WARN
            else GuardStatus.CONSISTENT
        ),
        recommended_action=action,
        can_proceed=action in (GuardAction.PROCEED, GuardAction.WARN),
        mismatch_detected=action != GuardAction.PROCEED,
        ml_probability=0.0,
        confidence=1.0,
        threshold=0.30,
        reason=f"Test guard action: {action.value}",
    )


@pytest.mark.parametrize(
    "guard_action",
    [
        GuardAction.PROCEED,
        GuardAction.WARN,
    ],
)
def test_proceed_and_warn_return_continue_without_bridge_call(
    service_with_mock_bridge,
    guard_action,
):
    """Allowed continuation must not mark the task completed."""
    service, bridge = service_with_mock_bridge
    guard_result = make_guard_result(guard_action)

    decision = service.apply_guard_decision(
        task_id=101,
        guard_result=guard_result,
    )

    assert decision.action == DecisionAction.CONTINUE
    assert decision.task_id == 101
    bridge.apply_decision.assert_not_called()


def test_recover_maps_to_retry_before_retry_limit(
    service_with_mock_bridge,
):
    service, bridge = service_with_mock_bridge

    decision = service.apply_guard_decision(
        task_id=102,
        guard_result=make_guard_result(GuardAction.RECOVER),
        attempt=1,
        max_retries=3,
    )

    assert decision.action == DecisionAction.RETRY
    bridge.apply_decision.assert_called_once_with(decision)


def test_recover_maps_to_fallback_at_retry_limit(
    service_with_mock_bridge,
):
    service, bridge = service_with_mock_bridge

    decision = service.apply_guard_decision(
        task_id=103,
        guard_result=make_guard_result(GuardAction.RECOVER),
        attempt=3,
        max_retries=3,
    )

    assert decision.action == DecisionAction.FALLBACK
    bridge.apply_decision.assert_called_once_with(decision)


@pytest.mark.parametrize(
    "guard_action",
    [
        GuardAction.REPLAN,
        GuardAction.BLOCK,
    ],
)
def test_replan_and_block_map_to_fail(
    service_with_mock_bridge,
    guard_action,
):
    service, bridge = service_with_mock_bridge

    decision = service.apply_guard_decision(
        task_id=104,
        guard_result=make_guard_result(guard_action),
    )

    assert decision.action == DecisionAction.FAIL
    bridge.apply_decision.assert_called_once_with(decision)


def test_bridge_exception_does_not_prevent_decision_return(
    service_with_mock_bridge,
):
    service, bridge = service_with_mock_bridge
    bridge.apply_decision.side_effect = RuntimeError("bridge unavailable")

    decision = service.apply_guard_decision(
        task_id=105,
        guard_result=make_guard_result(GuardAction.RECOVER),
        attempt=1,
        max_retries=3,
    )

    assert decision.action == DecisionAction.RETRY
    assert decision.task_id == 105
    bridge.apply_decision.assert_called_once_with(decision)