import json
import os
import tempfile
from typing import Any, Callable

import portalocker

from utils.errors import TSGError

CONFIG_DIR = os.path.expanduser("~/.tsg-cli")
METADATA_FILE = os.path.join(CONFIG_DIR, "metadata.json")
METADATA_LOCK_FILE = f"{METADATA_FILE}.lock"



def ensure_config_dir():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)



def validate_metadata(data: Any):
    if not isinstance(data, dict):
        raise ValueError("Invalid metadata")

    for _, value in data.items():
        if not isinstance(value, dict):
            raise ValueError("Invalid entry")
        if "name" in value and not isinstance(value["name"], str):
            raise ValueError("Invalid name")
        tags = value.get("tags", [])
        if tags is not None and not isinstance(tags, list):
            raise ValueError("Invalid tags")



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
                validate_metadata(payload)
                return payload
            except (json.JSONDecodeError, ValueError):
                return {}
    return {}



def _with_metadata_lock(fn: Callable[[dict], Any]):
    ensure_config_dir()
    try:
        with portalocker.Lock(METADATA_LOCK_FILE, timeout=5):
            data = _read_metadata_unlocked()
            return fn(data)
    except portalocker.exceptions.LockException as exc:
        raise TSGError("Metadata is busy, please try again.") from exc



def load_metadata() -> dict:
    def _loader(data: dict):
        return data

    return _with_metadata_lock(_loader)



def save_metadata(data: dict):
    def _saver(_: dict):
        atomic_write_json(METADATA_FILE, data)

    _with_metadata_lock(_saver)



def add_tag(file_id: str, tag: str):
    if not file_id:
        raise ValueError("Invalid file_id")
    normalized_tag = (tag or "").strip().lower()
    if not normalized_tag:
        raise ValueError("Invalid tag")
    if len(normalized_tag) > 50:
        raise ValueError("Tag too long")

    def _mutator(data: dict):
        if file_id not in data:
            data[file_id] = {}

        tags = data[file_id].get("tags", [])
        if normalized_tag not in tags:
            tags.append(normalized_tag)
            data[file_id]["tags"] = tags
            validate_metadata(data)
            atomic_write_json(METADATA_FILE, data)

    _with_metadata_lock(_mutator)



def remove_tag(file_id: str, tag: str):
    if not file_id:
        raise ValueError("Invalid file_id")
    normalized_tag = (tag or "").strip().lower()
    if not normalized_tag:
        raise ValueError("Invalid tag")
    if len(normalized_tag) > 50:
        raise ValueError("Tag too long")

    def _mutator(data: dict):
        if file_id in data:
            tags = data[file_id].get("tags", [])
            if normalized_tag in tags:
                tags.remove(normalized_tag)
                data[file_id]["tags"] = tags
                validate_metadata(data)
                atomic_write_json(METADATA_FILE, data)

    _with_metadata_lock(_mutator)



def get_tags(file_id: str) -> list:
    if not file_id:
        raise ValueError("Invalid file_id")

    def _getter(data: dict):
        if file_id in data:
            return data[file_id].get("tags", [])
        return []

    return _with_metadata_lock(_getter)



def set_custom_name(file_id: str, name: str):
    if not file_id:
        raise ValueError("Invalid file_id")
    if not name or not name.strip():
        raise ValueError("Invalid filename")

    def _mutator(data: dict):
        entry = data.setdefault(file_id, {})
        entry["custom_name"] = name.strip()
        validate_metadata(data)
        atomic_write_json(METADATA_FILE, data)

    _with_metadata_lock(_mutator)



def get_custom_name(file_id: str):
    if not file_id:
        raise ValueError("Invalid file_id")

    def _getter(data: dict):
        return data.get(file_id, {}).get("custom_name")

    return _with_metadata_lock(_getter)



def remove_custom_name(file_id: str):
    if not file_id:
        raise ValueError("Invalid file_id")

    def _mutator(data: dict):
        if file_id in data and "custom_name" in data[file_id]:
            del data[file_id]["custom_name"]
            validate_metadata(data)
            atomic_write_json(METADATA_FILE, data)

    _with_metadata_lock(_mutator)
