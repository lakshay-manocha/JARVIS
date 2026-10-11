"""
===============================================================================
File Name   : test_f7_agent_orchestrator_integration.py
Module      : Integration Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Phase F.7 integration tests for AgentOrchestrator.

These tests verify that AgentOrchestrator correctly coordinates:

    Validation
        ↓
    Interpretation
        ↓
    Intent Detection
        ↓
    Action Resolution
        ↓
    Parameter Resolution
        ↓
    Tool Resolution
        ↓
    Graph Construction
        ↓
    Planning
        ↓
    State Management
        ↓
    Action Dispatch
        ↓
    Failure Handling
        ↓
    Decision Management
        ↓
    Decision-State Bridge

The tests use controlled dispatchers so that orchestration behavior can be
tested without depending on real browser, desktop, or system automation.

Author : Team JARVIS
===============================================================================
"""

from __future__ import annotations

from agent_engine.contracts.enums import (
    ExecutionMode,
    ExecutionStatus,
    ResultStatus,
)
from agent_engine.decision_manager.models.decision import (
    DecisionAction,
)
from agent_engine.decision_manager.models.execution_outcome import (
    ExecutionOutcome,
    FailureType,
)
from agent_engine.orchestration.agent_orchestrator import (
    AgentOrchestrator,
)


# =============================================================================
# Test Data
# =============================================================================


def build_plan():
    """
    Build a minimal valid LLM plan suitable for orchestrator integration
    testing.
    """

    return {
        "goal": "Execute browser tasks",
        "summary": "Open the requested website and perform the requested action.",
        "missing_information": [],
        "tasks": [
            "Open https://example.com",
            "Search for artificial intelligence",
        ],
    }


def build_single_task_plan():
    """
    Build a minimal single-task plan.
    """

    return {
        "goal": "Open a website",
        "summary": "Open the requested website.",
        "missing_information": [],
        "tasks": [
            "Open https://example.com",
        ],
    }


def success(task_id: int) -> ExecutionOutcome:
    """
    Construct a successful dispatcher outcome.
    """

    return ExecutionOutcome(
        task_id=task_id,
        status=ExecutionStatus.COMPLETED,
        success=True,
        attempt=1,
        retry_count=0,
        max_retries=0,
        timeout_seconds=60.0,
        execution_time=0.01,
        timed_out=False,
        failure_type=FailureType.NONE,
        error_message=None,
    )


def success_for_attempt(
    task_id: int,
    attempt: int,
) -> ExecutionOutcome:
    """
    Construct a successful outcome for a specific attempt.
    """

    return ExecutionOutcome(
        task_id=task_id,
        status=ExecutionStatus.COMPLETED,
        success=True,
        attempt=attempt,
        retry_count=max(attempt - 1, 0),
        max_retries=1,
        timeout_seconds=60.0,
        execution_time=0.01,
        timed_out=False,
        failure_type=FailureType.NONE,
        error_message=None,
    )


# =============================================================================
# F.7.1 — Complete Successful Orchestration
# =============================================================================


def test_f7_complete_successful_orchestration():
    """
    Verify that AgentOrchestrator can execute a complete request successfully.

    Expected:

        ResultStatus.SUCCESS
        all tasks COMPLETED
        decisions contain COMPLETE
    """

    class SuccessfulDispatcher:

        def dispatch(
            self,
            task,
            *,
            attempt,
            timeout_seconds=None,
        ):
            return success(task.task_id)

    orchestrator = AgentOrchestrator(
        SuccessfulDispatcher(),
        execution_mode=ExecutionMode.SEQUENTIAL,
        timeout_seconds=60.0,
        max_retries=0,
    )

    result = orchestrator.run(build_plan())

    assert result.status == ResultStatus.SUCCESS

    assert len(result.outcomes) == 2
    assert len(result.decisions) == 2

    assert all(
        outcome.success
        for outcome in result.outcomes
    )

    assert all(
        decision.action == DecisionAction.COMPLETE
        for decision in result.decisions
    )

    for task_id in result.planning_result.execution_order:
        assert (
            orchestrator.state_manager.get_status(task_id)
            == ExecutionStatus.COMPLETED
        )


# =============================================================================
# F.7.2 — Retry Coordination
# =============================================================================


def test_f7_orchestrator_coordinates_retry():
    """
    Verify that AgentOrchestrator correctly coordinates:

        Dispatcher failure
            ↓
        FailureHandler
            ↓
        DecisionManager
            ↓
        RETRY
            ↓
        second execution
            ↓
        SUCCESS
    """

    class FailureThenSuccessDispatcher:

        def __init__(self):
            self.calls = []

        def dispatch(
            self,
            task,
            *,
            attempt,
            timeout_seconds=None,
        ):
            self.calls.append(
                (task.task_id, attempt)
            )

            if (
                task.task_id == 1
                and attempt == 1
            ):
                raise TimeoutError(
                    "temporary controller timeout"
                )

            return success_for_attempt(
                task.task_id,
                attempt,
            )

    dispatcher = FailureThenSuccessDispatcher()

    orchestrator = AgentOrchestrator(
        dispatcher,
        max_retries=1,
        timeout_seconds=60.0,
    )

    result = orchestrator.run(
        build_single_task_plan()
    )

    assert result.status == ResultStatus.SUCCESS

    assert dispatcher.calls == [
        (1, 1),
        (1, 2),
    ]

    assert len(result.outcomes) == 2
    assert len(result.decisions) == 2

    assert (
        result.decisions[0].action
        == DecisionAction.RETRY
    )

    assert (
        result.decisions[1].action
        == DecisionAction.COMPLETE
    )

    assert (
        orchestrator.state_manager.get_status(1)
        == ExecutionStatus.COMPLETED
    )


