"""
===============================================================================
File Name   : action_request_builder.py
Module      : Automation Engine - Integration
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Converts an InterpretedTask produced by the Agent Brain into an
ActionRequest understood by the Automation Engine.

The ActionRequestBuilder is the integration boundary between:

    Agent Brain
        ↓
    InterpretedTask
        ↓
    ActionRequest
        ↓
    Automation Engine

Responsibilities:
    - Validate required task information
    - Convert task information into ActionRequest
    - Resolve the action category
    - Resolve the automation tool
    - Preserve parameters and metadata

The builder does NOT:
    - Execute actions
    - Dispatch actions
    - Manage retries
    - Manage task state
    - Make execution decisions

Author      : Team Agent
===============================================================================
"""

from __future__ import annotations

from agent_engine.agent_brain.models.interpreted_task import InterpretedTask
from agent_engine.contracts.action import ActionRequest
from agent_engine.contracts.enums import ActionCategory, ToolType


class ActionRequestBuilder:
    """
    Builds an ActionRequest from an InterpretedTask.

    This class forms the contract boundary between the Agent Brain and
    Automation Engine.
    """

    # =========================================================================
    # Public API
    # =========================================================================

    def build(
        self,
        task: InterpretedTask,
        *,
        timeout_seconds: float | None = None,
    ) -> ActionRequest:
        """
        Convert an InterpretedTask into an ActionRequest.

        Args:
            task:
                Interpreted task produced by the Agent Brain.

            timeout_seconds:
                Optional execution timeout supplied by the orchestrator.

        Returns:
            A validated ActionRequest.

        Raises:
            TypeError:
                If task is not an InterpretedTask.

            ValueError:
                If action or tool information is missing or invalid.
        """

        if not isinstance(task, InterpretedTask):
            raise TypeError(
                "task must be an InterpretedTask instance."
            )

        if not task.action or not task.action.strip():
            raise ValueError(
                f"Task {task.task_id} does not contain a valid action."
            )

        if not task.tool or not task.tool.strip():
            raise ValueError(
                f"Task {task.task_id} does not contain a valid tool."
            )

        category = self._resolve_category(task.action)
        tool = self._resolve_tool(task.tool)

        return ActionRequest(
            task_id=task.task_id,
            action=task.action.strip().lower(),
            category=category,
            tool=tool,
            parameters=dict(task.parameters),
            timeout_seconds=timeout_seconds,
            metadata=dict(task.metadata),
        )

    # =========================================================================
    # Category Resolution
    # =========================================================================

    @staticmethod
    def _resolve_category(action: str) -> ActionCategory:
        """
        Resolve an action to its ActionCategory.

        The mapping is intentionally simple for Level 1.

        More sophisticated action classification can be introduced later
        without changing the ActionRequest contract.
        """

        normalized_action = action.strip().lower()

        if normalized_action in {
            "open",
            "open_url",
            "search",
            "download",
            "close",
            "go_back",
            "go_forward",
            "refresh",
            "get_page_title",
            "get_current_url",
            "get_text",
            "extract_text",
            "new_tab",
            "switch_tab",
            "close_tab",
        }:
            return ActionCategory.BROWSER

        if normalized_action in {
            "click_element",
            "type_text",
            "press_key",
        }:
            return ActionCategory.KEYBOARD
        
        if normalized_action in {
            "move_mouse",
            "click",
            "double_click",
            "right_click",
            "mouse_down",
            "mouse_up",
            "scroll",
        }:
            return ActionCategory.MOUSE
        
        if normalized_action in {
            "take_screenshot",
            "capture_screen",
        }:
            return ActionCategory.SCREEN

        if normalized_action in {
            "copy",
            "move",
            "rename",
            "delete",
            "create_file",
        }:
            return ActionCategory.FILESYSTEM

        return ActionCategory.APPLICATION

    # =========================================================================
    # Tool Resolution
    # =========================================================================

    @staticmethod
    def _resolve_tool(tool: str) -> ToolType:
        """
        Convert the tool string from InterpretedTask into ToolType.
        """

        normalized_tool = tool.strip().lower()

        try:
            return ToolType(normalized_tool)
        except ValueError:
            raise ValueError(
                f"Unsupported automation tool: '{tool}'."
            ) from None