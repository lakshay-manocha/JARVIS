from agent_engine.agent_brain.graph_builder import GraphBuilder
from agent_engine.agent_brain.models.interpreted_task import InterpretedTask
from agent_engine.agent_brain.models.processing_context import ProcessingContext
from agent_engine.agent_brain.models.llm_plan import LLMPlan


def create_context(tasks):
    return ProcessingContext(
        llm_plan=LLMPlan(
            goal="test",
            summary="test",
            missing_information=[],
            tasks=[task.original_text for task in tasks],
        ),
        interpreted_tasks=tasks,
    )


def test_independent_tasks_do_not_create_sequential_edges():
    tasks = [
        InterpretedTask(
            task_id=1,
            original_text="Open calculator",
            normalized_text="open calculator",
        ),
        InterpretedTask(
            task_id=2,
            original_text="Open notepad",
            normalized_text="open notepad",
        ),
        InterpretedTask(
            task_id=3,
            original_text="Open browser",
            normalized_text="open browser",
        ),
    ]

    context = create_context(tasks)

    result = GraphBuilder().build(context)

    graph = result.execution_graph

    assert graph.nodes[1].children == []
    assert graph.nodes[2].children == []
    assert graph.nodes[3].children == []

    assert graph.nodes[1].parents == []
    assert graph.nodes[2].parents == []
    assert graph.nodes[3].parents == []


def test_task_order_does_not_create_dependency():
    tasks = [
        InterpretedTask(
            task_id=1,
            original_text="Prepare presentation",
            normalized_text="prepare presentation",
        ),
        InterpretedTask(
            task_id=2,
            original_text="Play music",
            normalized_text="play music",
        ),
        InterpretedTask(
            task_id=3,
            original_text="Open calculator",
            normalized_text="open calculator",
        ),
    ]

    context = create_context(tasks)

    result = GraphBuilder().build(context)

    graph = result.execution_graph

    assert graph.node_count == 3

    total_edges = sum(
        len(node.children)
        for node in graph.nodes.values()
    )

    assert total_edges == 0