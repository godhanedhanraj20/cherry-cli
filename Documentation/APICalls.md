# TSG API Calls

## 1. Introduction

TSG exposes a REST API over the existing Telegram-backed storage system.

Base URL (local):

```text
http://localhost:8000
```

## 2. Authentication

### POST /auth/send-otp

Starts an authentication session by sending an OTP.

Request body:

```json
{
  "api_id": 123456,
  "api_hash": "your_api_hash",
  "phone_number": "+1234567890"
}
```

Response body:

```json
{
  "status": "otp_sent",
  "session_id": "f0a4de45-8f2a-4c4f-a0c0-c0f2e8f9f5cd"
}
```

### POST /auth/verify-otp

Verifies OTP using the `session_id` from `/auth/send-otp`.

Request body:

```json
{
  "session_id": "f0a4de45-8f2a-4c4f-a0c0-c0f2e8f9f5cd",
  "otp": "12345"
}
```

Possible response (login complete):

```json
{
  "status": "success",
  "is_premium": false,
  "requires_2fa": false,
  "session_id": null
}
```

Possible response (2FA required):

```json
{
  "status": "2fa_required",
  "is_premium": false,
  "requires_2fa": true,
  "session_id": "f0a4de45-8f2a-4c4f-a0c0-c0f2e8f9f5cd"
}
```

### POST /auth/2fa

Completes authentication when 2FA is required.

Request body:

```json
{
  "session_id": "f0a4de45-8f2a-4c4f-a0c0-c0f2e8f9f5cd",
  "password": "your_2fa_password"
}
```

Response body:

```json
{
  "status": "success",
  "is_premium": false,
  "requires_2fa": false,
  "session_id": null
}
```

### GET /auth/status

Returns whether a valid session is currently authenticated.

Response body:

```json
{
  "logged_in": true,
  "is_premium": true
}
```

## 3. File APIs

### POST /files/upload

Uploads one file.

- Content-Type: `multipart/form-data`
- Field name: `file`

Response body:

```json
{
  "file_id": 12345,
  "name": "video.mp4",
  "size": "120.53 MB"
}
```

### GET /files

Lists files with optional filters.

Query params:

- `page` (default `1`)
- `limit` (default `50`, max `200`)
- `sort` (`date | name | size`)
- `type` (`video | image | document | audio`)
- `tag` (string)

Response body:

```json
{
  "files": [
    {
      "id": 12345,
      "name": "video.mp4",
      "size": "120.53 MB",
      "date": "2026-03-30 09:12:00",
      "tags": "work,archive",
      "raw_size": 126385152,
      "caption": ""
    }
  ]
}
```

### GET /files/search

Searches files by query and/or filters.

Query params:

- `query` (string, optional)
- `tag` (string, optional)
- `type` (`video | image | document | audio`, optional)
- `page` (default `1`)
- `limit` (default `50`, max `200`)
- `sort` (`date | name | size`)

Note: at least one of `query`, `tag`, or `type` must be provided.

Response body:

```json
{
  "results": [
    {
      "id": 12345,
      "name": "video.mp4",
      "size": "120.53 MB",
      "date": "2026-03-30 09:12:00",
      "tags": "work,archive",
      "raw_size": 126385152,
      "caption": ""
    }
  ]
}
```

### GET /files/{file_id}/download

Downloads a file by numeric ID.

Response:

- Binary stream
- Header:

```text
Content-Disposition: attachment; filename="<resolved_name>"
```

### DELETE /files

Deletes one or more file IDs.

Request body:

```json
{
  "file_ids": [12345, 67890]
}
```

Response body:

```json
{
  "deleted": 1,
  "failed": 1,
  "errors": [
    {
      "file_id": 67890,
      "error": "File with ID 67890 not found."
    }
  ]
}
```

## 4. Notes

- All endpoints return JSON except `GET /files/{file_id}/download`.
- Error format is standardized:

```json
{
  "error": "message"
}
```

## 5. cURL Examples

### Send OTP

```bash
curl -X POST http://localhost:8000/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{
    "api_id": 123456,
    "api_hash": "your_api_hash",
    "phone_number": "+1234567890"
  }'
```

### Verify OTP

```bash
curl -X POST http://localhost:8000/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "f0a4de45-8f2a-4c4f-a0c0-c0f2e8f9f5cd",
    "otp": "12345"
  }'
```

### Upload File

```bash
curl -X POST http://localhost:8000/files/upload \
  -F "file=@/absolute/path/to/file.mp4"
```

### List Files

```bash
curl "http://localhost:8000/files?page=1&limit=20&sort=date&type=video"
```

### Download File

```bash
curl -L "http://localhost:8000/files/12345/download" -o downloaded_file.bin
```

### Delete Files

```bash
curl -X DELETE http://localhost:8000/files \
  -H "Content-Type: application/json" \
  -d '{"file_ids": [12345, 67890]}'
```
