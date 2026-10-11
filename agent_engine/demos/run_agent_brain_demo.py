"""
===============================================================================
File Name   : run_agent_brain_demo.py
Module      : Agent Brain Demonstration
Project     : JARVIS - Agent Decision Engine & Automation Engine

Purpose:
--------
Runs the real Agent Brain orchestration pipeline using the existing
AgentOrchestrator and a non-automation demonstration dispatcher.

This file contains presentation/demo code only.

No Module 5 automation is implemented here.
===============================================================================
"""

from __future__ import annotations

import logging

from agent_engine.agent_brain.models.llm_plan import LLMPlan
from agent_engine.contracts.enums import ExecutionMode
from agent_engine.dispatcher.demo_dispatcher import DemoDispatcher
from agent_engine.events.event_bus import AgentEvent, EventBus
from agent_engine.orchestration.agent_orchestrator import AgentOrchestrator


LINE = "═" * 90
SUB_LINE = "-" * 90


def print_banner(title: str) -> None:
    print()
    print(LINE)
    print(title.center(90))
    print(LINE)


def print_event(event: AgentEvent) -> None:
    """
    Display actual orchestration events emitted by the AgentOrchestrator.
    """

    task = (
        f" | Task {event.task_id}"
        if event.task_id is not None
        else ""
    )

    print(
        f"[EVENT] {event.name}{task}"
    )

    if event.payload:
        for key, value in event.payload.items():
            print(f"        {key}: {value}")


def build_demo_plan() -> dict:
    """
    LLM-plan-shaped input.

    In the actual panel demonstration this can later be replaced by the
    real LLM team's LLMPlan output.
    """

    return {
        "goal": "Process a user information request",
        "summary": (
            "Demonstrate the complete JARVIS Agent Brain orchestration "
            "pipeline from LLM plan to execution boundary."
        ),
        "missing_information": [],
        "tasks": [
            "Open application",
            "Search for requested information",
            "Process the obtained information",
        ],
    }


def print_result(result, dispatcher: DemoDispatcher, orchestrator) -> None:

    print_banner("AGENT BRAIN EXECUTION RESULT")

    print("Request ID")
    print(SUB_LINE)
    print(result.request_id)

    print()
    print("Overall Result")
    print(SUB_LINE)
    print(result.status)

    print()
    print("Planning")
    print(SUB_LINE)

    if result.planning_result:
        print(
            f"Total Steps : "
            f"{result.planning_result.total_steps}"
        )
        print(
            f"Plan Valid  : "
            f"{result.planning_result.is_valid}"
        )

    print()
    print("Execution Outcomes")
    print(SUB_LINE)

    for outcome in result.outcomes:
        print(
            f"Task {outcome.task_id} | "
            f"Attempt {outcome.attempt} | "
            f"Success {outcome.success} | "
            f"Status {outcome.status}"
        )

    print()
    print("Decision Results")
    print(SUB_LINE)

    for decision in result.decisions:
        print(
            f"Task {decision.task_id} | "
            f"Decision {decision.action.value} | "
            f"Reason: {decision.reason}"
        )

    print()
    print("Runtime States")
    print(SUB_LINE)

    for task_id in dispatcher.calls:
        actual_task_id = task_id[0]
        state = result.context

        # State is displayed through the orchestrator's StateManager below.
        del state

        print(
            f"Task {actual_task_id} | "
            f"{orchestrator.state_manager.get_status(actual_task_id)}"
        )

    print()
    print("Dispatcher Calls")
    print(SUB_LINE)

    for task_id, attempt in dispatcher.calls:
        print(
            f"Task {task_id} → Attempt {attempt}"
        )

    print()
    print("Execution Boundary")
    print(SUB_LINE)
    print("Agent Brain              : COMPLETE")
    print("Action Dispatcher        : REACHED")
    print("Automation Engine        : NOT IMPLEMENTED")
    print("Module 5                 : NEXT DEVELOPMENT MODULE")


def main() -> None:

    logging.basicConfig(
        level=logging.WARNING,
        format="%(message)s",
    )

    print_banner("JARVIS AGENT BRAIN — LIVE ORCHESTRATION DEMO")

    print("Purpose")
    print(SUB_LINE)
    print(
        "Demonstrating the real Agent Brain pipeline and its "
        "execution boundary."
    )

    print()
    print("Automation Status")
    print(SUB_LINE)
    print(
        "Module 5 automation is intentionally NOT executed."
    )

    event_bus = EventBus()
    dispatcher = DemoDispatcher()

    event_bus.subscribe("*", print_event)

    orchestrator = AgentOrchestrator(
        dispatcher,
        event_bus=event_bus,
        execution_mode=ExecutionMode.SEQUENTIAL,
    )

    print()
    print("Starting Agent Brain...")
    print(SUB_LINE)

    result = orchestrator.run(build_demo_plan())

    print_result(result, dispatcher, orchestrator)

    print()
    print_banner("AGENT BRAIN DEMO COMPLETE")


if __name__ == "__main__":
    main()