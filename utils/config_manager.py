import json
import os
import tempfile

from utils.errors import TSGError

CONFIG_DIR = os.path.expanduser("~/.tsg-cli")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
SESSION_FILE = os.path.join(CONFIG_DIR, "session")  # Pyrogram appends .session



def ensure_config_dir():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)



def load_config():
    ensure_config_dir()
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as exc:
                raise TSGError("Config file is corrupted. Please delete ~/.tsg-cli/config.json and login again.") from exc
    return {}



def save_config(config):
    ensure_config_dir()
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=CONFIG_DIR, delete=False) as tmp:
            json.dump(config, tmp, indent=4)
            tmp.flush()
            os.fsync(tmp.fileno())
            temp_name = tmp.name
        os.replace(temp_name, CONFIG_FILE)
    except Exception as exc:
        if temp_name and os.path.exists(temp_name):
            os.remove(temp_name)
        raise TSGError("Failed to save config safely") from exc
