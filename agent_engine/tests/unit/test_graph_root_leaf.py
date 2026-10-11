"""
===============================================================================
File Name   : test_graph_root_leaf.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Tests for B4 — Root / Leaf Detection for Branching DAGs.

B4 Requirements
---------------
    • Detect root nodes correctly.
    • Detect leaf nodes correctly.
    • Support branching DAGs.
    • Support merging DAGs.
    • Support multiple roots.
    • Support multiple leaves.
    • Support disconnected DAG components.
    • Support single-node graphs.
    • Recalculate root/leaf identifiers correctly.
    • Ensure root/leaf detection is based on actual parent/child
      relationships rather than task ordering.
===============================================================================
"""

import pytest

from agent_engine.agent_brain.models.execution_graph import ExecutionGraph
from agent_engine.agent_brain.models.execution_node import ExecutionNode
from agent_engine.agent_brain.models.interpreted_task import InterpretedTask


# =============================================================================
# Helper Functions
# =============================================================================

def create_task(task_id: int) -> InterpretedTask:
    """
    Create a minimal valid InterpretedTask for testing.
    """

    return InterpretedTask(
        task_id=task_id,
        original_text=f"Task {task_id}",
        normalized_text=f"task {task_id}",
        action="open",
        tool="desktop_agent",
    )


def create_graph(task_ids: list[int]) -> ExecutionGraph:
    """
    Create an ExecutionGraph containing nodes for the supplied task IDs.
    """

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
    """
    Add a dependency edge between two existing graph nodes.
    """

    graph.add_dependency(
        parent_id=parent_id,
        child_id=child_id,
        dependency_type="test",
        confidence=1.0,
        reason="B4 root/leaf test",
    )


# =============================================================================
# B4 — Basic Root Detection
# =============================================================================

def test_single_node_is_root():
    """
    A graph containing one node should identify that node as a root.
    """

    graph = create_graph([1])

    roots = graph.root_nodes

    assert len(roots) == 1
    assert roots[0].node_id == 1


def test_single_node_is_leaf():
    """
    A graph containing one node should identify that node as a leaf.
    """

    graph = create_graph([1])

    leaves = graph.leaf_nodes

    assert len(leaves) == 1
    assert leaves[0].node_id == 1


def test_single_node_is_both_root_and_leaf():
    """
    A standalone node has neither parents nor children, so it must be
    both a root and a leaf.
    """

    graph = create_graph([1])

    assert [node.node_id for node in graph.root_nodes] == [1]
    assert [node.node_id for node in graph.leaf_nodes] == [1]


# =============================================================================
# B4 — Linear DAG
# =============================================================================

def test_linear_graph_has_one_root():
    """
    For:

        1 -> 2 -> 3

    Task 1 is the only root.
    """

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 2)
    add_edge(graph, 2, 3)

    roots = [node.node_id for node in graph.root_nodes]

    assert roots == [1]


def test_linear_graph_has_one_leaf():
    """
    For:

        1 -> 2 -> 3

    Task 3 is the only leaf.
    """

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 2)
    add_edge(graph, 2, 3)

    leaves = [node.node_id for node in graph.leaf_nodes]

    assert leaves == [3]


def test_linear_graph_root_and_leaf_are_different():
    """
    In a multi-node linear DAG, the root and leaf should be different.
    """

    graph = create_graph([1, 2, 3, 4])

    add_edge(graph, 1, 2)
    add_edge(graph, 2, 3)
    add_edge(graph, 3, 4)

    roots = [node.node_id for node in graph.root_nodes]
    leaves = [node.node_id for node in graph.leaf_nodes]

    assert roots == [1]
    assert leaves == [4]


# =============================================================================
# B4 — Branching DAG
# =============================================================================

def test_branching_graph_detects_single_root():
    """
    For:

             2
            /
        1
            \
             3

    Task 1 is the only root.
    """

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 2)
    add_edge(graph, 1, 3)

    roots = [node.node_id for node in graph.root_nodes]

    assert roots == [1]


def test_branching_graph_detects_multiple_leaves():
    """
    For:

             -> 2
            /
        1
            \
             -> 3

    Tasks 2 and 3 are leaves.
    """

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 2)
    add_edge(graph, 1, 3)

    leaves = [node.node_id for node in graph.leaf_nodes]

    assert set(leaves) == {2, 3}
    assert len(leaves) == 2


