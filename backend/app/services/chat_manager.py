"""
Background task workers for chat session management.

These functions run outside the request/response cycle and therefore
MUST create their own database sessions rather than relying on the
request-scoped session (which will be closed by the time the task runs).
"""

import logging

from app.crud.crud_chat import chat as crud_chat
from app.crud.crud_session import chat_session as crud_session
from app.db.session import AsyncSessionLocal
from app.services.adk_service import ADKService

logger = logging.getLogger(__name__)

SUMMARY_MESSAGE_WINDOW = 6


async def update_session_summary_task(session_id: int) -> None:
    """
    Background task: generate and persist a rolling summary for a chat session.

    This function intentionally creates its own DB session because it runs
    after the request session has already been closed (FastAPI BackgroundTasks
    execute post-response). Using the request session here would raise
    ``sqlalchemy.exc.InvalidRequestError`` / ``DetachedInstanceError``.

    Args:
        session_id: The ID of the ``ChatSession`` to summarise.
    """
    logger.info(
        "Starting session summary update",
        extra={"json_fields": {"event": "summary_start", "session_id": session_id}},
    )

    async with AsyncSessionLocal() as db:
        try:
            session = await crud_session.get(db, id=session_id)
            if not session:
                logger.warning(
                    "Session not found for summary update",
                    extra={
                        "json_fields": {
                            "event": "summary_session_missing",
                            "session_id": session_id,
                        }
                    },
                )
                return

            recent_messages = await crud_chat.get_recent_by_session_id(
                db,
                session_id=session_id,
                limit=SUMMARY_MESSAGE_WINDOW,
            )

            if not recent_messages:
                logger.info(
                    "No messages to summarise",
                    extra={
                        "json_fields": {
                            "event": "summary_no_messages",
                            "session_id": session_id,
                        }
                    },
                )
                return

            adk = ADKService()
            new_summary = await adk.generate_session_summary(
                current_summary=session.summary,
                recent_messages=recent_messages,
            )

            await crud_session.update(
                db,
                db_obj=session,
                obj_in={"summary": new_summary},
            )
            await db.commit()

            logger.info(
                "Session summary updated successfully",
                extra={
                    "json_fields": {
                        "event": "summary_done",
                        "session_id": session_id,
                    }
                },
            )

        except Exception:
            logger.error(
                "Failed to update session summary",
                extra={
                    "json_fields": {
                        "event": "summary_error",
                        "session_id": session_id,
                    }
                },
            )
            await db.rollback()
