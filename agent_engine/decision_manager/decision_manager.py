"""
===============================================================================
File Name   : decision_manager.py
Module      : Decision Manager
Project     : JARVIS - Agent Decision Engine & Automation Engine

Phase D:
    D-1 - Retry Policy
    D-2 - Timeout Handling
    D-3 - Failure Strategy
    D-4 - Skip Policy
    D-5 - Fallback / Recovery
    D-6 - Unified DecisionResult
===============================================================================
"""

from collections.abc import Mapping, Sequence

from agent_engine.contracts.enums import ExecutionStatus
from agent_engine.contracts.task import Task

from agent_engine.decision_manager.failure_strategy import (
    FailureStrategy,
)

from agent_engine.decision_manager.fallback_policy import (
    FallbackPolicy,
)

from agent_engine.decision_manager.models.decision import (
    DecisionAction,
    DecisionResult,
)

from agent_engine.decision_manager.models.execution_outcome import (
    ExecutionOutcome,
    FailureType,
)

from agent_engine.decision_manager.models.fallback import (
    FallbackOption,
)

from agent_engine.decision_manager.retry_policy import (
    RetryPolicy,
)

from agent_engine.decision_manager.skip_policy import (
    SkipPolicy,
)

from agent_engine.decision_manager.timeout_policy import (
    TimeoutPolicy,
)
from agent_engine.decision_manager.decision_priority import (
    DecisionPriorityPolicy,
)


class DecisionManager:
    """
    Central decision-making component of the Agent Engine.

    The DecisionManager delegates decision-making to specialized policies
    while exposing a unified DecisionResult contract to the rest of the
    Agent Engine.
    """

    def __init__(
        self,
        retry_policy: RetryPolicy | None = None,
        timeout_policy: TimeoutPolicy | None = None,
        failure_strategy: FailureStrategy | None = None,
        skip_policy: SkipPolicy | None = None,
        fallback_policy: FallbackPolicy | None = None,
        decision_priority_policy: DecisionPriorityPolicy | None = None,
    ) -> None:

        self.retry_policy = retry_policy or RetryPolicy()

        self.timeout_policy = timeout_policy or TimeoutPolicy()

        self.failure_strategy = (
            failure_strategy or FailureStrategy()
        )

        self.skip_policy = skip_policy or SkipPolicy()

        self.fallback_policy = (
            fallback_policy or FallbackPolicy()
        )

        self.decision_priority_policy = (
            decision_priority_policy or DecisionPriorityPolicy()
        )

    def decide(
        self,
        outcome: ExecutionOutcome,
    ) -> DecisionResult:
        """
        Produce the next decision for an execution outcome.
        """

        # ---------------------------------------------------------------------
        # D-2: Normalize timeout information first.
        # ---------------------------------------------------------------------

        normalized_outcome = self.timeout_policy.normalize(
            outcome
        )

        # ---------------------------------------------------------------------
        # Successful execution.
        # ---------------------------------------------------------------------

        if normalized_outcome.success:
            return DecisionResult(
                action=DecisionAction.COMPLETE,
                task_id=normalized_outcome.task_id,
                reason="Task execution completed successfully.",
                attempt=normalized_outcome.attempt,
                max_retries=normalized_outcome.max_retries,
                failure_type=FailureType.NONE,
            )

        # ---------------------------------------------------------------------
        # D-1: Retryable failures.
        # ---------------------------------------------------------------------

        if normalized_outcome.failure_type in (
            FailureType.TRANSIENT,
            FailureType.TIMEOUT,
        ):
            return self.retry_policy.evaluate(
                normalized_outcome
            )

        # ---------------------------------------------------------------------
        # D-3: Non-retryable failures.
        # ---------------------------------------------------------------------

        return self.failure_strategy.evaluate(
            normalized_outcome
        )

    def evaluate_dependencies(
        self,
        task: Task,
        task_states: Mapping[int, ExecutionStatus],
        attempt: int = 1,
    ) -> DecisionResult:
        """
        Evaluate whether dependency state prevents task execution.

        This method is intentionally separate from `decide()` because
        dependency readiness is evaluated before the task itself executes.
        """

        return self.skip_policy.evaluate(
            task=task,
            task_states=task_states,
            attempt=attempt,
        )

    def evaluate_fallback(
        self,
        task: Task,
        fallback_options: Sequence[FallbackOption] | None = None,
        attempt: int = 1,
    ) -> DecisionResult:
        """
        Evaluate available recovery options for a task.

        The Decision Manager selects the recovery path but does not
        execute it.

        D-6:
            The method exposes the unified DecisionResult contract.
        """

        return self.fallback_policy.select_fallback(
            task=task,
            fallback_options=fallback_options,
            attempt=attempt,
        )

    def prioritize(
        self,
        decisions: Sequence[DecisionResult],
    ) -> DecisionResult:
        """
        Select the highest-priority decision from candidate decisions.

        D-7:
            Decision Priority.

        The Decision Manager delegates priority resolution to the
        DecisionPriorityPolicy.

        This method does not execute the selected decision or modify
        any task state.
        """

        return self.decision_priority_policy.select(
            decisions
        )