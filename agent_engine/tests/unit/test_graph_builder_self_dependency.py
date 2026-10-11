import pytest

from agent_engine.agent_brain.models.execution_graph import ExecutionGraph
from agent_engine.agent_brain.models.execution_node import ExecutionNode
from agent_engine.agent_brain.models.interpreted_task import InterpretedTask


def create_graph() -> ExecutionGraph:
    graph = ExecutionGraph()

    for task_id in range(1, 3):
        task = InterpretedTask(
            task_id=task_id,
            original_text=f"Task {task_id}",
            normalized_text=f"task {task_id}",
        )

        graph.add_node(
            ExecutionNode(
                node_id=task_id,
                task=task,
            )
        )

    return graph


def test_self_dependency_is_rejected():
    graph = create_graph()

    with pytest.raises(ValueError, match="Self-dependency is not allowed"):
        graph.add_dependency(1, 1)


def test_self_dependency_does_not_modify_graph():
    graph = create_graph()

    try:
        graph.add_dependency(1, 1)
    except ValueError:
        pass

    assert graph.nodes[1].parents == []
    assert graph.nodes[1].children == []


def test_valid_dependency_still_works():
    graph = create_graph()

    graph.add_dependency(1, 2)

    assert graph.nodes[1].children == [2]
    assert graph.nodes[2].parents == [1]