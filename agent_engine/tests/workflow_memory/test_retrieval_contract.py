"""
===============================================================================
File Name   : test_retrieval_contract.py
Module      : Workflow Memory Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
Unit tests for Model A retrieval contracts.

These tests validate only the data models and their input/output contracts.
No actual retrieval, embedding generation, vector search, or model inference
is performed.
===============================================================================
"""

import pytest
from pydantic import ValidationError

from agent_engine.workflow_memory.retrieval_contract import (
    RetrievalQuery,
    RetrievalResponse,
    RetrievalResult,
    WorkflowMemoryDocument,
)


def create_document(
    document_id="doc_001",
    workflow_id="workflow_001",
    text="Open browser and search for artificial intelligence",
    goal="Search for artificial intelligence",
    domain="desktop_browser",
    overall_status="COMPLETED",
    metadata=None,
    **extra,
):
    payload = {
        "document_id": document_id,
        "workflow_id": workflow_id,
        "text": text,
        "goal": goal,
        "domain": domain,
        "overall_status": overall_status,
    }

    if metadata is not None:
        payload["metadata"] = metadata

    payload.update(extra)

    return WorkflowMemoryDocument(**payload)
def create_query(
    query="execute workflow",
    domain=None,
    top_k=5,
    min_score=None,
    filters=None,
    metadata=None,
    **extra,
):
    payload = {
        "query": query,
        "top_k": top_k,
    }

    if domain is not None:
        payload["domain"] = domain

    if min_score is not None:
        payload["min_score"] = min_score

    if filters is not None:
        payload["filters"] = filters

    if metadata is not None:
        payload["metadata"] = metadata

    payload.update(extra)

    return RetrievalQuery(**payload)

def create_result(
    document=None,
    score=0.95,
    rank=1,
    retrieval_source="model_a",
    metadata=None,
    **extra,
):
    payload = {
        "document": document or create_document(),
        "score": score,
        "rank": rank,
        "retrieval_source": retrieval_source,
    }

    if metadata is not None:
        payload["metadata"] = metadata

    payload.update(extra)

    return RetrievalResult(**payload)

# =============================================================================
# WorkflowMemoryDocument Tests
# =============================================================================


def test_workflow_memory_document_creates_with_required_fields():
    """
    Verify that a document can be created with required fields.
    """

    document = create_document()

    assert document.document_id == "doc_001"
    assert document.workflow_id == "workflow_001"
    assert document.text == (
        "Open browser and search for artificial intelligence"
    )
    assert document.goal == "Search for artificial intelligence"
    assert document.domain == "desktop_browser"
    assert document.overall_status == "COMPLETED"


def test_workflow_memory_document_uses_default_metadata():
    """
    Verify that metadata defaults to an empty dictionary.
    """

    document = create_document()

    assert document.metadata == {}


def test_workflow_memory_document_accepts_metadata():
    """
    Verify that document metadata is preserved.
    """

    metadata = {
        "source": "workflow_memory",
        "execution_mode": "mock",
        "node_count": 3,
    }

    document = create_document(metadata=metadata)

    assert document.metadata == metadata
    assert document.metadata["source"] == "workflow_memory"


@pytest.mark.parametrize(
    "field_name",
    [
        "document_id",
        "workflow_id",
        "text",
        "goal",
        "domain",
        "overall_status",
    ],
)
def test_workflow_memory_document_rejects_empty_required_fields(field_name):
    """
    Verify that required document string fields reject empty strings.
    """

    payload = {
        "document_id": "doc_001",
        "workflow_id": "workflow_001",
        "text": "Open browser",
        "goal": "Open browser",
        "domain": "desktop",
        "overall_status": "COMPLETED",
    }

    payload[field_name] = ""

    with pytest.raises(ValidationError):
        WorkflowMemoryDocument(**payload)


def test_workflow_memory_document_rejects_extra_fields():
    """
    Verify that unexpected document fields are rejected.
    """

    with pytest.raises(ValidationError):
        create_document(unexpected_field="not_allowed")


# =============================================================================
# RetrievalQuery Tests
# =============================================================================


