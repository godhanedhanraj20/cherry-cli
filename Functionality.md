# TSG-CLI Functionality


## 1. Introduction

This document provides a complete breakdown of all CLI commands and core system functionalities available in TSG-CLI (Phase 4).

---

## 2. Authentication

**Command:** `login`

**Features:**
* OTP-based login
* 2FA support
* Session persistence

**Examples:**
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

**Command:** `upload`

**Features:**
* Single file upload
* Folder upload (recursive batch upload)
* File validation (size limits)
* Progress display
* Retry on failure

**Examples:**
```bash
python main.py upload file.mp4
python main.py upload ./movies/
```

**Behavior:**
* Accepts only ONE path argument per command
* Automatically detects a file vs folder
* Expands folders recursively for batch uploading
* Skips missing files
* Shows progress and speed

### 3.2 Download

**Command:** `download`

**Features:**
* Single file download
* Batch download (multiple IDs)
* Custom output directory (`--output` / `-o`)
* Resume support
* Retry logic
* Partial file cleanup

**Examples:**
```bash
python main.py download 12345
python main.py download 12345 67890
python main.py download 12345 -o ./downloads
```

**Behavior:**
* Resumes from checkpoint
* Retries on network failure
* Displays progress + speed

### 3.3 Delete

**Command:** `delete`

**Features:**
* Batch delete
* Confirmation prompt

**Examples:**
```bash
python main.py delete 12345
python main.py delete 12345 67890
```

**Behavior:**
* Accepts space-separated file IDs
* Asks confirmation before deleting
* Reports success/failed count

### 3.4 Rename

**Command:** `rename`

**Features:**
* Modifies virtual file name

**Examples:**
```bash
python main.py rename 12345 new_video.mp4
```

**Behavior:**
* Updates custom file name in metadata
* If name is empty, it resets to the original file name

---

## 4. Search & Filter

**Command:** `search`

**Features:**
* Positional query search
* Tag filtering
* File type filtering
* Combined filters

**Examples:**
```bash
python main.py search movie
python main.py search --tag anime
python main.py search movie --type video --tag anime
```

**Behavior:**
* Query is passed as a positional argument (not a flag)
* Requires at least one of: query, tag, or type
* Supports combining filters
* Returns matched results from metadata
* Displays table output with structured data

---

## 5. Listing

**Command:** `list`

**Features:**
* Displays stored files
* Pagination support (`--limit`, `--page`)
* Sorting support (`--sort`)
* Filtering support (`--type`, `--tag`)

**Examples:**
```bash
python main.py list
python main.py list --limit 20
python main.py list --sort name
python main.py list --sort size
python main.py list --sort date
```

**Behavior:**
* Supports sorting and pagination together
* Tag filter supports comma-separated tags
* Displays results in table format (ID, Name, Size, Date, Tags)

---

## 6. Tagging System

**Command:** `tag`

**Features:**
* Add tags
* Remove tags
* List tags
* Batch tagging

**Examples:**
```bash
python main.py tag 12345,67890 add anime
python main.py tag 12345,67890 remove anime
python main.py tag 12345 list
```

**Behavior:**
* File IDs MUST be comma-separated
* Multiple tags in one command are NOT supported
* Updates local metadata

---

## 7. Batch Operations

**Features:**
* Upload (via folder recursion)
* Download (via space-separated IDs)
* Delete (via space-separated IDs)
* Tag (via comma-separated IDs)

**Behavior:**
* Handles partial failures (if one file fails, the others continue)
* Shows a summary upon completion:
  * Success: X
  * Failed: Y

---

## 8. Retry & Resilience

**Features:**
* Upload retry logic
* Download retry logic
* Resume support
* Network failure handling

**Behavior:**
* Retry logic is handled internally by the service layer
* Downloads resume from the last saved byte
* Gracefully attempts to recover from network drops

---

## 9. Metadata System

All organizational data is stored locally.

**Features:**
* Managed via `metadata_manager`
* Local metadata storage (`metadata.json`)

**Behavior:**
* Acts as the single source of truth for the CLI
* Automatically updated on:
  * upload
  * delete
  * tag
  * rename
* Stores: `file_id`, `name`, `size`, `path`, `tags`

---

## 10. Backup & Restore

Metadata can be backed up to Telegram and restored to sync multiple devices.

### 10.1 Backup

**Command:** `backup`

**Features:**
* Cloud backup of local metadata

**Examples:**
```bash
python main.py backup
```

**Behavior:**
* Uploads `metadata.json` directly to Telegram "Saved Messages"
* Stored as a document with the tag: `#TSG_METADATA_BACKUP`

### 10.2 Restore

**Command:** `restore`

**Features:**
* Restores cloud metadata
* Manual backup selection (`--select`)

**Examples:**
```bash
python main.py restore
python main.py restore --select
```

**Behavior:**
* Fetches backups from Telegram chat history
* Automatically selects the latest backup (unless `--select` is used)
* Supports manual selection using `--select`
* Downloads and replaces the local metadata file
* Validates JSON before restoring
* Warns before overwriting current local metadata

---

## 11. Error Handling

**Features:**
* Controlled failures
* Safe interruption

**Behavior:**
* `TSGError` is used internally for controlled failures
* Provides clear error messages for invalid file IDs
* Handles missing local files gracefully during upload
* `KeyboardInterrupt` handling safely closes buffers to prevent file corruption

---

## 12. Limitations

* Depends on Telegram API limits (2GB free / 4GB premium)
* CLI-only interaction (no GUI or external API access)
