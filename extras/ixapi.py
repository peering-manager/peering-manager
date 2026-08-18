from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pyixapi
import requests
from django.conf import settings

if TYPE_CHECKING:
    from pyixapi.core.api import API

__all__ = ("TimeoutSession", "build_api")


class TimeoutSession(requests.Session):
    """
    Session applying a timeout to every request.

    `pyixapi` does not expose a timeout, so an unresponsive IX-API would block the
    caller until the operating system gives up on the socket.
    """

    def __init__(self, timeout: int) -> None:
        super().__init__()
        self.timeout = timeout

    def request(self, *args: Any, **kwargs: Any) -> requests.Response:
        kwargs.setdefault("timeout", self.timeout)
        return super().request(*args, **kwargs)


def build_api(
    url: str,
    key: str,
    secret: str,
    access_token: str = "",
    refresh_token: str = "",
) -> API:
    """
    Returns an IX-API client bound to the project wide HTTP settings.
    """
    api = pyixapi.api(
        url=url,
        key=key,
        secret=secret,
        access_token=access_token or "",
        refresh_token=refresh_token or "",
        user_agent=settings.REQUESTS_USER_AGENT,
        proxies=settings.HTTP_PROXIES,
    )
    api.http_session = TimeoutSession(settings.IXAPI_TIMEOUT)

    return api
