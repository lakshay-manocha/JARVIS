"""
===============================================================================
File Name   : test_graph_validator.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Tests for B-5 — DAG Validation.
===============================================================================
"""

from agent_engine.agent_brain.graph_validator import GraphValidator
from agent_engine.agent_brain.models.execution_graph import ExecutionGraph
from agent_engine.agent_brain.models.execution_node import ExecutionNode
from agent_engine.agent_brain.models.interpreted_task import InterpretedTask


# =============================================================================
# Helpers
# =============================================================================

def create_task(task_id: int) -> InterpretedTask:

    return InterpretedTask(
        task_id=task_id,
        original_text=f"Task {task_id}",
        normalized_text=f"task {task_id}",
        action="open",
        tool="desktop_agent",
    )


def create_graph(task_ids: list[int]) -> ExecutionGraph:

    graph = ExecutionGraph()

    for task_id in task_ids:

        graph.add_node(
            ExecutionNode(
                node_id=task_id,
                task=create_task(task_id),
            )
        )

    return graph


def add_edge(
    graph: ExecutionGraph,
    parent_id: int,
    child_id: int,
) -> None:

    graph.add_dependency(
        parent_id=parent_id,
        child_id=child_id,
        dependency_type="test",
        confidence=1.0,
        reason="B5 test dependency",
    )


def validator() -> GraphValidator:

    return GraphValidator()


# =============================================================================
# Valid DAGs
# =============================================================================

def test_linear_dag_is_valid():

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 2)
    add_edge(graph, 2, 3)

    result = validator().validate(graph)

    assert result.is_valid is True
    assert result.errors == []


def test_branching_dag_is_valid():

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 2)
    add_edge(graph, 1, 3)

    result = validator().validate(graph)

    assert result.is_valid is True


def test_merging_dag_is_valid():

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 3)
    add_edge(graph, 2, 3)

    result = validator().validate(graph)

    assert result.is_valid is True


def test_complex_dag_is_valid():

    graph = create_graph([1, 2, 3, 4, 5])

    add_edge(graph, 1, 2)
    add_edge(graph, 1, 3)
    add_edge(graph, 2, 5)
    add_edge(graph, 3, 4)
    add_edge(graph, 3, 5)

    result = validator().validate(graph)

    assert result.is_valid is True


# =============================================================================
# Empty Graph
# =============================================================================

def test_empty_graph_is_handled():

    graph = ExecutionGraph()

    result = validator().validate(graph)

    assert result.is_valid is True
    assert result.node_count == 0
    assert result.edge_count == 0
    assert result.metadata["status"] == "empty_graph"
    assert result.metadata["cycle_detected"] is False


# =============================================================================
# Node Integrity
# =============================================================================

def test_node_count_is_recorded():

    graph = create_graph([1, 2, 3])

    result = validator().validate(graph)

    assert result.node_count == 3


def test_edge_count_is_recorded():

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 2)
    add_edge(graph, 2, 3)

    result = validator().validate(graph)

    assert result.edge_count == 2


# =============================================================================
# Self Dependency
# =============================================================================

def test_self_dependency_is_invalid():

    graph = create_graph([1])

    graph.nodes[1].parents.append(1)
    graph.nodes[1].children.append(1)

    result = validator().validate(graph)

    assert result.is_valid is False

    assert any(
        "Self-dependency detected" in error
        for error in result.errors
    )


# =============================================================================
# Missing References
# =============================================================================

def test_missing_parent_is_invalid():

    graph = create_graph([1])

    graph.nodes[1].parents.append(99)

    result = validator().validate(graph)

    assert result.is_valid is False

    assert any(
        "missing parent Task 99" in error
        for error in result.errors
    )


def test_missing_child_is_invalid():

    graph = create_graph([1])

    graph.nodes[1].children.append(99)

    result = validator().validate(graph)

    assert result.is_valid is False

    assert any(
        "missing child Task 99" in error
        for error in result.errors
    )


# =============================================================================
# Parent / Child Symmetry
# =============================================================================

