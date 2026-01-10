import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import LLMServiceDep, SessionDep
from app.crud.crud_chat import chat as crud_chat
from app.crud.crud_session import chat_session as crud_session
from app.crud.crud_user import user as crud_user
from app.schemas.chat import (
    ChatHistory,
    ChatHistoryCreate,
    ChatRequest,
    ChatResponse,
    ChatSessionCreate,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/process", response_model=ChatResponse)
async def process_chat_message(
    *,
    db: SessionDep,
    chat_request: ChatRequest,
    llm_service: LLMServiceDep,
) -> Any:
    """
    Process a chat message with Gemini AI.

    Flow:
    1. Validate user exists
    2. Save user message to database
    3. Fetch last 20 messages for context
    4. Call Gemini AI with history
    5. Save assistant response to database
    6. Return response
    """
    user = await crud_user.get(db, id=chat_request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    current_session_id = chat_request.session_id

    if not current_session_id:
        current_session = await crud_session.create(
            db,
            obj_in=ChatSessionCreate(
                user_id=user.id,
                title="New Chat",
            ),
        )
        current_session_id = current_session.id
    else:
        current_session = await crud_session.get(db, id=current_session_id)
        if not current_session:
            raise HTTPException(status_code=404, detail="Session not found")

        if current_session.user_id != user.id:
            raise HTTPException(
                status_code=403, detail="Session does not belong to user"
            )

    try:
        # Fetch last 20 messages for context (oldest to newest)
        # We do this before saving the new message to avoid including it in history
        history_records = await crud_chat.get_recent_by_session_id(
            db, session_id=current_session_id, limit=20
        )

        user_message = await crud_chat.create(
            db,
            obj_in=ChatHistoryCreate(
                user_id=user.id,
                session_id=current_session_id,
                role="user",
                content=chat_request.message,
            ),
        )

        # Call Gemini AI
        assistant_response_text = await llm_service.chat(
            user_text=chat_request.message,
            history_records=history_records,
        )

        # Save assistant response to database
        assistant_message = await crud_chat.create(
            db,
            obj_in=ChatHistoryCreate(
                user_id=user.id,
                session_id=current_session_id,
                role="assistant",
                content=assistant_response_text,
            ),
        )

        return ChatResponse(
            response=assistant_response_text,
            session_id=current_session_id,
            user_message_id=user_message.id,
            assistant_message_id=assistant_message.id,
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process chat message",
        )


@router.get("/", response_model=list[ChatHistory])
async def read_chat_history(
    db: SessionDep,
    skip: int = 0,
    limit: int = 100,
    user_id: int | None = None,
) -> Any:
    """
    Retrieve chat history.
    """
    if user_id is not None:
        chat_history = await crud_chat.get_by_user_id(
            db, user_id=user_id, skip=skip, limit=limit
        )
    else:
        chat_history = await crud_chat.get_multi(db, skip=skip, limit=limit)
    return chat_history


@router.post("/", response_model=ChatHistory)
async def create_chat_message(
    *,
    db: SessionDep,
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
    db: SessionDep,
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
    db: SessionDep,
    chat_id: int,
) -> Any:
    """
    Delete a chat message.
    """
    chat_message = await crud_chat.remove(db, id=chat_id)
    if not chat_message:
        raise HTTPException(status_code=404, detail="Chat message not found")
    return chat_message