# =============================================================================
# F.7.3 — Permanent Failure Coordination
# =============================================================================


def test_f7_permanent_failure_reaches_failed_state():
    """
    Verify that a permanent dispatcher failure is converted into:

        FAILED outcome
            ↓
        FAIL decision
            ↓
        FAILED runtime state
            ↓
        FAILED orchestration result
    """

    class PermanentFailureDispatcher:

        def dispatch(
            self,
            task,
            *,
            attempt,
            timeout_seconds=None,
        ):
            return ExecutionOutcome(
                task_id=task.task_id,
                status=ExecutionStatus.FAILED,
                success=False,
                attempt=attempt,
                retry_count=attempt - 1,
                max_retries=0,
                timeout_seconds=60.0,
                execution_time=0.01,
                timed_out=False,
                failure_type=FailureType.PERMANENT,
                error_message="Permanent automation failure",
            )

    orchestrator = AgentOrchestrator(
        PermanentFailureDispatcher(),
        max_retries=0,
    )

    result = orchestrator.run(
        build_single_task_plan()
    )

    assert result.status == ResultStatus.FAILED

    assert len(result.outcomes) == 1
    assert len(result.decisions) == 1

    assert (
        result.outcomes[0].success is False
    )

    assert (
        result.outcomes[0].failure_type
        == FailureType.PERMANENT
    )

    assert (
        result.decisions[0].action
        == DecisionAction.FAIL
    )

    assert (
        orchestrator.state_manager.get_status(1)
        == ExecutionStatus.FAILED
    )


# =============================================================================
# F.7.4 — Dispatcher Exception Containment
# =============================================================================


def test_f7_dispatcher_exception_is_converted_to_failure_outcome():
    """
    Verify that an exception raised by the dispatcher does not escape from
    _execute_task().

    AgentOrchestrator must route the exception through FailureHandler.
    """

    class ExplodingDispatcher:

        def dispatch(
            self,
            task,
            *,
            attempt,
            timeout_seconds=None,
        ):
            raise RuntimeError(
                "automation controller unavailable"
            )

    orchestrator = AgentOrchestrator(
        ExplodingDispatcher(),
        max_retries=0,
    )

    result = orchestrator.run(
        build_single_task_plan()
    )

    assert result.status == ResultStatus.FAILED

    assert len(result.outcomes) == 1
    assert len(result.decisions) == 1

    outcome = result.outcomes[0]

    assert outcome.success is False
    assert outcome.failure_type == FailureType.UNKNOWN
    assert (
        "automation controller unavailable"
        in outcome.error_message
    )

    assert (
        result.decisions[0].action
        == DecisionAction.FAIL
    )

    assert (
        orchestrator.state_manager.get_status(1)
        == ExecutionStatus.FAILED
    )


# =============================================================================
# F.7.5 — Dependency-Aware Orchestration
# =============================================================================


def test_f7_failed_parent_causes_dependent_task_to_skip():
    """
    Verify complete dependency-aware orchestration.

    Task 1:
        FAIL

    Task 2:
        depends on Task 1
        ↓
        SKIP
    """

    class FailingFirstDispatcher:

        def dispatch(
            self,
            task,
            *,
            attempt,
            timeout_seconds=None,
        ):
            if task.task_id == 1:
                return ExecutionOutcome(
                    task_id=1,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    attempt=attempt,
                    retry_count=attempt - 1,
                    max_retries=0,
                    timeout_seconds=60.0,
                    execution_time=0.01,
                    timed_out=False,
                    failure_type=FailureType.PERMANENT,
                    error_message="Parent task failed",
                )

            return success(task.task_id)

    # -------------------------------------------------------------------------
    # Inject an explicit dependency into the graph after the normal graph
    # construction stage.
    # -------------------------------------------------------------------------

    class DependencyGraphBuilder:

        def __init__(self):
            from agent_engine.agent_brain.graph_builder import (
                GraphBuilder,
            )

            self.inner = GraphBuilder()

        def build(self, context):

            context = self.inner.build(context)

            graph = context.execution_graph

            graph.add_dependency(
                parent_id=1,
                child_id=2,
                dependency_type="EXPLICIT",
                confidence=1.0,
                reason="Task 2 depends on Task 1",
            )

            graph.recalculate_roots_and_leaves()

            from agent_engine.agent_brain.graph_validator import (
                GraphValidator,
            )

            context.graph_validation_result = (
                GraphValidator().validate(graph)
            )

            return context

    orchestrator = AgentOrchestrator(
        FailingFirstDispatcher(),
        graph_builder=DependencyGraphBuilder(),
        max_retries=0,
    )

    result = orchestrator.run(
        build_plan()
    )

    assert result.status == ResultStatus.FAILED

    assert (
        orchestrator.state_manager.get_status(1)
        == ExecutionStatus.FAILED
    )

    assert (
        orchestrator.state_manager.get_status(2)
        == ExecutionStatus.SKIPPED
    )

    assert any(
        decision.action == DecisionAction.FAIL
        for decision in result.decisions
    )

    assert any(
        decision.action == DecisionAction.SKIP
        for decision in result.decisions
    )


