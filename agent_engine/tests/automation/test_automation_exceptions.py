import pytest

from agent_engine.automation.exceptions import (
    AgentCapabilityError,
    AgentCleanupError,
    AgentExecutionError,
    AgentInitializationError,
    AutomationException,
    AutomationTimeoutError,
    AutomationValidationError,
)


def test_base_exception() -> None:
    error = AutomationException("Automation failed.")

    assert error.message == "Automation failed."
    assert error.task_id is None
    assert error.agent_id is None
    assert str(error) == "Automation failed."


def test_exception_context() -> None:
    error = AutomationException(
        "Browser execution failed.",
        task_id=10,
        agent_id="browser_agent",
    )

    assert error.message == "Browser execution failed."
    assert error.task_id == 10
    assert error.agent_id == "browser_agent"

    assert "Browser execution failed." in str(error)
    assert "task_id=10" in str(error)
    assert "agent_id=browser_agent" in str(error)


def test_specialized_exceptions_inherit_from_base() -> None:
    exceptions = [
        AgentInitializationError("Initialization failed."),
        AgentExecutionError("Execution failed."),
        AgentCapabilityError("Unsupported action."),
        AutomationTimeoutError("Execution timed out."),
        AutomationValidationError("Invalid parameters."),
        AgentCleanupError("Cleanup failed."),
    ]

    for error in exceptions:
        assert isinstance(error, AutomationException)
        assert isinstance(error, Exception)


def test_initialization_error() -> None:
    error = AgentInitializationError(
        "Browser could not be initialized.",
        agent_id="browser_agent",
    )

    assert isinstance(error, AutomationException)
    assert error.agent_id == "browser_agent"


def test_execution_error() -> None:
    error = AgentExecutionError(
        "Action execution failed.",
        task_id=5,
    )

    assert isinstance(error, AutomationException)
    assert error.task_id == 5


def test_capability_error() -> None:
    error = AgentCapabilityError(
        "Agent does not support click.",
        task_id=2,
        agent_id="keyboard_agent",
    )

    assert isinstance(error, AutomationException)
    assert error.task_id == 2
    assert error.agent_id == "keyboard_agent"


def test_timeout_error() -> None:
    error = AutomationTimeoutError(
        "Action exceeded timeout.",
        task_id=7,
    )

    assert isinstance(error, AutomationException)
    assert error.task_id == 7


def test_validation_error() -> None:
    error = AutomationValidationError(
        "Invalid action parameters.",
        task_id=3,
    )

    assert isinstance(error, AutomationException)
    assert error.task_id == 3


def test_cleanup_error() -> None:
    error = AgentCleanupError(
        "Agent cleanup failed.",
        agent_id="desktop_agent",
    )

    assert isinstance(error, AutomationException)
    assert error.agent_id == "desktop_agent"


def test_message_must_be_string() -> None:
    with pytest.raises(TypeError, match="message must be a string"):
        AutomationException(123)  # type: ignore[arg-type]


def test_message_cannot_be_empty() -> None:
    with pytest.raises(ValueError, match="message cannot be empty"):
        AutomationException("   ")


def test_task_id_cannot_be_negative() -> None:
    with pytest.raises(ValueError, match="task_id cannot be negative"):
        AutomationException(
            "Failure",
            task_id=-1,
        )


def test_agent_id_cannot_be_empty() -> None:
    with pytest.raises(ValueError, match="agent_id cannot be empty"):
        AutomationException(
            "Failure",
            agent_id="   ",
        )


def test_agent_id_must_be_string() -> None:
    with pytest.raises(TypeError, match="agent_id must be a string"):
        AutomationException(
            "Failure",
            agent_id=123,  # type: ignore[arg-type]
        )