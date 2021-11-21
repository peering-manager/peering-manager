import ipaddress
import json
import logging
from datetime import datetime

import requests
from cacheops import cached_as
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse

from net.models import Connection
from utils.models import ChangeLoggedModel

logger = logging.getLogger("peering.manager.extras.ixapi")


def format_url(host, resource):
    """
    Returns a usable URL out of a host and a resource to fetch.
    """
    return host.rstrip("/") + "/" + resource.lstrip("/").rstrip("/")


def unpack_response(response):
    """
    Fetches the JSON body of a response and returns a tuple composed of the
    response itself with the decoded JSON.
    """
    try:
        j = response.json()
    except json.JSONDecodeError:
        j = response.text

    if response.status_code == requests.codes.ok:
        return (response, j)
    else:
        return (response, {})


def parse_datetime(string, format="%Y-%m-%dT%H:%M:%SZ"):
    """
    Parses a string into a datetime instance.

    If `format` is not provided, expect format is `2031-08-28T17:52:27Z`.
    """
    return datetime.strptime(string, format)


class Client(object):
    """
    IX-API client to send requests.
    """

    def __init__(
        self, ixapi_endpoint=None, ixapi_url="", ixapi_key="", ixapi_secret=""
    ):
        self.ixapi_endpoint = ixapi_endpoint
        self.host = ixapi_url or self.ixapi_endpoint.url

        self._ixapi_key = ixapi_key
        self._ixapi_secret = ixapi_secret

        self.access_token = ""
        self.refresh_token = ""

    @property
    def request_headers(self):
        """
        Returns the authentication header to perform a request.
        """
        if not self.access_token:
            return {}
        else:
            return {"Authorization": f"Bearer {self.access_token}"}

    def auth(self):
        """
        Creates a new set of tokens to start interacting with the API.
        """
        _, d = self.post(
            "auth/token",
            payload={
                "api_key": self._ixapi_key or self.ixapi_endpoint.api_key,
                "api_secret": self._ixapi_secret or self.ixapi_endpoint.api_secret,
            },
        )
        logger.debug(f"api at {self.host} responded {d}")

        if "access_token" not in d or "refresh_token" not in d:
            logger.error(f"malformed response from api at {self.host}")
            return

        self.access_token = d["access_token"]
        self.refresh_token = d["refresh_token"]

    def refresh_auth(self):
        """
        Refreshes the current session to continue using the same token.
        """
        _, d = self.post("auth/refresh", payload={"refresh_token": self.refresh_token})
        logger.debug(f"api at {self.host} responded {d}")

        if "access_token" not in d or "refresh_token" not in d:
            logger.error(f"malformed response from api at {self.host}")
            return

        self.access_token = d["access_token"]
        self.refresh_token = d["refresh_token"]

    def get(self, resource, params={}):
        u = format_url(self.host, resource)
        logger.debug(f"sending get to api located at {u}")

        r = requests.get(u, params=params, headers=self.request_headers)
        r.raise_for_status()
        return unpack_response(r)

    def post(self, resource, payload=None):
        u = format_url(self.host, resource)
        logger.debug(f"sending post to api located at {u}")

        r = requests.post(u, json=payload, headers=self.request_headers)
        r.raise_for_status()
        return unpack_response(r)


class RemoteObject(object):
    """
    Object serving as a proxy to IX-API remote data.

    This object essentially tracks raw data from the IX-API and the object used to
    interact with it.

    Properties for each child of this class should be defined with the `@property`
    annotation as it may use some logic to get remote data, i.e. the property is an
    object referred to as an ID.
    """

    def __init__(self, ixapi, data):
        self._ixapi = ixapi
        self._data = data

    def get_property(self, name):
        """
        Looks up a value by a key in the underlying `_data` dict of this object.
        """
        return self._data.get(name)

    @property
    def id(self):
        return self.get_property("id")


class IP(RemoteObject):
    def __init__(self, ixapi, data):
        super().__init__(ixapi, data)

        self._value = ipaddress.ip_interface(
            f"{self.get_property('address')}/{self.get_property('prefix_length')}"
        )

    @property
    def address(self):
        return self._value.ip

    @property
    def network(self):
        return self._value.network

    def __str__(self):
        return str(self._value)


class MAC(RemoteObject):
    @property
    def address(self):
        return self.get_property("address")

    def __str__(self):
        return self.address


