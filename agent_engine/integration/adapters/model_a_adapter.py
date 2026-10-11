"""
===============================================================================
File Name   : model_a_adapter.py
Module      : Integration / Adapters
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
Connects standalone Model A (Goal-Conditioned Workflow Retrieval) to JARVIS
using the contracts defined in agent_engine.workflow_memory.retrieval_contract.

Responsibilities:
- Translate JARVIS RetrievalQuery and WorkflowRepository into Model A format.
- Invoke Model A retrieval engine safely.
- Map Model A output back to JARVIS RetrievalResponse / RetrievalResult.
- Enforce fail-safe error handling and logging mode (Phase 5).
- Ensure Model A remains advisory and never executes actions directly.
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
from agent_engine.workflow_memory.retrieval_contract import (
    RetrievalQuery,
    RetrievalResponse,
    RetrievalResult,
    WorkflowMemoryDocument,
)
from agent_engine.workflow_memory.workflow_record import WorkflowRecord
from agent_engine.workflow_memory.workflow_repository import WorkflowRepository

logger = logging.getLogger("jarvis.integration.model_a")


class ModelAAdapter:
    """
    Adapter between JARVIS and Model A (Goal-Conditioned Workflow Retrieval).
    """

    def __init__(
        self,
        predictor_callable: Callable[..., dict[str, Any]] | None = None,
        model_dir: str | None = None,
        feature_flags: IntegrationFeatureFlags | None = None,
    ) -> None:
        """
        Initialize the adapter.

        Args:
            predictor_callable: Optional custom predictor function for testing or DI.
            model_dir: Directory containing the model weights and predictor.py.
            feature_flags: Optional feature flag overrides.
        """
        self._predictor_callable = predictor_callable
        self._model_dir = model_dir or self._discover_model_dir()
        self._feature_flags = feature_flags
        self._engine_instance: Any = None

    def _discover_model_dir(self) -> str | None:
        """Find the local model path."""
        # 1. Project models/model_a
        base_workspace = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        local_path = os.path.join(base_workspace, "models", "model_a")
        if os.path.isdir(local_path):
            return local_path

        # 2. Downloads path
        downloads_path = r"C:\Users\anmol\Downloads\Custom Goal-Conditioned Workflow Retrieval\jarvis_workflow_retrieval_model"
        if os.path.isdir(downloads_path):
            return downloads_path

        return None

    def _get_flags(self) -> IntegrationFeatureFlags:
        return self._feature_flags or get_feature_flags()

    def _load_engine(self) -> Callable[..., dict[str, Any]] | None:
        """Lazily load Model A without colliding with Model B's predictor."""
        if self._predictor_callable is not None:
            return self._predictor_callable

        if self._engine_instance is not None:
            return self._engine_instance

        if not self._model_dir:
            logger.warning("Model A directory is not configured.")
            return None

        predictor_path = os.path.join(self._model_dir, "predictor.py")

        if not os.path.isfile(predictor_path):
            logger.warning("Model A predictor not found: %s", predictor_path)
            return None

        module_name = "_jarvis_model_a_predictor"

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

            predictor_class = getattr(module, "WorkflowPredictor")

            predictor = predictor_class(
                model_dir=os.path.join(self._model_dir, "model"),
                tokenizer_dir=os.path.join(self._model_dir, "tokenizer"),
            )

            self._engine_instance = predictor.retrieve
            return self._engine_instance

        except Exception as exc:
            logger.error(
                "Failed to initialize Model A WorkflowPredictor: %s",
                exc,
                exc_info=True,
            )
            return None
        
    def retrieve(
        self,
        query: RetrievalQuery,
        repository: WorkflowRepository,
        current_state: dict[str, Any] | None = None,
    ) -> RetrievalResponse:
        """
        Execute workflow retrieval using Model A.

        Fail-Safe: If Model A is disabled, unavailable, or raises an error,
        returns an empty RetrievalResponse with retrieval_performed=False.
        """
        flags = self._get_flags()

        # Check feature flags
        if not flags.is_model_a_active():
            reason = (
                "FEATURE_FLAG_DISABLED"
                if not flags.model_a_enabled
                else "FEATURE_MODES_DISABLED"
            )
            logger.debug("Model A is inactive (%s).", reason)
            return RetrievalResponse(
                query=query,
                results=[],
                retrieval_performed=False,
                metadata={"reason": reason},
            )

        start_time = time.perf_counter()
        try:
            records = repository.list_all()
            # Filter by domain if specified in query
            if query.domain:
                records = [r for r in records if r.domain == query.domain]
        except Exception as exc:
            logger.warning("Model A repository lookup failed: %s", exc, exc_info=True)
            return RetrievalResponse(
                query=query,
                results=[],
                retrieval_performed=False,
                metadata={"reason": "REPOSITORY_ERROR", "error": str(exc)},
            )

        if not records:
            latency_ms = (time.perf_counter() - start_time) * 1000
            if flags.model_a_logging_mode:
                self._log_operation(
                    query=query,
                    success=True,
                    results_count=0,
                    latency_ms=latency_ms,
                    detail="No candidate workflows available in repository",
                )
            return RetrievalResponse(
                query=query,
                results=[],
                retrieval_performed=True,
                metadata={"latency_ms": latency_ms, "candidates_count": 0},
            )

        # Convert JARVIS records to Model A candidate workflow format
        candidates = [self._record_to_candidate(r) for r in records]

        engine_fn = self._load_engine()
        if engine_fn is None:
            latency_ms = (time.perf_counter() - start_time) * 1000
            if flags.model_a_logging_mode:
                self._log_operation(
                    query=query,
                    success=False,
                    results_count=0,
                    latency_ms=latency_ms,
                    detail="Model A engine unavailable",
                )
            return RetrievalResponse(
                query=query,
                results=[],
                retrieval_performed=False,
                metadata={
                    "reason": "ENGINE_UNAVAILABLE",
                    "latency_ms": latency_ms,
                },
            )

        try:
            raw_result = engine_fn(
                query=query.query,
                current_state=current_state or {},
                candidate_workflows=candidates,
                top_k=query.top_k,
            )
        except Exception as exc:
            latency_ms = (time.perf_counter() - start_time) * 1000
            if flags.model_a_logging_mode:
                self._log_operation(
                    query=query,
                    success=False,
                    results_count=0,
                    latency_ms=latency_ms,
                    detail=f"Engine error: {exc}",
                )
            logger.error("Model A inference error: %s", exc, exc_info=True)
            return RetrievalResponse(
                query=query,
                results=[],
                retrieval_performed=False,
                metadata={
                    "reason": "INFERENCE_ERROR",
                    "error": str(exc),
                    "latency_ms": latency_ms,
                },
            )

        latency_ms = (time.perf_counter() - start_time) * 1000
        try:
            if not isinstance(raw_result, dict):
                raise TypeError("Model A output must be a dictionary.")
            raw_results = raw_result.get("results", [])
            if not isinstance(raw_results, list):
                raise TypeError("Model A output 'results' must be a list.")

            parsed_results = self._parse_engine_results(
                raw_result=raw_result,
                repository=repository,
                min_score=query.min_score,
            )
            model_version = raw_result.get("model_version", "unknown")
        except Exception as exc:
            logger.warning("Model A returned malformed output: %s", exc, exc_info=True)
            if flags.model_a_logging_mode:
                self._log_operation(
                    query=query,
                    success=False,
                    results_count=0,
                    latency_ms=latency_ms,
                    detail=f"Malformed model output: {exc}",
                )
            return RetrievalResponse(
                query=query,
                results=[],
                retrieval_performed=False,
                metadata={
                    "reason": "MALFORMED_OUTPUT",
                    "error": str(exc),
                    "latency_ms": latency_ms,
                },
            )

        if flags.model_a_logging_mode:
            self._log_operation(
                query=query,
                success=True,
                results_count=len(parsed_results),
                latency_ms=latency_ms,
                detail=f"Model version: {model_version}",
            )

        return RetrievalResponse(
            query=query,
            results=parsed_results,
            retrieval_performed=True,
            metadata={
                "latency_ms": latency_ms,
                "model_version": model_version,
                "candidates_count": len(candidates),
                "logging_mode": flags.model_a_logging_mode,
                "advisory_mode": flags.model_a_advisory_mode,
            },
        )

    def _record_to_candidate(self, record: WorkflowRecord) -> dict[str, Any]:
        """Convert a JARVIS WorkflowRecord to Model A candidate workflow schema."""
        return {
            "workflow_id": record.workflow_id,
            "goal": record.goal,
            "domain": record.domain,
            "overall_status": record.overall_status,
            "graph": record.graph,
            "current_state": record.current_state,
        }

    def _parse_engine_results(
        self,
        raw_result: dict[str, Any],
        repository: WorkflowRepository,
        min_score: float | None = None,
    ) -> list[RetrievalResult]:
        """Convert raw engine results to JARVIS RetrievalResult contracts."""
        parsed: list[RetrievalResult] = []
        raw_list = raw_result.get("results", [])
        if not isinstance(raw_list, list):
            raise TypeError("Model A output 'results' must be a list.")

        rank = 1
        for item in raw_list:
            if not isinstance(item, dict):
                raise TypeError("Each Model A result must be a dictionary.")
            wf_id = item.get("workflow_id")
            score = float(item.get("score", 0.0))
            if not math.isfinite(score) or not 0.0 <= score <= 1.0:
                raise ValueError("Model A result scores must be finite values in [0, 1].")

            if min_score is not None and score < min_score:
                continue

            record = repository.get(wf_id)
            if record is None:
                continue

            doc_text = (
                f"Domain: {record.domain} | Goal: {record.goal} | "
                f"Status: {record.overall_status}"
            )

            metadata = dict(record.metadata)
            metadata["retrieved_node_ids"] = item.get("retrieved_node_ids", [])

            document = WorkflowMemoryDocument(
                document_id=f"doc_{record.workflow_id}",
                workflow_id=record.workflow_id,
                text=doc_text,
                goal=record.goal,
                domain=record.domain,
                overall_status=record.overall_status,
                metadata=metadata,
            )

            parsed.append(
                RetrievalResult(
                    document=document,
                    score=score,
                    rank=rank,
                    retrieval_source="model_a",
                    metadata={"retrieved_node_ids": item.get("retrieved_node_ids", [])},
                )
            )
            rank += 1

        return parsed

    def _log_operation(
        self,
        query: RetrievalQuery,
        success: bool,
        results_count: int,
        latency_ms: float,
        detail: str,
    ) -> None:
        """Phase 5 Logging Mode requirement: log structured telemetry."""
        logger.info(
            "[MODEL_A_RETRIEVAL] query='%s' domain=%s success=%s results=%d latency=%.2fms detail='%s'",
            query.query,
            query.domain,
            success,
            results_count,
            latency_ms,
            detail,
        )
