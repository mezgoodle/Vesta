"""
ADK integration service — replaces the monolithic ``LLMService``.

This service orchestrates the multi-agent system by:
1. Creating per-request tool closures bound to ``user_id`` / ``db``.
2. Building the agent hierarchy (root → secretary + knowledge).
3. Running the root agent via ADK's ``InMemoryRunner``.
4. Extracting the final text response from ADK events.
5. Logging tool calls and agent delegations to GCP.

The ``generate_session_summary`` method uses a standalone ``SummaryAgent``
for rolling conversation summaries (invoked by background tasks).
"""

import logging
import os
from typing import TYPE_CHECKING

from google.adk.agents import LlmAgent
from google.adk.events import Event
from google.adk.runners import InMemoryRunner
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.knowledge_agent import create_knowledge_agent
from app.agents.root_agent import create_root_agent
from app.agents.secretary_agent import create_secretary_agent
from app.agents.summary_agent import create_summary_agent
from app.core.config import settings
from app.services.gemini_tools import build_system_instruction, create_tools

if TYPE_CHECKING:
    from app.models.chat import ChatHistory

logger = logging.getLogger(__name__)

# ADK uses a fixed app_name / user_id pair to scope sessions.
_ADK_APP_NAME = "vesta"


class ADKService:
    """Service for interacting with the Vesta multi-agent system via Google ADK."""

    def __init__(self) -> None:
        """
        Initialize the ADK Service.

        Raises:
            ValueError: If GOOGLE_API_KEY or GOOGLE_MODEL_NAME is not set.
        """
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not set")
        if not settings.GOOGLE_MODEL_NAME:
            raise ValueError("GOOGLE_MODEL_NAME is not set")

        self.model = settings.GOOGLE_MODEL_NAME

        # ADK reads the API key from the GOOGLE_API_KEY env var.
        # Vesta loads it via pydantic Settings, so we bridge the two.
        os.environ.setdefault("GOOGLE_API_KEY", settings.GOOGLE_API_KEY)

    # ------------------------------------------------------------------ #
    # Main chat flow                                                      #
    # ------------------------------------------------------------------ #

    async def process_chat(
        self,
        user_text: str,
        history_records: list["ChatHistory"],
        user_id: int,
        db: AsyncSession,
        session_summary: str | None = None,
    ) -> str:
        """
        Process a chat message through the multi-agent system.

        Steps:
            1. Create request-scoped tools (bound to ``user_id`` / ``db``).
            2. Build agent hierarchy (root → secretary, knowledge).
            3. Convert DB history to ADK-compatible content.
            4. Create an ephemeral ADK session and runner.
            5. Run the root agent and collect events.
            6. Extract and return the final text response.

        Args:
            user_text: The user's message.
            history_records: List of ChatHistory DB records (oldest → newest).
            user_id: The authenticated user's ID.
            db: Database session.
            session_summary: Optional rolling summary of the conversation.

        Returns:
            The assistant's response text.

        Raises:
            Exception: If the agent invocation fails.
        """
        try:
            # 1. Create tools bound to this request's context
            tool_groups = create_tools(user_id=user_id, db=db)

            # 2. Build agent hierarchy
            secretary = create_secretary_agent(
                tools=tool_groups["secretary"],
                model=self.model,
            )
            knowledge = create_knowledge_agent(
                tools=tool_groups["knowledge"],
                model=self.model,
            )

            system_instruction = build_system_instruction(session_summary)

            root_agent = create_root_agent(
                sub_agents=[secretary, knowledge],
                system_instruction=system_instruction,
                model=self.model,
            )

            # 3. Convert DB history to ADK content
            history_content = self._map_history_to_content(history_records)

            # 4. Create ephemeral runner + session
            runner = InMemoryRunner(
                agent=root_agent,
                app_name=_ADK_APP_NAME,
            )

            # Create a session and pre-populate with conversation history
            adk_user_id = f"user-{user_id}"
            session = await runner.session_service.create_session(
                app_name=_ADK_APP_NAME,
                user_id=adk_user_id,
            )

            # Inject history into the session events so the agent has context
            if history_content:
                for content in history_content:
                    event = Event(
                        author=content.role if content.role != "model" else root_agent.name,
                        content=content,
                    )
                    session.events.append(event)

            # 5. Run the root agent with the new user message
            final_response = ""
            new_content = types.Content(
                role="user",
                parts=[types.Part(text=user_text)],
            )

            async for event in runner.run_async(
                user_id=adk_user_id,
                session_id=session.id,
                new_message=new_content,
            ):
                # Log agent delegations
                if event.author and event.author != root_agent.name:
                    self._log_agent_delegation(event.author)

                # Log tool calls if present
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "function_call") and part.function_call:
                            self._log_function_call(part.function_call)

                # Capture the final text response
                if event.is_final_response() and event.content and event.content.parts:
                    text_parts = [
                        p.text for p in event.content.parts
                        if hasattr(p, "text") and p.text
                    ]
                    if text_parts:
                        final_response = "\n".join(text_parts)

            if final_response:
                return final_response
            else:
                return "I couldn't generate a response. Please try again."

        except Exception:
            logger.error(
                "ADK agent error",
                extra={"json_fields": {"event": "adk_error"}},
            )
            raise

    # ------------------------------------------------------------------ #
    # Session summary generation                                          #
    # ------------------------------------------------------------------ #

    async def generate_session_summary(
        self,
        current_summary: str | None,
        recent_messages: list["ChatHistory"],
    ) -> str:
        """
        Generate an updated rolling summary of the conversation.

        Uses a standalone ``SummaryAgent`` (not part of the root hierarchy)
        to produce a concise summary from the existing summary and recent
        messages.

        Args:
            current_summary: The existing summary (may be None for first summary).
            recent_messages: The most recent ChatHistory records to fold in.

        Returns:
            An updated concise summary string.
        """
        formatted_messages = "\n".join(
            f"{msg.role}: {msg.content}" for msg in recent_messages
        )
        current_summary_text = current_summary or "No previous summary."
        fallback_summary = current_summary or ""

        prompt = (
            f"Here is the current summary of the conversation: {current_summary_text}.\n"
            f"Here are the newest messages:\n{formatted_messages}\n"
            f"Write an updated, concise summary including all important facts and context."
        )

        try:
            summary_agent = create_summary_agent(model=self.model)
            runner = InMemoryRunner(
                agent=summary_agent,
                app_name=_ADK_APP_NAME,
            )

            session = await runner.session_service.create_session(
                app_name=_ADK_APP_NAME,
                user_id="system-summary",
            )

            new_content = types.Content(
                role="user",
                parts=[types.Part(text=prompt)],
            )

            final_response = ""
            async for event in runner.run_async(
                user_id="system-summary",
                session_id=session.id,
                new_message=new_content,
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    text_parts = [
                        p.text for p in event.content.parts
                        if hasattr(p, "text") and p.text
                    ]
                    if text_parts:
                        final_response = "\n".join(text_parts)

            return final_response or fallback_summary

        except Exception:
            logger.error(
                "Failed to generate session summary via ADK",
                extra={"json_fields": {"event": "summary_error"}},
            )
            return fallback_summary

    # ------------------------------------------------------------------ #
    # Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _map_history_to_content(
        self, history_records: list["ChatHistory"]
    ) -> list[types.Content]:
        """
        Convert DB chat history to Gemini Content format.

        Maps:
        - DB role "model" → Gemini role "model"
        - DB role "user"  → Gemini role "user"

        Args:
            history_records: List of ChatHistory DB records.

        Returns:
            List of Gemini Content objects.
        """
        mapped = []
        for record in history_records:
            mapped.append(
                types.Content(
                    role=record.role,
                    parts=[types.Part(text=record.content)],
                )
            )
        return mapped

    def _log_function_call(self, function_call) -> None:
        """Log a tool/function call to GCP."""
        args = getattr(function_call, "args", {}) or {}
        logger.info(
            "ADK function call",
            extra={
                "json_fields": {
                    "event": "adk_function_call",
                    "function_name": function_call.name,
                    "function_arg_keys": list(args.keys())
                    if isinstance(args, dict)
                    else [],
                    "function_args_size": len(str(args)),
                }
            },
        )

    def _log_agent_delegation(self, agent_name: str) -> None:
        """Log an agent delegation event to GCP."""
        logger.info(
            "ADK agent delegation",
            extra={
                "json_fields": {
                    "event": "adk_delegation",
                    "delegated_to": agent_name,
                }
            },
        )


# ------------------------------------------------------------------ #
# FastAPI dependency                                                   #
# ------------------------------------------------------------------ #


async def adk_service():
    """FastAPI dependency that yields an ADKService instance."""
    yield ADKService()
