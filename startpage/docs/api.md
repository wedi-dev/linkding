# linkding API — curl cheatsheet

This guide covers every HTTP endpoint linkding exposes: bookmarks, tags, bundles,
user profile, and the start page (pages, widgets, smart links). All endpoints
share the same auth scheme.

Interactive browser: `/start/api-docs/swagger/` (Swagger UI) or
`/start/api-docs/redoc/` (Redoc). Raw OpenAPI: `/start/api-docs/schema.yaml`.

---

## 1. Auth

1. Log in, go to **Settings → Integrations**, click *Create API token*.
2. Copy the token (shown once). Example: `0123456789abcdef...`
3. Pass it in every request:

```bash
export LD_BASE=http://localhost:8000
export LD_TOK=0123456789abcdef...

curl -H "Authorization: Token $LD_TOK" $LD_BASE/api/user/profile/
```

`Bearer` works as an alias for `Token` — both are accepted.

All endpoints require authentication except the public shared-bookmarks feed.

Pagination: list endpoints return `{count, next, previous, results}` and accept
`?limit=<n>&offset=<n>` (default page size is 100).

---

## 2. Bookmarks (`/api/bookmarks/`)

```bash
# List — supports ?q=<search>, ?limit=, ?offset=
curl -H "Authorization: Token $LD_TOK" "$LD_BASE/api/bookmarks/?limit=5"

# List archived
curl -H "Authorization: Token $LD_TOK" "$LD_BASE/api/bookmarks/archived/"

# Retrieve one
curl -H "Authorization: Token $LD_TOK" "$LD_BASE/api/bookmarks/42/"

# Create
curl -X POST -H "Authorization: Token $LD_TOK" -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "title": "Example",
    "description": "optional",
    "notes": "optional markdown notes",
    "tag_names": ["example", "demo"],
    "unread": false,
    "shared": false
  }' \
  "$LD_BASE/api/bookmarks/"

# Update (PATCH — partial)
curl -X PATCH -H "Authorization: Token $LD_TOK" -H "Content-Type: application/json" \
  -d '{"tag_names": ["renamed"]}' \
  "$LD_BASE/api/bookmarks/42/"

# Archive / unarchive
curl -X POST -H "Authorization: Token $LD_TOK" "$LD_BASE/api/bookmarks/42/archive/"
curl -X POST -H "Authorization: Token $LD_TOK" "$LD_BASE/api/bookmarks/42/unarchive/"

# Delete
curl -X DELETE -H "Authorization: Token $LD_TOK" "$LD_BASE/api/bookmarks/42/"

# Check if a URL is already bookmarked
curl -H "Authorization: Token $LD_TOK" \
  -G --data-urlencode "url=https://example.com" \
  "$LD_BASE/api/bookmarks/check/"
```

Tip: by default, linkding scrapes title/description when creating a bookmark.
Pass `?disable_scraping` on POST to skip the fetch.

---

## 3. Tags (`/api/tags/`)

```bash
# List
curl -H "Authorization: Token $LD_TOK" "$LD_BASE/api/tags/"

# Create (idempotent — returns existing tag if name is taken)
curl -X POST -H "Authorization: Token $LD_TOK" -H "Content-Type: application/json" \
  -d '{"name": "my-tag"}' \
  "$LD_BASE/api/tags/"
```

Note: tag names are per-user.

---

## 4. Bundles (`/api/bundles/`)

Bundles are saved searches combining tags + filters.

```bash
# List
curl -H "Authorization: Token $LD_TOK" "$LD_BASE/api/bundles/"

# Create
curl -X POST -H "Authorization: Token $LD_TOK" -H "Content-Type: application/json" \
  -d '{
    "name": "Work reading",
    "search": "",
    "any_tags": "work reading",
    "all_tags": "",
    "excluded_tags": "archived",
    "filter_unread": "yes",
    "filter_shared": "off"
  }' \
  "$LD_BASE/api/bundles/"

# Patch / delete
curl -X PATCH -H "Authorization: Token $LD_TOK" -H "Content-Type: application/json" \
  -d '{"name": "Renamed"}' "$LD_BASE/api/bundles/7/"
curl -X DELETE -H "Authorization: Token $LD_TOK" "$LD_BASE/api/bundles/7/"
```

---

## 5. User profile (`/api/user/profile/`)

```bash
curl -H "Authorization: Token $LD_TOK" "$LD_BASE/api/user/profile/"
```

Read-only. Returns theme, display preferences, sharing flags, app version.

---

## 6. Start pages (`/start/api/pages/`)

A start page is a dashboard with widgets (collections of bookmarks) and smart
links (URL templates with placeholders).

```bash
# List my pages
curl -H "Authorization: Token $LD_TOK" "$LD_BASE/start/api/pages/"

# Create
curl -X POST -H "Authorization: Token $LD_TOK" -H "Content-Type: application/json" \
  -d '{"name": "Work", "domain_grouping": "domain"}' \
  "$LD_BASE/start/api/pages/"
# domain_grouping: off | domain | subdomain

# Retrieve
curl -H "Authorization: Token $LD_TOK" "$LD_BASE/start/api/pages/1/"

# Update
curl -X PATCH -H "Authorization: Token $LD_TOK" -H "Content-Type: application/json" \
  -d '{"name": "Work dashboard"}' "$LD_BASE/start/api/pages/1/"

# Delete
curl -X DELETE -H "Authorization: Token $LD_TOK" "$LD_BASE/start/api/pages/1/"
```

### Preview a page as markdown (for LLM agents)

