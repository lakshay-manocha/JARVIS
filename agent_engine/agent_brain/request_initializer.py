"""
===============================================================================
File Name   : request_initializer.py
Module      : Agent Brain
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Initializes the ProcessingContext for a validated LLM plan.

This module is responsible for creating the shared execution context that
will be passed through every Agent Brain module.

Responsibilities:
    • Create ProcessingContext
    • Initialize metadata
    • Set initial processing stage
    • Record initialization logs

Author      : Team Agent
===============================================================================
"""

from datetime import datetime
from multiprocessing import context

from agent_engine.agent_brain.models.llm_plan import LLMPlan
from agent_engine.agent_brain.models.processing_context import ProcessingContext
from agent_engine.contracts.enums import ProcessingStage


class RequestInitializer:
    """
    Creates and initializes a ProcessingContext from a validated LLM plan.
    """

    def initialize(self, plan: LLMPlan) -> ProcessingContext:
        """
        Creates a ProcessingContext for the incoming request.

        Parameters
        ----------
        plan : LLMPlan
            Validated execution plan received from the LLM.

        Returns
        -------
        ProcessingContext
            Initialized processing context.
        """

        context = ProcessingContext(
            llm_plan=plan,
            current_stage=ProcessingStage.INITIALIZED
        )

        self._initialize_metadata(context)

        context.log("Processing context initialized.")

        return context

    # ------------------------------------------------------------------

    def _initialize_metadata(
        self,
        context: ProcessingContext
    ) -> None:
        """
        Initializes runtime metadata for the request.
        """

        context.metadata.status = "READY"

        context.metadata.pipeline = "Agent Brain"

        context.metadata.agent_version = "1.0.0"

        context.log("Metadata initialized.")