from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ResourceType(str, Enum):
    APPLICATION = "APPLICATION"
    FILE = "FILE"
    BROWSER_TAB = "BROWSER_TAB"
    PROCESS = "PROCESS"
    COMPLETED_SUBTASK = "COMPLETED_SUBTASK"


class ResourceChange(str, Enum):
    ADDED = "ADDED"
    MISSING = "MISSING"


class StateSnapshot(BaseModel):
    """
    Canonical representation of a stored or current runtime state.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    applications: list[str] | str = "NOT_AVAILABLE"
    files: list[str] | str = "NOT_AVAILABLE"
    browser_tabs: list[str] | str = "NOT_AVAILABLE"
    processes: list[str] | str = "NOT_AVAILABLE"
    completed_subtasks: list[str] | str = "NOT_AVAILABLE"

    timestamp: float | None = None
    resource_identities: list[str] = Field(default_factory=list)

    @field_validator(
        "applications",
        "files",
        "browser_tabs",
        "processes",
        "completed_subtasks",
    )
    @classmethod
    def validate_collection_or_unavailable(
        cls,
        value: list[str] | str,
    ) -> list[str] | str:
        if value == "NOT_AVAILABLE":
            return value

        if not isinstance(value, list):
            raise TypeError(
                "State collection must be a list or 'NOT_AVAILABLE'."
            )

        if not all(isinstance(item, str) for item in value):
            raise TypeError(
                "Every state collection item must be a string."
            )

        return value

    @field_validator("resource_identities")
    @classmethod
    def validate_resource_identities(
        cls,
        value: list[str],
    ) -> list[str]:
        if not all(isinstance(item, str) for item in value):
            raise TypeError(
                "Every resource identity must be a string."
            )

        return value


class StateMismatchQuery(BaseModel):
    """
    Input contract for Model B state mismatch prediction.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    stored_state: StateSnapshot
    current_state: StateSnapshot


class ChangedResource(BaseModel):
    """
    Represents a deterministic difference between stored and current state.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    type: ResourceType
    identifier: str = Field(min_length=1)
    change: ResourceChange

    @field_validator("identifier")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Changed-resource identifier cannot be blank."
            )

        return value


class StateMismatchResult(BaseModel):
    """
    Public output contract for Model B.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    mismatch: bool
    probability: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    threshold: float = Field(ge=0.0, le=1.0)

    changed_resources: list[ChangedResource] = Field(
        default_factory=list
    )

    model_version: str = Field(min_length=1)

    @field_validator("model_version")
    @classmethod
    def validate_model_version(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Model version cannot be blank."
            )

        return value