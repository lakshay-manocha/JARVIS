"""
===============================================================================
Package Name : automation.agents
Project      : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Contains the base contract and concrete implementations of JARVIS
Automation Agents.

Author      : Team JARVIS
===============================================================================
"""

from agent_engine.automation.agents.base import (
    AutomationAgent,
)
from agent_engine.automation.agents.mock_agent import (
    MockAutomationAgent,
)


__all__ = [
    "AutomationAgent",
    "MockAutomationAgent",
]