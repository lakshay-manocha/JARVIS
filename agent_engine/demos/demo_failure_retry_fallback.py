"""
===============================================================================
File Name   : demo_failure_retry_fallback.py
Module      : Demonstration
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Demonstrates the complete Phase F reliability layer:

    Failure Handling
        ↓
    Retry Decision
        ↓
    Retry Execution
        ↓
    Permanent Failure
        ↓
    Fallback Selection

The demo uses a controlled dispatcher so that failures are deterministic.

No real browser, keyboard, mouse, or desktop automation is performed.

Author : Team JARVIS
===============================================================================
"""

from __future__ import annotations

from agent_engine.contracts.enums import (
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

from agent_engine.decision_manager.models.fallback import (
    FallbackOption,
)

from agent_engine.orchestration.agent_orchestrator import (
    AgentOrchestrator,
)


# =============================================================================
# Helpers
# =============================================================================


def print_header(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def print_result(result) -> None:
    print()
    print(f"Final Result : {result.status.value}")

    print()
    print("Execution Outcomes:")

    for outcome in result.outcomes:
        print(
            f"  Task {outcome.task_id} | "
            f"Attempt {outcome.attempt} | "
            f"Success={outcome.success} | "
            f"Failure={outcome.failure_type.value}"
        )

    print()
    print("Decision History:")

    for decision in result.decisions:
        print(
            f"  Task {decision.task_id} | "
            f"Decision={decision.action.value} | "
            f"Reason={decision.reason}"
        )


def single_task_plan(description: str) -> dict:
    return {
        "goal": description,
        "summary": description,
        "missing_information": [],
        "tasks": [description],
    }


# =============================================================================
# Scenario 1 — Retry
# =============================================================================


def demo_retry() -> None:

    print_header(
        "SCENARIO 1 — TRANSIENT FAILURE → RETRY → SUCCESS"
    )

    class RetryDispatcher:

        def __init__(self):
            self.calls = 0

        def dispatch(
            self,
            task,
            *,
            attempt,
            timeout_seconds=None,
        ):

            self.calls += 1

            print(
                f"[Dispatcher] Attempt {attempt}"
            )

            if attempt == 1:

                print(
                    "[Dispatcher] Temporary failure occurred."
                )

                raise TimeoutError(
                    "Temporary automation timeout"
                )

            print(
                "[Dispatcher] Automation succeeded."
            )

            return ExecutionOutcome(
                task_id=task.task_id,
                status=ExecutionStatus.COMPLETED,
                success=True,
                attempt=attempt,
                retry_count=attempt - 1,
                max_retries=1,
                timeout_seconds=60.0,
                execution_time=0.02,
                timed_out=False,
                failure_type=FailureType.NONE,
                error_message=None,
            )

    dispatcher = RetryDispatcher()

    orchestrator = AgentOrchestrator(
        dispatcher,
        max_retries=1,
        timeout_seconds=60.0,
    )

    print(
        "[JARVIS] Request: Open https://example.com"
    )

    result = orchestrator.run(
        single_task_plan(
            "Open https://example.com"
        )
    )

    print()
    print(
        "[DecisionManager] First attempt → RETRY"
    )

    print(
        "[DecisionManager] Second attempt → COMPLETE"
    )

    print_result(result)

    assert result.status == ResultStatus.SUCCESS

    assert len(result.outcomes) == 2

    assert (
        result.decisions[0].action
        == DecisionAction.RETRY
    )

    assert (
        result.decisions[1].action
        == DecisionAction.COMPLETE
    )

    print()
    print("✓ Retry scenario completed successfully.")


# =============================================================================
# Scenario 2 — Permanent Failure
# =============================================================================


def demo_permanent_failure() -> None:

    print_header(
        "SCENARIO 2 — PERMANENT FAILURE → FAIL"
    )

    class PermanentFailureDispatcher:

        def dispatch(
            self,
            task,
            *,
            attempt,
            timeout_seconds=None,
        ):

            print(
                f"[Dispatcher] Attempt {attempt}"
            )

            print(
                "[Dispatcher] Permanent automation failure."
            )

            return ExecutionOutcome(
                task_id=task.task_id,
                status=ExecutionStatus.FAILED,
                success=False,
                attempt=attempt,
                retry_count=attempt - 1,
                max_retries=0,
                timeout_seconds=60.0,
                execution_time=0.02,
                timed_out=False,
                failure_type=FailureType.PERMANENT,
                error_message="Permanent automation failure",
            )

    orchestrator = AgentOrchestrator(
        PermanentFailureDispatcher(),
        max_retries=0,
        timeout_seconds=60.0,
    )

    print(
        "[JARVIS] Request: Open unavailable resource"
    )

    result = orchestrator.run(
        single_task_plan(
            "Open unavailable resource"
        )
    )

    print()
    print(
        "[DecisionManager] Decision → FAIL"
    )

    print_result(result)

    assert result.status == ResultStatus.FAILED

    assert len(result.outcomes) == 1

    assert (
        result.decisions[0].action
        == DecisionAction.FAIL
    )

    print()
    print("✓ Permanent failure scenario completed successfully.")


# =============================================================================
# Scenario 3 — Fallback
# =============================================================================


def demo_fallback() -> None:

    print_header(
        "SCENARIO 3 — PRIMARY FAILURE → FALLBACK SELECTION"
    )

    class FailingPrimaryDispatcher:

        def __init__(self):
            self.calls = 0

        def dispatch(
            self,
            task,
            *,
            attempt,
            timeout_seconds=None,
        ):

            self.calls += 1

            print(
                "[Dispatcher] Executing primary action..."
            )

            print(
                "[Dispatcher] Primary action failed."
            )

            return ExecutionOutcome(
                task_id=task.task_id,
                status=ExecutionStatus.FAILED,
                success=False,
                attempt=attempt,
                retry_count=attempt - 1,
                max_retries=0,
                timeout_seconds=60.0,
                execution_time=0.02,
                timed_out=False,
                failure_type=FailureType.PERMANENT,
                error_message="Primary automation unavailable",
            )

    dispatcher = FailingPrimaryDispatcher()

    fallback = FallbackOption(
        id="browser_fallback",
        action="open",
        tool="browser",
        parameters={
            "url": "https://example.com"
        },
        priority=1,
        description="Use browser automation as fallback",
    )

    orchestrator = AgentOrchestrator(
        dispatcher,
        max_retries=0,
        timeout_seconds=60.0,
        fallback_options={
            1: [fallback]
        },
    )

    print(
        "[JARVIS] Request: Open https://example.com"
    )

    result = orchestrator.run(
        single_task_plan(
            "Open https://example.com"
        )
    )

    print()
    print(
        "[DecisionManager] Primary action failed."
    )

    print(
        "[DecisionManager] Evaluating fallback..."
    )

    print(
        "[DecisionManager] Fallback selected:"
    )

    print(
        f"  ID       : {fallback.id}"
    )

    print(
        f"  Action   : {fallback.action}"
    )

    print(
        f"  Tool     : {fallback.tool}"
    )

    print(
        f"  Priority : {fallback.priority}"
    )

    print()
    print(
        "[Automation Layer] Fallback execution NOT performed."
    )

    print(
        "[Reason] DecisionManager selects the fallback; "
        "automation execution belongs to the automation layer."
    )

    print_result(result)

    assert result.status == ResultStatus.FAILED

    assert (
        result.decisions[0].action
        == DecisionAction.FALLBACK
    )

    assert (
        result.decisions[0].selected_fallback.id
        == "browser_fallback"
    )

    assert dispatcher.calls == 1

    assert (
        orchestrator.state_manager.get_status(1)
        == ExecutionStatus.RUNNING
    )

    print()
    print("✓ Fallback selection scenario completed successfully.")


# =============================================================================
# Main
# =============================================================================


def main() -> None:

    print()
    print("#" * 72)
    print("# JARVIS — PHASE F RELIABILITY DEMONSTRATION")
    print("# Failure Handling | Retry | Fallback")
    print("#" * 72)

    demo_retry()

    demo_permanent_failure()

    demo_fallback()

    print_header(
        "PHASE F DEMONSTRATION COMPLETED"
    )

    print(
        "✓ Failure Handling demonstrated"
    )

    print(
        "✓ Retry mechanism demonstrated"
    )

    print(
        "✓ Permanent failure demonstrated"
    )

    print(
        "✓ Fallback selection demonstrated"
    )

    print(
        "✓ DecisionManager coordination demonstrated"
    )

    print(
        "✓ StateManager coordination demonstrated"
    )

    print()
    print(
        "JARVIS Phase F reliability layer is operational."
    )


if __name__ == "__main__":
    main()