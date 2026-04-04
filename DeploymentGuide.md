# Deployment Guide

This guide covers practical deployment options for TSG-CLI API and operational usage of the CLI.

## 1. Local Deployment

### Requirements

- Python 3.10+
- `pip`
- Telegram `API_ID` and `API_HASH`

### Steps

1. Clone the repository and enter the project directory.
2. Install dependencies.
3. Start the API server.
4. Authenticate once using CLI login.

```bash
git clone <your-repo-url>
cd tsg-cli
pip install -r requirements.txt
uvicorn api.main:app --reload
```

In a separate terminal:

```bash
python main.py login
```

### How login works

- You provide Telegram API credentials and phone number.
- Telegram sends OTP.
- If enabled, 2FA password is required.
- Session artifacts are stored locally under `~/.tsg-cli/`.

### Local data storage

By default, local runtime state is under:

- `~/.tsg-cli/config.json`
- `~/.tsg-cli/metadata.json`
- `~/.tsg-cli/auth_sessions.db`
- Telegram session files (`~/.tsg-cli/session*`)

### Quick endpoint testing

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/metrics
```

For authenticated routes, use your API auth flow endpoints from `APICalls.md`.

---

## 2. Cloud Server Deployment (VPS / Ubuntu)

### Requirements

- Ubuntu server
- Python 3.10+
- `git`
- network access to Telegram

### Steps

1. SSH into server.
2. Clone project.
3. Install dependencies.
4. Set environment variables.
5. Run Uvicorn on public interface.

```bash
ssh <user>@<server-ip>

sudo apt update
sudo apt install -y python3 python3-pip git

git clone <your-repo-url>
cd tsg-cli
pip3 install -r requirements.txt

export API_ID="<your_api_id>"
export API_HASH="<your_api_hash>"

uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Production process management

Use `systemd` for service supervision.

Example: `/etc/systemd/system/tsg-api.service`

```ini
[Unit]
Description=TSG API Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/tsg-cli
Environment=API_ID=<your_api_id>
Environment=API_HASH=<your_api_hash>
ExecStart=/usr/bin/python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Apply and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable tsg-api
sudo systemctl start tsg-api
sudo systemctl status tsg-api
```

Alternative (lightweight):

```bash
nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > tsg-api.log 2>&1 &
```

### Firewall

```bash
sudo ufw allow 8000/tcp
sudo ufw status
```

---

## 3. Docker Deployment

The repository includes both `Dockerfile` and `docker-compose.yml`.

### Build and run with Docker

```bash
docker build -t tsg-api .
docker run --rm -p 8000:8000 \
  -e API_ID=<your_api_id> \
  -e API_HASH=<your_api_hash> \
  tsg-api
```

### Run with Docker Compose

```bash
export API_ID=<your_api_id>
export API_HASH=<your_api_hash>
docker-compose up --build
```

### Environment variables

Set at minimum:

- `API_ID`
- `API_HASH`

### Volume behavior

The provided compose file mounts the repository into `/app`, which is convenient for development and iterative changes.

For stricter production isolation, use immutable images and explicit persistent volumes for `~/.tsg-cli` data.

---

## 4. Heroku Deployment

Heroku can run this API, but it is not ideal for this project due to local-state requirements.

### Why Heroku is not ideal

- Ephemeral filesystem can remove session/metadata state between restarts.
- Telegram session and local metadata persistence are core for stable operation.

### Minimal Heroku setup

1. Install Heroku CLI.
2. Create app.
3. Ensure Python buildpack.
4. Set config vars (`API_ID`, `API_HASH`).
5. Add `Procfile`.
6. Deploy.

```bash
heroku login
heroku create <app-name>
heroku buildpacks:set heroku/python
heroku config:set API_ID=<your_api_id> API_HASH=<your_api_hash>
```

`Procfile` content:

```text
web: uvicorn api.main:app --host=0.0.0.0 --port=$PORT
```

Deploy:

```bash
git push heroku main
```

---

## 5. Notes and Warnings

- Metadata is stored locally and is not automatically shared across multiple instances.
- Telegram rate limits still apply; API-level throttling does not remove upstream Telegram limits.
- Session/state files are local; stateless or highly ephemeral environments require explicit persistence planning.
- For production, secure API exposure behind TLS and a reverse proxy (for example, Nginx) and restrict CORS origins as needed.
