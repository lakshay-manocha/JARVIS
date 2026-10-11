"""
===============================================================================
File Name   : model_b_adapter.py
Module      : Integration / Adapters
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
Connects standalone Model B (State Mismatch Classifier) to JARVIS using the
contracts defined in agent_engine.state_mismatch.state_mismatch_contract.

Responsibilities:
- Validate and construct StateMismatchQuery.
- Invoke Model B inference engine safely.
- Incorporate DeterministicStateChecker differences.
- Validate and return StateMismatchResult.
- Enforce fail-safe error handling and logging mode.
===============================================================================
"""

from __future__ import annotations

import logging
import math
import os
import sys
import time
from typing import Any, Callable
import importlib.util

from agent_engine.integration.feature_flags import (
    IntegrationFeatureFlags,
    get_feature_flags,
)
from agent_engine.integration.guard.deterministic_checker import (
    DeterministicStateChecker,
)
from agent_engine.state_mismatch.state_mismatch_contract import (
    ChangedResource,
    StateMismatchQuery,
    StateMismatchResult,
    StateSnapshot,
)

logger = logging.getLogger("jarvis.integration.model_b")

DEFAULT_MODEL_B_THRESHOLD = 0.30
MODEL_B_VERSION = "JARVIS-StateMismatch-v1.0"


