# API & Web UI Background (Repository Analysis)

This report is based strictly on the current repository implementation in `/workspace/cherry-cli`.

## 1. System Overview

### What the project currently does

The project is a command-line tool (`TSG-CLI`) for storing and managing files in the authenticated Telegram account's **Saved Messages** chat. The CLI supports authentication, upload/download/delete flows, file discovery (list/search), metadata tagging and virtual renaming, plus metadata backup/restore.

### Purpose of the CLI

The CLI is the only user interface in this repository. It:

- Parses command-line input (`typer`) and renders output (`rich`).
- Handles command-level UX (prompts, confirmations, progress headers, summary counts).
- Delegates Telegram + file operations to the service layer.
- Delegates metadata persistence (tags/custom names) to utility modules.

### How Telegram is used as storage

- Files are uploaded using `client.send_document("me", document=...)`, i.e., sent to Saved Messages.
- Files are discovered by reading `client.get_chat_history("me")`.
- Files are downloaded using message ID lookup (`client.get_messages("me", file_id)`) and streaming (`client.stream_media(...)`).
- Files are deleted via `client.delete_messages("me", file_id)`.

### Core capabilities present in code

- `login`: interactive API credential setup + OTP sign-in + optional 2FA password.
- `upload`: single file or recursive directory upload with per-file status and retry logic.
- `download`: single/batch download with checkpoint-based resume and retry.
- `delete`: single/batch delete with confirmation.
- `list`: paginated/sorted listing with optional tag/type filter.
- `search`: query/tag/type search (AND semantics).
- `tag`: add/remove/list tags in local metadata.
- `rename`: set/remove custom display name in local metadata.
- `backup`: upload local metadata JSON to Telegram with a backup marker caption.
- `restore`: find backup messages, select latest/manual, download and replace local metadata.

## 2. Project Structure Analysis

## Top-level files and folders

- `main.py`: process entry point; imports CLI app and executes it.
- `cli/`: command routing and user interaction.
- `services/`: authentication and file operation logic against Telegram.
- `utils/`: config, metadata, parsing, and custom error class.
- `telegram/`: Pyrogram client factory.
- `tests/`: unit/integration-style CLI/service tests.
- `requirements.txt`: runtime/test dependencies.

## Responsibilities by module area

### `cli/`

- `cli/commands.py` defines all Typer commands and command orchestration.
- It handles prompts/confirmations, output formatting, and async execution wrapper (`run_async`).
- It calls into service functions (`services.auth`, `services.file_service`) and metadata utilities.

### `services/`

- `services/auth.py`:
  - Login status checks.
  - Interactive authentication workflow.
  - Returns authenticated `pyrogram.Client` instances.
- `services/file_service.py`:
  - Upload/download/delete/search/get_files operations.
  - Internal helper functions for checkpoints and type matching.

### `utils/`

- `utils/config_manager.py`: local config path creation + read/write (`~/.tsg-cli/config.json`) and session name path.
- `utils/metadata_manager.py`: local metadata file read/write (`~/.tsg-cli/metadata.json`) + tag/custom_name APIs.
- `utils/parser.py`: file size formatting and metadata extraction from Pyrogram messages.
- `utils/errors.py`: `TSGError` custom user-facing exception class.

### Metadata manager separation

There is no separate service-level metadata module; metadata operations are centralized in `utils/metadata_manager.py` and consumed from CLI/parser/service paths.

### Entry point and command routing flow

1. `main.py` imports `app` from `cli.commands` and invokes `app()`.
2. `typer` dispatches to the selected `@app.command()` function.
3. Command function may define an internal async function and execute it via `run_async(...)`.
4. Async command logic gets authenticated client (`get_authenticated_client`) and calls service functions.
5. Service function executes Telegram operation, returning metadata or file path / raising `TSGError`.
6. CLI formats output + summary and closes/disconnects client.

## 3. Command Flow Breakdown

## `login`

- Service calls: `check_auth_status()`, `authenticate_user(prompt_cb, log_cb)`.
- Flow:
  - Check if already logged in.
  - If not, prompt for credentials (if missing), phone number, OTP, and optional 2FA password.
  - Return status dict with premium flag.
- Dependencies: `services.auth`, `typer.prompt`, `rich` output helpers.

## `upload`

- Service calls: `get_authenticated_client()`, then `upload_file(client, path, log_cb)` per file.
- Flow:
  - Validate path exists.
  - If file: upload once.
  - If directory: recursively collect files, confirm with user, upload each file.
  - Aggregate success/fail counts.
- Dependencies: `os` traversal, auth service, file service, `TSGError` handling.

## `download`

- Service calls: `get_authenticated_client()`, then `download_file(client, fid, output_dir, log_cb)` for each ID.
- Flow:
  - Ensure output directory exists.
  - Iterate IDs; for each, request download.
  - Summarize success/failure; handles keyboard interruption.
- Dependencies: auth service, file service, filesystem writes, checkpoint logic (inside service).

## `delete`

