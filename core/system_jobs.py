from __future__ import annotations

from datetime import timedelta
from importlib import import_module

import requests
from django.conf import settings
from django.core.cache import cache
from django.db import DEFAULT_DB_ALIAS
from django.utils import timezone
from packaging import version

from peering_manager.jobs import JobRunner, system_job

from .enums import JobInterval
from .models import Job, ObjectChange


@system_job(
    interval=JobInterval.DAILY,
    key="housekeeping",
    label="Housekeeping",
    min_interval=JobInterval.HOURLY,
)
class HousekeepingJob(JobRunner):
    """
    Periodic housekeeping: clear expired auth sessions, prune expired changelog
    + Job records, and refresh the cached "latest release" entry. Mirrors the
    behaviour of the `housekeeping` management command.
    """

    class Meta:
        name = "Housekeeping"

    def run(self, *args, **kwargs) -> None:
        self._clear_expired_sessions()
        self._prune_changelog()
        self._delete_expired_jobs()
        self._check_for_new_releases()

    def _clear_expired_sessions(self) -> None:
        self.logger.info("Clearing expired authentication sessions")
        engine = import_module(settings.SESSION_ENGINE)
        try:
            engine.SessionStore.clear_expired()
        except NotImplementedError:
            self.logger.info(
                "Session engine %s does not support clearing sessions; skipping",
                settings.SESSION_ENGINE,
            )

    def _prune_changelog(self) -> None:
        if not settings.CHANGELOG_RETENTION:
            self.logger.info("CHANGELOG_RETENTION is 0; skipping changelog pruning")
            return

        cutoff = timezone.now() - timedelta(days=settings.CHANGELOG_RETENTION)
        expired = ObjectChange.objects.filter(time__lt=cutoff)
        count = expired.count()
        if count:
            self.logger.info("Deleting %d expired changelog records", count)
            expired._raw_delete(using=DEFAULT_DB_ALIAS)
        else:
            self.logger.info("No expired changelog records to delete")

    def _delete_expired_jobs(self) -> None:
        if not settings.JOB_RETENTION:
            self.logger.info("JOB_RETENTION is 0; skipping job pruning")
            return

        cutoff = timezone.now() - timedelta(days=settings.JOB_RETENTION)
        expired = Job.objects.filter(created__lt=cutoff)
        count = expired.count()
        if count:
            self.logger.info("Deleting %d expired job records", count)
            expired._raw_delete(using=DEFAULT_DB_ALIAS)
        else:
            self.logger.info("No expired job records to delete")

    def _check_for_new_releases(self) -> None:
        if not settings.RELEASE_CHECK_URL:
            self.logger.info("RELEASE_CHECK_URL not set; skipping release check")
            return

        try:
            response = requests.get(
                url=settings.RELEASE_CHECK_URL,
                headers={"Accept": "application/vnd.github.v3+json"},
                proxies=settings.HTTP_PROXIES,
                timeout=15,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.logger.error("Release check failed: %s", e)
            return

        releases = []
        for release in response.json():
            if "tag_name" not in release or release.get("devrelease") or release.get("prerelease"):
                continue
            releases.append((version.parse(release["tag_name"]), release.get("html_url")))

        if not releases:
            self.logger.info("No usable releases found")
            return

        latest_release = max(releases)
        self.logger.info("Latest release: %s", latest_release[0])
        cache.set("latest_release", latest_release, None)