def test_branching_graph_root_and_leaves_are_correct():
    """
    Verify both root and leaf detection for:

             2
            /
        1
            \
             3
    """

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 2)
    add_edge(graph, 1, 3)

    roots = [node.node_id for node in graph.root_nodes]
    leaves = [node.node_id for node in graph.leaf_nodes]

    assert roots == [1]
    assert set(leaves) == {2, 3}


# =============================================================================
# B4 — Merging DAG
# =============================================================================

def test_merging_graph_detects_multiple_roots():
    """
    For:

        1 ----\
              -> 3
        2 ----/

    Tasks 1 and 2 are roots.
    """

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 3)
    add_edge(graph, 2, 3)

    roots = [node.node_id for node in graph.root_nodes]

    assert set(roots) == {1, 2}
    assert len(roots) == 2


def test_merging_graph_detects_single_leaf():
    """
    For:

        1 ----\
              -> 3
        2 ----/

    Task 3 is the only leaf.
    """

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 3)
    add_edge(graph, 2, 3)

    leaves = [node.node_id for node in graph.leaf_nodes]

    assert leaves == [3]


def test_merging_graph_root_and_leaf_detection():
    """
    Verify roots and leaves for a merging DAG.
    """

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 3)
    add_edge(graph, 2, 3)

    roots = [node.node_id for node in graph.root_nodes]
    leaves = [node.node_id for node in graph.leaf_nodes]

    assert set(roots) == {1, 2}
    assert leaves == [3]


# =============================================================================
# B4 — Complex Branching DAG
# =============================================================================

def test_complex_branching_dag_detects_roots_and_leaves():
    """
    Graph:

             2 ----\
            /       \
        1             5
            \       /
             3 ----/
              \
               4

    Root:
        1

    Leaves:
        4, 5
    """

    graph = create_graph([1, 2, 3, 4, 5])

    add_edge(graph, 1, 2)
    add_edge(graph, 1, 3)
    add_edge(graph, 2, 5)
    add_edge(graph, 3, 5)
    add_edge(graph, 3, 4)

    roots = [node.node_id for node in graph.root_nodes]
    leaves = [node.node_id for node in graph.leaf_nodes]

    assert roots == [1]
    assert set(leaves) == {4, 5}
    assert len(leaves) == 2


# =============================================================================
# B4 — Multiple Roots and Multiple Leaves
# =============================================================================

def test_multiple_roots_and_multiple_leaves():
    """
    Graph:

        1 ----> 3 ----> 5
                 \
                  -> 6

        2 ----> 4 ----> 6

    Roots:
        1, 2

    Leaves:
        5, 6
    """

    graph = create_graph([1, 2, 3, 4, 5, 6])

    add_edge(graph, 1, 3)
    add_edge(graph, 2, 4)
    add_edge(graph, 3, 5)
    add_edge(graph, 3, 6)
    add_edge(graph, 4, 6)

    roots = [node.node_id for node in graph.root_nodes]
    leaves = [node.node_id for node in graph.leaf_nodes]

    assert set(roots) == {1, 2}
    assert set(leaves) == {5, 6}


# =============================================================================
# B4 — Disconnected Graph
# =============================================================================

def test_disconnected_graph_detects_all_roots():
    """
    Graph:

        1 -> 2

        3 -> 4

    Roots are 1 and 3.
    """

    graph = create_graph([1, 2, 3, 4])

    add_edge(graph, 1, 2)
    add_edge(graph, 3, 4)

    roots = [node.node_id for node in graph.root_nodes]

    assert set(roots) == {1, 3}


def test_disconnected_graph_detects_all_leaves():
    """
    Graph:

        1 -> 2

        3 -> 4

    Leaves are 2 and 4.
    """

    graph = create_graph([1, 2, 3, 4])

    add_edge(graph, 1, 2)
    add_edge(graph, 3, 4)

    leaves = [node.node_id for node in graph.leaf_nodes]

    assert set(leaves) == {2, 4}


# =============================================================================
# B4 — Root / Leaf Recalculation
# =============================================================================

def test_recalculate_roots_and_leaves_for_linear_graph():
    """
    Verify recalculate_roots_and_leaves() for:

        1 -> 2 -> 3
    """

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 2)
    add_edge(graph, 2, 3)

    roots, leaves = graph.recalculate_roots_and_leaves()

    assert roots == [1]
    assert leaves == [3]


def test_recalculate_roots_and_leaves_for_branching_graph():
    """
    Verify recalculation for:

             -> 2
            /
        1
            \
             -> 3
    """

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 2)
    add_edge(graph, 1, 3)

    roots, leaves = graph.recalculate_roots_and_leaves()

    assert roots == [1]
    assert set(leaves) == {2, 3}


