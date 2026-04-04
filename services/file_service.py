import os
import time
import asyncio
import json
import random
from typing import List, Dict, Any, Callable
from pyrogram import Client
from utils.parser import extract_message_metadata, format_size
from utils.errors import TSGError
from utils.metadata_manager import get_custom_name

SEARCH_CACHE_TTL = 60
_SEARCH_CACHE: dict[tuple, tuple[float, list[dict[str, Any]]]] = {}


def _make_cache_key(query: str | None, tag: str | None, file_type: str | None, page: int, limit: int, sort_by: str | None):
    return (query or "", tag or "", file_type or "", page, limit, sort_by or "")


def _get_cached_search(key: tuple):
    cached = _SEARCH_CACHE.get(key)
    if not cached:
        return None
    ts, items = cached
    if time.time() - ts > SEARCH_CACHE_TTL:
        _SEARCH_CACHE.pop(key, None)
        return None
    return items


def _set_cached_search(key: tuple, items: list[dict[str, Any]]):
    _SEARCH_CACHE[key] = (time.time(), items)


def invalidate_search_cache():
    _SEARCH_CACHE.clear()


def _emit(log_cb: Callable[[str, str], None] | None, level: str, message: str):
    if log_cb:
        log_cb(level, message)

def load_checkpoint(file_path: str) -> int:
    cp_file = file_path + ".checkpoint"
    if os.path.exists(cp_file):
        with open(cp_file, "r") as f:
            try:
                data = json.load(f)
                return data.get("downloaded", 0)
            except Exception:
                return 0
    return 0

def save_checkpoint(file_path: str, downloaded: int):
    cp_file = file_path + ".checkpoint"
    with open(cp_file, "w") as f:
        json.dump({"downloaded": downloaded}, f)

def clear_checkpoint(file_path: str):
    cp_file = file_path + ".checkpoint"
    if os.path.exists(cp_file):
        try:
            os.remove(cp_file)
        except OSError:
            pass

async def upload_file(client: Client, file_path: str, log_cb: Callable[[str, str], None] = None) -> Dict[str, Any]:
    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        raise TSGError("File not found")
        
    try:
        if not client.is_connected:
            await client.connect()
            
        # Ensure client.me is populated
        if not getattr(client, "me", None):
            client.me = await client.get_me()
            
        is_premium = getattr(client.me, "is_premium", False)
        max_size = 4 * 1024 * 1024 * 1024 if is_premium else 2 * 1024 * 1024 * 1024
        
        file_size = os.path.getsize(abs_path)
        if file_size > max_size:
            limit_str = "4GB" if is_premium else "2GB"
            raise TSGError(f"File exceeds upload limit ({limit_str})")
            
        time_tracker = [time.time()]
    
        async def progress(current, total):
            elapsed = time.time() - time_tracker[0]
            elapsed = elapsed if elapsed > 0 else 1
            speed = current / elapsed
            
            c_fmt = format_size(current)
            t_fmt = format_size(total) if total > 0 else "?"
            s_fmt = format_size(speed)
            
            if total > 0:
                percent = current * 100 / total
                _emit(log_cb, "progress", f"Uploading: {percent:.2f}% ({c_fmt}/{t_fmt}) | {s_fmt}/s")
            else:
                _emit(log_cb, "progress", f"Uploading: ({c_fmt}) | {s_fmt}/s")
                
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                message = await client.send_document("me", document=abs_path, progress=progress)
                _emit(log_cb, "progress_done", "")
                
                metadata = extract_message_metadata(message)
                if not metadata:
                    raise TSGError("Failed to extract metadata after upload.")
                    
                invalidate_search_cache()
                return metadata
                
            except KeyboardInterrupt:
                _emit(log_cb, "progress_done", "")
                raise
            except TSGError as e:
                _emit(log_cb, "progress_done", "")
                raise e
            except Exception as e:
                _emit(log_cb, "progress_done", "")
                
                err_str = str(e).lower()
                is_transient = any(x in err_str for x in ["timeout", "connection", "network", "reset"])
                
                if attempt == max_retries - 1:
                    raise TSGError(f"Upload failed after retries: {str(e)}")
                    
                if not is_transient:
                    raise e
                    
                if log_cb:
                    log_cb("warn", f"Retrying upload... [{attempt+1}/{max_retries}]")
                
                await asyncio.sleep(2 * (attempt + 1))
                time_tracker[0] = time.time()
                
    except TSGError as e:
        raise e
    except Exception as e:
        raise TSGError(f"Upload failed: {str(e)}")

