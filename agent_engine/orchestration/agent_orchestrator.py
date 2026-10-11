"""
===============================================================================
File Name   : agent_orchestrator.py
Module      : Orchestration
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Coordinates the complete Agent Brain execution pipeline.

The orchestrator connects the existing Agent Brain components in the correct
processing order:

    Validation
        ↓
    Interpretation
        ↓
    Intent Detection
        ↓
    Action Resolution
        ↓
    Parameter Resolution
        ↓
    Tool Resolution
        ↓
    Graph Construction
        ↓
    Planning
        ↓
    Decision Management
        ↓
    Action Dispatch
        ↓
    Automation Engine

The orchestrator coordinates these components but does not take ownership of
their internal responsibilities.

Author      : Team Agent
===============================================================================
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any

# =============================================================================
# Agent Brain
# =============================================================================

from agent_engine.agent_brain.graph_builder import GraphBuilder
from agent_engine.agent_brain.interpreter import Interpreter
from agent_engine.agent_brain.intent_detector import IntentDetector
from agent_engine.agent_brain.action_resolver import ActionResolver
from agent_engine.agent_brain.parameter_resolver import ParameterResolver
from agent_engine.agent_brain.tool_resolver import ToolResolver
from agent_engine.agent_brain.models.llm_plan import LLMPlan
from agent_engine.agent_brain.models.processing_context import ProcessingContext
from agent_engine.agent_brain.planner import Planner
from agent_engine.agent_brain.validator import BasicValidator

# =============================================================================
# Contracts
# =============================================================================

from agent_engine.contracts.enums import (
    ExecutionMode,
    ExecutionStatus,
    ProcessingStage,
    ResultStatus,
    ToolType,
)

from agent_engine.contracts.task import Task

# =============================================================================
# Decision Manager
# =============================================================================

from agent_engine.decision_manager.decision_manager import DecisionManager
from agent_engine.decision_manager.models.decision import (
    DecisionAction,
    DecisionResult,
)
from agent_engine.decision_manager.models.fallback import (
    FallbackOption,
)
from agent_engine.decision_manager.models.execution_outcome import (
    ExecutionOutcome,
    FailureType,
)

# =============================================================================
# Dispatcher
# =============================================================================

from agent_engine.dispatcher.action_dispatcher import ActionDispatcher

# =============================================================================
# Events / Integration / Monitoring
# =============================================================================

from agent_engine.events.event_bus import AgentEvent, EventBus
from agent_engine.integration.decision_state_bridge import DecisionStateBridge
from agent_engine.monitoring.structured_logger import StructuredLogger

# =============================================================================
# Orchestration / State
# =============================================================================

from agent_engine.orchestration.models import OrchestrationResult
from agent_engine.state_manager.state_manager import StateManager
from agent_engine.decision_manager.failure_handler import FailureHandler


class AgentOrchestrator:
    """
    Coordinate the complete Agent Brain pipeline and task execution.

    Existing components remain authoritative:

    * BasicValidator validates the LLM plan.
    * Interpreter normalizes task descriptions.
    * IntentDetector identifies task intent.
    * ActionResolver resolves canonical actions.
    * ParameterResolver extracts structured parameters.
    * ToolResolver selects the automation controller.
    * GraphBuilder constructs and validates the execution DAG.
    * Planner creates execution order and parallel groups.
    * DecisionManager decides the next action after execution attempts.
    * DecisionStateBridge translates decisions into runtime states.
    * StateManager owns runtime state/history/checkpoints.
    * ActionDispatcher is the execution boundary.
    """

    # =========================================================================
    # Initialization
    # =========================================================================

    def __init__(
        self,
        dispatcher: ActionDispatcher,
        *,
        validator: BasicValidator | None = None,
        interpreter: Interpreter | None = None,
        intent_detector: IntentDetector | None = None,
        action_resolver: ActionResolver | None = None,
        parameter_resolver: ParameterResolver | None = None,
        tool_resolver: ToolResolver | None = None,
        graph_builder: GraphBuilder | None = None,
        planner: Planner | None = None,
        decision_manager: DecisionManager | None = None,
        failure_handler: FailureHandler | None = None,
        state_manager: StateManager | None = None,
        decision_state_bridge: DecisionStateBridge | None = None,
        event_bus: EventBus | None = None,
        logger: StructuredLogger | None = None,
        execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL,
        timeout_seconds: float | None = 60.0,
        max_retries: int = 0,
        max_workers: int | None = None,
        fallback_options: dict[int, list[FallbackOption]] | None = None,
    ) -> None:

        if max_retries < 0:
            raise ValueError("max_retries cannot be negative")

        if timeout_seconds is not None and timeout_seconds <= 0:
            raise ValueError(
                "timeout_seconds must be positive or None"
            )

        # ---------------------------------------------------------------------
        # Core dependencies
        # ---------------------------------------------------------------------

        self.dispatcher = dispatcher

        # ---------------------------------------------------------------------
        # Phase A - Validation
        # ---------------------------------------------------------------------

        self.validator = validator or BasicValidator()

        # ---------------------------------------------------------------------
        # Agent Brain semantic processing
        # ---------------------------------------------------------------------

        self.interpreter = interpreter or Interpreter()

        self.intent_detector = (
            intent_detector or IntentDetector()
        )

        self.action_resolver = (
            action_resolver or ActionResolver()
        )

        self.parameter_resolver = (
            parameter_resolver or ParameterResolver()
        )

        self.tool_resolver = (
            tool_resolver or ToolResolver()
        )

        # ---------------------------------------------------------------------
        # Phase B/C - Graph + Planning
        # ---------------------------------------------------------------------

        self.graph_builder = (
            graph_builder or GraphBuilder()
        )

        self.planner = planner or Planner()

        # ---------------------------------------------------------------------
        # Phase D/E - Decision + State
        # ---------------------------------------------------------------------

        self.decision_manager = (
            decision_manager or DecisionManager()
        )

        self.failure_handler = (
            failure_handler or FailureHandler()
        )

        self.state_manager = (
            state_manager or StateManager()
        )

        self.decision_state_bridge = (
            decision_state_bridge
            or DecisionStateBridge(self.state_manager)
        )

        # ---------------------------------------------------------------------
        # Infrastructure
        # ---------------------------------------------------------------------

        self.event_bus = event_bus or EventBus()
        self.logger = logger or StructuredLogger()

        # ---------------------------------------------------------------------
        # Execution configuration
        # ---------------------------------------------------------------------

        self.execution_mode = execution_mode
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.max_workers = max_workers
        self.fallback_options = fallback_options or {}

        # ---------------------------------------------------------------------
        # State Manager consistency
        # ---------------------------------------------------------------------

        if (
            self.decision_state_bridge.state_manager
            is not self.state_manager
        ):
            raise ValueError(
                "DecisionStateBridge must use the orchestrator's StateManager"
            )

    # =========================================================================
    # Public API
    # =========================================================================

    def run(
        self,
        source: dict[str, Any] | LLMPlan | ProcessingContext,
    ) -> OrchestrationResult:
        """
        Run one request through the complete Agent Brain pipeline and execute
        the resulting tasks.
        """

        # ---------------------------------------------------------------------
        # Build processing context
        # ---------------------------------------------------------------------

        context = self._build_context(source)
        request_id = context.request_id

        self._emit(
            "request.started",
            request_id,
            payload={
                "goal": context.llm_plan.goal
            },
        )

        self.logger.info(
            "request.started",
            request_id=request_id,
            goal=context.llm_plan.goal,
        )

        # ---------------------------------------------------------------------
        # Phase A - Validation
        # ---------------------------------------------------------------------

        validation = self.validator.validate(
            context.llm_plan
        )

        if not validation.is_valid:
            return self._fail_result(
                context,
                validation,
                "LLM plan validation failed.",
            )

        try:

            # ================================================================
            # Agent Brain semantic processing
            # ================================================================

            # ----------------------------------------------------------------
            # Interpreter
            # ----------------------------------------------------------------

            context = self.interpreter.interpret(context)

            # ----------------------------------------------------------------
            # Intent Detector
            # ----------------------------------------------------------------

            context = self.intent_detector.detect(context)

            # ----------------------------------------------------------------
            # Action Resolver
            # ----------------------------------------------------------------

            context = self.action_resolver.resolve(context)

            # ----------------------------------------------------------------
            # Parameter Resolver
            # ----------------------------------------------------------------

            context = self.parameter_resolver.resolve(context)

            # ----------------------------------------------------------------
            # Tool Resolver
            # ----------------------------------------------------------------

            context = self.tool_resolver.resolve(context)

            # ================================================================
            # Phase B - Graph Construction
            # ================================================================

            context = self.graph_builder.build(context)

            if (
                context.graph_validation_result is None
                or not context.graph_validation_result.is_valid
            ):
                return self._fail_result(
                    context,
                    validation,
                    "Execution graph validation failed.",
                )

            # ================================================================
            # Phase C - Planning
            # ================================================================

            context = self.planner.plan(context)

            planning = context.execution_plan

            if planning is None or not planning.is_valid:
                return self._fail_result(
                    context,
                    validation,
                    "Execution planning failed.",
                    planning_result=planning,
                )

            # ----------------------------------------------------------------
            # Register tasks with State Manager
            # ----------------------------------------------------------------

            self.state_manager.register_tasks(
                list(planning.execution_order)
            )

            outcomes: list[ExecutionOutcome] = []
            decisions: list[DecisionResult] = []

            groups = (
                planning.parallel_groups
                or [
                    [task_id]
                    for task_id in planning.execution_order
                ]
            )

            # ================================================================
            # Phase F - Execution
            # ================================================================

            for group in groups:

                self._execute_group(
                    context,
                    group,
                    outcomes,
                    decisions,
                    parallel=(
                        self.execution_mode
                        == ExecutionMode.PARALLEL
                    ),
                )

            # ----------------------------------------------------------------
            # Request completed
            # ----------------------------------------------------------------

            context.current_stage = ProcessingStage.COMPLETED

            context.log(
                "Agent Orchestrator execution completed."
            )

            self._emit(
                "request.completed",
                request_id,
                payload={
                    "task_count": len(
                        planning.execution_order
                    )
                },
            )

            self.logger.info(
                "request.completed",
                request_id=request_id,
                task_count=len(
                    planning.execution_order
                ),
            )

            status = self._final_result_status(
                planning.execution_order
            )

            return OrchestrationResult(
                request_id=request_id,
                status=status,
                context=context,
                validation=validation,
                planning_result=planning,
                outcomes=outcomes,
                decisions=decisions,
            )

        # ---------------------------------------------------------------------
        # Unexpected orchestration failure
        # ---------------------------------------------------------------------

        except Exception as exc:

            context.current_stage = ProcessingStage.FAILED

            context.log(
                f"Orchestration failed: {exc}"
            )

            self._emit(
                "request.failed",
                request_id,
                payload={
                    "error": str(exc)
                },
            )

            self.logger.error(
                "request.failed",
                request_id=request_id,
                error=str(exc),
            )

            return OrchestrationResult(
                request_id=request_id,
                status=ResultStatus.FAILED,
                context=context,
                validation=validation,
                planning_result=context.execution_plan,
                error=str(exc),
            )

    # =========================================================================
    # Pipeline preparation
    # =========================================================================

    @staticmethod
    def _build_context(
        source: dict[str, Any] | LLMPlan | ProcessingContext,
    ) -> ProcessingContext:
        """
        Convert supported input formats into ProcessingContext.
        """

        if isinstance(source, ProcessingContext):
            return source

        if isinstance(source, LLMPlan):
            return ProcessingContext(
                llm_plan=source
            )

        if isinstance(source, dict):
            return ProcessingContext(
                llm_plan=LLMPlan(**source)
            )

        raise TypeError(
            "source must be a dict, LLMPlan, or ProcessingContext"
        )

    # =========================================================================
    # Group execution
    # =========================================================================

    def _execute_group(
        self,
        context: ProcessingContext,
        task_ids: list[int],
        outcomes: list[ExecutionOutcome],
        decisions: list[DecisionResult],
        *,
        parallel: bool,
    ) -> bool:

        if parallel and len(task_ids) > 1:

            workers = (
                self.max_workers
                or len(task_ids)
            )

            with ThreadPoolExecutor(
                max_workers=workers
            ) as executor:

                futures = {
                    executor.submit(
                        self._execute_task,
                        context,
                        task_id,
                    ): task_id
                    for task_id in task_ids
                }

                results = []

                for future in as_completed(futures):
                    results.append(
                        future.result()
                    )

        else:

            results = [
                self._execute_task(
                    context,
                    task_id,
                )
                for task_id in task_ids
            ]

        for (
            task_outcomes,
            task_decisions,
            success,
        ) in results:

            outcomes.extend(
                task_outcomes
            )

            decisions.extend(
                task_decisions
            )

        return all(
            result[2]
            for result in results
        )

    # =========================================================================
    # Single task execution
    # =========================================================================

    def _execute_task(
        self,
        context: ProcessingContext,
        task_id: int,
    ) -> tuple[
        list[ExecutionOutcome],
        list[DecisionResult],
        bool,
    ]:

        node = context.execution_graph.get_node(
            task_id
        )

        if node is None:
            raise KeyError(
                f"Execution node {task_id} not found"
            )

        outcomes: list[ExecutionOutcome] = []
        decisions: list[DecisionResult] = []

        # ---------------------------------------------------------------------
        # Dependency evaluation
        # ---------------------------------------------------------------------

        dependency_task = (
            self._build_dependency_task(node)
        )

        task_states = {
            registered_id:
                self.state_manager.get_status(
                    registered_id
                )
            for registered_id
            in self.state_manager.task_ids()
        }

        dependency_decision = (
            self.decision_manager.evaluate_dependencies(
                dependency_task,
                task_states,
                attempt=1,
            )
        )

        if (
            dependency_decision.action
            == DecisionAction.SKIP
        ):

            # PENDING -> READY
            self.state_manager.set_state(
                task_id,
                ExecutionStatus.READY,
            )

            # READY -> SKIPPED
            self.decision_state_bridge.apply_decision(
                dependency_decision
            )

            decisions.append(
                dependency_decision
            )

            self._emit(
                "task.skipped",
                context.request_id,
                task_id=task_id,
                payload={
                    "reason":
                        dependency_decision.reason
                },
            )

            return (
                outcomes,
                decisions,
                True,
            )

        # ---------------------------------------------------------------------
        # Task ready
        # ---------------------------------------------------------------------

        self.state_manager.set_state(
            task_id,
            ExecutionStatus.READY,
        )

        self._emit(
            "task.ready",
            context.request_id,
            task_id=task_id,
        )

        # ---------------------------------------------------------------------
        # Attempt loop
        # ---------------------------------------------------------------------

        attempt = 1

        while True:

            self.state_manager.set_state(
                task_id,
                ExecutionStatus.RUNNING,
            )

            state = (
                self.state_manager.get_state(
                    task_id
                )
            )

            if state.started_at is None:
                state.started_at = (
                    datetime.now(timezone.utc)
                )

            self._emit(
                "task.started",
                context.request_id,
                task_id=task_id,
                payload={
                    "attempt": attempt
                },
            )

            started = datetime.now(
                timezone.utc
            )

            try:

                outcome = self.dispatcher.dispatch(
                    node.task,
                    attempt=attempt,
                    timeout_seconds=self.timeout_seconds,
                )

                outcome = self._normalize_outcome(
                    outcome,
                    task_id,
                    attempt,
                )

            except Exception as exc:

                execution_time = (
                    datetime.now(
                        timezone.utc
                    ) - started
                ).total_seconds()

                outcome = self.failure_handler.handle_exception(
                    exception=exc,
                    task_id=task_id,
                    attempt=attempt,
                    retry_count=attempt - 1,
                    max_retries=self.max_retries,
                    timeout_seconds=self.timeout_seconds,
                    execution_time=execution_time,
                )
            # -----------------------------------------------------------------
            # Record outcome
            # -----------------------------------------------------------------

            outcomes.append(outcome)

            decision = (
                self.decision_manager.decide(
                    outcome
                )
            )

            # -------------------------------------------------------------
            # Fallback evaluation
            # -------------------------------------------------------------
            #
            # DecisionManager first evaluates the normal execution result.
            # Fallback is considered only when the normal decision reaches
            # FAIL. The fallback itself is NOT executed here.
            #

            if decision.action == DecisionAction.FAIL:

                task_fallbacks = (
                    self.fallback_options.get(
                        task_id,
                        [],
                    )
                )

                if task_fallbacks:

                    fallback_decision = (
                        self.decision_manager.evaluate_fallback(
                            task=self._build_dependency_task(node),
                            fallback_options=task_fallbacks,
                            attempt=attempt,
                        )
                    )

                    if (
                        fallback_decision.action
                        == DecisionAction.FALLBACK
                    ):
                        decision = fallback_decision

            decisions.append(decision)

            self._emit(
                "task.decision",
                context.request_id,
                task_id=task_id,
                payload={
                    "action":
                        decision.action.value,
                    "attempt":
                        attempt,
                    "reason":
                        decision.reason,
                },
            )

            self._update_runtime_fields(
                task_id,
                outcome,
            )

            # -----------------------------------------------------------------
            # Failed attempt -> FAILED state
            # -----------------------------------------------------------------

            if (
                not outcome.success
                and self.state_manager.get_status(
                    task_id
                )
                == ExecutionStatus.RUNNING
            ):

                self.state_manager.set_state(
                    task_id,
                    ExecutionStatus.FAILED,
                )

            # -----------------------------------------------------------------
            # Apply DecisionManager decision
            # -----------------------------------------------------------------

            self.decision_state_bridge.apply_decision(
                decision
            )

            # -----------------------------------------------------------------
            # COMPLETE
            # -----------------------------------------------------------------

            if (
                decision.action
                == DecisionAction.COMPLETE
            ):

                self.state_manager.update_state(
                    task_id,
                    progress=100.0,
                    completed_at=(
                        datetime.now(
                            timezone.utc
                        )
                    ),
                    execution_time=(
                        outcome.execution_time
                    ),
                )

                self._emit(
                    "task.completed",
                    context.request_id,
                    task_id=task_id,
                )

                return (
                    outcomes,
                    decisions,
                    True,
                )

            # -----------------------------------------------------------------
            # RETRY
            # -----------------------------------------------------------------

            if (
                decision.action
                == DecisionAction.RETRY
            ):

                self.state_manager.update_state(
                    task_id,
                    retry_count=attempt,
                )

                attempt += 1

                self.state_manager.set_state(
                    task_id,
                    ExecutionStatus.RUNNING,
                )

                self._emit(
                    "task.retrying",
                    context.request_id,
                    task_id=task_id,
                    payload={
                        "attempt": attempt
                    },
                )

                continue

            # -----------------------------------------------------------------
            # FALLBACK
            # -----------------------------------------------------------------

            if (
                decision.action
                == DecisionAction.FALLBACK
            ):

                self._emit(
                    "task.fallback",
                    context.request_id,
                    task_id=task_id,
                    payload={
                        "action":
                            decision.action.value,
                        "reason":
                            decision.reason,
                        "selected_fallback":
                            decision.selected_fallback,
                    },
                )

                # -------------------------------------------------------------
                # IMPORTANT:
                # -------------------------------------------------------------
                # The fallback is selected, but NOT executed here.
                #
                # DecisionManager decides.
                # DecisionStateBridge updates runtime state.
                # Actual fallback execution belongs to the automation layer.
                # -------------------------------------------------------------

                return (
                    outcomes,
                    decisions,
                    False,
                )

            # -----------------------------------------------------------------
            # FAIL / SKIP / ABORT
            # -----------------------------------------------------------------

            self._emit(
                "task.failed",
                context.request_id,
                task_id=task_id,
                payload={
                    "action":
                        decision.action.value,
                    "reason":
                        decision.reason,
                },
            )

            return (
                outcomes,
                decisions,
                False,
            )
    # =========================================================================
    # Dependency adapter
    # =========================================================================

    @staticmethod
    def _build_dependency_task(node) -> Task:
        """
        Adapt an ExecutionNode into the narrow Phase D dependency contract.

        The DecisionManager's dependency/skip policy expects the contracts.Task
        model, while Phase C currently works with InterpretedTask objects.

        Only the fields required by the dependency policy are adapted here.
        """

        try:

            tool = (
                ToolType(node.task.tool)
                if node.task.tool
                else ToolType.DESKTOP
            )

        except ValueError:

            tool = ToolType.DESKTOP

        return Task(
            id=node.node_id,
            description=node.task.original_text,
            action=node.task.action or "UNKNOWN",
            tool=tool,
            parameters=dict(
                node.task.parameters
            ),
            depends_on=list(
                node.parents
            ),
            retry=0,
        )

    # =========================================================================
    # Outcome normalization
    # =========================================================================

    def _normalize_outcome(
        self,
        outcome: ExecutionOutcome,
        task_id: int,
        attempt: int,
    ) -> ExecutionOutcome:
        """
        Normalize dispatcher output so the orchestrator owns attempt
        numbering and retry configuration.
        """

        if not isinstance(
            outcome,
            ExecutionOutcome,
        ):
            raise TypeError(
                "ActionDispatcher.dispatch() must return ExecutionOutcome"
            )

        if outcome.task_id != task_id:
            raise ValueError(
                f"Dispatcher returned outcome for task "
                f"{outcome.task_id}; expected {task_id}"
            )

        data = outcome.model_dump()

        data["attempt"] = attempt

        data["retry_count"] = max(
            attempt - 1,
            0,
        )

        if self.max_retries >= 0:
            data["max_retries"] = (
                self.max_retries
            )

        return ExecutionOutcome(
            **data
        )

    # =========================================================================
    # Runtime state updates
    # =========================================================================

    def _update_runtime_fields(
        self,
        task_id: int,
        outcome: ExecutionOutcome,
    ) -> None:

        updates: dict[str, Any] = {}

        if outcome.execution_time is not None:
            updates["execution_time"] = (
                outcome.execution_time
            )

        if outcome.error_message:
            updates["error_message"] = (
                outcome.error_message
            )

        if updates:
            self.state_manager.update_state(
                task_id,
                **updates,
            )

    # =========================================================================
    # Event helper
    # =========================================================================

    def _emit(
        self,
        name: str,
        request_id: str,
        *,
        task_id: int | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:

        self.event_bus.publish(
            AgentEvent(
                name=name,
                request_id=request_id,
                task_id=task_id,
                payload=payload or {},
            )
        )

    # =========================================================================
    # Final result status
    # =========================================================================

    def _final_result_status(
        self,
        task_ids: list[int],
    ) -> ResultStatus:

        statuses = [
            self.state_manager.get_status(
                task_id
            )
            for task_id in task_ids
        ]

        if statuses and all(
            status
            in {
                ExecutionStatus.COMPLETED,
                ExecutionStatus.SKIPPED,
            }
            for status in statuses
        ):

            if any(
                status == ExecutionStatus.SKIPPED
                for status in statuses
            ):
                return ResultStatus.PARTIAL_SUCCESS

            return ResultStatus.SUCCESS

        return ResultStatus.FAILED

    # =========================================================================
    # Failure result helper
    # =========================================================================

    def _fail_result(
        self,
        context: ProcessingContext,
        validation,
        error: str,
        planning_result=None,
    ) -> OrchestrationResult:

        context.current_stage = (
            ProcessingStage.FAILED
        )

        context.log(error)

        self._emit(
            "request.failed",
            context.request_id,
            payload={
                "error": error
            },
        )

        self.logger.error(
            "request.failed",
            request_id=context.request_id,
            error=error,
        )

        return OrchestrationResult(
            request_id=context.request_id,
            status=ResultStatus.FAILED,
            context=context,
            validation=validation,
            planning_result=planning_result,
            error=error,
        )
