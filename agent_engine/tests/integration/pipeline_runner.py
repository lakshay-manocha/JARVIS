"""
===============================================================================
File Name   : pipeline_runner.py
Module      : Integration Tests
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Executes the complete Agent Brain pipeline for a given LLM output.

Pipeline:

LLM JSON
    ↓
LLMPlan
    ↓
ProcessingContext
    ↓
Validator
    ↓
Interpreter
    ↓
Graph Builder
    ↓
Planner

Each stage updates the ProcessingContext and the results are displayed using
pipeline_printer.

Author : Team JARVIS
===============================================================================
"""

from __future__ import annotations

from agent_engine.agent_brain.validator import BasicValidator
from agent_engine.agent_brain.interpreter import Interpreter
from agent_engine.agent_brain.graph_builder import GraphBuilder
from agent_engine.agent_brain.planner import Planner

from agent_engine.agent_brain.models.llm_plan import LLMPlan
from agent_engine.agent_brain.models.processing_context import ProcessingContext

from agent_engine.tests.integration.pipeline_printer import (
    print_banner,
    print_graph_validation,
    print_llm_output,
    print_validator,
    print_interpreter,
    print_graph,
    print_planner,
    print_logs,
    print_pipeline_summary,
)


class PipelineRunner:
    """
    Executes the complete Agent Brain pipeline.
    """

    def __init__(self):

        self.validator = BasicValidator()

        self.interpreter = Interpreter()

        self.graph_builder = GraphBuilder()

        self.planner = Planner()

    # ---------------------------------------------------------------------

    def build_context(
        self,
        llm_json: dict
    ) -> ProcessingContext:
        """
        Creates ProcessingContext from raw LLM JSON.
        """

        plan = LLMPlan(**llm_json)

        return ProcessingContext(
            llm_plan=plan
        )

    # ---------------------------------------------------------------------

    def run(
        self,
        llm_json: dict
    ) -> ProcessingContext:
        """
        Runs the complete Agent Brain pipeline.
        """

        print_banner("JARVIS AGENT BRAIN PIPELINE")

        context = self.build_context(llm_json)

        # -----------------------------------------------------------------
        # Raw LLM Output
        # -----------------------------------------------------------------

        print_llm_output(context)

        # -----------------------------------------------------------------
        # Validator
        # -----------------------------------------------------------------

        validation = self.validator.validate(context.llm_plan)

        print_validator(context,validation)

        # -----------------------------------------------------------------
        # Interpreter
        # -----------------------------------------------------------------

        context = self.interpreter.interpret(context)
        print("Interpreted Tasks:", len(context.interpreted_tasks))

        print_interpreter(context)

        # -----------------------------------------------------------------
        # Graph Builder
        # -----------------------------------------------------------------

        context = self.graph_builder.build(context)

        print_graph(context.execution_graph)
        print_graph_validation(context)

        # -----------------------------------------------------------------
        # Planner
        # -----------------------------------------------------------------

        context = self.planner.plan(context)

        print_planner(context.execution_plan,context.execution_graph)

        # -----------------------------------------------------------------
        # Logs
        # -----------------------------------------------------------------

        print_logs(context)

        # -----------------------------------------------------------------
        # Summary
        # -----------------------------------------------------------------

        print_pipeline_summary(context)

        return context