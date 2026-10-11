"""
===============================================================================
File Name   : test_planner.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Tests for Planner.

C-0:
    Basic sequential planning.

C-1:
    Dependency-aware topological scheduling.

C-2:
    Dependency-based parallel task grouping.
===============================================================================
"""

from agent_engine.agent_brain.graph_builder import GraphBuilder
from agent_engine.agent_brain.planner import Planner

from agent_engine.agent_brain.models.execution_graph import ExecutionGraph
from agent_engine.agent_brain.models.execution_node import ExecutionNode
from agent_engine.agent_brain.execution_estimator import ExecutionEstimator
from agent_engine.agent_brain.models.interpreted_task import InterpretedTask
from agent_engine.agent_brain.models.processing_context import ProcessingContext
from agent_engine.agent_brain.models.llm_plan import LLMPlan

from agent_engine.contracts.enums import (ProcessingStage,Priority)


# =============================================================================
# Helpers
# =============================================================================

def build_context(task_count=3):

    tasks = []

    for i in range(task_count):

        tasks.append(
            InterpretedTask(
                task_id=i + 1,
                original_text=f"Task {i+1}",
                normalized_text=f"task {i+1}",
                action="open",
                tool="desktop_agent"
            )
        )

    context = ProcessingContext(
        llm_plan=LLMPlan(
            goal="Goal",
            summary="Summary",
            missing_information=[],
            tasks=[t.original_text for t in tasks]
        )
    )

    context.interpreted_tasks = tasks

    context = GraphBuilder().build(context)

    return context


def create_node(node_id: int) -> ExecutionNode:

    task = InterpretedTask(
        task_id=node_id,
        original_text=f"Task {node_id}",
        normalized_text=f"task {node_id}",
        action="open",
        tool="desktop_agent"
    )

    return ExecutionNode(
        node_id=node_id,
        task=task
    )


def create_graph(node_ids):

    graph = ExecutionGraph()

    for node_id in node_ids:
        graph.add_node(
            create_node(node_id)
        )

    return graph


# =============================================================================
# Existing Planner / C-0 Tests
# =============================================================================

def test_execution_plan_created():

    planner = Planner()

    context = build_context()

    result = planner.plan(context)

    assert result.execution_plan is not None


def test_plan_is_valid():

    planner = Planner()

    context = build_context()

    result = planner.plan(context)

    assert result.execution_plan.is_valid is True


def test_total_steps():

    planner = Planner()

    context = build_context(5)

    result = planner.plan(context)

    assert result.execution_plan.total_steps == 5


def test_execution_order():

    planner = Planner()

    context = build_context(4)

    result = planner.plan(context)

    orders = result.execution_plan.execution_order

    assert orders == [1, 2, 3, 4]


def test_parallel_groups_generated_for_independent_tasks():

    planner = Planner()

    context = build_context()

    result = planner.plan(context)

    assert result.execution_plan.parallel_groups == [
        [1, 2, 3]
    ]


def test_processing_stage_updated():

    planner = Planner()

    context = build_context()

    result = planner.plan(context)

    assert result.current_stage == ProcessingStage.PLANNING


def test_logs_created():

    planner = Planner()

    context = build_context()

    result = planner.plan(context)

    assert len(result.processing_logs) >= 2


def test_plan_saved_in_context():

    planner = Planner()

    context = build_context()

    result = planner.plan(context)

    assert result.execution_plan is not None


def test_returns_same_context():

    planner = Planner()

    context = build_context()

    result = planner.plan(context)

    assert result is context


# =============================================================================
# C-1 — Dependency-Aware Topological Scheduling
# =============================================================================

def test_linear_dependency_order():

    graph = create_graph([1, 2, 3])

    graph.add_dependency(1, 2)
    graph.add_dependency(2, 3)

    execution_order = Planner()._topological_sort(graph)

    order = execution_order

    assert order == [1, 2, 3]


def test_branching_dependencies():

    graph = create_graph([1, 2, 3])

    graph.add_dependency(1, 2)
    graph.add_dependency(1, 3)

    execution_order = Planner()._topological_sort(graph)

    order = execution_order


    assert order == [1, 2, 3]


def test_merging_dependencies():

    graph = create_graph([1, 2, 3])

    graph.add_dependency(1, 3)
    graph.add_dependency(2, 3)

    execution_order = Planner()._topological_sort(graph)

    order = execution_order

    assert order == [1, 2, 3]


def test_independent_nodes_are_deterministic():

    graph = create_graph([3, 1, 2])

    execution_order = Planner()._topological_sort(graph)

    order = execution_order

    assert order == [1, 2, 3]


