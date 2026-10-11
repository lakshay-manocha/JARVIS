"""
===============================================================================
File Name   : test_workflow_repository.py
Module      : Workflow Memory Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
Unit tests for WorkflowRepository.
===============================================================================
"""

import pytest

from agent_engine.workflow_memory.workflow_record import WorkflowRecord
from agent_engine.workflow_memory.workflow_repository import WorkflowRepository


def create_record(
    workflow_id: str = "workflow_001",
    goal: str = "Open browser and search for a topic",
    domain: str = "desktop_browser",
    overall_status: str = "COMPLETED",
) -> WorkflowRecord:
    """
    Helper function to create a valid WorkflowRecord.
    """

    return WorkflowRecord(
        workflow_id=workflow_id,
        goal=goal,
        domain=domain,
        overall_status=overall_status,
    )


def test_repository_initializes_empty():
    """
    Verify that a newly created repository contains no records.
    """

    repository = WorkflowRepository()

    assert repository.count() == 0
    assert repository.list_all() == []


def test_save_stores_workflow_record():
    """
    Verify that save() stores a workflow record.
    """

    repository = WorkflowRepository()
    record = create_record()

    saved_record = repository.save(record)

    assert saved_record.workflow_id == "workflow_001"
    assert repository.count() == 1
    assert repository.exists("workflow_001") is True


def test_get_returns_saved_workflow_record():
    """
    Verify that get() retrieves a stored record by workflow_id.
    """

    repository = WorkflowRepository()
    record = create_record()

    repository.save(record)

    retrieved_record = repository.get("workflow_001")

    assert retrieved_record is not None
    assert retrieved_record.workflow_id == record.workflow_id
    assert retrieved_record.goal == record.goal
    assert retrieved_record.domain == record.domain
    assert retrieved_record.overall_status == record.overall_status


def test_get_returns_none_for_unknown_workflow_id():
    """
    Verify that get() returns None when workflow_id is not found.
    """

    repository = WorkflowRepository()

    assert repository.get("unknown_workflow") is None


def test_list_all_returns_all_records():
    """
    Verify that list_all() returns all stored records.
    """

    repository = WorkflowRepository()

    record_one = create_record(workflow_id="workflow_001")
    record_two = create_record(workflow_id="workflow_002")
    record_three = create_record(workflow_id="workflow_003")

    repository.save(record_one)
    repository.save(record_two)
    repository.save(record_three)

    records = repository.list_all()

    assert len(records) == 3
    assert {record.workflow_id for record in records} == {
        "workflow_001",
        "workflow_002",
        "workflow_003",
    }


def test_save_overwrites_record_with_same_workflow_id():
    """
    Verify that saving a record with an existing workflow_id replaces
    the previous record.
    """

    repository = WorkflowRepository()

    original_record = create_record(
        workflow_id="workflow_001",
        goal="Open browser",
        overall_status="RUNNING",
    )

    updated_record = create_record(
        workflow_id="workflow_001",
        goal="Open browser and search for AI",
        overall_status="COMPLETED",
    )

    repository.save(original_record)
    repository.save(updated_record)

    retrieved_record = repository.get("workflow_001")

    assert retrieved_record is not None
    assert retrieved_record.goal == "Open browser and search for AI"
    assert retrieved_record.overall_status == "COMPLETED"
    assert repository.count() == 1


def test_delete_removes_existing_record():
    """
    Verify that delete() removes an existing workflow record.
    """

    repository = WorkflowRepository()
    repository.save(create_record())

    result = repository.delete("workflow_001")

    assert result is True
    assert repository.get("workflow_001") is None
    assert repository.exists("workflow_001") is False
    assert repository.count() == 0


def test_delete_returns_false_for_unknown_workflow_id():
    """
    Verify that deleting an unknown workflow_id returns False.
    """

    repository = WorkflowRepository()

    result = repository.delete("unknown_workflow")

    assert result is False
    assert repository.count() == 0


def test_exists_returns_correct_result():
    """
    Verify exists() for both existing and missing records.
    """

    repository = WorkflowRepository()

    assert repository.exists("workflow_001") is False

    repository.save(create_record())

    assert repository.exists("workflow_001") is True
    assert repository.exists("workflow_002") is False


def test_clear_removes_all_records():
    """
    Verify that clear() removes every stored record.
    """

    repository = WorkflowRepository()

    repository.save(create_record(workflow_id="workflow_001"))
    repository.save(create_record(workflow_id="workflow_002"))

    assert repository.count() == 2

    repository.clear()

    assert repository.count() == 0
    assert repository.list_all() == []


def test_save_rejects_invalid_record_type():
    """
    Verify that save() rejects objects that are not WorkflowRecord instances.
    """

    repository = WorkflowRepository()

    with pytest.raises(TypeError):
        repository.save("not a workflow record")


def test_repository_stores_independent_copy_on_save():
    """
    Verify that repository data does not directly depend on the original
    record object after save().
    """

    repository = WorkflowRepository()

    original_record = create_record()
    repository.save(original_record)

    original_record.goal = "Modified outside repository"

    retrieved_record = repository.get("workflow_001")

    assert retrieved_record is not None
    assert retrieved_record.goal == "Open browser and search for a topic"


def test_repository_returns_independent_copy_on_get():
    """
    Verify that modifying a retrieved record does not modify repository data.
    """

    repository = WorkflowRepository()
    repository.save(create_record())

    retrieved_record = repository.get("workflow_001")

    assert retrieved_record is not None

    retrieved_record.goal = "Modified retrieved copy"

    second_retrieval = repository.get("workflow_001")

    assert second_retrieval is not None
    assert second_retrieval.goal == "Open browser and search for a topic"


def test_repository_returns_independent_copies_in_list_all():
    """
    Verify that list_all() returns independent record copies.
    """

    repository = WorkflowRepository()
    repository.save(create_record())

    records = repository.list_all()

    assert len(records) == 1

    records[0].goal = "Modified list copy"

    retrieved_record = repository.get("workflow_001")

    assert retrieved_record is not None
    assert retrieved_record.goal == "Open browser and search for a topic"