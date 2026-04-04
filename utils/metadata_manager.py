import json
import logging
import os
import tempfile
from typing import Any, Callable

import portalocker

from utils.errors import TSGError

logger = logging.getLogger(__name__)

CONFIG_DIR = os.path.expanduser("~/.tsg-cli")
METADATA_FILE = os.path.join(CONFIG_DIR, "metadata.json")



def ensure_config_dir():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)



def get_lock_path(metadata_path: str):
    return metadata_path + ".lock"



def validate_metadata(data: Any):
    if not isinstance(data, dict):
        logger.error("Metadata validation failed: invalid top-level format")
        raise TSGError("Invalid metadata format")

    for key, value in data.items():
        if not isinstance(value, dict):
            logger.error("Metadata validation failed: invalid entry type for file_id=%s", key)
            raise TSGError(f"Invalid entry for file_id {key}")

        if "name" not in value or not isinstance(value["name"], str):
            logger.error("Metadata validation failed: missing/invalid name for file_id=%s", key)
            raise TSGError(f"Invalid or missing name for file_id {key}")

        if "tags" in value and not isinstance(value["tags"], list):
            logger.error("Metadata validation failed: invalid tags for file_id=%s", key)
            raise TSGError(f"Tags must be a list for file_id {key}")

        if "custom_name" in value and not isinstance(value["custom_name"], str):
            logger.error("Metadata validation failed: invalid custom_name for file_id=%s", key)
            raise TSGError(f"Invalid custom_name for file_id {key}")



def atomic_write_json(file_path: str, data: dict):
    ensure_config_dir()
    validate_metadata(data)

    temp_name = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=os.path.dirname(file_path), delete=False) as tmp:
            json.dump(data, tmp, indent=4)
            tmp.flush()
            os.fsync(tmp.fileno())
            temp_name = tmp.name

        os.replace(temp_name, file_path)
    except Exception:
        if temp_name and os.path.exists(temp_name):
            os.remove(temp_name)
        raise



def _read_metadata_unlocked() -> dict:
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r") as f:
            try:
                payload = json.load(f)
            except json.JSONDecodeError as exc:
                logger.error("Metadata JSON decode failed", exc_info=True)
                raise TSGError("Invalid metadata format") from exc
            validate_metadata(payload)
            return payload
    return {}



def _with_metadata_lock(fn: Callable[[dict], Any]):
    ensure_config_dir()
    lock_path = get_lock_path(METADATA_FILE)
    try:
        with portalocker.Lock(lock_path, timeout=5):
            data = _read_metadata_unlocked()
            return fn(data)
    except portalocker.exceptions.LockException as exc:
        logger.error("Metadata lock timeout", exc_info=True)
        raise TSGError("Metadata is busy, please try again.") from exc



def load_metadata() -> dict:
    def _loader(data: dict):
        return data

    return _with_metadata_lock(_loader)



def save_metadata(data: dict):
    def _saver(_: dict):
        atomic_write_json(METADATA_FILE, data)

    _with_metadata_lock(_saver)



def _ensure_entry(data: dict, file_id: str):
    entry = data.setdefault(file_id, {})
    if "name" not in entry or not isinstance(entry["name"], str):
        entry["name"] = file_id
    return entry



def add_tag(file_id: str, tag: str):
    if not file_id:
        raise TSGError("Invalid file_id")
    normalized_tag = (tag or "").strip().lower()
    if not normalized_tag:
        raise TSGError("Invalid tag")
    if len(normalized_tag) > 50:
        raise TSGError("Tag too long")

    def _mutator(data: dict):
        entry = _ensure_entry(data, file_id)
        tags = entry.get("tags", [])
        if normalized_tag not in tags:
            tags.append(normalized_tag)
            entry["tags"] = tags
            atomic_write_json(METADATA_FILE, data)

    _with_metadata_lock(_mutator)



def remove_tag(file_id: str, tag: str):
    if not file_id:
        raise TSGError("Invalid file_id")
    normalized_tag = (tag or "").strip().lower()
    if not normalized_tag:
        raise TSGError("Invalid tag")
    if len(normalized_tag) > 50:
        raise TSGError("Tag too long")

    def _mutator(data: dict):
        if file_id in data:
            entry = _ensure_entry(data, file_id)
            tags = entry.get("tags", [])
            if normalized_tag in tags:
                tags.remove(normalized_tag)
                entry["tags"] = tags
                atomic_write_json(METADATA_FILE, data)

    _with_metadata_lock(_mutator)



def get_tags(file_id: str) -> list:
    if not file_id:
        raise TSGError("Invalid file_id")

    def _getter(data: dict):
        if file_id in data:
            return data[file_id].get("tags", [])
        return []

    return _with_metadata_lock(_getter)



def set_custom_name(file_id: str, name: str):
    if not file_id:
        raise TSGError("Invalid file_id")
    if not name or not name.strip():
        raise TSGError("Invalid filename")

    def _mutator(data: dict):
        entry = _ensure_entry(data, file_id)
        entry["custom_name"] = name.strip()
        atomic_write_json(METADATA_FILE, data)

    _with_metadata_lock(_mutator)



def get_custom_name(file_id: str):
    if not file_id:
        raise TSGError("Invalid file_id")

    def _getter(data: dict):
        return data.get(file_id, {}).get("custom_name")

    return _with_metadata_lock(_getter)



def remove_custom_name(file_id: str):
    if not file_id:
        raise TSGError("Invalid file_id")

    def _mutator(data: dict):
        if file_id in data and "custom_name" in data[file_id]:
            del data[file_id]["custom_name"]
            _ensure_entry(data, file_id)
            atomic_write_json(METADATA_FILE, data)

    _with_metadata_lock(_mutator)