def test_complex_dependency_graph():

    graph = create_graph([1, 2, 3, 4, 5])

    graph.add_dependency(1, 2)
    graph.add_dependency(1, 3)
    graph.add_dependency(2, 4)
    graph.add_dependency(3, 4)
    graph.add_dependency(4, 5)

    execution_order = Planner()._topological_sort(graph)

    order = execution_order

    assert order == [1, 2, 3, 4, 5]


def test_dependency_is_always_before_child():

    graph = create_graph([1, 2, 3, 4])

    graph.add_dependency(1, 3)
    graph.add_dependency(2, 3)
    graph.add_dependency(3, 4)

    execution_order = Planner()._topological_sort(graph)

    positions = {
        node_id: index
        for index, node_id in enumerate(execution_order)
    }

    assert positions[1] < positions[3]
    assert positions[2] < positions[3]
    assert positions[3] < positions[4]


def test_planner_does_not_modify_graph_dependencies():

    graph = create_graph([1, 2, 3])

    graph.add_dependency(1, 2)
    graph.add_dependency(2, 3)

    original_parents = {
        node.node_id: list(node.parents)
        for node in graph.nodes.values()
    }

    original_children = {
        node.node_id: list(node.children)
        for node in graph.nodes.values()
    }

    Planner()._topological_sort(graph)

    for node in graph.nodes.values():

        assert node.parents == original_parents[node.node_id]
        assert node.children == original_children[node.node_id]


def test_cycle_is_detected_by_incomplete_topological_order():

    graph = create_graph([1, 2, 3])

    graph.add_dependency(1, 2)
    graph.add_dependency(2, 3)
    graph.add_dependency(3, 1)

    execution_order = Planner()._topological_sort(graph)

    assert len(execution_order) < graph.node_count


def test_cycle_produces_invalid_planning_result():

    graph = create_graph([1, 2, 3])

    graph.add_dependency(1, 2)
    graph.add_dependency(2, 3)
    graph.add_dependency(3, 1)

    result = Planner()._create_plan(graph)

    assert result.is_valid is False
    assert result.execution_order == []
    assert result.total_steps == 0


def test_invalid_empty_graph():

    graph = ExecutionGraph()

    result = Planner()._create_plan(graph)

    assert result.is_valid is False
    assert result.execution_order == []
    assert result.total_steps == 0


def test_valid_graph_produces_valid_planning_result():

    graph = create_graph([1, 2, 3])

    graph.add_dependency(1, 2)
    graph.add_dependency(2, 3)

    result = Planner()._create_plan(graph)

    assert result.is_valid is True
    assert result.total_steps == 3

    order = result.execution_order
    assert order == [1, 2, 3]


# =============================================================================
# C-1 Metadata Tests
# =============================================================================

def test_planner_notes_indicate_topological_planning():

    graph = create_graph([1, 2])

    graph.add_dependency(1, 2)

    result = Planner()._create_plan(graph)

    assert (
        "Dependency-aware topological planning."
        in result.planning_notes
    )


# =============================================================================
# C-2 — Parallel Task Grouping
# =============================================================================

def test_parallel_groups_linear_dependency():

    graph = create_graph([1, 2, 3])

    graph.add_dependency(1, 2)
    graph.add_dependency(2, 3)

    result = Planner()._create_plan(graph)

    assert result.parallel_groups == [
        [1],
        [2],
        [3]
    ]


def test_parallel_groups_branching_dependencies():

    graph = create_graph([1, 2, 3])

    graph.add_dependency(1, 2)
    graph.add_dependency(1, 3)

    result = Planner()._create_plan(graph)

    assert result.parallel_groups == [
        [1],
        [2, 3]
    ]


def test_parallel_groups_merging_dependencies():

    graph = create_graph([1, 2, 3])

    graph.add_dependency(1, 3)
    graph.add_dependency(2, 3)

    result = Planner()._create_plan(graph)

    assert result.parallel_groups == [
        [1, 2],
        [3]
    ]


def test_parallel_groups_independent_tasks():

    graph = create_graph([1, 2, 3])

    result = Planner()._create_plan(graph)

    assert result.parallel_groups == [
        [1, 2, 3]
    ]


def test_parallel_groups_complex_graph():

    graph = create_graph([1, 2, 3, 4, 5])

    graph.add_dependency(1, 2)
    graph.add_dependency(1, 3)
    graph.add_dependency(2, 4)
    graph.add_dependency(3, 4)
    graph.add_dependency(4, 5)

    result = Planner()._create_plan(graph)

    assert result.parallel_groups == [
        [1],
        [2, 3],
        [4],
        [5]
    ]


