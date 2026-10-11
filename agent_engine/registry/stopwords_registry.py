"""
===============================================================================
File Name   : stopwords_registry.py
Module      : Registry
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Maintains automation-specific stopwords used during task normalization.

Unlike traditional NLP stopwords, this registry only removes words that do not
contribute to automation intent.

Author : Team JARVIS
===============================================================================
"""


class StopwordsRegistry:
    """
    Registry responsible for automation-specific stopwords.
    """

    CATEGORY = "STOPWORDS"

    _STOPWORDS = {

        # ------------------------------------------------------------------
        # Politeness
        # ------------------------------------------------------------------

        "please",
        "kindly",

        # ------------------------------------------------------------------
        # Fillers
        # ------------------------------------------------------------------

        "just",
        "simply",
        "only",

        # ------------------------------------------------------------------
        # Generic Articles
        # ------------------------------------------------------------------

        "a",
        "an",
        "the",

        # ------------------------------------------------------------------
        # Common Descriptive Words
        # ------------------------------------------------------------------

        "latest",
        "available",
        "current",
        "new",

        # ------------------------------------------------------------------
        # Request Words
        # ------------------------------------------------------------------

        "can",
        "could",
        "would",

        "me",

        "my"
    }

    @classmethod
    def contains(cls, word: str) -> bool:
        """
        Checks whether the word is a stopword.
        """

        return word.lower().strip() in cls._STOPWORDS

    @classmethod
    def remove(cls, words: list[str]) -> list[str]:
        """
        Removes stopwords from a list of words.
        """

        return [
            word
            for word in words
            if word.lower().strip() not in cls._STOPWORDS
        ]

    @classmethod
    def all_stopwords(cls) -> set[str]:
        """
        Returns all registered stopwords.
        """

        return cls._STOPWORDS.copy()