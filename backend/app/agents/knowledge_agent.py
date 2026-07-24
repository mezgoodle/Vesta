"""
Knowledge sub-agent — answers questions from the user's personal knowledge base.

This module provides a factory function that creates an ``LlmAgent`` with
the RAG tool (``consult_knowledge_base``) already attached.
"""

from collections.abc import Callable

from google.adk.agents import LlmAgent

from app.core.config import settings


def create_knowledge_agent(
    tools: list[Callable], model: str, current_time_str: str | None = None
) -> LlmAgent:
    """
    Create the Knowledge sub-agent.

    Args:
        tools: Pre-bound tool functions for RAG
               (``consult_knowledge_base``).
        model: The Gemini model name (e.g. ``gemini-2.5-flash``).
        current_time_str: Optional current date/time context.

    Returns:
        A configured ``LlmAgent`` ready for use as a sub-agent.
    """

    instruction = (
        "You are a knowledge base assistant within the Vesta smart assistant.\n"
        "Your responsibilities:\n"
        "1. CRITICAL: You MUST ALWAYS use the `consult_knowledge_base` tool to search "
        "the user's personal knowledge base BEFORE answering any question. Do NOT answer "
        "from your general knowledge.\n"
        "2. Synthesize information from retrieved documents into clear, "
        "helpful answers.\n"
        "3. If the knowledge base returns no relevant results, let the user "
        "know and suggest they may need to sync their documents.\n"
        "4. Always cite or reference the source context when providing "
        "information from documents.\n"
        "Always respond in a friendly, concise manner.\n\n"
        f"{settings.TELEGRAM_HTML_GUIDELINES}"
    )
    if current_time_str:
        instruction = f"Current Date and Time: {current_time_str}.\n{instruction}"

    return LlmAgent(
        name="KnowledgeAgent",
        model=model,
        description=(
            "Answers questions using the user's personal knowledge base and uploaded documents. "
            "You MUST delegate to this agent if the user asks about: "
            "1. Personal notes, recipes, reports, meeting notes, research papers, or any topic in their document library. "
            "2. Instructions, manuals, or configuration/setup guides for appliances and equipment (e.g., boiler, washing machine, heating system, printer). "
            "3. Personal documents, files, rules, agreements, or assets stored on Google Drive. "
            "4. Troubleshooting or document queries containing phrases like 'find in documents', 'search my files', or 'what is written in the manual' for personal files or saved guides. "
            "Do NOT delegate generic technical questions or uncontextualized errors unless explicit document, manual, or saved file context is present."
        ),
        instruction=instruction,
        tools=tools,
        mode="single_turn",
    )
