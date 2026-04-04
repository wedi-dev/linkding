from django.test import TestCase
from django.urls import reverse

from bookmarks.tests.helpers import BookmarkFactoryMixin
from startpage.models import StartPage, StartPageWidget


class HubViewTestCase(TestCase, BookmarkFactoryMixin):
    def setUp(self):
        self.user = self.get_or_create_test_user()
        self.client.force_login(self.user)

    def test_renders_page_list(self):
        StartPage.objects.create(name="My Page", owner=self.user)

        response = self.client.get(reverse("startpage:hub"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Page")

    def test_empty_state(self):
        response = self.client.get(reverse("startpage:hub"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You have no start pages yet")

    def test_only_shows_own_pages(self):
        StartPage.objects.create(name="My Page", owner=self.user)
        other_user = self.setup_user()
        StartPage.objects.create(name="Other Page", owner=other_user)

        response = self.client.get(reverse("startpage:hub"))

        self.assertContains(response, "My Page")
        self.assertNotContains(response, "Other Page")

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("startpage:hub"))
        self.assertEqual(response.status_code, 302)


class DetailViewTestCase(TestCase, BookmarkFactoryMixin):
    def setUp(self):
        self.user = self.get_or_create_test_user()
        self.client.force_login(self.user)

    def test_renders_page(self):
        page = StartPage.objects.create(name="My Page", owner=self.user)

        response = self.client.get(reverse("startpage:detail", args=[page.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Page")

    def test_renders_widget_with_bookmarks(self):
        page = StartPage.objects.create(name="My Page", owner=self.user)
        tag = self.setup_tag(name="test-tag")
        self.setup_bookmark(tags=[tag], title="Test Bookmark")
        StartPageWidget.objects.create(
            start_page=page,
            name="Tag Widget",
            widget_type=StartPageWidget.WIDGET_TYPE_TAG,
            tag_name="test-tag",
        )

        response = self.client.get(reverse("startpage:detail", args=[page.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tag Widget")
        self.assertContains(response, "Test Bookmark")

    def test_renders_domain_groups(self):
        page = StartPage.objects.create(
            name="Grouped",
            owner=self.user,
            domain_grouping=StartPage.DOMAIN_GROUPING_DOMAIN,
        )
        self.setup_bookmark(url="https://example.com/a", title="Link A")
        self.setup_bookmark(url="https://example.com/b", title="Link B")
        self.setup_bookmark(url="https://other.org/c", title="Link C")
        StartPageWidget.objects.create(
            start_page=page,
            name="All",
            widget_type=StartPageWidget.WIDGET_TYPE_FILTER,
            filter_query="",
        )

        response = self.client.get(reverse("startpage:detail", args=[page.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "example.com")
        self.assertContains(response, "other.org")

    def test_404_on_other_users_page(self):
        other_user = self.setup_user()
        page = StartPage.objects.create(name="Other", owner=other_user)

        response = self.client.get(reverse("startpage:detail", args=[page.id]))

        self.assertEqual(response.status_code, 404)

    def test_404_on_invalid_id(self):
        response = self.client.get(reverse("startpage:detail", args=[999]))
        self.assertEqual(response.status_code, 404)


class DomainDetailViewTestCase(TestCase, BookmarkFactoryMixin):
    def setUp(self):
        self.user = self.get_or_create_test_user()
        self.client.force_login(self.user)

    def test_renders_domain_bookmarks(self):
        page = StartPage.objects.create(
            name="Test",
            owner=self.user,
            domain_grouping=StartPage.DOMAIN_GROUPING_DOMAIN,
        )
        self.setup_bookmark(url="https://example.com/a", title="Link A")
        self.setup_bookmark(url="https://example.com/b", title="Link B")
        self.setup_bookmark(url="https://other.org/c", title="Link C")
        StartPageWidget.objects.create(
            start_page=page,
            name="All",
            widget_type=StartPageWidget.WIDGET_TYPE_FILTER,
        )

        response = self.client.get(
            reverse("startpage:domain.detail", args=[page.id, "example.com"])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Link A")
        self.assertContains(response, "Link B")
        self.assertNotContains(response, "Link C")

    def test_404_on_other_users_page(self):
        other_user = self.setup_user()
        page = StartPage.objects.create(name="Other", owner=other_user)

        response = self.client.get(
            reverse("startpage:domain.detail", args=[page.id, "example.com"])
        )
        self.assertEqual(response.status_code, 404)


class PageNewViewTestCase(TestCase, BookmarkFactoryMixin):
    def setUp(self):
        self.user = self.get_or_create_test_user()
        self.client.force_login(self.user)

    def test_renders_form(self):
        response = self.client.get(reverse("startpage:page.new"))
        self.assertEqual(response.status_code, 200)

    def test_creates_page(self):
        response = self.client.post(
            reverse("startpage:page.new"),
            {"name": "New Page", "domain_grouping": "off"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(StartPage.objects.filter(name="New Page").exists())

    def test_validation_error(self):
        response = self.client.post(
            reverse("startpage:page.new"),
            {"name": "", "domain_grouping": "off"},
        )
        self.assertEqual(response.status_code, 422)


class PageEditViewTestCase(TestCase, BookmarkFactoryMixin):
    def setUp(self):
        self.user = self.get_or_create_test_user()
        self.client.force_login(self.user)
        self.page = StartPage.objects.create(name="Test", owner=self.user)

    def test_renders_form(self):
        response = self.client.get(reverse("startpage:page.edit", args=[self.page.id]))
        self.assertEqual(response.status_code, 200)

    def test_updates_page(self):
        response = self.client.post(
            reverse("startpage:page.edit", args=[self.page.id]),
            {"name": "Updated", "domain_grouping": "domain"},
        )
        self.assertEqual(response.status_code, 302)
        self.page.refresh_from_db()
        self.assertEqual(self.page.name, "Updated")
        self.assertEqual(self.page.domain_grouping, "domain")


class PageActionViewTestCase(TestCase, BookmarkFactoryMixin):
    def setUp(self):
        self.user = self.get_or_create_test_user()
        self.client.force_login(self.user)

    def test_remove_page(self):
        page = StartPage.objects.create(name="Test", owner=self.user)

        self.client.post(
            reverse("startpage:page.action"),
            {"remove_page": page.id},
        )

        self.assertFalse(StartPage.objects.filter(pk=page.id).exists())


class WidgetNewViewTestCase(TestCase, BookmarkFactoryMixin):
    def setUp(self):
        self.user = self.get_or_create_test_user()
        self.client.force_login(self.user)
        self.page = StartPage.objects.create(name="Test", owner=self.user)

    def test_renders_form(self):
        response = self.client.get(reverse("startpage:widget.new", args=[self.page.id]))
        self.assertEqual(response.status_code, 200)

    def test_creates_widget(self):
        response = self.client.post(
            reverse("startpage:widget.new", args=[self.page.id]),
            {
                "name": "New Widget",
                "widget_type": "filter",
                "filter_query": "",
                "filter_unread": "off",
                "filter_shared": "off",
                "sort": "added_desc",
                "max_items": 20,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            StartPageWidget.objects.filter(
                start_page=self.page, name="New Widget"
            ).exists()
        )


class WidgetEditViewTestCase(TestCase, BookmarkFactoryMixin):
    def setUp(self):
        self.user = self.get_or_create_test_user()
        self.client.force_login(self.user)
        self.page = StartPage.objects.create(name="Test", owner=self.user)
        self.widget = StartPageWidget.objects.create(
            start_page=self.page,
            name="Widget",
            widget_type="filter",
        )

    def test_renders_form(self):
        response = self.client.get(
            reverse(
                "startpage:widget.edit",
                args=[self.page.id, self.widget.id],
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_updates_widget(self):
        response = self.client.post(
            reverse(
                "startpage:widget.edit",
                args=[self.page.id, self.widget.id],
            ),
            {
                "name": "Updated Widget",
                "widget_type": "filter",
                "filter_query": "test",
                "filter_unread": "off",
                "filter_shared": "off",
                "sort": "title_asc",
                "max_items": 10,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.widget.refresh_from_db()
        self.assertEqual(self.widget.name, "Updated Widget")
        self.assertEqual(self.widget.sort, "title_asc")


class WidgetActionViewTestCase(TestCase, BookmarkFactoryMixin):
    def setUp(self):
        self.user = self.get_or_create_test_user()
        self.client.force_login(self.user)
        self.page = StartPage.objects.create(name="Test", owner=self.user)

    def test_remove_widget(self):
        widget = StartPageWidget.objects.create(
            start_page=self.page,
            name="Widget",
            widget_type="filter",
        )

        self.client.post(
            reverse("startpage:widget.action", args=[self.page.id]),
            {"remove_widget": widget.id},
        )

        self.assertFalse(StartPageWidget.objects.filter(pk=widget.id).exists())
