"""
===============================================================================
File Name   : consistency_guard.py
Module      : Integration / Guard
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
Implements Phase 12 (Consistency Guard), Phase 13 (Logging-Only Mode),
Phase 14 (Warning Mode), and Phase 15 (Controlled Blocking / Replanning).

Combines:
- Model A contextual & continuation info
- Model B mismatch prediction & confidence
- Deterministic state differences
- Policy safety thresholds

Outputs a structured GuardEvaluationResult.

Critical Rule:
The Guard is a policy layer. It does not replace the Decision Manager.
All blocking and replanning recommendations are routed through JARVIS decision
mechanisms.
===============================================================================
"""

from __future__ import annotations

from enum import Enum
import logging
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agent_engine.integration.feature_flags import (
    IntegrationFeatureFlags,
    get_feature_flags,
)
from agent_engine.state_mismatch.state_mismatch_contract import (
    ChangedResource,
    ResourceChange,
    StateMismatchResult,
    StateSnapshot,
)

logger = logging.getLogger("jarvis.integration.consistency_guard")


class GuardStatus(str, Enum):
    """Safety status evaluated by the Consistency Guard."""

    CONSISTENT = "CONSISTENT"
    WARNING = "WARNING"
    MISMATCH = "MISMATCH"
    REPLAN_REQUIRED = "REPLAN_REQUIRED"


class GuardAction(str, Enum):
    """Recommended action proposed to JARVIS Decision Manager."""

    PROCEED = "PROCEED"
    WARN = "WARN"
    RECOVER = "RECOVER"
    REPLAN = "REPLAN"
    BLOCK = "BLOCK"


