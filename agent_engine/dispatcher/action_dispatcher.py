"""Phase F-3: Action Dispatcher contract.

The dispatcher is the execution boundary between the Agent Engine and the
future Automation Engine/controllers.  It executes one already-planned task
and returns a normalized :class:`ExecutionOutcome`.

The dispatcher owns *how* an action is executed.  It does not decide retry,
fallback, skip, or final task state; those responsibilities remain with the
Decision Manager and State Manager.
"""

from __future__ import annotations

from typing import Protocol

from agent_engine.agent_brain.models.interpreted_task import InterpretedTask
from agent_engine.decision_manager.models.execution_outcome import ExecutionOutcome


class ActionDispatcher(Protocol):
    """Interface implemented by the Automation Engine execution layer."""

    def dispatch(
        self,
        task: InterpretedTask,
        *,
        attempt: int,
        timeout_seconds: float | None = None,
    ) -> ExecutionOutcome:
        """Execute one task attempt and return its normalized outcome.

        Implementations must not mutate Agent Engine state.  They may raise
        an exception when execution cannot produce an outcome; the
        orchestrator converts that exception into a failed outcome.
        """
        ...
