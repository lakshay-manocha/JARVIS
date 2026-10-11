"""
===============================================================================
File Name   : snapshot_collector.py
Module      : Integration / Environment
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
Implements Phase 8 Environment Snapshot Collector.

Collects live runtime environment state and constructs a valid StateSnapshot
for Model B (State Mismatch Classifier).

Safety Boundaries:
- Read-only: Does not modify the runtime environment.
- Non-fabrication: If a category cannot be inspected, marks it as "NOT_AVAILABLE".
- Exception-safe: Catches any OS/platform errors and falls back safely.
===============================================================================
"""

from __future__ import annotations

import logging
import time
from typing import Any

from agent_engine.state_mismatch.state_mismatch_contract import StateSnapshot

logger = logging.getLogger("jarvis.integration.snapshot_collector")


class EnvironmentSnapshotCollector:
    """
    Collects runtime snapshots conforming to Model B's StateSnapshot contract.
    """

    def __init__(
        self,
        application_provider: Any = None,
        process_provider: Any = None,
        browser_tab_provider: Any = None,
    ) -> None:
        self.application_provider = application_provider
        self.process_provider = process_provider
        self.browser_tab_provider = browser_tab_provider

    def capture_snapshot(
        self,
        applications: list[str] | str | None = None,
        files: list[str] | str | None = None,
        browser_tabs: list[str] | str | None = None,
        processes: list[str] | str | None = None,
        completed_subtasks: list[str] | str | None = None,
        resource_identities: list[str] | None = None,
    ) -> StateSnapshot:
        """
        Capture current environment snapshot.

        Parameters allow explicit injection by agents/orchestration.
        Where parameters are None, providers or safe defaults ("NOT_AVAILABLE")
        are used.
        """
        now = time.time()

        # 1. Applications
        collected_apps = applications
        if collected_apps is None and self.application_provider:
            try:
                collected_apps = self.application_provider()
            except Exception as exc:
                logger.warning("Failed collecting applications: %s", exc)
                collected_apps = "NOT_AVAILABLE"
        elif collected_apps is None:
            collected_apps = "NOT_AVAILABLE"

        # 2. Files
        collected_files = files if files is not None else "NOT_AVAILABLE"

        # 3. Browser Tabs
        collected_tabs = browser_tabs
        if collected_tabs is None and self.browser_tab_provider:
            try:
                collected_tabs = self.browser_tab_provider()
            except Exception as exc:
                logger.warning("Failed collecting browser tabs: %s", exc)
                collected_tabs = "NOT_AVAILABLE"
        elif collected_tabs is None:
            collected_tabs = "NOT_AVAILABLE"

        # 4. Processes
        collected_procs = processes
        if collected_procs is None and self.process_provider:
            try:
                collected_procs = self.process_provider()
            except Exception as exc:
                logger.warning("Failed collecting processes: %s", exc)
                collected_procs = "NOT_AVAILABLE"
        elif collected_procs is None:
            collected_procs = "NOT_AVAILABLE"

        # 5. Completed Subtasks
        collected_subtasks = (
            completed_subtasks
            if completed_subtasks is not None
            else "NOT_AVAILABLE"
        )

        # 6. Resource Identities
        identities: list[str] = []
        if resource_identities is not None:
            identities = list(resource_identities)
        else:
            if isinstance(collected_apps, list):
                identities.extend(f"app:{a.lower()}" for a in collected_apps)
            if isinstance(collected_files, list):
                identities.extend(f"file:{f.lower()}" for f in collected_files)
            if isinstance(collected_tabs, list):
                identities.extend(f"tab:{t.lower()}" for t in collected_tabs)

        return StateSnapshot(
            applications=collected_apps,
            files=collected_files,
            browser_tabs=collected_tabs,
            processes=collected_procs,
            completed_subtasks=collected_subtasks,
            timestamp=now,
            resource_identities=identities,
        )
