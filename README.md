# TSG-CLI: Telegram-Based File Storage System

## Description

TSG-CLI is a Telegram-backed file storage system that provides:

- A command-line interface (CLI) for day-to-day file operations.
- A FastAPI-based HTTP API for programmatic access.

The system uses Telegram Saved Messages as the storage backend. Files are uploaded as Telegram media messages and referenced by message ID for later download, search, and deletion.

Local metadata is used to organize files with tags and metadata-based custom names without changing the original Telegram media payload.

## Features

### Core Features

- Upload / download / delete operations.
- Search and filtering by query, type, and tags.
- Tagging system for categorization.
- Rename support via metadata-based custom names.
- Batch-style operations for selected actions (for example, delete/tag flows over multiple file IDs).
- Metadata backup and restore.
- Retry and resume support for file transfer workflows.

### API Features

- REST API powered by FastAPI.
- OTP + 2FA authentication flow.
- File operations over HTTP endpoints.
- Streaming downloads.
- Structured JSON responses and standardized error payloads.

## Architecture

- `CLI -> Services -> Telegram`
- `API -> Adapters -> Services -> Telegram`

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
├── frontend/
├── tests/
```

Notes:

- The `frontend/` directory exists in the repository, but production backend support is focused on CLI + API in the current stable scope.
- `~/.tsg-cli/` stores local runtime state (session/config/metadata).

## Installation

### Requirements

- Python 3.10+
- `pip`

### Setup

```bash
git clone <your-repo-url>
cd tsg-cli
pip install -r requirements.txt
```

## Running

### CLI

```bash
python main.py login
```

Follow prompts for Telegram credentials and OTP/2FA if required.

### API

```bash
uvicorn api.main:app --reload
```

API default local address:

- `http://127.0.0.1:8000`

## Configuration

The system uses both environment variables and local config.

- `API_ID`: Telegram API ID
- `API_HASH`: Telegram API hash

Configuration precedence:

- Environment variables (`API_ID`, `API_HASH`)
- Local config file (`~/.tsg-cli/config.json`)

Runtime/local state:

- Telegram session files: under `~/.tsg-cli/`
- Metadata file: `~/.tsg-cli/metadata.json`
- Auth session SQLite store: `~/.tsg-cli/auth_sessions.db`

## API Overview

Detailed endpoint-level documentation is available in `APICalls.md`.

## Limits

Telegram upload limits apply:

- 2GB for free accounts
- 4GB for Telegram Premium accounts

Additional application-level upload checks are enforced in API paths to protect server resources.

## Current Status

Stable CLI + API (Phase 5)

## Roadmap

- Web UI integration and release hardening.
- Additional performance improvements for high-volume libraries.
- Expanded caching and observability enhancements.

## Contributing

Contributions are welcome.

Please follow the modular service-based architecture:

- Keep business logic in `services/`.
- Keep HTTP translation logic in `api/services_adapter/`.
- Keep route handlers thin and focused on request/response handling.

## License

MIT
