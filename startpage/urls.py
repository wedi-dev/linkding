from django.urls import path

from startpage import views

app_name = "startpage"

urlpatterns = [
    path("", views.hub, name="hub"),
    path("new", views.page_new, name="page.new"),
    path("action", views.page_action, name="page.action"),
    path("<int:page_id>/", views.detail, name="detail"),
    path("<int:page_id>/edit", views.page_edit, name="page.edit"),
    path(
        "<int:page_id>/domain/<path:domain_key>/",
        views.domain_detail,
        name="domain.detail",
    ),
    path(
        "<int:page_id>/widgets/new",
        views.widget_new,
        name="widget.new",
    ),
    path(
        "<int:page_id>/widgets/<int:widget_id>/edit",
        views.widget_edit,
        name="widget.edit",
    ),
    path(
        "<int:page_id>/widgets/action",
        views.widget_action,
        name="widget.action",
    ),
    # Smart links
    path(
        "<int:page_id>/smart-links/new",
        views.smart_link_new,
        name="smart_link.new",
    ),
    path(
        "<int:page_id>/smart-links/<int:smart_link_id>/edit",
        views.smart_link_edit,
        name="smart_link.edit",
    ),
    path(
        "<int:page_id>/smart-links/action",
        views.smart_link_action,
        name="smart_link.action",
    ),
    path(
        "<int:page_id>/smart-links/<int:smart_link_id>/open",
        views.smart_link_open,
        name="smart_link.open",
    ),
]
