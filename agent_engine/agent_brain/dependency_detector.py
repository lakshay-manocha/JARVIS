"""
===============================================================================
File Name   : dependency_detector.py
Module      : Agent Brain
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Provides rule-based dependency detection between interpreted tasks.

B1.4 introduces structured confidence and reasoning metadata so that every
dependency decision can be traced to the rule that produced it.

This rule-based implementation acts as the baseline for the future
research-oriented dependency prediction model.

Author : Team JARVIS
===============================================================================
"""

from __future__ import annotations

import re

from agent_engine.agent_brain.models.dependency_result import DependencyResult
from agent_engine.agent_brain.models.interpreted_task import InterpretedTask
from agent_engine.contracts.dependency_types import DependencyType


class DependencyDetector:
    """
    Detects dependencies between two interpreted tasks using deterministic
    rule-based logic.
    """

    # ------------------------------------------------------------------
    # Dependency patterns
    # ------------------------------------------------------------------

    DATA_DEPENDENCY_PATTERNS = [
        r"\bthe found\b",
        r"\bthe downloaded\b",
        r"\bthe generated\b",
        r"\bthe created\b",
        r"\bthe selected\b",
        r"\bthe identified\b",
        r"\bthe result\b",
        r"\bthe output\b",
        r"\bprevious\b",
        r"\babove\b",
        r"\bmentioned\b",
    ]

    STATE_DEPENDENCY_PATTERNS = [
        r"\bafter\b",
        r"\bonce\b",
        r"\bwhen\b",
        r"\buntil\b",
        r"\bcompleted\b",
        r"\bfinished\b",
        r"\bavailable\b",
        r"\bread\b",
        r"\breview\b",
    ]

    # ------------------------------------------------------------------
    # Confidence levels
    # ------------------------------------------------------------------

    CONFIDENCE_DATA = 0.90
    CONFIDENCE_STATE = 0.85
    CONFIDENCE_RESOURCE = 0.75
    CONFIDENCE_CONTEXT = 0.65
    CONFIDENCE_NONE = 0.80
    CONFIDENCE_SELF = 1.00

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(
        self,
        parent_task: InterpretedTask,
        child_task: InterpretedTask,
    ) -> DependencyResult:
        """
        Detect whether child_task depends on parent_task.

        Returns a structured DependencyResult containing:

            • dependency decision
            • confidence
            • dependency type
            • reason
            • rule identifier
            • supporting evidence
        """

        parent_text = self._prepare_text(
            parent_task.normalized_text
        )

        child_text = self._prepare_text(
            child_task.normalized_text
        )

        # --------------------------------------------------------------
        # Safety rule: self dependency
        # --------------------------------------------------------------

        if parent_task.task_id == child_task.task_id:

            return self._build_result(
                parent_task=parent_task,
                child_task=child_task,
                depends_on=False,
                confidence=self.CONFIDENCE_SELF,
                dependency_type=DependencyType.NONE,
                reason="A task cannot depend on itself.",
                rule="self_dependency",
            )

        # --------------------------------------------------------------
        # Rule 1: Data dependency
        # --------------------------------------------------------------

        matched_data_pattern = self._find_matching_pattern(
            child_text,
            self.DATA_DEPENDENCY_PATTERNS,
        )

        if matched_data_pattern:

            return self._build_result(
                parent_task=parent_task,
                child_task=child_task,
                depends_on=True,
                confidence=self.CONFIDENCE_DATA,
                dependency_type=DependencyType.DATA,
                reason=(
                    "The child task contains a reference to an "
                    "artifact, result, or output that may have been "
                    "produced by the parent task."
                ),
                rule="data_reference",
                evidence=matched_data_pattern,
            )

        # --------------------------------------------------------------
        # Rule 2: State dependency
        # --------------------------------------------------------------

        matched_state_pattern = self._find_matching_pattern(
            child_text,
            self.STATE_DEPENDENCY_PATTERNS,
        )

        if matched_state_pattern:

            return self._build_result(
                parent_task=parent_task,
                child_task=child_task,
                depends_on=True,
                confidence=self.CONFIDENCE_STATE,
                dependency_type=DependencyType.STATE,
                reason=(
                    "The child task contains language indicating "
                    "that a previous state or completed action is "
                    "required."
                ),
                rule="state_requirement",
                evidence=matched_state_pattern,
            )
        # --------------------------------------------------------------
        # Rule 4: Shared meaningful object
        # --------------------------------------------------------------

        shared_terms = self._find_shared_terms(
            parent_text,
            child_text,
        )

        if shared_terms:

            return self._build_result(
                parent_task=parent_task,
                child_task=child_task,
                depends_on=True,
                confidence=self.CONFIDENCE_CONTEXT,
                dependency_type=DependencyType.CONTEXT,
                reason=(
                    "The tasks share meaningful entities or objects, "
                    "suggesting a possible contextual dependency."
                ),
                rule="shared_context",
                evidence=", ".join(shared_terms),
                metadata={
                    "shared_terms": ", ".join(shared_terms)
                },
            )

        # --------------------------------------------------------------
        # Rule 3: Resource dependency
        # --------------------------------------------------------------

        if self._detect_resource_dependency(
            parent_text,
            child_text,
        ):

            return self._build_result(
                parent_task=parent_task,
                child_task=child_task,
                depends_on=True,
                confidence=self.CONFIDENCE_RESOURCE,
                dependency_type=DependencyType.RESOURCE,
                reason=(
                    "The child task appears to require a resource "
                    "prepared, located, or made available by the "
                    "parent task."
                ),
                rule="resource_provision",
            )

        
        # --------------------------------------------------------------
        # Rule 5: No dependency
        # --------------------------------------------------------------

        return self._build_result(
            parent_task=parent_task,
            child_task=child_task,
            depends_on=False,
            confidence=self.CONFIDENCE_NONE,
            dependency_type=DependencyType.NONE,
            reason=(
                "No dependency relationship was detected by the "
                "current rule set."
            ),
            rule="no_dependency",
        )

    # ------------------------------------------------------------------
    # Result construction
    # ------------------------------------------------------------------

    def _build_result(
        self,
        parent_task: InterpretedTask,
        child_task: InterpretedTask,
        depends_on: bool,
        confidence: float,
        dependency_type: DependencyType,
        reason: str,
        rule: str,
        evidence: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> DependencyResult:
        """
        Creates a standardized DependencyResult.

        Centralizing result construction ensures that all rules produce
        the same structured metadata.
        """

        result_metadata = {
            "rule": rule,
        }

        if evidence:
            result_metadata["evidence"] = evidence

        if metadata:
            result_metadata.update(metadata)

        return DependencyResult(
            parent_task_id=parent_task.task_id,
            child_task_id=child_task.task_id,
            depends_on=depends_on,
            confidence=confidence,
            reason=reason,
            dependency_type=dependency_type,
            metadata=result_metadata,
        )

    # ------------------------------------------------------------------
    # Text preparation
    # ------------------------------------------------------------------

    def _prepare_text(
        self,
        text: str,
    ) -> str:
        """
        Normalize text used internally by dependency rules.
        """

        text = text.lower().strip()

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text

    # ------------------------------------------------------------------
    # Pattern matching
    # ------------------------------------------------------------------

    def _matches_any(
        self,
        text: str,
        patterns: list[str],
    ) -> bool:
        """
        Returns True if any supplied regex pattern matches the text.
        """

        return any(
            re.search(pattern, text)
            for pattern in patterns
        )

    def _find_matching_pattern(
        self,
        text: str,
        patterns: list[str],
    ) -> str | None:
        """
        Returns the first dependency pattern that matches the text.
        """

        for pattern in patterns:
            if re.search(pattern, text):
                return pattern

        return None

    # ------------------------------------------------------------------
    # Resource dependency
    # ------------------------------------------------------------------

    def _detect_resource_dependency(
        self,
        parent_text: str,
        child_text: str,
    ) -> bool:
        """
        Detect simple resource relationships.

        Examples:

            Search for a paper
                ↓
            Compare the paper

            Download PDF
                ↓
            Read PDF
        """

        parent_resource_actions = [
            "open",
            "download",
            "create",
            "generate",
            "find",
            "search",
            "locate",
            "prepare",
            "select",
        ]

        child_resource_actions = [
            "use",
            "read",
            "review",
            "summarize",
            "edit",
            "modify",
            "execute",
            "run",
            "process",
            "compare",
        ]

        parent_has_action = any(
            self._contains_word(
                parent_text,
                action,
            )
            for action in parent_resource_actions
        )

        child_has_action = any(
            self._contains_word(
                child_text,
                action,
            )
            for action in child_resource_actions
        )

        return (
            parent_has_action
            and child_has_action
        )

    # ------------------------------------------------------------------
    # Shared terms
    # ------------------------------------------------------------------

    def _find_shared_terms(
        self,
        parent_text: str,
        child_text: str,
    ) -> list[str]:
        """
        Find meaningful terms shared between two tasks.

        Common English words and workflow verbs are ignored.
        """

        stopwords = {
            # General English
            "the",
            "a",
            "an",
            "and",
            "or",
            "to",
            "for",
            "of",
            "in",
            "on",
            "with",
            "from",
            "by",
            "is",
            "are",
            "was",
            "were",
            "this",
            "that",
            "it",
            "task",

            # Workflow/action words
            "open",
            "close",
            "launch",
            "start",
            "stop",
            "search",
            "find",
            "locate",
            "navigate",
            "download",
            "upload",
            "read",
            "write",
            "create",
            "generate",
            "prepare",
            "review",
            "run",
            "execute",
            "complete",
            "identify",
            "determine",
            "check",
            "compare",
            "summarize",
            "edit",
            "modify",
            "use",
            "access",
            "select",
        }

        parent_words = set(
            parent_text.split()
        )

        child_words = set(
            child_text.split()
        )

        shared = (
            parent_words
            & child_words
            - stopwords
        )

        return sorted(shared)

    # ------------------------------------------------------------------
    # Word matching
    # ------------------------------------------------------------------

    def _contains_word(
        self,
        text: str,
        word: str,
    ) -> bool:
        """
        Checks whether a complete word exists in text.
        """

        return bool(
            re.search(
                rf"\b{re.escape(word)}\b",
                text,
            )
        )