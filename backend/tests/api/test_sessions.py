import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.crud_session import chat_session as crud_session
from app.crud.crud_user import user as crud_user
from app.schemas.chat import ChatSessionCreate
from app.schemas.user import UserCreate

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_user(db: AsyncSession, telegram_id: int = 111222333) -> object:
    user_in = UserCreate(
        telegram_id=telegram_id,
        full_name="Session User",
        username=f"sessionuser{telegram_id}",
    )
    return await crud_user.create(db, obj_in=user_in)


# ---------------------------------------------------------------------------
# GET /sessions/
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_sessions_empty(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Returns an empty list when no sessions exist."""
    response = await client.get(f"{settings.API_V1_STR}/sessions/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_sessions_all(client: AsyncClient, db_session: AsyncSession) -> None:
    """Returns all sessions without filtering."""
    user = await _create_user(db_session, telegram_id=111000001)
    await crud_session.create(
        db_session, obj_in=ChatSessionCreate(user_id=user.id, title="A")
    )
    await crud_session.create(
        db_session, obj_in=ChatSessionCreate(user_id=user.id, title="B")
    )

    response = await client.get(f"{settings.API_V1_STR}/sessions/")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_list_sessions_filter_by_user_id(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Returns only sessions belonging to the given user_id."""
    user1 = await _create_user(db_session, telegram_id=111000002)
    user2 = await _create_user(db_session, telegram_id=111000003)
    await crud_session.create(
        db_session, obj_in=ChatSessionCreate(user_id=user1.id, title="U1 Session")
    )
    await crud_session.create(
        db_session, obj_in=ChatSessionCreate(user_id=user2.id, title="U2 Session")
    )

    response = await client.get(f"{settings.API_V1_STR}/sessions/?user_id={user1.id}")
    assert response.status_code == 200
    content = response.json()
    assert len(content) == 1
    assert content[0]["user_id"] == user1.id
    assert content[0]["title"] == "U1 Session"


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_read_session(client: AsyncClient, db_session: AsyncSession) -> None:
    """Returns a session with its messages list."""
    user = await _create_user(db_session, telegram_id=111000004)
    session = await crud_session.create(
        db_session, obj_in=ChatSessionCreate(user_id=user.id, title="My Session")
    )

    response = await client.get(f"{settings.API_V1_STR}/sessions/{session.id}")
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == session.id
    assert content["title"] == "My Session"
    assert content["user_id"] == user.id
    assert "messages" in content


@pytest.mark.asyncio
async def test_read_session_not_found(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Returns 404 for a non-existent session ID."""
    response = await client.get(f"{settings.API_V1_STR}/sessions/99999")
    assert response.status_code == 404
    assert "Session not found" in response.json()["detail"]


# ---------------------------------------------------------------------------
# POST /sessions/
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_session(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    """Creates a new session and returns it."""
    user = auth_user["user"]
    headers = auth_user["headers"]

    payload = {"user_id": user.id, "title": "Brand New Session"}
    response = await client.post(
        f"{settings.API_V1_STR}/sessions/", json=payload, headers=headers
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == "Brand New Session"
    assert content["user_id"] == user.id
    assert "id" in content
    assert "messages" in content


@pytest.mark.asyncio
async def test_create_session_default_title(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    """Omitting title falls back to the default 'New Chat'."""
    user = auth_user["user"]
    headers = auth_user["headers"]

    payload = {"user_id": user.id}
    response = await client.post(
        f"{settings.API_V1_STR}/sessions/", json=payload, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["title"] == "New Chat"


@pytest.mark.asyncio
async def test_create_session_requires_auth(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """POST without a token is rejected with 401."""
    user = await _create_user(db_session, telegram_id=111000005)
    payload = {"user_id": user.id, "title": "Unauthorised"}
    response = await client.post(f"{settings.API_V1_STR}/sessions/", json=payload)
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# PATCH /sessions/{session_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_session_title(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    """Updates the title of an existing session."""
    user = auth_user["user"]
    headers = auth_user["headers"]

    session = await crud_session.create(
        db_session, obj_in=ChatSessionCreate(user_id=user.id, title="Old Title")
    )

    response = await client.patch(
        f"{settings.API_V1_STR}/sessions/{session.id}",
        json={"title": "New Title"},
        headers=headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == session.id
    assert content["title"] == "New Title"


@pytest.mark.asyncio
async def test_update_session_not_found(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    """Returns 404 when trying to update a non-existent session."""
    headers = auth_user["headers"]
    response = await client.patch(
        f"{settings.API_V1_STR}/sessions/99999",
        json={"title": "Ghost"},
        headers=headers,
    )
    assert response.status_code == 404
    assert "Session not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_session_requires_auth(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """PATCH without a token is rejected with 401."""
    user = await _create_user(db_session, telegram_id=111000006)
    session = await crud_session.create(
        db_session, obj_in=ChatSessionCreate(user_id=user.id, title="Title")
    )
    response = await client.patch(
        f"{settings.API_V1_STR}/sessions/{session.id}", json={"title": "Hacked"}
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# DELETE /sessions/{session_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_session(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    """Deletes a session and returns the deleted object."""
    user = auth_user["user"]
    headers = auth_user["headers"]

    session = await crud_session.create(
        db_session, obj_in=ChatSessionCreate(user_id=user.id, title="To Delete")
    )

    response = await client.delete(
        f"{settings.API_V1_STR}/sessions/{session.id}", headers=headers
    )
    assert response.status_code == 200
    assert response.json()["id"] == session.id

    # Confirm it's gone
    gone = await client.get(f"{settings.API_V1_STR}/sessions/{session.id}")
    assert gone.status_code == 404


@pytest.mark.asyncio
async def test_delete_session_not_found(
    client: AsyncClient, db_session: AsyncSession, auth_user: dict
) -> None:
    """Returns 404 when deleting a non-existent session."""
    headers = auth_user["headers"]
    response = await client.delete(
        f"{settings.API_V1_STR}/sessions/99999", headers=headers
    )
    assert response.status_code == 404
    assert "Session not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_session_requires_auth(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """DELETE without a token is rejected with 401."""
    user = await _create_user(db_session, telegram_id=111000007)
    session = await crud_session.create(
        db_session, obj_in=ChatSessionCreate(user_id=user.id, title="Protected")
    )
    response = await client.delete(f"{settings.API_V1_STR}/sessions/{session.id}")
    assert response.status_code == 401