class NetworkService(RemoteObject):
    """
    Proxy object for `network-services` endpoint.
    """

    def __init__(self, ixapi, data):
        super().__init__(ixapi, data)

        self._product = None
        self._ips = []
        self._network_features = []
        self._network_service_configs = []

    @property
    def peeringdb_ixid(self):
        return self.get_property("peeringdb_ixid")

    @property
    def name(self):
        return self.get_property("name")

    @property
    def metro_area(self):
        return self.get_property("metro_area")

    @property
    def product(self):
        product_id = self.get_property("product")
        if not self._product and product_id:
            self._product = self._ixapi.get_products(id=[product_id])[0]
        return self._product

    @property
    def subnet_v6(self):
        if self._ixapi.version > 1:
            try:
                return ipaddress.ip_network(self.get_property("subnet_v6"))
            except (AttributeError, ValueError):
                return None

        # v1 uses `ips` list, iterator over list and return best value
        for ip in self._ixapi.get_ips(id=self.get_property("ips")):
            if ip.address.version == 6:
                return ip.network
        return None

    @property
    def subnet_v4(self):
        if self._ixapi.version > 1:
            try:
                return ipaddress.ip_network(self.get_property("subnet_v4"))
            except (AttributeError, ValueError):
                return None

        # v1 uses `ips` list, iterator over list and return best value
        for ip in self._ixapi.get_ips(id=self.get_property("ips")):
            if ip.address.version == 4:
                return ip.network
        return None

    @property
    def network_features(self):
        id = self.get_property("network_features")
        if id and not self._network_features:
            self._network_features = self._ixapi.get_network_features(id=id)
        return self._network_features

    @property
    def network_service_configs(self):
        if not self._network_service_configs:
            self._network_service_configs = self._ixapi.get_network_service_configs(
                network_service_id=self.id
            )
        return self._network_service_configs


class NetworkServiceConfig(RemoteObject):
    """
    Proxy object for `network-service-configs` endpoint.
    """

    def __init__(self, ixapi, data):
        super().__init__(ixapi, data)

        self._ips = []
        self._macs = []

    @property
    def network_service(self):
        return self.get_property("network_service")

    @property
    def outer_vlan(self):
        return self.get_property("outer_vlan")

    @property
    def inner_vlan(self):
        return self.get_property("inner_vlan")

    @property
    def ips(self):
        id = self.get_property("ips")
        if id and not self._ips:
            self._ips = self._ixapi.get_ips(id=id)

        return self._ips

    @property
    def ipv4_address(self):
        for i in self.ips:
            if i.address.version == 4:
                return i
        return None

    @property
    def ipv6_address(self):
        for i in self.ips:
            if i.address.version == 6:
                return i
        return None

    @property
    def macs(self):
        id = self.get_property("macs")
        if id and not self._macs:
            self._macs = self._ixapi.get_macs(id=id)
        return self._macs

    @property
    def state(self):
        return self.get_property("state")

    @property
    def connection(self):
        """
        Returns a `net.Connection` matching the IP addresses.
        """
        qs_filter = Q()
        if self.ipv6_address:
            qs_filter |= Q(ipv4_address=self.ipv6_address)
        if self.ipv4_address:
            qs_filter |= Q(ipv4_address=self.ipv4_address)

        try:
            return Connection.objects.get(qs_filter)
        except (Connection.DoesNotExist, Connection.MultipleObjectsReturned):
            return None


class NetworkFeature(RemoteObject):
    @property
    def name(self):
        return self.get_property("name")

    @property
    def type(self):
        return self.get_property("type")

    @property
    def asn(self):
        return self.get_property("asn")

    @property
    def fqdn(self):
        return self.get_property("fqdn")

    @property
    def required(self):
        return self.get_property("required")

    @property
    def ip_v6(self):
        if self._ixapi.version > 1:
            try:
                return ipaddress.ip_address(self.get_property("ip_v6"))
            except (AttributeError, ValueError):
                return None

        # v1 uses `ips` list, iterator over list and return best value
        for ip in self._ixapi.get_ips(id=self.get_property("ips")):
            if ip.address.version == 6:
                return ip.address
        return None

    @property
    def ip_v4(self):
        if self._ixapi.version > 1:
            try:
                return ipaddress.ip_address(self.get_property("ip_v4"))
            except (AttributeError, ValueError):
                return None

        # v1 uses `ips` list, iterator over list and return best value
        for ip in self._ixapi.get_ips(id=self.get_property("ips")):
            if ip.address.version == 4:
                return ip.address
        return None


