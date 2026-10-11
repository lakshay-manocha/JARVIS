"""
===============================================================================
File Name   : parameter_resolver.py
Module      : Agent Brain
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Extracts structured parameters from interpreted tasks.

The Parameter Resolver identifies entities and execution parameters such as
applications, browsers, websites, URLs, search queries, and file types.

The extracted parameters are attached to each InterpretedTask for downstream
modules such as the Tool Resolver, Action Resolver, Planner, and Automation
Dispatcher.

This implementation is intentionally rule-based so it can later be replaced
with an ML, NER, or LLM-based parameter extraction model without changing
the rest of the Agent Brain pipeline.

Responsibilities:
    • Extract browser names
    • Extract application names
    • Extract website names
    • Extract URLs
    • Extract search queries
    • Extract file types
    • Populate task parameters
    • Record processing logs

Author      : Team JARVIS
===============================================================================
"""

from __future__ import annotations

import re

from agent_engine.agent_brain.models.processing_context import ProcessingContext
from agent_engine.contracts.enums import ProcessingStage

from agent_engine.registry.browser_registry import BrowserRegistry
from agent_engine.registry.application_registry import ApplicationRegistry
from agent_engine.registry.website_registry import WebsiteRegistry
from agent_engine.registry.filetype_registry import FileTypeRegistry


