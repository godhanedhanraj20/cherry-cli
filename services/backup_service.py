import json
import logging
import os
import shutil
from typing import Any

from pyrogram import Client

from utils.errors import TSGError
from utils.metadata_manager import METADATA_FILE, atomic_write_json, validate_metadata

logger = logging.getLogger(__name__)


async def backup_metadata(client: Client):
    if not os.path.exists(METADATA_FILE):
        raise TSGError("No metadata found to backup.")

    await client.send_document(
        "me",
        document=METADATA_FILE,
        caption="#TSG_METADATA_BACKUP",
        file_name="metadata_backup.json",
    )
    return {"status": "success", "invalidate_cache": True}


async def list_metadata_backups(client: Client) -> list[Any]:
    backups = []
    async for message in client.get_chat_history("me"):
        if message.document and getattr(message, "caption", None) and "#TSG_METADATA_BACKUP" in message.caption:
            backups.append(message)

    backups.sort(key=lambda x: x.date, reverse=True)
    return backups



def _cleanup_backup_temp_dir(temp_dir: str):
    shutil.rmtree(temp_dir, ignore_errors=True)


async def restore_metadata_backup(client: Client, backup_id: int | None = None):
    backups = await list_metadata_backups(client)
    if not backups:
        raise TSGError("No backup found")

    if backup_id is None:
        selected_backup = backups[0]
    else:
        selected_backup = next((b for b in backups if b.id == backup_id), None)
        if not selected_backup:
            raise TSGError("Invalid backup ID")

    temp_dir = os.path.expanduser("~/.tsg-cli/tmp_backup")
    os.makedirs(temp_dir, exist_ok=True)

    temp_file = os.path.join(temp_dir, "metadata_temp.json")
    downloaded_path = await client.download_media(selected_backup, file_name=temp_file)

    if not downloaded_path:
        _cleanup_backup_temp_dir(temp_dir)
        raise TSGError("Failed to download backup file.")

    try:
        with open(downloaded_path, "r") as f:
            payload = json.load(f)
        validate_metadata(payload)
    except Exception as exc:
        logger.error("Restore validation failed", exc_info=True)
        _cleanup_backup_temp_dir(temp_dir)
        raise TSGError("Backup file is corrupted") from exc

    try:
        atomic_write_json(METADATA_FILE, payload)
    except Exception as exc:
        logger.error("Restore write failed", exc_info=True)
        raise TSGError("Failed to restore metadata backup.") from exc
    finally:
        _cleanup_backup_temp_dir(temp_dir)

    return {"status": "success", "backup_id": selected_backup.id, "invalidate_cache": True}
