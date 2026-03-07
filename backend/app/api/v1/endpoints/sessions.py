import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
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
    return session


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
    session = await crud_session.update(db, db_obj=session, obj_in=session_in)
    return session


@router.delete("/{session_id}", response_model=ChatSession)
async def delete_session(
    *,
    db: SessionDep,
    session_id: int,
    current_user: CurrentUser,
) -> Any:
    """
    Delete a chat session by ID.
    """
    session = await crud_session.get(db, id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session = await crud_session.remove(db, id=session_id)
    return session
