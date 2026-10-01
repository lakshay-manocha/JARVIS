"""
===============================================================================
File Name   : intent_detector.py
Module      : Agent Brain
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Detects the high-level intent of each interpreted task.

This module performs lightweight rule-based intent detection using normalized
task text. The detected intent is stored as an IntentResult object and attached
to each InterpretedTask.

The rules are ordered from most specific to most generic so that a specific
automation intent is not incorrectly classified by a generic keyword.

Responsibilities:
    • Read interpreted tasks
    • Detect task intent
    • Create IntentResult objects
    • Attach intent to InterpretedTask
    • Record processing logs

Author      : Team JARVIS
===============================================================================
"""

from __future__ import annotations

import re

from agent_engine.agent_brain.models.intent_result import IntentResult
from agent_engine.agent_brain.models.processing_context import ProcessingContext
from agent_engine.contracts.enums import IntentType, ProcessingStage


class IntentDetector:
    """
    Detects the intent of interpreted tasks.
    """

    # =========================================================================
    # Public API
    # =========================================================================

    def detect(
        self,
        context: ProcessingContext,
    ) -> ProcessingContext:
        """
        Detect intents for every interpreted task.
        """

        context.current_stage = ProcessingStage.DETECTING_INTENT

        context.log("Intent detection started.")

        for task in context.interpreted_tasks:

            intent_result = self._detect_intent(
                task.normalized_text
            )

            task.intent = intent_result

            context.log(
                f"Intent detected for Task {task.task_id}: "
                f"{intent_result.intent.value}"
            )

        context.log(
            f"Intent detection completed for "
            f"{len(context.interpreted_tasks)} task(s)."
        )

        return context

    # =========================================================================
    # Rule-Based Intent Detection
    # =========================================================================

    def _detect_intent(
        self,
        text: str,
    ) -> IntentResult:
        """
        Detect intent using rule-based pattern matching.

        Rules are intentionally ordered from specific to generic.

        For example:

            "move mouse to 500 300"

        must be classified as:

            MOVE_MOUSE

        rather than:

            MOVE_FILE

        because "move mouse" is a specific mouse command while "move" alone
        is a generic file-operation keyword.
        """

        text = text.lower().strip()

        # =====================================================================
        # 1. WEBSITE
        # =====================================================================

        url_pattern = r"https?://[^\s]+|www\.[^\s]+"

        contains_url = re.search(
            url_pattern,
            text,
        ) is not None

        website_keywords = [
            "visit",
            "browse",
            "go to",
            "open website",
            "open webpage",
            "open web page",
            "open url",
            "open link",
        ]

        if contains_url or any(
            keyword in text
            for keyword in website_keywords
        ):
            return IntentResult(
                intent=IntentType.OPEN_WEBSITE,
                confidence=1.0,
                detection_method="rule_based",
                reasoning=(
                    "Detected website-opening language or URL in task."
                ),
            )

        # =====================================================================
        # 2. WEB SEARCH
        # =====================================================================

        search_keywords = [
            "search",
            "find",
            "lookup",
            "google",
        ]

        for keyword in search_keywords:

            if keyword in text:

                return IntentResult(
                    intent=IntentType.SEARCH_WEB,
                    confidence=1.0,
                    detection_method="rule_based",
                    reasoning=(
                        f"Matched keyword '{keyword}' "
                        f"for intent {IntentType.SEARCH_WEB.value}."
                    ),
                )

        # =====================================================================
        # 3. FILE DOWNLOAD
        # =====================================================================

        download_keywords = [
            "download",
            "fetch",
            "grab",
        ]

        for keyword in download_keywords:

            if keyword in text:

                return IntentResult(
                    intent=IntentType.DOWNLOAD_FILE,
                    confidence=1.0,
                    detection_method="rule_based",
                    reasoning=(
                        f"Matched keyword '{keyword}' "
                        f"for intent {IntentType.DOWNLOAD_FILE.value}."
                    ),
                )

        # =====================================================================
        # 4. DOCUMENT SUMMARIZATION
        # =====================================================================

        summarize_keywords = [
            "summarize",
            "summary",
        ]

        for keyword in summarize_keywords:

            if keyword in text:

                return IntentResult(
                    intent=IntentType.SUMMARIZE_DOCUMENT,
                    confidence=1.0,
                    detection_method="rule_based",
                    reasoning=(
                        f"Matched keyword '{keyword}' "
                        f"for intent "
                        f"{IntentType.SUMMARIZE_DOCUMENT.value}."
                    ),
                )

        # =====================================================================
        # 5. MOUSE - DOUBLE CLICK
        # =====================================================================

        if "double click" in text:

            return IntentResult(
                intent=IntentType.MOUSE_DOUBLE_CLICK,
                confidence=1.0,
                detection_method="rule_based",
                reasoning="Detected double-click mouse action.",
            )

        # =====================================================================
        # 6. MOUSE - RIGHT CLICK
        # =====================================================================

        if "right click" in text:

            return IntentResult(
                intent=IntentType.MOUSE_RIGHT_CLICK,
                confidence=1.0,
                detection_method="rule_based",
                reasoning="Detected right-click mouse action.",
            )

        # =====================================================================
        # 7. MOUSE - MOVE
        # =====================================================================

        if (
            "move mouse" in text
            or "move cursor" in text
        ):

            return IntentResult(
                intent=IntentType.MOVE_MOUSE,
                confidence=1.0,
                detection_method="rule_based",
                reasoning="Detected mouse movement action.",
            )

        # =====================================================================
        # 8. MOUSE - BUTTON DOWN
        # =====================================================================

        if (
            "mouse down" in text
            or "press mouse button" in text
            or "hold mouse button" in text
        ):

            return IntentResult(
                intent=IntentType.MOUSE_DOWN,
                confidence=1.0,
                detection_method="rule_based",
                reasoning=(
                    "Detected mouse button press-and-hold action."
                ),
            )

        # =====================================================================
        # 9. MOUSE - BUTTON UP
        # =====================================================================

        if (
            "mouse up" in text
            or "release mouse button" in text
        ):

            return IntentResult(
                intent=IntentType.MOUSE_UP,
                confidence=1.0,
                detection_method="rule_based",
                reasoning=(
                    "Detected mouse button release action."
                ),
            )

        # =====================================================================
        # 10. MOUSE - SCROLL
        # =====================================================================

        if "scroll" in text:

            return IntentResult(
                intent=IntentType.MOUSE_SCROLL,
                confidence=1.0,
                detection_method="rule_based",
                reasoning="Detected mouse scrolling action.",
            )

        # =====================================================================
        # 11. MOUSE - CLICK
        # =====================================================================

        if "click" in text:

            return IntentResult(
                intent=IntentType.MOUSE_CLICK,
                confidence=1.0,
                detection_method="rule_based",
                reasoning="Detected mouse click action.",
            )

        # =====================================================================
        # 12. KEYBOARD - TYPE TEXT
        # =====================================================================

        type_keywords = [
            "type",
            "write",
            "enter text",
        ]

        for keyword in type_keywords:

            if text.startswith(keyword):

                return IntentResult(
                    intent=IntentType.TYPE_TEXT,
                    confidence=1.0,
                    detection_method="rule_based",
                    reasoning=(
                        f"Matched keyword '{keyword}' "
                        f"for intent {IntentType.TYPE_TEXT.value}."
                    ),
                )

        # =====================================================================
        # 13. KEYBOARD - HOTKEY
        # =====================================================================

        hotkey_keywords = [
            "hotkey",
            "shortcut",
        ]

        for keyword in hotkey_keywords:

            if keyword in text:

                return IntentResult(
                    intent=IntentType.HOTKEY,
                    confidence=1.0,
                    detection_method="rule_based",
                    reasoning=(
                        f"Matched keyword '{keyword}' "
                        f"for intent {IntentType.HOTKEY.value}."
                    ),
                )

        # =====================================================================
        # 14. KEYBOARD - PRESS KEY
        # =====================================================================

        press_keywords = [
            "press",
            "hit",
        ]

        for keyword in press_keywords:

            if (
                text.startswith(keyword)
                and "mouse button" not in text
            ):

                return IntentResult(
                    intent=IntentType.PRESS_KEY,
                    confidence=1.0,
                    detection_method="rule_based",
                    reasoning=(
                        f"Matched keyword '{keyword}' "
                        f"for intent {IntentType.PRESS_KEY.value}."
                    ),
                )

        # =====================================================================
        # 15. FILE - DELETE
        # =====================================================================

        delete_keywords = [
            "delete",
            "remove",
            "erase",
        ]

        for keyword in delete_keywords:

            if keyword in text:

                return IntentResult(
                    intent=IntentType.DELETE_FILE,
                    confidence=1.0,
                    detection_method="rule_based",
                    reasoning=(
                        f"Matched keyword '{keyword}' "
                        f"for intent {IntentType.DELETE_FILE.value}."
                    ),
                )

        # =====================================================================
        # 16. FILE - MOVE
        # =====================================================================

        move_keywords = [
            "move",
            "transfer",
        ]

        for keyword in move_keywords:

            if keyword in text:

                return IntentResult(
                    intent=IntentType.MOVE_FILE,
                    confidence=1.0,
                    detection_method="rule_based",
                    reasoning=(
                        f"Matched keyword '{keyword}' "
                        f"for intent {IntentType.MOVE_FILE.value}."
                    ),
                )

        # =====================================================================
        # 17. FILE - COPY
        # =====================================================================

        copy_keywords = [
            "copy",
            "duplicate",
        ]

        for keyword in copy_keywords:

            if keyword in text:

                return IntentResult(
                    intent=IntentType.COPY_FILE,
                    confidence=1.0,
                    detection_method="rule_based",
                    reasoning=(
                        f"Matched keyword '{keyword}' "
                        f"for intent {IntentType.COPY_FILE.value}."
                    ),
                )

        # =====================================================================
        # 18. FILE - RENAME
        # =====================================================================

        rename_keywords = [
            "rename",
            "change name",
        ]

        for keyword in rename_keywords:

            if keyword in text:

                return IntentResult(
                    intent=IntentType.RENAME_FILE,
                    confidence=1.0,
                    detection_method="rule_based",
                    reasoning=(
                        f"Matched keyword '{keyword}' "
                        f"for intent {IntentType.RENAME_FILE.value}."
                    ),
                )

        # =====================================================================
        # 19. APPLICATION OPENING
        # =====================================================================

        application_keywords = [
            "open",
            "launch",
            "start",
            "run",
        ]

        for keyword in application_keywords:

            if keyword in text:

                return IntentResult(
                    intent=IntentType.OPEN_APPLICATION,
                    confidence=1.0,
                    detection_method="rule_based",
                    reasoning=(
                        f"Matched keyword '{keyword}' "
                        f"for intent "
                        f"{IntentType.OPEN_APPLICATION.value}."
                    ),
                )

        # =====================================================================
        # 20. UNKNOWN
        # =====================================================================

        return IntentResult(
            intent=IntentType.UNKNOWN,
            confidence=0.0,
            detection_method="rule_based",
            reasoning="No matching intent pattern was found.",
        )