def test_retrieval_query_creates_with_default_values():
    """
    Verify default values of RetrievalQuery.
    """

    query = RetrievalQuery(
        query="Find browser workflows",
    )

    assert query.query == "Find browser workflows"
    assert query.domain is None
    assert query.top_k == 5
    assert query.min_score is None
    assert query.filters == {}
    assert query.metadata == {}


def test_retrieval_query_accepts_all_supported_fields():
    """
    Verify that all query fields are preserved.
    """

    query = RetrievalQuery(
        query="Find browser workflows",
        domain="desktop_browser",
        top_k=3,
        min_score=0.70,
        filters={"overall_status": "COMPLETED"},
        metadata={"request_source": "agent_brain"},
    )

    assert query.query == "Find browser workflows"
    assert query.domain == "desktop_browser"
    assert query.top_k == 3
    assert query.min_score == 0.70
    assert query.filters == {"overall_status": "COMPLETED"}
    assert query.metadata == {"request_source": "agent_brain"}


def test_retrieval_query_rejects_blank_query():
    """
    Verify that whitespace-only queries are rejected.
    """

    with pytest.raises(ValidationError):
        RetrievalQuery(query="   ")


@pytest.mark.parametrize(
    "invalid_top_k",
    [0, -1],
)
def test_retrieval_query_rejects_invalid_top_k(invalid_top_k):
    """
    Verify that top_k must be at least 1.
    """

    with pytest.raises(ValidationError):
        RetrievalQuery(
            query="Find browser workflows",
            top_k=invalid_top_k,
        )


@pytest.mark.parametrize(
    "invalid_score",
    [-0.01, 1.01, 2.0],
)
def test_retrieval_query_rejects_invalid_min_score(invalid_score):
    """
    Verify that min_score must be between 0 and 1.
    """

    with pytest.raises(ValidationError):
        RetrievalQuery(
            query="Find browser workflows",
            min_score=invalid_score,
        )


def test_retrieval_query_accepts_boundary_scores():
    """
    Verify that min_score accepts the valid boundary values 0 and 1.
    """

    query_zero = RetrievalQuery(
        query="Find browser workflows",
        min_score=0.0,
    )

    query_one = RetrievalQuery(
        query="Find browser workflows",
        min_score=1.0,
    )

    assert query_zero.min_score == 0.0
    assert query_one.min_score == 1.0


def test_retrieval_query_rejects_extra_fields():
    """
    Verify that unexpected query fields are rejected.
    """

    with pytest.raises(ValidationError):
        RetrievalQuery(
            query="Find browser workflows",
            unexpected_field="not_allowed",
        )


# =============================================================================
# RetrievalResult Tests
# =============================================================================


def test_retrieval_result_creates_with_required_fields():
    """
    Verify that a retrieval result can be created.
    """

    document = create_document()

    result = RetrievalResult(
        document=document,
        score=0.91,
        rank=1,
    )

    assert result.document == document
    assert result.score == 0.91
    assert result.rank == 1
    assert result.retrieval_source == "model_a"
    assert result.metadata == {}


def test_retrieval_result_accepts_metadata():
    """
    Verify that result metadata is preserved.
    """

    metadata = {
        "index_name": "workflow_memory_index",
        "distance_metric": "cosine",
    }

    result = create_result(metadata=metadata)

    assert result.metadata == metadata
    assert result.metadata["index_name"] == "workflow_memory_index"


@pytest.mark.parametrize(
    "invalid_score",
    [-0.01, 1.01, 2.0],
)
def test_retrieval_result_rejects_invalid_score(invalid_score):
    """
    Verify that relevance score must be between 0 and 1.
    """

    with pytest.raises(ValidationError):
        create_result(score=invalid_score)


def test_retrieval_result_accepts_boundary_scores():
    """
    Verify that score accepts 0 and 1.
    """

    result_zero = create_result(score=0.0)
    result_one = create_result(score=1.0)

    assert result_zero.score == 0.0
    assert result_one.score == 1.0


@pytest.mark.parametrize(
    "invalid_rank",
    [0, -1],
)
def test_retrieval_result_rejects_invalid_rank(invalid_rank):
    """
    Verify that rank must be at least 1.
    """

    with pytest.raises(ValidationError):
        create_result(rank=invalid_rank)


