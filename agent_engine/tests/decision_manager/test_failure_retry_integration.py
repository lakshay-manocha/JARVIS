"""
===============================================================================
File Name   : test_failure_retry_integration.py
Module      : Decision Manager Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Phase F:
    F.2 - Retry Policy Integration

Verifies the integration:

    Exception
        ↓
    FailureHandler
        ↓
    ExecutionOutcome
        ↓
    DecisionManager
        ↓
    RetryPolicy
        ↓
    DecisionResult
===============================================================================
"""

from agent_engine.decision_manager.decision_manager import (
    DecisionManager,
)

from agent_engine.decision_manager.failure_handler import (
    FailureHandler,
)

from agent_engine.decision_manager.models.decision import (
    DecisionAction,
)

from agent_engine.decision_manager.models.execution_outcome import (
    FailureType,
)


def test_transient_failure_reaches_retry_policy() -> None:
    """
    A retryable TRANSIENT ExecutionOutcome should result in RETRY.
    """

    handler = FailureHandler()
    manager = DecisionManager()

    outcome = handler.handle_exception(
        task_id=1,
        exception=RuntimeError("Temporary automation failure"),
        attempt=1,
        retry_count=0,
        max_retries=2,
    )

    # F.1 produces UNKNOWN for generic exceptions by design.
    # Therefore explicitly classify this execution failure as transient
    # before passing it to the DecisionManager.
    outcome.failure_type = FailureType.TRANSIENT

    decision = manager.decide(outcome)

    assert decision.action == DecisionAction.RETRY
    assert decision.task_id == 1
    assert decision.attempt == 1
    assert decision.max_retries == 2
    assert decision.failure_type == FailureType.TRANSIENT


def test_timeout_failure_reaches_retry_policy() -> None:
    """
    A timeout normalized by FailureHandler should result in RETRY when
    retries are available.
    """

    handler = FailureHandler()
    manager = DecisionManager()

    outcome = handler.handle_exception(
        task_id=2,
        exception=TimeoutError("Automation timed out"),
        attempt=1,
        retry_count=0,
        max_retries=2,
        timeout_seconds=10.0,
        execution_time=11.5,
    )

    decision = manager.decide(outcome)

    assert outcome.failure_type == FailureType.TIMEOUT
    assert outcome.timed_out is True

    assert decision.action == DecisionAction.RETRY
    assert decision.task_id == 2
    assert decision.failure_type == FailureType.TIMEOUT


def test_retry_exhaustion_reaches_fail_decision() -> None:
    """
    A retryable failure with retry_count == max_retries must result in FAIL.
    """

    handler = FailureHandler()
    manager = DecisionManager()

    outcome = handler.handle_exception(
        task_id=3,
        exception=TimeoutError("Automation timed out again"),
        attempt=3,
        retry_count=2,
        max_retries=2,
        timeout_seconds=10.0,
        execution_time=12.0,
    )

    decision = manager.decide(outcome)

    assert outcome.failure_type == FailureType.TIMEOUT
    assert decision.action == DecisionAction.FAIL
    assert decision.task_id == 3
    assert decision.failure_type == FailureType.TIMEOUT


def test_non_retryable_failure_reaches_fail_decision() -> None:
    """
    A permanent failure must bypass retry and produce FAIL.
    """

    handler = FailureHandler()
    manager = DecisionManager()

    outcome = handler.handle_exception(
        task_id=4,
        exception=RuntimeError("Permanent automation failure"),
        attempt=1,
        retry_count=0,
        max_retries=3,
    )

    outcome.failure_type = FailureType.PERMANENT

    decision = manager.decide(outcome)

    assert decision.action == DecisionAction.FAIL
    assert decision.task_id == 4
    assert decision.failure_type == FailureType.PERMANENT


def test_retry_metadata_is_preserved() -> None:
    """
    FailureHandler must preserve retry metadata so RetryPolicy can make
    the correct decision.
    """

    handler = FailureHandler()

    outcome = handler.handle_exception(
        task_id=5,
        exception=TimeoutError("Temporary timeout"),
        attempt=2,
        retry_count=1,
        max_retries=3,
    )

    assert outcome.attempt == 2
    assert outcome.retry_count == 1
    assert outcome.max_retries == 3
    assert outcome.failure_type == FailureType.TIMEOUT