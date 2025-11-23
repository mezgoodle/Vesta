from typing import Any, List

from app.api import deps
from app.crud.crud_chat import chat as crud_chat
from app.crud.crud_user import user as crud_user
from app.schemas.chat import ChatHistory, ChatHistoryCreate
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/", response_model=List[ChatHistory])
async def read_chat_history(
    db: deps.SessionDep,
    skip: int = 0,
    limit: int = 100,
    user_id: int = None,
) -> Any:
    """
    Retrieve chat history.
    """
    if user_id:
        chat_history = await crud_chat.get_by_user_id(
            db, user_id=user_id, skip=skip, limit=limit
        )
    else:
        chat_history = await crud_chat.get_multi(db, skip=skip, limit=limit)
    return chat_history


@router.post("/", response_model=ChatHistory)
async def create_chat_message(
    *,
    db: deps.SessionDep,
    chat_in: ChatHistoryCreate,
) -> Any:
    """
    Create new chat message.
    """
    # Check if user exists
    user = await crud_user.get(db, id=chat_in.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    chat_message = await crud_chat.create(db, obj_in=chat_in)
    return chat_message


@router.get("/{chat_id}", response_model=ChatHistory)
async def read_chat_message(
    *,
    db: deps.SessionDep,
    chat_id: int,
) -> Any:
    """
    Get chat message by ID.
    """
    chat_message = await crud_chat.get(db, id=chat_id)
    if not chat_message:
        raise HTTPException(status_code=404, detail="Chat message not found")
    return chat_message


@router.delete("/{chat_id}", response_model=ChatHistory)
async def delete_chat_message(
    *,
    db: deps.SessionDep,
    chat_id: int,
) -> Any:
    """
    Delete a chat message.
    """
    chat_message = await crud_chat.get(db, id=chat_id)
    if not chat_message:
        raise HTTPException(status_code=404, detail="Chat message not found")
    chat_message = await crud_chat.remove(db, id=chat_id)
    return chat_message
