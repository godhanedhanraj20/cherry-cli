import os
import tempfile
from contextlib import suppress
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

from api.dependencies.auth import get_client
from api.schemas.file import FileListResponse, FileSearchResponse, UploadResponse
from api.services_adapter.adapters import download_adapter, list_adapter, search_adapter, upload_adapter
from utils.errors import TSGError

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...), client=Depends(get_client)):
    if not file.filename:
        raise HTTPException(status_code=400, detail={"error": "No file provided"})
    return await upload_adapter(client, file)


@router.get("", response_model=FileListResponse)
async def list_files(
    limit: int = Query(50, ge=1, le=200),
    page: int = Query(1, ge=1),
    sort: str = Query("date"),
    type: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    client=Depends(get_client),
):
    return await list_adapter(client, limit=limit, page=page, sort=sort, file_type=type, tag=tag)


@router.get("/search", response_model=FileSearchResponse)
async def search(
    query: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    page: int = Query(1, ge=1),
    sort: str = Query("date"),
    type: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    client=Depends(get_client),
):
    if not any([query, type, tag]):
        raise HTTPException(status_code=400, detail={"error": "Provide query, type, or tag"})
    return await search_adapter(client, query=query, limit=limit, page=page, sort=sort, file_type=type, tag=tag)


@router.get("/{file_id}/download")
async def download(file_id: int, client=Depends(get_client)):
    output_dir = tempfile.mkdtemp(prefix="tsg_api_download_")
    try:
        result = await download_adapter(client, file_id, output_dir)
    except TSGError:
        with suppress(OSError):
            os.rmdir(output_dir)
        raise

    path = result["path"]
    filename = os.path.basename(path)

    def _cleanup():
        with suppress(OSError):
            if os.path.exists(path):
                os.remove(path)
        with suppress(OSError):
            os.rmdir(output_dir)

    file_stream = open(path, "rb")
    def _close_and_cleanup():
        file_stream.close()
        _cleanup()

    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(
        file_stream,
        media_type="application/octet-stream",
        headers=headers,
        background=BackgroundTask(_close_and_cleanup),
    )
