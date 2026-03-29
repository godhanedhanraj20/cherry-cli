from fastapi import APIRouter, Depends

from api.dependencies.auth import get_client
from api.schemas.file import DeleteRequest, DeleteResponse
from api.services_adapter.adapters import delete_adapter

router = APIRouter(tags=["operations"])


@router.delete("/files", response_model=DeleteResponse)
async def delete_files(payload: DeleteRequest, client=Depends(get_client)):
    return await delete_adapter(client, payload.file_ids)