def test_retrieval_result_rejects_empty_retrieval_source():
    """
    Verify that retrieval_source cannot be empty.
    """

    with pytest.raises(ValidationError):
        create_result(retrieval_source="")


def test_retrieval_result_rejects_extra_fields():
    """
    Verify that unexpected result fields are rejected.
    """

    with pytest.raises(ValidationError):
        create_result(unexpected_field="not_allowed")


def test_retrieval_result_validates_nested_document():
    """
    Verify that RetrievalResult requires a valid WorkflowMemoryDocument.
    """

    with pytest.raises(ValidationError):
        RetrievalResult(
            document={
                "document_id": "doc_001",
                "workflow_id": "workflow_001",
            },
            score=0.90,
            rank=1,
        )


# =============================================================================
# RetrievalResponse Tests
# =============================================================================


def test_retrieval_response_creates_with_empty_results():
    """
    Verify that an empty retrieval response is valid.
    """

    query = create_query()

    response = RetrievalResponse(
        query=query,
        results=[],
        retrieval_performed=True,
    )

    assert response.query == query
    assert response.results == []
    assert response.total_results == 0
    assert response.retrieval_performed is True
    assert response.metadata == {}


def test_retrieval_response_accepts_retrieval_results():
    """
    Verify that retrieval results are preserved.
    """

    query = create_query(top_k=2)

    result_one = create_result(
        document=create_document(document_id="doc_001"),
        score=0.95,
        rank=1,
    )

    result_two = create_result(
        document=create_document(document_id="doc_002"),
        score=0.85,
        rank=2,
    )

    response = RetrievalResponse(
        query=query,
        results=[result_one, result_two],
        retrieval_performed=True,
    )

    assert len(response.results) == 2
    assert response.total_results == 2
    assert response.results[0].rank == 1
    assert response.results[1].rank == 2


def test_retrieval_response_sets_total_results_automatically():
    """
    Verify that total_results is derived from the result list.
    """

    query = create_query()

    results = [
        create_result(
            document=create_document(document_id="doc_001"),
            score=0.90,
            rank=1,
        ),
        create_result(
            document=create_document(document_id="doc_002"),
            score=0.80,
            rank=2,
        ),
        create_result(
            document=create_document(document_id="doc_003"),
            score=0.70,
            rank=3,
        ),
    ]

    response = RetrievalResponse(
        query=query,
        results=results,
    )

    assert response.total_results == 3


def test_retrieval_response_defaults_retrieval_performed_to_false():
    """
    Verify the default value of retrieval_performed.
    """

    response = RetrievalResponse(
        query=create_query(),
    )

    assert response.retrieval_performed is False
    assert response.results == []
    assert response.total_results == 0


def test_retrieval_response_accepts_metadata():
    """
    Verify that response metadata is preserved.
    """

    metadata = {
        "retrieval_backend": "in_memory",
        "execution_time_ms": 12,
    }

    response = RetrievalResponse(
        query=create_query(),
        metadata=metadata,
    )

    assert response.metadata == metadata
    assert response.metadata["retrieval_backend"] == "in_memory"


def test_retrieval_response_rejects_extra_fields():
    """
    Verify that unexpected response fields are rejected.
    """

    with pytest.raises(ValidationError):
        RetrievalResponse(
            query=create_query(),
            unexpected_field="not_allowed",
        )


def test_retrieval_response_rejects_invalid_nested_query():
    """
    Verify that RetrievalResponse requires a valid RetrievalQuery.
    """

    with pytest.raises(ValidationError):
        RetrievalResponse(
            query={
                "query": "",
            },
        )


def test_retrieval_response_model_dump_contains_expected_fields():
    """
    Verify that the complete response can be serialized.
    """

    response = RetrievalResponse(
        query=create_query(),
        results=[create_result()],
        retrieval_performed=True,
    )

    dumped_response = response.model_dump()

    assert "query" in dumped_response
    assert "results" in dumped_response
    assert "total_results" in dumped_response
    assert "retrieval_performed" in dumped_response
    assert "metadata" in dumped_response