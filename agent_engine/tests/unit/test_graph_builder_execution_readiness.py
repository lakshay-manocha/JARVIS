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


def test_valid_graph_is_execution_ready():

    graph = ExecutionGraph()

    for node_id in range(1, 4):
        graph.add_node(create_node(node_id))

    graph.add_dependency(1, 2)
    graph.add_dependency(1, 3)

    assert graph.is_execution_ready() is True


def test_empty_graph_is_not_execution_ready():

    graph = ExecutionGraph()

    assert graph.is_execution_ready() is False


def test_missing_parent_reference_makes_graph_not_ready():

    graph = ExecutionGraph()

    graph.add_node(create_node(1))
    graph.add_node(create_node(2))

    graph.nodes[2].parents.append(99)

    assert graph.is_execution_ready() is False


def test_missing_child_reference_makes_graph_not_ready():

    graph = ExecutionGraph()

    graph.add_node(create_node(1))
    graph.add_node(create_node(2))

    graph.nodes[1].children.append(99)

    assert graph.is_execution_ready() is False


def test_unsynchronized_parent_child_relationship_is_not_ready():

    graph = ExecutionGraph()

    graph.add_node(create_node(1))
    graph.add_node(create_node(2))

    graph.nodes[1].children.append(2)

    assert graph.is_execution_ready() is False


def test_self_dependency_makes_graph_not_ready():

    graph = ExecutionGraph()

    graph.add_node(create_node(1))

    graph.nodes[1].parents.append(1)

    assert graph.is_execution_ready() is False


def test_duplicate_parent_dependency_makes_graph_not_ready():

    graph = ExecutionGraph()

    graph.add_node(create_node(1))
    graph.add_node(create_node(2))

    graph.nodes[2].parents.extend([1, 1])
    graph.nodes[1].children.append(2)

    assert graph.is_execution_ready() is False