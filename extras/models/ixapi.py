import logging

import pyixapi
from django.apps import apps
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.timezone import make_aware

from peering_manager.models import ChangeLoggedModel

logger = logging.getLogger("peering.manager.extras.ixapi")

__all__ = ("IXAPI",)


class IXAPI(ChangeLoggedModel):
    """
    An Endpoint holds the details to reach an IX-API given its URL, API key and
    secret.
    """

    name = models.CharField(max_length=100)
    url = models.CharField(max_length=2000, verbose_name="URL")
    api_key = models.CharField(max_length=2000, verbose_name="API key")
    api_secret = models.CharField(max_length=2000, verbose_name="API secret")
    identity = models.CharField(
        max_length=256, help_text="Identity used to interact with the IX-API"
    )
    access_token = models.TextField(blank=True, null=True)
    access_token_expiration = models.DateTimeField(blank=True, null=True)
    refresh_token = models.TextField(blank=True, null=True)
    refresh_token_expiration = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "IX-API"
        ordering = ["name", "url", "-created"]
        constraints = [
            models.UniqueConstraint(
                fields=["url", "api_key"], name="unique_ixapi_url_key"
            )
        ]

    @property
    def version(self):
        """
        Returns the API version based on the URL.
        """
        if not hasattr(self, "_version"):
            logger.debug("ix-api version not cached, querying...")
            # Cache version to avoid re-querying the API
            api = self.dial()
            self._version = api.version
        return self._version

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("extras:ixapi_view", args=[self.pk])

    def dial(self):
        """
        Returns a API client to use for queries.
        """
        api = pyixapi.api(
            self.url,
            self.api_key,
            self.api_secret,
            access_token=self.access_token,
            refresh_token=self.refresh_token,
            user_agent=settings.REQUESTS_USER_AGENT,
        )

        # Perform an authentication
        auth = api.authenticate()
        if auth:
            # Save tokens if they've changed
            self.access_token = api.access_token.encoded
            self.access_token_expiration = make_aware(api.access_token.expires_at)
            self.refresh_token = api.refresh_token.encoded
            self.refresh_token_expiration = make_aware(api.refresh_token.expires_at)
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
        elif health["status"] == "warn":
            return "degraded"
        else:
            return "unhealthy"

    def get_accounts(self, id=""):
        """
        Returns accounts that we are entitled to use.

        In theory the primary account is us, that said we may be a reseller (thus
        having sub-accounts), but we do not need to track this, at least not yet.
        """
        accounts = self.dial().customers
        if id:
            return accounts.filter(id=id)
        else:
            return accounts.all()

    def get_identity(self):
        """
        Returns our own account instance.
        """
        if not self.identity:
            return None
        else:
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
        Fetches all IX-API useful data and cache them in memory, to improve lookup
        speed.
        """
        if hasattr(self, "_cached_data"):
            logger.debug("ix-api data already cached")
            return

        logger.debug("ix-api data not cached, fetching and caching")
        api = self.dial()
        self._cached_data = {
            "network_service_configs": list(api.network_service_configs.all()),
            "network_services": list(api.network_services.all()),
            "network_features": list(api.network_features.all()),
            "products": list(api.products.all()),
            "macs": list(api.macs.all()),
            "ips": list(api.ips.all()),
        }

    def get_cached_data(self, endpoint):
        """
        Retrieves a cached value for an IX-API endpoint.
        """
        if not hasattr(self, "_cached_data"):
            return []
        return self._cached_data.get(endpoint, [])

    def get_network_service_configs(
        self, network_service=None, states=("production", "testing")
    ):
        """
        Returns configs for IXP services specific to us.

        TODO: retrieve RS configurations with network feature configs
        """
        self.cache_ixapi_data()

        c = []
        network_service_configs = self.get_cached_data("network_service_configs")

        if not network_service_configs:
            # Data must be cached to use this function
            return []

        for nsc in network_service_configs:
            if (states and nsc.state not in states) or (
                network_service and nsc.network_service != network_service.id
            ):
                continue

            # Resolve IP addresses
            ips = []
            for ip in nsc.ips:
                i = self.search_in_list(self.get_cached_data("ips"), ip)
                if i:
                    ips.append(i.cidr)
            setattr(nsc, "ips", ips)
            for ip in nsc.ips:
                setattr(nsc, f"ipv{ip.version}_address", ip)

            # Resolve MAC addresses
            macs = []
            for mac in nsc.macs:
                m = self.search_in_list(self.get_cached_data("macs"), mac)
                if m:
                    macs.append(m.address.lower())
            setattr(nsc, "macs", macs)

            # Check if it matches a known connection
            Connection = apps.get_model("net", "Connection")
            qs_filter = Q()
            if hasattr(nsc, "ipv6_address"):
                qs_filter |= Q(ipv4_address=nsc.ipv6_address)
            if hasattr(nsc, "ipv4_address"):
                qs_filter |= Q(ipv4_address=nsc.ipv4_address)
            if qs_filter:
                try:
                    setattr(nsc, "connection", Connection.objects.get(qs_filter))
                except (Connection.DoesNotExist, Connection.MultipleObjectsReturned):
                    return setattr(nsc, "connection", None)

            c.append(nsc)

        return c

    def get_network_services(self):
        """
        Returns all known network services assigned to us.
        """
        self.cache_ixapi_data()

        network_services = self.get_cached_data("network_services")
        for ns in network_services:
            if hasattr(ns, "product"):
                setattr(
                    ns,
                    "product",
                    self.search_in_list(self.get_cached_data("products"), ns.product),
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
                setattr(ns, "network_features", features)
            if not hasattr(ns, "network_service_configs"):
                setattr(
                    ns, "network_service_configs", self.get_network_service_configs(ns)
                )

        return network_services

    def create_mac_address(self, mac_address):
        """
        Create a new MAC address in IX-API.
        """
        # IX-API has MACs in upper case strings
        mac_address = str(mac_address).upper()

        # Fetch MACs and only get the actual addresses
        self.cache_ixapi_data()
        macs = [i["address"] for i in self.get_cached_data("macs")]
        if mac_address in macs:
            print(f"{mac_address} already exists")
        else:
            print(f"create mac address {mac_address}")
            # self.dial().macs.create(address=mac_address)
