import pytest

from agent_engine.automation.models.lifecycle import (
    AgentLifecycleState,
    VALID_LIFECYCLE_TRANSITIONS,
    can_transition,
)


def test_lifecycle_states_exist() -> None:
    assert AgentLifecycleState.CREATED.value == "created"
    assert AgentLifecycleState.INITIALIZING.value == "initializing"
    assert AgentLifecycleState.READY.value == "ready"
    assert AgentLifecycleState.EXECUTING.value == "executing"
    assert AgentLifecycleState.CLEANING_UP.value == "cleaning_up"
    assert AgentLifecycleState.CLEANED.value == "cleaned"
    assert AgentLifecycleState.FAILED.value == "failed"


def test_created_can_initialize() -> None:
    assert can_transition(
        AgentLifecycleState.CREATED,
        AgentLifecycleState.INITIALIZING,
    )


def test_initializing_can_become_ready() -> None:
    assert can_transition(
        AgentLifecycleState.INITIALIZING,
        AgentLifecycleState.READY,
    )


def test_initializing_can_fail() -> None:
    assert can_transition(
        AgentLifecycleState.INITIALIZING,
        AgentLifecycleState.FAILED,
    )


def test_ready_can_execute() -> None:
    assert can_transition(
        AgentLifecycleState.READY,
        AgentLifecycleState.EXECUTING,
    )


def test_execution_returns_to_ready() -> None:
    assert can_transition(
        AgentLifecycleState.EXECUTING,
        AgentLifecycleState.READY,
    )


def test_ready_can_cleanup() -> None:
    assert can_transition(
        AgentLifecycleState.READY,
        AgentLifecycleState.CLEANING_UP,
    )


def test_cleanup_can_complete() -> None:
    assert can_transition(
        AgentLifecycleState.CLEANING_UP,
        AgentLifecycleState.CLEANED,
    )


def test_failed_agent_can_cleanup() -> None:
    assert can_transition(
        AgentLifecycleState.FAILED,
        AgentLifecycleState.CLEANING_UP,
    )


def test_cleaned_is_terminal() -> None:
    assert VALID_LIFECYCLE_TRANSITIONS[
        AgentLifecycleState.CLEANED
    ] == frozenset()


def test_invalid_created_to_execute_transition() -> None:
    assert not can_transition(
        AgentLifecycleState.CREATED,
        AgentLifecycleState.EXECUTING,
    )


def test_invalid_created_to_ready_transition() -> None:
    assert not can_transition(
        AgentLifecycleState.CREATED,
        AgentLifecycleState.READY,
    )


def test_invalid_ready_to_created_transition() -> None:
    assert not can_transition(
        AgentLifecycleState.READY,
        AgentLifecycleState.CREATED,
    )


def test_invalid_cleaned_to_ready_transition() -> None:
    assert not can_transition(
        AgentLifecycleState.CLEANED,
        AgentLifecycleState.READY,
    )


def test_invalid_cleaned_to_execute_transition() -> None:
    assert not can_transition(
        AgentLifecycleState.CLEANED,
        AgentLifecycleState.EXECUTING,
    )