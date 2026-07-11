import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_facts import user_fact as crud_user_fact
from app.crud.crud_user import user as crud_user
from app.schemas.user_facts import FactCreate
from app.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_create_and_get_fact(db_session: AsyncSession) -> None:
    # 1. Create a user
    user_in = UserCreate(
        telegram_id=12345,
        full_name="Alice Memory",
        username="alice",
        is_superuser=False,
    )
    user = await crud_user.create(db_session, obj_in=user_in)

    # 2. Create a fact for user
    fact_in = FactCreate(fact_content="Likes green tea", category="preferences")
    fact = await crud_user_fact.create_fact(db_session, user_id=user.id, obj_in=fact_in)

    assert fact.id is not None
    assert fact.user_id == user.id
    assert fact.fact_content == "Likes green tea"
    assert fact.category == "preferences"

    # 3. Retrieve facts
    facts = await crud_user_fact.get_by_user_id(db_session, user_id=user.id)
    assert len(facts) == 1
    assert facts[0].id == fact.id


@pytest.mark.asyncio
async def test_fact_multi_tenant_isolation(db_session: AsyncSession) -> None:
    # Create User A
    user_a = await crud_user.create(
        db_session,
        obj_in=UserCreate(
            telegram_id=11111,
            full_name="User A",
            username="usera",
        ),
    )
    # Create User B
    user_b = await crud_user.create(
        db_session,
        obj_in=UserCreate(
            telegram_id=22222,
            full_name="User B",
            username="userb",
        ),
    )

    # Create fact for User A
    fact_a = await crud_user_fact.create_fact(
        db_session,
        user_id=user_a.id,
        obj_in=FactCreate(fact_content="User A likes coding"),
    )

    # User B should have 0 facts
    facts_b = await crud_user_fact.get_by_user_id(db_session, user_id=user_b.id)
    assert len(facts_b) == 0

    # User B trying to delete User A's fact should fail
    deleted = await crud_user_fact.delete_fact(
        db_session, fact_id=fact_a.id, user_id=user_b.id
    )
    assert deleted is None

    # User A's fact should still exist
    facts_a = await crud_user_fact.get_by_user_id(db_session, user_id=user_a.id)
    assert len(facts_a) == 1

    # User A deletes their own fact (success)
    deleted_a = await crud_user_fact.delete_fact(
        db_session, fact_id=fact_a.id, user_id=user_a.id
    )
    assert deleted_a is not None
    assert deleted_a.id == fact_a.id

    # User A should now have 0 facts
    facts_a_after = await crud_user_fact.get_by_user_id(db_session, user_id=user_a.id)
    assert len(facts_a_after) == 0


@pytest.mark.asyncio
async def test_get_by_user_id_with_limit(db_session: AsyncSession) -> None:
    # 1. Create a user
    user = await crud_user.create(
        db_session,
        obj_in=UserCreate(
            telegram_id=33333,
            full_name="Alice Limit",
            username="alicelimit",
        ),
    )

    # 2. Create 5 facts for this user
    for i in range(5):
        fact_in = FactCreate(fact_content=f"Fact number {i}", category="preferences")
        await crud_user_fact.create_fact(db_session, user_id=user.id, obj_in=fact_in)

    # 3. Retrieve with limit=3
    facts = await crud_user_fact.get_by_user_id(db_session, user_id=user.id, limit=3)
    assert len(facts) == 3

    # 4. Verify they are the most recent (last created)
    # i.e., "Fact number 4", "Fact number 3", "Fact number 2"
    assert facts[0].fact_content == "Fact number 4"
    assert facts[1].fact_content == "Fact number 3"
    assert facts[2].fact_content == "Fact number 2"
