from django.test import TestCase
from django.urls import reverse

from bookmarks.tests.helpers import BookmarkFactoryMixin
from startpage.models import (
    SmartLink,
    SmartLinkParameter,
    SmartLinkValue,
    StartPage,
    parse_url_template,
    resolve_url_template,
)
from startpage.services import (
    create_smart_link,
    delete_smart_link,
    get_smart_link_data,
    move_smart_link,
    resolve_and_record,
    update_smart_link,
)


class ParseUrlTemplateTestCase(TestCase):
    def test_single_placeholder(self):
        result = parse_url_template("https://jira.com/browse/PAC-{ticket}")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "ticket")
        self.assertEqual(result[0]["label"], "")
        self.assertEqual(result[0]["order"], 0)

    def test_placeholder_with_label(self):
        result = parse_url_template(
            "https://jira.com/browse/PAC-{ticket:Ticket number}"
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "ticket")
        self.assertEqual(result[0]["label"], "Ticket number")

    def test_multiple_placeholders(self):
        result = parse_url_template(
            "https://github.com/{org:Organization}/{repo:Repository}/pull/{pr:PR number}"
        )
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["name"], "org")
        self.assertEqual(result[1]["name"], "repo")
        self.assertEqual(result[2]["name"], "pr")
        self.assertEqual(result[0]["order"], 0)
        self.assertEqual(result[1]["order"], 1)
        self.assertEqual(result[2]["order"], 2)

    def test_no_placeholders(self):
        result = parse_url_template("https://example.com/page")
        self.assertEqual(result, [])

    def test_whitespace_in_placeholder(self):
        result = parse_url_template("https://example.com/{ name : Label }")
        self.assertEqual(result[0]["name"], "name")
        self.assertEqual(result[0]["label"], "Label")


class ResolveUrlTemplateTestCase(TestCase):
    def test_single_placeholder(self):
        url = resolve_url_template(
            "https://jira.com/browse/PAC-{ticket}", {"ticket": "384"}
        )
        self.assertEqual(url, "https://jira.com/browse/PAC-384")

    def test_multiple_placeholders(self):
        url = resolve_url_template(
            "https://github.com/{org}/{repo}/pull/{pr}",
            {"org": "sissbruecker", "repo": "linkding", "pr": "42"},
        )
        self.assertEqual(url, "https://github.com/sissbruecker/linkding/pull/42")

    def test_missing_value_keeps_placeholder(self):
        url = resolve_url_template(
            "https://jira.com/browse/{project}-{ticket}", {"ticket": "384"}
        )
        self.assertEqual(url, "https://jira.com/browse/{project}-384")

    def test_placeholder_with_label(self):
        url = resolve_url_template(
            "https://jira.com/browse/PAC-{ticket:Ticket number}", {"ticket": "384"}
        )
        self.assertEqual(url, "https://jira.com/browse/PAC-384")

    def test_no_placeholders(self):
        url = resolve_url_template("https://example.com/page", {})
        self.assertEqual(url, "https://example.com/page")


