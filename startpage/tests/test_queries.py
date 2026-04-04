from django.test import TestCase

from bookmarks.tests.helpers import BookmarkFactoryMixin
from startpage.models import StartPage, StartPageWidget
from startpage.queries import group_bookmarks_by_domain, query_widget_bookmarks
from startpage.utils import extract_domain, get_registrable_domain


class ExtractDomainTestCase(TestCase):
    def test_basic_url(self):
        self.assertEqual(extract_domain("https://example.com/path"), "example.com")

    def test_with_subdomain(self):
        self.assertEqual(
            extract_domain("https://www.example.com/page"), "www.example.com"
        )

    def test_with_port(self):
        self.assertEqual(extract_domain("https://example.com:8080/path"), "example.com")

    def test_case_insensitive(self):
        self.assertEqual(extract_domain("https://EXAMPLE.COM"), "example.com")

    def test_empty_url(self):
        self.assertEqual(extract_domain(""), "")
        self.assertEqual(extract_domain(None), "")

    def test_invalid_url(self):
        self.assertEqual(extract_domain("not-a-url"), "")


class GetRegistrableDomainTestCase(TestCase):
    def test_simple_domain(self):
        self.assertEqual(get_registrable_domain("example.com"), "example.com")

    def test_strip_www(self):
        self.assertEqual(get_registrable_domain("www.example.com"), "example.com")

    def test_strip_subdomain(self):
        self.assertEqual(get_registrable_domain("blog.example.com"), "example.com")

    def test_two_part_tld(self):
        self.assertEqual(get_registrable_domain("www.example.co.uk"), "example.co.uk")

    def test_polish_tld(self):
        self.assertEqual(
            get_registrable_domain("nopgo.noclegi.com.pl"), "noclegi.com.pl"
        )

    def test_single_part(self):
        self.assertEqual(get_registrable_domain("localhost"), "localhost")

    def test_empty(self):
        self.assertEqual(get_registrable_domain(""), "")
        self.assertIsNone(get_registrable_domain(None))


class QueryWidgetBookmarksTestCase(TestCase, BookmarkFactoryMixin):
    def setUp(self):
        self.user = self.get_or_create_test_user()
        self.page = StartPage.objects.create(name="Test", owner=self.user)

    def test_bundle_type(self):
        tag = self.setup_tag(name="django")
        bookmark = self.setup_bookmark(tags=[tag])
        bundle = self.setup_bundle(all_tags="django")
        widget = StartPageWidget.objects.create(
            start_page=self.page,
            name="W",
            widget_type=StartPageWidget.WIDGET_TYPE_BUNDLE,
            bundle=bundle,
        )

        qs = query_widget_bookmarks(self.user, self.user.profile, widget)
        self.assertIn(bookmark, list(qs))

    def test_tag_type(self):
        tag = self.setup_tag(name="python")
        bookmark = self.setup_bookmark(tags=[tag])
        self.setup_bookmark()  # no tag

        widget = StartPageWidget.objects.create(
            start_page=self.page,
            name="W",
            widget_type=StartPageWidget.WIDGET_TYPE_TAG,
            tag_name="python",
        )

        qs = query_widget_bookmarks(self.user, self.user.profile, widget)
        results = list(qs)
        self.assertIn(bookmark, results)
        self.assertEqual(len(results), 1)

    def test_filter_type(self):
        bookmark = self.setup_bookmark(title="Important thing")
        self.setup_bookmark(title="Other thing")

        widget = StartPageWidget.objects.create(
            start_page=self.page,
            name="W",
            widget_type=StartPageWidget.WIDGET_TYPE_FILTER,
            filter_query="Important",
        )

        qs = query_widget_bookmarks(self.user, self.user.profile, widget)
        results = list(qs)
        self.assertIn(bookmark, results)
        self.assertEqual(len(results), 1)


class GroupBookmarksByDomainTestCase(TestCase, BookmarkFactoryMixin):
    def setUp(self):
        self.user = self.get_or_create_test_user()

    def test_group_by_domain(self):
        bm1 = self.setup_bookmark(url="https://www.example.com/page1")
        bm2 = self.setup_bookmark(url="https://blog.example.com/page2")
        bm3 = self.setup_bookmark(url="https://other.org/page")

        groups = group_bookmarks_by_domain([bm1, bm2, bm3], "domain")

        self.assertEqual(len(groups), 2)
        self.assertEqual(groups[0].domain, "example.com")
        self.assertEqual(groups[0].count, 2)
        self.assertEqual(groups[1].domain, "other.org")
        self.assertEqual(groups[1].count, 1)

    def test_group_by_subdomain(self):
        bm1 = self.setup_bookmark(url="https://www.example.com/page1")
        bm2 = self.setup_bookmark(url="https://blog.example.com/page2")

        groups = group_bookmarks_by_domain([bm1, bm2], "subdomain")

        self.assertEqual(len(groups), 2)
        self.assertEqual(groups[0].domain, "www.example.com")
        self.assertEqual(groups[1].domain, "blog.example.com")

    def test_empty_list(self):
        groups = group_bookmarks_by_domain([], "domain")
        self.assertEqual(groups, [])

    def test_no_domain(self):
        bm = self.setup_bookmark(url="javascript:void(0)")

        groups = group_bookmarks_by_domain([bm], "domain")

        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].domain, "(no domain)")
