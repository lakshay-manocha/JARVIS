from agent_engine.agent_brain.models.execution_graph import ExecutionGraph
from agent_engine.agent_brain.models.execution_node import ExecutionNode
from agent_engine.agent_brain.models.interpreted_task import InterpretedTask


def create_node(node_id: int) -> ExecutionNode:
    return ExecutionNode(
        node_id=node_id,
        task=InterpretedTask(
            task_id=node_id,
            original_text=f"Task {node_id}",
            normalized_text=f"task {node_id}",
        ),
    )


def test_roots_and_leaves_for_branching_graph():
    graph = ExecutionGraph()

    for node_id in range(1, 5):
        graph.add_node(create_node(node_id))

    # 1 -> 2
    # 1 -> 3
    # 4 -> 3
    graph.add_dependency(1, 2)
    graph.add_dependency(1, 3)
    graph.add_dependency(4, 3)

    roots, leaves = graph.recalculate_roots_and_leaves()

    assert roots == [1, 4]
    assert leaves == [2, 3]


def test_independent_node_is_both_root_and_leaf():
    graph = ExecutionGraph()

    for node_id in range(1, 4):
        graph.add_node(create_node(node_id))

    # 1 -> 2
    graph.add_dependency(1, 2)

    roots, leaves = graph.recalculate_roots_and_leaves()

    assert roots == [1, 3]
    assert leaves == [2, 3]


def test_root_and_leaf_change_after_new_dependency():
    graph = ExecutionGraph()

    for node_id in range(1, 4):
        graph.add_node(create_node(node_id))

    roots, leaves = graph.recalculate_roots_and_leaves()

    assert roots == [1, 2, 3]
    assert leaves == [1, 2, 3]

    # Add 1 -> 2
    graph.add_dependency(1, 2)

    roots, leaves = graph.recalculate_roots_and_leaves()

    assert roots == [1, 3]
    assert leaves == [2, 3]

    # Add 2 -> 3
    graph.add_dependency(2, 3)

    roots, leaves = graph.recalculate_roots_and_leaves()

    assert roots == [1]
    assert leaves == [3]