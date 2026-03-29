# TSG-CLI (Telegram Storage CLI)

A fast, lightweight, and local-first CLI tool that uses Telegram "Saved Messages" as an unlimited cloud storage drive. Built entirely on top of Pyrogram.

No subscriptions. No databases. No web dashboards. Just your terminal and your files.

---

## 🌟 Features

### ⚡ Batch Operations
* Batch upload (multiple files)
* Batch download (multiple IDs)
* Folder upload (recursive scanning)
* Mixed input (files + folders)

### 🔄 Reliability
* Automatic retry for failed uploads and downloads
* Resume downloads after interruption or network failure
* Safe interruption handling (Ctrl+C safely pauses without corruption)
* Graceful network recovery

### 🧠 Organization
* Tagging system for metadata grouping
* Virtual folders (via tag filtering)
* Virtual file renaming layer
* Server-side pagination and local filtering

### 🎯 CLI Experience
* Clean, structured tabular output
* Real-time progress tracking with speeds and checkpoints
* Consistent command feedback with summaries
* Clear, actionable success/error reporting

### 🏗️ Architecture
* Clean service layer (business logic only, no UI/styling concerns)
* Decoupled CLI layer (handles all user interaction and presentation)
* Structured data returned from core services
* API-ready and Web UI expandable

---

## 🚀 Getting Started

### Prerequisites

* Python 3.9+
* Telegram API ID and Hash (from [my.telegram.org/apps](https://my.telegram.org/apps))
* Your phone number

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the login setup:
   ```bash
   python main.py login
   ```
   *You will be prompted for your API ID, API Hash, phone number, and OTP code.*

---

## 📖 Usage Guide

### 📤 Uploading Files

Upload a single file:
```bash
python main.py upload my_document.pdf
```

**Batch Upload** (multiple files):
```bash
python main.py upload file1.mp4 file2.mp4
```

**Folder Upload** (recursive):
```bash
python main.py upload ./movies/
```

**Mixed Input** (files and folders):
```bash
python main.py upload ./movies file.txt
```

*Note: Directories are scanned recursively. Missing files are safely skipped with clear warnings.*

### 📄 Listing Files

List the 50 most recent files:
```bash
python main.py list
```

Filter by type or tags:
```bash
python main.py list --type video --tag anime
python main.py list --limit 100 --page 2 --sort size
```

### 📥 Downloading Files

Download a file by its ID (found via `list` or `search`):
```bash
python main.py download 12345
```

**Batch Download**:
```bash
python main.py download 12345 67890
```

**Custom Output Directory**:
```bash
python main.py download 12345 --output ./downloads
```

*Note: Interrupted downloads automatically resume. No need to restart large file downloads from scratch!*

### 🔍 Searching

Search by name (case-insensitive):
```bash
python main.py search "report"
```

Combine search with filters:
```bash
python main.py search "project" --tag work --type document
```

### 🗑️ Deleting Files

Delete one or multiple files by ID:
```bash
python main.py delete 12345
python main.py delete 12345 67890
```

---

## ⚡ Batch Workflow Example

```bash
# Upload an entire folder
python main.py upload ./anime/

# Download multiple files at once
python main.py download 246810 246811 246812

# Tag multiple files simultaneously
python main.py tag 246810,246811 add anime
```

---

## 🧠 System Design

* **Telegram as the Database:** Files are stored directly as Telegram messages in your "Saved Messages".
* **Unique IDs:** The File ID is simply the Telegram message ID.
* **Local Metadata:** Tags and virtual names are stored locally in a `~/.tsg-cli/metadata.json` file.
* **No Database Required:** Keeps the tool fast, portable, and impossible to desync.
* **Clean Architecture:** The internal services handle logic entirely independent of the UI. The CLI handles all user formatting.

---

## 🛡️ Reliability Features

* **Retry Loops:** Automatically attempts to recover from failed uploads/downloads due to Telegram CDN drops.
* **Resume Support:** Downloads save `.checkpoint` files to resume large downloads exactly where they left off.
* **Safe Interruption:** Pressing `Ctrl+C` flushes download buffers to disk to prevent corrupted partial files.
* **Clean Errors:** No stack traces on expected network issues.

---

## ⚠️ Limitations

* **Upload Limits:**
  * Free accounts: up to **2GB** per file
  * Premium accounts: up to **4GB** per file
* Files larger than this already existing in Telegram can still be downloaded without issue.
* Files must be uploaded manually through the CLI to ensure proper internal metadata is generated.

---

## 💡 Pro Tips

* Use **folder upload** for bulk operations and easy backups.
* Use **batch download** to grab entire collections efficiently.
* Combine `search` + `--tag` for powerful, instant filtering.
* Always run `python main.py backup` to save your metadata before switching systems!

---

## 🚀 Status

✅ Phase 1 — Core CLI  
✅ Phase 2 — Search & Filtering  
✅ Phase 3 — Organization + Backup  
✅ Phase 4 — Batch + Reliability + UX  
✅ Architecture — Clean separation (API-ready)  
