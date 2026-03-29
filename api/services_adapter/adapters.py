import os
import tempfile
from contextlib import suppress
from typing import Optional

from fastapi import UploadFile
from pyrogram.errors import SessionPasswordNeeded

from services.auth import check_auth_status, setup_credentials
from services.file_service import delete_file, download_file, get_files, search_files, upload_file
from telegram.client import get_client as make_client
from utils.errors import TSGError

_PENDING_OTP: dict[str, dict] = {}
_PENDING_2FA: dict[str, object] = {}
_LAST_2FA_PHONE: Optional[str] = None


def _noop_log_cb(_: str, __: str):
    return None


async def send_otp_adapter(api_id: int, api_hash: str, phone_number: str):
    await setup_credentials(api_id, api_hash)

    client = make_client(api_id, api_hash)
    try:
        await client.connect()
        sent_code = await client.send_code(phone_number)
        _PENDING_OTP[phone_number] = {
            "api_id": api_id,
            "api_hash": api_hash,
            "phone_code_hash": sent_code.phone_code_hash,
            "client": client,
        }
        return {"status": "otp_sent", "is_premium": False, "requires_2fa": False}
    except Exception as exc:
        with suppress(Exception):
            await client.disconnect()
        raise TSGError(f"Error sending code: {str(exc)}") from exc


async def verify_otp_adapter(phone_number: str, otp: str):
    global _LAST_2FA_PHONE

    pending = _PENDING_OTP.get(phone_number)
    if not pending:
        raise TSGError("No pending OTP session for this phone number. Send OTP first.")

    client = pending["client"]
    try:
        await client.sign_in(phone_number, pending["phone_code_hash"], otp)
        me = await client.get_me()
        is_premium = bool(getattr(me, "is_premium", False))

        with suppress(KeyError):
            del _PENDING_OTP[phone_number]
        with suppress(Exception):
            await client.disconnect()

        return {"status": "success", "is_premium": is_premium, "requires_2fa": False}
    except SessionPasswordNeeded:
        _PENDING_2FA[phone_number] = client
        _LAST_2FA_PHONE = phone_number
        with suppress(KeyError):
            del _PENDING_OTP[phone_number]
        return {"status": "2fa_required", "is_premium": False, "requires_2fa": True}
    except Exception as exc:
        with suppress(Exception):
            await client.disconnect()
        with suppress(KeyError):
            del _PENDING_OTP[phone_number]
        raise TSGError(f"Invalid or expired code: {str(exc)}") from exc


async def two_fa_adapter(password: str):
    global _LAST_2FA_PHONE

    if not _LAST_2FA_PHONE or _LAST_2FA_PHONE not in _PENDING_2FA:
        raise TSGError("No pending 2FA session. Verify OTP first.")

    phone_number = _LAST_2FA_PHONE
    client = _PENDING_2FA[phone_number]
    try:
        await client.check_password(password)
        me = await client.get_me()
        is_premium = bool(getattr(me, "is_premium", False))

        with suppress(KeyError):
            del _PENDING_2FA[phone_number]
        _LAST_2FA_PHONE = None
        with suppress(Exception):
            await client.disconnect()

        return {"status": "success", "is_premium": is_premium, "requires_2fa": False}
    except Exception as exc:
        raise TSGError(f"Invalid password: {str(exc)}") from exc


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
