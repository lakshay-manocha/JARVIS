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


def test_duplicate_dependency_is_not_inserted():
    graph = create_graph()

    graph.add_dependency(1, 2)
    graph.add_dependency(1, 2)
    graph.add_dependency(1, 2)

    assert graph.nodes[1].children == [2]
    assert graph.nodes[2].parents == [1]


def test_parent_child_relationship_remains_synchronized():
    graph = create_graph()

    graph.add_dependency(1, 2)
    graph.add_dependency(1, 2)

    assert 2 in graph.nodes[1].children
    assert 1 in graph.nodes[2].parents

    assert graph.nodes[1].children.count(2) == 1
    assert graph.nodes[2].parents.count(1) == 1