"""
===============================================================================
File Name   : test_workflow_adapter.py
Module      : Workflow Memory Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
Tests the read-only conversion of JARVIS ExecutionGraph objects into the
workflow format expected by Model A.
===============================================================================
"""

from copy import deepcopy

import pytest

from agent_engine.agent_brain.models.execution_graph import ExecutionGraph
from agent_engine.agent_brain.models.execution_node import ExecutionNode
from agent_engine.agent_brain.models.interpreted_task import InterpretedTask
from agent_engine.contracts.enums import ExecutionStatus, Priority

from agent_engine.workflow_memory.workflow_adapter import (
    execution_node_to_model_a_node,
    execution_graph_to_model_a_graph,
    execution_graph_to_model_a_workflow,
)


# =============================================================================
# Test Helpers
# =============================================================================


def create_interpreted_task(
    task_id: int,
    original_text: str,
    *,
    action: str | None = None,
    tool: str | None = None,
    parameters: dict | None = None,
    metadata: dict | None = None,
) -> InterpretedTask:
    """
    Creates a valid InterpretedTask for testing.
    """

    return InterpretedTask(
        task_id=task_id,
        original_text=original_text,
        normalized_text=original_text.lower(),
        action=action,
        tool=tool,
        parameters=parameters or {},
        metadata=metadata or {},
    )


def create_execution_node(
    node_id: int,
    original_text: str,
    *,
    action: str | None = None,
    tool: str | None = None,
    parameters: dict | None = None,
    parents: list[int] | None = None,
    children: list[int] | None = None,
    priority: Priority = Priority.MEDIUM,
    status: ExecutionStatus = ExecutionStatus.PENDING,
) -> ExecutionNode:
    """
    Creates a valid ExecutionNode for testing.
    """

    task = create_interpreted_task(
        task_id=node_id,
        original_text=original_text,
        action=action,
        tool=tool,
        parameters=parameters,
    )

    return ExecutionNode(
        node_id=node_id,
        task=task,
        parents=parents or [],
        children=children or [],
        priority=priority,
        status=status,
    )


def create_three_node_graph() -> ExecutionGraph:
    """
    Creates the following dependency graph:

        Node 1 → Node 2 → Node 3
    """

    graph = ExecutionGraph()

    node_1 = create_execution_node(
        node_id=1,
        original_text="Open Chrome",
        action="open_application",
        tool="desktop",
        parameters={
            "application": "chrome",
        },
        parents=[],
        children=[2],
        priority=Priority.HIGH,
        status=ExecutionStatus.COMPLETED,
    )

    node_2 = create_execution_node(
        node_id=2,
        original_text="Search for artificial intelligence",
        action="search_web",
        tool="browser",
        parameters={
            "query": "artificial intelligence",
        },
        parents=[1],
        children=[3],
        priority=Priority.MEDIUM,
        status=ExecutionStatus.COMPLETED,
    )

    node_3 = create_execution_node(
        node_id=3,
        original_text="Save the search result",
        action="save_file",
        tool="filesystem",
        parameters={
            "filename": "ai_result.txt",
        },
        parents=[2],
        children=[],
        priority=Priority.LOW,
        status=ExecutionStatus.PENDING,
    )

    graph.add_node(node_1)
    graph.add_node(node_2)
    graph.add_node(node_3)

    return graph


# =============================================================================
# Node Adapter Tests
# =============================================================================


def test_execution_node_to_model_a_node_maps_fields_correctly():
    """
    Verifies that one ExecutionNode is converted correctly.
    """

    node = create_execution_node(
        node_id=1,
        original_text="Open Chrome",
        action="open_application",
        tool="desktop",
        parameters={
            "application": "chrome",
        },
        parents=[],
        children=[2],
        priority=Priority.HIGH,
        status=ExecutionStatus.COMPLETED,
    )

    result = execution_node_to_model_a_node(node)

    assert result["id"] == 1
    assert result["description"] == "Open Chrome"
    assert result["action"] == "open_application"
    assert result["tool"] == "desktop"
    assert result["parameters"] == {
        "application": "chrome",
    }
    assert result["depends_on"] == []
    assert result["children"] == [2]

    assert result["status"] == (
        ExecutionStatus.COMPLETED.value
        if hasattr(ExecutionStatus.COMPLETED, "value")
        else str(ExecutionStatus.COMPLETED)
    )

    assert result["priority"] == (
        Priority.HIGH.value
        if hasattr(Priority.HIGH, "value")
        else str(Priority.HIGH)
    )


def test_execution_node_to_model_a_node_handles_missing_action_and_tool():
    """
    Verifies that unresolved action and tool values remain None.
    """

    node = create_execution_node(
        node_id=1,
        original_text="Perform an unresolved task",
        action=None,
        tool=None,
    )

    result = execution_node_to_model_a_node(node)

    assert result["id"] == 1
    assert result["description"] == "Perform an unresolved task"
    assert result["action"] is None
    assert result["tool"] is None
    assert result["parameters"] == {}


def test_execution_node_to_model_a_node_does_not_mutate_original_node():
    """
    Verifies that mutable fields are copied rather than shared.
    """

    node = create_execution_node(
        node_id=1,
        original_text="Open Chrome",
        action="open_application",
        tool="desktop",
        parameters={
            "application": "chrome",
        },
        parents=[],
        children=[2],
    )

    original_parameters = deepcopy(node.task.parameters)
    original_parents = list(node.parents)
    original_children = list(node.children)

    result = execution_node_to_model_a_node(node)

    result["parameters"]["application"] = "firefox"
    result["depends_on"].append(99)
    result["children"].append(100)

    assert node.task.parameters == original_parameters
    assert node.parents == original_parents
    assert node.children == original_children


