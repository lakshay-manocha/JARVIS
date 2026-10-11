from agent_engine.agent_brain.models.execution_graph import ExecutionGraph
from agent_engine.agent_brain.models.execution_node import ExecutionNode
from agent_engine.agent_brain.models.interpreted_task import InterpretedTask
from agent_engine.contracts.dependency_types import DependencyType
from agent_engine.agent_brain.graph_builder import GraphBuilder
from agent_engine.agent_brain.models.processing_context import ProcessingContext
from agent_engine.agent_brain.models.llm_plan import LLMPlan


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


def test_dependency_metadata_is_preserved():
    graph = create_graph()

    graph.add_dependency(
        parent_id=1,
        child_id=2,
        dependency_type=DependencyType.DATA,
        confidence=0.90,
        reason="Child uses parent output.",
        metadata={
            "rule": "data_reference",
            "evidence": r"\bthe found\b",
        },
    )

    metadata = graph.get_dependency_metadata(1, 2)

    assert metadata is not None

    assert metadata["dependency_type"] == "data"
    assert metadata["confidence"] == "0.9"
    assert metadata["reason"] == "Child uses parent output."

    assert metadata["rule"] == "data_reference"
    assert metadata["evidence"] == r"\bthe found\b"


def test_dependency_metadata_is_stored_per_edge():
    graph = create_graph()

    graph.add_dependency(
        parent_id=1,
        child_id=2,
        dependency_type=DependencyType.DATA,
        confidence=0.90,
        reason="Data dependency.",
        metadata={
            "rule": "data_reference",
        },
    )

    assert "1->2" in graph.dependency_metadata

    assert graph.dependency_metadata["1->2"][
        "dependency_type"
    ] == "data"


def test_missing_dependency_metadata_returns_none():
    graph = create_graph()

    assert (
        graph.get_dependency_metadata(1, 2)
        is None
    )




def test_graph_builder_preserves_dependency_metadata():
    tasks = [
        InterpretedTask(
            task_id=1,
            original_text="Search for Spring AI tutorial",
            normalized_text="search for spring ai tutorial",
        ),
        InterpretedTask(
            task_id=2,
            original_text="Download the found PDF",
            normalized_text="download the found pdf",
        ),
    ]

    context = ProcessingContext(
        llm_plan=LLMPlan(
            goal="Test metadata preservation",
            summary="Test dependency metadata",
            missing_information=[],
            tasks=[
                task.original_text
                for task in tasks
            ],
        ),
        interpreted_tasks=tasks,
    )

    result_context = GraphBuilder().build(context)

    graph = result_context.execution_graph

    assert graph is not None

    metadata = graph.get_dependency_metadata(1, 2)

    assert metadata is not None

    assert metadata["dependency_type"] == "data"
    assert metadata["confidence"] == "0.9"

    assert "reason" in metadata
    assert "rule" in metadata
    assert "evidence" in metadata