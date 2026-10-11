"""
===============================================================================
File Name   : level_1_multi_task_demo.py
Module      : Integration Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
M5-E.9 demonstration for multi-task Level-1 Agentic → Automation integration.

This demonstration verifies that multiple tasks received from an LLM plan can
travel through the complete Agent Brain and Automation Engine pipeline using
the Mock Automation Engine.

Pipeline:

    LLM Plan
        ↓
    AgentOrchestrator
        ↓
    Validator
        ↓
    Interpreter
        ↓
    GraphBuilder
        ↓
    Planner
        ↓
    AutomationActionDispatcher
        ↓
    ActionRegistry
        ↓
    MockAutomationEngine
        ↓
    ExecutionOutcome × N
        ↓
    DecisionManager
        ↓
    StateManager
        ↓
    Final Request Result

No real browser, desktop, filesystem, keyboard, mouse, or screen automation
is performed.

This is a Level-1 integration demonstration.

Author : Team JARVIS
===============================================================================
"""

from unittest import result

from agent_engine.agent_brain.models.llm_plan import LLMPlan
from agent_engine.automation.dispatcher.action_dispatcher import (
    AutomationActionDispatcher,
)
from agent_engine.automation.engine.mock_automation_engine import (
    create_default_mock_engine,
)
from agent_engine.automation.registry.action_registry import ActionRegistry
from agent_engine.contracts.enums import (
    ExecutionMode,
    ExecutionStatus,
    ResultStatus,
)
from agent_engine.decision_manager.models.decision import DecisionAction
from agent_engine.orchestration.agent_orchestrator import AgentOrchestrator


# =============================================================================
# Display Helpers
# =============================================================================

SEPARATOR = "-" * 78
DOUBLE_SEPARATOR = "=" * 78


def print_header(title: str) -> None:
    """Print a formatted demonstration header."""
    print()
    print(DOUBLE_SEPARATOR)
    print(title)
    print(DOUBLE_SEPARATOR)


def print_field(label: str, value) -> None:
    """Print a formatted result field."""
    print(f"[{label:<24}] {value}")


# =============================================================================
# M5-E.9 — Multi-Task Level-1 LLM Plan
# =============================================================================

def build_level_1_multi_task_llm_plan() -> LLMPlan:
    """
    Build a simple multi-task Level-1 LLM plan.

    The tasks are intentionally independent so that this demonstration
    verifies multi-task orchestration without introducing additional
    dependency or failure-handling complexity.
    """

    return LLMPlan(
        goal="Open example.com and search for artificial intelligence",
        summary=(
            "Open the example website and perform a web search "
            "for artificial intelligence."
        ),
        missing_information=[],
        tasks=[
            "Open https://example.com",
            "Search for artificial intelligence",
        ],
    )


# =============================================================================
# Mock Automation Engine Setup
# =============================================================================

def create_handler(mock_engine, action):
    """
    Create a handler bound to one specific mock action.
    """

    def handler(**kwargs):
        return mock_engine.execute(
            action,
            kwargs,
        )

    return handler


def create_automation_dispatcher() -> tuple[
    AutomationActionDispatcher,
    object,
]:
    """
    Create the Mock Automation Engine and connect all of its actions to the
    Automation Action Dispatcher.
    """

    mock_engine = create_default_mock_engine()

    registry = ActionRegistry()

    for action in mock_engine.list_actions():
        registry.register(
            action,
            create_handler(mock_engine, action),
        )

    dispatcher = AutomationActionDispatcher(
        registry,
    )

    return dispatcher, mock_engine


# =============================================================================
# M5-E.9 Multi-Task Demonstration
# =============================================================================

