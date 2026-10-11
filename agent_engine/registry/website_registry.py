"""
===============================================================================
File Name   : website_registry.py
Module      : Registry
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Maintains the canonical website registry used throughout the Agent Brain.

This registry normalizes website aliases into a single canonical website name
and provides metadata required for browser automation.

Author : Team JARVIS
===============================================================================
"""

from typing import Dict, Optional


class WebsiteRegistry:
    """
    Registry responsible for website normalization.
    """

    CATEGORY = "WEBSITE"

    _WEBSITE_MAP: Dict[str, Dict[str, object]] = {

        # ------------------------------------------------------------------
        # Google
        # ------------------------------------------------------------------

        "google": {
            "canonical": "google",
            "display_name": "Google",
            "url": "https://www.google.com",
            "requires_login": False
        },

        # ------------------------------------------------------------------
        # YouTube
        # ------------------------------------------------------------------

        "youtube": {
            "canonical": "youtube",
            "display_name": "YouTube",
            "url": "https://www.youtube.com",
            "requires_login": False
        },

        # ------------------------------------------------------------------
        # GitHub
        # ------------------------------------------------------------------

        "github": {
            "canonical": "github",
            "display_name": "GitHub",
            "url": "https://github.com",
            "requires_login": True
        },

        # ------------------------------------------------------------------
        # ChatGPT
        # ------------------------------------------------------------------

        "chatgpt": {
            "canonical": "chatgpt",
            "display_name": "ChatGPT",
            "url": "https://chat.openai.com",
            "requires_login": True
        },

        "openai chat": {
            "canonical": "chatgpt",
            "display_name": "ChatGPT",
            "url": "https://chat.openai.com",
            "requires_login": True
        },

        # ------------------------------------------------------------------
        # Gmail
        # ------------------------------------------------------------------

        "gmail": {
            "canonical": "gmail",
            "display_name": "Gmail",
            "url": "https://mail.google.com",
            "requires_login": True
        },

        # ------------------------------------------------------------------
        # LinkedIn
        # ------------------------------------------------------------------

        "linkedin": {
            "canonical": "linkedin",
            "display_name": "LinkedIn",
            "url": "https://www.linkedin.com",
            "requires_login": True
        },

        # ------------------------------------------------------------------
        # Stack Overflow
        # ------------------------------------------------------------------

        "stackoverflow": {
            "canonical": "stackoverflow",
            "display_name": "Stack Overflow",
            "url": "https://stackoverflow.com",
            "requires_login": False
        },

        "stack overflow": {
            "canonical": "stackoverflow",
            "display_name": "Stack Overflow",
            "url": "https://stackoverflow.com",
            "requires_login": False
        }
    }

    @classmethod
    def normalize(cls, website_name: str) -> str:
        """
        Returns the canonical website name.
        """

        website_name = website_name.lower().strip()

        if website_name in cls._WEBSITE_MAP:
            return cls._WEBSITE_MAP[website_name]["canonical"]

        return website_name

    @classmethod
    def contains(cls, website_name: str) -> bool:
        """
        Checks whether a website exists in the registry.
        """

        return website_name.lower().strip() in cls._WEBSITE_MAP

    @classmethod
    def get_metadata(cls, website_name: str) -> Optional[Dict[str, object]]:
        """
        Returns metadata associated with a website.
        """

        return cls._WEBSITE_MAP.get(website_name.lower().strip())

    @classmethod
    def get_url(cls, website_name: str) -> Optional[str]:
        """
        Returns the default URL of the website.
        """

        metadata = cls.get_metadata(website_name)

        if metadata:
            return metadata["url"]

        return None

    @classmethod
    def all_websites(cls) -> Dict[str, Dict[str, object]]:
        """
        Returns the complete website registry.
        """

        return cls._WEBSITE_MAP.copy()