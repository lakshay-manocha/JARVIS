"""
===============================================================================
File Name   : browser_registry.py
Module      : Registry
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Maintains the canonical browser registry used throughout the Agent Brain.

This registry normalizes browser aliases into a single canonical browser name
and stores metadata that can later be used by the automation engine.

Author : Team JARVIS
===============================================================================
"""

from copy import deepcopy
from typing import Dict, Optional


class BrowserRegistry:
    """
    Registry responsible for browser normalization.
    """

    CATEGORY = "BROWSER"

    _BROWSER_MAP: Dict[str, Dict[str, str]] = {

        # ------------------------------------------------------------------
        # Google Chrome
        # ------------------------------------------------------------------

        "chrome": {
            "canonical": "chrome",
            "display_name": "Google Chrome"
        },

        "google chrome": {
            "canonical": "chrome",
            "display_name": "Google Chrome"
        },

        "chrome browser": {
            "canonical": "chrome",
            "display_name": "Google Chrome"
        },

        # ------------------------------------------------------------------
        # Mozilla Firefox
        # ------------------------------------------------------------------

        "firefox": {
            "canonical": "firefox",
            "display_name": "Mozilla Firefox"
        },

        "mozilla firefox": {
            "canonical": "firefox",
            "display_name": "Mozilla Firefox"
        },

        # ------------------------------------------------------------------
        # Microsoft Edge
        # ------------------------------------------------------------------

        "edge": {
            "canonical": "edge",
            "display_name": "Microsoft Edge"
        },

        "microsoft edge": {
            "canonical": "edge",
            "display_name": "Microsoft Edge"
        },

        "edge browser": {
            "canonical": "edge",
            "display_name": "Microsoft Edge"
        },

        # ------------------------------------------------------------------
        # Safari
        # ------------------------------------------------------------------

        "safari": {
            "canonical": "safari",
            "display_name": "Safari"
        },

        # ------------------------------------------------------------------
        # Opera
        # ------------------------------------------------------------------

        "opera": {
            "canonical": "opera",
            "display_name": "Opera"
        },

        # ------------------------------------------------------------------
        # Brave
        # ------------------------------------------------------------------

        "brave": {
            "canonical": "brave",
            "display_name": "Brave Browser"
        }
    }

    @classmethod
    def normalize(cls, browser_name: str) -> str:
        """
        Returns the canonical browser name.
        """

        browser_name = browser_name.lower().strip()

        if browser_name in cls._BROWSER_MAP:
            return cls._BROWSER_MAP[browser_name]["canonical"]

        return browser_name

    @classmethod
    def contains(cls, browser_name: str) -> bool:
        """
        Checks whether a browser exists in the registry.
        """

        return browser_name.lower().strip() in cls._BROWSER_MAP

    @classmethod
    def get_metadata(cls, browser_name: str) -> Optional[Dict[str, str]]:
        """
        Returns metadata associated with the browser.
        """
        browser_name = browser_name.lower().strip()
        return deepcopy(cls._BROWSER_MAP.get(browser_name, None))

    @classmethod
    def all_browsers(cls) -> Dict[str, Dict[str, str]]:
        """
        Returns the complete browser registry.
        """

        return cls._BROWSER_MAP.copy()