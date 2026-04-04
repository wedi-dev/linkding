from django.contrib.auth.models import User
from django.db.models import Max

from startpage.models import StartPage, StartPageWidget


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
