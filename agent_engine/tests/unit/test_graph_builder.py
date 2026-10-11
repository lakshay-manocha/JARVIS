"""
===============================================================================
File Name   : test_graph_builder.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Unit tests for GraphBuilder.

B2.12 — Graph Builder Unit Tests

Tests:
    • Graph creation
    • Correct node count
    • Node ordering
    • Dependency creation
    • Parent/child synchronization
    • Root node detection
    • Leaf node detection
    • Processing stage update
    • Processing logs
    • Graph storage in ProcessingContext
    • Same-context return behavior
    • Graph validation integration
    • Validation result storage
    • Dependency metadata preservation
    • No self-dependencies
    • No duplicate dependencies

Author : Team JARVIS
===============================================================================
"""

import pytest
from pydantic import ValidationError
from agent_engine.agent_brain.graph_builder import GraphBuilder
from agent_engine.agent_brain.models.interpreted_task import InterpretedTask
from agent_engine.agent_brain.models.processing_context import ProcessingContext
from agent_engine.agent_brain.models.llm_plan import LLMPlan
from agent_engine.contracts.enums import ProcessingStage


# =============================================================================
# Test Data Helpers
# =============================================================================

def build_context(task_count: int = 3) -> ProcessingContext:
    """
    Creates a ProcessingContext containing a configurable
    number of interpreted tasks.
    """

    tasks = []

    for i in range(task_count):

        tasks.append(
            InterpretedTask(
                task_id=i + 1,
                original_text=f"Task {i + 1}",
                normalized_text=f"task {i + 1}",
                action="open",
                tool="desktop_agent",
            )
        )

    context = ProcessingContext(
        llm_plan=LLMPlan(
            goal="Test Goal",
            summary="Test Summary",
            missing_information=[],
            tasks=[
                task.original_text
                for task in tasks
            ],
        )
    )

    context.interpreted_tasks = tasks

    return context


def build_builder() -> GraphBuilder:
    """
    Creates a GraphBuilder instance.
    """

    return GraphBuilder()


# =============================================================================
# B2.12 — Graph Creation
# =============================================================================

def test_graph_created():
    """
    GraphBuilder must create an execution graph.
    """

    builder = build_builder()
    context = build_context(3)

    result = builder.build(context)

    assert result.execution_graph is not None


def test_correct_number_of_nodes():
    """
    The execution graph must contain the same number
    of nodes as interpreted tasks.
    """

    builder = build_builder()
    context = build_context(5)

    result = builder.build(context)

    assert result.execution_graph.node_count == 5


def test_node_order():
    """
    Nodes should be stored using their task IDs.
    """

    builder = build_builder()
    context = build_context(4)

    result = builder.build(context)

    graph = result.execution_graph

    assert list(graph.nodes.keys()) == [1, 2, 3, 4]


def test_node_ids_match_task_ids():
    """
    Every graph node must preserve the corresponding
    interpreted task ID.
    """

    builder = build_builder()
    context = build_context(4)

    result = builder.build(context)

    graph = result.execution_graph

    for node_id, node in graph.nodes.items():

        assert node.node_id == node_id
        assert node.task.task_id == node_id


# =============================================================================
# B2.12 — Dependency Structure
# =============================================================================

def test_dependencies_are_consistent():
    """
    If dependencies are detected and accepted by the policy,
    parent/child relationships must remain synchronized.

    This test does NOT assume a sequential dependency structure.
    """

    builder = build_builder()
    context = build_context(5)

    result = builder.build(context)

    graph = result.execution_graph

    for node in graph.nodes.values():

        for child_id in node.children:

            child = graph.get_node(child_id)

            assert child is not None
            assert node.node_id in child.parents

        for parent_id in node.parents:

            parent = graph.get_node(parent_id)

            assert parent is not None
            assert node.node_id in parent.children


def test_no_self_dependencies():
    """
    A node must never depend on itself.
    """

    builder = build_builder()
    context = build_context(5)

    result = builder.build(context)

    graph = result.execution_graph

    for node in graph.nodes.values():

        assert node.node_id not in node.parents
        assert node.node_id not in node.children


def test_no_duplicate_parent_dependencies():
    """
    A node must not contain duplicate parent references.
    """

    builder = build_builder()
    context = build_context(5)

    result = builder.build(context)

    graph = result.execution_graph

    for node in graph.nodes.values():

        assert len(node.parents) == len(set(node.parents))


def test_no_duplicate_child_dependencies():
    """
    A node must not contain duplicate child references.
    """

    builder = build_builder()
    context = build_context(5)

    result = builder.build(context)

    graph = result.execution_graph

    for node in graph.nodes.values():

        assert len(node.children) == len(set(node.children))


# =============================================================================
# B2.12 — Root / Leaf Nodes
# =============================================================================

def test_root_nodes_are_consistent():
    """
    Every root node must have no parents.
    """

    builder = build_builder()
    context = build_context(5)

    result = builder.build(context)

    graph = result.execution_graph

    roots = graph.root_nodes

    for node in roots:

        assert node.parents == []


def test_leaf_nodes_are_consistent():
    """
    Every leaf node must have no children.
    """

    builder = build_builder()
    context = build_context(5)

    result = builder.build(context)

    graph = result.execution_graph

    leaves = graph.leaf_nodes

    for node in leaves:

        assert node.children == []


