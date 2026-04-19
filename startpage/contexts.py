from django.db import models
from django.db.models import Count

from startpage.models import SmartLink, StartPage, StartPageWidget
from startpage.queries import group_bookmarks_by_domain, query_widget_bookmarks
from startpage.services import get_smart_link_data
from startpage.utils import extract_domain, get_registrable_domain


class StartPageBookmarkItem:
    def __init__(self, bookmark, profile):
        self.id = bookmark.id
        self.url = bookmark.url
        self.title = bookmark.resolved_title
        self.favicon_file = bookmark.favicon_file


class WidgetContext:
    def __init__(self, widget, user, profile, page_id=None):
        self.widget = widget
        self.id = widget.id
        self.name = widget.name

        qs = query_widget_bookmarks(user, profile, widget)
        bookmarks = list(qs[: widget.max_items])
        models.prefetch_related_objects(bookmarks, "tags")

        self.total_count = qs.count()
        self.show_favicons = profile.enable_favicons
        self.link_target = profile.bookmark_link_target

        grouping = widget.domain_grouping
        if grouping != StartPageWidget.DOMAIN_GROUPING_OFF:
            groups = group_bookmarks_by_domain(bookmarks, grouping)
            multi_groups = []
            leaf_bookmarks = []
            for group in groups:
                if group.count == 1:
                    leaf_bookmarks.append(group.bookmarks[0])
                else:
                    group.page_id = page_id
                    multi_groups.append(group)
            self.groups = multi_groups
            self.leaf_items = [
                StartPageBookmarkItem(bm, profile) for bm in leaf_bookmarks
            ]
            self.items = None
        else:
            self.groups = None
            self.leaf_items = None
            self.items = [StartPageBookmarkItem(bm, profile) for bm in bookmarks]


class StartPageHubContext:
    def __init__(self, request):
        self.pages = (
            StartPage.objects.filter(owner=request.user)
            .annotate(widget_count=Count("widgets"))
            .order_by("order")
        )
        self.is_empty = not self.pages.exists()


class StartPageDetailContext:
    def __init__(self, request, start_page):
        self.start_page = start_page
        self.name = start_page.name

        user = request.user
        profile = request.user_profile
        widgets = StartPageWidget.objects.filter(start_page=start_page).order_by(
            "order"
        )

        self.widgets = [
            WidgetContext(w, user, profile, page_id=start_page.id) for w in widgets
        ]

        smart_links = SmartLink.objects.filter(start_page=start_page).order_by("order")
        self.smart_links = [get_smart_link_data(sl) for sl in smart_links]

        self.is_empty = len(self.widgets) == 0 and len(self.smart_links) == 0
        self.show_favicons = profile.enable_favicons
        self.link_target = profile.bookmark_link_target


class DomainDetailContext:
    def __init__(self, request, start_page, domain_key):
        self.start_page = start_page
        self.domain_key = domain_key

        user = request.user
        profile = request.user_profile

        # Collect bookmarks from widgets with grouping enabled, matching this domain key
        filtered = []
        seen_ids = set()
        widgets = StartPageWidget.objects.filter(start_page=start_page).order_by(
            "order"
        )
        for widget in widgets:
            grouping = widget.domain_grouping
            if grouping == StartPageWidget.DOMAIN_GROUPING_OFF:
                continue
            qs = query_widget_bookmarks(user, profile, widget)
            bookmarks = list(qs[: widget.max_items])
            models.prefetch_related_objects(bookmarks, "tags")
            for bm in bookmarks:
                if bm.id in seen_ids:
                    continue
                domain = extract_domain(bm.url)
                key = (
                    domain
                    if grouping == StartPageWidget.DOMAIN_GROUPING_SUBDOMAIN
                    else get_registrable_domain(domain)
                )
                if key == domain_key:
                    filtered.append(bm)
                    seen_ids.add(bm.id)

        self.items = [StartPageBookmarkItem(bm, profile) for bm in filtered]
        self.total_count = len(self.items)
        self.domain_url = f"https://{domain_key}" if domain_key != "(no domain)" else ""
        self.show_favicons = profile.enable_favicons
        self.link_target = profile.bookmark_link_target
