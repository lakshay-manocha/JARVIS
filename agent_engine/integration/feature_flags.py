"""
===============================================================================
File Name   : feature_flags.py
Module      : Integration
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
Defines Phase 3 feature flags for controlling Model A, Model B, and the
Consistency Guard independently.

All flags default to safe values (fail-safe principle) so that disabling
any flag preserves original baseline JARVIS behavior.
===============================================================================
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


def _env_bool(var_name: str, default: bool) -> bool:
    val = os.getenv(var_name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


@dataclass
class IntegrationFeatureFlags:
    """
    Feature flag configuration for Model A, Model B, and Consistency Guard.
    """

    # Model A controls
    model_a_enabled: bool = field(
        default_factory=lambda: _env_bool("JARVIS_MODEL_A_ENABLED", False)
    )
    model_a_logging_mode: bool = field(
        default_factory=lambda: _env_bool("JARVIS_MODEL_A_LOGGING_MODE", True)
    )
    model_a_advisory_mode: bool = field(
        default_factory=lambda: _env_bool("JARVIS_MODEL_A_ADVISORY_MODE", False)
    )

    # Model B controls
    model_b_enabled: bool = field(
        default_factory=lambda: _env_bool("JARVIS_MODEL_B_ENABLED", False)
    )
    model_b_logging_mode: bool = field(
        default_factory=lambda: _env_bool("JARVIS_MODEL_B_LOGGING_MODE", True)
    )

    # Consistency Guard & Operational Modes
    consistency_guard_enabled: bool = field(
        default_factory=lambda: _env_bool("JARVIS_CONSISTENCY_GUARD_ENABLED", False)
    )
    warning_mode_enabled: bool = field(
        default_factory=lambda: _env_bool("JARVIS_WARNING_MODE_ENABLED", False)
    )
    controlled_blocking_enabled: bool = field(
        default_factory=lambda: _env_bool("JARVIS_CONTROLLED_BLOCKING_ENABLED", False)
    )

    def is_model_a_active(self) -> bool:
        """Returns True if Model A is enabled and in either logging or advisory mode."""
        return self.model_a_enabled and (
            self.model_a_logging_mode or self.model_a_advisory_mode
        )

    def is_model_b_active(self) -> bool:
        """Returns True if Model B is enabled."""
        return self.model_b_enabled

    def is_guard_active(self) -> bool:
        """Returns True if Consistency Guard is enabled."""
        return self.consistency_guard_enabled


# Default global flags instance
_GLOBAL_FLAGS = IntegrationFeatureFlags()


def get_feature_flags() -> IntegrationFeatureFlags:
    """Return the active global feature flags."""
    global _GLOBAL_FLAGS
    return _GLOBAL_FLAGS


def set_feature_flags(flags: IntegrationFeatureFlags) -> None:
    """Set the active global feature flags."""
    global _GLOBAL_FLAGS
    _GLOBAL_FLAGS = flags


def reset_feature_flags() -> IntegrationFeatureFlags:
    """Reset feature flags to defaults based on environment variables."""
    global _GLOBAL_FLAGS
    _GLOBAL_FLAGS = IntegrationFeatureFlags()
    return _GLOBAL_FLAGS