def test_parallel_groups_preserve_dependencies():

    graph = create_graph([1, 2, 3, 4])

    graph.add_dependency(1, 3)
    graph.add_dependency(2, 3)
    graph.add_dependency(3, 4)

    result = Planner()._create_plan(graph)

    assert result.parallel_groups == [
        [1, 2],
        [3],
        [4]
    ]


def test_parallel_groups_are_saved_in_planning_result():

    graph = create_graph([1, 2, 3])

    graph.add_dependency(1, 2)
    graph.add_dependency(1, 3)

    result = Planner()._create_plan(graph)

    assert result.parallel_groups == [
        [1],
        [2, 3]
    ]


def test_c2_does_not_change_execution_order():

    graph = create_graph([1, 2, 3, 4])

    graph.add_dependency(1, 2)
    graph.add_dependency(1, 3)
    graph.add_dependency(2, 4)
    graph.add_dependency(3, 4)

    result = Planner()._create_plan(graph)

    order = result.execution_order

    assert order == [1, 2, 3, 4]


def test_parallel_groups_are_deterministic():

    graph = create_graph([4, 2, 3, 1])

    graph.add_dependency(1, 2)
    graph.add_dependency(1, 3)
    graph.add_dependency(2, 4)
    graph.add_dependency(3, 4)

    result = Planner()._create_plan(graph)

    assert result.parallel_groups == [
        [1],
        [2, 3],
        [4]
    ]


def test_parallel_groups_for_single_node():

    graph = create_graph([1])

    result = Planner()._create_plan(graph)

    assert result.parallel_groups == [
        [1]
    ]


def test_invalid_graph_has_no_parallel_groups():

    graph = ExecutionGraph()

    result = Planner()._create_plan(graph)

    assert result.is_valid is False
    assert result.parallel_groups == []


def test_cycle_has_no_parallel_groups():

    graph = create_graph([1, 2, 3])

    graph.add_dependency(1, 2)
    graph.add_dependency(2, 3)
    graph.add_dependency(3, 1)

    result = Planner()._create_plan(graph)

    assert result.is_valid is False
    assert result.parallel_groups == []


def test_parallel_groups_contain_all_nodes_once():

    graph = create_graph([1, 2, 3, 4, 5])

    graph.add_dependency(1, 2)
    graph.add_dependency(1, 3)
    graph.add_dependency(2, 4)
    graph.add_dependency(3, 4)
    graph.add_dependency(4, 5)

    result = Planner()._create_plan(graph)

    grouped_nodes = [
        node_id
        for group in result.parallel_groups
        for node_id in group
    ]

    assert sorted(grouped_nodes) == [1, 2, 3, 4, 5]
    assert len(grouped_nodes) == len(set(grouped_nodes))


def test_parallel_groups_match_execution_order_nodes():

    graph = create_graph([1, 2, 3, 4])

    graph.add_dependency(1, 2)
    graph.add_dependency(1, 3)
    graph.add_dependency(2, 4)
    graph.add_dependency(3, 4)

    result = Planner()._create_plan(graph)

    execution_ids = result.execution_order
    grouped_ids = [
        node_id
        for group in result.parallel_groups
        for node_id in group
    ]

    assert grouped_ids == execution_ids


def test_c2_planning_notes_indicate_parallel_grouping():

    graph = create_graph([1, 2, 3])

    graph.add_dependency(1, 2)
    graph.add_dependency(1, 3)

    result = Planner()._create_plan(graph)

    assert (
        "Parallel groups generated from dependency levels."
        in result.planning_notes
    )

# =============================================================================
# C-3 — Priority-Aware Scheduling
# =============================================================================

def test_critical_priority_is_scheduled_first():

    graph = create_graph([1, 2, 3, 4])

    graph.nodes[1].priority = Priority.LOW
    graph.nodes[2].priority = Priority.CRITICAL
    graph.nodes[3].priority = Priority.HIGH
    graph.nodes[4].priority = Priority.MEDIUM

    execution_order = Planner()._topological_sort(graph)

    order = execution_order

    assert order == [2, 3, 4, 1]

def test_priority_order_is_correct():

    graph = create_graph([1, 2, 3, 4])

    graph.nodes[1].priority = Priority.LOW
    graph.nodes[2].priority = Priority.MEDIUM
    graph.nodes[3].priority = Priority.HIGH
    graph.nodes[4].priority = Priority.CRITICAL

    execution_order = Planner()._topological_sort(graph)

    order = execution_order

    assert order == [4, 3, 2, 1]

