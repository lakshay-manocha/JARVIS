"""
===============================================================================
File Name   : level_1_single_task_demo.py
Module      : Integration Demo
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
M5-E.8 — Single-Task Level-1 Demonstration.

Demonstrates one complete Agentic execution cycle:

    User/LLM Request
            ↓
        LLM Plan
            ↓
    AgentOrchestrator
            ↓
        Validator
            ↓
        Interpreter
            ↓
      Intent Detector
            ↓
      Action Resolver
            ↓
    Parameter Resolver
            ↓
      Tool Resolver
            ↓
       GraphBuilder
            ↓
         Planner
            ↓
    Action Dispatcher
            ↓
      Action Registry
            ↓
   Mock Automation Engine
            ↓
     ExecutionOutcome
            ↓
      DecisionManager
            ↓
       StateManager
            ↓
       Final Result

This is a Level-1 demonstration only.

No real browser, desktop, filesystem, keyboard, mouse, or screen
automation is performed.

The purpose is to demonstrate that the complete Agent Brain +
Automation Engine integration works for a single task.

Author : Team JARVIS
===============================================================================
"""

from __future__ import annotations

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
from agent_engine.orchestration.agent_orchestrator import AgentOrchestrator


# =============================================================================
# Display Helpers
# =============================================================================

def print_header(title: str) -> None:
    """Print a formatted section header."""

    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def print_stage(stage: str, value: str) -> None:
    """Print one pipeline stage."""

    print(f"[{stage:<24}] {value}")


# =============================================================================
# Mock Automation Setup
# =============================================================================

def create_handler(mock_engine, action):
    """
    Create a registry handler bound to one mock automation action.
    """

    def handler(**kwargs):
        return mock_engine.execute(
            action,
            kwargs,
        )

    return handler


def create_automation_dispatcher():
    """
    Create the mock Automation Engine and connect it to the
    Automation Action Dispatcher.
    """

    mock_engine = create_default_mock_engine()

    registry = ActionRegistry()

    for action in mock_engine.list_actions():

        registry.register(
            action,
            create_handler(
                mock_engine,
                action,
            ),
        )

    dispatcher = AutomationActionDispatcher(
        registry,
    )

    return dispatcher, mock_engine


# =============================================================================
# Level-1 LLM Plan
# =============================================================================

def build_level_1_plan() -> LLMPlan:
    """
    Create the single-task Level-1 demonstration plan.

    The request is intentionally simple so that the complete pipeline
    can be observed without introducing multi-task dependencies.
    """

    return LLMPlan(
        goal="Open example website",
        summary="Open the example website in the browser.",
        missing_information=[],
        tasks=[
            "Open https://example.com",
        ],
    )


# =============================================================================
# Main Demonstration
# =============================================================================

