from agent_engine.agent_brain.models.execution_graph import ExecutionGraph
from agent_engine.agent_brain.models.execution_node import ExecutionNode
from agent_engine.agent_brain.models.interpreted_task import InterpretedTask


def create_graph(task_count: int) -> ExecutionGraph:
    graph = ExecutionGraph()

    for task_id in range(1, task_count + 1):
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


def test_one_to_many_branching():
    graph = create_graph(3)

    graph.add_dependency(1, 2)
    graph.add_dependency(1, 3)

    assert graph.nodes[1].children == [2, 3]

    assert graph.nodes[2].parents == [1]
    assert graph.nodes[3].parents == [1]


def test_many_to_one_branching():
    graph = create_graph(3)

    graph.add_dependency(1, 3)
    graph.add_dependency(2, 3)

    assert graph.nodes[1].children == [3]
    assert graph.nodes[2].children == [3]

    assert graph.nodes[3].parents == [1, 2]


def test_combined_branching():
    graph = create_graph(5)

    graph.add_dependency(1, 2)
    graph.add_dependency(1, 3)
    graph.add_dependency(2, 5)
    graph.add_dependency(3, 5)
    graph.add_dependency(4, 5)

    assert graph.nodes[1].children == [2, 3]

    assert graph.nodes[2].parents == [1]
    assert graph.nodes[3].parents == [1]

    assert graph.nodes[2].children == [5]
    assert graph.nodes[3].children == [5]
    assert graph.nodes[4].children == [5]

    assert graph.nodes[5].parents == [2, 3, 4]