class IXAPI(ChangeLoggedModel):
    """
    An Endpoint holds the details to reach an IX-API given its URL, API key and
    secret.
    """

    name = models.CharField(max_length=128)
    url = models.CharField(max_length=2000, verbose_name="URL")
    api_key = models.CharField(max_length=2000, verbose_name="API key")
    api_secret = models.CharField(max_length=2000, verbose_name="API secret")
    identity = models.CharField(
        max_length=256,
        help_text="Identity used to interact with the IX-API",
        blank=True,
    )

    class Meta:
        verbose_name = "IX-API"
        ordering = ["url", "-created"]

    @property
    def version(self):
        """
        Returns the API version based on the URL.
        """
        if "/v1" in self.url:
            return 1
        elif "/v2" in self.url:
            return 2
        elif "/v3" in self.url:
            return 3
        else:
            return 0

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("extras:ixapi_details", args=[self.pk])

    def dial(self):
        """
        Returns a API client to use for querying.
        """
        c = Client(self)
        c.auth()

        return c

    def lookup(self, endpoint, params={}):
        """
        Performs a GET request with given parameters and returns the data as dict.
        """

        # Process special id key depending, change endpoint if a single id is given,
        # join id if it's a list
        if "id" in params:
            if type(params["id"]) is list:
                id = ",".join(params["id"])
                params["id"] = id
            else:
                endpoint = f"{endpoint}/{params['id']}"
                del params["id"]

        @cached_as(self, extra=params, timeout=settings.CACHE_TIMEOUT)
        def _lookup():
            # Make use of cache to speed up consecutive runs
            client = self.dial()
            _, data = client.get(endpoint, params=params)
            return data

        return _lookup()

    def get_health(self):
        """
        Returns the health of the API according to the following specification:

        https://tools.ietf.org/id/draft-inadarei-api-health-check-04.html

        This is only available for version greater than v1.
        """
        if self.version == 1:
            raise NotImplementedError(
                "health resource is not available on API version 1"
            )

        c = self.dial()
        _, data = c.get("health")

        if data["status"] in ("pass", "ok", "up"):
            return "healthy"
        elif data["status"] == "warn":
            return "degraded"
        else:
            return "unhealthy"

    def get_customers(self, id=0):
        """
        Returns our own customer.

        In theory the primary customer is us, that said we may be a reseller (thus
        having sub-customers), but we do not need to track this, at least yet.
        """
        c = self.dial()
        _, d = c.get("customers", {"id": id} if id else {})

        if id:
            return d[0]
        else:
            return d

    def get_identity(self):
        """
        Returns our own customer instance.
        """
        if not self.identity:
            return None
        else:
            return self.get_customers(id=self.identity)

    def get_ips(self, id=[]):
        d = []
        if id:
            d = self.lookup("ips", params={"id": id})
        else:
            d = self.lookup("ips", params={"consuming_customer": self.identity})

        return [IP(self, i) for i in d]

    def get_macs(self, id=[]):
        d = []
        if id:
            d = self.lookup("macs", params={"id": id})
        else:
            d = self.lookup("macs", params={"consuming_customer": self.identity})

        return [MAC(self, i) for i in d]

    def get_network_features(self, id=[]):
        d = []
        if id:
            d = self.lookup("network-features", params={"id": id})
        else:
            d = self.lookup("network-features")

        return [NetworkFeature(self, i) for i in d]

    def get_network_service_configs(
        self, network_service_id="", state=("production", "testing")
    ):
        """
        Returns configs for IXP services specific for us.
        """
        o = []
        if not network_service_id:
            o = self.lookup("network-service-configs")
        elif self.version > 1:
            o = self.lookup(
                "network-service-configs",
                params={"network_service": network_service_id},
            )
        else:
            for i in self.lookup("network-service-configs"):
                if i["network_service"] == network_service_id:
                    o.append(i)

        return [NetworkServiceConfig(self, i) for i in o if i["state"] in state]

    def get_network_services(self, id=[]):
        """
        Returns IXP services available for all IX members.
        """
        d = []
        if id:
            d = self.lookup("network-services", params={"id": id})
        else:
            d = self.lookup(
                "network-services",
                params={"consuming_customer": self.identity, "type": "exchange_lan"},
            )

        return [NetworkService(self, i) for i in d]

    def get_products(self, id=[]):
        if id:
            return self.lookup("products", params={"id": id})
        else:
            return self.lookup("products")