# =============================================================================
# Graph Adapter Tests
# =============================================================================


def test_execution_graph_to_model_a_graph_converts_nodes_to_list():
    """
    Verifies that ExecutionGraph.nodes dictionary is converted into a list.
    """

    graph = create_three_node_graph()

    result = execution_graph_to_model_a_graph(graph)

    assert "nodes" in result
    assert isinstance(result["nodes"], list)
    assert len(result["nodes"]) == 3


def test_execution_graph_to_model_a_graph_preserves_node_order():
    """
    Verifies deterministic ordering by node ID.
    """

    graph = ExecutionGraph()

    node_3 = create_execution_node(
        node_id=3,
        original_text="Third task",
    )

    node_1 = create_execution_node(
        node_id=1,
        original_text="First task",
    )

    node_2 = create_execution_node(
        node_id=2,
        original_text="Second task",
    )

    # Intentionally add nodes in non-sequential order.
    graph.add_node(node_3)
    graph.add_node(node_1)
    graph.add_node(node_2)

    result = execution_graph_to_model_a_graph(graph)

    node_ids = [
        node["id"]
        for node in result["nodes"]
    ]

    assert node_ids == [1, 2, 3]


def test_execution_graph_to_model_a_graph_preserves_dependencies():
    """
    Verifies parent dependencies and child relationships.
    """

    graph = create_three_node_graph()

    result = execution_graph_to_model_a_graph(graph)

    nodes_by_id = {
        node["id"]: node
        for node in result["nodes"]
    }

    assert nodes_by_id[1]["depends_on"] == []
    assert nodes_by_id[1]["children"] == [2]

    assert nodes_by_id[2]["depends_on"] == [1]
    assert nodes_by_id[2]["children"] == [3]

    assert nodes_by_id[3]["depends_on"] == [2]
    assert nodes_by_id[3]["children"] == []


def test_execution_graph_to_model_a_graph_handles_empty_graph():
    """
    Verifies that an empty graph produces an empty node list.
    """

    graph = ExecutionGraph()

    result = execution_graph_to_model_a_graph(graph)

    assert result == {
        "nodes": []
    }


# =============================================================================
# Complete Workflow Adapter Tests
# =============================================================================


def test_execution_graph_to_model_a_workflow_maps_top_level_fields():
    """
    Verifies complete Model A workflow structure.
    """

    graph = create_three_node_graph()

    result = execution_graph_to_model_a_workflow(
        graph,
        goal="Open Chrome, search for AI, and save the result",
        domain="desktop_browser",
        current_state={
            "applications": ["chrome"],
            "files": [],
        },
    )

    assert result["goal"] == (
        "Open Chrome, search for AI, and save the result"
    )

    assert result["domain"] == "desktop_browser"
    assert result["overall_status"] == "PARTIAL"

    assert result["current_state"] == {
        "applications": ["chrome"],
        "files": [],
    }

    assert "graph" in result
    assert "nodes" in result["graph"]
    assert len(result["graph"]["nodes"]) == 3


def test_execution_graph_to_model_a_workflow_accepts_explicit_status():
    """
    Verifies that an explicitly supplied overall status is preserved.
    """

    graph = create_three_node_graph()

    result = execution_graph_to_model_a_workflow(
        graph,
        goal="Test workflow",
        domain="testing",
        overall_status="CUSTOM_STATUS",
    )

    assert result["overall_status"] == "CUSTOM_STATUS"


def test_execution_graph_to_model_a_workflow_defaults_current_state_to_empty():
    """
    Verifies that current_state defaults to an empty dictionary.
    """

    graph = create_three_node_graph()

    result = execution_graph_to_model_a_workflow(
        graph,
        goal="Test workflow",
        domain="testing",
    )

    assert result["current_state"] == {}


def test_execution_graph_to_model_a_workflow_derives_completed_status():
    """
    Verifies that a graph with only completed nodes gets COMPLETED status.
    """

    graph = ExecutionGraph()

    node = create_execution_node(
        node_id=1,
        original_text="Completed task",
        status=ExecutionStatus.COMPLETED,
    )

    graph.add_node(node)

    result = execution_graph_to_model_a_workflow(
        graph,
        goal="Completed workflow",
        domain="testing",
    )

    assert result["overall_status"] == (
        ExecutionStatus.COMPLETED.value
        if hasattr(ExecutionStatus.COMPLETED, "value")
        else str(ExecutionStatus.COMPLETED)
    )


def test_execution_graph_to_model_a_workflow_derives_failed_status():
    """
    Verifies that a graph containing a failed node gets FAILED status.
    """

    graph = ExecutionGraph()

    node = create_execution_node(
        node_id=1,
        original_text="Failed task",
        status=ExecutionStatus.FAILED,
    )

    graph.add_node(node)

    result = execution_graph_to_model_a_workflow(
        graph,
        goal="Failed workflow",
        domain="testing",
    )

    assert result["overall_status"] == (
        ExecutionStatus.FAILED.value
        if hasattr(ExecutionStatus.FAILED, "value")
        else str(ExecutionStatus.FAILED)
    )


def test_execution_graph_to_model_a_workflow_does_not_mutate_graph():
    """
    Verifies that the complete adapter is read-only.
    """

    graph = create_three_node_graph()

    original_graph = deepcopy(graph.model_dump())

    result = execution_graph_to_model_a_workflow(
        graph,
        goal="Read-only test",
        domain="testing",
        current_state={
            "applications": ["chrome"],
            "files": [],
        },
    )

    result["graph"]["nodes"][0]["parameters"]["application"] = "firefox"
    result["graph"]["nodes"][0]["depends_on"].append(999)

    assert graph.model_dump() == original_graph