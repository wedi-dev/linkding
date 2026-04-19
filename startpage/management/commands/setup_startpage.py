from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count

from bookmarks.models import BookmarkBundle, Tag
from startpage import services
from startpage.models import StartPage, StartPageWidget


class Command(BaseCommand):
    help = "Create a default start page with widgets for a user"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user",
            type=str,
            help="Username to create start page for. If omitted, creates for all users.",
        )
        parser.add_argument(
            "--name",
            type=str,
            default="My Start Page",
            help="Name for the start page (default: 'My Start Page')",
        )

    def handle(self, *args, **options):
        username = options.get("user")
        page_name = options["name"]

        if username:
            try:
                users = [User.objects.get(username=username)]
            except User.DoesNotExist:
                raise CommandError(f"User '{username}' does not exist") from None
        else:
            users = User.objects.all()

        for user in users:
            if StartPage.objects.filter(owner=user).exists():
                self.stdout.write(
                    f"User '{user.username}' already has start pages, skipping."
                )
                continue

            page = StartPage(name=page_name)
            services.create_start_page(page, user)
            widget_count = 0

            # Create widgets from existing bundles
            bundles = BookmarkBundle.objects.filter(owner=user).order_by("order")
            for bundle in bundles:
                widget = StartPageWidget(
                    name=bundle.name,
                    widget_type=StartPageWidget.WIDGET_TYPE_BUNDLE,
                    bundle=bundle,
                    domain_grouping=StartPageWidget.DOMAIN_GROUPING_DOMAIN,
                )
                services.create_widget(widget, page)
                widget_count += 1

            # If no bundles, create widgets from popular tags
            if widget_count == 0:
                popular_tags = (
                    Tag.objects.filter(owner=user)
                    .annotate(bookmark_count=Count("bookmark"))
                    .order_by("-bookmark_count")[:5]
                )
                for tag in popular_tags:
                    widget = StartPageWidget(
                        name=tag.name,
                        widget_type=StartPageWidget.WIDGET_TYPE_TAG,
                        tag_name=tag.name,
                        domain_grouping=StartPageWidget.DOMAIN_GROUPING_DOMAIN,
                    )
                    services.create_widget(widget, page)
                    widget_count += 1

            # Fallback: create a generic "All bookmarks" widget
            if widget_count == 0:
                widget = StartPageWidget(
                    name="All bookmarks",
                    widget_type=StartPageWidget.WIDGET_TYPE_FILTER,
                    filter_query="",
                    domain_grouping=StartPageWidget.DOMAIN_GROUPING_DOMAIN,
                )
                services.create_widget(widget, page)
                widget_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Created start page '{page_name}' with {widget_count} "
                    f"widget(s) for user '{user.username}'."
                )
            )