def test_parent_child_asymmetry_is_invalid():

    graph = create_graph([1, 2])

    graph.nodes[2].parents.append(1)

    result = validator().validate(graph)

    assert result.is_valid is False

    assert any(
        "does not list Task 2 as child" in error
        for error in result.errors
    )


def test_child_parent_asymmetry_is_invalid():

    graph = create_graph([1, 2])

    graph.nodes[1].children.append(2)

    result = validator().validate(graph)

    assert result.is_valid is False

    assert any(
        "does not list Task 1 as parent" in error
        for error in result.errors
    )


# =============================================================================
# Duplicate Dependencies
# =============================================================================

def test_duplicate_parent_dependency_is_invalid():

    graph = create_graph([1, 2])

    graph.nodes[2].parents.extend([1, 1])

    result = validator().validate(graph)

    assert result.is_valid is False

    assert any(
        "duplicate parent dependencies" in error
        for error in result.errors
    )


def test_duplicate_child_dependency_is_invalid():

    graph = create_graph([1, 2])

    graph.nodes[1].children.extend([2, 2])

    result = validator().validate(graph)

    assert result.is_valid is False

    assert any(
        "duplicate child dependencies" in error
        for error in result.errors
    )


# =============================================================================
# Cycle Detection
# =============================================================================

def test_two_node_cycle_is_invalid():

    graph = create_graph([1, 2])

    add_edge(graph, 1, 2)
    add_edge(graph, 2, 1)

    result = validator().validate(graph)

    assert result.is_valid is False
    assert result.metadata["cycle_detected"] is True


def test_three_node_cycle_is_invalid():

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 2)
    add_edge(graph, 2, 3)
    add_edge(graph, 3, 1)

    result = validator().validate(graph)

    assert result.is_valid is False
    assert result.metadata["cycle_detected"] is True


def test_cycle_nodes_are_recorded():

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 2)
    add_edge(graph, 2, 3)
    add_edge(graph, 3, 1)

    result = validator().validate(graph)

    assert result.metadata["cycle_nodes"] == [1, 2, 3]


# =============================================================================
# Root / Leaf Validation
# =============================================================================

def test_valid_graph_has_root():

    graph = create_graph([1, 2])

    add_edge(graph, 1, 2)

    result = validator().validate(graph)

    assert result.metadata["root_count"] == 1
    assert result.metadata["root_nodes"] == [1]


def test_valid_graph_has_leaf():

    graph = create_graph([1, 2])

    add_edge(graph, 1, 2)

    result = validator().validate(graph)

    assert result.metadata["leaf_count"] == 1
    assert result.metadata["leaf_nodes"] == [2]


def test_branching_graph_root_leaf_metadata():

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 2)
    add_edge(graph, 1, 3)

    result = validator().validate(graph)

    assert result.metadata["root_nodes"] == [1]
    assert set(result.metadata["leaf_nodes"]) == {2, 3}


# =============================================================================
# Metadata
# =============================================================================

def test_valid_graph_metadata():

    graph = create_graph([1, 2])

    add_edge(graph, 1, 2)

    result = validator().validate(graph)

    assert result.metadata["validator"] == "GraphValidator"
    assert result.metadata["status"] == "valid"
    assert result.metadata["cycle_detected"] is False


def test_invalid_graph_metadata():

    graph = create_graph([1, 2])

    add_edge(graph, 1, 2)
    add_edge(graph, 2, 1)

    result = validator().validate(graph)

    assert result.metadata["validator"] == "GraphValidator"
    assert result.metadata["status"] == "invalid"
    assert result.metadata["cycle_detected"] is True


# =============================================================================
# Final Integrity
# =============================================================================

def test_valid_dag_has_no_errors():

    graph = create_graph([1, 2, 3, 4])

    add_edge(graph, 1, 2)
    add_edge(graph, 1, 3)
    add_edge(graph, 2, 4)
    add_edge(graph, 3, 4)

    result = validator().validate(graph)

    assert result.is_valid is True
    assert result.error_count == 0


def test_invalid_dag_has_errors():

    graph = create_graph([1, 2])

    add_edge(graph, 1, 2)
    add_edge(graph, 2, 1)

    result = validator().validate(graph)

    assert result.is_valid is False
    assert result.error_count > 0