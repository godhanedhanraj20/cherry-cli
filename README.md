# TSG-CLI: Telegram-Based File Storage System

A powerful CLI tool for managing files on Telegram with advanced features like batch operations, virtual folders, tagging, and retry-based transfers.

---

## 🌟 Features

### Core Features

* Upload files (2GB free / 4GB premium)
* Download with retry & resume support
* Delete files
* Batch operations:
  * Batch upload
  * Batch download
  * Batch delete
  * Batch tagging
* Tagging system
* Virtual folder system (path-based)
* Rename (virtual metadata)
* Backup & restore metadata

### CLI Features

* Login (OTP + 2FA)
* Session persistence
* Search:
  * Query-based
  * Tag-based
  * Type-based
* Combined filters
* Sorting:
  * Name
  * Size
  * Date
* Pagination
* Clean terminal output

---

## 🏗️ Architecture (Internal)

The system is designed with a clean, decoupled architecture:

* **CLI layer**: Handles all user interaction, parsing arguments, and formatting output.
* **Service layer**: Handles all core logic (upload, download, metadata management, and Telegram interactions).
* **Utils**: Provides helper functions for path handling, parsing, and metadata management.

All core logic is centralized in the service layer to ensure consistency and maintainability.

---

## 📁 Project Structure

```
tsg-cli/
├── cli/
├── services/
├── tests/
└── utils/
```

---

## 🚀 Installation

### Requirements

* Python 3.10+

### Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run CLI login:
   ```bash
   python main.py login
   ```

---

## 📖 Usage

### Examples

**Upload:**
```bash
python main.py upload file.mp4
```

**Download:**
```bash
python main.py download 12345
```

**Search:**
```bash
python main.py search --query "movie"
```

**Batch Operations:**
```bash
python main.py upload file1.mp4 file2.mp4
```

---

## ⚙️ Configuration

The application requires Telegram API credentials to operate.

* `API_ID`: Your Telegram API ID, provided via environment variables.
* `API_HASH`: Your Telegram API Hash, provided via environment variables.
* **Session**: Your Telegram session is persisted locally after a successful login, meaning you only need to authenticate once.

---

## 📊 Current Status

**Status:** Stable CLI (Phase 4 Complete)

**Completed:**
* Core CLI system
* Batch operations
* Folder system
* Retry mechanisms
* Metadata system

---

## ⚠️ Limitations

* CLI-only interface
* No graphical interface
* No external API access (yet)

---

## 🛣️ Roadmap

**Next:**
* API layer
* Web interface
* Telegram bot integration

---

## 🤝 Contributing

Contributions welcome. Follow clean modular architecture.

---

## 📄 License

MIT License