- Service calls: `get_authenticated_client()`, then `delete_file(client, int(file_id))`.
- Flow:
  - Confirm destructive action.
  - Iterate IDs, delete each message by ID.
  - Summarize success/failure.
- Dependencies: auth service, file service, confirmation prompt.

## `search`

- Service calls: `get_authenticated_client()`, `search_files(client, query, limit, file_type, sort_by, tag, page, debug)`.
- Flow:
  - Normalize query/type strings.
  - Require at least one filter among query/tag/type.
  - Fetch matching metadata list from service and render table.
- Dependencies: auth service, file service, rich table rendering.

## `list`

- Service calls: `get_authenticated_client()`, `get_files(...)` (which delegates to `search_files(..., query=None)`).
- Flow:
  - Fetch files with pagination/sort/type/tag options.
  - Render tabular output.
- Dependencies: auth service, file service.

## `tag`

- Service calls: none in `services/`; directly uses metadata manager functions.
- Flow:
  - Parse comma-separated IDs.
  - Action `add|remove|list`.
  - Apply metadata mutation/read per ID.
  - Summarize success/failure.
- Dependencies: `utils.metadata_manager`.

## `rename`

- Service calls: none in `services/`; directly uses metadata manager.
- Flow:
  - Validate non-empty name if provided.
  - Set or remove custom name in metadata.
- Dependencies: `utils.metadata_manager`, `TSGError`.

## `backup`

- Service calls: `get_authenticated_client()` only; Telegram call done directly in CLI.
- Flow:
  - Ensure metadata file exists.
  - Upload metadata file to Saved Messages with caption `#TSG_METADATA_BACKUP`.
- Dependencies: auth service, `METADATA_FILE`, Pyrogram `send_document`.

## `restore`

- Service calls: `get_authenticated_client()` only; Telegram + file replacement logic done directly in CLI.
- Flow:
  - Scan chat history for documents tagged with backup caption.
  - Optionally let user pick backup ID.
  - Download selected backup to temp location, validate JSON, replace local metadata file.
- Dependencies: auth service, `json`, filesystem replace, `format_size` for table display.

## 4. Service Layer Analysis

## Service modules identified

- `services/auth.py`
- `services/file_service.py`

## Responsibilities

### Upload service logic

Implemented by `upload_file(...)` in `services/file_service.py`:

- Validates file path and size limit (2GB free / 4GB premium via `client.me.is_premium`).
- Uses `send_document` with progress callback.
- Retries transient failures up to 3 attempts with incremental sleep.
- Extracts return metadata through `extract_message_metadata`.

### Download service logic

Implemented by `download_file(...)`:

- Resolves message by ID.
- Computes final filename (custom name fallback).
- Streams media with buffered writes, checkpoint persistence, resume behavior, progress output.
- Retries interrupted stream (up to 3 attempts), refetches message on retry.
- Verifies final file size against expected media size and clears checkpoint.

### Metadata handling in service context

- Search/list pipelines call `extract_message_metadata`, which enriches message metadata with local tags and custom name.
- Download name resolution also uses metadata (`get_custom_name`) before filesystem write.
- Tag/rename CRUD itself is not implemented in service layer (CLI calls metadata manager directly).

### Retry logic

- Upload: retries transient network-like exceptions by substring matching (`timeout`, `connection`, `network`, `reset`).
- Download: retries stream failures with backoff + jitter and can abort when progress appears stuck repeatedly.

## Centralization assessment

- Telegram file transfer/search logic is mostly centralized in `services/file_service.py`.
- Authentication is centralized in `services/auth.py`.
- However, backup/restore and metadata tag/rename operations are currently implemented in CLI layer, not service layer.

## 5. Metadata System

## Where metadata is stored

Local file at `~/.tsg-cli/metadata.json` (`METADATA_FILE` constant in `utils/metadata_manager.py`).

## Structure of `metadata.json` (as implied by code)

Top-level JSON object keyed by `file_id` string. Each file entry may contain:

- `tags`: list of strings
- `custom_name`: string

Example shape:

```json
{
  "12345": {
    "tags": ["work", "urgent"],
    "custom_name": "report_final.pdf"
  }
}
```

## Update behavior across operations

- Updated by:
  - `tag add/remove`
  - `rename` set/remove custom name
  - `restore` (replaces whole file with backup)
- Read by:
  - `search`/`list` metadata extraction (tags/custom names applied to output)
  - `download` filename resolution (custom name)
  - `backup` existence check + upload to Telegram
- Not updated by upload/delete service functions.

## Role as source of truth

Metadata is source of truth for **local organizational overlays** (tags/custom_name), not for raw Telegram file existence. File existence still comes from Telegram chat history/messages.

## 6. Telegram Integration

## Library used

`pyrogram` (with `tgcrypto` in dependencies).

## Authentication mechanics

- Client factory: `telegram/client.py::get_client(...)` returns `pyrogram.Client` with session path `~/.tsg-cli/session` and `no_updates=True`.
- Credential storage: `~/.tsg-cli/config.json` with `api_id`, `api_hash`.
- Login flow in `authenticate_user`:
  - connect
  - `send_code(phone_number)`
  - `sign_in(...)` with OTP
  - fallback to `check_password(...)` when `SessionPasswordNeeded`

