"""
===============================================================================
File Name   : agent_registry.py
Module      : Automation Engine - Registry
Project     : JARVIS - Agent Decision Engine & Automation Engine

Description:
-------------
Provides a central registry for Automation Agents.

The AgentRegistry is responsible for:
    - Registering automation agents
    - Retrieving agents by agent ID
    - Checking whether an agent is registered
    - Unregistering agents
    - Listing registered agents
    - Clearing the registry

The registry manages agent instances only.

It does NOT:
    - execute actions
    - perform planning
    - perform retry decisions
    - perform fallback decisions
    - manage task execution state
    - map ToolType values to agents

Those responsibilities belong to the appropriate Dispatcher,
Decision Manager, State Manager, and later registry/mapping components.

Author      : Team JARVIS
===============================================================================
"""

from __future__ import annotations

from agent_engine.automation.agents.base import AutomationAgent


# =============================================================================
# Automation Agent Registry
# =============================================================================

class AgentRegistry:
    """
    Central registry for JARVIS Automation Agents.

    Agents are uniquely identified by their agent_id.
    """

    def __init__(self) -> None:
        """
        Initialize an empty agent registry.
        """

        self._agents: dict[str, AutomationAgent] = {}

    # -------------------------------------------------------------------------
    # Registration
    # -------------------------------------------------------------------------

    def register(self, agent: AutomationAgent) -> None:
        """
        Register an automation agent.

        Args:
            agent:
                AutomationAgent instance to register.

        Raises:
            TypeError:
                If the supplied object is not an AutomationAgent.

            ValueError:
                If the agent_id is empty.

            KeyError:
                If another agent with the same agent_id is already registered.
        """

        if not isinstance(agent, AutomationAgent):
            raise TypeError(
                "agent must be an instance of AutomationAgent."
            )

        agent_id = agent.agent_id

        if not isinstance(agent_id, str):
            raise TypeError(
                "agent.agent_id must be a string."
            )

        agent_id = agent_id.strip()

        if not agent_id:
            raise ValueError(
                "agent.agent_id cannot be empty."
            )

        if agent_id in self._agents:
            raise KeyError(
                f"Automation agent already registered: {agent_id}"
            )

        self._agents[agent_id] = agent

    # -------------------------------------------------------------------------
    # Retrieval
    # -------------------------------------------------------------------------

    def get(self, agent_id: str) -> AutomationAgent:
        """
        Retrieve a registered automation agent by ID.

        Args:
            agent_id:
                Unique identifier of the agent.

        Returns:
            Registered AutomationAgent.

        Raises:
            TypeError:
                If agent_id is not a string.

            ValueError:
                If agent_id is empty.

            KeyError:
                If no agent is registered with the supplied ID.
        """

        if not isinstance(agent_id, str):
            raise TypeError(
                "agent_id must be a string."
            )

        agent_id = agent_id.strip()

        if not agent_id:
            raise ValueError(
                "agent_id cannot be empty."
            )

        if agent_id not in self._agents:
            raise KeyError(
                f"Automation agent not registered: {agent_id}"
            )

        return self._agents[agent_id]

    # -------------------------------------------------------------------------
    # Membership
    # -------------------------------------------------------------------------

    def contains(self, agent_id: str) -> bool:
        """
        Check whether an agent is registered.

        Args:
            agent_id:
                Agent identifier.

        Returns:
            True if the agent is registered, otherwise False.
        """

        if not isinstance(agent_id, str):
            raise TypeError(
                "agent_id must be a string."
            )

        agent_id = agent_id.strip()

        if not agent_id:
            return False

        return agent_id in self._agents

    # -------------------------------------------------------------------------
    # Unregistration
    # -------------------------------------------------------------------------

    def unregister(self, agent_id: str) -> AutomationAgent:
        """
        Remove and return a registered automation agent.

        Args:
            agent_id:
                Unique identifier of the agent.

        Returns:
            The removed AutomationAgent.

        Raises:
            TypeError:
                If agent_id is not a string.

            ValueError:
                If agent_id is empty.

            KeyError:
                If the agent is not registered.
        """

        if not isinstance(agent_id, str):
            raise TypeError(
                "agent_id must be a string."
            )

        agent_id = agent_id.strip()

        if not agent_id:
            raise ValueError(
                "agent_id cannot be empty."
            )

        if agent_id not in self._agents:
            raise KeyError(
                f"Automation agent not registered: {agent_id}"
            )

        return self._agents.pop(agent_id)

    # -------------------------------------------------------------------------
    # Listing
    # -------------------------------------------------------------------------

    def list_agents(self) -> list[AutomationAgent]:
        """
        Return all registered automation agents.

        Returns:
            List of registered AutomationAgent instances.
        """

        return list(self._agents.values())

    # -------------------------------------------------------------------------
    # Registry Size
    # -------------------------------------------------------------------------

    def count(self) -> int:
        """
        Return the number of registered automation agents.
        """

        return len(self._agents)

    # -------------------------------------------------------------------------
    # Clear Registry
    # -------------------------------------------------------------------------

    def clear(self) -> None:
        """
        Remove all registered automation agents.
        """

        self._agents.clear()
