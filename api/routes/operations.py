from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel

from api.dependencies.auth import get_client
from api.schemas.file import DeleteRequest, DeleteResponse
from api.services_adapter.adapters import delete_adapter
from services.auth import get_authenticated_client
from services.backup_service import backup_metadata, restore_metadata_backup

router = APIRouter(tags=["operations"])


class RestoreRequest(BaseModel):
    backup_id: int | None = None


async def _run_backup_task():
    client = await get_authenticated_client()
    try:
        await backup_metadata(client)
    finally:
        await client.disconnect()


async def _run_restore_task(backup_id: int | None):
    client = await get_authenticated_client()
    try:
        await restore_metadata_backup(client, backup_id=backup_id)
    finally:
        await client.disconnect()


@router.delete("/files", response_model=DeleteResponse)
async def delete_files(payload: DeleteRequest, client=Depends(get_client)):
    return await delete_adapter(client, payload.file_ids)


@router.post("/metadata/backup")
async def start_backup(background_tasks: BackgroundTasks):
    background_tasks.add_task(_run_backup_task)
    return {"status": "started", "invalidate_cache": True}


@router.post("/metadata/restore")
async def start_restore(payload: RestoreRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(_run_restore_task, payload.backup_id)
    return {"status": "started", "invalidate_cache": True}
