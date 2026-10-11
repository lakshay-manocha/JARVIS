"""
===============================================================================
File Name   : test_execution_estimator.py
Module      : Unit Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Tests for ExecutionEstimator.

C-5:
    Meaningful execution-time estimation.
===============================================================================
"""

from agent_engine.agent_brain.execution_estimator import ExecutionEstimator
from agent_engine.agent_brain.models.execution_node import ExecutionNode
from agent_engine.agent_brain.models.interpreted_task import InterpretedTask


def create_node(
    node_id: int,
    action: str | None
) -> ExecutionNode:

    task = InterpretedTask(
        task_id=node_id,
        original_text=f"Task {node_id}",
        normalized_text=f"task {node_id}",
        action=action,
        tool="desktop_agent"
    )

    return ExecutionNode(
        node_id=node_id,
        task=task
    )


def test_open_action_estimate():

    node = create_node(1, "open")

    estimate = ExecutionEstimator().estimate(node)

    assert estimate == 2.0


def test_click_action_estimate():

    node = create_node(1, "click")

    estimate = ExecutionEstimator().estimate(node)

    assert estimate == 0.5


def test_search_action_estimate():

    node = create_node(1, "search")

    estimate = ExecutionEstimator().estimate(node)

    assert estimate == 3.0


def test_unknown_action_uses_default_estimate():

    node = create_node(1, "unknown_action")

    estimate = ExecutionEstimator().estimate(node)

    assert estimate == ExecutionEstimator.DEFAULT_DURATION


def test_missing_action_uses_default_estimate():

    node = create_node(1, None)

    estimate = ExecutionEstimator().estimate(node)

    assert estimate == ExecutionEstimator.DEFAULT_DURATION