# =============================================================================
# F.7.6 — Fallback Coordination
# =============================================================================


def test_f7_orchestrator_selects_fallback_after_failure():
    """
    Verify:

        normal execution
              ↓
            FAIL
              ↓
        fallback evaluation
              ↓
          FALLBACK
              ↓
        task returns to RUNNING

    The fallback itself must NOT execute.
    """

    from agent_engine.decision_manager.models.fallback import (
        FallbackOption,
    )

    class FailingDispatcher:

        def __init__(self):
            self.calls = []

        def dispatch(
            self,
            task,
            *,
            attempt,
            timeout_seconds=None,
        ):
            self.calls.append(
                task.task_id
            )

            return ExecutionOutcome(
                task_id=task.task_id,
                status=ExecutionStatus.FAILED,
                success=False,
                attempt=attempt,
                retry_count=attempt - 1,
                max_retries=0,
                timeout_seconds=60.0,
                execution_time=0.01,
                timed_out=False,
                failure_type=FailureType.PERMANENT,
                error_message="Primary automation failed",
            )

    dispatcher = FailingDispatcher()

    fallback = FallbackOption(
        id="fallback_browser",
        action="open",
        tool="browser",
        parameters={
            "url": "https://example.com"
        },
        priority=1,
        description="Use browser fallback",
    )

    orchestrator = AgentOrchestrator(
        dispatcher,
        fallback_options={
            1: [fallback]
        },
        max_retries=0,
    )

    result = orchestrator.run(
        build_single_task_plan()
    )

    assert result.status == ResultStatus.FAILED

    assert len(dispatcher.calls) == 1

    assert (
        result.decisions[0].action
        == DecisionAction.FALLBACK
    )

    assert (
        result.decisions[0].selected_fallback.id
        == "fallback_browser"
    )

    assert (
        orchestrator.state_manager.get_status(1)
        == ExecutionStatus.RUNNING
    )


# =============================================================================
# F.7.7 — State History Consistency
# =============================================================================


def test_f7_successful_task_has_consistent_state_history():
    """
    Verify that the StateManager records the lifecycle coordinated by the
    orchestrator.
    """

    class SuccessfulDispatcher:

        def dispatch(
            self,
            task,
            *,
            attempt,
            timeout_seconds=None,
        ):
            return success(task.task_id)

    orchestrator = AgentOrchestrator(
        SuccessfulDispatcher(),
        max_retries=0,
    )

    result = orchestrator.run(
        build_single_task_plan()
    )

    assert result.status == ResultStatus.SUCCESS

    history = (
        orchestrator.state_manager.get_history(1)
    )

    statuses = [
        entry.to_status
        for entry in history
    ]

    assert statuses == [
        ExecutionStatus.PENDING,
        ExecutionStatus.READY,
        ExecutionStatus.RUNNING,
        ExecutionStatus.COMPLETED,
    ]


# =============================================================================
# F.7.8 — Parallel Orchestration
# =============================================================================


def test_f7_parallel_execution_completes_all_tasks():
    """
    Verify that AgentOrchestrator can execute tasks belonging to the same
    parallel group concurrently and still produce a consistent final result.
    """

    class ParallelDispatcher:

        def __init__(self):
            self.calls = []

        def dispatch(
            self,
            task,
            *,
            attempt,
            timeout_seconds=None,
        ):
            self.calls.append(
                task.task_id
            )

            return success(task.task_id)

    dispatcher = ParallelDispatcher()

    orchestrator = AgentOrchestrator(
        dispatcher,
        execution_mode=ExecutionMode.PARALLEL,
        max_workers=2,
        max_retries=0,
    )

    result = orchestrator.run(
        build_plan()
    )

    assert result.status == ResultStatus.SUCCESS

    assert sorted(dispatcher.calls) == [1, 2]

    assert len(result.outcomes) == 2

    assert all(
        outcome.success
        for outcome in result.outcomes
    )

    assert all(
        decision.action
        == DecisionAction.COMPLETE
        for decision in result.decisions
    )

    for task_id in [1, 2]:
        assert (
            orchestrator.state_manager.get_status(task_id)
            == ExecutionStatus.COMPLETED
        )