```bash
# JSON
curl -H "Authorization: Token $LD_TOK" "$LD_BASE/start/api/pages/1/preview/"

# Markdown — paste straight into an LLM context
curl -H "Authorization: Token $LD_TOK" -H "Accept: text/markdown" \
  "$LD_BASE/start/api/pages/1/preview/"

# Equivalent: append ?format=md
curl -H "Authorization: Token $LD_TOK" \
  "$LD_BASE/start/api/pages/1/preview/?format=md"
```

---

## 7. Widgets (`/start/api/widgets/`)

A widget renders bookmarks on a start page. Three types:

- `bundle` — uses a saved `BookmarkBundle` (pass `bundle: <id>`)
- `tag` — all bookmarks with a given tag (pass `tag_name`)
- `filter` — custom filter query (pass `filter_query`, optional
  `filter_unread` / `filter_shared`, both `off|yes|no`)

```bash
# List widgets on page 1
curl -H "Authorization: Token $LD_TOK" \
  "$LD_BASE/start/api/widgets/?start_page=1"

# Tag widget
curl -X POST -H "Authorization: Token $LD_TOK" -H "Content-Type: application/json" \
  -d '{
    "start_page": 1,
    "name": "Docs",
    "widget_type": "tag",
    "tag_name": "docs",
    "sort": "added_desc",
    "max_items": 15
  }' \
  "$LD_BASE/start/api/widgets/"

# Bundle widget (bundle must be owned by you)
curl -X POST -H "Authorization: Token $LD_TOK" -H "Content-Type: application/json" \
  -d '{
    "start_page": 1,
    "name": "Work reading",
    "widget_type": "bundle",
    "bundle": 7,
    "sort": "added_desc",
    "max_items": 20
  }' \
  "$LD_BASE/start/api/widgets/"

# Custom filter widget
curl -X POST -H "Authorization: Token $LD_TOK" -H "Content-Type: application/json" \
  -d '{
    "start_page": 1,
    "name": "Unread shared",
    "widget_type": "filter",
    "filter_query": "react",
    "filter_unread": "yes",
    "filter_shared": "yes",
    "sort": "title_asc"
  }' \
  "$LD_BASE/start/api/widgets/"

# Patch / delete
curl -X PATCH -H "Authorization: Token $LD_TOK" -H "Content-Type: application/json" \
  -d '{"max_items": 30}' "$LD_BASE/start/api/widgets/42/"
curl -X DELETE -H "Authorization: Token $LD_TOK" "$LD_BASE/start/api/widgets/42/"
```

Valid `sort` values: `added_desc`, `added_asc`, `title_asc`, `title_desc`.

---

## 8. Smart links (`/start/api/smart-links/`)

A smart link is a URL template with `{param}` or `{param:Label}` placeholders.
The user fills them in from the UI and linkding records recent values for
autocomplete.

```bash
# List on page 1
curl -H "Authorization: Token $LD_TOK" \
  "$LD_BASE/start/api/smart-links/?start_page=1"

# Create
curl -X POST -H "Authorization: Token $LD_TOK" -H "Content-Type: application/json" \
  -d '{
    "start_page": 1,
    "name": "Jira ticket",
    "url_template": "https://jira.example.com/browse/{ticket:Ticket number}"
  }' \
  "$LD_BASE/start/api/smart-links/"

# The response always echoes parsed parameters:
#   "parameters": [{"name": "ticket", "label": "Ticket number", "order": 0}]

# Update
curl -X PATCH -H "Authorization: Token $LD_TOK" -H "Content-Type: application/json" \
  -d '{"url_template": "https://jira.example.com/browse/{ticket}/{tab:Tab name}"}' \
  "$LD_BASE/start/api/smart-links/9/"

# Delete
curl -X DELETE -H "Authorization: Token $LD_TOK" "$LD_BASE/start/api/smart-links/9/"
```

Parameters are derived from the template — you don't manage them separately.
On update, values for parameter names that still exist in the new template are
preserved; removed names drop their history.

---

## 9. Gotchas

- **Trailing slash is required.** `/start/api/pages` (no slash) redirects to
  `/start/api/pages/`, which will break POSTs.
- **Owner isolation.** You cannot see or edit another user's pages, widgets,
  bookmarks or bundles — they return 404 (not 403).
- **Widget type validation.** `widget_type=bundle` requires a `bundle` id you
  own. `widget_type=tag` requires a non-empty `tag_name`.
- **`order` is managed server-side.** It auto-increments on create. Use the web
  UI drag-and-drop to reorder — the API does not currently expose a reorder
  endpoint.
- **Start page for a widget can't be changed** via PATCH. Delete and recreate.
- **Pagination.** Default page size is 100. Pass `?limit=<n>&offset=<n>` for
  custom pages.

---

## 10. Minimal LLM agent flow

```bash
# 1. Find out what exists
curl -H "Authorization: Token $LD_TOK" $LD_BASE/start/api/pages/

# 2. Grab a compact snapshot of the current state
curl -H "Authorization: Token $LD_TOK" -H "Accept: text/markdown" \
  $LD_BASE/start/api/pages/1/preview/

# 3. Mutate
curl -X POST -H "Authorization: Token $LD_TOK" -H "Content-Type: application/json" \
  -d '{"start_page":1,"name":"New widget","widget_type":"tag","tag_name":"ai"}' \
  $LD_BASE/start/api/widgets/

# 4. Re-grab the snapshot to verify
curl -H "Authorization: Token $LD_TOK" -H "Accept: text/markdown" \
  $LD_BASE/start/api/pages/1/preview/
```
