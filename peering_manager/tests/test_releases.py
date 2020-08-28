import requests

from cacheops import CacheMiss, RedisCache
from django.conf import settings
from django.test import SimpleTestCase, override_settings
from io import BytesIO
from logging import ERROR
from packaging.version import Version
from requests import Response
from unittest.mock import Mock, patch

from peering_manager.releases import get_releases


def successful_github_response(url, *_args, **_kwargs):
    r = Response()
    r.url = url
    r.status_code = 200
    r.reason = "OK"
    r.headers = {"Content-Type": "application/json; charset=utf-8"}
    r.raw = BytesIO(
        b'[{"html_url": "https://github.com/peering-manager/peering-manager/releases/tag/v1.1.0","tag_name": "v1.1.0","prerelease": false},{"html_url": "https://github.com/peering-manager/peering-manager/releases/tag/v1.1-beta1","tag_name": "v1.1-beta1","prerelease": true},{"html_url": "https://github.com/peering-manager/peering-manager/releases/tag/v1.0.0","tag_name": "v1.0.0","prerelease": false}]'
    )
    return r


def unsuccessful_github_response(url, *_args, **_kwargs):
    r = Response()
    r.url = url
    r.status_code = 404
    r.reason = "Not Found"
    r.headers = {"Content-Type": "application/json; charset=utf-8"}
    r.raw = BytesIO(
        b'{"message": "Not Found","documentation_url": "https://developer.github.com/v3/repos/releases/#list-releases-for-a-repository"}'
    )
    return r


@override_settings(
    RELEASE_CHECK_URL="https://localhost/unittest/releases",
    RELEASE_CHECK_TIMEOUT=160876,
)
class GetReleasesTestCase(SimpleTestCase):
    @patch.object(requests, "get")
    @patch.object(RedisCache, "set")
    @patch.object(RedisCache, "get")
    def test_pre_releases(self, mocked_cache_get, mocked_cache_set, mocked_request_get):
        mocked_cache_get.side_effect = CacheMiss()
        mocked_request_get.side_effect = successful_github_response

        releases = get_releases(pre_releases=True)
        self.assertListEqual(
            releases,
            [
                (
                    Version("1.1.0"),
                    "https://github.com/peering-manager/peering-manager/releases/tag/v1.1.0",
                ),
                (
                    Version("1.1b1"),
                    "https://github.com/peering-manager/peering-manager/releases/tag/v1.1-beta1",
                ),
                (
                    Version("1.0.0"),
                    "https://github.com/peering-manager/peering-manager/releases/tag/v1.0.0",
                ),
            ],
        )
        mocked_request_get.assert_called_once_with(
            "https://localhost/unittest/releases",
            headers={"Accept": "application/vnd.github.v3+json"},
        )
        mocked_cache_set.assert_called_once_with(
            "latest_release", max(releases), 160876
        )

    @patch.object(requests, "get")
    @patch.object(RedisCache, "set")
    @patch.object(RedisCache, "get")
    def test_no_pre_releases(
        self, mocked_cache_get, mocked_cache_set, mocked_request_get
    ):
        mocked_cache_get.side_effect = CacheMiss()
        mocked_request_get.side_effect = successful_github_response

        releases = get_releases(pre_releases=False)
        self.assertListEqual(
            releases,
            [
                (
                    Version("1.1.0"),
                    "https://github.com/peering-manager/peering-manager/releases/tag/v1.1.0",
                ),
                (
                    Version("1.0.0"),
                    "https://github.com/peering-manager/peering-manager/releases/tag/v1.0.0",
                ),
            ],
        )
        mocked_request_get.assert_called_once_with(
            "https://localhost/unittest/releases",
            headers={"Accept": "application/vnd.github.v3+json"},
        )
        mocked_cache_set.assert_called_once_with(
            "latest_release", max(releases), 160876
        )
