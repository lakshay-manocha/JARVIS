"""
===============================================================================
File Name   : test_model_a_integration.py
Module      : Tests / Integration
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
Unit & integration tests for Phase 4 (Model A Adapter), Phase 5 (Logging Mode),
and Phase 6 (Advisory Planning) in compliance with Phase 7 requirements.
===============================================================================
"""

from __future__ import annotations

import pytest

from agent_engine.integration.adapters.model_a_adapter import ModelAAdapter
from agent_engine.integration.advisory.workflow_advisory_planner import (
    WorkflowAdvisoryPlanner,
)
from agent_engine.integration.feature_flags import IntegrationFeatureFlags
from agent_engine.workflow_memory.retrieval_contract import RetrievalQuery
from agent_engine.workflow_memory.workflow_record import WorkflowRecord
from agent_engine.workflow_memory.workflow_repository import WorkflowRepository


@pytest.fixture
def sample_repository() -> WorkflowRepository:
    repo = WorkflowRepository()
    record1 = WorkflowRecord(
        workflow_id="wf_data_analysis",
        goal="Fetch dataset and train linear model",
        domain="data_science",
        overall_status="COMPLETED",
        graph={
            "nodes": [
                {"id": 1, "description": "Fetch CSV data", "status": "COMPLETED"},
                {"id": 2, "description": "Train linear model", "status": "COMPLETED"},
            ]
        },
        current_state={"applications": ["Python"], "files": ["data.csv"]},
    )
    record2 = WorkflowRecord(
        workflow_id="wf_browser_scrape",
        goal="Scrape product prices from web page",
        domain="browser",
        overall_status="FAILED",
        graph={
            "nodes": [
                {"id": 10, "description": "Open website", "status": "COMPLETED"},
                {"id": 11, "description": "Scrape table rows", "status": "FAILED"},
            ]
        },
        current_state={"applications": ["Chrome"], "files": []},
    )
    repo.save(record1)
    repo.save(record2)
    return repo


@pytest.fixture
def mock_predictor_callable():
    def _mock_predict(query: str, current_state: dict, candidate_workflows: list, top_k: int):
        results = []
        for cand in candidate_workflows:
            wf_id = cand["workflow_id"]
            if "scrape" in query.lower() and "scrape" in wf_id:
                results.append({"workflow_id": wf_id, "score": 0.88, "retrieved_node_ids": [11]})
            elif "dataset" in query.lower() and "data" in wf_id:
                results.append({"workflow_id": wf_id, "score": 0.92, "retrieved_node_ids": [1, 2]})
            else:
                results.append({"workflow_id": wf_id, "score": 0.30, "retrieved_node_ids": []})
        results.sort(key=lambda r: r["score"], reverse=True)
        return {
            "query": query,
            "results": results[:top_k],
            "model_version": "Mock-ModelA-v1.0",
        }
    return _mock_predict


def test_feature_flag_off_returns_safely(sample_repository, mock_predictor_callable):
    flags = IntegrationFeatureFlags(model_a_enabled=False)
    adapter = ModelAAdapter(predictor_callable=mock_predictor_callable, feature_flags=flags)

    query = RetrievalQuery(query="Scrape product prices")
    response = adapter.retrieve(query, sample_repository)

    assert not response.retrieval_performed
    assert len(response.results) == 0
    assert response.metadata.get("reason") == "FEATURE_FLAG_DISABLED"


def test_adapter_retrieval_success(sample_repository, mock_predictor_callable):
    flags = IntegrationFeatureFlags(model_a_enabled=True, model_a_logging_mode=True)
    adapter = ModelAAdapter(predictor_callable=mock_predictor_callable, feature_flags=flags)

    query = RetrievalQuery(query="Scrape product prices", top_k=2)
    response = adapter.retrieve(query, sample_repository)

    assert response.retrieval_performed
    assert len(response.results) > 0
    top = response.results[0]
    assert top.document.workflow_id == "wf_browser_scrape"
    assert top.score == 0.88
    assert top.rank == 1
    assert top.metadata.get("retrieved_node_ids") == [11]


def test_adapter_domain_filter(sample_repository, mock_predictor_callable):
    flags = IntegrationFeatureFlags(model_a_enabled=True)
    adapter = ModelAAdapter(predictor_callable=mock_predictor_callable, feature_flags=flags)

    query = RetrievalQuery(query="Scrape product prices", domain="data_science")
    response = adapter.retrieve(query, sample_repository)

    assert response.retrieval_performed
    # Browser workflow should be excluded by domain filter
    for r in response.results:
        assert r.document.domain == "data_science"


def test_empty_repository(mock_predictor_callable):
    flags = IntegrationFeatureFlags(model_a_enabled=True)
    adapter = ModelAAdapter(predictor_callable=mock_predictor_callable, feature_flags=flags)
    empty_repo = WorkflowRepository()

    query = RetrievalQuery(query="Anything")
    response = adapter.retrieve(query, empty_repo)

    assert response.retrieval_performed
    assert len(response.results) == 0


def test_engine_failure_handles_gracefully(sample_repository):
    def failing_predictor(*args, **kwargs):
        raise RuntimeError("GPU memory exhausted")

    flags = IntegrationFeatureFlags(model_a_enabled=True)
    adapter = ModelAAdapter(predictor_callable=failing_predictor, feature_flags=flags)

    query = RetrievalQuery(query="Scrape product prices")
    response = adapter.retrieve(query, sample_repository)

    # Must fail-safe without raising exception
    assert not response.retrieval_performed
    assert len(response.results) == 0
    assert response.metadata.get("reason") == "INFERENCE_ERROR"


def test_advisory_planner_integration(sample_repository, mock_predictor_callable):
    flags = IntegrationFeatureFlags(
        model_a_enabled=True,
        model_a_advisory_mode=True,
    )
    adapter = ModelAAdapter(predictor_callable=mock_predictor_callable, feature_flags=flags)
    advisor = WorkflowAdvisoryPlanner(
        adapter=adapter,
        repository=sample_repository,
        feature_flags=flags,
        min_relevance_threshold=0.50,
    )

    context = advisor.get_advisory_context("Scrape product prices")
    assert context.has_advice
    assert context.matched_workflow_id == "wf_browser_scrape"
    assert context.continuation_node_ids == [11]
    assert len(context.suggested_nodes) == 1
    assert context.suggested_nodes[0]["id"] == 11


def test_advisory_planner_inactive_when_flag_off(sample_repository, mock_predictor_callable):
    flags = IntegrationFeatureFlags(
        model_a_enabled=True,
        model_a_advisory_mode=False,  # Advisory mode OFF
    )
    adapter = ModelAAdapter(predictor_callable=mock_predictor_callable, feature_flags=flags)
    advisor = WorkflowAdvisoryPlanner(
        adapter=adapter,
        repository=sample_repository,
        feature_flags=flags,
    )

    context = advisor.get_advisory_context("Scrape product prices")
    assert not context.has_advice
