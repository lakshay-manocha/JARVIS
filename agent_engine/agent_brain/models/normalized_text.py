"""
===============================================================================
File Name   : normalized_text.py
Module      : Agent Brain Models
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Defines the normalized text model produced by the Text Normalizer.

This model acts as the standardized output passed to the Interpreter,
Intent Detector, and other downstream Agent Brain components.

Author : Team JARVIS
===============================================================================
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class NormalizedText:
    """
    Represents the output of the text normalization pipeline.
    """

    # ----------------------------------------------------------------------
    # Raw Input
    # ----------------------------------------------------------------------

    original_text: str

    # ----------------------------------------------------------------------
    # Final Normalized Text
    # ----------------------------------------------------------------------

    normalized_text: str

    # ----------------------------------------------------------------------
    # Token Information
    # ----------------------------------------------------------------------

    original_tokens: List[str] = field(default_factory=list)

    normalized_tokens: List[str] = field(default_factory=list)

    # ----------------------------------------------------------------------
    # Tracking Information
    # ----------------------------------------------------------------------

    removed_tokens: List[str] = field(default_factory=list)

    replacements: Dict[str, str] = field(default_factory=dict)

    processing_steps: List[str] = field(default_factory=list)

    # ----------------------------------------------------------------------
    # Metadata
    # ----------------------------------------------------------------------

    metadata: Dict[str, str] = field(default_factory=dict)

    # ----------------------------------------------------------------------
    # Processing Information
    # ----------------------------------------------------------------------

    processing_steps: List[str] = field(default_factory=list)

    def token_count(self) -> int:
        """
        Returns the number of normalized tokens.
        """
        return len(self.normalized_tokens)

    def has_changes(self) -> bool:
        """
        Returns True if normalization modified the input.
        """
        return self.original_text != self.normalized_text

    def was_removed(self, token: str) -> bool:
        """
        Checks whether a token was removed during normalization.
        """
        return token in self.removed_tokens

    def was_replaced(self, token: str) -> bool:
        """
        Checks whether a token was replaced.
        """
        return token in self.replacements

    def to_dict(self) -> Dict:
        """
        Serializes the model into a dictionary.
        """
        return {
            "original_text": self.original_text,
            "normalized_text": self.normalized_text,
            "original_tokens": self.original_tokens,
            "normalized_tokens": self.normalized_tokens,
            "removed_tokens": self.removed_tokens,
            "replacements": self.replacements,
            "processing_steps": self.processing_steps,
            "metadata": self.metadata,
        }