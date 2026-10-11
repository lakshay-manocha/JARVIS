"""
===============================================================================
File Name   : graph_builder.py
Module      : Agent Brain
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Builds the execution graph from interpreted tasks.

The Graph Builder converts interpreted tasks into an execution DAG by using
the DependencyDetector to determine actual task dependencies.

After constructing the graph, the GraphValidator verifies its structural
integrity before the graph is passed to the Planner.

Responsibilities:
    • Create ExecutionNode objects
    • Detect task dependencies
    • Build dependency edges
    • Validate execution graph integrity
    • Store validation result in ProcessingContext
    • Update processing context

Author : Team JARVIS
===============================================================================
"""

from __future__ import annotations

from agent_engine.agent_brain.models.execution_graph import ExecutionGraph
from agent_engine.agent_brain.models.execution_node import ExecutionNode
from agent_engine.agent_brain.models.processing_context import ProcessingContext
from agent_engine.agent_brain.dependency_detector import DependencyDetector
from agent_engine.agent_brain.graph_validator import GraphValidator
from agent_engine.contracts.enums import ProcessingStage
from agent_engine.agent_brain.dependency_policy import DependencyPolicy


class GraphBuilder:
    """
    Builds and validates an execution graph from interpreted tasks.
    """

    def __init__(self) -> None:

        self.dependency_detector = DependencyDetector()
        self.dependency_policy = DependencyPolicy()
        self.graph_validator = GraphValidator()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(
        self,
        context: ProcessingContext,
    ) -> ProcessingContext:
        """
        Build and validate the execution graph.
        """

        context.current_stage = ProcessingStage.GRAPH_BUILDING

        context.log(
            "Execution graph building started."
        )

        graph = ExecutionGraph()

        tasks = context.interpreted_tasks

        # --------------------------------------------------------------
        # Stage 1: Create execution nodes
        # --------------------------------------------------------------

        for task in tasks:

            node = ExecutionNode(
                node_id=task.task_id,
                task=task,
            )

            graph.add_node(node)

            context.log(
                f"Execution node created for Task "
                f"{task.task_id}."
            )

        # --------------------------------------------------------------
        # Stage 2: Detect dependencies
        # --------------------------------------------------------------

        dependency_checks = 0
        dependency_edges = 0

        for parent_task in tasks:

            for child_task in tasks:

                # ------------------------------------------------------
                # A task cannot depend on itself
                # ------------------------------------------------------

                if (
                    parent_task.task_id
                    == child_task.task_id
                ):
                    continue

                # ------------------------------------------------------
                # Avoid checking the reverse pair separately
                # ------------------------------------------------------

                if (
                    parent_task.task_id
                    >= child_task.task_id
                ):
                    continue

                dependency_checks += 1

                result = self.dependency_detector.detect(
                    parent_task=parent_task,
                    child_task=child_task,
                )

                context.log(
                    f"Dependency check: "
                    f"Task {result.parent_task_id} -> "
                    f"Task {result.child_task_id} | "
                    f"depends_on={result.depends_on} | "
                    f"confidence={result.confidence:.2f} | "
                    f"type={result.dependency_type}"
                )

                if self.dependency_policy.should_create_edge(result):

                    graph.add_dependency(
                        parent_id=result.parent_task_id,
                        child_id=result.child_task_id,
                        dependency_type=result.dependency_type,
                        confidence=result.confidence,
                        reason=result.reason,
                        metadata=result.metadata,
                    )

                    dependency_edges += 1

                    context.log(
                        f"Dependency accepted by policy: "
                        f"Task {result.parent_task_id} -> "
                        f"Task {result.child_task_id} "
                        f"({result.dependency_type}, "
                        f"confidence={result.confidence:.2f})"
                    )

                else:

                    context.log(
                        f"Dependency rejected by policy: "
                        f"Task {result.parent_task_id} -> "
                        f"Task {result.child_task_id} "
                        f"({result.dependency_type}, "
                        f"confidence={result.confidence:.2f})"
                    )
        # --------------------------------------------------------------
        # Stage 3: Recalculate roots and leaves
        # --------------------------------------------------------------

        root_ids, leaf_ids = graph.recalculate_roots_and_leaves()

        context.log(
            f"Root/leaf recalculation completed: "
            f"roots={root_ids} | "
            f"leaves={leaf_ids}"
        )
        # --------------------------------------------------------------
        # Stage 4: Store graph
        # --------------------------------------------------------------

        context.execution_graph = graph

        context.log(
            f"Execution graph created with "
            f"{graph.node_count} node(s) and "
            f"{dependency_edges} dependency edge(s)."
        )

        # --------------------------------------------------------------
        # Stage 5: Validate graph
        # --------------------------------------------------------------

        context.log(
            "Execution graph validation started."
        )

        validation_result = self.graph_validator.validate(
            graph
        )

        context.graph_validation_result = validation_result
        

        context.log(
            f"Graph validation completed: "
            f"valid={validation_result.is_valid} | "
            f"nodes={validation_result.node_count} | "
            f"edges={validation_result.edge_count} | "
            f"errors={validation_result.error_count} | "
            f"warnings={validation_result.warning_count}"
        )
        # --------------------------------------------------------------
        # Stage 5: Execution readiness
        # --------------------------------------------------------------

        execution_ready = (
            validation_result.is_valid
            and graph.is_execution_ready()
        )

        graph.graph_metadata[
            "execution_ready"
        ] = str(execution_ready)

        context.log(
            f"Execution readiness check: "
            f"ready={execution_ready}"
        )

        if execution_ready:

            context.log(
                "Execution graph is ready for Planner."
            )

        else:

            context.log(
                "Execution graph is NOT ready for Planner."
            )

        # --------------------------------------------------------------
        # Validation errors
        # --------------------------------------------------------------

        for error in validation_result.errors:

            context.log(
                f"Graph validation error: {error}"
            )

        # --------------------------------------------------------------
        # Validation warnings
        # --------------------------------------------------------------

        for warning in validation_result.warnings:

            context.log(
                f"Graph validation warning: {warning}"
            )

        # --------------------------------------------------------------
        # Final integrity decision
        # --------------------------------------------------------------

        if validation_result.is_valid:

            context.log(
                "Execution graph passed integrity validation."
            )

        else:

            context.log(
                "Execution graph failed integrity validation."
            )

        return context