class ParameterResolver:
    """
    Resolves structured parameters from normalized task text.

    The resolver extracts parameters required by downstream automation
    components without performing any actual execution.
    """

    # ------------------------------------------------------------------
    # URL Pattern
    # ------------------------------------------------------------------

    _URL_PATTERN = re.compile(
        r"https?://[^\s]+",
        re.IGNORECASE,
    )

    # ------------------------------------------------------------------
    # Search Query Prefixes
    # ------------------------------------------------------------------

    _SEARCH_PREFIXES = (
        "search for ",
        "search ",
        "find ",
        "lookup ",
        "google ",
    )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve(
        self,
        context: ProcessingContext,
    ) -> ProcessingContext:
        """
        Resolve parameters for every interpreted task.

        Parameters
        ----------
        context : ProcessingContext
            Current Agent Brain processing context.

        Returns
        -------
        ProcessingContext
            Updated processing context containing resolved parameters.
        """

        context.current_stage = ProcessingStage.PARAMETER_RESOLUTION

        context.log("Parameter resolution started.")

        for task in context.interpreted_tasks:

            task.parameters = self._extract_parameters(
                task.normalized_text
            )

            context.log(
                f"Parameters resolved for Task {task.task_id}: "
                f"{task.parameters}"
            )

        context.log(
            f"Parameter resolution completed for "
            f"{len(context.interpreted_tasks)} task(s)."
        )

        return context

    # ------------------------------------------------------------------
    # Parameter Extraction
    # ------------------------------------------------------------------

    def _extract_parameters(
        self,
        text: str,
    ) -> dict:
        """
        Extract all supported parameters from normalized task text.

        Parameters
        ----------
        text : str
            Normalized task text.

        Returns
        -------
        dict
            Structured task parameters.
        """

        text = text.strip()

        parameters = {}

        # --------------------------------------------------------------
        # URL
        # --------------------------------------------------------------

        url = self._extract_url(text)

        if url:
            parameters["url"] = url

            # A URL is also a website target.
            website = self._website_from_url(url)

            if website:
                parameters["website"] = website

        # --------------------------------------------------------------
        # Browser
        # --------------------------------------------------------------

        browser = self._extract_browser(text)

        if browser:
            parameters["browser"] = browser

        # --------------------------------------------------------------
        # Application
        # --------------------------------------------------------------

        application = self._extract_application(text)

        if application:
            parameters["application"] = application

        # --------------------------------------------------------------
        # Website Registry
        # --------------------------------------------------------------

        website = self._extract_website(text)

        if website:
            parameters["website"] = website

        # --------------------------------------------------------------
        # Search Query
        # --------------------------------------------------------------

        query = self._extract_search_query(text)

        if query:
            parameters["query"] = query

        # --------------------------------------------------------------
        # File Type
        # --------------------------------------------------------------

        filetype = self._extract_filetype(text)

        if filetype:
            parameters["filetype"] = filetype

        # --------------------------------------------------------------
        # Keyboard Parameters
        # --------------------------------------------------------------

        text_value = self._extract_text_parameter(text)

        if text_value is not None:
            parameters["text"] = text_value

        key = self._extract_key_parameter(text)

        if key is not None:
            parameters["key"] = key

        hotkey = self._extract_hotkey_parameter(text)

        if hotkey is not None:
            parameters["hotkey"] = hotkey

        # --------------------------------------------------------------
        # Mouse Parameters
        # --------------------------------------------------------------

        coordinates = self._extract_mouse_coordinates(text)

        if coordinates is not None:
            parameters["x"] = coordinates["x"]
            parameters["y"] = coordinates["y"]

        mouse_button = self._extract_mouse_button(text)

        if mouse_button is not None:
            parameters["button"] = mouse_button

        scroll_values = self._extract_scroll_parameters(text)

        if scroll_values is not None:
            parameters.update(scroll_values)

        return parameters
    # ------------------------------------------------------------------
    # URL Extraction
    # ------------------------------------------------------------------

    def _extract_url(
        self,
        text: str,
    ) -> str | None:
        """
        Extract the first HTTP/HTTPS URL from the task text.

        Examples
        --------
        "open https://example.com"
            -> "https://example.com"

        "visit https://github.com/project"
            -> "https://github.com/project"
        """

        match = self._URL_PATTERN.search(text)

        if not match:
            return None

        url = match.group(0)

        # Remove common trailing punctuation.
        return url.rstrip(".,!?;:)")

    # ------------------------------------------------------------------
    # Website From URL
    # ------------------------------------------------------------------

    def _website_from_url(
        self,
        url: str,
    ) -> str | None:
        """
        Extract the hostname from a URL.

        Example
        -------
        https://example.com/docs
            -> example.com
        """

        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)

            hostname = parsed.hostname

            if not hostname:
                return None

            return hostname.lower()

        except Exception:
            return None

    # ------------------------------------------------------------------
    # Browser
    # ------------------------------------------------------------------

    def _extract_browser(
        self,
        text: str,
    ) -> str | None:
        """
        Extract a supported browser from the task text.
        """

        normalized_text = text.lower()

        for browser in BrowserRegistry.all_browsers():

            if browser.lower() in normalized_text:

                return BrowserRegistry.normalize(browser)

        return None

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------

    def _extract_application(
        self,
        text: str,
    ) -> str | None:
        """
        Extract a supported application from the task text.
        """

        normalized_text = text.lower()

        for application in ApplicationRegistry.all_applications():

            if application.lower() in normalized_text:

                return ApplicationRegistry.normalize(
                    application
                )

        return None

    # ------------------------------------------------------------------
    # Website
    # ------------------------------------------------------------------

    def _extract_website(
        self,
        text: str,
    ) -> str | None:
        """
        Extract a known website from the Website Registry.
        """

        normalized_text = text.lower()

        for website in WebsiteRegistry.all_websites():

            if website.lower() in normalized_text:

                return WebsiteRegistry.normalize(
                    website
                )

        return None

    # ------------------------------------------------------------------
    # Search Query
    # ------------------------------------------------------------------

    def _extract_search_query(
        self,
        text: str,
    ) -> str | None:
        """
        Extract the user's search query.

        Examples
        --------
        "search for python tutorials"
            -> "python tutorials"

        "find latest AI news"
            -> "latest AI news"

        "google machine learning"
            -> "machine learning"
        """

        normalized_text = text.strip()

        lowered_text = normalized_text.lower()

        for prefix in self._SEARCH_PREFIXES:

            if lowered_text.startswith(prefix):

                query = normalized_text[
                    len(prefix):
                ].strip()

                if query:
                    return query

        return None

    # ------------------------------------------------------------------
    # File Type
    # ------------------------------------------------------------------

    def _extract_filetype(
        self,
        text: str,
    ) -> str | None:
        """
        Extract a supported file type from the task text.
        """

        normalized_text = text.lower()

        for filetype in FileTypeRegistry.all_filetypes():

            if filetype.lower() in normalized_text:

                return FileTypeRegistry.normalize(
                    filetype
                )

        return None

    # ------------------------------------------------------------------
    # Keyboard - Text
    # ------------------------------------------------------------------

    def _extract_text_parameter(
        self,
        text: str,
    ) -> str | None:
        """
        Extract text that should be typed by the keyboard agent.

        Examples
        --------
        "type Hello World"
            -> "Hello World"

        "write Python is powerful"
            -> "Python is powerful"

        "enter text JARVIS"
            -> "JARVIS"
        """

        normalized_text = text.strip()

        prefixes = (
            "type ",
            "write ",
            "enter text ",
        )

        lowered_text = normalized_text.lower()

        for prefix in prefixes:

            if lowered_text.startswith(prefix):

                value = normalized_text[
                    len(prefix):
                ].strip()

                if value:
                    return value

        return None

    # ------------------------------------------------------------------
    # Keyboard - Key
    # ------------------------------------------------------------------

    def _extract_key_parameter(
        self,
        text: str,
    ) -> str | None:
        """
        Extract a keyboard key from a press-key command.

        Examples
        --------
        "press enter"
            -> "enter"

        "press escape"
            -> "escape"

        "hit tab"
            -> "tab"
        """

        normalized_text = text.strip()

        lowered_text = normalized_text.lower()

        prefixes = (
            "press ",
            "hit ",
        )

        for prefix in prefixes:

            if lowered_text.startswith(prefix):

                key = normalized_text[
                    len(prefix):
                ].strip()

                if key:
                    return key.lower()

        return None

    # ------------------------------------------------------------------
    # Keyboard - Hotkey
    # ------------------------------------------------------------------

    def _extract_hotkey_parameter(
        self,
        text: str,
    ) -> list[str] | None:
        """
        Extract keyboard shortcut components.

        Examples
        --------
        "hotkey ctrl c"
            -> ["ctrl", "c"]

        "shortcut ctrl shift s"
            -> ["ctrl", "shift", "s"]
        """

        normalized_text = text.strip()

        lowered_text = normalized_text.lower()

        prefixes = (
            "hotkey ",
            "shortcut ",
        )

        for prefix in prefixes:

            if lowered_text.startswith(prefix):

                value = normalized_text[
                    len(prefix):
                ].strip()

                if not value:
                    return None

                parts = re.split(
                    r"\s*(?:\+|,|\s)\s*",
                    value.lower(),
                )

                parts = [
                    part.strip()
                    for part in parts
                    if part.strip()
                ]

                return parts if parts else None

        return None

    # ------------------------------------------------------------------
    # Mouse - Coordinates
    # ------------------------------------------------------------------

    def _extract_mouse_coordinates(
        self,
        text: str,
    ) -> dict[str, int] | None:
        """
        Extract mouse coordinates from a task.

        Examples
        --------
        "move mouse to 500 300"
            -> {"x": 500, "y": 300}

        "move cursor to 100, 200"
            -> {"x": 100, "y": 200}
        """

        pattern = re.compile(
            r"(?:move mouse|move cursor)"
            r".*?"
            r"(-?\d+(?:\.\d+)?)"
            r"\s*(?:,|to)?\s*"
            r"(-?\d+(?:\.\d+)?)",
            re.IGNORECASE,
        )

        match = pattern.search(text)

        if not match:
            return None

        x = float(match.group(1))
        y = float(match.group(2))

        if x.is_integer():
            x = int(x)

        if y.is_integer():
            y = int(y)

        return {
            "x": x,
            "y": y,
        }

    # ------------------------------------------------------------------
    # Mouse - Button
    # ------------------------------------------------------------------

    def _extract_mouse_button(
        self,
        text: str,
    ) -> str | None:
        """
        Extract mouse button from the task.

        Examples
        --------
        "click"
            -> "left"

        "left click"
            -> "left"

        "right click"
            -> "right"

        "middle click"
            -> "middle"
        """

        normalized_text = text.lower().strip()

        if "right click" in normalized_text:
            return "right"

        if "middle click" in normalized_text:
            return "middle"

        if "left click" in normalized_text:
            return "left"

        if normalized_text == "click":
            return "left"

        return None

    # ------------------------------------------------------------------
    # Mouse - Scroll
    # ------------------------------------------------------------------

    def _extract_scroll_parameters(
        self,
        text: str,
    ) -> dict[str, int] | None:
        """
        Extract scroll direction and amount.

        Examples
        --------
        "scroll down"
            -> {"dx": 0, "dy": -1}

        "scroll up"
            -> {"dx": 0, "dy": 1}

        "scroll down 5"
            -> {"dx": 0, "dy": -5}
        """

        normalized_text = text.lower().strip()

        if "scroll" not in normalized_text:
            return None

        amount_match = re.search(
            r"(-?\d+)",
            normalized_text,
        )

        amount = 1

        if amount_match:
            amount = abs(
                int(amount_match.group(1))
            )

        if "down" in normalized_text:
            return {
                "dx": 0,
                "dy": -amount,
            }

        if "up" in normalized_text:
            return {
                "dx": 0,
                "dy": amount,
            }

        return {
            "dx": 0,
            "dy": 0,
        }