from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pyixapi
from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.db.models import Q
from django.urls import reverse

from core.constants import CENSORSHIP_STRING, CENSORSHIP_STRING_CHANGED
from peering_manager.models import ChangeLoggedModel

if TYPE_CHECKING:
    from core.models import ObjectChange

logger = logging.getLogger("peering.manager.extras.ixapi")

__all__ = ("IXAPI",)


class IXAPI(ChangeLoggedModel):
    """
    This model holds the details to reach an IX-API given its URL, API key and secret.
    """

    name = models.CharField(max_length=100)
    api_url = models.CharField(max_length=2000, verbose_name="URL")
    api_key = models.CharField(max_length=2000, verbose_name="API key")
    api_secret = models.CharField(max_length=2000, verbose_name="API secret")
    identity = models.CharField(
        max_length=256, help_text="Identity used to interact with the IX-API"
    )
    access_token = models.TextField(blank=True, null=True)
    access_token_expiration = models.DateTimeField(blank=True, null=True)
    refresh_token = models.TextField(blank=True, null=True)
    refresh_token_expiration = models.DateTimeField(blank=True, null=True)
    changelog_excluded_fields = [
        "access_token",
        "access_token_expiration",
        "refresh_token",
        "refresh_token_expiration",
    ]

    class Meta:
        verbose_name = "IX-API"
        ordering = ["name", "api_url", "-created"]
        constraints = [
            models.UniqueConstraint(
                fields=["api_url", "api_key"], name="unique_ixapi_url_key"
            )
        ]

    @property
    def _cache_key(self) -> str:
        return f"ixapi_data__{self.pk}"

    @property
    def version(self) -> int:
        """
        Returns the API version based on the URL.
        """
        key = f"ixapi_version__{self.pk}"
        value = cache.get(key)

        if not value:
            logger.debug("ix-api version not cached, querying...")
            # Cache version to avoid re-querying the API
            api = self.dial()
            value = api.version
            cache.set(key, value)

        return value

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("extras:ixapi", args=[self.pk])

    def to_objectchange(self, action) -> ObjectChange:
        object_change = super().to_objectchange(action)

        prechange_data = {}
        postchange_data = {}

        if object_change.prechange_data:
            prechange_data = object_change.prechange_data or {}
        if object_change.postchange_data:
            postchange_data = object_change.postchange_data or {}

        for param in ["api_key", "api_secret"]:
            if param in postchange_data:
                if postchange_data.get(param) != prechange_data.get(param):
                    postchange_data[param] = CENSORSHIP_STRING_CHANGED
                else:
                    postchange_data[param] = CENSORSHIP_STRING
            if param in prechange_data:
                prechange_data[param] = CENSORSHIP_STRING

        return object_change

    @staticmethod
    def test_connectivity(api_url, api_key, api_secret):
        """
        Performs a authentication and see if it succeeds.
        """
        api = pyixapi.api(
            url=api_url,
            key=api_key,
            secret=api_secret,
            user_agent=settings.REQUESTS_USER_AGENT,
            proxies=settings.HTTP_PROXIES,
        )

        # Perform an authentication
        return api.authenticate() is not None

    def get_account_dict(self):
        """
        Returns a key/value mapping for account fields to set in IX-API requests.

        If the API version is 1, it'll use the `_customer` suffix. It'll use
        `_account` for all other versions.
        """
        suffix = "_customer" if self.version == 1 else "_account"
        return {
            f"managing_{suffix}": self.identity,
            f"consuming_{suffix}": self.identity,
        }

    def dial(self):
        """
        Returns a API client to use for queries.
        """
        api = pyixapi.api(
            url=self.api_url,
            key=self.api_key,
            secret=self.api_secret,
            access_token=self.access_token,
            refresh_token=self.refresh_token,
            user_agent=settings.REQUESTS_USER_AGENT,
            proxies=settings.HTTP_PROXIES,
        )

        # Perform an authentication
        auth = api.authenticate()
        if auth:
            self.snapshot()
            # Save tokens if they've changed
            self.access_token = api.access_token.encoded
            self.access_token_expiration = api.access_token.expires_at
            self.refresh_token = api.refresh_token.encoded
            self.refresh_token_expiration = api.refresh_token.expires_at
            self.save()

        return api

    def get_health(self):
        """
        Returns the health of the API.

        This is only available for version greater than v1.
        """
        health = self.dial().health()

        if not health:
            return ""

        if health["status"] in ("pass", "ok", "up"):
            return "healthy"
        if health["status"] == "warn":
            return "degraded"
        return "unhealthy"

    def get_accounts(self, id=""):
        """
        Returns accounts that we are entitled to use.

        In theory the primary account is us, that said we may be a reseller (thus
        having sub-accounts), but we do not need to track this, at least not yet.
        """
        accounts = self.dial().accounts
        if id:
            return accounts.filter(id=id)
        return accounts.all()

    def get_identity(self):
        """
        Returns our own account instance.
        """
        if not self.identity:
            return None

        # If we have none or more than one account, we cannot decide which one is
        # the correct one; it should not happen though
        accounts = self.get_accounts(id=self.identity)
        return next(accounts) if len(accounts) == 1 else None

    def search_in_list(self, items, value, key="id"):
        """
        Looks up a value for a specific attribute (default to `id`) in a list of
        items.
        """
        for i in items:
            if hasattr(i, key) and getattr(i, key) == value:
                return i
        return None

    def cache_ixapi_data(self):
        """
        Fetches all IX-API useful data and cache them, to improve lookup speed.
        """
        api = self.dial()
        data = {
            "network_service_configs": list(api.network_service_configs.all()),
            "network_services": list(api.network_services.all()),
            "network_features": list(api.network_features.all()),
            "product_offerings": list(api.product_offerings.all()),
            "macs": list(api.macs.all()),
            "ips": list(api.ips.all()),
        }
        cache.set(self._cache_key, data)

        return data

    def get_cached_data(self, endpoint):
        """
        Retrieves a cached value for an IX-API endpoint. If not cached data are found,
        build the cache and return its value.
        """
        cached_value = cache.get(self._cache_key)
        if not cached_value:
            logger.debug("ix-api data not cached, fetching and caching")
            cached_value = self.cache_ixapi_data()
        return cached_value.get(endpoint, [])

    def get_network_service_configs(
        self,
        network_service=None,
        states=(),
        exclude_states=("archived", "decommissioned"),
    ):
        """
        Returns configs for IXP services specific to us.

        TODO: retrieve RS configurations with network feature configs
        """
        c = []
        network_service_configs = self.get_cached_data("network_service_configs")

        if not network_service_configs:
            # Data must be cached to use this function
            return []

        for nsc in network_service_configs:
            # Ignore depends on state or if network service IDs don't match
            if (
                (states and nsc.state not in states)
                or (exclude_states and nsc.state in exclude_states)
                or (network_service and nsc.network_service != network_service.id)
            ):
                continue

            # Resolve IP addresses
            ips = []
            for ip in nsc.ips:
                i = self.search_in_list(self.get_cached_data("ips"), ip)
                if i:
                    ips.append(i.cidr)
            nsc.ips = ips
            for ip in nsc.ips:
                setattr(nsc, f"ipv{ip.version}_address", ip)

            # Resolve MAC addresses
            macs = []
            for mac in nsc.macs:
                m = self.search_in_list(self.get_cached_data("macs"), mac)
                if m:
                    macs.append(m.address.lower())
            nsc.macs = macs

            # Check if it matches a known connection
            Connection = apps.get_model("net", "Connection")
            qs_filter = Q()
            if hasattr(nsc, "ipv6_address"):
                qs_filter |= Q(ipv4_address=nsc.ipv6_address)
            if hasattr(nsc, "ipv4_address"):
                qs_filter |= Q(ipv4_address=nsc.ipv4_address)
            if qs_filter:
                try:
                    nsc.connection = Connection.objects.get(qs_filter)
                except (Connection.DoesNotExist, Connection.MultipleObjectsReturned):
                    nsc.connectin = None

            c.append(nsc)

        return c

    def get_network_services(self):
        """
        Returns all known network services assigned to us.
        """
        network_services = self.get_cached_data("network_services")
        for ns in network_services:
            # Product IX-APi v1/v2 compatibility
            if hasattr(ns, "product"):
                ns.product = self.search_in_list(
                    self.get_cached_data("product_offerings"), ns.product
                )
            if hasattr(ns, "product_offering"):
                ns.product_offering = self.search_in_list(
                    self.get_cached_data("product_offerings"), ns.product_offering
                )
            if hasattr(ns, "ips"):
                for ip in ns.ips:
                    i = self.search_in_list(self.get_cached_data("ips"), ip)
                    if i:
                        setattr(ns, f"subnet_v{i.network.version}", i.network)
            if hasattr(ns, "network_features"):
                features = []
                for feature in ns.network_features:
                    f = self.search_in_list(
                        self.get_cached_data("network_features"), feature
                    )
                    if f:
                        features.append(f)
                ns.network_features = features
            if not hasattr(ns, "network_service_configs"):
                ns.network_service_configs = self.get_network_service_configs(ns)

        return network_services

    def create_mac_address(self, mac_address):
        """
        Create a new MAC address in IX-API. If the MAC already exists, return it
        without creation.
        """
        # Make sure to have a consistent case
        mac_address = str(mac_address).lower()

        # Return existing object if MAC already exists
        for mac in self.get_cached_data("macs"):
            if mac["address"].lower() == mac_address:
                logger.debug(f"{mac_address} already exists")
                return mac

        logger.debug(f"create mac address {mac_address}")
        return self.dial().macs.create(address=mac_address, **self.get_account_dict())
