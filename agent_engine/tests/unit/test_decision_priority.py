"""
===============================================================================
File Name   : test_decision_priority.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Phase D-7:
    Tests for deterministic Decision Priority.

The tests verify:

    1. Single decision selection.
    2. Retry beats failure.
    3. Fallback beats failure.
    4. Retry beats fallback.
    5. Complete beats retry.
    6. Skip beats retry.
    7. Abort beats every other decision.
    8. Selection is independent of input order.
    9. Equal-priority decisions preserve input order.
    10. Empty decision collections are rejected.
===============================================================================
"""

import pytest

from agent_engine.decision_manager.decision_priority import (
    DecisionPriorityPolicy,
)

from agent_engine.decision_manager.models.decision import (
    DecisionAction,
    DecisionResult,
)

from agent_engine.decision_manager.models.execution_outcome import (
    FailureType,
)


policy = DecisionPriorityPolicy()


def make_decision(
    action: DecisionAction,
    task_id: int = 1,
) -> DecisionResult:
    """
    Create a valid DecisionResult for priority testing.
    """

    return DecisionResult(
        action=action,
        task_id=task_id,
        reason=f"Test decision: {action.value}",
        attempt=1,
        max_retries=3,
        failure_type=FailureType.NONE,
    )


# =============================================================================
# Single decision
# =============================================================================


def test_single_decision_is_selected() -> None:

    decision = make_decision(
        DecisionAction.FAIL,
    )

    result = policy.select(
        [decision],
    )

    assert result is decision
    assert result.action == DecisionAction.FAIL


# =============================================================================
# Retry vs Fail
# =============================================================================


def test_retry_has_higher_priority_than_fail() -> None:

    retry = make_decision(
        DecisionAction.RETRY,
    )

    fail = make_decision(
        DecisionAction.FAIL,
    )

    result = policy.select(
        [fail, retry],
    )

    assert result is retry
    assert result.action == DecisionAction.RETRY


# =============================================================================
# Fallback vs Fail
# =============================================================================


def test_fallback_has_higher_priority_than_fail() -> None:

    fallback = make_decision(
        DecisionAction.FALLBACK,
    )

    fail = make_decision(
        DecisionAction.FAIL,
    )

    result = policy.select(
        [fail, fallback],
    )

    assert result is fallback
    assert result.action == DecisionAction.FALLBACK


# =============================================================================
# Retry vs Fallback
# =============================================================================


def test_retry_has_higher_priority_than_fallback() -> None:

    retry = make_decision(
        DecisionAction.RETRY,
    )

    fallback = make_decision(
        DecisionAction.FALLBACK,
    )

    result = policy.select(
        [fallback, retry],
    )

    assert result is retry
    assert result.action == DecisionAction.RETRY


# =============================================================================
# Complete vs Retry
# =============================================================================


def test_complete_has_higher_priority_than_retry() -> None:

    complete = make_decision(
        DecisionAction.COMPLETE,
    )

    retry = make_decision(
        DecisionAction.RETRY,
    )

    result = policy.select(
        [retry, complete],
    )

    assert result is complete
    assert result.action == DecisionAction.COMPLETE


# =============================================================================
# Skip vs Retry
# =============================================================================


def test_skip_has_higher_priority_than_retry() -> None:

    skip = make_decision(
        DecisionAction.SKIP,
    )

    retry = make_decision(
        DecisionAction.RETRY,
    )

    result = policy.select(
        [retry, skip],
    )

    assert result is skip
    assert result.action == DecisionAction.SKIP


# =============================================================================
# Abort vs every other decision
# =============================================================================


def test_abort_has_highest_priority() -> None:

    decisions = [
        make_decision(DecisionAction.FAIL, task_id=1),
        make_decision(DecisionAction.FALLBACK, task_id=2),
        make_decision(DecisionAction.RETRY, task_id=3),
        make_decision(DecisionAction.COMPLETE, task_id=4),
        make_decision(DecisionAction.SKIP, task_id=5),
        make_decision(DecisionAction.ABORT, task_id=6),
    ]

    result = policy.select(
        decisions,
    )

    assert result.action == DecisionAction.ABORT
    assert result.task_id == 6


# =============================================================================
# Input-order independence
# =============================================================================


def test_priority_selection_is_independent_of_input_order() -> None:

    fail = make_decision(
        DecisionAction.FAIL,
        task_id=1,
    )

    fallback = make_decision(
        DecisionAction.FALLBACK,
        task_id=2,
    )

    retry = make_decision(
        DecisionAction.RETRY,
        task_id=3,
    )

    result_1 = policy.select(
        [fail, fallback, retry],
    )

    result_2 = policy.select(
        [retry, fail, fallback],
    )

    result_3 = policy.select(
        [fallback, retry, fail],
    )

    assert result_1.action == DecisionAction.RETRY
    assert result_2.action == DecisionAction.RETRY
    assert result_3.action == DecisionAction.RETRY


# =============================================================================
# Equal priority
# =============================================================================


def test_equal_priority_preserves_input_order() -> None:

    retry_a = make_decision(
        DecisionAction.RETRY,
        task_id=10,
    )

    retry_b = make_decision(
        DecisionAction.RETRY,
        task_id=20,
    )

    result = policy.select(
        [retry_a, retry_b],
    )

    assert result is retry_a
    assert result.task_id == 10


# =============================================================================
# Empty candidates
# =============================================================================


def test_empty_decision_collection_raises_value_error() -> None:

    with pytest.raises(ValueError):

        policy.select([])