class GuardEvaluationResult(BaseModel):
    """
    Public output contract of the Consistency Guard.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    status: GuardStatus
    recommended_action: GuardAction
    can_proceed: bool
    mismatch_detected: bool
    ml_probability: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    threshold: float = Field(ge=0.0, le=1.0)
    changed_resources: list[ChangedResource] = Field(default_factory=list)
    reason: str = Field(default="")
    target_workflow_id: str | None = None
    target_node_ids: list[Any] = Field(default_factory=list)
    recovery_hints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConsistencyGuard:
    """
    Combines Model A contextual continuation information with Model B
    runtime-state evidence to ensure safe workflow execution.
    """

    def __init__(
        self,
        feature_flags: IntegrationFeatureFlags | None = None,
        replan_probability_threshold: float = 0.85,
    ) -> None:
        self._feature_flags = feature_flags
        self.replan_probability_threshold = replan_probability_threshold

    def _get_flags(self) -> IntegrationFeatureFlags:
        return self._feature_flags or get_feature_flags()

    def evaluate(
        self,
        mismatch_result: StateMismatchResult,
        stored_state: StateSnapshot | None = None,
        current_state: StateSnapshot | None = None,
        target_workflow_id: str | None = None,
        continuation_node_ids: list[Any] | None = None,
    ) -> GuardEvaluationResult:
        """
        Evaluate workflow continuation safety.

        Supports:
        - Phase 13: Logging-Only Guard (does not block)
        - Phase 14: Warning Mode (issues warning, allows continuation)
        - Phase 15: Controlled Blocking / Replanning (recommends RECOVER/REPLAN/BLOCK)
        """
        flags = self._get_flags()
        prob = mismatch_result.probability
        conf = mismatch_result.confidence
        thresh = mismatch_result.threshold
        diffs = mismatch_result.changed_resources
        is_mismatch = mismatch_result.mismatch

        hints = self._generate_recovery_hints(diffs)

        # ---------------------------------------------------------------------
        # Case 1: Consistency Guard is Disabled (Baseline JARVIS Pass-through)
        # ---------------------------------------------------------------------
        if not flags.consistency_guard_enabled:
            logger.debug("Consistency Guard disabled by feature flag.")
            return GuardEvaluationResult(
                status=GuardStatus.CONSISTENT,
                recommended_action=GuardAction.PROCEED,
                can_proceed=True,
                mismatch_detected=is_mismatch,
                ml_probability=prob,
                confidence=conf,
                threshold=thresh,
                changed_resources=diffs,
                reason="Consistency Guard disabled by feature flags.",
                target_workflow_id=target_workflow_id,
                target_node_ids=continuation_node_ids or [],
                recovery_hints=[],
                metadata={"mode": "DISABLED"},
            )

        # ---------------------------------------------------------------------
        # Case 2: Consistent State (No mismatch detected)
        # ---------------------------------------------------------------------
        if not is_mismatch and len(diffs) == 0:
            logger.info("[GUARD_CONSISTENT] Runtime state is compatible with stored checkpoint.")
            return GuardEvaluationResult(
                status=GuardStatus.CONSISTENT,
                recommended_action=GuardAction.PROCEED,
                can_proceed=True,
                mismatch_detected=False,
                ml_probability=prob,
                confidence=conf,
                threshold=thresh,
                changed_resources=[],
                reason="Stored state and current state are consistent.",
                target_workflow_id=target_workflow_id,
                target_node_ids=continuation_node_ids or [],
                recovery_hints=[],
                metadata={"mode": "ACTIVE"},
            )

        # ---------------------------------------------------------------------
        # Case 3: Mismatch Detected - Phase 13 Logging-Only Mode
        # ---------------------------------------------------------------------
        # If neither Warning Mode nor Controlled Blocking is active, run logging-only
        if not flags.warning_mode_enabled and not flags.controlled_blocking_enabled:
            reason = (
                f"Logging-Only: Mismatch detected (prob={prob:.4f}, diffs={len(diffs)}). "
                f"Execution continues without disruption."
            )
            logger.info("[GUARD_LOGGING_ONLY] %s", reason)
            return GuardEvaluationResult(
                status=GuardStatus.CONSISTENT,
                recommended_action=GuardAction.PROCEED,
                can_proceed=True,
                mismatch_detected=True,
                ml_probability=prob,
                confidence=conf,
                threshold=thresh,
                changed_resources=diffs,
                reason=reason,
                target_workflow_id=target_workflow_id,
                target_node_ids=continuation_node_ids or [],
                recovery_hints=hints,
                metadata={"mode": "LOGGING_ONLY"},
            )

        # ---------------------------------------------------------------------
        # Case 4: Mismatch Detected - Phase 14 Warning Mode
        # ---------------------------------------------------------------------
        if flags.warning_mode_enabled and not flags.controlled_blocking_enabled:
            reason = (
                f"Warning: Runtime environment discrepancy observed (prob={prob:.4f}, "
                f"changed_resources={len(diffs)}). Execution allowed to proceed."
            )
            logger.warning("[GUARD_WARNING_MODE] %s", reason)
            return GuardEvaluationResult(
                status=GuardStatus.WARNING,
                recommended_action=GuardAction.WARN,
                can_proceed=True,
                mismatch_detected=True,
                ml_probability=prob,
                confidence=conf,
                threshold=thresh,
                changed_resources=diffs,
                reason=reason,
                target_workflow_id=target_workflow_id,
                target_node_ids=continuation_node_ids or [],
                recovery_hints=hints,
                metadata={"mode": "WARNING_MODE"},
            )

        # ---------------------------------------------------------------------
        # Case 5: Mismatch Detected - Phase 15 Controlled Blocking / Replanning
        # ---------------------------------------------------------------------
        # Check if severity requires complete replan or targeted recovery
        if prob >= self.replan_probability_threshold:
            reason = (
                f"Severe state discrepancy (prob={prob:.4f} >= {self.replan_probability_threshold}). "
                f"Workflow cannot safely resume; full replan recommended."
            )
            logger.warning("[GUARD_REPLAN_REQUIRED] %s", reason)
            return GuardEvaluationResult(
                status=GuardStatus.REPLAN_REQUIRED,
                recommended_action=GuardAction.REPLAN,
                can_proceed=False,
                mismatch_detected=True,
                ml_probability=prob,
                confidence=conf,
                threshold=thresh,
                changed_resources=diffs,
                reason=reason,
                target_workflow_id=target_workflow_id,
                target_node_ids=continuation_node_ids or [],
                recovery_hints=hints,
                metadata={"mode": "CONTROLLED_BLOCKING"},
            )

        # Moderate mismatch: recommend targeted recovery before continuing
        reason = (
            f"State mismatch detected (prob={prob:.4f} >= {thresh}). "
            f"Recovery recommended for missing resources."
        )
        logger.warning("[GUARD_MISMATCH_RECOVERY] %s", reason)
        return GuardEvaluationResult(
            status=GuardStatus.MISMATCH,
            recommended_action=GuardAction.RECOVER,
            can_proceed=False,
            mismatch_detected=True,
            ml_probability=prob,
            confidence=conf,
            threshold=thresh,
            changed_resources=diffs,
            reason=reason,
            target_workflow_id=target_workflow_id,
            target_node_ids=continuation_node_ids or [],
            recovery_hints=hints,
            metadata={"mode": "CONTROLLED_BLOCKING"},
        )

    def _generate_recovery_hints(
        self,
        changed_resources: list[ChangedResource],
    ) -> list[str]:
        """Generate human-readable recovery hints for missing resources."""
        hints = []
        for item in changed_resources:
            if item.change == ResourceChange.MISSING:
                hints.append(f"Restore missing {item.type.value.lower()}: '{item.identifier}'")
            elif item.change == ResourceChange.ADDED:
                hints.append(f"Unexpected {item.type.value.lower()} running: '{item.identifier}'")
        return hints
