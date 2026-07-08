"""
Root (dispatcher) agent — routes user requests to the correct sub-agent.

The root agent has **no tools of its own**.  It uses ADK's Agent Transfer
mechanism: the LLM reads each sub-agent's ``description`` and decides which
one should handle the current request.  For general conversation that doesn't
need any tools, the root agent responds directly.
"""

from typing import Callable
from google.adk.agents import LlmAgent


def create_root_agent(
    sub_agents: list[LlmAgent],
    system_instruction: str,
    model: str,
    tools: list[Callable] = None,
) -> LlmAgent:
    """
    Create the Vesta root dispatcher agent.

    Args:
        sub_agents: List of sub-agents to delegate to
                    (``WeatherAgent``, ``CalendarAgent``, ``KnowledgeAgent``).
        system_instruction: The dynamic system prompt (includes current time,
                            location defaults, conversation summary, and
                            delegation guidelines).
        model: The Gemini model name (e.g. ``gemini-2.5-flash``).
        tools: Optional list of tools for the root agent itself (e.g. memory tools).

    Returns:
        A configured ``LlmAgent`` that acts as the entry-point for all
        user interactions.
    """
    return LlmAgent(
        name="VestaRootAgent",
        model=model,
        description="Root routing agent for the Vesta smart assistant.",
        instruction=system_instruction,
        sub_agents=sub_agents,
        tools=tools,
    )