def _is_internal_file(metadata: Dict[str, Any]) -> bool:
    name = metadata.get("name", "")
    caption = metadata.get("caption", "")
    
    # Internal metadata file
    if name == "metadata.json" and "tsg-cli" in caption.lower():
        return True
    
    # Backup files
    if "#TSG_METADATA_BACKUP" in caption:
        return True
        
    return False

async def get_files(client: Client, limit: int = 50, sort_by: str = None, file_type: str = None, tag: str = None, page: int = 1, debug: bool = False) -> List[Dict[str, Any]]:
    return await search_files(client, query=None, limit=limit, file_type=file_type, sort_by=sort_by, tag=tag, page=page, debug=debug)

async def download_file(client: Client, file_id: int, output_directory: str, log_cb: Callable[[str, str], None] = None) -> str:
    try:
        message = await client.get_messages("me", file_id)
        if not message or getattr(message, "empty", False):
            raise TSGError(f"File with ID {file_id} not found.")
            
        metadata = extract_message_metadata(message)
        if not metadata:
            raise TSGError(f"Message ID {file_id} does not contain valid media.")
            
        custom_name = get_custom_name(str(file_id))
        if custom_name:
            final_name = custom_name
        else:
            final_name = getattr(message.document or message.video or message.audio or message.photo, "file_name", metadata['name'])

        file_path = os.path.join(output_directory, final_name)
        expected_size = metadata.get("raw_size", 0)
        
        # Start time tracking for progress speed calculation
        time_tracker = [time.time()]
        
        # Download the file with retries
        max_retries = 3
        download_success = False
        
        same_progress_count = 0
        last_downloaded = -1
        
        BUFFER_SIZE = 4 * 1024 * 1024  # 4MB
        CHECKPOINT_INTERVAL = 20 * 1024 * 1024  # 20MB
        LOG_INTERVAL = 100 * 1024 * 1024  # 100MB
        
        for attempt in range(max_retries):
            existing_size = load_checkpoint(file_path)
            
            if os.path.exists(file_path):
                file_sz = os.path.getsize(file_path)
                if file_sz > existing_size:
                    existing_size = file_sz
            else:
                existing_size = 0
                
            if existing_size > 0:
                if log_cb:
                    log_cb("info", f"Resuming download from {format_size(existing_size)}")
                
            if existing_size == last_downloaded:
                same_progress_count += 1
            else:
                same_progress_count = 0
                
            last_downloaded = existing_size
                
            if same_progress_count >= 3:
                raise TSGError("Download stuck at same point repeatedly. Possible network/CDN issue.")
                
            buffer = bytearray()
            last_checkpoint_size = existing_size
            last_log_size = existing_size
            
            try:
                mode = "ab" if existing_size > 0 else "wb"
                bytes_written = 0
                bytes_skipped = 0
                stream_yielded = False
                
                with open(file_path, mode) as f:
                    async for chunk in client.stream_media(message):
                        if not chunk:
                            continue
                            
                        stream_yielded = True
                        chunk_len = len(chunk)
                        
                        # Skip logic to simulate resume support natively
                        if bytes_skipped + chunk_len <= existing_size:
                            bytes_skipped += chunk_len
                            continue
                        elif bytes_skipped < existing_size:
                            # Write the remainder of the chunk
                            remainder = existing_size - bytes_skipped
                            buffer.extend(chunk[remainder:])
                            bytes_skipped += remainder
                            
                            written_chunk = chunk_len - remainder
                            bytes_written += written_chunk
                        else:
                            buffer.extend(chunk)
                            bytes_written += chunk_len
                            
                        downloaded_total = existing_size + bytes_written
                            
                        # Buffer system
                        if len(buffer) >= BUFFER_SIZE:
                            f.write(buffer)
                            buffer.clear()
                            
                            if downloaded_total - last_checkpoint_size >= CHECKPOINT_INTERVAL:
                                save_checkpoint(file_path, downloaded_total)
                                last_checkpoint_size = downloaded_total
                                
                            if downloaded_total - last_log_size >= LOG_INTERVAL:
                                if log_cb:
                                    log_cb("info", f"Checkpoint saved at {format_size(downloaded_total)}")
                                last_log_size = downloaded_total
                            
                        # Progress tracking
                        elapsed = time.time() - time_tracker[0]
                        speed = bytes_written / elapsed if elapsed > 0 else 0
                        speed_mb = speed / (1024 * 1024)
                        
                        c_fmt = format_size(downloaded_total)
                        t_fmt = format_size(expected_size) if expected_size > 0 else "?"
                        
                        if expected_size > 0:
                            percent = (downloaded_total / expected_size) * 100
                            _emit(log_cb, "progress", f"Downloading: {percent:.2f}% ({c_fmt}/{t_fmt}) | {speed_mb:.2f} MB/s")
                        else:
                            _emit(log_cb, "progress", f"Downloading: ({c_fmt}) | {speed_mb:.2f} MB/s")
                            
                    # After loop ends
                    if not stream_yielded and expected_size > 0 and existing_size == 0:
                        raise TSGError("Telegram stream error")
                        
                    if buffer:
                        f.write(buffer)
                        buffer.clear()
                        save_checkpoint(file_path, existing_size + bytes_written)
                        
                download_success = True
                break
                
            except KeyboardInterrupt:
                if buffer:
                    with open(file_path, "ab") as f:
                        f.write(buffer)
                    save_checkpoint(file_path, existing_size + bytes_written)
                raise
            except Exception as e:
                _emit(log_cb, "progress_done", "")
                if isinstance(e, TSGError) and "Telegram stream error" in str(e):
                    raise e
                
                # DO NOT delete file unless it's empty
                if os.path.exists(file_path) and os.path.getsize(file_path) == 0:
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass
                
                if attempt == max_retries - 1:
                    raise TSGError(f"Download failed after retries: {str(e)}")
                    
                if log_cb:
                    log_cb("warn", f"Stream interrupted, retrying... [{attempt+1}/{max_retries}]")
                
                delay = 2 * (attempt + 1) + random.random()
                await asyncio.sleep(delay)
                
                # Force message refetch
                message = await client.get_messages("me", file_id)
                if not message or getattr(message, "empty", False):
                    raise TSGError(f"File with ID {file_id} not found during retry.")
                    
                if not getattr(message, "document", None) and not getattr(message, "video", None) and not getattr(message, "audio", None) and not getattr(message, "photo", None):
                    raise TSGError("Download failed: message document missing")
                    
                if "Peer id invalid" in str(e):
                    chat = message.chat
                    await client.get_chat(chat.id)
                    
                # Reset start time AFTER retry
                time_tracker[0] = time.time()

        _emit(log_cb, "progress_done", "")
        
        if not download_success:
            raise TSGError("Download failed after retries")
            
        if not os.path.exists(file_path):
            raise TSGError("Download failed: file missing")
            
        final_size = os.path.getsize(file_path)
        actual_expected = getattr(message.document or message.video or message.audio or message.photo, "file_size", expected_size)
        if actual_expected > 0 and final_size < actual_expected:
            raise TSGError("Download incomplete: file size mismatch")
            
        clear_checkpoint(file_path)
        return file_path
    except KeyboardInterrupt:
        _emit(log_cb, "progress_done", "")
        raise TSGError("Download cancelled by user")
    except TSGError as e:
        raise e
    except Exception as e:
        raise TSGError(f"Download failed: {str(e)}")

