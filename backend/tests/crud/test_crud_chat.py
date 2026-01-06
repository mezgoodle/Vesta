import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_chat import chat as crud_chat
from app.crud.crud_user import user as crud_user
from app.schemas.chat import ChatHistoryCreate
from app.schemas.user import UserCreate


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


@pytest.mark.asyncio
async def test_get_recent_by_user_id(db_session: AsyncSession) -> None:
    """Test get_recent_by_user_id returns messages in correct order with limit."""
    # Create a user
    user_in = UserCreate(
        telegram_id=444555666, full_name="Recent Chat User", username="recentchat"
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    # Create multiple messages
    messages = [
        ("user", "First message"),
        ("assistant", "First response"),
        ("user", "Second message"),
        ("assistant", "Second response"),
        ("user", "Third message"),
        ("assistant", "Third response"),
    ]

    for role, content in messages:
        chat_in = ChatHistoryCreate(user_id=user.id, role=role, content=content)
        await crud_chat.create(db_session, obj_in=chat_in)

    # Test with limit - should get LAST 4 messages (most recent)
    recent = await crud_chat.get_recent_by_user_id(db_session, user_id=user.id, limit=4)

    assert len(recent) == 4
    # Should return last 4 messages in oldest to newest order
    # Last 4 are: "Second message", "Second response", "Third message", "Third response"
    assert recent[0].content == "Second message"
    assert recent[1].content == "Second response"
    assert recent[2].content == "Third message"
    assert recent[3].content == "Third response"

    # Test getting all messages
    all_recent = await crud_chat.get_recent_by_user_id(
        db_session, user_id=user.id, limit=20
    )
    assert len(all_recent) == 6
    # First message should be the oldest
    assert all_recent[0].content == "First message"
    # Last message should be the newest
    assert all_recent[-1].content == "Third response"


@pytest.mark.asyncio
async def test_get_recent_by_user_id_ordering(db_session: AsyncSession) -> None:
    """Test that messages are returned in oldest to newest order."""
    # Create a user
    user_in = UserCreate(
        telegram_id=555666777, full_name="Order Test User", username="ordertest"
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    # Test with empty history
    empty_history = await crud_chat.get_recent_by_user_id(
        db_session, user_id=user.id, limit=20
    )
    assert len(empty_history) == 0

    # Create single message
    chat_in = ChatHistoryCreate(user_id=user.id, role="user", content="Single message")
    await crud_chat.create(db_session, obj_in=chat_in)

    single = await crud_chat.get_recent_by_user_id(db_session, user_id=user.id)
    assert len(single) == 1
    assert single[0].content == "Single message"

    # Add more messages and verify order
    for i in range(5):
        chat_in = ChatHistoryCreate(
            user_id=user.id, role="user", content=f"Message {i + 2}"
        )
        await crud_chat.create(db_session, obj_in=chat_in)

    # Now we have 6 messages total, get all of them
    ordered = await crud_chat.get_recent_by_user_id(
        db_session, user_id=user.id, limit=6
    )
    # Verify chronological order (oldest to newest)
    assert len(ordered) == 6
    assert ordered[0].content == "Single message"
    assert ordered[1].content == "Message 2"
    assert ordered[-1].content == "Message 6"
