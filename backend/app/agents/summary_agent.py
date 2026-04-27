"""
Summary agent — generates rolling conversation summaries.

This is a standalone agent (not a sub-agent of the root dispatcher).  It is
invoked directly by the background task in ``chat_manager.py`` to produce
concise summaries of recent conversation messages.
"""

from google.adk.agents import LlmAgent


def create_summary_agent(model: str) -> LlmAgent:
    """
    Create the Summary agent.

    Args:
        model: The Gemini model name (e.g. ``gemini-2.5-flash``).

    Returns:
        A configured ``LlmAgent`` for summarisation tasks.
    """
    return LlmAgent(
        name="SummaryAgent",
        model=model,
        description="Generates concise conversation summaries.",
        instruction=(
            "You are a summarisation assistant.\n"
            "Your sole task is to produce an updated, concise summary of a "
            "conversation when given the current summary and the newest "
            "messages.\n"
            "Rules:\n"
            "1. Preserve all important facts, topics, preferences, and context "
            "from the existing summary.\n"
            "2. Incorporate the key points from the new messages.\n"
            "3. Keep the summary concise — aim for 3-5 sentences.\n"
            "4. Do NOT add information that was not in the conversation.\n"
            "5. Write the summary in third person (e.g. 'The user asked about…')."
        ),
    )
