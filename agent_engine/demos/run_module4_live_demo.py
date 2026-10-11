"""
===============================================================================
File Name   : run_module4_live_demo.py
Module      : Module 4 - Agent Brain Demonstration
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Single live terminal demonstration of the completed Agent Brain.

The runner presents the complete Module 4 pipeline:

    LLM Plan
        ↓
    Validation
        ↓
    Interpretation
        ↓
    Graph Construction
        ↓
    Graph Validation
        ↓
    Planning
        ↓
    Orchestration
        ↓
    Decision Manager
        ↓
    State Manager
        ↓
    Action Dispatcher Boundary
        ↓
    Module 5 Automation

This file is presentation/integration code only.

It does not implement Automation Engine functionality.
===============================================================================
"""

from __future__ import annotations

import logging

from agent_engine.agent_brain.models.processing_context import ProcessingContext
from agent_engine.agent_brain.validator import BasicValidator
from agent_engine.agent_brain.interpreter import Interpreter
from agent_engine.agent_brain.graph_builder import GraphBuilder
from agent_engine.agent_brain.planner import Planner

from agent_engine.contracts.enums import (
    ExecutionMode,
    ProcessingStage,
)

from agent_engine.dispatcher.demo_dispatcher import DemoDispatcher
from agent_engine.events.event_bus import AgentEvent, EventBus
from agent_engine.orchestration.agent_orchestrator import AgentOrchestrator

from agent_engine.tests.integration.sample_llm_outputs import SPRING_AI_CASE


# =============================================================================
# Formatting
# =============================================================================

LINE = "═" * 90
SUB_LINE = "-" * 90


def banner(title: str) -> None:
    print()
    print(LINE)
    print(title.center(90))
    print(LINE)


def section(title: str) -> None:
    print()
    print(title)
    print(SUB_LINE)


# =============================================================================
# Event display
# =============================================================================

def print_event(event: AgentEvent) -> None:
    """
    Print actual events emitted by AgentOrchestrator.

    These are not simulated presentation messages.
    They come directly from the EventBus.
    """

    task_suffix = (
        f" | Task {event.task_id}"
        if event.task_id is not None
        else ""
    )

    print(f"[EVENT] {event.name}{task_suffix}")

    for key, value in event.payload.items():
        print(f"        {key}: {value}")


# =============================================================================
# Phase A-E preparation
# =============================================================================

def prepare_agent_brain() -> ProcessingContext:
    """
    Run the existing Agent Brain preparation stages.

    No logic is reimplemented here. Existing Phase A-E components remain
    authoritative.
    """

    context = ProcessingContext(
        llm_plan=SPRING_AI_CASE
    )

    # -------------------------------------------------------------------------
    # Stage 1 - Validation
    # -------------------------------------------------------------------------

    banner("STAGE 1 : VALIDATION")

    validator = BasicValidator()
    validation = validator.validate(context.llm_plan)

    print(f"Valid         : {validation.is_valid}")
    print(f"Error Count   : {len(validation.errors)}")

    if not validation.is_valid:
        raise RuntimeError(
            "LLM plan validation failed; Agent Brain cannot continue."
        )

    print("Validation Status : PASSED")

    # -------------------------------------------------------------------------
    # Stage 2 - Interpretation
    # -------------------------------------------------------------------------

    banner("STAGE 2 : INTERPRETATION")

    interpreter = Interpreter()
    context = interpreter.interpret(context)

    print(f"Tasks Interpreted : {len(context.interpreted_tasks)}")

    for task in context.interpreted_tasks:
        print()
        print(f"Task {task.task_id}")
        print(SUB_LINE)
        print(f"Original Text   : {task.original_text}")
        print(f"Normalized Text : {task.normalized_text}")
        print(f"Action          : {task.action}")
        print(f"Tool            : {task.tool}")

    # -------------------------------------------------------------------------
    # Stage 3 - Graph Construction
    # -------------------------------------------------------------------------

    banner("STAGE 3 : GRAPH BUILDER")

    graph_builder = GraphBuilder()
    context = graph_builder.build(context)

    graph = context.execution_graph

    print(f"Node Count : {graph.node_count}")

    print("\nRoot Nodes")
    for node in graph.root_nodes:
        print(f"• Node {node.node_id}")

    print("\nLeaf Nodes")
    for node in graph.leaf_nodes:
        print(f"• Node {node.node_id}")

    print("\nExecution Graph")

    for node in graph.nodes.values():
        print()
        print(f"Node {node.node_id}")
        print(f"Task     : {node.task.original_text}")
        print(f"Parents  : {node.parents}")
        print(f"Children : {node.children}")

    # -------------------------------------------------------------------------
    # Stage 3A - Graph Validation
    # -------------------------------------------------------------------------

    banner("STAGE 3A : GRAPH VALIDATION")

    if context.graph_validation_result is None:
        raise RuntimeError(
            "Graph validation result was not produced."
        )

    graph_validation = context.graph_validation_result

    print(f"Graph Valid : {graph_validation.is_valid}")
    print(f"Node Count  : {graph.node_count}")
    print(f"Error Count : {len(graph_validation.errors)}")

    if not graph_validation.is_valid:
        raise RuntimeError(
            "Execution graph validation failed; Agent Brain cannot continue."
        )

    print("\nGraph Validation Status : PASSED")

    # -------------------------------------------------------------------------
    # Stage 4 - Planner
    # -------------------------------------------------------------------------

    banner("STAGE 4 : PLANNER")

    planner = Planner()
    context = planner.plan(context)

    planning = context.execution_plan

    if planning is None:
        raise RuntimeError(
            "Planner did not produce an execution plan."
        )

    print(f"Plan Valid       : {planning.is_valid}")
    print(f"Total Steps      : {planning.total_steps}")
    print(f"Estimated Time   : {planning.estimated_time}")

    print("\nExecution Order")

    for node in planning.execution_order:
        print(
            f"{node.node_id}. "
            f"{node.task.original_text}"
        )

    print("\nParallel Groups")

    if planning.parallel_groups:
        for level, group in enumerate(
            planning.parallel_groups,
            start=1,
        ):
            print(f"Level {level} : {group}")
    else:
        print("None")

    return context


