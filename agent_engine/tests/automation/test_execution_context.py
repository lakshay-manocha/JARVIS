import pytest

from agent_engine.automation.models.execution_context import AgentExecutionContext


def test_execution_context_defaults() -> None:
    context = AgentExecutionContext(task_id=1)

    assert context.task_id == 1
    assert context.attempt == 1
    assert context.timeout_seconds is None
    assert context.execution_id is None
    assert context.metadata == {}


def test_execution_context_accepts_valid_values() -> None:
    context = AgentExecutionContext(
        task_id=10,
        attempt=2,
        timeout_seconds=30.0,
        execution_id="exec-001",
        metadata={
            "source": "agent_orchestrator",
            "mode": "sequential",
        },
    )

    assert context.task_id == 10
    assert context.attempt == 2
    assert context.timeout_seconds == 30.0
    assert context.execution_id == "exec-001"
    assert context.metadata["source"] == "agent_orchestrator"


def test_task_id_cannot_be_negative() -> None:
    with pytest.raises(ValueError, match="task_id cannot be negative"):
        AgentExecutionContext(task_id=-1)


def test_attempt_must_be_positive() -> None:
    with pytest.raises(ValueError, match="attempt must be greater than or equal to 1"):
        AgentExecutionContext(
            task_id=1,
            attempt=0,
        )


def test_timeout_must_be_positive() -> None:
    with pytest.raises(ValueError, match="timeout_seconds must be greater than 0"):
        AgentExecutionContext(
            task_id=1,
            timeout_seconds=0,
        )


def test_execution_id_cannot_be_empty() -> None:
    with pytest.raises(ValueError, match="execution_id cannot be empty"):
        AgentExecutionContext(
            task_id=1,
            execution_id="   ",
        )


def test_context_is_immutable() -> None:
    context = AgentExecutionContext(
        task_id=1,
        attempt=1,
    )

    with pytest.raises(AttributeError):
        context.attempt = 2


def test_metadata_defaults_are_independent() -> None:
    context_one = AgentExecutionContext(task_id=1)
    context_two = AgentExecutionContext(task_id=2)

    context_one.metadata["test"] = "value"

    assert "test" not in context_two.metadata