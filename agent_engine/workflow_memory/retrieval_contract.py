"""
===============================================================================
File Name   : retrieval_contract.py
Module      : Workflow Memory
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
Defines the input and output contracts for Model A-compatible workflow
retrieval.

This file contains only data models. It does not perform embeddings,
vector search, ranking, model inference, or workflow execution.

The contracts are intentionally independent of any specific retrieval
implementation such as FAISS, a vector database, or a language model.
===============================================================================
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class WorkflowMemoryDocument(BaseModel):
    """
    Retrieval-friendly representation of a historical workflow.

    A document contains the textual and structured information that may be
    indexed or supplied to a retrieval system.
    """

    document_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier of the retrieval document.",
    )

    workflow_id: str = Field(
        ...,
        min_length=1,
        description="Identifier of the source historical workflow.",
    )

    text: str = Field(
        ...,
        min_length=1,
        description="Textual representation used for retrieval.",
    )

    goal: str = Field(
        ...,
        min_length=1,
        description="High-level goal of the source workflow.",
    )

    domain: str = Field(
        ...,
        min_length=1,
        description="Domain of the source workflow.",
    )

    overall_status: str = Field(
        ...,
        min_length=1,
        description="Recorded status of the source workflow.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional retrieval metadata.",
    )

    model_config = {
        "validate_assignment": True,
        "extra": "forbid",
    }


class RetrievalQuery(BaseModel):
    """
    Input contract for workflow-memory retrieval.

    This model describes what information the retrieval layer should search
    for. It does not execute the search.
    """

    query: str = Field(
        ...,
        min_length=1,
        description="Natural-language retrieval query.",
    )

    domain: str | None = Field(
        default=None,
        description="Optional domain filter.",
    )

    top_k: int = Field(
        default=5,
        ge=1,
        description="Maximum number of results requested.",
    )

    min_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional minimum normalized relevance score.",
    )

    filters: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional retrieval filters.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional query metadata.",
    )

    model_config = {
        "validate_assignment": True,
        "extra": "forbid",
    }

    @field_validator("query")
    @classmethod
    def validate_query_not_blank(cls, value: str) -> str:
        """
        Reject whitespace-only queries.
        """

        if not value.strip():
            raise ValueError("query must not be blank")

        return value


class RetrievalResult(BaseModel):
    """
    Output contract for one retrieved workflow-memory result.
    """

    document: WorkflowMemoryDocument = Field(
        ...,
        description="Retrieved workflow-memory document.",
    )

    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Normalized relevance score.",
    )

    rank: int = Field(
        ...,
        ge=1,
        description="One-based ranking position.",
    )

    retrieval_source: str = Field(
        default="model_a",
        min_length=1,
        description="Source or retrieval mechanism that produced the result.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional result metadata.",
    )

    model_config = {
        "validate_assignment": True,
        "extra": "forbid",
    }


class RetrievalResponse(BaseModel):
    """
    Complete response contract for a retrieval operation.

    This model supports both successful retrieval and empty-result responses.
    """

    query: RetrievalQuery = Field(
        ...,
        description="Original retrieval query.",
    )

    results: list[RetrievalResult] = Field(
        default_factory=list,
        description="Retrieved results ordered by rank.",
    )

    total_results: int | None = Field(
        default=None,
        ge=0,
        description="Number of returned results.",
    )

    retrieval_performed: bool = Field(
        default=False,
        description="Whether a retrieval operation was performed.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional response metadata.",
    )

    model_config = {
        "validate_assignment": True,
        "extra": "forbid",
    }

    def model_post_init(self, __context: Any) -> None:
        """
        Set total_results consistently after model initialization.
        """

        object.__setattr__(
            self,
            "total_results",
            len(self.results),
        )