def test_dependency_overrides_priority():

    graph = create_graph([1, 2])

    graph.nodes[1].priority = Priority.LOW
    graph.nodes[2].priority = Priority.CRITICAL

    graph.add_dependency(1, 2)

    execution_order = Planner()._topological_sort(graph)

    order = execution_order

    assert order == [1, 2]

def test_priority_applies_only_to_ready_nodes():

    graph = create_graph([1, 2, 3])

    graph.nodes[1].priority = Priority.LOW
    graph.nodes[2].priority = Priority.CRITICAL
    graph.nodes[3].priority = Priority.HIGH

    graph.add_dependency(1, 2)

    execution_order = Planner()._topological_sort(graph)

    order = execution_order

    assert order == [3, 1, 2]

def test_same_priority_uses_node_id_as_tiebreaker():

    graph = create_graph([3, 1, 2])

    graph.nodes[1].priority = Priority.HIGH
    graph.nodes[2].priority = Priority.HIGH
    graph.nodes[3].priority = Priority.HIGH

    execution_order = Planner()._topological_sort(graph)

    order = execution_order
    assert order == [1, 2, 3]

def test_priority_does_not_change_parallel_groups():

    graph = create_graph([1, 2, 3])

    graph.nodes[1].priority = Priority.LOW
    graph.nodes[2].priority = Priority.CRITICAL
    graph.nodes[3].priority = Priority.HIGH

    result = Planner()._create_plan(graph)

    assert result.parallel_groups == [
        [1, 2, 3]
    ]

def test_priority_works_with_branching_dependencies():

    graph = create_graph([1, 2, 3])

    graph.nodes[1].priority = Priority.LOW
    graph.nodes[2].priority = Priority.HIGH
    graph.nodes[3].priority = Priority.CRITICAL

    graph.add_dependency(1, 2)
    graph.add_dependency(1, 3)

    result = Planner()._create_plan(graph)

    order = result.execution_order

    assert order == [1, 3, 2]

    assert result.parallel_groups == [
        [1],
        [2, 3]
    ]

def test_priority_works_with_merging_dependencies():

    graph = create_graph([1, 2, 3])

    graph.nodes[1].priority = Priority.LOW
    graph.nodes[2].priority = Priority.HIGH
    graph.nodes[3].priority = Priority.CRITICAL

    graph.add_dependency(1, 3)
    graph.add_dependency(2, 3)

    result = Planner()._create_plan(graph)

    order = result.execution_order
    assert order == [2, 1, 3]

    assert result.parallel_groups == [
        [1, 2],
        [3]
    ]

# =============================================================================
# C-5 — Meaningful Execution-Time Estimation
# =============================================================================

def test_execution_time_is_estimated():

    graph = create_graph([1, 2, 3])

    graph.nodes[1].task.action = "open"
    graph.nodes[2].task.action = "click"
    graph.nodes[3].task.action = "search"

    result = Planner()._create_plan(graph)

    assert result.estimated_time == 3.0

def test_execution_nodes_receive_estimated_duration():

    graph = create_graph([1, 2])

    graph.nodes[1].task.action = "open"
    graph.nodes[2].task.action = "click"

    result = Planner()._create_plan(graph)

    assert result.graph.nodes[1].estimated_duration == 2.0
    assert result.graph.nodes[2].estimated_duration == 0.5


def test_parallel_tasks_use_maximum_duration():

    graph = create_graph([1, 2, 3])

    graph.nodes[1].task.action = "open"
    graph.nodes[2].task.action = "search"
    graph.nodes[3].task.action = "click"

    graph.add_dependency(1, 3)

    result = Planner()._create_plan(graph)

    assert result.parallel_groups == [
        [1, 2],
        [3]
    ]

    assert result.estimated_time == 3.5


def test_sequential_tasks_sum_duration():

    graph = create_graph([1, 2, 3])

    graph.nodes[1].task.action = "open"
    graph.nodes[2].task.action = "search"
    graph.nodes[3].task.action = "click"

    graph.add_dependency(1, 2)
    graph.add_dependency(2, 3)

    result = Planner()._create_plan(graph)

    assert result.parallel_groups == [
        [1],
        [2],
        [3]
    ]

    assert result.estimated_time == 5.5


def test_unknown_actions_still_receive_estimate():

    graph = create_graph([1])

    graph.nodes[1].task.action = "some_future_action"

    result = Planner()._create_plan(graph)

    assert result.graph.nodes[1].estimated_duration == (
        ExecutionEstimator.DEFAULT_DURATION
    )

    assert result.estimated_time == (
        ExecutionEstimator.DEFAULT_DURATION
    )

