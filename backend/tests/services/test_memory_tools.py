import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_user import user as crud_user
from app.schemas.user import UserCreate
from app.services.gemini_tools import (
    build_personalized_prompt,
    build_system_instruction,
    create_tools,
)


@pytest.mark.asyncio
async def test_memory_tools_end_to_end(db_session: AsyncSession) -> None:
    # 1. Create a user
    user = await crud_user.create(
        db_session,
        obj_in=UserCreate(
            telegram_id=99999,
            full_name="Memory User",
            username="memuser",
        ),
    )

    # 2. Create tools bound to user
    tool_groups = create_tools(user_id=user.id, db=db_session)
    assert "memory" in tool_groups
    remember_tool = tool_groups["memory"][0]
    delete_tool = tool_groups["memory"][1]

    # 3. Call remember tool
    remember_res = await remember_tool(
        fact_content="Likes spicy food", category="preferences"
    )
    assert "Saved fact:" in remember_res
    assert "Likes spicy food" in remember_res

    # Extract ID from the result string like "Saved fact: [ID: 1] Likes spicy food"
    import re

    match = re.search(r"\[ID: (\d+)\]", remember_res)
    assert match is not None
    fact_id = int(match.group(1))

    # 4. Personalize instruction
    prompt_res = await build_personalized_prompt(
        db=db_session, user_id=user.id, session_summary="Some summary"
    )
    assert "Likes spicy food" in prompt_res
    assert f"[ID: {fact_id}] (preferences) Likes spicy food" in prompt_res

    # 5. Delete fact
    delete_res = await delete_tool(fact_id=fact_id)
    assert f"Successfully deleted fact [ID: {fact_id}]" in delete_res

    # 6. Verify fact is deleted
    prompt_res_after = await build_personalized_prompt(
        db=db_session, user_id=user.id, session_summary="Some summary"
    )
    assert "Likes spicy food" not in prompt_res_after
    assert "No personal facts stored yet." in prompt_res_after
