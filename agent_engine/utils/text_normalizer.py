"""
===============================================================================
File Name   : text_normalizer.py
Module      : Utilities
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Provides the centralized text normalization pipeline for the Agent Brain.

The TextNormalizer standardizes raw natural language tasks into a structured
NormalizedText object that is consumed by downstream reasoning modules.

Responsibilities:
    • Normalize letter case
    • Remove extra whitespaces
    • Tokenize text
    • Apply synonym normalization
    • Apply registry-based normalization
    • Remove automation stopwords
    • Build NormalizedText object

Author : Team Agent
===============================================================================
"""

import re
from typing import Dict, List

from agent_engine.agent_brain.models.normalized_text import NormalizedText
from agent_engine.utils.registry_manager import RegistryManager

class TextNormalizer:
    """
    Performs normalization of task descriptions.
    """

    def normalize(self, text: str) -> NormalizedText:
        """
        Normalize a raw task description.

        Parameters
        ----------
        text : str

        Returns
        -------
        NormalizedText
        """

        original_text = text

        processing_steps = []

        # ----------------------------------------------------------
        # Lowercase
        # ----------------------------------------------------------

        text = self._normalize_case(text)
        processing_steps.append("lowercase")

        # ----------------------------------------------------------
        # Remove extra whitespace
        # ----------------------------------------------------------

        text = self._normalize_whitespace(text)
        processing_steps.append("whitespace_normalization")

        # ----------------------------------------------------------
        # Tokenization
        # ----------------------------------------------------------

        original_tokens = self._tokenize(text)
        tokens = original_tokens.copy()

        processing_steps.append("tokenization")

        replacements: Dict[str, str] = {}

        # ----------------------------------------------------------
        # Synonyms
        # ----------------------------------------------------------

        tokens = self._apply_registry(
            tokens,
            RegistryManager.synonyms,
            replacements
        )

        processing_steps.append("synonym_normalization")

        # ----------------------------------------------------------
        # Actions
        # ----------------------------------------------------------

        tokens = self._apply_registry(
            tokens,
            RegistryManager.actions,
            replacements
        )

        processing_steps.append("action_normalization")

        # ----------------------------------------------------------
        # Browsers
        # ----------------------------------------------------------

        tokens = self._apply_registry(
            tokens,
            RegistryManager.browsers,
            replacements
        )

        processing_steps.append("browser_normalization")

        # ----------------------------------------------------------
        # Applications
        # ----------------------------------------------------------

        tokens = self._apply_registry(
            tokens,
            RegistryManager.applications,
            replacements
        )

        processing_steps.append("application_normalization")

        # ----------------------------------------------------------
        # Websites
        # ----------------------------------------------------------

        tokens = self._apply_registry(
            tokens,
            RegistryManager.websites,
            replacements
        )

        processing_steps.append("website_normalization")

        # ----------------------------------------------------------
        # File Types
        # ----------------------------------------------------------

        tokens = self._apply_registry(
            tokens,
            RegistryManager.filetypes,
            replacements
        )

        processing_steps.append("filetype_normalization")

        # ----------------------------------------------------------
        # Stopword Removal
        # ----------------------------------------------------------

        removed_tokens = [
            token
            for token in tokens
            if RegistryManager.stopwords.contains(token)
        ]

        tokens = RegistryManager.stopwords.remove(tokens)

        processing_steps.append("stopword_removal")

        normalized_text = " ".join(tokens)

        return NormalizedText(
            original_text=original_text,
            normalized_text=normalized_text,
            original_tokens=original_tokens,
            normalized_tokens=tokens,
            removed_tokens=removed_tokens,
            replacements=replacements,
            metadata={
                "normalizer": "v1.0"
            },
            processing_steps=processing_steps
        )

    # ==============================================================
    # Private Helper Methods
    # ==============================================================

    def _normalize_case(self, text: str) -> str:
        """Convert text to lowercase."""
        return text.lower()

    def _normalize_whitespace(self, text: str) -> str:
        """Collapse multiple whitespaces."""
        return re.sub(r"\s+", " ", text).strip()

    def _tokenize(self, text: str) -> List[str]:
        """Split text into tokens."""
        return text.split()

    def _apply_registry(
        self,
        tokens: List[str],
        registry,
        replacements: Dict[str, str]
    ) -> List[str]:
        """
        Apply registry normalization.
        """

        normalized_tokens = []

        for token in tokens:

            normalized = registry.normalize(token)

            if normalized != token:
                replacements[token] = normalized

            normalized_tokens.append(normalized)

        return normalized_tokens