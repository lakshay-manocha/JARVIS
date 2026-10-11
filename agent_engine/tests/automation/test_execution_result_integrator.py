"""
===============================================================================
File Name   : test_execution_result_integrator.py
Module      : Automation Engine - Integration Tests
Project     : JARVIS

Description:
-------------
Tests M5-G.11 conversion from AutomationExecutionResult to ExecutionOutcome.

Author : Team Automation
===============================================================================
"""

import pytest

from agent_engine.automation.integration.execution_result_integrator import (
    ExecutionResultIntegrator,
)
from agent_engine.automation.models.execution_result import (
    AutomationExecutionResult,
)
from agent_engine.contracts.enums import (
    ExecutionStatus,
)
from agent_engine.decision_manager.models.execution_outcome import (
    FailureType,
)


# =============================================================================
# Helpers
# =============================================================================

def create_integrator():
    return ExecutionResultIntegrator()


# =============================================================================
# Successful Result
# =============================================================================

def test_successful_result_converts_to_completed_outcome():
    """
    Successful AutomationExecutionResult should become COMPLETED.
    """

    integrator = create_integrator()

    result = AutomationExecutionResult(
        task_id=1,
        action="open_url",
        success=True,
        output="Page opened",
        execution_time=0.25,
    )

    outcome = integrator.integrate(
        result,
        attempt=1,
    )

    assert outcome.task_id == 1
    assert outcome.status == ExecutionStatus.COMPLETED
    assert outcome.success is True
    assert outcome.attempt == 1
    assert outcome.retry_count == 0
    assert outcome.failure_type == FailureType.NONE
    assert outcome.error_message is None
    assert outcome.execution_time == 0.25


# =============================================================================
# Failed Result
# =============================================================================

def test_failed_result_converts_to_failed_outcome():
    """
    Failed AutomationExecutionResult should become FAILED.
    """

    integrator = create_integrator()

    result = AutomationExecutionResult(
        task_id=2,
        action="open_url",
        success=False,
        error="Browser could not open the page.",
        execution_time=0.50,
    )

    outcome = integrator.integrate(
        result,
        attempt=1,
    )

    assert outcome.task_id == 2
    assert outcome.status == ExecutionStatus.FAILED
    assert outcome.success is False
    assert outcome.failure_type == FailureType.UNKNOWN
    assert outcome.error_message == (
        "Browser could not open the page."
    )


# =============================================================================
# Attempt Information
# =============================================================================

def test_attempt_information_is_preserved():
    """
    Attempt number should determine retry_count.
    """

    integrator = create_integrator()

    result = AutomationExecutionResult(
        task_id=3,
        action="click",
        success=True,
    )

    outcome = integrator.integrate(
        result,
        attempt=4,
        max_retries=5,
    )

    assert outcome.attempt == 4
    assert outcome.retry_count == 3
    assert outcome.max_retries == 5


# =============================================================================
# Timeout Information
# =============================================================================

def test_timeout_information_is_preserved():
    """
    Configured timeout should be transferred to ExecutionOutcome.
    """

    integrator = create_integrator()

    result = AutomationExecutionResult(
        task_id=4,
        action="search",
        success=True,
        execution_time=1.2,
    )

    outcome = integrator.integrate(
        result,
        attempt=1,
        timeout_seconds=30,
    )

    assert outcome.timeout_seconds == 30
    assert outcome.execution_time == 1.2
    assert outcome.timed_out is False


# =============================================================================
# Explicit Timeout Failure
# =============================================================================

def test_timeout_failure_is_classified_as_timeout():
    """
    Automation agents can explicitly report timeout information through
    result metadata.
    """

    integrator = create_integrator()

    result = AutomationExecutionResult(
        task_id=5,
        action="open_url",
        success=False,
        error="Operation timed out.",
        execution_time=30.1,
        metadata={
            "timed_out": True,
        },
    )

    outcome = integrator.integrate(
        result,
        attempt=1,
        timeout_seconds=30,
    )

    assert outcome.status == ExecutionStatus.FAILED
    assert outcome.success is False
    assert outcome.timed_out is True
    assert outcome.failure_type == FailureType.TIMEOUT
    assert outcome.error_message == "Operation timed out."


# =============================================================================
# Explicit Failure Type
# =============================================================================

def test_explicit_failure_type_is_preserved():
    """
    Automation agents may provide an explicit FailureType through metadata.
    """

    integrator = create_integrator()

    result = AutomationExecutionResult(
        task_id=6,
        action="delete",
        success=False,
        error="Permission denied.",
        metadata={
            "failure_type": FailureType.PERMANENT,
        },
    )

    outcome = integrator.integrate(
        result,
        attempt=1,
    )

    assert outcome.failure_type == FailureType.PERMANENT


# =============================================================================
# String Failure Type
# =============================================================================

def test_string_failure_type_is_normalized():
    """
    String failure types should be converted to FailureType.
    """

    integrator = create_integrator()

    result = AutomationExecutionResult(
        task_id=7,
        action="download",
        success=False,
        error="Network unavailable.",
        metadata={
            "failure_type": "TRANSIENT",
        },
    )

    outcome = integrator.integrate(
        result,
        attempt=2,
    )

    assert outcome.failure_type == FailureType.TRANSIENT


# =============================================================================
# Unknown Failure Type
# =============================================================================

def test_unknown_failure_type_falls_back_to_unknown():
    """
    Unsupported failure classification should become UNKNOWN.
    """

    integrator = create_integrator()

    result = AutomationExecutionResult(
        task_id=8,
        action="open",
        success=False,
        error="Unexpected automation error.",
        metadata={
            "failure_type": "SOMETHING_NEW",
        },
    )

    outcome = integrator.integrate(
        result,
        attempt=1,
    )

    assert outcome.failure_type == FailureType.UNKNOWN


# =============================================================================
# Invalid Input
# =============================================================================

def test_invalid_result_is_rejected():
    """
    Only AutomationExecutionResult objects are accepted.
    """

    integrator = create_integrator()

    with pytest.raises(TypeError):
        integrator.integrate(
            "invalid result",
            attempt=1,
        )


# =============================================================================
# Invalid Attempt
# =============================================================================

def test_invalid_attempt_is_rejected():
    """
    Attempt numbers must be one-based.
    """

    integrator = create_integrator()

    result = AutomationExecutionResult(
        task_id=9,
        action="click",
        success=True,
    )

    with pytest.raises(ValueError):
        integrator.integrate(
            result,
            attempt=0,
        )


# =============================================================================
# Invalid Retry Configuration
# =============================================================================

def test_negative_max_retries_is_rejected():
    """
    max_retries cannot be negative.
    """

    integrator = create_integrator()

    result = AutomationExecutionResult(
        task_id=10,
        action="click",
        success=True,
    )

    with pytest.raises(ValueError):
        integrator.integrate(
            result,
            attempt=1,
            max_retries=-1,
        )