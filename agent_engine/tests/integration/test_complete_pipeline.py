"""
===============================================================================
File Name   : test_complete_pipeline.py
Module      : Integration Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
End-to-end integration tests for the JARVIS Agent Brain pipeline.

Pipeline:

    LLM Plan
        ↓
    Basic Validator
        ↓
    Interpreter
        ↓
    Graph Builder
        ↓
    Graph Validator
        ↓
    Planner

B2.13 verifies that the complete Agent Brain pipeline works correctly and
that the validated execution graph can be consumed by the Planner.

Author : Team JARVIS
===============================================================================
"""

from agent_engine.agent_brain.validator import BasicValidator
from agent_engine.agent_brain.interpreter import Interpreter
from agent_engine.agent_brain.graph_builder import GraphBuilder
from agent_engine.agent_brain.planner import Planner

from agent_engine.agent_brain.models.llm_plan import LLMPlan
from agent_engine.agent_brain.models.processing_context import ProcessingContext


# =============================================================================
# Test Data
# =============================================================================

def build_llm_plan() -> LLMPlan:
    """
    Creates a realistic multi-step LLM plan for integration testing.
    """

    return LLMPlan(
        goal="Summarize the latest PDF of Spring AI tutorial",

        summary=(
            "Open browser, perform search for Spring AI tutorial, "
            "download the latest PDF and summarize it."
        ),

        missing_information=[
            "URL or specific source for Spring AI tutorial"
        ],

        tasks=[
            "Open Chrome",
            "Search for Spring AI tutorial URL",
            "Navigate to the found URL",
            "Download the latest PDF available",
            "Summarize the downloaded PDF",
        ],
    )


# =============================================================================
# Pipeline Context
# =============================================================================

def build_pipeline_context(
    plan: LLMPlan,
) -> ProcessingContext:
    """
    Creates the ProcessingContext used by the Agent Brain pipeline.
    """

    return ProcessingContext(
        llm_plan=plan
    )


# =============================================================================
# B2.13 — Complete Pipeline Integration
# =============================================================================

def test_complete_pipeline():

    # -------------------------------------------------------------------------
    # Stage 0 — LLM Plan
    # -------------------------------------------------------------------------

    plan = build_llm_plan()

    context = build_pipeline_context(plan)

    assert context.llm_plan is plan

    # -------------------------------------------------------------------------
    # Stage 1 — Basic Validator
    # -------------------------------------------------------------------------

    validator = BasicValidator()

    validation_result = validator.validate(plan)

    assert validation_result is not None
    assert validation_result.is_valid is True
    assert validation_result.errors == []

    # -------------------------------------------------------------------------
    # Stage 2 — Interpreter
    # -------------------------------------------------------------------------

    interpreter = Interpreter()

    context = interpreter.interpret(context)

    assert context.interpreted_tasks is not None

    assert len(context.interpreted_tasks) == 5

    # Task IDs should remain deterministic.
    task_ids = [
        task.task_id
        for task in context.interpreted_tasks
    ]

    assert task_ids == [1, 2, 3, 4, 5]

    # -------------------------------------------------------------------------
    # Stage 3 — Graph Builder
    # -------------------------------------------------------------------------

    graph_builder = GraphBuilder()

    context = graph_builder.build(context)

    graph = context.execution_graph

    assert graph is not None

    # One execution node per interpreted task.
    assert graph.node_count == 5

    assert graph.node_count == len(
        context.interpreted_tasks
    )

    # -------------------------------------------------------------------------
    # Stage 3A — Graph Validation
    # -------------------------------------------------------------------------

    graph_validation = context.graph_validation_result

    assert graph_validation is not None

    assert graph_validation.is_valid is True

    assert graph_validation.node_count == graph.node_count

    assert graph_validation.error_count == 0

    # -------------------------------------------------------------------------
    # Stage 3B — Graph Structural Integrity
    # -------------------------------------------------------------------------

    for node_id, node in graph.nodes.items():

        # Node ID must match dictionary key.
        assert node.node_id == node_id

        # Node ID must match interpreted task ID.
        assert node.task.task_id == node_id

        # No self dependency.
        assert node_id not in node.parents

        assert node_id not in node.children

        # Parent-child symmetry.
        for parent_id in node.parents:

            parent = graph.get_node(parent_id)

            assert parent is not None

            assert node_id in parent.children

        # Child-parent symmetry.
        for child_id in node.children:

            child = graph.get_node(child_id)

            assert child is not None

            assert node_id in child.parents

    # -------------------------------------------------------------------------
    # Stage 3C — Dependency Metadata
    # -------------------------------------------------------------------------

    for dependency_key in graph.dependency_metadata:

        parent_id, child_id = map(
            int,
            dependency_key.split("->")
        )

        parent = graph.get_node(parent_id)

        child = graph.get_node(child_id)

        assert parent is not None

        assert child is not None

        assert child_id in parent.children

        assert parent_id in child.parents

    # -------------------------------------------------------------------------
    # Stage 4 — Planner
    # -------------------------------------------------------------------------

    planner = Planner()

    context = planner.plan(context)

    # -------------------------------------------------------------------------
    # Planner Output
    # -------------------------------------------------------------------------

    assert context.execution_plan is not None

    execution_plan = context.execution_plan

    assert execution_plan.is_valid is True

    assert execution_plan.total_steps == graph.node_count

    # -------------------------------------------------------------------------
    # Final Pipeline State
    # -------------------------------------------------------------------------

    assert context.execution_graph is graph

    assert context.graph_validation_result is graph_validation

    assert context.execution_plan is execution_plan