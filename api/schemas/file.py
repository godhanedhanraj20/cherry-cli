from typing import List, Optional

from pydantic import BaseModel


class UploadResponse(BaseModel):
    file_id: int
    name: str
    size: str


class FileListResponse(BaseModel):
    files: List[dict]


class FileSearchResponse(BaseModel):
    results: List[dict]


class DeleteRequest(BaseModel):
    file_ids: List[int]


class DeleteResponse(BaseModel):
    deleted: int
    failed: int
    errors: Optional[List[dict]] = None
