from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AgentExecutionContext:
    """
    Runtime context supplied to an automation agent during execution.

    The context describes the execution environment and runtime metadata
    surrounding an ActionRequest. It does not contain decision-making,
    retry, fallback, or state-management logic.
    """

    task_id: int
    attempt: int = 1
    timeout_seconds: float | None = None
    execution_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.task_id < 0:
            raise ValueError("task_id cannot be negative.")

        if self.attempt < 1:
            raise ValueError("attempt must be greater than or equal to 1.")

        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than 0.")

        if self.execution_id is not None:
            if not isinstance(self.execution_id, str):
                raise TypeError("execution_id must be a string or None.")

            if not self.execution_id.strip():
                raise ValueError("execution_id cannot be empty.")

        if not isinstance(self.metadata, dict):
            raise TypeError("metadata must be a dictionary.")