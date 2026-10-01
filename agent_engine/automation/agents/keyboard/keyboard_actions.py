"""
===============================================================================
File Name   : keyboard_actions.py
Module      : Automation Agents - Keyboard
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Provides the low-level keyboard operations used by the JARVIS Keyboard
Automation Agent.

This module is responsible only for interaction with pynput.

It does NOT:
    - create ActionRequest objects
    - perform planning
    - resolve tools
    - manage retries
    - manage fallbacks
    - manage task state
    - communicate with the LLM

The higher-level KeyboardAutomationAgent is responsible for integrating these
operations with the JARVIS AutomationAgent contract.
===============================================================================
"""

from __future__ import annotations

from typing import Iterable

from pynput.keyboard import Controller, Key

from agent_engine.automation.exceptions import (
    AutomationValidationError,
    AgentExecutionError,
)


# =============================================================================
# Common Keyboard Keys
# =============================================================================

KEY_MAP = {
    "enter": Key.enter,
    "esc": Key.esc,
    "escape": Key.esc,
    "tab": Key.tab,
    "space": Key.space,
    "backspace": Key.backspace,
    "delete": Key.delete,

    "shift": Key.shift,
    "ctrl": Key.ctrl,
    "alt": Key.alt,
    "cmd": Key.cmd,
    "windows": Key.cmd,

    "up": Key.up,
    "down": Key.down,
    "left": Key.left,
    "right": Key.right,

    "home": Key.home,
    "end": Key.end,
    "page_up": Key.page_up,
    "page_down": Key.page_down,

    "insert": Key.insert,
    "caps_lock": Key.caps_lock,
    "num_lock": Key.num_lock,

    "f1": Key.f1,
    "f2": Key.f2,
    "f3": Key.f3,
    "f4": Key.f4,
    "f5": Key.f5,
    "f6": Key.f6,
    "f7": Key.f7,
    "f8": Key.f8,
    "f9": Key.f9,
    "f10": Key.f10,
    "f11": Key.f11,
    "f12": Key.f12,
}


# =============================================================================
# Keyboard Actions
# =============================================================================

class KeyboardActions:
    """
    Low-level keyboard operations.

    This class is responsible only for interacting with pynput.
    """

    def __init__(self, controller=None) -> None:
        self.controller = controller or Controller()

    # -------------------------------------------------------------------------
    # Key Resolution
    # -------------------------------------------------------------------------

    @staticmethod
    def resolve_key(key: str):
        """
        Convert a human-readable key name into a pynput key.

        Supports:
            - a-z
            - 0-9
            - named special keys
            - f1-f12
        """

        if not isinstance(key, str):
            raise AutomationValidationError(
                "key must be a string."
            )

        if not key.strip():
            raise AutomationValidationError(
                "key cannot be empty."
            )

        normalized = key.strip().lower()

        # Single alphanumeric character.
        if len(normalized) == 1 and normalized.isalnum():
            return normalized

        if normalized in KEY_MAP:
            return KEY_MAP[normalized]

        raise AutomationValidationError(
            f"Unsupported key: {key}"
        )

    # -------------------------------------------------------------------------
    # Type Text
    # -------------------------------------------------------------------------

    def type_text(self, text: str) -> None:
        """
        Type arbitrary text character by character.
        """

        if not isinstance(text, str):
            raise AutomationValidationError(
                "text must be a string."
            )

        if not text:
            raise AutomationValidationError(
                "text cannot be empty."
            )

        try:
            for char in text:
                self.controller.press(char)
                self.controller.release(char)

        except Exception as exc:
            raise AgentExecutionError(
                f"Failed to type text: {exc}"
            ) from exc

    # -------------------------------------------------------------------------
    # Press Key
    # -------------------------------------------------------------------------

    def press_key(self, key: str) -> None:
        """
        Press and release a single key.
        """

        resolved_key = self.resolve_key(key)

        try:
            self.controller.press(resolved_key)
            self.controller.release(resolved_key)

        except Exception as exc:

            # Best-effort release.
            try:
                self.controller.release(resolved_key)
            except Exception:
                pass

            raise AgentExecutionError(
                f"Failed to press key '{key}': {exc}"
            ) from exc

    # -------------------------------------------------------------------------
    # Key Down
    # -------------------------------------------------------------------------

    def key_down(self, key: str) -> None:
        """
        Press and hold a key.
        """

        resolved_key = self.resolve_key(key)

        try:
            self.controller.press(resolved_key)

        except Exception as exc:
            raise AgentExecutionError(
                f"Failed to press key down '{key}': {exc}"
            ) from exc

    # -------------------------------------------------------------------------
    # Key Up
    # -------------------------------------------------------------------------

    def key_up(self, key: str) -> None:
        """
        Release a previously held key.
        """

        resolved_key = self.resolve_key(key)

        try:
            self.controller.release(resolved_key)

        except Exception as exc:
            raise AgentExecutionError(
                f"Failed to release key '{key}': {exc}"
            ) from exc

    # -------------------------------------------------------------------------
    # Hotkey
    # -------------------------------------------------------------------------

    def hotkey(self, keys: Iterable[str]) -> None:
        """
        Press a combination of keys.

        Keys are pressed in order and released in reverse order.
        """

        if not isinstance(keys, (list, tuple)):
            raise AutomationValidationError(
                "keys must be a list or tuple."
            )

        if not keys:
            raise AutomationValidationError(
                "keys cannot be empty."
            )

        resolved_keys = [
            self.resolve_key(key)
            for key in keys
        ]

        pressed_keys = []

        try:

            # Press in order.
            for key in resolved_keys:
                self.controller.press(key)
                pressed_keys.append(key)

            # Release in reverse order.
            for key in reversed(pressed_keys):
                self.controller.release(key)

            pressed_keys.clear()

        except Exception as exc:

            # Critical safety behavior:
            # release anything that was successfully pressed.
            for key in reversed(pressed_keys):
                try:
                    self.controller.release(key)
                except Exception:
                    pass

            raise AgentExecutionError(
                f"Failed to execute hotkey: {exc}"
            ) from exc

    # -------------------------------------------------------------------------
    # Release All
    # -------------------------------------------------------------------------

    def release_all(self) -> None:
        """
        Best-effort release of modifier keys.

        Used during cleanup.
        """

        modifiers = [
            Key.ctrl,
            Key.alt,
            Key.shift,
            Key.cmd,
        ]

        for key in modifiers:
            try:
                self.controller.release(key)
            except Exception:
                pass