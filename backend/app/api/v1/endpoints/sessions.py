import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.api.deps import ArchiverServiceDep, CurrentUser, SessionDep
from app.core.config import settings
from app.crud.crud_chat import chat as crud_chat
from app.crud.crud_session import chat_session as crud_session
from app.schemas.chat import ChatSession, ChatSessionCreate, ChatSessionUpdate

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=list[ChatSession])
async def read_sessions(
    db: SessionDep,
    skip: int = 0,
    limit: int = 100,
    user_id: int | None = None,
) -> Any:
    """
    Retrieve chat sessions. Optionally filter by user_id.
    """
    if user_id is not None:
        sessions = await crud_session.get_by_user_id(
            db, user_id=user_id, skip=skip, limit=limit
        )
    else:
        sessions = await crud_session.get_multi(db, skip=skip, limit=limit)
    return sessions


@router.post("/", response_model=ChatSession)
async def create_session(
    *,
    db: SessionDep,
    session_in: ChatSessionCreate,
    current_user: CurrentUser,
) -> Any:
    """
    Create a new chat session.
    """
    session = await crud_session.create(db, obj_in=session_in)
    return await crud_session.get(db, id=session.id)


@router.get("/{session_id}", response_model=ChatSession)
async def read_session(
    *,
    db: SessionDep,
    session_id: int,
) -> Any:
    """
    Get a chat session by ID (includes messages).
    """
    session = await crud_session.get(db, id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.patch("/{session_id}", response_model=ChatSession)
async def update_session(
    *,
    db: SessionDep,
    session_id: int,
    session_in: ChatSessionUpdate,
    current_user: CurrentUser,
) -> Any:
    """
    Update a chat session (e.g. rename the title).
    """
    session = await crud_session.get(db, id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await crud_session.update(db, db_obj=session, obj_in=session_in)
    return await crud_session.get(db, id=session_id)


@router.delete("/{session_id}", response_model=ChatSession)
async def delete_session(
    *,
    db: SessionDep,
    session_id: int,
    current_user: CurrentUser,
    archiver: ArchiverServiceDep,
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Delete a chat session by ID and trigger background archiving to Google Drive.
    """
    session = await crud_session.get(db, id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = await crud_chat.get_by_session_id(db, session_id=session_id)

    session_data = {
        "id": session.id,
        "user_id": session.user_id,
        "title": session.title,
        "summary": session.summary,
        "created_at": session.created_at.isoformat() if session.created_at else None,
    }
    messages_data = [
        {
            "role": msg.role.value,
            "content": msg.content,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
        }
        for msg in messages
    ]

    session = await crud_session.remove(db, id=session_id)

    if messages_data and settings.SESSION_ARCHIVE_ENABLED:
        background_tasks.add_task(
            archiver.archive_session, session_data, messages_data
        )

    return session

