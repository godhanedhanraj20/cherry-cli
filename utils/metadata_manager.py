import os
import json

CONFIG_DIR = os.path.expanduser("~/.tsg-cli")
METADATA_FILE = os.path.join(CONFIG_DIR, "metadata.json")

def ensure_config_dir():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

def load_metadata() -> dict:
    ensure_config_dir()
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_metadata(data: dict):
    ensure_config_dir()
    with open(METADATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def add_tag(file_id: str, tag: str):
    data = load_metadata()
    if file_id not in data:
        data[file_id] = {"tags": []}
        
    tags = data[file_id].get("tags", [])
    if tag not in tags:
        tags.append(tag)
        data[file_id]["tags"] = tags
        save_metadata(data)

def remove_tag(file_id: str, tag: str):
    data = load_metadata()
    if file_id in data:
        tags = data[file_id].get("tags", [])
        if tag in tags:
            tags.remove(tag)
            data[file_id]["tags"] = tags
            save_metadata(data)

def get_tags(file_id: str) -> list:
    data = load_metadata()
    if file_id in data:
        return data[file_id].get("tags", [])
    return []

def set_custom_name(file_id: str, name: str):
    data = load_metadata()
    entry = data.setdefault(file_id, {})
    entry["custom_name"] = name
    save_metadata(data)

def get_custom_name(file_id: str):
    data = load_metadata()
    return data.get(file_id, {}).get("custom_name")

def remove_custom_name(file_id: str):
    data = load_metadata()
    if file_id in data and "custom_name" in data[file_id]:
        del data[file_id]["custom_name"]
        save_metadata(data)
