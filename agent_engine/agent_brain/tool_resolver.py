"""
===============================================================================
File Name   : tool_resolver.py
Module      : Agent Brain
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Resolves the appropriate automation tool/controller required to execute each
interpreted task.

The Tool Resolver examines the resolved action and extracted parameters and
maps them to the most suitable automation controller. This keeps downstream
components independent from natural language and allows the Dispatcher to
invoke the correct controller.

Current implementation is rule-based and intentionally modular so it can be
replaced with an ML-based routing model in the future.

Responsibilities:
    • Resolve execution tool
    • Assign controller to each task
    • Update processing stage
    • Record processing logs

Author      : Team JARVIS
===============================================================================
"""

from agent_engine.agent_brain.models.processing_context import ProcessingContext
from agent_engine.contracts.enums import ProcessingStage, ToolType


class ToolResolver:
    """
    Resolves the automation tool required for each interpreted task.
    """

    # ------------------------------------------------------------------
    # Canonical Action → Tool Mapping
    # ------------------------------------------------------------------

    _ACTION_TOOL_MAP = {

        # --------------------------------------------------------------
        # Browser Automation
        # --------------------------------------------------------------

        "search": ToolType.BROWSER.value,
        "download": ToolType.BROWSER.value,

        # --------------------------------------------------------------
        # Filesystem Automation
        # --------------------------------------------------------------

        "delete": ToolType.FILESYSTEM.value,
        "move": ToolType.FILESYSTEM.value,
        "copy": ToolType.FILESYSTEM.value,
        "rename": ToolType.FILESYSTEM.value,
        "summarize": ToolType.FILESYSTEM.value,

        # --------------------------------------------------------------
        # Keyboard Automation
        # --------------------------------------------------------------

        "type": ToolType.KEYBOARD.value,
        "press": ToolType.KEYBOARD.value,
        "hotkey": ToolType.KEYBOARD.value,

        # --------------------------------------------------------------
        # Mouse Automation
        # --------------------------------------------------------------

        "move_mouse": ToolType.MOUSE.value,
        "mouse_click": ToolType.MOUSE.value,
        "mouse_double_click": ToolType.MOUSE.value,
        "mouse_right_click": ToolType.MOUSE.value,
        "mouse_down": ToolType.MOUSE.value,
        "mouse_up": ToolType.MOUSE.value,
        "mouse_scroll": ToolType.MOUSE.value,
    }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve(
        self,
        context: ProcessingContext
    ) -> ProcessingContext:
        """
        Resolve execution tool for every interpreted task.

        Parameters
        ----------
        context : ProcessingContext
            Current Agent Brain processing context.

        Returns
        -------
        ProcessingContext
            Updated processing context containing resolved tools.
        """

        context.current_stage = ProcessingStage.TOOL_RESOLUTION

        context.log("Tool resolution started.")

        resolved_count = 0
        unresolved_count = 0

        for task in context.interpreted_tasks:

            task.tool = self._resolve_tool(
                task.action,
                task.parameters
            )

            if task.tool is not None:

                resolved_count += 1

                context.log(
                    f"Tool resolved for Task "
                    f"{task.task_id}: {task.tool}"
                )

            else:

                unresolved_count += 1

                context.log(
                    f"Tool resolution failed for Task "
                    f"{task.task_id}: unsupported action "
                    f"{task.action}"
                )

        context.log(
            f"Tool resolution completed. "
            f"Resolved: {resolved_count}, "
            f"Unresolved: {unresolved_count}"
        )

        return context

    # ------------------------------------------------------------------
    # Tool Resolution
    # ------------------------------------------------------------------

    @classmethod
    def _resolve_tool(
        cls,
        action: str | None,
        parameters: dict
    ) -> str | None:
        """
        Resolve the automation tool based on canonical action and parameters.

        Parameters
        ----------
        action : str | None
            Canonical action resolved by ActionResolver.

        parameters : dict
            Structured parameters resolved by ParameterResolver.

        Returns
        -------
        str | None
            ToolType value required to execute the action.
        """

        if action is None:
            return None

        # --------------------------------------------------------------
        # Normalize action
        # --------------------------------------------------------------

        action = action.strip().lower()

        # --------------------------------------------------------------
        # Browser / Filesystem / Keyboard / Mouse
        # --------------------------------------------------------------

        if action in cls._ACTION_TOOL_MAP:
            return cls._ACTION_TOOL_MAP[action]

        # --------------------------------------------------------------
        # Open Application / Website
        # --------------------------------------------------------------
        #
        # "open" is context-dependent:
        #
        #   open Chrome       → desktop_agent
        #   open Notepad      → desktop_agent
        #   open google.com   → browser_agent
        #   open URL          → browser_agent
        #
        # Therefore, unlike the other actions, "open" cannot be resolved
        # from the action alone.
        # --------------------------------------------------------------

        if action == "open":

            # Website / URL takes priority because an explicit website
            # target should be handled by the browser agent.

            if (
                "url" in parameters
                or "website" in parameters
            ):
                return ToolType.BROWSER.value

            # Applications and browsers installed on the system are
            # launched through the desktop agent.

            if (
                "application" in parameters
                or "browser" in parameters
            ):
                return ToolType.DESKTOP.value

            # No sufficient information to determine the controller.

            return None

        # --------------------------------------------------------------
        # Unsupported Action
        # --------------------------------------------------------------

        return None