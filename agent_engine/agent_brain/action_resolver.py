"""
===============================================================================
File Name   : action_resolver.py
Module      : Agent Brain
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Resolves executable actions from detected task intents.

This module converts high-level intents into canonical actions using the
Action Registry.

Pipeline position:

    InterpretedTask
          ↓
    IntentDetector
          ↓
    ActionResolver
          ↓
    ParameterResolver
          ↓
    ToolResolver

The implementation is intentionally rule-based so it can later be replaced
by a machine-learning action prediction model without changing the rest
of the Agent Brain pipeline.

Responsibilities:
    • Read detected intents
    • Resolve canonical actions
    • Attach actions to interpreted tasks
    • Validate actions against ActionRegistry
    • Record processing logs

Author      : Team JARVIS
===============================================================================
"""

from __future__ import annotations

from agent_engine.agent_brain.models.processing_context import ProcessingContext
from agent_engine.contracts.enums import (
    IntentType,
    ProcessingStage,
)
from agent_engine.registry.action_registry import ActionRegistry


class ActionResolver:
    """
    Resolves canonical executable actions from detected intents.
    """

    # =========================================================================
    # Intent → Canonical Action Mapping
    # =========================================================================

    _INTENT_ACTION_MAP: dict[IntentType, str] = {

        # ---------------------------------------------------------------------
        # Application / Website
        # ---------------------------------------------------------------------

        IntentType.OPEN_APPLICATION: "open",

        IntentType.OPEN_WEBSITE: "open",

        # ---------------------------------------------------------------------
        # Web
        # ---------------------------------------------------------------------

        IntentType.SEARCH_WEB: "search",

        IntentType.DOWNLOAD_FILE: "download",

        # ---------------------------------------------------------------------
        # Document
        # ---------------------------------------------------------------------

        IntentType.SUMMARIZE_DOCUMENT: "summarize",

        # ---------------------------------------------------------------------
        # Filesystem
        # ---------------------------------------------------------------------

        IntentType.DELETE_FILE: "delete",

        IntentType.MOVE_FILE: "move",

        IntentType.COPY_FILE: "copy",

        IntentType.RENAME_FILE: "rename",

        # ---------------------------------------------------------------------
        # Keyboard
        # ---------------------------------------------------------------------

        IntentType.TYPE_TEXT: "type",

        IntentType.PRESS_KEY: "press",

        IntentType.HOTKEY: "hotkey",

        # ---------------------------------------------------------------------
        # Mouse
        # ---------------------------------------------------------------------

        IntentType.MOVE_MOUSE: "move_mouse",

        IntentType.MOUSE_CLICK: "mouse_click",

        IntentType.MOUSE_DOUBLE_CLICK: "mouse_double_click",

        IntentType.MOUSE_RIGHT_CLICK: "mouse_right_click",

        IntentType.MOUSE_DOWN: "mouse_down",

        IntentType.MOUSE_UP: "mouse_up",

        IntentType.MOUSE_SCROLL: "mouse_scroll",
    }

    # =========================================================================
    # Public API
    # =========================================================================

    def resolve(
        self,
        context: ProcessingContext,
    ) -> ProcessingContext:
        """
        Resolve canonical actions for all interpreted tasks.

        The resolver expects intent detection to have already taken place.

        Parameters
        ----------
        context : ProcessingContext
            Current Agent Brain processing context.

        Returns
        -------
        ProcessingContext
            Updated context containing resolved actions.
        """

        context.current_stage = ProcessingStage.RESOLVING_ACTIONS

        context.log("Action resolution started.")

        resolved_count = 0
        unresolved_count = 0

        for task in context.interpreted_tasks:

            # -----------------------------------------------------------------
            # Validate intent availability
            # -----------------------------------------------------------------

            if task.intent is None:

                task.action = None

                unresolved_count += 1

                context.log(
                    f"Action resolution skipped for Task "
                    f"{task.task_id}: intent is missing."
                )

                continue

            # -----------------------------------------------------------------
            # Resolve action from intent
            # -----------------------------------------------------------------

            action = self._resolve_action(
                task.intent.intent
            )

            task.action = action

            # -----------------------------------------------------------------
            # Resolution result
            # -----------------------------------------------------------------

            if action is not None:

                resolved_count += 1

                context.log(
                    f"Action resolved for Task "
                    f"{task.task_id}: {action}"
                )

            else:

                unresolved_count += 1

                context.log(
                    f"Action resolution failed for Task "
                    f"{task.task_id}: unsupported intent "
                    f"{task.intent.intent}"
                )

        context.log(
            f"Action resolution completed. "
            f"Resolved: {resolved_count}, "
            f"Unresolved: {unresolved_count}"
        )

        return context

    # =========================================================================
    # Internal Resolution
    # =========================================================================

    @classmethod
    def _resolve_action(
        cls,
        intent: IntentType,
    ) -> str | None:
        """
        Resolve a canonical action from an IntentType.

        Resolution flow:

            IntentType
                ↓
            Intent → Action mapping
                ↓
            ActionRegistry normalization
                ↓
            Canonical action validation
                ↓
            Canonical action

        Returns
        -------
        str | None
            Canonical action registered in ActionRegistry, or None when
            the intent cannot be mapped to a supported executable action.
        """

        # ---------------------------------------------------------------------
        # Step 1: Resolve intent to action
        # ---------------------------------------------------------------------

        action = cls._INTENT_ACTION_MAP.get(intent)

        if action is None:
            return None

        # ---------------------------------------------------------------------
        # Step 2: Normalize the action through the registry
        # ---------------------------------------------------------------------

        canonical_action = ActionRegistry.normalize(action)

        # ---------------------------------------------------------------------
        # Step 3: Validate canonical action
        #
        # ActionRegistry.contains() checks registry keys/aliases.
        # We validate against the registry's canonical values as well.
        # ---------------------------------------------------------------------

        registered_actions = ActionRegistry.all_actions()

        canonical_actions = set(
            registered_actions.values()
        )

        if canonical_action not in canonical_actions:
            return None

        # ---------------------------------------------------------------------
        # Step 4: Return canonical executable action
        # ---------------------------------------------------------------------

        return canonical_action