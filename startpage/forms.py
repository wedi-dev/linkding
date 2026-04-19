from django import forms

from bookmarks.models import BookmarkBundle
from bookmarks.widgets import (
    FormErrorList,
    FormInput,
    FormNumberInput,
    FormSelect,
    TagAutocomplete,
)
from startpage.models import SmartLink, StartPage, StartPageWidget


class StartPageForm(forms.ModelForm):
    name = forms.CharField(max_length=256, widget=FormInput)

    class Meta:
        model = StartPage
        fields = ["name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, error_class=FormErrorList)


class StartPageWidgetForm(forms.ModelForm):
    name = forms.CharField(max_length=256, widget=FormInput)
    widget_type = forms.ChoiceField(
        choices=StartPageWidget.WIDGET_TYPE_CHOICES,
        widget=FormSelect,
    )
    bundle = forms.ModelChoiceField(
        queryset=BookmarkBundle.objects.none(),
        required=False,
        widget=FormSelect,
    )
    tag_name = forms.CharField(max_length=64, required=False, widget=TagAutocomplete)
    filter_query = forms.CharField(max_length=256, required=False, widget=FormInput)
    filter_unread = forms.ChoiceField(
        choices=StartPageWidget.FILTER_UNREAD_CHOICES,
        required=False,
        widget=FormSelect,
    )
    filter_shared = forms.ChoiceField(
        choices=StartPageWidget.FILTER_SHARED_CHOICES,
        required=False,
        widget=FormSelect,
    )
    sort = forms.ChoiceField(
        choices=StartPageWidget.SORT_CHOICES,
        widget=FormSelect,
    )
    max_items = forms.IntegerField(widget=FormNumberInput)
    domain_grouping = forms.ChoiceField(
        choices=StartPageWidget.DOMAIN_GROUPING_CHOICES,
        widget=FormSelect,
    )

    class Meta:
        model = StartPageWidget
        fields = [
            "name",
            "widget_type",
            "bundle",
            "tag_name",
            "filter_query",
            "filter_unread",
            "filter_shared",
            "sort",
            "max_items",
            "domain_grouping",
        ]

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs, error_class=FormErrorList)
        self.fields["bundle"].queryset = BookmarkBundle.objects.filter(owner=user)


class SmartLinkForm(forms.ModelForm):
    name = forms.CharField(max_length=256, widget=FormInput)
    url_template = forms.CharField(
        max_length=2048,
        widget=FormInput(
            attrs={"placeholder": "https://jira.com/browse/PAC-{ticket:Ticket number}"}
        ),
    )

    class Meta:
        model = SmartLink
        fields = ["name", "url_template"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, error_class=FormErrorList)
