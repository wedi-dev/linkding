# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

linkding is a self-hosted bookmark manager built with Django 6 and Lit web components. It runs in Docker with uWSGI, uses Huey for background tasks, and supports SQLite (default) or PostgreSQL.

## Development Commands

```bash
make init              # One-time setup: uv sync, create data dirs, migrate, npm install
make serve             # Django dev server on localhost:8000
make frontend          # Watch mode for JS/CSS (Rollup + PostCSS)
make tasks             # Run Huey background task queue
make test              # Run all tests with pytest (parallel: -n auto)
make lint              # ruff check bookmarks
make format            # ruff format + djlint templates + prettier JS/CSS
make e2e               # Playwright E2E tests (installs chromium, builds frontend, collectstatic)
```

Run a single test file or test:
```bash
uv run pytest bookmarks/tests/test_bookmark_edit_view.py
uv run pytest bookmarks/tests/test_bookmark_edit_view.py -k "test_name"
```

Dev requires two terminals: `make frontend` (JS/CSS watch) and `make serve` (Django server).

## Architecture

Main app is `bookmarks/`. The `startpage/` app (feature branch `feature/start-page`) adds a mobile-friendly start page hub.

### Backend Layers

- **Models** (`models.py`): `Bookmark`, `Tag`, `BookmarkBundle`, `BookmarkAsset`, `UserProfile`. Bookmarks have many-to-many Tags, both owned per-user.
- **Services** (`services/`): Business logic layer. `bookmarks.py` and `tags.py` for CRUD, `website_loader.py` for fetching URL metadata, `favicon_loader.py`/`preview_image_loader.py` for assets, `importer.py`/`exporter.py` for Netscape HTML format, `wayback.py` for Internet Archive, `auto_tagging.py` for ML tag suggestions.
- **Views** (`views/`): Server-rendered Django views using Turbo Frames for SPA-like navigation. Organized by domain: bookmarks, tags, bundles, settings, assets, auth.
- **API** (`api/`): Django REST Framework with `routes.py` (DefaultRouter + SimpleRouter), ViewSets, token auth (`LinkdingTokenAuthentication`). Endpoints at `/api/bookmarks/`, `/api/tags/`, `/api/bundles/`, `/api/user/`.
- **Background tasks** (`services/tasks.py`): Huey tasks for favicon loading, preview images, HTML snapshots, web archive submissions.
- **Settings** (`settings/`): `base.py` (shared), `dev.py` (DEBUG=True), `prod.py` (production), `custom.py` (user overrides). Test settings module: `bookmarks.settings.dev`.

### Frontend

- **Components** (`frontend/components/`): Lit 3 web components — `tag-autocomplete.js`, `search-autocomplete.js`, `bookmark-page.js`, `details-modal.js`, `filter-drawer.js`, etc.
- **Styles** (`styles/`): PostCSS with nesting, bundled via Rollup.
- **Build output**: `static/bundle.js` and `static/bundle.css`.
- **Navigation**: Hotwired Turbo for page transitions without full reloads.
- **Custom HTML elements**: Templates use `ld-*` prefixed elements (e.g., `ld-button`, `ld-button-group`), registered in djlint config.

### URL Structure

All app URLs are namespaced under `linkding:` (e.g., `linkding:bookmarks.index`). Auth URLs (`login`, `logout`) are at the root. The optional `LD_CONTEXT_PATH` setting prefixes all URLs.

### Start Page App (`startpage/`)

Separate Django app on branch `feature/start-page`. Provides a browser start page with configurable widgets.

- **Models** (`startpage/models.py`): `StartPage` (hub cards with domain grouping setting), `StartPageWidget` (bundle/tag/filter type, FK to `bookmarks.BookmarkBundle`).
- **Queries** (`startpage/queries.py`): `query_widget_bookmarks()` delegates to `bookmarks.queries`, `group_bookmarks_by_domain()` groups in Python from URL.
- **Views** (`startpage/views.py`): Hub at `/start/`, detail at `/start/<id>/`, full CRUD for pages and widgets.
- **Frontend**: `ld-start-widget` (collapse/expand), `ld-widget-form` (conditional fields). CSS in `bookmarks/styles/start-page.css`.
- **URL namespace**: `startpage:` (e.g., `startpage:hub`, `startpage:detail`).
- **Management command**: `python manage.py setup_startpage [--user USERNAME]` seeds default pages.
- **Tests**: `startpage/tests/` — 47 tests covering models, queries, views.

## Testing

- Unit/integration tests in `bookmarks/tests/` — pytest-django with parallel execution via pytest-xdist.
- E2E tests in `bookmarks/tests_e2e/` — Playwright, file pattern `e2e_test_*.py`.
- Tests use `bookmarks.settings.dev` (from `pytest.ini`).

## Linting

- **Python**: ruff (E, F, UP, B, SIM, I rules; E501 line length ignored)
- **Templates**: djlint with Django profile
- **JS/CSS**: Prettier
