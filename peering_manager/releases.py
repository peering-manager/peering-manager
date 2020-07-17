import logging
import requests

from cacheops import cache, CacheMiss
from django.conf import settings
from django_rq import get_queue, job
from packaging import version


logger = logging.getLogger("peering.manager.releases")


@job("check_releases")
def get_releases(pre_releases=False):
    url = settings.RELEASE_CHECK_URL
    releases = []

    try:
        logger.debug(f"fetching new releases from {url}")
        response = requests.get(
            url, headers={"Accept": "application/vnd.github.v3+json"}
        )
        response.raise_for_status()
        total_releases = len(response.json())

        for release in response.json():
            if "tag_name" not in release:
                continue
            if not pre_releases and (
                release.get("devrelease") or release.get("prerelease")
            ):
                continue
            releases.append(
                (version.parse(release["tag_name"]), release.get("html_url"))
            )
        logger.debug(f"found {total_releases} releases; {len(releases)} usable")
    except requests.exceptions.RequestException:
        logger.exception(f"error while fetching {url}")
        return []

    # Cache the most recent release
    cache.set("latest_release", max(releases), settings.RELEASE_CHECK_TIMEOUT)

    return releases


def get_latest_release(pre_releases=False):
    if settings.RELEASE_CHECK_URL:
        logger.debug("checking for most recent release")
        try:
            latest_release = cache.get("latest_release")
            if latest_release:
                logger.debug(f"found cached release: {latest_release}")
                return latest_release
        except CacheMiss:
            queue = get_queue("check_releases")
            if queue.jobs:
                logger.warning("job to check for new releases already queued")
            else:
                logger.info(
                    "starting background task to retrieve updated releases list"
                )
                get_releases.delay(pre_releases=pre_releases)
    else:
        logger.debug("skipping release check; RELEASE_CHECK_URL not defined")

    return "unknown", None
