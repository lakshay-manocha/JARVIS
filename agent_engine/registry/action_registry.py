"""
===============================================================================
File Name   : action_registry.py
Module      : Agent Brain - Registry
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Maintains the canonical action vocabulary used by the Agent Brain.

The Action Registry normalizes supported action names and aliases into
standardized canonical actions.

This registry does NOT execute actions.

Execution handlers belong to the Automation Engine registry.

Responsibilities:
    • Maintain canonical action vocabulary
    • Normalize action aliases
    • Validate supported Agent Brain actions
    • Provide canonical action names to downstream modules

Author : Team JARVIS
===============================================================================
"""

from __future__ import annotations

from typing import Dict


class ActionRegistry:
    """
    Registry for canonical Agent Brain actions.

    The registry is responsible only for action vocabulary and normalization.
    It does not store or execute automation handlers.
    """

    # =========================================================================
    # Canonical Action Map
    # =========================================================================

    _ACTION_MAP: Dict[str, str] = {

        # ---------------------------------------------------------------------
        # Application / Website Opening
        # ---------------------------------------------------------------------

        "open": "open",
        "launch": "open",
        "start": "open",
        "run": "open",
        "execute": "open",

        # ---------------------------------------------------------------------
        # Web Search
        # ---------------------------------------------------------------------

        "search": "search",
        "find": "search",
        "lookup": "search",
        "google": "search",

        # ---------------------------------------------------------------------
        # File Download
        # ---------------------------------------------------------------------

        "download": "download",
        "fetch": "download",
        "grab": "download",
        "save": "download",

        # ---------------------------------------------------------------------
        # Document Summarization
        # ---------------------------------------------------------------------

        "summarize": "summarize",
        "summary": "summarize",

        # ---------------------------------------------------------------------
        # File Deletion
        # ---------------------------------------------------------------------

        "delete": "delete",
        "remove": "delete",
        "erase": "delete",

        # ---------------------------------------------------------------------
        # File Movement
        # ---------------------------------------------------------------------

        "move": "move",
        "transfer": "move",
        "relocate": "move",

        # ---------------------------------------------------------------------
        # File Copy
        # ---------------------------------------------------------------------

        "copy": "copy",
        "duplicate": "copy",

        # ---------------------------------------------------------------------
        # File Rename
        # ---------------------------------------------------------------------

        "rename": "rename",
        "change name": "rename",

        # ---------------------------------------------------------------------
        # Application Closing
        # ---------------------------------------------------------------------

        "close": "close",
        "exit": "close",
        "quit": "close",

        # =====================================================================
        # Keyboard Actions
        # =====================================================================

        # ---------------------------------------------------------------------
        # Type Text
        # ---------------------------------------------------------------------

        "type": "type",
        "write": "type",
        "enter text": "type",

        # ---------------------------------------------------------------------
        # Press Key
        # ---------------------------------------------------------------------

        "press": "press",
        "hit": "press",

        # ---------------------------------------------------------------------
        # Keyboard Hotkey
        # ---------------------------------------------------------------------

        "hotkey": "hotkey",
        "shortcut": "hotkey",

        # =====================================================================
        # Mouse Actions
        # =====================================================================

        # ---------------------------------------------------------------------
        # Move Mouse
        # ---------------------------------------------------------------------

        "move mouse": "move_mouse",
        "move cursor": "move_mouse",

        # ---------------------------------------------------------------------
        # Mouse Click
        # ---------------------------------------------------------------------

        "click": "mouse_click",
        "mouse click": "mouse_click",

        # ---------------------------------------------------------------------
        # Mouse Double Click
        # ---------------------------------------------------------------------

        "double click": "mouse_double_click",
        "double-click": "mouse_double_click",

        # ---------------------------------------------------------------------
        # Mouse Right Click
        # ---------------------------------------------------------------------

        "right click": "mouse_right_click",
        "right-click": "mouse_right_click",

        # ---------------------------------------------------------------------
        # Mouse Button Down
        # ---------------------------------------------------------------------

        "mouse down": "mouse_down",

        # ---------------------------------------------------------------------
        # Mouse Button Up
        # ---------------------------------------------------------------------

        "mouse up": "mouse_up",

        # ---------------------------------------------------------------------
        # Mouse Scroll
        # ---------------------------------------------------------------------

        "scroll": "mouse_scroll",
        "mouse scroll": "mouse_scroll",
    }

    # =========================================================================
    # Normalization
    # =========================================================================

    @classmethod
    def normalize(cls, word: str) -> str:
        """
        Return the canonical action for a supported action or alias.

        Args:
            word:
                Action name or supported alias.

        Returns:
            Canonical action name.
        """

        normalized_word = word.strip().lower()

        return cls._ACTION_MAP.get(
            normalized_word,
            normalized_word,
        )

    # =========================================================================
    # Membership Check
    # =========================================================================

    @classmethod
    def contains(cls, word: str) -> bool:
        """
        Check whether an action or action alias exists in the registry.

        Args:
            word:
                Action name or supported alias.

        Returns:
            True if the action is registered, otherwise False.
        """

        if not word or not word.strip():
            return False

        return word.strip().lower() in cls._ACTION_MAP

    # =========================================================================
    # Registry Inspection
    # =========================================================================

    @classmethod
    def all_actions(cls) -> Dict[str, str]:
        """
        Return a copy of the complete canonical action registry.
        """

        return cls._ACTION_MAP.copy()
