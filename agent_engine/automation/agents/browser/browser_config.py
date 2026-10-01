"""
===============================================================================
File Name   : browser_config.py
Module      : Automation Agents - Browser
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Configuration for the real Browser Automation Agent.

The configuration deliberately contains browser/runtime settings only.
Execution policy, retry, fallback, and task-state management remain in the
existing Agent Brain / Decision Manager / State Manager architecture.
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BrowserConfig:
    """Runtime configuration for the BrowserAutomationAgent."""

    browser: str = "chromium"
    headless: bool = False
    default_timeout_ms: int = 30_000
    viewport_width: int = 1280
    viewport_height: int = 720
    search_engine_url: str = "https://www.google.com/search?q={query}"
    browser_channel: str | None = None

    def __post_init__(self) -> None:
        browser = self.browser.strip().lower()

        if not browser:
            raise ValueError("browser cannot be empty.")

        if self.default_timeout_ms <= 0:
            raise ValueError("default_timeout_ms must be greater than 0.")

        if self.viewport_width <= 0:
            raise ValueError("viewport_width must be greater than 0.")

        if self.viewport_height <= 0:
            raise ValueError("viewport_height must be greater than 0.")

        if "{query}" not in self.search_engine_url:
            raise ValueError(
                "search_engine_url must contain the '{query}' placeholder."
            )

        object.__setattr__(self, "browser", browser)
