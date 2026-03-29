import os
import tempfile
from contextlib import suppress
from typing import Optional

from fastapi import UploadFile

from services.auth import authenticate_user, check_auth_status, setup_credentials
from services.file_service import delete_file, download_file, get_files, search_files, upload_file
from utils.errors import TSGError


def _noop_log_cb(_: str, __: str):
    return None


async def login_adapter(api_id: int, api_hash: str, phone_number: str, otp: str, password: Optional[str] = None):
    await setup_credentials(api_id, api_hash)

    answers = {
        "Enter your phone number (e.g., +1234567890)": phone_number,
        "Enter the OTP code received on Telegram": otp,
        "Two-Step Verification enabled. Enter your password": password or "",
    }

    def prompt_cb(text: str, is_password: bool):
        del is_password
        if text in answers:
            return answers[text]
        raise TSGError(f"Unexpected authentication prompt: {text}")

    result = await authenticate_user(prompt_cb=prompt_cb, log_cb=_noop_log_cb)
    return {
        "status": result.get("status", "success"),
        "is_premium": bool(result.get("is_premium", False)),
    }


async def auth_status_adapter():
    status = await check_auth_status()
    return {
        "logged_in": bool(status.get("logged_in", False)),
        "is_premium": bool(status.get("is_premium", False)),
    }


async def upload_adapter(client, file: UploadFile):
    suffix = os.path.splitext(file.filename or "upload.bin")[-1]
    fd, tmp_path = tempfile.mkstemp(prefix="tsg_api_upload_", suffix=suffix)
    os.close(fd)

    try:
        with open(tmp_path, "wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)

        metadata = await upload_file(client, tmp_path, _noop_log_cb)
        return {
            "file_id": metadata["id"],
            "name": metadata["name"],
            "size": metadata["size"],
        }
    finally:
        await file.close()
        with suppress(OSError):
            os.remove(tmp_path)


async def list_adapter(client, limit: int = 50, page: int = 1, sort: str = "date", file_type: Optional[str] = None, tag: Optional[str] = None):
    files = await get_files(client, limit=limit, page=page, sort_by=sort, file_type=file_type, tag=tag, debug=False)
    return {"files": files}


async def search_adapter(client, query: Optional[str], limit: int = 50, page: int = 1, sort: str = "date", file_type: Optional[str] = None, tag: Optional[str] = None):
    results = await search_files(client, query=query, limit=limit, page=page, sort_by=sort, file_type=file_type, tag=tag, debug=False)
    return {"results": results}


async def download_adapter(client, file_id: int, output_path: str):
    path = await download_file(client, file_id, output_path, _noop_log_cb)
    return {"path": path}


async def delete_adapter(client, file_ids: list[int]):
    deleted = 0
    failed = 0
    errors = []
    for fid in file_ids:
        try:
            await delete_file(client, int(fid))
            deleted += 1
        except Exception as exc:
            failed += 1
            errors.append({"file_id": int(fid), "error": str(exc)})

    payload = {"deleted": deleted, "failed": failed}
    if errors:
        payload["errors"] = errors
    return payload
