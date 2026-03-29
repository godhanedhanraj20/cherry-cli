import os
import json
from utils.errors import TSGError

CONFIG_DIR = os.path.expanduser("~/.tsg-cli")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
SESSION_FILE = os.path.join(CONFIG_DIR, "session") # Pyrogram appends .session

def ensure_config_dir():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

def load_config():
    ensure_config_dir()
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                raise TSGError("Config file is corrupted. Please delete ~/.tsg-cli/config.json and login again.")
    return {}

def save_config(config):
    ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
