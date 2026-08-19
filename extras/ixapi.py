from __future__ import annotations

import logging
from ipaddress import IPv4Interface, IPv4Network, IPv6Interface, IPv6Network, ip_interface
from typing import TYPE_CHECKING, Any

import pyixapi
import requests
from django.conf import settings

if TYPE_CHECKING:
    from pyixapi.core.api import API

__all__ = (
    "IP",
    "MAC",
    "CachedRecord",
    "NetworkService",
    "NetworkServiceConfig",
    "TimeoutSession",
    "build_api",
    "index_by_id",
)

logger = logging.getLogger("peering.manager.extras.ixapi")


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


def build_api(url: str, key: str, secret: str, access_token: str = "", refresh_token: str = "") -> API:
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


class CachedRecord:
    """
    Read only view over one IX-API object stored as a plain dictionary.

    Only the values that IX-API returns are cached. The API client, and the key and secret it holds, never reach the
    cache. A field that IX-API did not return raises `AttributeError`, which Django templates render as an empty value.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @property
    def id(self) -> str:
        return self._data.get("id", "")

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(name) from None

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, CachedRecord):
            return self._data == other._data
        return NotImplemented

    def __hash__(self) -> int:
        return hash((type(self).__name__, self.id))

    def __str__(self) -> str:
        return self.id

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.id}>"


class IP(CachedRecord):
    """
    An IP address with its prefix length, as IX-API returns it.
    """

    @property
    def cidr(self) -> IPv4Interface | IPv6Interface | None:
        address = self._data.get("address")
        prefix_length = self._data.get("prefix_length")
        if not address or prefix_length is None:
            return None
        try:
            return ip_interface(f"{address}/{prefix_length}")
        except ValueError:
            logger.debug("ignoring invalid ix-api ip %s/%s", address, prefix_length)
            return None

    @property
    def network(self) -> IPv4Network | IPv6Network | None:
        cidr = self.cidr
        return cidr.network if cidr else None

    def __str__(self) -> str:
        return str(self.cidr or self.id)


class MAC(CachedRecord):
    """
    A MAC address, always in lower case to allow comparisons.
    """

    @property
    def address(self) -> str:
        return str(self._data.get("address", "")).lower()

    def __str__(self) -> str:
        return self.address


class NetworkServiceConfig:
    """
    A network service config with its IP and MAC references resolved.
    """

    def __init__(
        self,
        record: CachedRecord,
        *,
        ips: list[IPv4Interface | IPv6Interface] | None = None,
        macs: list[str] | None = None,
        connection: Any = None,
    ) -> None:
        self.record = record
        self.ips = ips or []
        self.macs = macs or []
        self.connection = connection

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        return getattr(self.record, name)

    @property
    def ipv4_address(self) -> IPv4Interface | None:
        return next((i for i in self.ips if i.version == 4), None)

    @property
    def ipv6_address(self) -> IPv6Interface | None:
        return next((i for i in self.ips if i.version == 6), None)

    def __str__(self) -> str:
        return str(self.record)

    def __repr__(self) -> str:
        return f"<NetworkServiceConfig {self.record.id}>"


class NetworkService:
    """
    A network service with its product, features, subnets and configs resolved.
    """

    def __init__(
        self,
        record: CachedRecord,
        *,
        product_offering: CachedRecord | None = None,
        network_features: list[CachedRecord] | None = None,
        network_service_configs: list[NetworkServiceConfig] | None = None,
        subnet_v4: IPv4Network | None = None,
        subnet_v6: IPv6Network | None = None,
    ) -> None:
        self.record = record
        self.product_offering = product_offering
        self.network_features = network_features or []
        self.network_service_configs = network_service_configs or []
        self.subnet_v4 = subnet_v4
        self.subnet_v6 = subnet_v6

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        return getattr(self.record, name)

    def __str__(self) -> str:
        return str(self.record)

    def __repr__(self) -> str:
        return f"<NetworkService {self.record.id}>"


def index_by_id(rows: list[dict[str, Any]], record_class: type[CachedRecord] = CachedRecord) -> dict[str, CachedRecord]:
    """
    Returns cached rows as records, keyed by their IX-API identifier.
    """
    return {row["id"]: record_class(row) for row in rows if row.get("id")}
