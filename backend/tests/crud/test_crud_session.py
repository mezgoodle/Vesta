import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_session import chat_session as crud_session
from app.crud.crud_user import user as crud_user
from app.schemas.chat import ChatSessionCreate
from app.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_get_session(db_session: AsyncSession) -> None:
    user_in = UserCreate(
        telegram_id=888999000, full_name="Session Get User", username="sessionget"
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    session_in = ChatSessionCreate(user_id=user.id, title="Test Session")
    session = await crud_session.create(db_session, obj_in=session_in)

    retrieved = await crud_session.get(db_session, id=session.id)
    assert retrieved is not None
    assert retrieved.id == session.id
    assert retrieved.title == "Test Session"


@pytest.mark.asyncio
async def test_get_multi_sessions(db_session: AsyncSession) -> None:
    user_in = UserCreate(
        telegram_id=999000111, full_name="Session Multi User", username="sessionmulti"
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    session_in1 = ChatSessionCreate(user_id=user.id, title="Session 1")
    session_in2 = ChatSessionCreate(user_id=user.id, title="Session 2")

    await crud_session.create(db_session, obj_in=session_in1)
    await crud_session.create(db_session, obj_in=session_in2)

    sessions = await crud_session.get_multi(db_session)
    assert len(sessions) >= 2
