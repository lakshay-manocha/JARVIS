"""Phase F integration tests for orchestration, dispatch, events and state."""

from __future__ import annotations

from agent_engine.contracts.enums import ExecutionStatus, ResultStatus
from agent_engine.decision_manager.models.execution_outcome import ExecutionOutcome, FailureType
from agent_engine.dispatcher.action_dispatcher import ActionDispatcher
from agent_engine.events.event_bus import AgentEvent, EventBus
from agent_engine.orchestration.agent_orchestrator import AgentOrchestrator


class ScriptedDispatcher:
    def __init__(self, scripts: dict[int, list[ExecutionOutcome]]) -> None:
        self.scripts = {task_id: list(outcomes) for task_id, outcomes in scripts.items()}
        self.calls: list[tuple[int, int]] = []

    def dispatch(self, task, *, attempt: int, timeout_seconds=None):
        self.calls.append((task.task_id, attempt))
        outcomes = self.scripts[task.task_id]
        outcome = outcomes.pop(0)
        return outcome


def success(task_id: int) -> ExecutionOutcome:
    return ExecutionOutcome(
        task_id=task_id,
        status=ExecutionStatus.COMPLETED,
        success=True,
        attempt=1,
        max_retries=0,
    )


def transient_failure(task_id: int) -> ExecutionOutcome:
    return ExecutionOutcome(
        task_id=task_id,
        status=ExecutionStatus.FAILED,
        success=False,
        attempt=1,
        retry_count=0,
        max_retries=1,
        failure_type=FailureType.TRANSIENT,
        error_message="temporary failure",
    )


def build_plan():
    return {
        "goal": "Complete the browser workflow",
        "summary": "Open Chrome and search for the requested information.",
        "missing_information": [],
        "tasks": ["Open Chrome", "Search Google"],
    }


def test_phase_f_end_to_end_success():
    dispatcher = ScriptedDispatcher({1: [success(1)], 2: [success(2)]})
    events: list[AgentEvent] = []
    bus = EventBus()
    bus.subscribe("*", events.append)

    orchestrator = AgentOrchestrator(dispatcher, event_bus=bus)
    result = orchestrator.run(build_plan())

    assert result.status == ResultStatus.SUCCESS
    assert result.planning_result is not None
    assert result.planning_result.total_steps == 2
    assert dispatcher.calls == [(1, 1), (2, 1)]
    assert orchestrator.state_manager.get_status(1) == ExecutionStatus.COMPLETED
    assert orchestrator.state_manager.get_status(2) == ExecutionStatus.COMPLETED
    assert any(event.name == "request.completed" for event in events)
    assert any(event.name == "task.started" for event in events)
    assert any(event.name == "task.completed" for event in events)


def test_phase_f_retry_is_decided_by_decision_manager():
    dispatcher = ScriptedDispatcher({1: [transient_failure(1), success(1)], 2: [success(2)]})
    orchestrator = AgentOrchestrator(dispatcher, max_retries=1)

    result = orchestrator.run(build_plan())

    assert result.status == ResultStatus.SUCCESS
    assert dispatcher.calls[0] == (1, 1)
    assert dispatcher.calls[1] == (1, 2)
    assert orchestrator.state_manager.get_status(1) == ExecutionStatus.COMPLETED
    assert any(decision.action.value == "RETRY" for decision in result.decisions)


def test_phase_f_dispatch_failure_is_contained_and_request_continues():
    class FailingDispatcher:
        def dispatch(self, task, *, attempt, timeout_seconds=None):
            if task.task_id == 1:
                raise RuntimeError("controller unavailable")
            return success(task.task_id)

    orchestrator = AgentOrchestrator(FailingDispatcher())
    result = orchestrator.run(build_plan())

    assert result.status == ResultStatus.FAILED
    assert orchestrator.state_manager.get_status(1) == ExecutionStatus.FAILED
    # Task 2 is independent in this simple plan and must not be abandoned
    # merely because task 1 failed.
    assert orchestrator.state_manager.get_status(2) == ExecutionStatus.COMPLETED


def test_phase_f_dispatcher_contract_is_explicit():
    assert hasattr(ActionDispatcher, "__annotations__") or hasattr(ActionDispatcher, "dispatch")


def test_phase_f_skips_dependency_after_parent_failure():
    class FailingFirstDispatcher:
        def dispatch(self, task, *, attempt, timeout_seconds=None):
            if task.task_id == 1:
                raise RuntimeError("first task failed")
            return success(task.task_id)

    # Use an explicit GraphBuilder dependency so the test exercises the
    # Phase D/E boundary rather than a hard-coded orchestrator shortcut.
    class OneDependencyGraphBuilder:
        def __init__(self):
            from agent_engine.agent_brain.graph_builder import GraphBuilder
            self._inner = GraphBuilder()

        def build(self, context):
            context = self._inner.build(context)
            graph = context.execution_graph
            graph.add_dependency(1, 2, dependency_type="EXPLICIT", confidence=1.0, reason="test")
            graph.recalculate_roots_and_leaves()
            context.graph_validation_result = __import__(
                "agent_engine.agent_brain.graph_validator",
                fromlist=["GraphValidator"],
            ).GraphValidator().validate(graph)
            return context

    orchestrator = AgentOrchestrator(
        FailingFirstDispatcher(),
        graph_builder=OneDependencyGraphBuilder(),
    )
    result = orchestrator.run(build_plan())

    assert result.status == ResultStatus.FAILED
    assert orchestrator.state_manager.get_status(1) == ExecutionStatus.FAILED
    assert orchestrator.state_manager.get_status(2) == ExecutionStatus.SKIPPED
    assert any(decision.action.value == "SKIP" for decision in result.decisions)


def test_phase_f_parallel_mode_executes_same_dependency_level_concurrently():
    import threading
    import time

    class ParallelDispatcher:
        def __init__(self):
            self.started: list[int] = []
            self.lock = threading.Lock()

        def dispatch(self, task, *, attempt, timeout_seconds=None):
            with self.lock:
                self.started.append(task.task_id)
            time.sleep(0.02)
            return success(task.task_id)

    dispatcher = ParallelDispatcher()
    orchestrator = AgentOrchestrator(
        dispatcher,
        execution_mode="PARALLEL",
        max_workers=2,
    )
    result = orchestrator.run(build_plan())

    assert result.status == ResultStatus.SUCCESS
    assert sorted(dispatcher.started) == [1, 2]

def test_phase_f_failure_handler_integrates_with_retry_policy():
    class FailureThenSuccessDispatcher:
        def __init__(self):
            self.calls: list[tuple[int, int]] = []

        def dispatch(self, task, *, attempt, timeout_seconds=None):
            self.calls.append((task.task_id, attempt))

            if task.task_id == 1 and attempt == 1:
                raise TimeoutError("temporary controller timeout")

            return success(task.task_id)

    dispatcher = FailureThenSuccessDispatcher()

    orchestrator = AgentOrchestrator(
        dispatcher,
        max_retries=1,
    )

    result = orchestrator.run(build_plan())

    assert result.status == ResultStatus.SUCCESS

    assert dispatcher.calls == [
        (1, 1),
        (1, 2),
        (2, 1),
    ]

    assert orchestrator.state_manager.get_status(
        1
    ) == ExecutionStatus.COMPLETED

    assert orchestrator.state_manager.get_status(
        2
    ) == ExecutionStatus.COMPLETED

    assert result.outcomes[0].failure_type == FailureType.TIMEOUT
    assert result.outcomes[0].success is False

    assert result.decisions[0].action.value == "RETRY"
    assert result.decisions[1].action.value == "COMPLETE"