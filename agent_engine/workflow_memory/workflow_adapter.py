"""
===============================================================================
File Name   : workflow_adapter.py
Module      : Workflow Memory
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
Converts JARVIS ExecutionGraph objects into the workflow representation
required by Model A's workflow retrieval predictor.

The adapter is read-only and does not modify the stable JARVIS core.
===============================================================================
"""

from __future__ import annotations

from typing import Any

from agent_engine.agent_brain.models.execution_graph import ExecutionGraph
from agent_engine.agent_brain.models.execution_node import ExecutionNode


def _serialize_enum(value: Any) -> Any:
    """
    Converts Enum-like values into JSON-compatible values.
    """
    if value is None:
        return None

    return value.value if hasattr(value, "value") else str(value)


def _derive_overall_status(
    execution_graph: ExecutionGraph,
) -> str:
    """
    Derives a summary status from the statuses of all graph nodes.

    This function is read-only.
    """

    if execution_graph.node_count == 0:
        return "EMPTY"

    statuses = {
        _serialize_enum(node.status)
        for node in execution_graph.nodes.values()
    }

    if statuses == {"COMPLETED"}:
        return "COMPLETED"

    if "FAILED" in statuses:
        return "FAILED"

    if "RUNNING" in statuses:
        return "RUNNING"

    if "READY" in statuses:
        return "READY"

    if statuses == {"PENDING"}:
        return "PENDING"

    return "PARTIAL"


def execution_node_to_model_a_node(
    node: ExecutionNode,
) -> dict[str, Any]:
    """
    Converts one ExecutionNode into Model A's node format.
    """

    task = node.task

    description = (
        task.original_text
        or task.normalized_text
    )

    return {
        "id": node.node_id,
        "description": description,
        "action": task.action,
        "tool": task.tool,
        "parameters": dict(task.parameters),
        "depends_on": list(node.parents),
        "status": _serialize_enum(node.status),
        "priority": _serialize_enum(node.priority),
        "children": list(node.children),
    }


def execution_graph_to_model_a_graph(
    execution_graph: ExecutionGraph,
) -> dict[str, Any]:
    """
    Converts JARVIS's node dictionary into Model A's node list.
    """

    nodes = [
        execution_node_to_model_a_node(node)
        for node in execution_graph.nodes.values()
    ]

    nodes.sort(key=lambda item: item["id"])

    return {
        "nodes": nodes
    }


def execution_graph_to_model_a_workflow(
    execution_graph: ExecutionGraph,
    *,
    goal: str,
    domain: str,
    overall_status: str | None = None,
    current_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Converts a complete JARVIS ExecutionGraph into Model A's workflow input.

    Parameters:
        execution_graph:
            Stable JARVIS ExecutionGraph instance.

        goal:
            High-level objective of the workflow.

        domain:
            Workflow domain, such as desktop, browser, filesystem, or mixed.

        overall_status:
            Optional workflow status. If omitted, it is derived from node states.

        current_state:
            Optional runtime context. Model A currently uses applications
            and files when available.
    """

    return {
        "goal": goal,
        "domain": domain,
        "overall_status": (
            overall_status
            if overall_status is not None
            else _derive_overall_status(execution_graph)
        ),
        "graph": execution_graph_to_model_a_graph(
            execution_graph
        ),
        "current_state": (
            dict(current_state)
            if current_state is not None
            else {}
        ),
    }