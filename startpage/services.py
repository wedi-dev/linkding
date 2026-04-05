from django.contrib.auth.models import User
from django.db.models import Max
from django.utils import timezone

from startpage.models import (
    SmartLink,
    SmartLinkParameter,
    SmartLinkValue,
    StartPage,
    StartPageWidget,
    parse_url_template,
    resolve_url_template,
)


def create_start_page(page: StartPage, user: User):
    page.owner = user
    max_order = StartPage.objects.filter(owner=user).aggregate(Max("order", default=-1))
    page.order = max_order["order__max"] + 1
    page.save()
    return page


def delete_start_page(page: StartPage):
    owner = page.owner
    page.delete()
    _reorder_pages(owner)


def delete_start_pages(page_ids: list, user: User):
    StartPage.objects.filter(owner=user, pk__in=page_ids).delete()
    _reorder_pages(user)


def move_start_page(page: StartPage, new_order: int):
    pages = list(StartPage.objects.filter(owner=page.owner).order_by("order"))
    if new_order != pages.index(page):
        pages.remove(page)
        pages.insert(new_order, page)
        for i, p in enumerate(pages):
            p.order = i
        StartPage.objects.bulk_update(pages, ["order"])


def _reorder_pages(owner: User):
    pages = StartPage.objects.filter(owner=owner).order_by("order")
    for i, page in enumerate(pages):
        page.order = i
    StartPage.objects.bulk_update(pages, ["order"])


def create_widget(widget: StartPageWidget, start_page: StartPage):
    widget.start_page = start_page
    max_order = StartPageWidget.objects.filter(start_page=start_page).aggregate(
        Max("order", default=-1)
    )
    widget.order = max_order["order__max"] + 1
    widget.save()
    return widget


def delete_widget(widget: StartPageWidget):
    start_page = widget.start_page
    widget.delete()
    _reorder_widgets(start_page)


def delete_widgets(widget_ids: list, start_page: StartPage):
    StartPageWidget.objects.filter(start_page=start_page, pk__in=widget_ids).delete()
    _reorder_widgets(start_page)


def move_widget(widget: StartPageWidget, new_order: int):
    widgets = list(
        StartPageWidget.objects.filter(start_page=widget.start_page).order_by("order")
    )
    if new_order != widgets.index(widget):
        widgets.remove(widget)
        widgets.insert(new_order, widget)
        for i, w in enumerate(widgets):
            w.order = i
        StartPageWidget.objects.bulk_update(widgets, ["order"])


def _reorder_widgets(start_page: StartPage):
    widgets = StartPageWidget.objects.filter(start_page=start_page).order_by("order")
    for i, widget in enumerate(widgets):
        widget.order = i
    StartPageWidget.objects.bulk_update(widgets, ["order"])


# Smart link services


def create_smart_link(smart_link: SmartLink, start_page: StartPage, user: User):
    smart_link.start_page = start_page
    smart_link.owner = user
    max_order = SmartLink.objects.filter(start_page=start_page).aggregate(
        Max("order", default=-1)
    )
    smart_link.order = max_order["order__max"] + 1
    smart_link.save()
    _sync_smart_link_parameters(smart_link)
    return smart_link


def update_smart_link(smart_link: SmartLink):
    smart_link.save()
    _sync_smart_link_parameters(smart_link)
    return smart_link


def delete_smart_link(smart_link: SmartLink):
    start_page = smart_link.start_page
    smart_link.delete()
    _reorder_smart_links(start_page)


def move_smart_link(smart_link: SmartLink, new_order: int):
    links = list(
        SmartLink.objects.filter(start_page=smart_link.start_page).order_by("order")
    )
    if new_order != links.index(smart_link):
        links.remove(smart_link)
        links.insert(new_order, smart_link)
        for i, link in enumerate(links):
            link.order = i
        SmartLink.objects.bulk_update(links, ["order"])


def resolve_and_record(smart_link: SmartLink, values: dict) -> str:
    """Resolve URL template with values and record them in history."""
    url = resolve_url_template(smart_link.url_template, values)

    cutoff = timezone.now() - timezone.timedelta(days=30)
    for param in smart_link.parameters.all():
        value = values.get(param.name)
        if not value:
            continue
        existing = SmartLinkValue.objects.filter(parameter=param, value=value).first()
        if existing:
            existing.used_at = timezone.now()
            existing.save(update_fields=["used_at"])
        else:
            SmartLinkValue.objects.create(parameter=param, value=value)
        # Clean up old values
        param.values.filter(used_at__lt=cutoff).delete()

    return url


def get_smart_link_data(smart_link: SmartLink) -> dict:
    """Return parameters with their recent value history (for detail page context)."""
    params = []
    for param in smart_link.parameters.all():
        recent = list(
            param.values.order_by("-used_at").values_list("value", flat=True)[:5]
        )
        params.append(
            {
                "name": param.name,
                "label": param.label or param.name,
                "recent_values": recent,
            }
        )
    return {
        "id": smart_link.id,
        "name": smart_link.name,
        "url_template": smart_link.url_template,
        "parameters": params,
    }


def get_smart_link_params(smart_link: SmartLink) -> list[dict]:
    """Return parameters with history for the open page template."""
    params = []
    for param in smart_link.parameters.all():
        recent = list(
            param.values.order_by("-used_at").values_list("value", flat=True)[:5]
        )
        params.append(
            {
                "name": param.name,
                "label": param.label or param.name,
                "last_value": recent[0] if recent else "",
                "recent_values": recent,
            }
        )
    return params


def _sync_smart_link_parameters(smart_link: SmartLink):
    """Sync parameters from url_template. Preserves history for unchanged params."""
    parsed = parse_url_template(smart_link.url_template)
    parsed_names = {p["name"] for p in parsed}
    existing = {p.name: p for p in smart_link.parameters.all()}

    # Remove params no longer in template
    for name in set(existing) - parsed_names:
        existing[name].delete()

    # Create or update params
    for p in parsed:
        if p["name"] in existing:
            param = existing[p["name"]]
            param.label = p["label"]
            param.order = p["order"]
            param.save(update_fields=["label", "order"])
        else:
            SmartLinkParameter.objects.create(
                smart_link=smart_link,
                name=p["name"],
                label=p["label"],
                order=p["order"],
            )


def _reorder_smart_links(start_page: StartPage):
    links = SmartLink.objects.filter(start_page=start_page).order_by("order")
    for i, link in enumerate(links):
        link.order = i
    SmartLink.objects.bulk_update(links, ["order"])
