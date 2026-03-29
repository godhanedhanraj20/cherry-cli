from typing import List, Literal, Optional

from pydantic import BaseModel


SortValue = Literal["date", "name", "size"]
FileTypeValue = Literal["video", "image", "document", "audio"]


class FileItem(BaseModel):
    id: int
    name: str
    size: str
    date: str
    tags: str = "-"
    raw_size: int = 0
    caption: str = ""


class UploadResponse(BaseModel):
    file_id: int
    name: str
    size: str


class FileListResponse(BaseModel):
    files: List[FileItem]


class FileSearchResponse(BaseModel):
    results: List[FileItem]


class DeleteRequest(BaseModel):
    file_ids: List[int]


class DeleteErrorItem(BaseModel):
    file_id: int
    error: str


class DeleteResponse(BaseModel):
    deleted: int
    failed: int
    errors: Optional[List[DeleteErrorItem]] = None
