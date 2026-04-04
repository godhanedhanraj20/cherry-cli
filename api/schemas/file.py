from typing import List, Literal, Optional

from pydantic import BaseModel, PositiveInt

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
    file_ids: List[PositiveInt]


class DeleteErrorItem(BaseModel):
    file_id: int
    error: str


class DeleteResponse(BaseModel):
    deleted: int
    failed: int
    errors: Optional[List[DeleteErrorItem]] = None
    invalidate_cache: Optional[bool] = None


class UpdateTagRequest(BaseModel):
    file_id: PositiveInt
    tag: str
    action: Optional[Literal["remove"]] = None


class UpdateTagResponse(BaseModel):
    success: bool
    file_id: int
    action: Literal["add", "remove"]
    tag: str
    invalidate_cache: bool = True


class RenameFileRequest(BaseModel):
    file_id: PositiveInt
    new_name: str


class RenameFileResponse(BaseModel):
    success: bool
    file_id: int
    custom_name: str
    invalidate_cache: bool = True
