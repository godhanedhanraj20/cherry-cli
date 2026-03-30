import os
import tempfile
import time
import uuid
import logging
from contextlib import suppress
from typing import Optional

from fastapi import UploadFile
from pyrogram.errors import SessionPasswordNeeded

from api.schemas.file import FileItem
from services.auth import check_auth_status, setup_credentials
from services.file_service import delete_file, download_file, get_files, search_files, upload_file
from telegram.client import get_client as make_client
from utils.errors import TSGError

PENDING_AUTH_TTL_SECONDS = 300
MAX_PENDING_SESSIONS = 100
MAX_2FA_ATTEMPTS = 5
OTP_RATE_LIMIT_SECONDS = 30
_PENDING_AUTH: dict[str, dict] = {}
_LAST_OTP_REQUEST_TS: dict[str, float] = {}
logger = logging.getLogger(__name__)


def _noop_log_cb(_: str, __: str):
    return None


async def _cleanup_expired_sessions():
    now = time.time()
    expired = [(sid, data) for sid, data in _PENDING_AUTH.items() if data.get("created_at", 0) + PENDING_AUTH_TTL_SECONDS < now]
    for sid, _ in expired:
        del _PENDING_AUTH[sid]


async def send_otp_adapter(api_id: int, api_hash: str, phone_number: str):
    await _cleanup_expired_sessions()
    logger.info("Auth send_otp attempt for phone=%s", phone_number)
    last_request = _LAST_OTP_REQUEST_TS.get(phone_number)
    now = time.time()
    if last_request and now - last_request < OTP_RATE_LIMIT_SECONDS:
        raise TSGError("Too many OTP requests. Please wait before trying again.")
    if len(_PENDING_AUTH) >= MAX_PENDING_SESSIONS:
        raise TSGError("Too many pending auth sessions. Try again later.")
    await setup_credentials(api_id, api_hash)

    client = make_client(api_id, api_hash)
    try:
        await client.connect()
        sent_code = await client.send_code(phone_number)

        session_id = str(uuid.uuid4())
        _PENDING_AUTH[session_id] = {
            "api_id": api_id,
            "api_hash": api_hash,
            "phone_number": phone_number,
            "phone_code_hash": sent_code.phone_code_hash,
            "state": "otp_sent",
            "created_at": time.time(),
        }
        _LAST_OTP_REQUEST_TS[phone_number] = now
        return {"status": "otp_sent", "session_id": session_id}
    except Exception as exc:
        raise TSGError(f"Error sending code: {str(exc)}") from exc
    finally:
        with suppress(Exception):
            await client.disconnect()


async def verify_otp_adapter(session_id: str, otp: str):
    await _cleanup_expired_sessions()
    logger.info("Auth verify_otp attempt for session_id=%s", session_id)
    pending = _PENDING_AUTH.get(session_id)
    if not pending:
        raise TSGError("Invalid session_id. Send OTP first.")

    if pending.get("state") != "otp_sent":
        raise TSGError("OTP step is not pending for this session.")

    client = make_client(pending["api_id"], pending["api_hash"])
    try:
        await client.connect()
        await client.sign_in(pending["phone_number"], pending["phone_code_hash"], otp)
        me = await client.get_me()
        is_premium = bool(getattr(me, "is_premium", False))

        with suppress(KeyError):
            del _PENDING_AUTH[session_id]

        return {"status": "success", "is_premium": is_premium, "requires_2fa": False}
    except SessionPasswordNeeded:
        pending["state"] = "2fa_required"
        pending["created_at"] = time.time()
        pending["two_fa_attempts"] = 0
        return {
            "status": "2fa_required",
            "is_premium": False,
            "requires_2fa": True,
            "session_id": session_id,
        }
    except Exception as exc:
        with suppress(KeyError):
            del _PENDING_AUTH[session_id]
        raise TSGError(f"Invalid or expired code: {str(exc)}") from exc
    finally:
        with suppress(Exception):
            await client.disconnect()


async def two_fa_adapter(session_id: str, password: str):
    await _cleanup_expired_sessions()
    logger.info("Auth 2fa attempt for session_id=%s", session_id)
    pending = _PENDING_AUTH.get(session_id)
    if not pending:
        raise TSGError("Invalid session_id. Verify OTP first.")

    if pending.get("state") != "2fa_required":
        raise TSGError("2FA is not required for this session.")
    if pending.get("two_fa_attempts", 0) >= MAX_2FA_ATTEMPTS:
        with suppress(KeyError):
            del _PENDING_AUTH[session_id]
        raise TSGError("2FA attempt limit exceeded. Start login again.")

    client = make_client(pending["api_id"], pending["api_hash"])
    try:
        await client.connect()
        await client.check_password(password)
        me = await client.get_me()
        is_premium = bool(getattr(me, "is_premium", False))

        with suppress(KeyError):
            del _PENDING_AUTH[session_id]

        return {"status": "success", "is_premium": is_premium, "requires_2fa": False}
    except Exception as exc:
        pending["two_fa_attempts"] = pending.get("two_fa_attempts", 0) + 1
        if pending["two_fa_attempts"] >= MAX_2FA_ATTEMPTS:
            with suppress(KeyError):
                del _PENDING_AUTH[session_id]
            raise TSGError("2FA attempt limit exceeded. Start login again.") from exc
        raise TSGError(f"Invalid password: {str(exc)}") from exc
    finally:
        with suppress(Exception):
            await client.disconnect()


async def auth_status_adapter():
    status = await check_auth_status()
    return {
        "logged_in": bool(status.get("logged_in", False)),
        "is_premium": bool(status.get("is_premium", False)),
    }


async def upload_adapter(client, file: UploadFile):
    logger.info("Upload start filename=%s", file.filename)
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
        logger.info("Upload end filename=%s file_id=%s", file.filename, metadata.get("id"))
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
    return {"files": [FileItem(**f) for f in files]}


async def search_adapter(client, query: Optional[str], limit: int = 50, page: int = 1, sort: str = "date", file_type: Optional[str] = None, tag: Optional[str] = None):
    results = await search_files(client, query=query, limit=limit, page=page, sort_by=sort, file_type=file_type, tag=tag, debug=False)
    return {"results": [FileItem(**f) for f in results]}


async def download_adapter(client, file_id: int, output_path: str):
    logger.info("Download start file_id=%s", file_id)
    path = await download_file(client, file_id, output_path, _noop_log_cb)
    logger.info("Download end file_id=%s path=%s", file_id, path)
    return {"path": path}


async def delete_adapter(client, file_ids: list[int]):
    logger.info("Delete operation start file_ids=%s", file_ids)
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
    logger.info("Delete operation end deleted=%s failed=%s", deleted, failed)
    return payload
