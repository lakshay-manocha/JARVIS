"""
===============================================================================
File Name   : tool_agent_mapper.py
Module      : Automation Engine - Registry
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Provides the mapping between ToolType values and registered Automation Agents.

The ToolAgentMapper determines which AutomationAgent is responsible for
handling a particular ToolType.

Responsibilities:
    - Register ToolType -> agent mappings
    - Resolve an AutomationAgent from a ToolType
    - Validate ToolType and agent compatibility
    - Remove mappings
    - Inspect registered mappings

The mapper does NOT:
    - execute actions
    - perform retries
    - perform fallback decisions
    - manage execution state
    - create automation agents
    - perform planning

Those responsibilities belong to the appropriate Automation Engine and
Agent Brain components.

Author      : Team JARVIS
===============================================================================
"""

from __future__ import annotations

from agent_engine.automation.agents.base import AutomationAgent
from agent_engine.automation.registry.agent_registry import AgentRegistry
from agent_engine.contracts.enums import ToolType


class ToolAgentMapper:
    """
    Maps ToolType values to registered AutomationAgent instances.

    The mapper relies on AgentRegistry as the single source of truth for
    registered agents.
    """

    def __init__(self, agent_registry: AgentRegistry) -> None:
        """
        Initialize the ToolAgentMapper.

        Args:
            agent_registry:
                Registry containing the available AutomationAgent instances.

        Raises:
            TypeError:
                If agent_registry is not an AgentRegistry instance.
        """

        if not isinstance(agent_registry, AgentRegistry):
            raise TypeError("agent_registry must be an AgentRegistry.")

        self._agent_registry = agent_registry
        self._mappings: dict[ToolType, str] = {}

    # -------------------------------------------------------------------------
    # Registration
    # -------------------------------------------------------------------------

    def register(
        self,
        tool_type: ToolType,
        agent: AutomationAgent,
    ) -> None:
        """
        Register an AutomationAgent for a ToolType.
        """

        if not isinstance(tool_type, ToolType):
            raise TypeError("tool_type must be a ToolType.")

        if not isinstance(agent, AutomationAgent):
            raise TypeError("agent must be an AutomationAgent.")

        if agent.tool_type != tool_type:
            raise ValueError(
                "ToolType mismatch: "
                f"mapping={tool_type.value}, "
                f"agent={agent.tool_type.value}"
            )

        if tool_type in self._mappings:
            raise KeyError(
                f"A mapping already exists for ToolType: {tool_type.value}"
            )

        # Ensure the agent is registered in AgentRegistry.
        try:
            self._agent_registry.get(agent.agent_id)
        except KeyError:
            self._agent_registry.register(agent)

        self._mappings[tool_type] = agent.agent_id
    # -------------------------------------------------------------------------
    # Resolution
    # -------------------------------------------------------------------------

    def resolve(self, tool_type: ToolType) -> AutomationAgent:
        """
        Resolve the AutomationAgent responsible for a ToolType.

        Args:
            tool_type:
                ToolType that needs to be resolved.

        Returns:
            Registered AutomationAgent responsible for the ToolType.

        Raises:
            TypeError:
                If tool_type is not a ToolType.

            KeyError:
                If no mapping exists for the ToolType.
        """

        if not isinstance(tool_type, ToolType):
            raise TypeError("tool_type must be a ToolType.")

        if tool_type not in self._mappings:
            raise KeyError(
                f"No AutomationAgent mapped to ToolType: {tool_type.value}"
            )

        agent_id = self._mappings[tool_type]

        return self._agent_registry.get(agent_id)

    # -------------------------------------------------------------------------
    # Inspection
    # -------------------------------------------------------------------------

    def contains(self, tool_type: ToolType) -> bool:
        """
        Check whether a ToolType has an associated AutomationAgent.
        """

        if not isinstance(tool_type, ToolType):
            raise TypeError("tool_type must be a ToolType.")

        return tool_type in self._mappings

    def get_agent_id(self, tool_type: ToolType) -> str:
        """
        Return the agent ID mapped to a ToolType.
        """

        if not isinstance(tool_type, ToolType):
            raise TypeError("tool_type must be a ToolType.")

        if tool_type not in self._mappings:
            raise KeyError(
                f"No AutomationAgent mapped to ToolType: {tool_type.value}"
            )

        return self._mappings[tool_type]

    def list_mappings(self) -> dict[ToolType, str]:
        """
        Return a copy of the current ToolType -> agent_id mappings.
        """

        return dict(self._mappings)

    # -------------------------------------------------------------------------
    # Removal
    # -------------------------------------------------------------------------

    def unregister(self, tool_type: ToolType) -> None:
        """
        Remove the mapping for a ToolType.

        Note:
            This only removes the ToolType mapping. It does not unregister
            the AutomationAgent itself from AgentRegistry.
        """

        if not isinstance(tool_type, ToolType):
            raise TypeError("tool_type must be a ToolType.")

        if tool_type not in self._mappings:
            raise KeyError(
                f"No mapping exists for ToolType: {tool_type.value}"
            )

        del self._mappings[tool_type]

    def clear(self) -> None:
        """
        Remove all ToolType -> agent mappings.
        """

        self._mappings.clear()