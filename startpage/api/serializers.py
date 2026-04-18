from rest_framework import serializers

from startpage import services
from startpage.models import (
    SmartLink,
    StartPage,
    StartPageWidget,
    parse_url_template,
)


class StartPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = StartPage
        fields = ["id", "name", "domain_grouping", "order"]
        read_only_fields = ["id", "order"]

    def create(self, validated_data):
        page = StartPage(**validated_data)
        return services.create_start_page(page, self.context["user"])


class StartPageWidgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = StartPageWidget
        fields = [
            "id",
            "start_page",
            "name",
            "widget_type",
            "bundle",
            "tag_name",
            "filter_query",
            "filter_unread",
            "filter_shared",
            "sort",
            "max_items",
            "order",
        ]
        read_only_fields = ["id", "order"]

    def validate_start_page(self, value: StartPage):
        user = self.context["user"]
        if value.owner_id != user.id:
            raise serializers.ValidationError("Start page does not exist.")
        return value

    def validate_bundle(self, value):
        if value is None:
            return value
        user = self.context["user"]
        if value.owner_id != user.id:
            raise serializers.ValidationError("Bundle does not exist.")
        return value

    def validate(self, attrs):
        widget_type = attrs.get("widget_type") or (
            self.instance.widget_type if self.instance else None
        )
        if widget_type == StartPageWidget.WIDGET_TYPE_BUNDLE:
            bundle = attrs.get("bundle") or (
                self.instance.bundle if self.instance else None
            )
            if bundle is None:
                raise serializers.ValidationError(
                    {"bundle": "Required when widget_type is 'bundle'."}
                )
        elif widget_type == StartPageWidget.WIDGET_TYPE_TAG:
            tag_name = attrs.get("tag_name") or (
                self.instance.tag_name if self.instance else ""
            )
            if not tag_name:
                raise serializers.ValidationError(
                    {"tag_name": "Required when widget_type is 'tag'."}
                )
        return attrs

    def create(self, validated_data):
        start_page = validated_data.pop("start_page")
        widget = StartPageWidget(**validated_data)
        return services.create_widget(widget, start_page)

    def update(self, instance, validated_data):
        # Disallow moving a widget to a different start page via PATCH
        validated_data.pop("start_page", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance


class SmartLinkParameterSerializer(serializers.Serializer):
    name = serializers.CharField()
    label = serializers.CharField(allow_blank=True)


class SmartLinkSerializer(serializers.ModelSerializer):
    parameters = serializers.SerializerMethodField()

    class Meta:
        model = SmartLink
        fields = ["id", "start_page", "name", "url_template", "order", "parameters"]
        read_only_fields = ["id", "order", "parameters"]

    def validate_start_page(self, value: StartPage):
        user = self.context["user"]
        if value.owner_id != user.id:
            raise serializers.ValidationError("Start page does not exist.")
        return value

    def get_parameters(self, obj: SmartLink):
        # Derive from the template so response always reflects current state.
        return parse_url_template(obj.url_template)

    def create(self, validated_data):
        start_page = validated_data.pop("start_page")
        smart_link = SmartLink(**validated_data)
        return services.create_smart_link(smart_link, start_page, self.context["user"])

    def update(self, instance, validated_data):
        validated_data.pop("start_page", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        return services.update_smart_link(instance)


# Preview (read-only) serializers


class PreviewBookmarkSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    url = serializers.CharField()
    title = serializers.SerializerMethodField()
    tag_names = serializers.SerializerMethodField()

    def get_title(self, obj):
        return obj.resolved_title

    def get_tag_names(self, obj):
        return [t.name for t in obj.tags.all()]


class PreviewDomainGroupSerializer(serializers.Serializer):
    domain = serializers.CharField()
    domain_url = serializers.CharField()
    count = serializers.IntegerField()
    bookmarks = PreviewBookmarkSerializer(many=True)


class PreviewWidgetSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    widget_type = serializers.CharField()
    bookmarks = PreviewBookmarkSerializer(many=True, required=False)
    domain_groups = PreviewDomainGroupSerializer(many=True, required=False)


class PreviewSmartLinkSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    url_template = serializers.CharField()
    parameters = serializers.ListField(child=serializers.DictField())


class PreviewPageSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    domain_grouping = serializers.CharField()
    widgets = PreviewWidgetSerializer(many=True)
    smart_links = PreviewSmartLinkSerializer(many=True)