class SmartLinkServiceTestCase(TestCase, BookmarkFactoryMixin):
    def setUp(self):
        self.user = self.get_or_create_test_user()
        self.page = StartPage.objects.create(name="Test", owner=self.user)

    def test_create_smart_link(self):
        link = SmartLink(
            name="Jira PAC",
            url_template="https://jira.com/browse/PAC-{ticket:Ticket number}",
        )
        create_smart_link(link, self.page, self.user)

        self.assertEqual(link.start_page, self.page)
        self.assertEqual(link.owner, self.user)
        self.assertEqual(link.order, 0)

        params = list(link.parameters.all())
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0].name, "ticket")
        self.assertEqual(params[0].label, "Ticket number")

    def test_create_auto_increments_order(self):
        link1 = SmartLink(name="L1", url_template="https://example.com/{a}")
        create_smart_link(link1, self.page, self.user)

        link2 = SmartLink(name="L2", url_template="https://example.com/{b}")
        create_smart_link(link2, self.page, self.user)

        self.assertEqual(link1.order, 0)
        self.assertEqual(link2.order, 1)

    def test_update_smart_link_syncs_parameters(self):
        link = SmartLink(
            name="Test",
            url_template="https://example.com/{a}/{b}",
        )
        create_smart_link(link, self.page, self.user)
        self.assertEqual(link.parameters.count(), 2)

        link.url_template = "https://example.com/{a}/{c:New param}"
        update_smart_link(link)

        params = list(link.parameters.order_by("order"))
        self.assertEqual(len(params), 2)
        self.assertEqual(params[0].name, "a")
        self.assertEqual(params[1].name, "c")
        self.assertEqual(params[1].label, "New param")

    def test_update_preserves_history(self):
        link = SmartLink(
            name="Test",
            url_template="https://example.com/{ticket}",
        )
        create_smart_link(link, self.page, self.user)

        param = link.parameters.first()
        SmartLinkValue.objects.create(parameter=param, value="123")

        link.url_template = "https://example.com/{ticket:Updated label}"
        update_smart_link(link)

        param.refresh_from_db()
        self.assertEqual(param.label, "Updated label")
        self.assertEqual(param.values.count(), 1)
        self.assertEqual(param.values.first().value, "123")

    def test_delete_smart_link(self):
        link = SmartLink(name="Test", url_template="https://example.com/{a}")
        create_smart_link(link, self.page, self.user)

        delete_smart_link(link)

        self.assertFalse(SmartLink.objects.filter(pk=link.pk).exists())

    def test_move_smart_link(self):
        link1 = SmartLink(name="L1", url_template="https://example.com/{a}")
        create_smart_link(link1, self.page, self.user)
        link2 = SmartLink(name="L2", url_template="https://example.com/{b}")
        create_smart_link(link2, self.page, self.user)
        link3 = SmartLink(name="L3", url_template="https://example.com/{c}")
        create_smart_link(link3, self.page, self.user)

        move_smart_link(link3, 0)

        link1.refresh_from_db()
        link2.refresh_from_db()
        link3.refresh_from_db()
        self.assertEqual(link3.order, 0)
        self.assertEqual(link1.order, 1)
        self.assertEqual(link2.order, 2)

    def test_resolve_and_record(self):
        link = SmartLink(
            name="Test",
            url_template="https://jira.com/browse/PAC-{ticket}",
        )
        create_smart_link(link, self.page, self.user)

        url = resolve_and_record(link, {"ticket": "384"})

        self.assertEqual(url, "https://jira.com/browse/PAC-384")
        param = link.parameters.first()
        self.assertEqual(param.values.count(), 1)
        self.assertEqual(param.values.first().value, "384")

    def test_resolve_and_record_updates_existing(self):
        link = SmartLink(
            name="Test",
            url_template="https://jira.com/browse/PAC-{ticket}",
        )
        create_smart_link(link, self.page, self.user)

        resolve_and_record(link, {"ticket": "384"})
        resolve_and_record(link, {"ticket": "384"})

        param = link.parameters.first()
        self.assertEqual(param.values.count(), 1)

    def test_resolve_and_record_multiple_values(self):
        link = SmartLink(
            name="Test",
            url_template="https://jira.com/browse/PAC-{ticket}",
        )
        create_smart_link(link, self.page, self.user)

        resolve_and_record(link, {"ticket": "384"})
        resolve_and_record(link, {"ticket": "385"})

        param = link.parameters.first()
        values = list(param.values.order_by("-used_at").values_list("value", flat=True))
        self.assertEqual(len(values), 2)
        self.assertIn("384", values)
        self.assertIn("385", values)

    def test_get_smart_link_data(self):
        link = SmartLink(
            name="Jira PAC",
            url_template="https://jira.com/browse/PAC-{ticket:Ticket number}",
        )
        create_smart_link(link, self.page, self.user)
        resolve_and_record(link, {"ticket": "384"})

        data = get_smart_link_data(link)

        self.assertEqual(data["id"], link.id)
        self.assertEqual(data["name"], "Jira PAC")
        self.assertEqual(len(data["parameters"]), 1)
        self.assertEqual(data["parameters"][0]["name"], "ticket")
        self.assertEqual(data["parameters"][0]["label"], "Ticket number")
        self.assertEqual(data["parameters"][0]["recent_values"], ["384"])


