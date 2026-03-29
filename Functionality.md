# TSG-CLI Functionality


## 1. Introduction

This document provides a complete breakdown of all CLI commands and core system functionalities available in TSG-CLI (Phase 4).

---

## 2. Authentication

**Command:** `login`

The CLI requires an initial login sequence to authenticate with the Telegram API.

* OTP-based login
* 2FA support
* Session persistence

**Example:**
```bash
python main.py login
```

**Behavior:**
* Prompts for phone number
* Prompts for OTP (sent to your Telegram app)
* Prompts for 2FA password (if enabled on your account)
* Saves session locally for reuse in future commands

---

## 3. File Operations

### 3.1 Upload

**Command:**
```bash
python main.py upload <file_paths>
```

**Features:**
* Single file upload
* Batch upload
* Folder upload (recursive)
* File validation (size limits)
* Progress display
* Retry on failure

**Examples:**
```bash
python main.py upload file.mp4
python main.py upload file1.mp4 file2.mp4
python main.py upload ./movies/
```

**Behavior:**
* Automatically detects files vs folders
* Expands folders recursively
* Skips missing files
* Shows progress and speed

### 3.2 Download

**Command:**
```bash
python main.py download <file_ids>
```

**Features:**
* Single file download
* Batch download
* Resume support
* Retry logic
* Partial file cleanup

**Examples:**
```bash
python main.py download 12345
python main.py download 12345 67890
```

**Behavior:**
* Resumes from checkpoint
* Retries on network failure
* Displays progress + speed

### 3.3 Delete

**Command:**
```bash
python main.py delete <file_ids>
```

**Features:**
* Batch delete
* Confirmation prompt

**Example:**
```bash
python main.py delete 12345 67890
```

**Behavior:**
* Asks confirmation before deleting
* Reports success/failed count

---

## 4. Search & Filter

**Command:** `search`

**Features:**
* Query-based search
* Tag filtering
* File type filtering
* Combined filters

**Examples:**
```bash
python main.py search --query "movie"
python main.py search --tag anime
python main.py search --type video
```

---

## 5. Listing

**Command:** `list`

**Features:**
* Displays stored files
* Pagination support
* Sorting support

**Examples:**
```bash
python main.py list
python main.py list --limit 20
```

---

## 6. Tagging System

**Command:** `tag`

**Features:**
* Add tags
* Remove tags
* Batch tagging

**Examples:**
```bash
python main.py tag 12345 add anime
python main.py tag 12345,67890 remove anime
```

**Behavior:**
* Updates local metadata
* Supports processing multiple file IDs at once

---

## 7. Virtual Folder System

The virtual folder system provides path-based organization without relying on physical folders on Telegram. It is entirely metadata-driven.

**Command:** `mkdir`

**Example:**
```bash
python main.py mkdir /movies/action/
```

**Behavior:**
* Creates a virtual folder (metadata only)

**Command:** `move`

**Example:**
```bash
python main.py move 12345 /movies/action/
```

**Behavior:**
* Updates file path in metadata to place the file in the virtual folder

**Command:** `ls`

**Example:**
```bash
python main.py ls /movies/
```

**Behavior:**
* Lists files and subfolders within the virtual path
* Uses path prefix logic for organization

---

## 8. Batch Operations

The CLI natively supports batch operations for efficiency:
* Upload
* Download
* Delete
* Tag

**Behavior:**
* Handles partial failures (if one file fails, the others continue)
* Shows a summary upon completion:
  * Success: X
  * Failed: Y

---

## 9. Retry & Resilience

The core system is built to handle network instability:
* Upload retry logic
* Download retry logic
* Resume support (downloads resume from the last saved byte)
* Network failure handling gracefully attempts to recover

---

## 10. Metadata System

All organizational data is stored locally.

* Local metadata storage (typically `~/.tsg-cli/metadata.json`)
* Stores:
  * `file_id`
  * `name`
  * `size`
  * `path`
  * `tags`

---

## 11. Backup & Restore

Local metadata can be backed up and restored to easily migrate or secure the virtual file structure.

**Backup Metadata:**
```bash
python main.py backup
```

**Restore Metadata:**
```bash
python main.py restore
```

---

## 12. Error Handling

The system ensures strict handling of unexpected conditions:
* Graceful failures (no raw stack traces on common errors)
* Partial batch failures (reports what failed without crashing the run)
* `KeyboardInterrupt` handling safely closes buffers to prevent file corruption when pressing Ctrl+C

---

## 13. Limitations

* Depends on Telegram API limits (2GB free / 4GB premium)
* No real folders (virtual only, stored locally)
* CLI-only interaction (no GUI or API access)
