from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from startpage import services
from startpage.contexts import (
    DomainDetailContext,
    StartPageDetailContext,
    StartPageHubContext,
)
from startpage.forms import SmartLinkForm, StartPageForm, StartPageWidgetForm
from startpage.models import SmartLink, StartPage, StartPageWidget


def _get_page(request, page_id):
    try:
        return StartPage.objects.get(pk=page_id, owner=request.user)
    except StartPage.DoesNotExist:
        raise Http404("Start page does not exist") from None


def _get_widget(request, page_id, widget_id):
    page = _get_page(request, page_id)
    try:
        return page, StartPageWidget.objects.get(pk=widget_id, start_page=page)
    except StartPageWidget.DoesNotExist:
        raise Http404("Widget does not exist") from None


def _get_smart_link(request, page_id, smart_link_id):
    page = _get_page(request, page_id)
    try:
        return page, SmartLink.objects.get(pk=smart_link_id, start_page=page)
    except SmartLink.DoesNotExist:
        raise Http404("Smart link does not exist") from None


@login_required
def hub(request: HttpRequest):
    context = StartPageHubContext(request)
    return render(request, "startpage/hub.html", {"hub": context})


@login_required
def detail(request: HttpRequest, page_id: int):
    page = _get_page(request, page_id)
    context = StartPageDetailContext(request, page)
    return render(
        request, "startpage/detail.html", {"page": context, "start_page": page}
    )


@login_required
def domain_detail(request: HttpRequest, page_id: int, domain_key: str):
    page = _get_page(request, page_id)
    context = DomainDetailContext(request, page, domain_key)
    return render(
        request,
        "startpage/domain_detail.html",
        {"domain": context, "start_page": page},
    )


@login_required
def page_new(request: HttpRequest):
    return _handle_page_edit(request, "startpage/page_new.html")


@login_required
def page_edit(request: HttpRequest, page_id: int):
    page = _get_page(request, page_id)
    return _handle_page_edit(request, "startpage/page_edit.html", page)


def _handle_page_edit(request: HttpRequest, template: str, page=None):
    form_data = request.POST if request.method == "POST" else None
    form = StartPageForm(form_data, instance=page)

    if request.method == "POST" and form.is_valid():
        instance = form.save(commit=False)
        if page is None:
            services.create_start_page(instance, request.user)
        else:
            instance.save()
        messages.success(request, "Start page saved successfully.")
        return HttpResponseRedirect(reverse("startpage:hub"))

    status = 422 if request.method == "POST" and not form.is_valid() else 200
    return render(request, template, {"form": form, "start_page": page}, status=status)


@login_required
def page_action(request: HttpRequest):
    if "remove_page" in request.POST:
        page_id = request.POST.get("remove_page")
        page = _get_page(request, page_id)
        page_name = page.name
        services.delete_start_page(page)
        messages.success(request, f"Start page '{page_name}' removed successfully.")

    elif "move_page" in request.POST:
        page_id = request.POST.get("move_page")
        page = _get_page(request, page_id)
        new_order = int(request.POST.get("move_position"))
        services.move_start_page(page, new_order)

    return HttpResponseRedirect(reverse("startpage:hub"))


@login_required
def widget_new(request: HttpRequest, page_id: int):
    page = _get_page(request, page_id)
    return _handle_widget_edit(request, "startpage/widget_new.html", page)


@login_required
def widget_edit(request: HttpRequest, page_id: int, widget_id: int):
    page, widget = _get_widget(request, page_id, widget_id)
    return _handle_widget_edit(request, "startpage/widget_edit.html", page, widget)


def _handle_widget_edit(request: HttpRequest, template: str, page, widget=None):
    form_data = request.POST if request.method == "POST" else None
    form = StartPageWidgetForm(request.user, form_data, instance=widget)

    if request.method == "POST" and form.is_valid():
        instance = form.save(commit=False)
        if widget is None:
            services.create_widget(instance, page)
        else:
            instance.save()
        messages.success(request, "Widget saved successfully.")
        return HttpResponseRedirect(reverse("startpage:detail", args=[page.id]))

    status = 422 if request.method == "POST" and not form.is_valid() else 200
    return render(
        request,
        template,
        {"form": form, "start_page": page, "widget": widget},
        status=status,
    )


@login_required
def widget_action(request: HttpRequest, page_id: int):
    page = _get_page(request, page_id)

    if "remove_widget" in request.POST:
        widget_id = request.POST.get("remove_widget")
        _, widget = _get_widget(request, page_id, widget_id)
        widget_name = widget.name
        services.delete_widget(widget)
        messages.success(request, f"Widget '{widget_name}' removed successfully.")

    elif "move_widget" in request.POST:
        widget_id = request.POST.get("move_widget")
        _, widget = _get_widget(request, page_id, widget_id)
        new_order = int(request.POST.get("move_position"))
        services.move_widget(widget, new_order)

    return HttpResponseRedirect(reverse("startpage:detail", args=[page.id]))


# Smart link views


@login_required
def smart_link_new(request: HttpRequest, page_id: int):
    page = _get_page(request, page_id)
    return _handle_smart_link_edit(request, "startpage/smart_link_new.html", page)


@login_required
def smart_link_edit(request: HttpRequest, page_id: int, smart_link_id: int):
    page, smart_link = _get_smart_link(request, page_id, smart_link_id)
    return _handle_smart_link_edit(
        request, "startpage/smart_link_edit.html", page, smart_link
    )


def _handle_smart_link_edit(request: HttpRequest, template: str, page, smart_link=None):
    form_data = request.POST if request.method == "POST" else None
    form = SmartLinkForm(form_data, instance=smart_link)

    if request.method == "POST" and form.is_valid():
        instance = form.save(commit=False)
        if smart_link is None:
            services.create_smart_link(instance, page, request.user)
        else:
            services.update_smart_link(instance)
        messages.success(request, "Smart link saved successfully.")
        return HttpResponseRedirect(reverse("startpage:detail", args=[page.id]))

    status = 422 if request.method == "POST" and not form.is_valid() else 200
    return render(
        request,
        template,
        {"form": form, "start_page": page, "smart_link": smart_link},
        status=status,
    )


@login_required
def smart_link_action(request: HttpRequest, page_id: int):
    page = _get_page(request, page_id)

    if "remove_smart_link" in request.POST:
        smart_link_id = request.POST.get("remove_smart_link")
        _, smart_link = _get_smart_link(request, page_id, smart_link_id)
        link_name = smart_link.name
        services.delete_smart_link(smart_link)
        messages.success(request, f"Smart link '{link_name}' removed successfully.")

    elif "move_smart_link" in request.POST:
        smart_link_id = request.POST.get("move_smart_link")
        _, smart_link = _get_smart_link(request, page_id, smart_link_id)
        new_order = int(request.POST.get("move_position"))
        services.move_smart_link(smart_link, new_order)

    return HttpResponseRedirect(reverse("startpage:detail", args=[page.id]))


@login_required
def smart_link_open(request: HttpRequest, page_id: int, smart_link_id: int):
    """GET shows parameter form, POST resolves URL and redirects."""
    page, smart_link = _get_smart_link(request, page_id, smart_link_id)

    if request.method == "POST":
        values = {}
        for param in smart_link.parameters.all():
            values[param.name] = request.POST.get(f"param_{param.name}", "")
        url = services.resolve_and_record(smart_link, values)
        return HttpResponseRedirect(url)

    parameters = services.get_smart_link_params(smart_link)
    return render(
        request,
        "startpage/smart_link_open.html",
        {"start_page": page, "smart_link": smart_link, "parameters": parameters},
    )