def test_root_and_leaf_nodes_belong_to_graph():
    """
    Root and leaf nodes must be actual graph nodes.
    """

    builder = build_builder()
    context = build_context(5)

    result = builder.build(context)

    graph = result.execution_graph

    for node in graph.root_nodes:

        assert node.node_id in graph.nodes

    for node in graph.leaf_nodes:

        assert node.node_id in graph.nodes


# =============================================================================
# B2.12 — Processing Context
# =============================================================================

def test_processing_stage_updated():
    """
    GraphBuilder must update the processing stage to GRAPH_BUILDING.
    """

    builder = build_builder()
    context = build_context()

    result = builder.build(context)

    assert result.current_stage == ProcessingStage.GRAPH_BUILDING


def test_graph_saved_in_context():
    """
    The generated execution graph must be stored
    inside ProcessingContext.
    """

    builder = build_builder()
    context = build_context()

    result = builder.build(context)

    assert result.execution_graph is not None


def test_returns_same_context():
    """
    GraphBuilder.build() should mutate and return the
    same ProcessingContext object.
    """

    builder = build_builder()
    context = build_context()

    result = builder.build(context)

    assert result is context


# =============================================================================
# B2.12 — Logging
# =============================================================================

def test_logs_created():
    """
    GraphBuilder must create processing logs.
    """

    builder = build_builder()
    context = build_context()

    result = builder.build(context)

    assert len(result.processing_logs) >= 2


def test_graph_building_log_exists():
    """
    The processing logs should indicate that graph building started.
    """

    builder = build_builder()
    context = build_context()

    result = builder.build(context)

    messages = [
        str(log)
        for log in result.processing_logs
    ]

    assert any(
        "Execution graph building started"
        in message
        for message in messages
    )


# =============================================================================
# B2.12 — Graph Validation Integration
# =============================================================================

def test_graph_validation_result_created():
    """
    GraphBuilder must execute GraphValidator after graph construction.
    """

    builder = build_builder()
    context = build_context()

    result = builder.build(context)

    assert result.graph_validation_result is not None


def test_graph_validation_result_is_valid():
    """
    A normally constructed graph should pass validation.
    """

    builder = build_builder()
    context = build_context()

    result = builder.build(context)

    validation = result.graph_validation_result

    assert validation is not None
    assert validation.is_valid is True


def test_graph_validation_node_count_matches_graph():
    """
    GraphValidator node count must match the generated graph.
    """

    builder = build_builder()
    context = build_context(5)

    result = builder.build(context)

    graph = result.execution_graph
    validation = result.graph_validation_result

    assert validation.node_count == graph.node_count


def test_graph_validation_edge_count_is_non_negative():
    """
    Validation must report a valid non-negative edge count.
    """

    builder = build_builder()
    context = build_context(5)

    result = builder.build(context)

    validation = result.graph_validation_result

    assert validation.edge_count >= 0


def test_graph_validation_has_no_errors_for_valid_graph():
    """
    A normally generated graph must not contain validation errors.
    """

    builder = build_builder()
    context = build_context(5)

    result = builder.build(context)

    validation = result.graph_validation_result

    assert validation.errors == []


# =============================================================================
# B2.12 — Dependency Metadata
# =============================================================================

def test_dependency_metadata_is_a_dictionary():
    """
    ExecutionGraph must expose dependency metadata
    without requiring a specific DependencyType enum.
    """

    builder = build_builder()
    context = build_context(5)

    result = builder.build(context)

    graph = result.execution_graph

    assert isinstance(
        graph.dependency_metadata,
        dict
    )


def test_dependency_metadata_matches_existing_edges():
    """
    Every stored dependency metadata entry must correspond
    to an actual graph edge.
    """

    builder = build_builder()
    context = build_context(5)

    result = builder.build(context)

    graph = result.execution_graph

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


# =============================================================================
# B2.12 — Empty Task Set
# =============================================================================

def test_graph_builder_requires_at_least_one_task():
    """
    Empty task sets are rejected by LLMPlan before GraphBuilder
    can construct an execution graph.
    """

    with pytest.raises(
        ValidationError,
        match="At least one task must be present",
    ):
        build_context(0)

# =============================================================================
# B2.12 — Single Task
# =============================================================================

def test_single_task_creates_single_node():
    """
    A single interpreted task should create exactly one graph node.
    """

    builder = build_builder()
    context = build_context(1)

    result = builder.build(context)

    graph = result.execution_graph

    assert graph.node_count == 1
    assert graph.get_node(1) is not None


def test_single_task_is_root_and_leaf():
    """
    A graph containing one task should have the same node
    as both root and leaf.
    """

    builder = build_builder()
    context = build_context(1)

    result = builder.build(context)

    graph = result.execution_graph

    assert len(graph.root_nodes) == 1
    assert len(graph.leaf_nodes) == 1

    assert graph.root_nodes[0].node_id == 1
    assert graph.leaf_nodes[0].node_id == 1


# =============================================================================
# B2.12 — Final Graph Integrity
# =============================================================================

def test_final_graph_is_valid():
    """
    Final graph produced by GraphBuilder must pass
    the integrated validation boundary.
    """

    builder = build_builder()
    context = build_context(6)

    result = builder.build(context)

    assert result.execution_graph is not None
    assert result.graph_validation_result is not None

    assert (
        result.graph_validation_result.is_valid
        is True
    )