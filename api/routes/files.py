import os
import tempfile
from contextlib import suppress
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Path, Query, UploadFile
from fastapi.responses import StreamingResponse

from api.dependencies.auth import get_client
from api.schemas.file import FileListResponse, FileSearchResponse, FileTypeValue, SortValue, UploadResponse
from api.services_adapter.adapters import download_adapter, list_adapter, search_adapter, upload_adapter
from utils.errors import TSGError

router = APIRouter(prefix="/files", tags=["files"])


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


@router.get("/{file_id}/download")
async def download(file_id: int = Path(..., gt=0), client=Depends(get_client)):
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

    def _iter_file(chunk_size: int = 1024 * 1024):
        cleaned = False
        def _safe_cleanup():
            nonlocal cleaned
            if not cleaned:
                _cleanup()
                cleaned = True
        try:
            with open(path, "rb") as file_obj:
                while True:
                    chunk = file_obj.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        except Exception:
            _safe_cleanup()
            raise
        finally:
            _safe_cleanup()

    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(
        _iter_file(),
        media_type="application/octet-stream",
        headers=headers,
    )