## Upload / download mechanics

- Upload via `send_document("me", document=abs_path, progress=...)`.
- Download by:
  - `get_messages("me", file_id)`
  - async iteration over `stream_media(message)` chunks
  - buffered file writes and checkpointing.

## File ID management

- Telegram message ID (`message.id`) is used as the file ID throughout CLI operations.
- Commands like download/delete/tag/rename use that ID (as int or string depending on context).
- Search/list display this message ID.

## 7. Error Handling & Retry

## Error handling pattern

- Custom `TSGError` used for intentional user-facing errors.
- Services generally wrap unknown exceptions into `TSGError("...failed: ...")`.
- CLI catches `TSGError` and prints user-readable failures, often continuing per item in batch flows.

## Retry behavior

- Upload:
  - Up to 3 attempts.
  - Retries only when error string indicates transient network-related issue.
  - Exponential-style delay (`2 * (attempt + 1)`).
- Download:
  - Up to 3 attempts.
  - Checkpoint/resume via sidecar `.checkpoint` file.
  - Detects repeated no-progress state and aborts with specific error.
  - Randomized backoff (`2 * (attempt + 1) + random`).

## 8. Current Limitations (Observed in Code)

1. **No API/Web interface implementation present.**
2. **Backup/restore logic is in CLI command module**, not in reusable service module.
3. **Tag/rename logic bypasses service layer** and is directly bound to CLI commands.
4. **Search/list rely on scanning Saved Messages history** each time; no indexed cache layer in code.
5. **Type filtering is extension/native-attribute based with fixed sets** (`video/image/document/audio`) and limited extension lists.
6. **Pagination is in-memory over scanned messages** (collect up to requested page window), not server-side pagination abstraction.
7. **Internal file hiding is rule-based** (`metadata.json` with caption containing `tsg-cli`, and backup caption marker), which can miss other internal artifacts.
8. **Repository contains patch artifact files** (`cli/commands.py.orig`, `cli/commands.py.rej`) indicating unresolved/leftover merge tooling output in tree.

## 9. API Design Readiness

## Reusable functions already suitable for API layer

- Authentication service:
  - `check_auth_status`, `authenticate_user` (with callback abstraction), `get_authenticated_client`.
- File operations:
  - `upload_file`, `download_file`, `delete_file`, `search_files`, `get_files`.
- Metadata utility APIs:
  - `add_tag`, `remove_tag`, `get_tags`, `set_custom_name`, `remove_custom_name`.

## Tightly CLI-coupled areas

- `backup` and `restore` are implemented in `cli/commands.py` (Telegram operations + local file replacement mixed with prompt/output).
- `tag` and `rename` command logic also lives directly in CLI (not wrapped as service functions).
- Service functions print progress directly (`print(...)`) and optionally call `log_cb`, which is not purely API-response oriented.

## Abstractions likely needed before API exposure

- Move backup/restore into dedicated service module(s).
- Add service-level methods for tag and rename operations to remove CLI coupling.
- Replace direct stdout progress output in services with structured progress events/callback-only approach.
- Normalize return schemas across commands (currently mixed dict/path/None patterns).

## 10. Web UI Readiness

## Data currently available for UI display

From existing service outputs and parser metadata:

- File list/search rows: `id`, `name`, `size`, `date`, `tags`, `raw_size`, `caption`.
- Auth status: logged-in flag and premium limit info.
- Operation outcomes: success/failure messages and counts (currently composed in CLI).

## Functional endpoints implied by current command set

If mirrored directly, UI would need API endpoints for:

- auth status/login/logout-like session actions
- upload
- download
- delete
- list/search with filters/pagination/sort
- tag add/remove/list
- rename set/reset
- metadata backup/restore and backup listing/selection

## Gaps for UI integration in current structure

- No HTTP/API layer exists.
- Backup/restore and tag/rename are not standardized in service layer.
- Progress reporting is terminal-oriented (carriage-return prints), not websocket/event payload form.
- No explicit DTO/schema module for stable UI contracts.

## 11. Risks & Architecture Notes

## State handling

- Local state is split across:
  - `config.json` (credentials)
  - `session` file (Pyrogram)
  - `metadata.json` (tags/custom names)
- `restore` replaces metadata atomically via `os.replace`, but no merge strategy exists.

## Session management

- Each command creates/connects/disconnects client instances.
- Multi-request API scenarios would need explicit client lifecycle/session pooling strategy.

## Concurrency

- Metadata writes are simple JSON rewrites without locking; concurrent API/UI requests could race.
- Checkpoint file writes for download are single-path sidecar files; simultaneous downloads of same target path can conflict.
- Service methods assume command-serial CLI execution style.

## Scaling considerations from current implementation

- Search/list iterating entire Saved Messages history can become expensive as message volume grows.
- Retry logic is local and per-command; no global task queue or background worker model exists.
- Error handling is human-readable string oriented; API usage will require structured error codes/messages.
