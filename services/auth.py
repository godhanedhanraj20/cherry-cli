import asyncio
from typing import Dict, Any, Callable
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneCodeExpired
import os

from utils.config_manager import load_config, save_config, SESSION_FILE
from telegram.client import get_client
from utils.errors import TSGError

async def check_auth_status() -> Dict[str, Any]:
    """Check if the user is already logged in and return status + limits."""
    config = load_config()
    api_id = config.get("api_id")
    api_hash = config.get("api_hash")
    
    if not api_id or not api_hash:
        return {"logged_in": False, "needs_setup": True}
        
    client = get_client(api_id, api_hash)
    
    try:
        await client.connect()
    except Exception:
        await client.disconnect()
        await client.connect()
        
    try:
        me = await client.get_me()
        if me:
            is_premium = getattr(me, "is_premium", False)
            limit = "4GB" if is_premium else "2GB"
            return {"logged_in": True, "needs_setup": False, "is_premium": is_premium, "limit": limit}
    except Exception:
        pass # Not logged in
    finally:
        await client.disconnect()
        
    return {"logged_in": False, "needs_setup": False}

async def setup_credentials(api_id: int, api_hash: str):
    """Save API credentials locally."""
    config = load_config()
    config["api_id"] = api_id
    config["api_hash"] = api_hash
    save_config(config)

async def send_login_code(phone_number: str) -> str:
    """Send login code to the phone number and return phone_code_hash."""
    config = load_config()
    client = get_client(config.get("api_id"), config.get("api_hash"))
    
    try:
        await client.connect()
    except Exception:
        await client.disconnect()
        await client.connect()
        
    try:
        sent_code = await client.send_code(phone_number)
        return sent_code.phone_code_hash
    except Exception as e:
        raise TSGError(f"Error sending code: {str(e)}")
    finally:
        # Keep client connected, but disconnect if we fail completely here?
        # Actually Pyrogram needs to stay alive for sign_in, but this CLI splits operations.
        # Wait, if we disconnect, sign_in needs a fresh connection and might fail if we don't keep it open.
        # So we need a persistent interactive session logic, or pass the client object.
        await client.disconnect()

# Instead of splitting it into pure functions that drop connections, we'll expose 
# a generator or async sequence so the CLI can handle prompts while keeping Pyrogram open.
# Or, the simplest architectural refactor is to pass a prompt callback to the service layer.

async def authenticate_user(prompt_cb: Callable[[str, bool], str], log_cb: Callable[[str, str], None] = None) -> Dict[str, Any]:
    """Perform full interactive login without printing directly to console."""
    config = load_config()
    
    api_id = config.get("api_id")
    api_hash = config.get("api_hash")
    
    if not api_id or not api_hash:
        if log_cb: log_cb("info", "First time setup: Enter your Telegram API credentials.")
        if log_cb: log_cb("dim", "You can get these from https://my.telegram.org/apps")
        api_id_str = prompt_cb("API ID", False)
        api_hash = prompt_cb("API Hash", False)
        
        try:
            api_id = int(api_id_str)
        except ValueError:
            raise TSGError("API ID must be an integer.")
            
        config["api_id"] = api_id
        config["api_hash"] = api_hash
        save_config(config)
    
    client = get_client(api_id, api_hash)
    
    if log_cb: log_cb("info", "Connecting to Telegram...")
    try:
        await client.connect()
    except Exception:
        await client.disconnect()
        await client.connect()
    
    try:
        try:
            me = await client.get_me()
            if me:
                is_premium = getattr(me, "is_premium", False)
                return {
                    "status": "already_logged_in", 
                    "is_premium": is_premium,
                    "limit": "4GB" if is_premium else "2GB"
                }
        except Exception:
            pass # Not logged in
        
        phone_number = prompt_cb("Enter your phone number (e.g., +1234567890)", False)
        
        try:
            sent_code = await client.send_code(phone_number)
        except Exception as e:
            raise TSGError(f"Error sending code: {str(e)}")

        phone_code = prompt_cb("Enter the OTP code received on Telegram", False)
        
        try:
            await client.sign_in(phone_number, sent_code.phone_code_hash, phone_code)
        except SessionPasswordNeeded:
            password = prompt_cb("Two-Step Verification enabled. Enter your password", True)
            try:
                await client.check_password(password)
            except Exception as e:
                raise TSGError(f"Invalid password: {str(e)}")
        except (PhoneCodeInvalid, PhoneCodeExpired) as e:
            raise TSGError(f"Invalid or expired code: {str(e)}")
        except Exception as e:
            raise TSGError(f"Failed to sign in: {str(e)}")

        # Show limit logic on fresh login
        is_premium = False
        try:
            me = await client.get_me()
            is_premium = getattr(me, "is_premium", False)
        except Exception:
            pass
            
        return {
            "status": "success", 
            "is_premium": is_premium,
            "limit": "4GB" if is_premium else "2GB"
        }
            
    finally:
        await client.disconnect()

async def get_authenticated_client() -> Client:
    config = load_config()
    api_id = config.get("api_id")
    api_hash = config.get("api_hash")
    if not api_id or not api_hash:
        raise TSGError("You are not logged in. Run: tsg-cli login")
    
    client = get_client(api_id, api_hash)
    try:
        await client.connect()
        user = await client.get_me()
        client.me = user  # Fix: Ensure Pyrogram internal state is fully initialized
        
        if not user:
            await client.disconnect()
            raise TSGError("Authentication failed. Please login again.")
        return client
    except Exception as e:
        if isinstance(e, TSGError):
            raise e
        raise TSGError("You are not logged in. Run: tsg-cli login")