def test_recalculate_roots_and_leaves_for_merging_graph():
    """
    Verify recalculation for:

        1 ----\
              -> 3
        2 ----/
    """

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 3)
    add_edge(graph, 2, 3)

    roots, leaves = graph.recalculate_roots_and_leaves()

    assert set(roots) == {1, 2}
    assert leaves == [3]


# =============================================================================
# B4 — Dynamic Relationship Changes
# =============================================================================

def test_root_detection_changes_after_adding_dependency():
    """
    Initially:

        1    2

    Both nodes are roots.

    After adding:

        1 -> 2

    Only 1 remains a root.
    """

    graph = create_graph([1, 2])

    assert set(
        node.node_id for node in graph.root_nodes
    ) == {1, 2}

    add_edge(graph, 1, 2)

    assert [
        node.node_id for node in graph.root_nodes
    ] == [1]


def test_leaf_detection_changes_after_adding_dependency():
    """
    Initially:

        1    2

    Both nodes are leaves.

    After adding:

        1 -> 2

    Only 2 remains a leaf.
    """

    graph = create_graph([1, 2])

    assert set(
        node.node_id for node in graph.leaf_nodes
    ) == {1, 2}

    add_edge(graph, 1, 2)

    assert [
        node.node_id for node in graph.leaf_nodes
    ] == [2]


# =============================================================================
# B4 — Node Membership
# =============================================================================

def test_root_nodes_belong_to_graph():
    """
    Every root returned by the graph must actually exist in graph.nodes.
    """

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 2)
    add_edge(graph, 1, 3)

    for node in graph.root_nodes:

        assert graph.has_node(node.node_id)


def test_leaf_nodes_belong_to_graph():
    """
    Every leaf returned by the graph must actually exist in graph.nodes.
    """

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 2)
    add_edge(graph, 1, 3)

    for node in graph.leaf_nodes:

        assert graph.has_node(node.node_id)


# =============================================================================
# B4 — Relationship Semantics
# =============================================================================

def test_root_has_no_parents():
    """
    Every root must have zero parent dependencies.
    """

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 2)
    add_edge(graph, 1, 3)

    for node in graph.root_nodes:

        assert node.parents == []


def test_leaf_has_no_children():
    """
    Every leaf must have zero child dependencies.
    """

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 2)
    add_edge(graph, 1, 3)

    for node in graph.leaf_nodes:

        assert node.children == []


def test_non_root_has_parent():
    """
    Every non-root node must have at least one parent.
    """

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 2)
    add_edge(graph, 1, 3)

    root_ids = {
        node.node_id
        for node in graph.root_nodes
    }

    for node in graph.nodes.values():

        if node.node_id not in root_ids:

            assert len(node.parents) > 0


def test_non_leaf_has_child():
    """
    Every non-leaf node must have at least one child.
    """

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 2)
    add_edge(graph, 1, 3)

    leaf_ids = {
        node.node_id
        for node in graph.leaf_nodes
    }

    for node in graph.nodes.values():

        if node.node_id not in leaf_ids:

            assert len(node.children) > 0


# =============================================================================
# B4 — Root / Leaf Count
# =============================================================================

def test_branching_graph_root_leaf_counts():
    """
    Branching graph:

             2
            /
        1
            \
             3

    Expected:
        roots = 1
        leaves = 2
    """

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 2)
    add_edge(graph, 1, 3)

    assert len(graph.root_nodes) == 1
    assert len(graph.leaf_nodes) == 2


def test_merging_graph_root_leaf_counts():
    """
    Merging graph:

        1 ----\
              -> 3
        2 ----/

    Expected:
        roots = 2
        leaves = 1
    """

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 3)
    add_edge(graph, 2, 3)

    assert len(graph.root_nodes) == 2
    assert len(graph.leaf_nodes) == 1


# =============================================================================
# B4 — Execution Readiness Compatibility
# =============================================================================

def test_valid_branching_graph_is_execution_ready():
    """
    Root/leaf detection must remain compatible with the graph's
    execution-readiness checks.
    """

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 2)
    add_edge(graph, 1, 3)

    assert graph.is_execution_ready() is True


def test_valid_merging_graph_is_execution_ready():
    """
    A valid merging DAG should also be execution-ready.
    """

    graph = create_graph([1, 2, 3])

    add_edge(graph, 1, 3)
    add_edge(graph, 2, 3)

    assert graph.is_execution_ready() is True