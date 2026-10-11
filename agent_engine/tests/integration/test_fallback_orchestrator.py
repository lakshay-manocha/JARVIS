"""F-4.5 fallback integration tests for AgentOrchestrator."""

from __future__ import annotations

from agent_engine.contracts.enums import (
    ExecutionStatus,
    ResultStatus,
)
from agent_engine.decision_manager.models.execution_outcome import (
    ExecutionOutcome,
    FailureType,
)
from agent_engine.decision_manager.models.fallback import (
    FallbackOption,
)
from agent_engine.decision_manager.models.decision import (
    DecisionAction,
)
from agent_engine.orchestration.agent_orchestrator import (
    AgentOrchestrator,
)


def failure(task_id: int) -> ExecutionOutcome:
    return ExecutionOutcome(
        task_id=task_id,
        status=ExecutionStatus.FAILED,
        success=False,
        attempt=1,
        retry_count=0,
        max_retries=0,
        failure_type=FailureType.PERMANENT,
        error_message="primary action failed",
    )


class FailingDispatcher:
    def __init__(self) -> None:
        self.calls: list[tuple[int, int]] = []

    def dispatch(
        self,
        task,
        *,
        attempt: int,
        timeout_seconds=None,
    ):
        self.calls.append(
            (task.task_id, attempt)
        )

        return failure(task.task_id)


def build_plan():
    return {
        "goal": "Open the requested website",
        "summary": "Open the website using the browser.",
        "missing_information": [],
        "tasks": ["Open Chrome"],
    }


def build_fallback_options():
    return {
        1: [
            FallbackOption(
                id="fallback_browser",
                action="open",
                tool="browser_agent",
                parameters={
                    "url": "https://example.com"
                },
                priority=1,
                description="Use alternate browser path",
            )
        ]
    }


def test_orchestrator_selects_fallback_after_failure():

    dispatcher = FailingDispatcher()

    orchestrator = AgentOrchestrator(
        dispatcher,
        fallback_options=build_fallback_options(),
    )

    result = orchestrator.run(
        build_plan()
    )

    assert result.status == ResultStatus.FAILED

    assert len(result.decisions) == 1

    decision = result.decisions[0]

    assert decision.action == DecisionAction.FALLBACK

    assert decision.selected_fallback is not None

    assert (
        decision.selected_fallback.id
        == "fallback_browser"
    )


def test_fallback_moves_task_back_to_running():

    dispatcher = FailingDispatcher()

    orchestrator = AgentOrchestrator(
        dispatcher,
        fallback_options=build_fallback_options(),
    )

    orchestrator.run(
        build_plan()
    )

    assert (
        orchestrator.state_manager.get_status(1)
        == ExecutionStatus.RUNNING
    )


def test_fallback_does_not_execute_again():

    dispatcher = FailingDispatcher()

    orchestrator = AgentOrchestrator(
        dispatcher,
        fallback_options=build_fallback_options(),
    )

    orchestrator.run(
        build_plan()
    )

    # Only the original primary action was dispatched.
    # The fallback has been selected but not executed.
    assert dispatcher.calls == [
        (1, 1)
    ]


def test_no_fallback_keeps_task_failed():

    dispatcher = FailingDispatcher()

    orchestrator = AgentOrchestrator(
        dispatcher
    )

    result = orchestrator.run(
        build_plan()
    )

    assert result.status == ResultStatus.FAILED

    assert (
        orchestrator.state_manager.get_status(1)
        == ExecutionStatus.FAILED
    )

    assert result.decisions[0].action == (
        DecisionAction.FAIL
    )


def test_fallback_event_is_emitted():

    from agent_engine.events.event_bus import (
        AgentEvent,
        EventBus,
    )

    events: list[AgentEvent] = []

    bus = EventBus()
    bus.subscribe(
        "*",
        events.append,
    )

    orchestrator = AgentOrchestrator(
        FailingDispatcher(),
        fallback_options=build_fallback_options(),
        event_bus=bus,
    )

    orchestrator.run(
        build_plan()
    )

    fallback_events = [
        event
        for event in events
        if event.name == "task.fallback"
    ]

    assert len(fallback_events) == 1

    assert (
        fallback_events[0].payload[
            "selected_fallback"
        ].id
        == "fallback_browser"
    )