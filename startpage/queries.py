from collections import OrderedDict
from dataclasses import dataclass

from bookmarks.models import Bookmark, BookmarkSearch
from bookmarks.queries import query_bookmarks
from startpage.models import StartPageWidget
from startpage.utils import extract_domain, get_registrable_domain


@dataclass
class DomainGroup:
    domain: str
    domain_url: str
    bookmarks: list
    count: int


def query_widget_bookmarks(user, profile, widget):
    if widget.widget_type == StartPageWidget.WIDGET_TYPE_BUNDLE:
        search = BookmarkSearch(bundle=widget.bundle, sort=widget.sort)
    elif widget.widget_type == StartPageWidget.WIDGET_TYPE_TAG:
        search = BookmarkSearch(q=f"#{widget.tag_name}", sort=widget.sort)
    elif widget.widget_type == StartPageWidget.WIDGET_TYPE_FILTER:
        search = BookmarkSearch(
            q=widget.filter_query,
            sort=widget.sort,
            unread=widget.filter_unread,
            shared=widget.filter_shared,
        )
    else:
        return Bookmark.objects.none()
    return query_bookmarks(user, profile, search)


def group_bookmarks_by_domain(bookmarks, grouping_mode):
    groups = OrderedDict()
    for bm in bookmarks:
        domain = extract_domain(bm.url)
        key = domain if grouping_mode == "subdomain" else get_registrable_domain(domain)
        if not key:
            key = "(no domain)"
        groups.setdefault(key, []).append(bm)

    return [
        DomainGroup(
            domain=k,
            domain_url=f"https://{k}" if k != "(no domain)" else "",
            bookmarks=v,
            count=len(v),
        )
        for k, v in groups.items()
    ]
