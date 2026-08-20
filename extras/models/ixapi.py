from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.db.models import Q
from django.urls import reverse

from peering_manager.models import ChangeLoggedModel

from ..ixapi import IP, MAC, CachedRecord, NetworkService, NetworkServiceConfig, build_api, index_by_id

if TYPE_CHECKING:
    from ipaddress import IPv4Interface, IPv6Interface

    from pyixapi.core.api import API

logger = logging.getLogger("peering.manager.extras.ixapi")

__all__ = ("IXAPI",)

CACHED_ENDPOINTS = (
    "network_service_configs",
    "network_services",
    "network_features",
    "product_offerings",
    "macs",
    "ips",
)
TOKEN_FIELDS = ("access_token", "access_token_expiration", "refresh_token", "refresh_token_expiration")
DEFAULT_EXCLUDED_STATES = ("archived", "decommissioned")


class IXAPI(ChangeLoggedModel):
    """
    This model holds the details to reach an IX-API given its URL, API key and secret.
    """

    name = models.CharField(max_length=100)
    api_url = models.CharField(max_length=2000, verbose_name="URL")
    api_key = models.CharField(max_length=2000, verbose_name="API key")
    api_secret = models.CharField(max_length=2000, verbose_name="API secret")
    identity = models.CharField(max_length=256, help_text="Identity used to interact with the IX-API")
    access_token = models.TextField(blank=True, null=True)
    access_token_expiration = models.DateTimeField(blank=True, null=True)
    refresh_token = models.TextField(blank=True, null=True)
    refresh_token_expiration = models.DateTimeField(blank=True, null=True)
    changelog_excluded_fields = list(TOKEN_FIELDS)
    changelog_censored_fields = ["api_key", "api_secret"]

    class Meta:
        verbose_name = "IX-API"
        ordering = ["name", "api_url", "-created"]
        constraints = [models.UniqueConstraint(fields=["api_url", "api_key"], name="unique_ixapi_url_key")]

    @property
    def _cache_key(self) -> str:
        return f"ixapi_data__{self.pk}"

    @property
    def _version_cache_key(self) -> str:
        return f"ixapi_version__{self.pk}"

    @property
    def version(self) -> int:
        """
        Returns the API version based on the URL.
        """
        value = cache.get(self._version_cache_key)

        if not value:
            logger.debug("ix-api version not cached, querying...")
            value = self.dial().version
            cache.set(self._version_cache_key, value, timeout=settings.CACHE_IXAPI_TIMEOUT)

        return value

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("extras:ixapi", args=[self.pk])

    def invalidate_cache(self) -> None:
        """
        Drops the cached IX-API data and version for this endpoint.
        """
        if self.pk:
            cache.delete_many([self._cache_key, self._version_cache_key])

    def save(self, *args: Any, **kwargs: Any) -> None:
        super().save(*args, **kwargs)
        self.invalidate_cache()

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        self.invalidate_cache()
        return super().delete(*args, **kwargs)

    @staticmethod
    def test_connectivity(api_url: str, api_key: str, api_secret: str) -> bool:
        """
        Performs a authentication and see if it succeeds.
        """
        return build_api(api_url, api_key, api_secret).authenticate() is not None

    def get_account_dict(self) -> dict[str, str]:
        """
        Returns a key/value mapping for account fields to set in IX-API requests.

        If the API version is 1, it'll use the `customer` suffix. It'll use `account` for all other
        versions.
        """
        suffix = "customer" if self.version == 1 else "account"
        return {f"managing_{suffix}": self.identity, f"consuming_{suffix}": self.identity}

    def dial(self) -> API:
        """
        Returns a API client to use for queries.
        """
        api = build_api(
            self.api_url,
            self.api_key,
            self.api_secret,
            access_token=self.access_token or "",
            refresh_token=self.refresh_token or "",
        )

        if api.authenticate():
            self.access_token = api.access_token.encoded
            self.access_token_expiration = api.access_token.expires_at
            self.refresh_token = api.refresh_token.encoded
            self.refresh_token_expiration = api.refresh_token.expires_at
            if self.pk:
                # A token renewal is not a user change: no cache drop, no webhook, no clobbered edit
                IXAPI.objects.filter(pk=self.pk).update(**{f: getattr(self, f) for f in TOKEN_FIELDS})

        return api

    def get_health(self) -> str:
        """
        Returns the health of the API.

        This is only available for version greater than v1.
        """
        health = self.dial().health()

        if not health or "status" not in health:
            return ""

        if health["status"] in ("pass", "ok", "up"):
            return "healthy"
        if health["status"] == "warn":
            return "degraded"
        return "unhealthy"

    def get_accounts(self, account_id: str = ""):
        """
        Returns accounts that we are entitled to use.

        In theory the primary account is us, that said we may be a reseller (thus
        having sub-accounts), but we do not need to track this, at least not yet.
        """
        accounts = self.dial().accounts
        if account_id:
            return accounts.filter(id=account_id)
        return accounts.all()

    def get_identity(self):
        """
        Returns our own account instance.
        """
        if not self.identity:
            return None

        # With none or several accounts we cannot tell which one is ours; it should not happen
        accounts = self.get_accounts(account_id=self.identity)
        return next(accounts) if len(accounts) == 1 else None

    def cache_ixapi_data(self) -> dict[str, list[dict[str, Any]]]:
        """
        Fetches all IX-API useful data and cache them, to improve lookup speed.

        Records are stored as plain dictionaries. A `pyixapi` record keeps a reference
        to the API client, which holds the key, the secret and the tokens, so caching
        records as they are would copy the credentials to the cache.
        """
        api = self.dial()
        data = {endpoint: [dict(r) for r in getattr(api, endpoint).all()] for endpoint in CACHED_ENDPOINTS}
        cache.set(self._cache_key, data, timeout=settings.CACHE_IXAPI_TIMEOUT)

        return data

    def get_cached_data(self, endpoint: str = "") -> Any:
        """
        Retrieves cached values for IX-API endpoints. If no cached data are found,
        build the cache and return its value.

        Without an endpoint name, all endpoints are returned at once. A caller that
        resolves references between endpoints must use that form: each call to this
        function reads and decodes the complete cache entry.
        """
        cached_value = cache.get(self._cache_key)
        if cached_value is None:
            logger.debug("ix-api data not cached, fetching and caching")
            cached_value = self.cache_ixapi_data()

        if endpoint:
            return cached_value.get(endpoint, [])
        return cached_value

    def get_network_service_configs(
        self,
        network_service: NetworkService | None = None,
        states: tuple[str, ...] = (),
        exclude_states: tuple[str, ...] = DEFAULT_EXCLUDED_STATES,
    ) -> list[NetworkServiceConfig]:
        """
        Returns configs for IXP services specific to us.

        TODO: retrieve RS configurations with network feature configs
        """
        return self._build_network_service_configs(self.get_cached_data(), network_service, states, exclude_states)

    def _build_network_service_configs(
        self,
        data: dict[str, list[dict[str, Any]]],
        network_service: NetworkService | None,
        states: tuple[str, ...],
        exclude_states: tuple[str, ...],
    ) -> list[NetworkServiceConfig]:
        ips = index_by_id(data.get("ips", []), IP)
        macs = index_by_id(data.get("macs", []), MAC)

        configs = []
        for row in data.get("network_service_configs", []):
            state = row.get("state")
            if (
                (states and state not in states)
                or (exclude_states and state in exclude_states)
                or (network_service and row.get("network_service") != network_service.id)
            ):
                continue

            configs.append(
                NetworkServiceConfig(
                    record=CachedRecord(row),
                    ips=[c for i in row.get("ips") or [] if (c := self._resolve_ip(ips, i))],
                    macs=[m.address for i in row.get("macs") or [] if (m := macs.get(i))],
                )
            )

        self._link_connections(configs)

        return configs

    @staticmethod
    def _resolve_ip(ips: dict[str, CachedRecord], key: str) -> IPv4Interface | IPv6Interface | None:
        ip = ips.get(key)
        return ip.cidr if ip else None

    @staticmethod
    def _link_connections(configs: list[NetworkServiceConfig]) -> None:
        """
        Attaches the local connection matching each config, if there is one.

        All configs are resolved with a single query. Addresses are compared as hosts
        because IX-API and Peering Manager can record different prefix lengths for the
        same address.
        """
        hosts = {str(ip.ip) for config in configs for ip in config.ips}
        if not hosts:
            return

        qs_filter = Q()
        for host in hosts:
            qs_filter |= Q(ipv6_address__host=host) | Q(ipv4_address__host=host)

        connection_model = apps.get_model("net", "Connection")
        by_host: dict[str, Any] = {}
        ambiguous: set[str] = set()
        for connection in connection_model.objects.filter(qs_filter):
            for address in (connection.ipv6_address, connection.ipv4_address):
                if address is None:
                    continue
                host = str(getattr(address, "ip", address))
                if host in by_host and by_host[host] != connection:
                    ambiguous.add(host)
                by_host[host] = connection

        for config in configs:
            for ip in config.ips:
                host = str(ip.ip)
                if host in ambiguous:
                    logger.debug(f"several connections use {host}, cannot link ix-api config {config.id}")
                    continue
                if host in by_host:
                    config.connection = by_host[host]
                    break

    def get_network_services(self) -> list[NetworkService]:
        """
        Returns all known network services assigned to us.
        """
        data = self.get_cached_data()
        ips = index_by_id(data.get("ips", []), IP)
        features = index_by_id(data.get("network_features", []))
        offerings = index_by_id(data.get("product_offerings", []))

        configs_by_service: dict[str, list[NetworkServiceConfig]] = {}
        for config in self._build_network_service_configs(data, None, (), DEFAULT_EXCLUDED_STATES):
            configs_by_service.setdefault(config.record.get("network_service", ""), []).append(config)

        services = []
        for row in data.get("network_services", []):
            # A product is named product offering in IX-API v2 and later
            service = NetworkService(
                record=CachedRecord(row),
                product_offering=offerings.get(row.get("product_offering") or row.get("product") or ""),
                network_features=[f for i in row.get("network_features") or [] if (f := features.get(i))],
                network_service_configs=configs_by_service.get(row.get("id", ""), []),
            )
            for key in row.get("ips") or []:
                ip = ips.get(key)
                if ip and (network := ip.network):
                    setattr(service, f"subnet_v{network.version}", network)

            services.append(service)

        return services

    def create_mac_address(self, mac_address: str) -> MAC:
        """
        Create a new MAC address in IX-API. If the MAC already exists, return it
        without creation.
        """
        mac_address = str(mac_address).lower()

        for row in self.get_cached_data("macs"):
            mac = MAC(row)
            if mac.address == mac_address:
                logger.debug(f"{mac_address} already exists")
                return mac

        logger.debug(f"create mac address {mac_address}")
        created = MAC(dict(self.dial().macs.create(address=mac_address, **self.get_account_dict())))
        # A new MAC must be visible to the next lookup
        self.invalidate_cache()

        return created

    def set_network_service_config_macs(self, network_service_config_id: str, mac_ids: list[str]) -> bool:
        """
        Replaces the MAC addresses of a network service config.

        The config is fetched again instead of being taken from the cache: a cached
        record holds the token that was valid when it was cached, and `pyixapi` sends
        the difference between the record and its state at load time.
        """
        network_service_config = self.dial().network_service_configs.get(network_service_config_id)
        if network_service_config is None:
            logger.debug(f"ix-api network service config {network_service_config_id} not found")
            return False

        network_service_config.macs = list(mac_ids)
        if not network_service_config.updates():
            logger.debug(f"ix-api network service config {network_service_config_id} already uses these mac addresses")
            return True

        if network_service_config.save():
            self.invalidate_cache()
            return True

        return False
