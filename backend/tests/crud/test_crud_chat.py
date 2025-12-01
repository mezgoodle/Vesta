import pytest
from app.crud.crud_chat import chat as crud_chat
from app.crud.crud_user import user as crud_user
from app.schemas.chat import ChatHistoryCreate
from app.schemas.user import UserCreate
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_chat_history(db_session: AsyncSession) -> None:
    user_in = UserCreate(
        telegram_id=222333444, full_name="Chat CRUD User", username="chatcrud"
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    chat_in = ChatHistoryCreate(
        user_id=user.id, role="user", content="Testing CRUD chat"
    )
    chat_message = await crud_chat.create(db_session, obj_in=chat_in)

    assert chat_message.content == "Testing CRUD chat"
    assert chat_message.user_id == user.id


@pytest.mark.asyncio
async def test_get_chat_history_by_user_id(db_session: AsyncSession) -> None:
    user_in = UserCreate(
        telegram_id=333444555, full_name="Chat History User", username="chathist"
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    chat_in = ChatHistoryCreate(
        user_id=user.id, role="assistant", content="Response message"
    )
    await crud_chat.create(db_session, obj_in=chat_in)

    history = await crud_chat.get_by_user_id(db_session, user_id=user.id)
    assert len(history) == 1
    assert history[0].content == "Response message"
