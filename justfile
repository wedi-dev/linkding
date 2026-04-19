set shell := ["bash", "-ceu", "-o", "pipefail"]

# Deploy workflow for bare-metal (non-Docker) installs.
# See deploy/README.md for initial setup.

data_dir := env_var_or_default("LD_DATA_DIR", "./data")
backup_dir := data_dir / "backups"
backup_retention := env_var_or_default("LD_BACKUP_RETENTION", "10")

# Default: list targets
default:
    @just --list

# One-shot deploy: backup → pull → install → migrate → collectstatic → restart
deploy: backup pull install migrate collectstatic restart

# Snapshot the SQLite DB before any schema change
backup:
    mkdir -p "{{backup_dir}}"
    cp "{{data_dir}}/db.sqlite3" "{{backup_dir}}/pre-deploy-$(date +%Y%m%d-%H%M%S).sqlite3"
    ls -1t "{{backup_dir}}"/pre-deploy-*.sqlite3 2>/dev/null | tail -n +$(({{backup_retention}} + 1)) | xargs -r rm --

pull:
    git pull --ff-only

install:
    uv sync --frozen

migrate:
    DJANGO_SETTINGS_MODULE=bookmarks.settings.prod uv run python manage.py migrate --noinput

collectstatic:
    DJANGO_SETTINGS_MODULE=bookmarks.settings.prod uv run python manage.py collectstatic --noinput

restart:
    sudo systemctl restart linkding-web linkding-tasks

start:
    sudo systemctl start linkding-web linkding-tasks

stop:
    sudo systemctl stop linkding-web linkding-tasks

status:
    systemctl status linkding-web linkding-tasks --no-pager

logs service="linkding-web":
    journalctl -u {{service}} -f
