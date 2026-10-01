"""
===============================================================================
File Name   : real_automation_demo.py
Module      : JARVIS - Real Automation Demonstration
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
End-to-end real automation demonstration for the current JARVIS pipeline.

Demonstrates:

    Demo Scenario
          ↓
    Interpreted Tasks
          ↓
    ActionRequest
          ↓
    ToolAgentMapper
          ↓
    Real Automation Agents
          ↓
    Browser / Keyboard / Mouse
          ↓
    ExecutionOutcome

Current real agents:

    BrowserAutomationAgent
    KeyboardAutomationAgent
    MouseAutomationAgent

DesktopAutomationAgent is intentionally NOT used because it has not yet
been implemented.

The demonstration uses the real Browser, Keyboard and Mouse backends.

Author : Team JARVIS
===============================================================================
"""

from __future__ import annotations

import time

from agent_engine.agent_brain.models.interpreted_task import (
    InterpretedTask,
)
from agent_engine.automation.integration.action_request_builder import (
    ActionRequestBuilder,
)
from agent_engine.automation.integration.execution_result_integrator import (
    ExecutionResultIntegrator,
)
from agent_engine.automation.registry.agent_registry import (
    AgentRegistry,
)
from agent_engine.automation.registry.action_registry import (
    ActionRegistry,
)
from agent_engine.automation.registry.tool_agent_mapper import (
    ToolAgentMapper,
)
from agent_engine.automation.dispatcher.action_dispatcher import (
    AutomationActionDispatcher,
)
from agent_engine.automation.agents.browser.browser_agent import (
    BrowserAutomationAgent,
)
from agent_engine.automation.agents.keyboard.keyboard_agent import (
    KeyboardAutomationAgent,
)
from agent_engine.automation.agents.mouse.mouse_agent import (
    MouseAutomationAgent,
)
from agent_engine.contracts.enums import (
    ToolType,
)


# =============================================================================
# DEMONSTRATION SCENARIO
# =============================================================================

REAL_AUTOMATION_DEMO_CASE = {

    "goal": (
        "Open Chrome, search for a JARVIS project resource, interact with "
        "the browser using keyboard and mouse actions, and complete the "
        "demonstration workflow."
    ),

    "summary": (
        "Open Chrome, search for a JARVIS project resource, navigate to the "
        "search results, interact with the browser using keyboard and mouse "
        "input, and complete the requested workflow."
    ),

    "missing_information": [],

    "tasks": [
        "Open Chrome",
        "Search for JARVIS agentic AI automation",
        "Navigate to the search results",
        "Click on a relevant search result",
        "Scroll down the page",
        "Click on another visible page element",
        "Return to the search results",
        "Use the keyboard to search for JARVIS automation",
    ],
}


# =============================================================================
# TASK FACTORY
# =============================================================================
#
# IMPORTANT:
# These tasks use the canonical action names expected by the current
# Automation Agents.
#
# This allows us to validate the real Automation Engine independently while
# the Agent Brain <-> Automation Engine action naming boundary is finalized.
# =============================================================================


