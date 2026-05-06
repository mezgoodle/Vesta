"""
Knowledge sub-agent — answers questions from the user's personal knowledge base.

This module provides a factory function that creates an ``LlmAgent`` with
the RAG tool (``consult_knowledge_base``) already attached.
"""

from typing import Callable

from google.adk.agents import LlmAgent


def create_knowledge_agent(tools: list[Callable], model: str) -> LlmAgent:
    """
    Create the Knowledge sub-agent.

    Args:
        tools: Pre-bound tool functions for RAG
               (``consult_knowledge_base``).
        model: The Gemini model name (e.g. ``gemini-2.5-flash``).

    Returns:
        A configured ``LlmAgent`` ready for use as a sub-agent.
    """
    return LlmAgent(
        name="KnowledgeAgent",
        model=model,
        description=(
            "Answers questions using the user's personal knowledge base and "
            "uploaded documents. Delegate to this agent when the user asks about "
            "personal notes, uploaded files, recipes, manuals, reports, meeting "
            "notes, research papers, or any topic that might be in their "
            "document library."
        ),
        instruction=(
            "You are a knowledge base assistant within the Vesta smart assistant.\n"
            "Your responsibilities:\n"
            "1. Search the user's personal knowledge base using the "
            "consult_knowledge_base tool.\n"
            "2. Synthesize information from retrieved documents into clear, "
            "helpful answers.\n"
            "3. If the knowledge base returns no relevant results, let the user "
            "know and suggest they may need to sync their documents.\n"
            "4. Always cite or reference the source context when providing "
            "information from documents.\n"
            "Always respond in a friendly, concise manner."
        ),
        tools=tools,
    )