class SmartLinkViewTestCase(TestCase, BookmarkFactoryMixin):
    def setUp(self):
        self.user = self.get_or_create_test_user()
        self.client.force_login(self.user)
        self.page = StartPage.objects.create(name="Test", owner=self.user)

    def test_new_renders_form(self):
        response = self.client.get(
            reverse("startpage:smart_link.new", args=[self.page.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_new_creates_smart_link(self):
        response = self.client.post(
            reverse("startpage:smart_link.new", args=[self.page.id]),
            {
                "name": "Jira PAC",
                "url_template": "https://jira.com/browse/PAC-{ticket:Ticket number}",
            },
        )
        self.assertEqual(response.status_code, 302)

        link = SmartLink.objects.get(name="Jira PAC")
        self.assertEqual(link.start_page, self.page)
        self.assertEqual(link.owner, self.user)
        self.assertEqual(link.parameters.count(), 1)

    def test_new_validation_error(self):
        response = self.client.post(
            reverse("startpage:smart_link.new", args=[self.page.id]),
            {"name": "", "url_template": ""},
        )
        self.assertEqual(response.status_code, 422)

    def test_edit_renders_form(self):
        link = SmartLink.objects.create(
            start_page=self.page,
            name="Test",
            url_template="https://example.com/{a}",
            owner=self.user,
        )
        response = self.client.get(
            reverse("startpage:smart_link.edit", args=[self.page.id, link.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_edit_updates_smart_link(self):
        link = SmartLink.objects.create(
            start_page=self.page,
            name="Test",
            url_template="https://example.com/{a}",
            owner=self.user,
        )
        response = self.client.post(
            reverse("startpage:smart_link.edit", args=[self.page.id, link.id]),
            {
                "name": "Updated",
                "url_template": "https://example.com/{b:New param}",
            },
        )
        self.assertEqual(response.status_code, 302)
        link.refresh_from_db()
        self.assertEqual(link.name, "Updated")

    def test_action_remove(self):
        link = SmartLink.objects.create(
            start_page=self.page,
            name="Test",
            url_template="https://example.com/{a}",
            owner=self.user,
        )
        self.client.post(
            reverse("startpage:smart_link.action", args=[self.page.id]),
            {"remove_smart_link": link.id},
        )
        self.assertFalse(SmartLink.objects.filter(pk=link.id).exists())

    def test_open_renders_form(self):
        link = SmartLink.objects.create(
            start_page=self.page,
            name="Jira",
            url_template="https://jira.com/browse/PAC-{ticket:Ticket number}",
            owner=self.user,
        )
        SmartLinkParameter.objects.create(
            smart_link=link, name="ticket", label="Ticket number", order=0
        )
        response = self.client.get(
            reverse("startpage:smart_link.open", args=[self.page.id, link.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ticket number")
        self.assertContains(response, "Jira")

    def test_open_resolves_and_redirects(self):
        link = SmartLink.objects.create(
            start_page=self.page,
            name="Jira",
            url_template="https://jira.com/browse/PAC-{ticket}",
            owner=self.user,
        )
        SmartLinkParameter.objects.create(
            smart_link=link, name="ticket", label="Ticket number", order=0
        )
        response = self.client.post(
            reverse("startpage:smart_link.open", args=[self.page.id, link.id]),
            {"param_ticket": "384"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://jira.com/browse/PAC-384")

        # Value should be recorded
        param = link.parameters.first()
        self.assertEqual(param.values.count(), 1)
        self.assertEqual(param.values.first().value, "384")

    def test_open_shows_recent_values(self):
        link = SmartLink.objects.create(
            start_page=self.page,
            name="Jira",
            url_template="https://jira.com/browse/PAC-{ticket}",
            owner=self.user,
        )
        param = SmartLinkParameter.objects.create(
            smart_link=link, name="ticket", label="Ticket number", order=0
        )
        SmartLinkValue.objects.create(parameter=param, value="384")

        response = self.client.get(
            reverse("startpage:smart_link.open", args=[self.page.id, link.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "384")

    def test_404_on_other_users_page(self):
        other_user = self.setup_user()
        other_page = StartPage.objects.create(name="Other", owner=other_user)

        response = self.client.get(
            reverse("startpage:smart_link.new", args=[other_page.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_detail_view_shows_smart_links(self):
        link = SmartLink.objects.create(
            start_page=self.page,
            name="Jira PAC",
            url_template="https://jira.com/browse/PAC-{ticket}",
            owner=self.user,
        )
        SmartLinkParameter.objects.create(
            smart_link=link, name="ticket", label="Ticket number", order=0
        )

        response = self.client.get(
            reverse("startpage:detail", args=[self.page.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jira PAC")
        self.assertContains(response, "Smart links")


class SmartLinkModelTestCase(TestCase, BookmarkFactoryMixin):
    def setUp(self):
        self.user = self.get_or_create_test_user()
        self.page = StartPage.objects.create(name="Test", owner=self.user)

    def test_cascade_delete_page(self):
        link = SmartLink.objects.create(
            start_page=self.page,
            name="Test",
            url_template="https://example.com/{a}",
            owner=self.user,
        )
        SmartLinkParameter.objects.create(smart_link=link, name="a", order=0)

        self.page.delete()

        self.assertEqual(SmartLink.objects.count(), 0)
        self.assertEqual(SmartLinkParameter.objects.count(), 0)

    def test_cascade_delete_link(self):
        link = SmartLink.objects.create(
            start_page=self.page,
            name="Test",
            url_template="https://example.com/{a}",
            owner=self.user,
        )
        param = SmartLinkParameter.objects.create(
            smart_link=link, name="a", order=0
        )
        SmartLinkValue.objects.create(parameter=param, value="test")

        link.delete()

        self.assertEqual(SmartLinkParameter.objects.count(), 0)
        self.assertEqual(SmartLinkValue.objects.count(), 0)

    def test_ordering(self):
        link1 = SmartLink.objects.create(
            start_page=self.page,
            name="L1",
            url_template="https://example.com/{a}",
            owner=self.user,
            order=1,
        )
        link2 = SmartLink.objects.create(
            start_page=self.page,
            name="L2",
            url_template="https://example.com/{b}",
            owner=self.user,
            order=0,
        )
        links = list(SmartLink.objects.filter(start_page=self.page))
        self.assertEqual(links[0], link2)
        self.assertEqual(links[1], link1)
