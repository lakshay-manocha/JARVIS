"""
===============================================================================
File Name   : workflow_repository.py
Module      : Workflow Memory
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
Provides an in-memory repository for storing and retrieving WorkflowRecord
objects.

This repository is intentionally isolated from the stable JARVIS execution
pipeline. It does not execute workflows, invoke models, perform retrieval,
or modify execution state.

The repository acts as the first persistence abstraction for workflow memory.
A database or vector store can be integrated later behind the same interface.
===============================================================================
"""

from __future__ import annotations

from typing import Any

from agent_engine.workflow_memory.workflow_record import WorkflowRecord


class WorkflowRepository:
    """
    In-memory repository for historical workflow records.

    Responsibilities:
    - Store WorkflowRecord objects by workflow_id.
    - Retrieve records by workflow_id.
    - Return all stored records.
    - Delete records.
    - Report repository size.

    Non-responsibilities:
    - Workflow execution.
    - Model inference.
    - Retrieval ranking.
    - Embedding generation.
    - State mutation in the stable JARVIS core.
    """

    def __init__(self) -> None:
        """
        Initialize an empty workflow repository.
        """

        self._records: dict[str, WorkflowRecord] = {}

    def save(self, record: WorkflowRecord) -> WorkflowRecord:
        """
        Save a workflow record.

        If a record with the same workflow_id already exists, it is replaced.
        A deep copy is stored so that external mutation of the original object
        does not directly mutate repository data.

        Args:
            record: WorkflowRecord instance to store.

        Returns:
            A deep copy of the stored WorkflowRecord.
        """

        if not isinstance(record, WorkflowRecord):
            raise TypeError(
                "record must be an instance of WorkflowRecord"
            )

        stored_record = record.model_copy(deep=True)
        self._records[stored_record.workflow_id] = stored_record

        return stored_record.model_copy(deep=True)

    def get(self, workflow_id: str) -> WorkflowRecord | None:
        """
        Retrieve a workflow record by workflow_id.

        Args:
            workflow_id: Unique workflow identifier.

        Returns:
            A deep copy of the matching record, or None if not found.
        """

        record = self._records.get(workflow_id)

        if record is None:
            return None

        return record.model_copy(deep=True)

    def list_all(self) -> list[WorkflowRecord]:
        """
        Return all stored workflow records.

        Returns:
            A list of deep-copied WorkflowRecord objects.
        """

        return [
            record.model_copy(deep=True)
            for record in self._records.values()
        ]

    def delete(self, workflow_id: str) -> bool:
        """
        Delete a workflow record by workflow_id.

        Args:
            workflow_id: Unique workflow identifier.

        Returns:
            True if a record was deleted, otherwise False.
        """

        if workflow_id not in self._records:
            return False

        del self._records[workflow_id]
        return True

    def exists(self, workflow_id: str) -> bool:
        """
        Check whether a workflow record exists.

        Args:
            workflow_id: Unique workflow identifier.

        Returns:
            True if the record exists, otherwise False.
        """

        return workflow_id in self._records

    def count(self) -> int:
        """
        Return the number of stored workflow records.
        """

        return len(self._records)

    def clear(self) -> None:
        """
        Remove all workflow records from the repository.
        """

        self._records.clear()