from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from startpage import views
from startpage.api import markdown as md_views
from startpage.api.routes import router as api_router

app_name = "startpage"

urlpatterns = [
    # API
    path("api/", include(api_router.urls)),
    # API docs
    path("api-docs/", md_views.api_docs_index, name="api_docs.index"),
    path(
        "api-docs/schema.yaml",
        SpectacularAPIView.as_view(),
        name="api_docs.schema",
    ),
    path(
        "api-docs/swagger/",
        SpectacularSwaggerView.as_view(url_name="startpage:api_docs.schema"),
        name="api_docs.swagger",
    ),
    path(
        "api-docs/redoc/",
        SpectacularRedocView.as_view(url_name="startpage:api_docs.schema"),
        name="api_docs.redoc",
    ),
    path("api-docs/guide.md", md_views.serve_guide, name="api_docs.guide"),
    # UI
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