def build_demo_tasks() -> list[InterpretedTask]:
    """
    Build the concrete demonstration tasks.

    Returns:
        List of InterpretedTask objects representing the demo workflow.
    """

    return [

        # ---------------------------------------------------------------------
        # Task 1 - Open browser
        # ---------------------------------------------------------------------

        InterpretedTask(
            task_id=1,
            action="open",
            tool=ToolType.BROWSER.value,
            parameters={
                "browser": "chrome",
            },
            metadata={
                "demo_step": 1,
                "description": "Open Chrome",
            },
        ),

        # ---------------------------------------------------------------------
        # Task 2 - Search
        # ---------------------------------------------------------------------

        InterpretedTask(
            task_id=2,
            action="search",
            tool=ToolType.BROWSER.value,
            parameters={
                "query": "JARVIS agentic AI automation",
            },
            metadata={
                "demo_step": 2,
                "description": (
                    "Search for JARVIS agentic AI automation"
                ),
            },
        ),

        # ---------------------------------------------------------------------
        # Task 3 - Navigate to search results
        # ---------------------------------------------------------------------

        InterpretedTask(
            task_id=3,
            action="press_key",
            tool=ToolType.KEYBOARD.value,
            parameters={
                "key": "enter",
            },
            metadata={
                "demo_step": 3,
                "description": "Navigate to the search results",
            },
        ),

        # ---------------------------------------------------------------------
        # Task 4 - Click relevant result
        #
        # Coordinates are deliberately configurable rather than hidden in
        # the architecture. Adjust them after observing the browser window.
        # ---------------------------------------------------------------------

        InterpretedTask(
            task_id=4,
            action="click",
            tool=ToolType.MOUSE.value,
            parameters={
                "button": "left",
            },
            metadata={
                "demo_step": 4,
                "description": "Click on a relevant search result",
            },
        ),

        # ---------------------------------------------------------------------
        # Task 5 - Scroll
        # ---------------------------------------------------------------------

        InterpretedTask(
            task_id=5,
            action="scroll",
            tool=ToolType.MOUSE.value,
            parameters={
                "dx": 0,
                "dy": -5,
            },
            metadata={
                "demo_step": 5,
                "description": "Scroll down the page",
            },
        ),

        # ---------------------------------------------------------------------
        # Task 6 - Click another visible page element
        # ---------------------------------------------------------------------

        InterpretedTask(
            task_id=6,
            action="click",
            tool=ToolType.MOUSE.value,
            parameters={
                "button": "left",
            },
            metadata={
                "demo_step": 6,
                "description": "Click on another visible page element",
            },
        ),

        # ---------------------------------------------------------------------
        # Task 7 - Return to search results
        # ---------------------------------------------------------------------

        InterpretedTask(
            task_id=7,
            action="go_back",
            tool=ToolType.BROWSER.value,
            parameters={},
            metadata={
                "demo_step": 7,
                "description": "Return to the search results",
            },
        ),

        # ---------------------------------------------------------------------
        # Task 8 - Keyboard search
        # ---------------------------------------------------------------------

        InterpretedTask(
            task_id=8,
            action="type_text",
            tool=ToolType.KEYBOARD.value,
            parameters={
                "text": "JARVIS automation",
            },
            metadata={
                "demo_step": 8,
                "description": (
                    "Use the keyboard to search for JARVIS automation"
                ),
            },
        ),

        # ---------------------------------------------------------------------
        # Task 9 - Submit keyboard search
        # ---------------------------------------------------------------------

        InterpretedTask(
            task_id=9,
            action="press_key",
            tool=ToolType.KEYBOARD.value,
            parameters={
                "key": "enter",
            },
            metadata={
                "demo_step": 9,
                "description": "Submit the keyboard search",
            },
        ),
    ]


# =============================================================================
# AGENT REGISTRATION
# =============================================================================


def create_agent_system() -> tuple[
    AgentRegistry,
    ToolAgentMapper,
    AutomationActionDispatcher,
]:
    """
    Create and configure the real Automation Engine agent system.

    Returns:
        AgentRegistry
        ToolAgentMapper
        AutomationActionDispatcher
    """

    print()
    print("=" * 78)
    print("JARVIS REAL AUTOMATION ENGINE")
    print("=" * 78)

    # -------------------------------------------------------------------------
    # Agent Registry
    # -------------------------------------------------------------------------

    agent_registry = AgentRegistry()

    browser_agent = BrowserAutomationAgent()

    keyboard_agent = KeyboardAutomationAgent()

    mouse_agent = MouseAutomationAgent()

    # -------------------------------------------------------------------------
    # Register real agents
    # -------------------------------------------------------------------------

    agent_registry.register(browser_agent)

    agent_registry.register(keyboard_agent)

    agent_registry.register(mouse_agent)

    print()
    print("Registered Automation Agents:")

    for agent in agent_registry.list_agents():

        print(
            f"  [{agent.tool_type.value}] "
            f"{agent.agent_id}"
        )

    # -------------------------------------------------------------------------
    # Tool → Agent mapping
    # -------------------------------------------------------------------------

    mapper = ToolAgentMapper(
        agent_registry
    )

    mapper.register(
        ToolType.BROWSER,
        browser_agent,
    )

    mapper.register(
        ToolType.KEYBOARD,
        keyboard_agent,
    )

    mapper.register(
        ToolType.MOUSE,
        mouse_agent,
    )

    print()
    print("Tool → Agent Mappings:")

    for tool_type, agent_id in mapper.list_mappings().items():

        print(
            f"  {tool_type.value} -> {agent_id}"
        )

    # -------------------------------------------------------------------------
    # Existing Automation Engine Action Registry
    # -------------------------------------------------------------------------

    action_registry = ActionRegistry()

    # -------------------------------------------------------------------------
    # Dispatcher
    # -------------------------------------------------------------------------

    dispatcher = AutomationActionDispatcher(
        action_registry,
        request_builder=ActionRequestBuilder(),
        tool_agent_mapper=mapper,
        result_integrator=ExecutionResultIntegrator(),
    )

    print()
    print("Automation Dispatcher: READY")
    print("=" * 78)

    return (
        agent_registry,
        mapper,
        dispatcher,
    )


