"""
===============================================================================
File Name   : deterministic_checker.py
Module      : Integration / Guard
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
Implements Phase 11 Deterministic State Checker.

Provides explicit hard-difference detection across runtime state collections
independently of Model B's ML predictions.

Outputs ChangedResource items with ResourceChange (ADDED, MISSING).
===============================================================================
"""

from __future__ import annotations

import logging

from agent_engine.state_mismatch.state_mismatch_contract import (
    ChangedResource,
    ResourceChange,
    ResourceType,
    StateSnapshot,
)

logger = logging.getLogger("jarvis.integration.deterministic_checker")


class DeterministicStateChecker:
    """
    Computes exact, observable resource discrepancies between stored and current states.
    """

    @staticmethod
    def check_differences(
        stored_state: StateSnapshot,
        current_state: StateSnapshot,
    ) -> list[ChangedResource]:
        """
        Compare stored_state and current_state, returning a list of ChangedResource.
        """
        changed: list[ChangedResource] = []

        def compare_collection(
            stored_val: list[str] | str,
            current_val: list[str] | str,
            res_type: ResourceType,
        ) -> None:
            # If both are unavailable, no verifiable diff
            if stored_val == "NOT_AVAILABLE" and current_val == "NOT_AVAILABLE":
                return

            stored_set = (
                set(stored_val)
                if isinstance(stored_val, list)
                else set()
            )
            current_set = (
                set(current_val)
                if isinstance(current_val, list)
                else set()
            )

            # Missing: was expected in stored state, but absent in current
            if isinstance(stored_val, list):
                for item in sorted(stored_set - current_set):
                    if item.strip():
                        changed.append(
                            ChangedResource(
                                type=res_type,
                                identifier=item,
                                change=ResourceChange.MISSING,
                            )
                        )

            # Added: absent in stored state, but present in current
            if isinstance(current_val, list):
                for item in sorted(current_set - stored_set):
                    if item.strip():
                        changed.append(
                            ChangedResource(
                                type=res_type,
                                identifier=item,
                                change=ResourceChange.ADDED,
                            )
                        )

        # 1. Applications
        compare_collection(
            stored_state.applications,
            current_state.applications,
            ResourceType.APPLICATION,
        )

        # 2. Files
        compare_collection(
            stored_state.files,
            current_state.files,
            ResourceType.FILE,
        )

        # 3. Browser Tabs
        compare_collection(
            stored_state.browser_tabs,
            current_state.browser_tabs,
            ResourceType.BROWSER_TAB,
        )

        # 4. Processes
        compare_collection(
            stored_state.processes,
            current_state.processes,
            ResourceType.PROCESS,
        )

        # 5. Completed Subtasks
        compare_collection(
            stored_state.completed_subtasks,
            current_state.completed_subtasks,
            ResourceType.COMPLETED_SUBTASK,
        )

        return changed
