"""Markdown renderers for start page previews and docs."""

from pathlib import Path

from django.http import HttpResponse

from startpage.models import StartPage


def render_page_markdown(page: StartPage, widgets: list, smart_links: list) -> str:
    """Render a start page snapshot as markdown for LLM / agent consumption."""
    lines = [f"# {page.name}", ""]
    if not widgets and not smart_links:
        lines.append("_(empty page — no widgets or smart links)_")
        return "\n".join(lines) + "\n"

    for w in widgets:
        lines.append(f"## {w['name']}  _(widget: {w['widget_type']})_")
        lines.append("")
        if "domain_groups" in w:
            for group in w["domain_groups"]:
                lines.append(f"### {group.domain}  ({group.count})")
                for bm in group.bookmarks:
                    lines.append(_bookmark_line(bm))
                lines.append("")
        else:
            bookmarks = w.get("bookmarks", [])
            if not bookmarks:
                lines.append("_(no bookmarks)_")
            for bm in bookmarks:
                lines.append(_bookmark_line(bm))
            lines.append("")

    if smart_links:
        lines.append("## Smart links")
        lines.append("")
        for sl in smart_links:
            params = ", ".join(p["name"] for p in sl["parameters"])
            suffix = f" — params: {params}" if params else ""
            lines.append(f"- **{sl['name']}** — `{sl['url_template']}`{suffix}")
        lines.append("")

    return "\n".join(lines) + "\n"


def _bookmark_line(bookmark) -> str:
    title = bookmark.resolved_title.replace("]", "\\]")
    tag_names = [t.name for t in bookmark.tags.all()]
    tags = " ".join(f"#{name}" for name in tag_names)
    suffix = f" — {tags}" if tags else ""
    return f"- [{title}]({bookmark.url}){suffix}"


def serve_guide(request) -> HttpResponse:
    """Serve the static markdown curl cheatsheet."""
    path = Path(__file__).parent.parent / "docs" / "api.md"
    return HttpResponse(
        path.read_text(encoding="utf-8"),
        content_type="text/markdown; charset=utf-8",
    )


def api_docs_index(request) -> HttpResponse:
    """Mini landing page listing all available docs endpoints."""
    from django.template.response import TemplateResponse

    return TemplateResponse(request, "startpage/api_docs_index.html", {})