async def delete_file(client: Client, file_id: int):
    try:
        message = await client.get_messages("me", file_id)
        if not message or getattr(message, "empty", False):
            raise TSGError(f"File with ID {file_id} not found.")
            
        metadata = extract_message_metadata(message)
        if not metadata:
            raise TSGError(f"Message ID {file_id} does not contain valid media.")
            
        await client.delete_messages("me", file_id)
        invalidate_search_cache()
    except TSGError as e:
        raise e
    except Exception as e:
        raise TSGError(f"Delete failed: {str(e)}")

def _matches_type(file_name: str, file_type: str) -> bool:
    ext = file_name.split(".")[-1].lower() if "." in file_name else ""
    if file_type == "video":
        return ext in ["mp4", "mkv", "avi"]
    elif file_type == "image":
        return ext in ["jpg", "jpeg", "png"]
    elif file_type == "document":
        return ext in ["pdf", "txt", "csv"]
    elif file_type == "audio":
        return ext in ["mp3", "wav", "ogg", "flac"]
    return False

async def search_files(client: Client, query: str, limit: int = 50, file_type: str = None, sort_by: str = None, tag: str = None, page: int = 1, debug: bool = False) -> List[Dict[str, Any]]:
    # Enforce max limit = 200
    if limit > 200:
        limit = 200
        
    start = (page - 1) * limit
    end = start + limit
        
    query = query.strip().lower() if query else None
    tag = tag.strip().lower() if tag else None
    file_type = file_type.strip().lower() if file_type else None

    cache_key = _make_cache_key(query, tag, file_type, page, limit, sort_by)
    cached_items = _get_cached_search(cache_key)
    if cached_items is not None:
        return cached_items

    files = []
    try:
        # Fetch newest first (default in Pyrogram)
        async for message in client.get_chat_history("me"):
            if getattr(message, "empty", False) or getattr(message, "service", False):
                continue
                
            metadata = extract_message_metadata(message)
            if not metadata:
                continue
                
            file_name = metadata.get("name", "").lower()
            
            # Hide internal files
            if _is_internal_file(metadata):
                continue

            # AND logic: Name-based filtering
            if query and query not in file_name:
                continue

            # AND logic: Tag-based filtering
            if tag:
                raw_tags = metadata.get("tags") or []
                if isinstance(raw_tags, str):
                    raw_tags = [t.strip() for t in raw_tags.split(",")] if raw_tags != "-" else []
                tags_list = [t.lower() for t in raw_tags if t.strip()]
                
                if tag not in tags_list:
                    continue

            # AND logic: Type-based filtering (using extension fallback to mimic Pyrogram attributes safely)
            if file_type:
                # Also double check Pyrogram native types as a primary source if they exist
                has_native = False
                if file_type == "video" and getattr(message, "video", None): has_native = True
                elif file_type == "image" and getattr(message, "photo", None): has_native = True
                elif file_type == "document" and getattr(message, "document", None): has_native = True
                elif file_type == "audio" and getattr(message, "audio", None): has_native = True
                
                # If neither native Pyrogram type matches nor extension matches, skip
                if not has_native and not _matches_type(file_name, file_type):
                    continue

            files.append(metadata)
            if len(files) >= end:
                break
    except Exception as e:
        raise TSGError(f"Failed to search files: {str(e)}")
        
    if sort_by == "date":
        files.sort(key=lambda x: x["date"], reverse=True)
    elif sort_by == "size":
        files.sort(key=lambda x: x["raw_size"], reverse=True)
    elif sort_by == "name":
        files.sort(key=lambda x: x["name"].lower())

    paginated_items = files[start:end]
    _set_cached_search(cache_key, paginated_items)
    return paginated_items