# =============================================================================
# Phase F
# =============================================================================

def run_orchestration(context: ProcessingContext):
    """
    Continue the already-prepared Agent Brain context through Phase F.

    The same ProcessingContext is handed to AgentOrchestrator so the
    orchestration layer operates on the real Phase A-E results.
    """

    banner("STAGE 5 : AGENT ORCHESTRATOR")

    dispatcher = DemoDispatcher()
    event_bus = EventBus()

    event_bus.subscribe(
        "*",
        print_event,
    )

    orchestrator = AgentOrchestrator(
        dispatcher,
        event_bus=event_bus,
        execution_mode=ExecutionMode.SEQUENTIAL,
    )

    result = orchestrator.run(context)

    return result, orchestrator, dispatcher


# =============================================================================
# Final result
# =============================================================================

def print_final_result(
    result,
    orchestrator: AgentOrchestrator,
    dispatcher: DemoDispatcher,
) -> None:

    banner("AGENT BRAIN EXECUTION RESULT")

    section("Request")
    print(f"Request ID : {result.request_id}")

    section("Overall Result")
    print(f"Status : {result.status}")

    section("Execution Outcomes")

    if result.outcomes:
        for outcome in result.outcomes:
            print(
                f"Task {outcome.task_id}"
                f" | Attempt {outcome.attempt}"
                f" | Success {outcome.success}"
                f" | Status {outcome.status}"
            )
    else:
        print("No execution outcomes.")

    section("Decision Results")

    if result.decisions:
        for decision in result.decisions:
            print(
                f"Task {decision.task_id}"
                f" | Decision {decision.action.value}"
                f" | Reason: {decision.reason}"
            )
    else:
        print("No decisions.")

    section("Runtime State")

    if result.planning_result:
        for node in result.planning_result.execution_order:
            task_id = node.node_id
            status = orchestrator.state_manager.get_status(task_id)

            print(
                f"Task {task_id}"
                f" | {status}"
            )

    section("Dispatcher Activity")

    if dispatcher.calls:
        for task_id, attempt in dispatcher.calls:
            print(
                f"Task {task_id}"
                f" → Attempt {attempt}"
            )
    else:
        print("Dispatcher was not invoked.")

    section("Agent Brain Completion")

    print("LLM Plan           : RECEIVED")
    print("Validation         : PASSED")
    print("Interpretation     : COMPLETED")
    print("Graph Construction : COMPLETED")
    print("Graph Validation   : PASSED")
    print("Planning           : COMPLETED")
    print("Orchestration      : COMPLETED")
    print("Decision Manager   : COMPLETED")
    print("State Manager      : COMPLETED")

    if result.planning_result:
        print(
            f"Execution Graph    : "
            f"READY ({result.planning_result.total_steps} steps)"
        )
        print("Execution Plan     : READY")

    section("Execution Boundary")

    print("Agent Brain        : COMPLETE")
    print("Action Dispatcher  : REACHED")
    print("Automation Engine  : NOT IMPLEMENTED")
    print("Module 5           : NEXT DEVELOPMENT MODULE")


# =============================================================================
# Main
# =============================================================================

def main() -> None:

    # Keep standard-library logging quiet during the panel demonstration.
    logging.basicConfig(
        level=logging.WARNING,
        format="%(message)s",
    )

    banner("JARVIS — MODULE 4 : AGENT BRAIN LIVE DEMONSTRATION")

    section("Demonstration Scope")

    print(
        "This demonstration executes the completed Agent Brain pipeline."
    )

    print(
        "The Action Dispatcher boundary is exercised using the development"
        " dispatcher."
    )

    print(
        "No external browser, desktop, or environment automation is performed."
    )

    # -------------------------------------------------------------------------
    # Display LLM plan
    # -------------------------------------------------------------------------

    banner("STAGE 0 : LLM PLAN RECEIVED")

    print("Goal")
    print(SUB_LINE)
    print(SPRING_AI_CASE.goal)

    print("\nSummary")
    print(SUB_LINE)
    print(SPRING_AI_CASE.summary)

    print("\nMissing Information")
    print(SUB_LINE)

    if SPRING_AI_CASE.missing_information:
        for item in SPRING_AI_CASE.missing_information:
            print(f"• {item}")
    else:
        print("None")

    print("\nTasks")
    print(SUB_LINE)

    for index, task in enumerate(
        SPRING_AI_CASE.tasks,
        start=1,
    ):
        print(f"{index}. {task}")

    # -------------------------------------------------------------------------
    # Run Agent Brain preparation
    # -------------------------------------------------------------------------

    context = prepare_agent_brain()

    # -------------------------------------------------------------------------
    # Run Phase F
    # -------------------------------------------------------------------------

    result, orchestrator, dispatcher = run_orchestration(
        context
    )

    # -------------------------------------------------------------------------
    # Final result
    # -------------------------------------------------------------------------

    print_final_result(
        result,
        orchestrator,
        dispatcher,
    )

    banner("MODULE 4 : AGENT BRAIN DEMONSTRATION COMPLETE")


if __name__ == "__main__":
    main()