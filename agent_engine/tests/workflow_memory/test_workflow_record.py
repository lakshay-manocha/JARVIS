"""
===============================================================================
File Name   : test_workflow_record.py
Module      : Workflow Memory Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
Unit tests for the WorkflowRecord model.
===============================================================================
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from agent_engine.workflow_memory.workflow_record import WorkflowRecord


def create_valid_record(**overrides) -> WorkflowRecord:
    """
    Helper function to create a valid WorkflowRecord.
    """

    payload = {
        "workflow_id": "workflow_001",
        "goal": "Open browser and search for a topic",
        "domain": "desktop_browser",
        "overall_status": "COMPLETED",
    }

    payload.update(overrides)

    return WorkflowRecord(**payload)


def test_workflow_record_creates_with_required_fields():
    """
    Verify that a WorkflowRecord can be created using required fields.
    """

    record = create_valid_record()

    assert record.workflow_id == "workflow_001"
    assert record.goal == "Open browser and search for a topic"
    assert record.domain == "desktop_browser"
    assert record.overall_status == "COMPLETED"


def test_workflow_record_uses_expected_default_values():
    """
    Verify default values for graph, current_state, metadata,
    and timestamps.
    """

    record = create_valid_record()

    assert record.graph == {"nodes": []}
    assert record.current_state == {}
    assert record.metadata == {}

    assert isinstance(record.created_at, datetime)
    assert record.created_at.tzinfo is not None

    assert record.completed_at is None


def test_workflow_record_accepts_graph_data():
    """
    Verify that Model A-compatible graph data is preserved.
    """

    graph = {
        "nodes": [
            {
                "id": 1,
                "description": "Open browser",
                "action": "open_application",
                "tool": "browser",
                "parameters": {"application": "chrome"},
                "depends_on": [],
                "status": "COMPLETED",
                "priority": 1,
            }
        ]
    }

    record = create_valid_record(graph=graph)

    assert record.graph == graph
    assert record.graph["nodes"][0]["action"] == "open_application"


def test_workflow_record_accepts_current_state():
    """
    Verify that workflow environment state is preserved.
    """

    current_state = {
        "active_application": "chrome",
        "open_files": [],
        "network_available": True,
    }

    record = create_valid_record(current_state=current_state)

    assert record.current_state == current_state
    assert record.current_state["active_application"] == "chrome"
    assert record.current_state["network_available"] is True


def test_workflow_record_accepts_metadata():
    """
    Verify that additional workflow metadata is preserved.
    """

    metadata = {
        "source": "agent_brain",
        "execution_mode": "mock",
        "retry_count": 1,
    }

    record = create_valid_record(metadata=metadata)

    assert record.metadata == metadata
    assert record.metadata["source"] == "agent_brain"
    assert record.metadata["execution_mode"] == "mock"


def test_workflow_record_accepts_completed_at():
    """
    Verify that completed_at can be provided.
    """

    completed_at = datetime.now()

    record = create_valid_record(completed_at=completed_at)

    assert record.completed_at == completed_at


@pytest.mark.parametrize(
    "missing_field",
    [
        "workflow_id",
        "goal",
        "domain",
        "overall_status",
    ],
)
def test_required_fields_cannot_be_missing(missing_field):
    """
    Verify that every required field is mandatory.
    """

    payload = {
        "workflow_id": "workflow_001",
        "goal": "Open browser",
        "domain": "desktop",
        "overall_status": "COMPLETED",
    }

    del payload[missing_field]

    with pytest.raises(ValidationError):
        WorkflowRecord(**payload)


@pytest.mark.parametrize(
    "field_name",
    [
        "workflow_id",
        "goal",
        "domain",
        "overall_status",
    ],
)
def test_required_string_fields_cannot_be_empty(field_name):
    """
    Verify that required string fields reject empty strings.
    """

    payload = {
        "workflow_id": "workflow_001",
        "goal": "Open browser",
        "domain": "desktop",
        "overall_status": "COMPLETED",
    }

    payload[field_name] = ""

    with pytest.raises(ValidationError):
        WorkflowRecord(**payload)


def test_workflow_record_rejects_extra_fields():
    """
    Verify that unexpected fields are rejected.
    """

    with pytest.raises(ValidationError):
        create_valid_record(unexpected_field="not_allowed")


def test_workflow_record_model_dump_contains_expected_fields():
    """
    Verify that the model can be serialized using model_dump().
    """

    record = create_valid_record()

    dumped_record = record.model_dump()

    assert "workflow_id" in dumped_record
    assert "goal" in dumped_record
    assert "domain" in dumped_record
    assert "overall_status" in dumped_record
    assert "graph" in dumped_record
    assert "current_state" in dumped_record
    assert "metadata" in dumped_record
    assert "created_at" in dumped_record
    assert "completed_at" in dumped_record


def test_mutable_default_fields_are_not_shared_between_instances():
    """
    Verify that mutable default fields are independently created
    for every WorkflowRecord instance.
    """

    record_one = create_valid_record()
    record_two = create_valid_record(workflow_id="workflow_002")

    record_one.current_state["active_application"] = "chrome"
    record_one.metadata["source"] = "test"
    record_one.graph["nodes"].append({"id": 1})

    assert record_two.current_state == {}
    assert record_two.metadata == {}
    assert record_two.graph == {"nodes": []}


def test_workflow_record_preserves_custom_status():
    """
    Verify that the model accepts non-empty workflow status values.
    """

    record = create_valid_record(overall_status="FAILED")

    assert record.overall_status == "FAILED"


def test_workflow_record_preserves_workflow_identity():
    """
    Verify that workflow_id remains unchanged.
    """

    record = create_valid_record(workflow_id="jarvis_workflow_2026_001")

    assert record.workflow_id == "jarvis_workflow_2026_001"