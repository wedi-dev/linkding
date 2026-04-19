from django.db.models import prefetch_related_objects
from django.http import HttpResponse
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import mixins, renderers, viewsets
from rest_framework.decorators import action
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter

from startpage import services
from startpage.api import markdown as md_preview
from startpage.api.serializers import (
    PreviewPageSerializer,
    PreviewSmartLinkSerializer,
    PreviewWidgetSerializer,
    SmartLinkSerializer,
    StartPageSerializer,
    StartPageWidgetSerializer,
)
from startpage.models import SmartLink, StartPage, StartPageWidget
from startpage.queries import group_bookmarks_by_domain, query_widget_bookmarks


class MarkdownRenderer(renderers.BaseRenderer):
    media_type = "text/markdown"
    format = "md"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if isinstance(data, str):
            return data
        return str(data)


class _OwnedViewSet(viewsets.GenericViewSet):
    """Base viewset that enforces owner isolation via the serializer context."""

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["user"] = self.request.user
        return ctx


class StartPageViewSet(
    _OwnedViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    serializer_class = StartPageSerializer

    def get_queryset(self):
        return StartPage.objects.filter(owner=self.request.user).order_by("order")

    def perform_destroy(self, instance: StartPage):
        services.delete_start_page(instance)

    @extend_schema(
        description=(
            "Render the current state of a start page. Defaults to JSON; "
            "pass `Accept: text/markdown` or `?format=md` for a plain-text "
            "markdown snapshot (useful for pasting into LLM contexts)."
        ),
        responses={
            200: OpenApiResponse(
                response=PreviewPageSerializer,
                description="Page preview as JSON or text/markdown depending on Accept.",
            ),
        },
    )
    @action(
        detail=True,
        methods=["get"],
        url_path="preview",
        renderer_classes=[JSONRenderer, MarkdownRenderer],
    )
    def preview(self, request, pk=None):
        page = self.get_object()
        profile = request.user_profile
        widgets_qs = StartPageWidget.objects.filter(start_page=page).order_by("order")
        smart_links_qs = SmartLink.objects.filter(start_page=page).order_by("order")

        widget_payloads = []
        for w in widgets_qs:
            bookmarks = list(
                query_widget_bookmarks(request.user, profile, w)[: w.max_items]
            )
            prefetch_related_objects(bookmarks, "tags")
            payload = {
                "id": w.id,
                "name": w.name,
                "widget_type": w.widget_type,
                "domain_grouping": w.domain_grouping,
            }
            if w.domain_grouping != StartPageWidget.DOMAIN_GROUPING_OFF:
                payload["domain_groups"] = group_bookmarks_by_domain(
                    bookmarks, w.domain_grouping
                )
            else:
                payload["bookmarks"] = bookmarks
            widget_payloads.append(payload)

        smart_link_payloads = [
            {
                "id": sl.id,
                "name": sl.name,
                "url_template": sl.url_template,
                "parameters": [
                    {"name": p.name, "label": p.label}
                    for p in sl.parameters.all().order_by("order")
                ],
            }
            for sl in smart_links_qs
        ]

        requested_format = request.GET.get("format")
        accepts_md = requested_format == "md" or "text/markdown" in request.META.get(
            "HTTP_ACCEPT", ""
        )
        if accepts_md:
            body = md_preview.render_page_markdown(
                page, widget_payloads, smart_link_payloads
            )
            return HttpResponse(body, content_type="text/markdown; charset=utf-8")

        data = {
            "id": page.id,
            "name": page.name,
            "widgets": [PreviewWidgetSerializer(w).data for w in widget_payloads],
            "smart_links": [
                PreviewSmartLinkSerializer(sl).data for sl in smart_link_payloads
            ],
        }
        return Response(data)


class StartPageWidgetViewSet(
    _OwnedViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    serializer_class = StartPageWidgetSerializer

    def get_queryset(self):
        qs = StartPageWidget.objects.filter(
            start_page__owner=self.request.user
        ).order_by("order")
        start_page = self.request.GET.get("start_page")
        if start_page:
            qs = qs.filter(start_page_id=start_page)
        return qs

    def perform_destroy(self, instance: StartPageWidget):
        services.delete_widget(instance)


class SmartLinkViewSet(
    _OwnedViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    serializer_class = SmartLinkSerializer

    def get_queryset(self):
        qs = SmartLink.objects.filter(owner=self.request.user).order_by("order")
        start_page = self.request.GET.get("start_page")
        if start_page:
            qs = qs.filter(start_page_id=start_page)
        return qs

    def perform_destroy(self, instance: SmartLink):
        services.delete_smart_link(instance)


router = DefaultRouter()
router.register("pages", StartPageViewSet, basename="pages")
router.register("widgets", StartPageWidgetViewSet, basename="widgets")
router.register("smart-links", SmartLinkViewSet, basename="smart-links")
