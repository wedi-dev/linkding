from django.contrib.auth.models import User
from django.db import models


class StartPage(models.Model):
    DOMAIN_GROUPING_OFF = "off"
    DOMAIN_GROUPING_DOMAIN = "domain"
    DOMAIN_GROUPING_SUBDOMAIN = "subdomain"
    DOMAIN_GROUPING_CHOICES = [
        (DOMAIN_GROUPING_OFF, "Off"),
        (DOMAIN_GROUPING_DOMAIN, "Domain"),
        (DOMAIN_GROUPING_SUBDOMAIN, "Subdomain"),
    ]

    name = models.CharField(max_length=256)
    domain_grouping = models.CharField(
        max_length=10,
        choices=DOMAIN_GROUPING_CHOICES,
        default=DOMAIN_GROUPING_OFF,
    )
    order = models.IntegerField(default=0)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class StartPageWidget(models.Model):
    WIDGET_TYPE_BUNDLE = "bundle"
    WIDGET_TYPE_TAG = "tag"
    WIDGET_TYPE_FILTER = "filter"
    WIDGET_TYPE_CHOICES = [
        (WIDGET_TYPE_BUNDLE, "Bundle"),
        (WIDGET_TYPE_TAG, "Tag"),
        (WIDGET_TYPE_FILTER, "Custom filter"),
    ]

    SORT_ADDED_DESC = "added_desc"
    SORT_ADDED_ASC = "added_asc"
    SORT_TITLE_ASC = "title_asc"
    SORT_TITLE_DESC = "title_desc"
    SORT_CHOICES = [
        (SORT_ADDED_DESC, "Added (newest)"),
        (SORT_ADDED_ASC, "Added (oldest)"),
        (SORT_TITLE_ASC, "Title (A-Z)"),
        (SORT_TITLE_DESC, "Title (Z-A)"),
    ]

    FILTER_STATE_OFF = "off"
    FILTER_STATE_YES = "yes"
    FILTER_STATE_NO = "no"
    FILTER_UNREAD_CHOICES = [
        (FILTER_STATE_OFF, "All"),
        (FILTER_STATE_YES, "Unread"),
        (FILTER_STATE_NO, "Read"),
    ]
    FILTER_SHARED_CHOICES = [
        (FILTER_STATE_OFF, "All"),
        (FILTER_STATE_YES, "Shared"),
        (FILTER_STATE_NO, "Unshared"),
    ]

    start_page = models.ForeignKey(
        StartPage, on_delete=models.CASCADE, related_name="widgets"
    )
    name = models.CharField(max_length=256)
    widget_type = models.CharField(max_length=10, choices=WIDGET_TYPE_CHOICES)

    # For bundle type — cross-app FK
    bundle = models.ForeignKey(
        "bookmarks.BookmarkBundle",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    # For tag type
    tag_name = models.CharField(max_length=64, blank=True)
    # For filter type
    filter_query = models.CharField(max_length=256, blank=True)
    filter_unread = models.CharField(
        max_length=3,
        choices=FILTER_UNREAD_CHOICES,
        default=FILTER_STATE_OFF,
    )
    filter_shared = models.CharField(
        max_length=3,
        choices=FILTER_SHARED_CHOICES,
        default=FILTER_STATE_OFF,
    )

    sort = models.CharField(
        max_length=10, choices=SORT_CHOICES, default=SORT_ADDED_DESC
    )
    max_items = models.IntegerField(default=20)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name
