"""
===============================================================================
File Name   : browser_backend.py
Module      : Automation Agents - Browser
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Playwright-backed browser execution layer.

BrowserBackend owns the real browser resources. BrowserAutomationAgent owns
the JARVIS AutomationAgent contract and converts backend results/errors into
AutomationExecutionResult.

Playwright is imported lazily so unit tests can mock this backend without
requiring Playwright to be installed.
===============================================================================
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus

from agent_engine.automation.agents.browser.browser_config import BrowserConfig
from agent_engine.automation.exceptions import (
    AgentExecutionError,
    AgentInitializationError,
    AutomationTimeoutError,
    AutomationValidationError,
)


class BrowserBackend:
    """Concrete Playwright backend used by BrowserAutomationAgent."""

    def __init__(self, config: BrowserConfig | None = None) -> None:
        self._config = config or BrowserConfig()
        self._playwright: Any = None
        self._browser: Any = None
        self._context: Any = None
        self._page: Any = None

    @property
    def config(self) -> BrowserConfig:
        return self._config

    @property
    def page(self) -> Any:
        return self._page

    @property
    def initialized(self) -> bool:
        return self._page is not None

    def initialize(self) -> None:
        if self.initialized:
            return

        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise AgentInitializationError(
                "Playwright is not installed. "
                "Install it with 'pip install playwright' and then run "
                "'python -m playwright install chromium'."
            ) from exc

        try:
            self._playwright = sync_playwright().start()

            browser_name = self._config.browser

            if browser_name in {"chromium", "chrome", "edge", "brave"}:
                channel = self._config.browser_channel

                if channel is None:
                    channel_map = {
                        "chrome": "chrome",
                        "edge": "msedge",
                        "brave": "brave",
                    }
                    channel = channel_map.get(browser_name)

                launch_kwargs: dict[str, Any] = {
                    "headless": self._config.headless,
                }

                if channel:
                    launch_kwargs["channel"] = channel

                self._browser = self._playwright.chromium.launch(
                    **launch_kwargs
                )

            elif browser_name == "firefox":
                self._browser = self._playwright.firefox.launch(
                    headless=self._config.headless
                )

            elif browser_name in {"webkit", "safari"}:
                self._browser = self._playwright.webkit.launch(
                    headless=self._config.headless
                )

            else:
                raise AgentInitializationError(
                    f"Unsupported Playwright browser: '{browser_name}'."
                )

            self._context = self._browser.new_context(
                viewport={
                    "width": self._config.viewport_width,
                    "height": self._config.viewport_height,
                }
            )
            self._page = self._context.new_page()
            self._page.set_default_timeout(
                self._config.default_timeout_ms
            )

        except AgentInitializationError:
            self._safe_close_resources()
            raise
        except Exception as exc:
            self._safe_close_resources()
            raise AgentInitializationError(
                f"Failed to initialize browser: {exc}"
            ) from exc

    def execute(
        self,
        action: str,
        parameters: dict[str, Any] | None = None,
        *,
        timeout_seconds: float | None = None,
    ) -> Any:
        """Execute one browser action through Playwright."""
        if not self.initialized:
            raise AgentExecutionError(
                "Browser backend is not initialized."
            )

        normalized_action = action.strip().lower()
        parameters = dict(parameters or {})

        if timeout_seconds is not None:
            if timeout_seconds <= 0:
                raise AutomationValidationError(
                    "timeout_seconds must be greater than 0."
                )
            timeout_ms = int(timeout_seconds * 1000)
        else:
            timeout_ms = self._config.default_timeout_ms

        try:
            return self._execute_action(
                normalized_action,
                parameters,
                timeout_ms=timeout_ms,
            )
        except Exception as exc:
            if exc.__class__.__name__ == "TimeoutError":
                raise AutomationTimeoutError(
                    f"Browser action '{normalized_action}' timed out."
                ) from exc

            if isinstance(
                exc,
                (
                    AutomationValidationError,
                    AutomationTimeoutError,
                    AgentExecutionError,
                ),
            ):
                raise

            raise AgentExecutionError(
                f"Browser action '{normalized_action}' failed: {exc}"
            ) from exc

    def _execute_action(
        self,
        action: str,
        parameters: dict[str, Any],
        *,
        timeout_ms: int,
    ) -> Any:
        page = self._page

        if action in {"open", "open_url"}:
            url = self._required_string(parameters, "url")
            page.set_default_timeout(timeout_ms)
            response = page.goto(url, wait_until="domcontentloaded")
            return {
                "url": page.url,
                "status": response.status if response else None,
                "title": page.title(),
            }

        if action == "search":
            query = self._required_string(parameters, "query")
            url = self._config.search_engine_url.format(
                query=quote_plus(query)
            )
            page.set_default_timeout(timeout_ms)
            response = page.goto(url, wait_until="domcontentloaded")
            return {
                "query": query,
                "url": page.url,
                "status": response.status if response else None,
                "title": page.title(),
            }

        if action == "go_back":
            page.set_default_timeout(timeout_ms)
            response = page.go_back(wait_until="domcontentloaded")
            return {
                "url": page.url,
                "status": response.status if response else None,
            }

        if action == "go_forward":
            page.set_default_timeout(timeout_ms)
            response = page.go_forward(wait_until="domcontentloaded")
            return {
                "url": page.url,
                "status": response.status if response else None,
            }

        if action == "refresh":
            page.set_default_timeout(timeout_ms)
            response = page.reload(wait_until="domcontentloaded")
            return {
                "url": page.url,
                "status": response.status if response else None,
                "title": page.title(),
            }

        if action in {"click", "click_element"}:
            selector = self._required_string(parameters, "selector")
            page.set_default_timeout(timeout_ms)
            page.locator(selector).click()
            return {
                "selector": selector,
                "url": page.url,
            }

        if action == "type_text":
            selector = self._required_string(parameters, "selector")
            text = self._required_string(parameters, "text")
            page.set_default_timeout(timeout_ms)
            page.locator(selector).fill(text)
            return {
                "selector": selector,
                "text": text,
            }

        if action == "get_page_title":
            return page.title()

        if action == "get_current_url":
            return page.url

        if action in {"get_text", "extract_text"}:
            selector = parameters.get("selector")
            page.set_default_timeout(timeout_ms)

            if selector:
                return page.locator(selector).inner_text()

            return page.locator("body").inner_text()

        if action == "new_tab":
            new_page = self._context.new_page()
            new_page.set_default_timeout(timeout_ms)
            self._page = new_page
            return {
                "tab_index": self._current_tab_index(),
                "url": new_page.url,
            }

        if action == "switch_tab":
            tab_index = self._required_non_negative_int(
                parameters,
                "index",
            )
            pages = self._context.pages

            if tab_index >= len(pages):
                raise AutomationValidationError(
                    f"Tab index {tab_index} is out of range. "
                    f"Available tabs: {len(pages)}."
                )

            self._page = pages[tab_index]
            self._page.set_default_timeout(timeout_ms)

            return {
                "tab_index": tab_index,
                "url": self._page.url,
            }

        if action in {"close_tab", "close"}:
            pages = self._context.pages
            current = self._page

            current.close()

            remaining = self._context.pages

            if remaining:
                self._page = remaining[-1]
            else:
                self._page = self._context.new_page()
                self._page.set_default_timeout(timeout_ms)

            return {
                "closed": True,
                "remaining_tabs": len(self._context.pages),
                "url": self._page.url,
            }

        raise AutomationValidationError(
            f"Unsupported browser action: '{action}'."
        )

    @staticmethod
    def _required_string(
        parameters: dict[str, Any],
        name: str,
    ) -> str:
        value = parameters.get(name)

        if not isinstance(value, str) or not value.strip():
            raise AutomationValidationError(
                f"Parameter '{name}' must be a non-empty string."
            )

        return value.strip()

    @staticmethod
    def _required_non_negative_int(
        parameters: dict[str, Any],
        name: str,
    ) -> int:
        value = parameters.get(name)

        if isinstance(value, bool) or not isinstance(value, int):
            raise AutomationValidationError(
                f"Parameter '{name}' must be a non-negative integer."
            )

        if value < 0:
            raise AutomationValidationError(
                f"Parameter '{name}' cannot be negative."
            )

        return value

    def _current_tab_index(self) -> int:
        pages = self._context.pages
        return pages.index(self._page)

    def cleanup(self) -> None:
        self._safe_close_resources()

    def _safe_close_resources(self) -> None:
        for resource in (
            self._page,
            self._context,
            self._browser,
        ):
            try:
                if resource is not None:
                    resource.close()
            except Exception:
                pass

        try:
            if self._playwright is not None:
                self._playwright.stop()
        except Exception:
            pass

        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None
