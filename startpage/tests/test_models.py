from django.test import TestCase

from bookmarks.tests.helpers import BookmarkFactoryMixin
from startpage.models import StartPage, StartPageWidget


class StartPageModelTestCase(TestCase, BookmarkFactoryMixin):
    def setUp(self):
        self.user = self.get_or_create_test_user()

    def test_create_start_page(self):
        page = StartPage.objects.create(name="Test Page", owner=self.user)
        self.assertEqual(page.name, "Test Page")
        self.assertEqual(page.order, 0)
        self.assertEqual(page.owner, self.user)

    def test_ordering(self):
        page1 = StartPage.objects.create(name="Page 1", order=1, owner=self.user)
        page2 = StartPage.objects.create(name="Page 2", order=0, owner=self.user)
        pages = list(StartPage.objects.filter(owner=self.user))
        self.assertEqual(pages[0], page2)
        self.assertEqual(pages[1], page1)


class StartPageWidgetModelTestCase(TestCase, BookmarkFactoryMixin):
    def setUp(self):
        self.user = self.get_or_create_test_user()
        self.page = StartPage.objects.create(name="Test Page", owner=self.user)

    def test_create_widget_bundle_type(self):
        bundle = self.setup_bundle()
        widget = StartPageWidget.objects.create(
            start_page=self.page,
            name="Bundle Widget",
            widget_type=StartPageWidget.WIDGET_TYPE_BUNDLE,
            bundle=bundle,
        )
        self.assertEqual(widget.name, "Bundle Widget")
        self.assertEqual(widget.bundle, bundle)
        self.assertEqual(widget.domain_grouping, StartPageWidget.DOMAIN_GROUPING_OFF)

    def test_widget_domain_grouping_default_and_set(self):
        widget = StartPageWidget.objects.create(
            start_page=self.page,
            name="W",
            widget_type=StartPageWidget.WIDGET_TYPE_FILTER,
            domain_grouping=StartPageWidget.DOMAIN_GROUPING_DOMAIN,
        )
        self.assertEqual(widget.domain_grouping, "domain")

    def test_create_widget_tag_type(self):
        widget = StartPageWidget.objects.create(
            start_page=self.page,
            name="Tag Widget",
            widget_type=StartPageWidget.WIDGET_TYPE_TAG,
            tag_name="python",
        )
        self.assertEqual(widget.tag_name, "python")

    def test_create_widget_filter_type(self):
        widget = StartPageWidget.objects.create(
            start_page=self.page,
            name="Filter Widget",
            widget_type=StartPageWidget.WIDGET_TYPE_FILTER,
            filter_query="test query",
        )
        self.assertEqual(widget.filter_query, "test query")

    def test_widget_ordering(self):
        w1 = StartPageWidget.objects.create(
            start_page=self.page, name="W1", widget_type="filter", order=1
        )
        w2 = StartPageWidget.objects.create(
            start_page=self.page, name="W2", widget_type="filter", order=0
        )
        widgets = list(StartPageWidget.objects.filter(start_page=self.page))
        self.assertEqual(widgets[0], w2)
        self.assertEqual(widgets[1], w1)

    def test_cascade_delete_page(self):
        StartPageWidget.objects.create(
            start_page=self.page, name="W", widget_type="filter"
        )
        self.page.delete()
        self.assertEqual(StartPageWidget.objects.count(), 0)
