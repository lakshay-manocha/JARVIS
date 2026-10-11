"""
===============================================================================
File Name   : test_graph_validator_cycles.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Tests for B-3:
    Circular Dependency Detection
===============================================================================
"""

import pytest

from agent_engine.agent_brain.graph_validator import GraphValidator
from agent_engine.agent_brain.models.execution_graph import ExecutionGraph
from agent_engine.agent_brain.models.execution_node import ExecutionNode
from agent_engine.agent_brain.models.interpreted_task import InterpretedTask


# =============================================================================
# Helpers
# =============================================================================

def create_node(task_id: int) -> ExecutionNode:
    """
    Create a minimal valid execution node.
    """

    task = InterpretedTask(
        task_id=task_id,
        original_text=f"Task {task_id}",
        normalized_text=f"task {task_id}",
        action="open",
        tool="desktop_agent",
    )

    return ExecutionNode(
        node_id=task_id,
        task=task,
    )


def create_graph(task_count: int) -> ExecutionGraph:
    """
    Create an execution graph containing the requested number of nodes.
    """

    graph = ExecutionGraph()

    for task_id in range(1, task_count + 1):

        graph.add_node(
            create_node(task_id)
        )

    return graph


# =============================================================================
# No Cycle
# =============================================================================

def test_linear_graph_has_no_cycle():
    """
    B-3: A simple linear DAG must not be detected as cyclic.

    1 -> 2 -> 3
    """

    graph = create_graph(3)

    graph.add_dependency(1, 2)
    graph.add_dependency(2, 3)

    validator = GraphValidator()

    result = validator.validate(graph)

    assert result.is_valid is True

    assert validator._find_cycle_nodes(graph) == []


# =============================================================================
# Two Node Cycle
# =============================================================================

def test_two_node_cycle_is_detected():
    """
    B-3: Detect a two-node circular dependency.

    1 -> 2
    2 -> 1
    """

    graph = create_graph(2)

    graph.add_dependency(1, 2)

    # Manually create reverse edge because ExecutionGraph represents
    # dependency creation as a normal DAG-building operation and the
    # test intentionally constructs an invalid graph.
    graph.get_node(2).add_child(1)
    graph.get_node(1).add_parent(2)

    validator = GraphValidator()

    cycle_nodes = validator._find_cycle_nodes(graph)

    assert cycle_nodes == [1, 2]


def test_two_node_cycle_invalidates_graph():
    """
    B-3: A graph containing a two-node cycle must be invalid.
    """

    graph = create_graph(2)

    graph.add_dependency(1, 2)

    graph.get_node(2).add_child(1)
    graph.get_node(1).add_parent(2)

    validator = GraphValidator()

    result = validator.validate(graph)

    assert result.is_valid is False

    assert any(
        "circular dependency" in error.lower()
        for error in result.errors
    )


# =============================================================================
# Three Node Cycle
# =============================================================================

def test_three_node_cycle_is_detected():
    """
    B-3: Detect a three-node circular dependency.

    1 -> 2 -> 3 -> 1
    """

    graph = create_graph(3)

    graph.add_dependency(1, 2)
    graph.add_dependency(2, 3)

    graph.get_node(3).add_child(1)
    graph.get_node(1).add_parent(3)

    validator = GraphValidator()

    cycle_nodes = validator._find_cycle_nodes(graph)

    assert cycle_nodes == [1, 2, 3]


def test_three_node_cycle_invalidates_graph():
    """
    B-3: A three-node cycle must invalidate the graph.
    """

    graph = create_graph(3)

    graph.add_dependency(1, 2)
    graph.add_dependency(2, 3)

    graph.get_node(3).add_child(1)
    graph.get_node(1).add_parent(3)

    validator = GraphValidator()

    result = validator.validate(graph)

    assert result.is_valid is False

    assert any(
        "circular dependency" in error.lower()
        for error in result.errors
    )


# =============================================================================
# Cycle Inside Larger Graph
# =============================================================================

def test_cycle_inside_larger_graph_is_detected():
    """
    B-3: Detect a cycle that exists inside a larger graph.

    1 -> 2 -> 3
         ↑    |
         |    ↓
         5 <- 4

    Task 1 is outside the cycle.
    """

    graph = create_graph(5)

    graph.add_dependency(1, 2)
    graph.add_dependency(2, 3)
    graph.add_dependency(3, 4)
    graph.add_dependency(4, 5)

    # Close the cycle: 5 -> 2
    graph.get_node(5).add_child(2)
    graph.get_node(2).add_parent(5)

    validator = GraphValidator()

    cycle_nodes = validator._find_cycle_nodes(graph)

    assert cycle_nodes == [2, 3, 4, 5]


# =============================================================================
# Branching DAG
# =============================================================================

def test_branching_dag_is_not_detected_as_cycle():
    """
    B-3: A valid branching DAG must remain valid.

            2
           / \
    1 ----      4
           \ /
            3

    Actual graph:

    1 -> 2 -> 4
    1 -> 3 -> 4
    """

    graph = create_graph(4)

    graph.add_dependency(1, 2)
    graph.add_dependency(1, 3)
    graph.add_dependency(2, 4)
    graph.add_dependency(3, 4)

    validator = GraphValidator()

    cycle_nodes = validator._find_cycle_nodes(graph)

    assert cycle_nodes == []


def test_branching_dag_is_valid():
    """
    B-3: Branching without circular dependencies must validate.
    """

    graph = create_graph(4)

    graph.add_dependency(1, 2)
    graph.add_dependency(1, 3)
    graph.add_dependency(2, 4)
    graph.add_dependency(3, 4)

    validator = GraphValidator()

    result = validator.validate(graph)

    assert result.is_valid is True


# =============================================================================
# Disconnected Components
# =============================================================================

def test_disconnected_acyclic_components_are_valid():
    """
    B-3: Multiple independent DAG components must not be considered cyclic.

    Component 1:
        1 -> 2

    Component 2:
        3 -> 4
    """

    graph = create_graph(4)

    graph.add_dependency(1, 2)
    graph.add_dependency(3, 4)

    validator = GraphValidator()

    cycle_nodes = validator._find_cycle_nodes(graph)

    assert cycle_nodes == []


# =============================================================================
# Self Dependency
# =============================================================================

def test_self_dependency_is_rejected_by_graph():
    """
    B-3: ExecutionGraph must reject a direct self-dependency.
    """

    graph = create_graph(1)

    with pytest.raises(ValueError):

        graph.add_dependency(
            parent_id=1,
            child_id=1,
        )


# =============================================================================
# Metadata
# =============================================================================

def test_cycle_detection_metadata_is_recorded():
    """
    B-3: Validation metadata should identify cycle detection status.
    """

    graph = create_graph(3)

    graph.add_dependency(1, 2)
    graph.add_dependency(2, 3)

    graph.get_node(3).add_child(1)
    graph.get_node(1).add_parent(3)

    validator = GraphValidator()

    result = validator.validate(graph)

    assert result.metadata["cycle_detected"] is True

    assert result.metadata["cycle_nodes"] == [1, 2, 3]


def test_no_cycle_metadata_is_recorded():
    """
    B-3: A valid DAG should report no cycle.
    """

    graph = create_graph(3)

    graph.add_dependency(1, 2)
    graph.add_dependency(2, 3)

    validator = GraphValidator()

    result = validator.validate(graph)

    assert result.metadata["cycle_detected"] is False

    assert result.metadata["cycle_nodes"] == []