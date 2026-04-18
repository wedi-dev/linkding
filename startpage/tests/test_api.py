from django.urls import reverse
from rest_framework import status

from bookmarks.tests.helpers import BookmarkFactoryMixin, LinkdingApiTestCase
from startpage.models import SmartLink, StartPage, StartPageWidget


class StartPageApiAuthTestCase(LinkdingApiTestCase, BookmarkFactoryMixin):
    def test_unauthenticated_requests_are_rejected(self):
        url = reverse("startpage:pages-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_auth_works(self):
        self.authenticate()
        url = reverse("startpage:pages-list")
        self.get(url, expected_status_code=status.HTTP_200_OK)

    def test_bearer_keyword_is_accepted(self):
        self.authenticate()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.api_token.key)
        url = reverse("startpage:pages-list")
        self.get(url, expected_status_code=status.HTTP_200_OK)


class StartPageApiTestCase(LinkdingApiTestCase, BookmarkFactoryMixin):
    def setUp(self):
        self.authenticate()

    def test_create_and_list(self):
        url = reverse("startpage:pages-list")
        self.post(
            url,
            {"name": "Work", "domain_grouping": "domain"},
            expected_status_code=status.HTTP_201_CREATED,
        )
        self.post(
            url,
            {"name": "Personal"},
            expected_status_code=status.HTTP_201_CREATED,
        )
        response = self.get(url)
        results = response.data["results"]
        self.assertEqual([p["name"] for p in results], ["Work", "Personal"])
        self.assertEqual(results[0]["order"], 0)
        self.assertEqual(results[1]["order"], 1)

    def test_owner_isolation(self):
        other = self.setup_user()
        StartPage.objects.create(name="Other", owner=other)
        url = reverse("startpage:pages-list")
        response = self.get(url)
        self.assertEqual(response.data["count"], 0)

    def test_cannot_retrieve_other_users_page(self):
        other = self.setup_user()
        page = StartPage.objects.create(name="Other", owner=other)
        url = reverse("startpage:pages-detail", args=[page.id])
        self.get(url, expected_status_code=status.HTTP_404_NOT_FOUND)

    def test_update(self):
        page = StartPage.objects.create(name="Work", owner=self.user)
        url = reverse("startpage:pages-detail", args=[page.id])
        self.patch(url, {"name": "Renamed"})
        page.refresh_from_db()
        self.assertEqual(page.name, "Renamed")

    def test_delete(self):
        page = StartPage.objects.create(name="Work", owner=self.user)
        url = reverse("startpage:pages-detail", args=[page.id])
        self.delete(url, expected_status_code=status.HTTP_204_NO_CONTENT)
        self.assertFalse(StartPage.objects.filter(pk=page.id).exists())


