from typing import Any

from fastapi import APIRouter, BackgroundTasks

from app.api import deps

router = APIRouter()


@router.post("/sync")
async def sync_knowledge(
    knowledge_service: deps.KnowledgeServiceDep,
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Sync knowledge base with Google Drive in the background.
    """
    background_tasks.add_task(knowledge_service.sync_with_drive)
    return {"status": "Sync started in background"}
