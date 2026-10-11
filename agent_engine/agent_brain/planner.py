"""
===============================================================================
File Name   : planner.py
Module      : Agent Brain
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Creates the final execution plan from the generated execution graph.

The Planner validates the graph, determines the dependency-aware execution
order, identifies parallel execution groups, creates a PlanningResult object,
and attaches it to the ProcessingContext.

The initial implementation is intentionally rule-based. Future versions can
replace the planning strategy with AI/ML scheduling models without changing
the public interface.

Responsibilities:
    • Validate execution graph
    • Generate dependency-aware execution order
    • Generate dependency-based parallel groups
    • Estimate execution statistics
    • Create PlanningResult
    • Update ProcessingContext
    • Record processing logs

Author : Team JARVIS
===============================================================================
"""

from agent_engine.agent_brain.models.execution_graph import ExecutionGraph
from agent_engine.agent_brain.models.planning_result import PlanningResult
from agent_engine.agent_brain.models.processing_context import ProcessingContext
from agent_engine.contracts.enums import ProcessingStage
from agent_engine.agent_brain.execution_estimator import ExecutionEstimator


class Planner:
    """
    Builds the final execution plan from the execution graph.
    """
    def __init__(self):
        self.execution_estimator = ExecutionEstimator()

    def plan(
        self,
        context: ProcessingContext
    ) -> ProcessingContext:
        """
        Generates an execution plan.

        Parameters
        ----------
        context : ProcessingContext

        Returns
        -------
        ProcessingContext
        """

        context.current_stage = ProcessingStage.PLANNING

        context.log("Planning started.")

        graph = context.execution_graph

        planning_result = self._create_plan(graph)

        context.execution_plan = planning_result

        context.log(
            f"Execution plan created with "
            f"{planning_result.total_steps} step(s)."
        )

        context.log("Planning completed.")

        return context

    # ------------------------------------------------------------------
    # Plan Creation
    # ------------------------------------------------------------------

    def _create_plan(
        self,
        graph: ExecutionGraph
    ) -> PlanningResult:
        """
        Creates a dependency-aware PlanningResult from an ExecutionGraph.

        The Planner uses topological scheduling so that every parent
        dependency is scheduled before its child.

        After generating the topological order, dependency-based parallel
        groups are generated.

        The original ExecutionGraph is never modified during planning.
        """

        # --------------------------------------------------------------
        # Graph availability
        # --------------------------------------------------------------

        if graph is None:

            return PlanningResult(
                graph=ExecutionGraph(),
                is_valid=False,
                execution_order=[],
                parallel_groups=[],
                total_steps=0,
                estimated_time=0,
                planning_notes=[
                    "Execution graph not available."
                ]
            )

        # --------------------------------------------------------------
        # Graph readiness
        # --------------------------------------------------------------

        if not graph.is_execution_ready():

            return PlanningResult(
                graph=graph,
                is_valid=False,
                execution_order=[],
                parallel_groups=[],
                total_steps=0,
                estimated_time=0,
                planning_notes=[
                    "Execution graph is not ready for planning."
                ]
            )

        # --------------------------------------------------------------
        # Dependency-aware topological scheduling
        # --------------------------------------------------------------

        execution_order = self._topological_sort(graph)

        # --------------------------------------------------------------
        # Cycle / impossible schedule protection
        # --------------------------------------------------------------

        if len(execution_order) != graph.node_count:

            return PlanningResult(
                graph=graph,
                is_valid=False,
                execution_order=[],
                parallel_groups=[],
                total_steps=0,
                estimated_time=0,
                planning_notes=[
                    "Unable to create a complete topological execution "
                    "order. The graph may contain a cycle or unresolved "
                    "dependency."
                ]
            )
                # --------------------------------------------------------------
        # C-2: Dependency-based parallel grouping
        # --------------------------------------------------------------

        parallel_groups = self._build_parallel_groups(
            graph,
            execution_order
        )

        # --------------------------------------------------------------
        # C-5: Estimate individual node durations
        # --------------------------------------------------------------

        self._estimate_node_durations(graph)

        # --------------------------------------------------------------
        # C-5: Calculate total execution time
        # --------------------------------------------------------------

        estimated_time = self._calculate_estimated_time(
            graph,
            parallel_groups
        )

        # --------------------------------------------------------------
        # Successful planning
        # --------------------------------------------------------------

        return PlanningResult(
            graph=graph,
            is_valid=True,
            execution_order=execution_order,
            parallel_groups=parallel_groups,
            total_steps=len(execution_order),
            estimated_time=estimated_time,
            planning_notes=[
                "Dependency-aware topological planning.",
                "Parallel groups generated from dependency levels.",
                "Execution time estimated using task-level durations."
            ]
        )
    # ------------------------------------------------------------------
    # C-5: Execution-Time Estimation
    # ------------------------------------------------------------------

    def _estimate_node_durations(
        self,
        graph: ExecutionGraph
    ) -> None:
        """
        Estimates the execution duration of every ExecutionNode.

        The ExecutionEstimator receives the complete ExecutionNode,
        because the estimator resolves the action through:

            node.task.action
        """

        for node in graph.nodes.values():

            node.estimated_duration = (
                self.execution_estimator.estimate(node)
            )

    def _calculate_estimated_time(
        self,
        graph: ExecutionGraph,
        parallel_groups: list[list[int]]
    ) -> float:
        """
        Calculates total estimated execution time.

        Tasks in the same parallel group execute concurrently, therefore
        the maximum duration within the group determines that group's
        execution time.

        Dependency levels execute sequentially, therefore group durations
        are summed.
        """

        total_time = 0.0

        for group in parallel_groups:

            group_durations = [
                graph.nodes[node_id].estimated_duration
                for node_id in group
                if (
                    node_id in graph.nodes
                    and graph.nodes[node_id].estimated_duration
                    is not None
                )
            ]

            if group_durations:
                total_time += max(group_durations)

        return total_time
    # ------------------------------------------------------------------
    # Execution-Time Estimation
    # ------------------------------------------------------------------

    def _estimate_execution_times(
        self,
        graph: ExecutionGraph
    ) -> None:
        """
        Estimates execution duration for every node in the graph.

        The graph structure itself is not modified. Only the planning
        metadata field `estimated_duration` on each ExecutionNode is
        populated.
        """

        for node in graph.nodes.values():

            node.estimated_duration = (
                self.execution_estimator.estimate(node)
            )

    # ------------------------------------------------------------------
    # Topological Scheduling
    # ------------------------------------------------------------------

    def _topological_sort(
        self,
        graph: ExecutionGraph
    ) -> list[int]:
        """
        Produces a deterministic, priority-aware topological execution
        order.

        Each node is scheduled only after all of its parent dependencies
        have been scheduled.

        When multiple nodes are ready at the same time, the node with
        the highest priority is selected first.

        If multiple ready nodes have the same priority, the node with
        the smallest node_id is selected first.

        Priority never overrides dependency constraints.

        The graph itself is never modified. A temporary dependency-count
        dictionary is used to track unresolved dependencies.
        """

        # --------------------------------------------------------------
        # Create temporary dependency counts.
        #
        # The actual node.parents lists must never be modified because
        # they represent the real ExecutionGraph structure.
        # --------------------------------------------------------------

        remaining_dependencies = {
            node.node_id: len(node.parents)
            for node in graph.nodes.values()
        }

        # --------------------------------------------------------------
        # Initial ready nodes
        # --------------------------------------------------------------

        ready_nodes = [
            node_id
            for node_id, dependency_count
            in remaining_dependencies.items()
            if dependency_count == 0
        ]

        execution_order = []

        # --------------------------------------------------------------
        # Priority-aware Kahn's topological sorting algorithm
        # --------------------------------------------------------------

        while ready_nodes:

            # ----------------------------------------------------------
            # Select the highest-priority ready node.
            #
            # For equal priorities, select the smallest node_id.
            # ----------------------------------------------------------

            ready_nodes.sort(
                key=lambda node_id: (
                    -self._priority_rank(
                        graph.get_node(node_id)
                    ),
                    node_id
                )
            )

            current_node_id = ready_nodes.pop(0)

            current_node = graph.get_node(current_node_id)

            if current_node is None:
                continue

            execution_order.append(current_node_id)

            # ----------------------------------------------------------
            # Resolve the current node's child dependencies.
            # ----------------------------------------------------------

            for child_id in sorted(current_node.children):

                if child_id not in remaining_dependencies:
                    continue

                remaining_dependencies[child_id] -= 1

                # ------------------------------------------------------
                # Child becomes ready only when every parent has been
                # scheduled.
                # ------------------------------------------------------

                if remaining_dependencies[child_id] == 0:

                    ready_nodes.append(child_id)

        return execution_order
    # ------------------------------------------------------------------
    # Priority Ranking
    # ------------------------------------------------------------------

    def _priority_rank(self, node) -> int:
        """
        Returns the scheduling rank of an execution node.

        Higher rank means higher execution priority.

        Priority order:
            CRITICAL > HIGH > MEDIUM > LOW
        """

        priority_ranks = {
            "CRITICAL": 4,
            "HIGH": 3,
            "MEDIUM": 2,
            "LOW": 1,
        }

        return priority_ranks.get(
            node.priority.value,
            0
        )

    # ------------------------------------------------------------------
    # C-2 Parallel Grouping
    # ------------------------------------------------------------------

    def _build_parallel_groups(
        self,
        graph: ExecutionGraph,
        execution_order: list[int]
    ) -> list[list[int]]:
        """
        Builds dependency-based parallel execution groups.

        Nodes are assigned to dependency levels.

        A node with no parents belongs to level 0.

        A node with dependencies belongs to one level after the highest
        level of its parents.

        The execution_order contains node IDs, while the graph contains
        the complete ExecutionNode objects.

        The original graph is never modified.
        """

        # --------------------------------------------------------------
        # Store the dependency level of every node.
        # --------------------------------------------------------------

        node_levels = {}

        # --------------------------------------------------------------
        # Process nodes in topological execution order.
        # --------------------------------------------------------------

        for node_id in execution_order:

            node = graph.get_node(node_id)

            if node is None:
                continue

            # ----------------------------------------------------------
            # Root node
            # ----------------------------------------------------------

            if not node.parents:

                node_levels[node_id] = 0
                continue

            # ----------------------------------------------------------
            # Determine the highest dependency level among parents.
            # ----------------------------------------------------------

            parent_levels = [
                node_levels[parent_id]
                for parent_id in node.parents
                if parent_id in node_levels
            ]

            if not parent_levels:

                # Defensive fallback.
                node_levels[node_id] = 0

            else:

                node_levels[node_id] = (
                    max(parent_levels) + 1
                )

        # --------------------------------------------------------------
        # Convert levels into parallel groups.
        # --------------------------------------------------------------

        grouped_nodes = {}

        for node_id in execution_order:

            if node_id not in node_levels:
                continue

            level = node_levels[node_id]

            grouped_nodes.setdefault(
                level,
                []
            ).append(node_id)

        # --------------------------------------------------------------
        # Keep groups ordered by dependency level.
        #
        # IMPORTANT:
        # Nodes inside groups are sorted by node_id so that C-2
        # deterministic grouping remains independent of C-3 priority
        # scheduling.
        # --------------------------------------------------------------

        parallel_groups = [
            sorted(grouped_nodes[level])
            for level in sorted(grouped_nodes)
        ]

        return parallel_groups