class WidgetApiTestCase(LinkdingApiTestCase, BookmarkFactoryMixin):
    def setUp(self):
        self.authenticate()
        self.page = StartPage.objects.create(name="Work", owner=self.user)

    def test_create_tag_widget(self):
        url = reverse("startpage:widgets-list")
        response = self.post(
            url,
            {
                "start_page": self.page.id,
                "name": "Docs",
                "widget_type": "tag",
                "tag_name": "docs",
            },
            expected_status_code=status.HTTP_201_CREATED,
        )
        widget = StartPageWidget.objects.get(pk=response.data["id"])
        self.assertEqual(widget.tag_name, "docs")
        self.assertEqual(widget.order, 0)

    def test_create_bundle_widget_requires_bundle(self):
        url = reverse("startpage:widgets-list")
        self.post(
            url,
            {
                "start_page": self.page.id,
                "name": "Bad",
                "widget_type": "bundle",
            },
            expected_status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_create_tag_widget_requires_tag_name(self):
        url = reverse("startpage:widgets-list")
        self.post(
            url,
            {
                "start_page": self.page.id,
                "name": "Bad",
                "widget_type": "tag",
            },
            expected_status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_cannot_attach_widget_to_other_users_page(self):
        other = self.setup_user()
        other_page = StartPage.objects.create(name="Other", owner=other)
        url = reverse("startpage:widgets-list")
        self.post(
            url,
            {
                "start_page": other_page.id,
                "name": "X",
                "widget_type": "tag",
                "tag_name": "x",
            },
            expected_status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_cannot_use_other_users_bundle(self):
        other = self.setup_user()
        other_bundle = self.setup_bundle(user=other, name="Other")
        url = reverse("startpage:widgets-list")
        self.post(
            url,
            {
                "start_page": self.page.id,
                "name": "X",
                "widget_type": "bundle",
                "bundle": other_bundle.id,
            },
            expected_status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_filter_by_start_page(self):
        StartPageWidget.objects.create(
            start_page=self.page,
            name="A",
            widget_type="tag",
            tag_name="a",
        )
        other_page = StartPage.objects.create(name="Other", owner=self.user)
        StartPageWidget.objects.create(
            start_page=other_page,
            name="B",
            widget_type="tag",
            tag_name="b",
        )
        url = reverse("startpage:widgets-list") + f"?start_page={self.page.id}"
        response = self.get(url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "A")


class SmartLinkApiTestCase(LinkdingApiTestCase, BookmarkFactoryMixin):
    def setUp(self):
        self.authenticate()
        self.page = StartPage.objects.create(name="Work", owner=self.user)

    def test_create_parses_parameters_from_template(self):
        url = reverse("startpage:smart-links-list")
        response = self.post(
            url,
            {
                "start_page": self.page.id,
                "name": "Jira",
                "url_template": "https://jira.example.com/browse/{ticket:Ticket number}",
            },
            expected_status_code=status.HTTP_201_CREATED,
        )
        params = response.data["parameters"]
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0]["name"], "ticket")
        self.assertEqual(params[0]["label"], "Ticket number")

    def test_update_reflects_new_parameters(self):
        sl = SmartLink.objects.create(
            start_page=self.page,
            owner=self.user,
            name="Jira",
            url_template="https://jira.example.com/browse/{ticket}",
        )
        url = reverse("startpage:smart-links-detail", args=[sl.id])
        response = self.patch(
            url,
            {
                "url_template": "https://jira.example.com/browse/{ticket}/{tab:Tab name}",
            },
        )
        param_names = [p["name"] for p in response.data["parameters"]]
        self.assertEqual(param_names, ["ticket", "tab"])


class PreviewApiTestCase(LinkdingApiTestCase, BookmarkFactoryMixin):
    def setUp(self):
        self.authenticate()
        self.page = StartPage.objects.create(name="Work", owner=self.user)
        tag = self.setup_tag(name="docs")
        self.bookmark = self.setup_bookmark(tags=[tag], title="Cool bookmark")
        StartPageWidget.objects.create(
            start_page=self.page,
            name="Docs",
            widget_type="tag",
            tag_name="docs",
        )

    def test_preview_json(self):
        url = reverse("startpage:pages-preview", args=[self.page.id])
        response = self.get(url)
        self.assertEqual(response.data["name"], "Work")
        self.assertEqual(len(response.data["widgets"]), 1)
        widget = response.data["widgets"][0]
        self.assertEqual(widget["name"], "Docs")
        titles = [b["title"] for b in widget["bookmarks"]]
        self.assertIn("Cool bookmark", titles)

    def test_preview_markdown_via_accept_header(self):
        url = reverse("startpage:pages-preview", args=[self.page.id])
        response = self.client.get(url, HTTP_ACCEPT="text/markdown")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("text/markdown", response["Content-Type"])
        body = response.content.decode("utf-8")
        self.assertIn("# Work", body)
        self.assertIn("## Docs", body)
        self.assertIn("Cool bookmark", body)
        self.assertIn("#docs", body)

    def test_preview_markdown_via_format_query(self):
        url = reverse("startpage:pages-preview", args=[self.page.id]) + "?format=md"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("text/markdown", response["Content-Type"])


class ApiDocsTestCase(LinkdingApiTestCase, BookmarkFactoryMixin):
    def test_openapi_schema_is_served(self):
        self.authenticate()
        url = reverse("startpage:api_docs.schema")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.content.decode("utf-8")
        self.assertIn("linkding API", body)
        # includes both startpage and bookmarks endpoints
        self.assertIn("/start/api/pages/", body)
        self.assertIn("/api/bookmarks/", body)

    def test_guide_markdown_is_served(self):
        self.authenticate()
        url = reverse("startpage:api_docs.guide")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("text/markdown", response["Content-Type"])
        self.assertIn("linkding API", response.content.decode("utf-8"))

    def test_docs_index_is_served(self):
        self.authenticate()
        url = reverse("startpage:api_docs.index")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
