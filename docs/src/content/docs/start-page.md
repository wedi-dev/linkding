---
title: "Start Page"
description: "Use linkding as your browser's start page with configurable widgets and domain grouping"
---

The Start Page feature lets you set linkding as your browser's start page. It provides a hub of configurable pages, each with widgets that display your bookmarks in a mobile-friendly layout.

## Overview

The feature is structured as a hierarchy:

- **Hub** (`/start/`) — Lists all your start pages as large, tappable cards
- **Start Page** (`/start/<id>/`) — Shows widgets with bookmarks, optionally grouped by domain
- **Widgets** — Each widget displays bookmarks from a bundle, tag, or custom filter

The design goal is a **3-click flow**: tap a start page card → expand a domain group → open a bookmark.

## Creating a Start Page

1. Navigate to **Bookmarks → Start Page** in the navigation menu
2. Click **Add start page**
3. Give it a name and choose a domain grouping mode:
   - **Off** — Bookmarks shown in a flat list
   - **Domain** — Groups bookmarks by registrable domain (e.g., `www.example.com` and `blog.example.com` both appear under `example.com`)
   - **Subdomain** — Groups by full hostname (each subdomain is a separate group)
4. Click **Save**

## Adding Widgets

Each start page contains one or more widgets. To add a widget:

1. Open a start page and click **Add widget**
2. Choose the widget **type**:
   - **Bundle** — Shows bookmarks matching an existing bundle's filters
   - **Tag** — Shows bookmarks with a specific tag
   - **Custom filter** — Define a search query with optional reading/sharing state filters
3. Configure **Sort** order (newest, oldest, A-Z, Z-A)
4. Set **Max items** — how many bookmarks to display (default: 20)

## Domain Grouping

When domain grouping is enabled on a start page, bookmarks within each widget are grouped by domain. Each domain group shows:

- The domain name and bookmark count
- An external link icon (↗) that opens the domain directly
- A collapsible list of bookmarks from that domain

Groups with a single bookmark are expanded by default. Tap any group header to expand or collapse it.

## Setting as Browser Start Page

Set your browser's homepage to your linkding instance's `/start/` URL. For example:

```
https://your-linkding-instance/start/
```

## Quick Setup

Use the management command to create a default start page with widgets based on your existing data:

```bash
# For a specific user
python manage.py setup_startpage --user yourname

# For all users
python manage.py setup_startpage
```

This creates a start page with:
- One widget per existing bundle (if you have bundles)
- Widgets for your most-used tags (if no bundles)
- A generic "All bookmarks" widget (fallback)

## Mobile Experience

The start page is designed mobile-first:
- Hub cards and bookmark items have large touch targets (48px+ height)
- Domain groups use native HTML `<details>` elements for accessible expand/collapse
- Layout is single-column on mobile, two-column on wider screens
- Widget headers are tappable to collapse/expand entire widgets
