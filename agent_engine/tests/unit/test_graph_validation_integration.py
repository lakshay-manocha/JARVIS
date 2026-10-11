import pytest

from agent_engine.agent_brain.graph_builder import GraphBuilder
from agent_engine.agent_brain.models.execution_graph import ExecutionGraph
from agent_engine.agent_brain.models.execution_node import ExecutionNode
from agent_engine.agent_brain.models.interpreted_task import InterpretedTask
from agent_engine.agent_brain.graph_validator import GraphValidator
from agent_engine.agent_brain.models.processing_context import ProcessingContext
from agent_engine.agent_brain.models.llm_plan import LLMPlan


def create_graph(task_count: int = 3) -> ExecutionGraph:
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


def test_valid_graph_passes_validation():
    graph = create_graph(3)

    graph.add_dependency(1, 2)
    graph.add_dependency(2, 3)

    result = GraphValidator().validate(graph)

    assert result.is_valid is True
    assert result.node_count == 3
    assert result.edge_count == 2
    assert result.error_count == 0


def test_invalid_parent_child_relationship_is_detected():
    graph = create_graph(2)

    # Deliberately corrupt one side of the relationship.
    graph.nodes[1].children.append(2)

    result = GraphValidator().validate(graph)

    assert result.is_valid is False
    assert result.error_count > 0

    assert any(
        "Dependency inconsistency" in error
        for error in result.errors
    )


def test_duplicate_dependency_is_detected():
    graph = create_graph(2)

    # Deliberately corrupt the graph.
    graph.nodes[1].children.extend([2, 2])
    graph.nodes[2].parents.extend([1, 1])

    result = GraphValidator().validate(graph)

    assert result.is_valid is False

    assert any(
        "duplicate" in error.lower()
        for error in result.errors
    )


def test_cycle_is_detected():
    graph = create_graph(3)

    graph.nodes[1].children.append(2)
    graph.nodes[2].parents.append(1)

    graph.nodes[2].children.append(3)
    graph.nodes[3].parents.append(2)

    graph.nodes[3].children.append(1)
    graph.nodes[1].parents.append(3)

    result = GraphValidator().validate(graph)

    assert result.is_valid is False

    assert any(
        "cycle" in error.lower()
        for error in result.errors
    )


def test_root_and_leaf_nodes_are_validated():
    graph = create_graph(3)

    graph.add_dependency(1, 2)
    graph.add_dependency(2, 3)

    result = GraphValidator().validate(graph)

    assert result.is_valid is True

    assert graph.root_nodes[0].node_id == 1
    assert graph.leaf_nodes[0].node_id == 3


def test_graph_builder_stores_validation_result():
    tasks = [
        InterpretedTask(
            task_id=1,
            original_text="Open Chrome",
            normalized_text="open chrome",
        ),
        InterpretedTask(
            task_id=2,
            original_text="Search for Spring AI",
            normalized_text="search for spring ai",
        ),
    ]

    context = ProcessingContext(
        llm_plan=LLMPlan(
            goal="Test graph validation",
            summary="Test graph validation integration",
            missing_information=[],
            tasks=[
                task.original_text
                for task in tasks
            ],
        ),
        interpreted_tasks=tasks,
    )

    result_context = GraphBuilder().build(context)

    assert result_context.execution_graph is not None
    assert result_context.graph_validation_result is not None

    assert (
        result_context.graph_validation_result.node_count
        == result_context.execution_graph.node_count
    )

    assert (
        result_context.graph_validation_result.is_valid
        is True
    )