class ModelBAdapter:
    """
    Adapter between JARVIS and Model B (State Mismatch Classifier).
    """

    def __init__(
        self,
        classifier_callable: Callable[..., dict[str, Any]] | None = None,
        model_dir: str | None = None,
        feature_flags: IntegrationFeatureFlags | None = None,
        threshold: float = DEFAULT_MODEL_B_THRESHOLD,
    ) -> None:
        if not math.isfinite(float(threshold)) or not 0.0 <= float(threshold) <= 1.0:
            raise ValueError("Model B threshold must be a finite value in [0, 1].")
        self._classifier_callable = classifier_callable
        self._model_dir = model_dir or self._discover_model_dir()
        self._feature_flags = feature_flags
        self._threshold = float(threshold)
        self._engine_instance: Any = None

    def _discover_model_dir(self) -> str | None:
        # 1. Project models/model_b
        base_workspace = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        local_path = os.path.join(base_workspace, "models", "model_b")
        if os.path.isdir(local_path):
            return local_path

        # 2. Downloads path
        downloads_path = r"C:\Users\anmol\Downloads\Custom Goal-Conditioned Workflow Retrieval\Stored-State vs Current-State Mismatch Classifier\jarvis_state_mismatch_model"
        if os.path.isdir(downloads_path):
            return downloads_path

        return None

    def _get_flags(self) -> IntegrationFeatureFlags:
        return self._feature_flags or get_feature_flags()

    def _load_engine(self) -> Callable[..., dict[str, Any]] | None:
        """Lazily load Model B without colliding with Model A's predictor."""
        if self._classifier_callable is not None:
            return self._classifier_callable

        if self._engine_instance is not None:
            return self._engine_instance

        if not self._model_dir:
            logger.warning("Model B directory is not configured.")
            return None

        predictor_path = os.path.join(self._model_dir, "predictor.py")

        if not os.path.isfile(predictor_path):
            logger.warning("Model B predictor not found: %s", predictor_path)
            return None

        module_name = "_jarvis_model_b_predictor"

        try:
            module = sys.modules.get(module_name)

            if module is None:
                spec = importlib.util.spec_from_file_location(
                    module_name, predictor_path
                )
                if spec is None or spec.loader is None:
                    raise ImportError(
                        f"Cannot create import specification for {predictor_path}"
                    )

                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module

                try:
                    spec.loader.exec_module(module)
                except Exception:
                    sys.modules.pop(module_name, None)
                    raise

            self._engine_instance = getattr(
                module, "predict_state_mismatch"
            )
            return self._engine_instance

        except Exception as exc:
            logger.error(
                "Failed to initialize Model B predictor: %s",
                exc,
                exc_info=True,
            )
            return None

    def check_mismatch(
        self,
        query: StateMismatchQuery,
    ) -> StateMismatchResult:
        """
        Evaluate runtime state mismatch between stored and current states.

        Returns StateMismatchResult.
        Fail-Safe: If Model B is disabled, unavailable, or raises an error,
        it still returns deterministic state differences with safe fallback flags.
        """
        flags = self._get_flags()
        start_time = time.perf_counter()

        # Step 1: Compute deterministic state differences
        deterministic_diffs = DeterministicStateChecker.check_differences(
            stored_state=query.stored_state,
            current_state=query.current_state,
        )

        # Check if Model B is disabled
        if not flags.model_b_enabled:
            latency_ms = (time.perf_counter() - start_time) * 1000
            # When Model B is disabled, report mismatch if hard differences exist,
            # or False if none exist.
            has_diff = len(deterministic_diffs) > 0
            logger.debug(
                "Model B feature flag is OFF. Using deterministic evidence only."
            )
            return StateMismatchResult(
                mismatch=has_diff,
                probability=1.0 if has_diff else 0.0,
                confidence=1.0,
                threshold=self._threshold,
                changed_resources=deterministic_diffs,
                model_version=f"{MODEL_B_VERSION}-deterministic-fallback",
            )

        engine_fn = self._load_engine()

        # If engine cannot be loaded, fail-safe to deterministic diff
        if engine_fn is None:
            latency_ms = (time.perf_counter() - start_time) * 1000
            has_diff = len(deterministic_diffs) > 0
            if flags.model_b_logging_mode:
                self._log_inference(
                    success=False,
                    mismatch=has_diff,
                    probability=1.0 if has_diff else 0.0,
                    latency_ms=latency_ms,
                    detail="Model B engine unavailable; used deterministic checker fallback",
                )
            return StateMismatchResult(
                mismatch=has_diff,
                probability=1.0 if has_diff else 0.0,
                confidence=1.0,
                threshold=self._threshold,
                changed_resources=deterministic_diffs,
                model_version=f"{MODEL_B_VERSION}-fallback",
            )

        # Prepare dict inputs for Model B predictor
        stored_dict = query.stored_state.model_dump()
        current_dict = query.current_state.model_dump()

        try:
            raw_result = engine_fn(
                stored_state=stored_dict,
                current_state=current_dict,
            )
        except Exception as exc:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error("Model B inference error: %s", exc, exc_info=True)
            has_diff = len(deterministic_diffs) > 0
            if flags.model_b_logging_mode:
                self._log_inference(
                    success=False,
                    mismatch=has_diff,
                    probability=1.0 if has_diff else 0.0,
                    latency_ms=latency_ms,
                    detail=f"Inference error: {exc}",
                )
            return self._deterministic_fallback(
                deterministic_diffs,
                suffix="error-fallback",
            )

        latency_ms = (time.perf_counter() - start_time) * 1000

        try:
            if not isinstance(raw_result, dict):
                raise TypeError("Model B output must be a dictionary.")

            raw_diffs = raw_result.get("changed_resources", [])
            if not isinstance(raw_diffs, list):
                raise TypeError("Model B 'changed_resources' must be a list.")

            prob = float(raw_result.get("probability", 0.0))
            confidence = float(raw_result.get("confidence", 1.0))
            threshold = float(raw_result.get("threshold", self._threshold))
            if not all(math.isfinite(v) and 0.0 <= v <= 1.0 for v in (prob, confidence, threshold)):
                raise ValueError("Model B probability, confidence, and threshold must be finite values in [0, 1].")

            raw_mismatch = raw_result.get("mismatch", prob >= threshold)
            if not isinstance(raw_mismatch, bool):
                raise TypeError("Model B 'mismatch' must be a boolean.")

            model_version = str(raw_result.get("model_version", MODEL_B_VERSION)).strip()
            if not model_version:
                raise ValueError("Model B model_version must not be empty.")

            merged_changed_resources = self._merge_changed_resources(
                deterministic_diffs, raw_diffs
            )
            # Deterministic differences are independent evidence. Never return
            # mismatch=False while the merged contract contains differences.
            mismatch = raw_mismatch or bool(merged_changed_resources)

            result = StateMismatchResult(
                mismatch=mismatch,
                probability=prob,
                confidence=confidence,
                threshold=threshold,
                changed_resources=merged_changed_resources,
                model_version=model_version,
            )
        except Exception as exc:
            logger.warning("Model B returned malformed output; using deterministic fallback: %s", exc, exc_info=True)
            if flags.model_b_logging_mode:
                self._log_inference(
                    success=False,
                    mismatch=bool(deterministic_diffs),
                    probability=1.0 if deterministic_diffs else 0.0,
                    latency_ms=latency_ms,
                    detail=f"Malformed output fallback: {exc}",
                )
            return self._deterministic_fallback(
                deterministic_diffs,
                suffix="malformed-output-fallback",
            )

        if flags.model_b_logging_mode:
            self._log_inference(
                success=True,
                mismatch=result.mismatch,
                probability=result.probability,
                latency_ms=latency_ms,
                detail=f"Found {len(result.changed_resources)} changed resources",
            )
        return result

    def _deterministic_fallback(
        self,
        deterministic_diffs: list[ChangedResource],
        suffix: str = "fallback",
    ) -> StateMismatchResult:
        """Build a validated deterministic-only result after any model failure."""
        has_diff = bool(deterministic_diffs)
        return StateMismatchResult(
            mismatch=has_diff,
            probability=1.0 if has_diff else 0.0,
            confidence=1.0,
            threshold=self._threshold,
            changed_resources=deterministic_diffs,
            model_version=f"{MODEL_B_VERSION}-{suffix}",
        )

    def _merge_changed_resources(
        self,
        deterministic_diffs: list[ChangedResource],
        raw_diffs: list[dict[str, Any]],
    ) -> list[ChangedResource]:
        """Merge deterministic and raw diffs without duplicating identities."""
        merged_map: dict[tuple[str, str, str], ChangedResource] = {}

        for diff in deterministic_diffs:
            key = (str(diff.type.value), diff.identifier.lower(), str(diff.change.value))
            merged_map[key] = diff

        for r in raw_diffs:
            try:
                res_type = r.get("type", "APPLICATION")
                ident = str(r.get("identifier", "")).strip()
                chg = r.get("change", "MISSING")
                if ident:
                    key = (str(res_type), ident.lower(), str(chg))
                    if key not in merged_map:
                        merged_map[key] = ChangedResource(
                            type=res_type,
                            identifier=ident,
                            change=chg,
                        )
            except Exception:
                continue

        return list(merged_map.values())

    def _log_inference(
        self,
        success: bool,
        mismatch: bool,
        probability: float,
        latency_ms: float,
        detail: str,
    ) -> None:
        """Phase 10 & Feature Flag Logging Mode requirement."""
        logger.info(
            "[MODEL_B_MISMATCH] success=%s mismatch=%s prob=%.4f latency=%.2fms detail='%s'",
            success,
            mismatch,
            probability,
            latency_ms,
            detail,
        )
