from __future__ import annotations


class AutomationException(Exception):
    """
    Base exception for all automation-layer failures.

    Every exception raised by an automation agent should ultimately
    derive from this class so that callers can handle automation
    failures consistently.
    """

    def __init__(
        self,
        message: str,
        *,
        task_id: int | None = None,
        agent_id: str | None = None,
    ) -> None:
        if not isinstance(message, str):
            raise TypeError("message must be a string.")

        if not message.strip():
            raise ValueError("message cannot be empty.")

        if task_id is not None and task_id < 0:
            raise ValueError("task_id cannot be negative.")

        if agent_id is not None:
            if not isinstance(agent_id, str):
                raise TypeError("agent_id must be a string or None.")

            if not agent_id.strip():
                raise ValueError("agent_id cannot be empty.")

        self.message = message
        self.task_id = task_id
        self.agent_id = agent_id

        super().__init__(message)

    def __str__(self) -> str:
        details = []

        if self.task_id is not None:
            details.append(f"task_id={self.task_id}")

        if self.agent_id is not None:
            details.append(f"agent_id={self.agent_id}")

        if details:
            return f"{self.message} ({', '.join(details)})"

        return self.message


class AgentInitializationError(AutomationException):
    """Raised when an automation agent cannot initialize."""


class AgentExecutionError(AutomationException):
    """Raised when an automation agent fails during action execution."""


class AgentCapabilityError(AutomationException):
    """Raised when an agent cannot perform the requested action."""


class AutomationTimeoutError(AutomationException):
    """Raised when an automation action exceeds its allowed timeout."""


class AutomationValidationError(AutomationException):
    """Raised when automation input or parameters are invalid."""


class AgentCleanupError(AutomationException):
    """Raised when an automation agent fails during cleanup."""