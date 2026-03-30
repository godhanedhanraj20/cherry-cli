# TSG-CLI: Telegram-Based File Storage System

TSG is a Python-based file storage system with two interfaces:

- A CLI (`python main.py ...`) for interactive terminal workflows.
- A REST API (FastAPI) for programmatic access.

Telegram Saved Messages is used as the storage backend. Files are uploaded as Telegram media messages, and message IDs are used as file identifiers for download, delete, and lookup operations. Local metadata (`~/.tsg-cli/metadata.json`) provides organizational overlays such as tags and custom names.

## Features

### Core Features

- Upload / Download / Delete
- Search and filtering
- Tagging system
- Rename (metadata-based custom name)
- Batch operations (CLI)
- Backup and restore metadata
- Retry and resume behavior for transfers

### API Features

- REST API (FastAPI)
- Authentication flow (OTP + optional 2FA)
- File operations via HTTP
- Streaming downloads
- Structured JSON responses (download endpoint returns binary stream)

## Architecture

- CLI -> Services -> Telegram
- API -> Adapters -> Services -> Telegram

All core logic resides in the service layer for consistency across CLI and API.

## Project Structure

```text
tsg-cli/
├── cli/
├── services/
├── utils/
├── api/
│   ├── routes/
│   ├── schemas/
│   ├── dependencies/
│   └── services_adapter/
├── tests/
```

## Installation

Requirements:

- Python 3.10+

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running

CLI:

```bash
python main.py login
```

API:

```bash
uvicorn api.main:app --reload
```

## Configuration

The system requires Telegram API credentials:

- `API_ID`
- `API_HASH`

In current implementation, credentials are collected during login and stored in local config (`~/.tsg-cli/config.json`). Session state is persisted locally (`~/.tsg-cli/session*`) after successful authentication.

## API Overview

Detailed API documentation is available in `APICalls.md`.

## Limits

Telegram upload limits enforced by current logic:

- 2GB for free accounts
- 4GB for premium accounts

Current product surface is CLI + API only (no Web UI yet).

## Current Status

Status: Stable CLI + API (Phase 5)

## Roadmap

- Web UI
- Streaming optimization
- Caching and performance improvements

## Contributing

Follow modular service-based architecture.

## License

MIT
