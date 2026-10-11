"""
===============================================================================
File Name   : validation_result.py
Module      : Agent Brain Models
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Defines the standard validation response used throughout the Agent Brain.

Every processing module returns a ValidationResult object instead of
raising exceptions for recoverable validation issues.

Author      : Team Agent
===============================================================================
"""

from typing import List

from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    """
    Represents a single validation issue.
    """

    code: str = Field(
        ...,
        description="Machine-readable validation code."
    )

    message: str = Field(
        ...,
        description="Human-readable validation message."
    )

    field: str | None = Field(
        default=None,
        description="Associated field."
    )

    severity: str = Field(
        default="ERROR",
        description="ERROR or WARNING."
    )


class ValidationResult(BaseModel):
    """
    Standard validation response.
    """

    is_valid: bool = True

    errors: List[ValidationIssue] = Field(
        default_factory=list
    )

    warnings: List[ValidationIssue] = Field(
        default_factory=list
    )

    def add_error(
        self,
        code: str,
        message: str,
        field: str | None = None
    ):

        self.errors.append(

            ValidationIssue(
                code=code,
                message=message,
                field=field,
                severity="ERROR"
            )
        )

        self.is_valid = False

    def add_warning(
        self,
        code: str,
        message: str,
        field: str | None = None
    ):

        self.warnings.append(

            ValidationIssue(
                code=code,
                message=message,
                field=field,
                severity="WARNING"
            )
        )