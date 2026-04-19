# Bare-metal deploy (no Docker)

Runs linkding as two systemd services: uWSGI for the web app and a Huey
process for background tasks. Driven by a `justfile` at the repo root.

## One-time setup on the server

```bash
# 1. User + directories
sudo useradd --system --create-home --home-dir /opt/linkding --shell /bin/bash linkding
sudo -u linkding mkdir -p /opt/linkding/data/{backups,favicons,previews,assets}

# 2. Clone the repo
sudo -u linkding git clone https://github.com/<fork>/linkding.git /opt/linkding
cd /opt/linkding

# 3. Install Python deps (uv must be available system-wide)
sudo -u linkding uv sync --frozen

# 4. Host-specific env
sudo install -o root -g root -m 0644 /dev/stdin /etc/default/linkding <<'EOF'
HOST_NAME=linkding.example.com
LD_UWSGI_UID=linkding
LD_UWSGI_GID=linkding
# Optional:
# LD_CONTEXT_PATH=
# LD_REQUEST_TIMEOUT=60
EOF

# 5. Seed the DB + static
cd /opt/linkding
sudo -u linkding just migrate
sudo -u linkding just collectstatic
sudo -u linkding .venv/bin/python manage.py createsuperuser

# 6. Install systemd units
sudo cp deploy/systemd/linkding-web.service /etc/systemd/system/
sudo cp deploy/systemd/linkding-tasks.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now linkding-web linkding-tasks

# 7. Reverse proxy (Caddy/nginx) → 127.0.0.1:9090
```

## Daily deploy

From /opt/linkding as the `linkding` user:

```bash
just deploy
```

This chains `backup → pull → install → migrate → collectstatic → restart`.

Individual targets are also available: `just backup`, `just migrate`,
`just restart`, `just logs linkding-tasks`, etc. Run `just` with no
arguments for the list.

## Backups

`just backup` copies `data/db.sqlite3` to `data/backups/pre-deploy-<timestamp>.sqlite3`
and keeps the 10 most recent (override with `LD_BACKUP_RETENTION`).

Assets and favicons are not included in the pre-deploy copy — only the SQLite
DB (the thing migrations can break). Use `manage.py full_backup` for a full
snapshot when the storage layout changes.
