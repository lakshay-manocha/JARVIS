"""
===============================================================================
File Name   : action_dispatcher.py
Module      : Automation Engine - Dispatcher
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Concrete implementation of the Automation Engine action dispatcher.

The dispatcher forms the execution boundary between the Agent Engine and
registered Automation Engine agents.

Responsibilities:
    - Receive an InterpretedTask
    - Build an ActionRequest
    - Resolve the responsible AutomationAgent
    - Validate agent capability
    - Delegate execution
    - Convert AutomationExecutionResult into ExecutionOutcome
    - Preserve backward compatibility with ActionRegistry

The dispatcher does NOT:
    - decide retry
    - decide fallback
    - manage task state
    - modify StateManager state
    - implement actual browser/desktop/filesystem automation

Author : Team Automation
===============================================================================
"""

from __future__ import annotations

from time import perf_counter

from agent_engine.agent_brain.models.interpreted_task import (
    InterpretedTask,
)
from agent_engine.automation.exceptions import (
    AgentCapabilityError,
)
from agent_engine.automation.integration.action_request_builder import (
    ActionRequestBuilder,
)
from agent_engine.automation.integration.execution_result_integrator import (
    ExecutionResultIntegrator,
)
from agent_engine.automation.models.execution_result import (
    AutomationExecutionResult,
)
from agent_engine.automation.registry.action_registry import (
    ActionRegistry,
)
from agent_engine.automation.registry.tool_agent_mapper import (
    ToolAgentMapper,
)
from agent_engine.contracts.enums import (
    ExecutionStatus,
)
from agent_engine.decision_manager.models.execution_outcome import (
    ExecutionOutcome,
    FailureType,
)


class AutomationActionDispatcher:
    """
    Concrete dispatcher for the Automation Engine.

    Execution flow:

        InterpretedTask
              ↓
        ActionRequestBuilder
              ↓
        ActionRequest
              ↓
        ToolAgentMapper
              ↓
        AutomationAgent
              ↓
        can_execute()
              ↓
        execute()
              ↓
        AutomationExecutionResult
              ↓
        ExecutionResultIntegrator
              ↓
        ExecutionOutcome

    When no ToolAgentMapper is supplied, the existing ActionRegistry
    execution path remains available for backward compatibility.
    """

    def __init__(
        self,
        registry: ActionRegistry,
        *,
        request_builder: ActionRequestBuilder | None = None,
        tool_agent_mapper: ToolAgentMapper | None = None,
        result_integrator: ExecutionResultIntegrator | None = None,
    ) -> None:
        """
        Initialize the dispatcher.

        Args:
            registry:
                Existing Automation Engine action registry.

            request_builder:
                Converts InterpretedTask into ActionRequest.

            tool_agent_mapper:
                Resolves ToolType into AutomationAgent.

            result_integrator:
                Converts AutomationExecutionResult into ExecutionOutcome.
        """

        if not isinstance(
            registry,
            ActionRegistry,
        ):
            raise TypeError(
                "registry must be an ActionRegistry."
            )

        if request_builder is not None and not isinstance(
            request_builder,
            ActionRequestBuilder,
        ):
            raise TypeError(
                "request_builder must be an ActionRequestBuilder."
            )

        if tool_agent_mapper is not None and not isinstance(
            tool_agent_mapper,
            ToolAgentMapper,
        ):
            raise TypeError(
                "tool_agent_mapper must be a ToolAgentMapper."
            )

        if result_integrator is not None and not isinstance(
            result_integrator,
            ExecutionResultIntegrator,
        ):
            raise TypeError(
                "result_integrator must be an ExecutionResultIntegrator."
            )

        self._registry = registry

        self._request_builder = (
            request_builder
            or ActionRequestBuilder()
        )

        self._tool_agent_mapper = (
            tool_agent_mapper
        )

        self._result_integrator = (
            result_integrator
            or ExecutionResultIntegrator()
        )

    # -------------------------------------------------------------------------
    # Dispatch API
    # -------------------------------------------------------------------------

    def dispatch(
        self,
        task: InterpretedTask,
        *,
        attempt: int,
        timeout_seconds: float | None = None,
    ) -> ExecutionOutcome:
        """
        Dispatch one task for execution.

        When a ToolAgentMapper is configured, execution is delegated to an
        AutomationAgent and its AutomationExecutionResult is converted to an
        ExecutionOutcome through the G.11 integrator.

        Without a ToolAgentMapper, the legacy ActionRegistry execution path
        remains active.
        """

        start_time = perf_counter()

        try:
            request = self._request_builder.build(
                task,
                timeout_seconds=timeout_seconds,
            )

            # =================================================================
            # AutomationAgent Execution Path
            # =================================================================

            if self._tool_agent_mapper is not None:

                agent = self._tool_agent_mapper.resolve(
                    request.tool
                )

                if not agent.can_execute(
                    request
                ):
                    raise AgentCapabilityError(
                        f"Agent '{agent.agent_id}' cannot execute "
                        f"action '{request.action}'."
                    )

                automation_result = agent.execute(
                    request
                )

                if not isinstance(
                    automation_result,
                    AutomationExecutionResult,
                ):
                    raise TypeError(
                        "AutomationAgent.execute() must return "
                        "AutomationExecutionResult."
                    )

                return self._result_integrator.integrate(
                    automation_result,
                    attempt=attempt,
                    timeout_seconds=request.timeout_seconds,
                )

            # =================================================================
            # Existing ActionRegistry Execution Path
            # =================================================================

            handler = self._registry.resolve(
                request.action
            )

            handler(
                **request.parameters
            )

            execution_time = (
                perf_counter()
                - start_time
            )

            return ExecutionOutcome(
                task_id=request.task_id,
                status=ExecutionStatus.COMPLETED,
                success=True,
                attempt=attempt,
                retry_count=max(
                    attempt - 1,
                    0,
                ),
                max_retries=0,
                timeout_seconds=request.timeout_seconds,
                execution_time=execution_time,
                timed_out=False,
                failure_type=FailureType.NONE,
                error_message=None,
            )

        except Exception as exc:

            execution_time = (
                perf_counter()
                - start_time
            )

            return ExecutionOutcome(
                task_id=task.task_id,
                status=ExecutionStatus.FAILED,
                success=False,
                attempt=attempt,
                retry_count=max(
                    attempt - 1,
                    0,
                ),
                max_retries=0,
                timeout_seconds=timeout_seconds,
                execution_time=execution_time,
                timed_out=False,
                failure_type=self._classify_failure(
                    exc
                ),
                error_message=str(exc),
            )

    # -------------------------------------------------------------------------
    # Failure Classification
    # -------------------------------------------------------------------------

    @staticmethod
    def _classify_failure(
        exception: Exception,
    ) -> FailureType:
        """
        Classify dispatcher-level failures.

        The dispatcher only classifies failures that prevent normal
        agent-result integration. It does not make retry/fallback decisions.
        """

        if isinstance(
            exception,
            (
                ValueError,
                TypeError,
                AgentCapabilityError,
            ),
        ):
            return FailureType.VALIDATION

        if isinstance(
            exception,
            KeyError,
        ):
            return FailureType.UNKNOWN

        return FailureType.UNKNOWN