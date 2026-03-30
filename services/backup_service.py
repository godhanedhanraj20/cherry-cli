import json
import os
from typing import Any

from pyrogram import Client

from utils.errors import TSGError
from utils.metadata_manager import METADATA_FILE


async def backup_metadata(client: Client):
    if not os.path.exists(METADATA_FILE):
        raise TSGError("No metadata found to backup.")

    await client.send_document(
        "me",
        document=METADATA_FILE,
        caption="#TSG_METADATA_BACKUP",
        file_name="metadata_backup.json",
    )
    return {"status": "success"}


async def list_metadata_backups(client: Client) -> list[Any]:
    backups = []
    async for message in client.get_chat_history("me"):
        if message.document and getattr(message, "caption", None) and "#TSG_METADATA_BACKUP" in message.caption:
            backups.append(message)

    backups.sort(key=lambda x: x.date, reverse=True)
    return backups


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
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    temp_file = os.path.join(temp_dir, "metadata_temp.json")
    downloaded_path = await client.download_media(selected_backup, file_name=temp_file)

    if not downloaded_path:
        raise TSGError("Failed to download backup file.")

    try:
        with open(downloaded_path, "r") as f:
            json.load(f)
    except Exception as exc:
        raise TSGError("Backup file is corrupted") from exc

    os.replace(downloaded_path, METADATA_FILE)

    try:
        os.rmdir(temp_dir)
    except OSError:
        pass

    return {"status": "success", "backup_id": selected_backup.id}