def run_demo() -> None:
    """
    Execute the complete M5-E.9 multi-task Level-1 demonstration.
    """

    print_header(
        "JARVIS — M5-E.9 MULTI-TASK LEVEL-1 DEMONSTRATION"
    )

    # -------------------------------------------------------------------------
    # Stage 1 — Create Mock Automation Engine
    # -------------------------------------------------------------------------

    print_field(
        "AUTOMATION ENGINE",
        "Mock Automation Engine initialized",
    )

    dispatcher, mock_engine = create_automation_dispatcher()

    # -------------------------------------------------------------------------
    # Stage 2 — Create Agent Orchestrator
    # -------------------------------------------------------------------------

    orchestrator = AgentOrchestrator(
        dispatcher,
        execution_mode=ExecutionMode.SEQUENTIAL,
        timeout_seconds=30.0,
        max_retries=0,
    )

    print_field(
        "ORCHESTRATOR",
        "AgentOrchestrator initialized",
    )

    # -------------------------------------------------------------------------
    # Stage 3 — Create Multi-Task LLM Plan
    # -------------------------------------------------------------------------

    plan = build_level_1_multi_task_llm_plan()

    print_field(
        "LLM PLAN",
        f"{len(plan.tasks)} task(s) received",
    )

    for index, task in enumerate(plan.tasks, start=1):
        print_field(
            f"TASK {index}",
            task,
        )

    # -------------------------------------------------------------------------
    # Stage 4 — Execute Complete Pipeline
    # -------------------------------------------------------------------------

    print()
    print(SEPARATOR)
    print("Executing multi-task Agent Brain → Automation Engine pipeline...")
    print(SEPARATOR)

    result = orchestrator.run(plan)

    # -------------------------------------------------------------------------
    # Stage 5 — Request Result
    # -------------------------------------------------------------------------

    print_header("REQUEST RESULT")

    print_field(
        "REQUEST ID",
        result.request_id,
    )

    print_field(
        "FINAL STATUS",
        result.status.value,
    )

    print_field(
        "VALIDATION",
        "PASSED" if result.validation.is_valid else "FAILED",
    )

    print_field(
        "PLANNING",
        (
            "PASSED"
            if result.planning_result
            and result.planning_result.is_valid
            else "FAILED"
        ),
    )

    if result.planning_result is not None:
        print_field(
            "TOTAL STEPS",
            result.planning_result.total_steps,
        )

    # -------------------------------------------------------------------------
    # Stage 6 — Validate Request
    # -------------------------------------------------------------------------

    assert result is not None

    assert result.request_id is not None

    assert result.status == ResultStatus.SUCCESS

    assert result.validation is not None
    assert result.validation.is_valid is True

    assert result.planning_result is not None
    assert result.planning_result.is_valid is True

    assert result.planning_result.total_steps == 2

    # -------------------------------------------------------------------------
    # Stage 7 — Execution Outcomes
    # -------------------------------------------------------------------------

    print_header("EXECUTION OUTCOMES")

    assert len(result.outcomes) == 2

    for outcome in result.outcomes:
        print_field(
            "TASK ID",
            outcome.task_id,
        )
        print_field(
            "ATTEMPT",
            outcome.attempt,
        )
        print_field(
            "STATUS",
            outcome.status.value,
        )
        print_field(
            "SUCCESS",
            outcome.success,
        )
        print_field(
            "EXECUTION TIME",
            f"{outcome.execution_time:.4f} seconds",
        )
        print()

    # Verify both tasks completed successfully.
    for outcome in result.outcomes:
        assert outcome.success is True
        assert outcome.status == ExecutionStatus.COMPLETED
        assert outcome.attempt == 1

    # Verify both task IDs are present.
    task_ids = sorted(
        outcome.task_id
        for outcome in result.outcomes
    )

    assert task_ids == [1, 2]

    # -------------------------------------------------------------------------
    # Stage 8 — Decision Manager
    # -------------------------------------------------------------------------

    print_header("DECISIONS")

    assert len(result.decisions) == 2

    for decision in result.decisions:
        print_field(
            "TASK ID",
            decision.task_id,
        )
        print_field(
            "DECISION",
            decision.action.value,
        )
        print_field(
            "DECISION ENUM",
            repr(decision.action),
        )
        print_field(
            "REASON",
            decision.reason,
        )
        print()

        assert decision.action == DecisionAction.COMPLETE, (
            f"Unexpected decision for Task {decision.task_id}: "
            f"{decision.action!r}"
        )
    # -------------------------------------------------------------------------
    # Stage 9 — Runtime State
    # -------------------------------------------------------------------------

    print_header("RUNTIME STATE")

    assert result.context.execution_graph is not None

    for task_id in [1, 2]:

        status = orchestrator.state_manager.get_status(
            task_id
        )

        print_field(
            f"TASK {task_id}",
            status.value,
        )

        assert status == ExecutionStatus.COMPLETED

    # -------------------------------------------------------------------------
    # Stage 10 — Mock Automation History
    # -------------------------------------------------------------------------

    print_header("AUTOMATION HISTORY")

    history = mock_engine.get_execution_history()

    assert len(history) == 2

    for entry in history:

        print_field(
            "ACTION",
            entry["action"],
        )

        print_field(
            "PARAMETERS",
            entry["parameters"],
        )

        print_field(
            "RESULT",
            entry["result"],
        )

        print()

    # Verify the expected actions were dispatched.
    actions = [
        entry["action"]
        for entry in history
    ]

    assert actions == [
        "open",
        "search",
    ]

    # Verify parameters were actually passed to the Automation Engine.
    assert history[0]["parameters"] is not None
    assert history[1]["parameters"] is not None

    # -------------------------------------------------------------------------
    # Stage 11 — Final Demonstration Verdict
    # -------------------------------------------------------------------------

    print_header("M5-E.9 DEMONSTRATION VERDICT")

    print(
        "✓ MULTI-TASK LEVEL-1 DEMO PASSED"
    )

    print()
    print(
        "JARVIS successfully processed multiple tasks from the LLM plan "
        "through the Agent Brain and Automation Engine."
    )

    print()
    print(
        "Both tasks were dispatched, executed by the Mock Automation Engine, "
        "converted into ExecutionOutcome objects, evaluated by the "
        "DecisionManager, and marked COMPLETED by the StateManager."
    )

    print()
    print(DOUBLE_SEPARATOR)
    print("M5-E.9 DEMONSTRATION COMPLETE")
    print(DOUBLE_SEPARATOR)


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    run_demo()