# =============================================================================
# TASK EXECUTION
# =============================================================================


def execute_demo_task(
    dispatcher: AutomationActionDispatcher,
    task: InterpretedTask,
    attempt: int = 1,
):
    """
    Execute one demonstration task through the real dispatcher.
    """

    step = task.metadata.get(
        "demo_step",
        task.task_id,
    )

    description = task.metadata.get(
        "description",
        task.action,
    )

    print()
    print("-" * 78)
    print(
        f"DEMO STEP {step}: {description}"
    )
    print("-" * 78)

    print(
        f"Task ID     : {task.task_id}"
    )

    print(
        f"Action      : {task.action}"
    )

    print(
        f"Tool        : {task.tool}"
    )

    print(
        f"Parameters  : {task.parameters}"
    )

    # -------------------------------------------------------------------------
    # Dispatch
    # -------------------------------------------------------------------------

    result = dispatcher.dispatch(
        task,
        attempt=attempt,
        timeout_seconds=30.0,
    )

    print()
    print("Execution Result")
    print(
        f"  Status       : {result.status}"
    )
    print(
        f"  Success      : {result.success}"
    )
    print(
        f"  Attempt      : {result.attempt}"
    )
    print(
        f"  Execution    : "
        f"{result.execution_time:.4f}s"
    )

    if result.failure_type is not None:
        print(
            f"  Failure Type : {result.failure_type}"
        )

    if result.error_message:
        print(
            f"  Error        : {result.error_message}"
        )

    return result


# =============================================================================
# MAIN DEMONSTRATION
# =============================================================================


def main() -> None:
    """
    Run the complete real automation demonstration.
    """

    print()
    print("#" * 78)
    print("#")
    print("#                 JARVIS REAL AUTOMATION DEMO")
    print("#")
    print("#" * 78)

    print()
    print("Demo Goal:")
    print(
        REAL_AUTOMATION_DEMO_CASE["goal"]
    )

    print()
    print("Workflow:")

    for index, task in enumerate(
        REAL_AUTOMATION_DEMO_CASE["tasks"],
        start=1,
    ):
        print(
            f"  {index}. {task}"
        )

    # -------------------------------------------------------------------------
    # Create Automation Engine
    # -------------------------------------------------------------------------

    (
        agent_registry,
        mapper,
        dispatcher,
    ) = create_agent_system()

    # -------------------------------------------------------------------------
    # Build demonstration tasks
    # -------------------------------------------------------------------------

    tasks = build_demo_tasks()

    print()
    print("=" * 78)
    print(
        f"Prepared {len(tasks)} executable demonstration tasks."
    )
    print("=" * 78)

    # -------------------------------------------------------------------------
    # Execute workflow
    # -------------------------------------------------------------------------

    successful = 0
    failed = 0

    for task in tasks:

        result = execute_demo_task(
            dispatcher,
            task,
        )

        if result.success:

            successful += 1

        else:

            failed += 1

            print()
            print(
                "Demo execution stopped because the current "
                "task failed."
            )

            break

        # Small delay gives the operator time to observe the action.
        time.sleep(1)

    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------

    print()
    print("=" * 78)
    print("CLEANUP")
    print("=" * 78)

    for agent in agent_registry.list_agents():

        try:

            agent.cleanup()

            print(
                f"  {agent.agent_id}: cleaned"
            )

        except Exception as exc:

            print(
                f"  {agent.agent_id}: cleanup failed - {exc}"
            )

    # -------------------------------------------------------------------------
    # Final Summary
    # -------------------------------------------------------------------------

    print()
    print("#" * 78)
    print("#                 DEMONSTRATION SUMMARY")
    print("#" * 78)

    print()
    print(
        f"Total Tasks : {len(tasks)}"
    )

    print(
        f"Successful  : {successful}"
    )

    print(
        f"Failed      : {failed}"
    )

    if failed == 0:

        print()
        print(
            "REAL AUTOMATION DEMONSTRATION COMPLETED SUCCESSFULLY."
        )

    else:

        print()
        print(
            "REAL AUTOMATION DEMONSTRATION STOPPED "
            "BEFORE COMPLETION."
        )

    print()


# =============================================================================
# ENTRY POINT
# =============================================================================


if __name__ == "__main__":
    main()