from datetime import timedelta
from importlib import import_module

import requests
from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import DEFAULT_DB_ALIAS
from django.template.defaultfilters import pluralize
from django.utils import timezone
from packaging import version

from core.models import Job, ObjectChange


class Command(BaseCommand):
    help = "Perform housekeeping tasks. (This command can be run at any time.)"

    def handle(self, *args, **options):
        # Clear expired authentication sessions (replicate `clearsessions` command)
        if options["verbosity"]:
            self.stdout.write("[*] Clearing expired authentication sessions")
            if options["verbosity"] >= 2:
                self.stdout.write(
                    f"    Configured session engine: {settings.SESSION_ENGINE}"
                )
        engine = import_module(settings.SESSION_ENGINE)
        try:
            engine.SessionStore.clear_expired()
            if options["verbosity"]:
                self.stdout.write("    Sessions cleared.", self.style.SUCCESS)
        except NotImplementedError:
            if options["verbosity"]:
                self.stdout.write(
                    f"    The configured session engine ({settings.SESSION_ENGINE}) does not support clearing sessions; skipping."
                )

        # Delete expired ObjectChanges
        if options["verbosity"]:
            self.stdout.write("[*] Checking for expired changelog records")
        if settings.CHANGELOG_RETENTION:
            cutoff = timezone.now() - timedelta(days=settings.CHANGELOG_RETENTION)
            if options["verbosity"] >= 2:
                self.stdout.write(
                    f"    Retention period: {settings.CHANGELOG_RETENTION} day{pluralize(settings.CHANGELOG_RETENTION)}"
                )
                self.stdout.write(f"    Cut-off time: {cutoff}")
            expired_records = ObjectChange.objects.filter(time__lt=cutoff).count()
            if expired_records:
                if options["verbosity"]:
                    self.stdout.write(
                        f"    Deleting {expired_records} expired records... ",
                        self.style.WARNING,
                        ending="",
                    )
                    self.stdout.flush()
                ObjectChange.objects.filter(time__lt=cutoff)._raw_delete(
                    using=DEFAULT_DB_ALIAS
                )
                if options["verbosity"]:
                    self.stdout.write("Done.", self.style.SUCCESS)
            elif options["verbosity"]:
                self.stdout.write("    No expired records found.", self.style.SUCCESS)
        elif options["verbosity"]:
            self.stdout.write(
                f"    Skipping: No retention period specified (CHANGELOG_RETENTION = {settings.CHANGELOG_RETENTION})"
            )

        # Delete expired jobs
        if options["verbosity"]:
            self.stdout.write("[*] Checking for expired jobs records")
        if settings.JOB_RETENTION:
            cutoff = timezone.now() - timedelta(days=settings.JOB_RETENTION)
            if options["verbosity"] >= 2:
                self.stdout.write(
                    f"    Retention period: {settings.JOB_RETENTION} day{pluralize(settings.JOB_RETENTION)}"
                )
                self.stdout.write(f"    Cut-off time: {cutoff}")
            expired_records = Job.objects.filter(created__lt=cutoff).count()
            if expired_records:
                if options["verbosity"]:
                    self.stdout.write(
                        f"    Deleting {expired_records} expired records... ",
                        self.style.WARNING,
                        ending="",
                    )
                    self.stdout.flush()
                Job.objects.filter(created__lt=cutoff)._raw_delete(
                    using=DEFAULT_DB_ALIAS
                )
                if options["verbosity"]:
                    self.stdout.write("Done.", self.style.SUCCESS)
            elif options["verbosity"]:
                self.stdout.write("    No expired records found.", self.style.SUCCESS)
        elif options["verbosity"]:
            self.stdout.write(
                f"    Skipping: No retention period specified (JOB_RETENTION = {settings.JOB_RETENTION})"
            )

        # Check for new releases (if enabled)
        if options["verbosity"]:
            self.stdout.write("[*] Checking for latest release")
        if settings.RELEASE_CHECK_URL:
            headers = {"Accept": "application/vnd.github.v3+json"}
            try:
                if options["verbosity"] >= 2:
                    self.stdout.write(f"    Fetching {settings.RELEASE_CHECK_URL}")
                response = requests.get(
                    url=settings.RELEASE_CHECK_URL,
                    headers=headers,
                    proxies=settings.HTTP_PROXIES,
                )
                response.raise_for_status()

                releases = []
                for release in response.json():
                    if (
                        "tag_name" not in release
                        or release.get("devrelease")
                        or release.get("prerelease")
                    ):
                        continue
                    releases.append(
                        (version.parse(release["tag_name"]), release.get("html_url"))
                    )
                latest_release = max(releases)
                if options["verbosity"] >= 2:
                    self.stdout.write(
                        f"    Found {len(response.json())} releases; {len(releases)} usable"
                    )
                if options["verbosity"]:
                    self.stdout.write(
                        f"    Latest release: {latest_release[0]}", self.style.SUCCESS
                    )

                # Cache the most recent release
                cache.set("latest_release", latest_release, None)
            except requests.exceptions.RequestException as e:
                self.stdout.write(f"    Request error: {e}", self.style.ERROR)
        elif options["verbosity"]:
            self.stdout.write("    Skipping: RELEASE_CHECK_URL not set")

        if options["verbosity"]:
            self.stdout.write("Finished.", self.style.SUCCESS)
