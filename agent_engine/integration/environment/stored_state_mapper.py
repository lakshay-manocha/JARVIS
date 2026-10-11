"""
===============================================================================
File Name   : stored_state_mapper.py
Module      : Integration / Environment
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
Implements Phase 9 Stored-State Mapping.

Maps JARVIS stored checkpoints, StateCheckpoint objects, TaskRuntimeState, or
historical workflow states into Model B's StateSnapshot contract.

Guarantees:
- Preserves semantic information without modifying StateManager.
- Never fabricates missing resources; uses 'NOT_AVAILABLE' when absent.
===============================================================================
"""

from __future__ import annotations

import logging
from typing import Any

from agent_engine.state_manager.state_checkpoint import StateCheckpoint
from agent_engine.state_mismatch.state_mismatch_contract import StateSnapshot

logger = logging.getLogger("jarvis.integration.stored_state_mapper")


class StoredStateMapper:
    """
    Translates JARVIS checkpoints and runtime state structures into StateSnapshot.
    """

    @classmethod
    def from_checkpoint(
        cls,
        checkpoint: StateCheckpoint,
        context_payload: dict[str, Any] | None = None,
    ) -> StateSnapshot:
        """
        Map a StateCheckpoint and optional context payload to a StateSnapshot.
        """
        payload = context_payload or {}

        # Extract applications if recorded in checkpoint context
        applications = payload.get("applications", "NOT_AVAILABLE")
        files = payload.get("files", "NOT_AVAILABLE")
        browser_tabs = payload.get("browser_tabs", "NOT_AVAILABLE")
        processes = payload.get("processes", "NOT_AVAILABLE")

        # Map task progress / status to completed subtasks if applicable
        completed_subtasks = payload.get("completed_subtasks")
        if completed_subtasks is None:
            if checkpoint.progress >= 1.0 or checkpoint.status.value == "COMPLETED":
                completed_subtasks = [f"task_{checkpoint.task_id}"]
            else:
                completed_subtasks = "NOT_AVAILABLE"

        identities: list[str] = []
        if isinstance(applications, list):
            identities.extend(f"app:{a.lower()}" for a in applications)
        if isinstance(files, list):
            identities.extend(f"file:{f.lower()}" for f in files)
        if isinstance(browser_tabs, list):
            identities.extend(f"tab:{t.lower()}" for t in browser_tabs)

        ts = (
            checkpoint.timestamp.timestamp()
            if checkpoint.timestamp is not None
            else None
        )

        return StateSnapshot(
            applications=applications,
            files=files,
            browser_tabs=browser_tabs,
            processes=processes,
            completed_subtasks=completed_subtasks,
            timestamp=ts,
            resource_identities=identities,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StateSnapshot:
        """
        Map a raw dictionary into a validated StateSnapshot.
        """
        apps = data.get("applications", "NOT_AVAILABLE")
        files = data.get("files", "NOT_AVAILABLE")
        tabs = data.get("browser_tabs", "NOT_AVAILABLE")
        procs = data.get("processes", "NOT_AVAILABLE")
        subtasks = data.get("completed_subtasks", "NOT_AVAILABLE")

        identities = data.get("resource_identities")
        if identities is None:
            identities = []
            if isinstance(apps, list):
                identities.extend(f"app:{a.lower()}" for a in apps)
            if isinstance(files, list):
                identities.extend(f"file:{f.lower()}" for f in files)
            if isinstance(tabs, list):
                identities.extend(f"tab:{t.lower()}" for t in tabs)

        return StateSnapshot(
            applications=apps,
            files=files,
            browser_tabs=tabs,
            processes=procs,
            completed_subtasks=subtasks,
            timestamp=data.get("timestamp"),
            resource_identities=identities,
        )