def main() -> None:
    """Run the M5-E.8 single-task Level-1 demonstration."""

    print_header(
        "JARVIS — M5-E.8 SINGLE-TASK LEVEL-1 DEMONSTRATION"
    )

    print_stage(
        "REQUEST",
        "Open https://example.com",
    )

    # -------------------------------------------------------------------------
    # Stage 1 — Automation Engine
    # -------------------------------------------------------------------------

    dispatcher, mock_engine = create_automation_dispatcher()

    print_stage(
        "AUTOMATION ENGINE",
        "Mock Automation Engine initialized",
    )

    # -------------------------------------------------------------------------
    # Stage 2 — Agent Orchestrator
    # -------------------------------------------------------------------------

    orchestrator = AgentOrchestrator(
        dispatcher,
        execution_mode=ExecutionMode.SEQUENTIAL,
        timeout_seconds=30.0,
        max_retries=0,
    )

    print_stage(
        "ORCHESTRATOR",
        "AgentOrchestrator initialized",
    )

    # -------------------------------------------------------------------------
    # Stage 3 — LLM Plan
    # -------------------------------------------------------------------------

    plan = build_level_1_plan()

    print_stage(
        "LLM PLAN",
        f"{len(plan.tasks)} task(s) received",
    )

    print_stage(
        "TASK",
        plan.tasks[0],
    )

    # -------------------------------------------------------------------------
    # Stage 4 — Complete Execution
    # -------------------------------------------------------------------------

    print()
    print("-" * 78)
    print("Executing Agent Brain → Automation Engine pipeline...")
    print("-" * 78)

    result = orchestrator.run(plan)

    # -------------------------------------------------------------------------
    # Stage 5 — Request Result
    # -------------------------------------------------------------------------

    print_header("REQUEST RESULT")

    print_stage(
        "REQUEST ID",
        str(result.request_id),
    )

    print_stage(
        "FINAL STATUS",
        result.status.value,
    )

    # -------------------------------------------------------------------------
    # Stage 6 — Validation
    # -------------------------------------------------------------------------

    if result.validation is not None:

        print_stage(
            "VALIDATION",
            "PASSED" if result.validation.is_valid else "FAILED",
        )

    # -------------------------------------------------------------------------
    # Stage 7 — Planning
    # -------------------------------------------------------------------------

    if result.planning_result is not None:

        print_stage(
            "PLANNING",
            "PASSED" if result.planning_result.is_valid else "FAILED",
        )

        print_stage(
            "TOTAL STEPS",
            str(result.planning_result.total_steps),
        )

    # -------------------------------------------------------------------------
    # Stage 8 — Execution Outcome
    # -------------------------------------------------------------------------

    if result.outcomes:

        outcome = result.outcomes[0]

        print_header("EXECUTION OUTCOME")

        print_stage(
            "TASK ID",
            str(outcome.task_id),
        )

        print_stage(
            "ATTEMPT",
            str(outcome.attempt),
        )

        print_stage(
            "STATUS",
            outcome.status.value,
        )

        print_stage(
            "SUCCESS",
            str(outcome.success),
        )

        if outcome.execution_time is not None:

            print_stage(
                "EXECUTION TIME",
                f"{outcome.execution_time:.4f} seconds",
            )

    # -------------------------------------------------------------------------
    # Stage 9 — Decision Manager
    # -------------------------------------------------------------------------

    if result.decisions:

        decision = result.decisions[0]

        print_header("DECISION")

        print_stage(
            "TASK ID",
            str(decision.task_id),
        )

        print_stage(
            "DECISION",
            decision.action.value,
        )

        print_stage(
            "REASON",
            decision.reason,
        )

    # -------------------------------------------------------------------------
    # Stage 10 — Runtime State
    # -------------------------------------------------------------------------

    runtime_status = orchestrator.state_manager.get_status(1)

    print_header("RUNTIME STATE")

    print_stage(
        "TASK 1",
        runtime_status.value,
    )

    # -------------------------------------------------------------------------
    # Stage 11 — Mock Automation History
    # -------------------------------------------------------------------------

    history = mock_engine.get_execution_history()

    print_header("AUTOMATION HISTORY")

    if history:

        execution = history[0]

        print_stage(
            "ACTION",
            str(execution.get("action")),
        )

        print_stage(
            "PARAMETERS",
            str(execution.get("parameters")),
        )

        print_stage(
            "RESULT",
            str(execution.get("result")),
        )

    else:

        print_stage(
            "HISTORY",
            "No automation execution recorded",
        )

    # -------------------------------------------------------------------------
    # Stage 12 — Final Demonstration Verdict
    # -------------------------------------------------------------------------

    print_header("M5-E.8 DEMONSTRATION VERDICT")

    success = (
        result.status == ResultStatus.SUCCESS
        and len(result.outcomes) == 1
        and result.outcomes[0].success is True
        and result.outcomes[0].status == ExecutionStatus.COMPLETED
        and runtime_status == ExecutionStatus.COMPLETED
        and len(history) == 1
    )

    if success:

        print("✓ SINGLE-TASK LEVEL-1 DEMO PASSED")
        print()
        print(
            "JARVIS successfully processed one task from the "
            "LLM plan through the Agent Brain and Automation Engine."
        )

    else:

        print("✗ SINGLE-TASK LEVEL-1 DEMO FAILED")

        if result.error:
            print()
            print(f"Error: {result.error}")

    print()
    print("=" * 78)
    print("M5-E.8 DEMONSTRATION COMPLETE")
    print("=" * 78)


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    main()