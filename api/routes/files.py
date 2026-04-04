import logging
import os
import shutil
import tempfile
import time
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Path, Query, UploadFile
from fastapi.responses import StreamingResponse

from api.dependencies.auth import get_client
from api.schemas.file import (
    FileListResponse,
    FileSearchResponse,
    FileTypeValue,
    RenameFileRequest,
    RenameFileResponse,
    SortValue,
    UpdateTagRequest,
    UpdateTagResponse,
    UploadResponse,
)
from api.services_adapter.adapters import download_adapter, list_adapter, search_adapter, upload_adapter
from services.metadata_service import manage_tags, rename_file
from utils.errors import TSGError

router = APIRouter(prefix="/files", tags=["files"])
logger = logging.getLogger(__name__)
_last_cleanup = 0.0



def should_cleanup() -> bool:
    global _last_cleanup
    now = time.time()
    if now - _last_cleanup > 300:
        _last_cleanup = now
        return True
    return False


@router.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...), client=Depends(get_client)):
    if not file.filename or not file.filename.strip():
        raise HTTPException(status_code=400, detail={"error": "No file provided"})
    return await upload_adapter(client, file)


@router.get("", response_model=FileListResponse)
async def list_files(
    limit: int = Query(50, ge=1, le=200),
    page: int = Query(1, ge=1),
    sort: SortValue = Query("date"),
    type: Optional[FileTypeValue] = Query(None),
    tag: Optional[str] = Query(None),
    client=Depends(get_client),
):
    return await list_adapter(client, limit=limit, page=page, sort=sort, file_type=type, tag=tag)


@router.get("/search", response_model=FileSearchResponse)
async def search(
    query: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    page: int = Query(1, ge=1),
    sort: SortValue = Query("date"),
    type: Optional[FileTypeValue] = Query(None),
    tag: Optional[str] = Query(None),
    client=Depends(get_client),
):
    if not any([query, type, tag]):
        raise HTTPException(status_code=400, detail={"error": "Provide query, type, or tag"})
    return await search_adapter(client, query=query, limit=limit, page=page, sort=sort, file_type=type, tag=tag)


@router.post("/tag", response_model=UpdateTagResponse)
async def update_tag(payload: UpdateTagRequest):
    action = "remove" if payload.action == "remove" else "add"
    result = manage_tags([str(payload.file_id)], action=action, tag_name=payload.tag)[0]
    return {
        "success": True,
        "file_id": int(result["file_id"]),
        "action": action,
        "tag": result["tag"],
        "invalidate_cache": True,
    }


@router.post("/rename", response_model=RenameFileResponse)
async def update_name(payload: RenameFileRequest):
    result = rename_file(str(payload.file_id), payload.new_name)
    return {
        "success": True,
        "file_id": int(result["file_id"]),
        "custom_name": result["custom_name"],
        "invalidate_cache": True,
    }


@router.get("/{file_id}/download")
async def download(file_id: int = Path(..., gt=0), client=Depends(get_client)):
    output_dir = tempfile.mkdtemp(prefix="tsg_api_download_")

    def _cleanup_temp_dir(temp_path: str):
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                logger.debug("Failed to remove temp file: %s", temp_path, exc_info=True)
        shutil.rmtree(output_dir, ignore_errors=True)

    def _cleanup_stale_download_temps(prefix: str = "tsg_api_download_"):
        base_dir = tempfile.gettempdir()
        for name in os.listdir(base_dir):
            if name.startswith(prefix):
                candidate = os.path.join(base_dir, name)
                if os.path.isdir(candidate):
                    shutil.rmtree(candidate, ignore_errors=True)

    try:
        result = await download_adapter(client, file_id, output_dir)
    except TSGError:
        shutil.rmtree(output_dir, ignore_errors=True)
        raise

    path = result["path"]
    filename = os.path.basename(path)

    def _iter_file(chunk_size: int = 1024 * 1024):
        try:
            with open(path, "rb") as file_obj:
                while True:
                    chunk = file_obj.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        finally:
            _cleanup_temp_dir(path)
            if should_cleanup():
                _cleanup_stale_download_temps()

    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(
        _iter_file(),
        media_type="application/octet-stream",
        headers=headers,
    )
