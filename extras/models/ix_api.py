import ipaddress
import json
import logging

import requests
from cacheops import CacheMiss, cache
from django.db import models
from django.urls import reverse

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


class Client(object):
    """
    IX-API client to send requests.
    """

    def __init__(self, ix_api_endpoint, *args, **kwargs):
        self.ix_api_endpoint = ix_api_endpoint
        self.host = self.ix_api_endpoint.url
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
                "api_key": self.ix_api_endpoint.api_key,
                "api_secret": self.ix_api_endpoint.api_secret,
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

    def put(self, resource, payload=None):
        u = format_url(self.host, resource)
        logger.debug(f"sending put to api located at {u}")

        r = requests.put(u, json=payload, headers=self.request_headers)
        r.raise_for_status()
        return unpack_response(r)

    def patch(self, resource, payload=None):
        u = format_url(self.host, resource)
        logger.debug(f"sending patch to api located at {u}")

        r = requests.patch(u, json=payload, headers=self.request_headers)
        r.raise_for_status()
        return unpack_response(r)

    def delete(self, resource):
        u = format_url(self.host, resource)
        logger.debug(f"sending delete to api located at {u}")

        r = requests.delete(u, headers=self.request_headers)
        r.raise_for_status()
        return unpack_response(r)

    def options(self, resource):
        u = format_url(self.host, resource)
        logger.debug(f"sending options to api located at {u}")

        r = requests.options(u, headers=self.request_headers)
        r.raise_for_status()
        return unpack_response(r)


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

    def get_health(self):
        """
        Returns the health of the API according to the following specification:

        https://tools.ietf.org/id/draft-inadarei-api-health-check-04.html

        This is only available for v2.
        """
        if self.version == 1:
            raise NotImplementedError("health resource is not available version 1 API")

        c = self.dial()
        _, data = c.get("health")

        if data["status"] in ("pass", "ok", "up"):
            return "healthy"
        elif "warn" == data["status"]:
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
        return self.get_customers(id=self.identity)

    def lookup(self, endpoint, params={}):
        client = self.dial()
        _, data = client.get(endpoint, params=params)

        return data

    def get_contacts(self):
        d = self.lookup(f"contacts?consuming_customer={self.identity}")
        return d

    def get_demarcs(self):
        return self.lookup("demarcs")

    def get_connections(self):
        return self.lookup("connections", params={"consuming_customer": self.identity})

    def get_ips(self):
        return self.lookup("ips", params={"consuming_customer": self.identity})

    def get_macs(self):
        return self.lookup("macs", params={"consuming_customer": self.identity})

    def get_network_feature_configs(self):
        return self.lookup("network-feature-configs")

    def get_network_service_configs(self):
        return self.lookup("network-service-configs")

    def get_network_services(self):
        return self.lookup(
            "network-services", params={"consuming_customer": self.identity}
        )

    # Figure out what can be achieved with IX-API in the context of an IXP
    # List all connections on an IXP, service IDs, demarcation points, characteristics
    # (speed, …); list all IPs; list all MAC address (create/destroy them); list all
    # services (order/cancel then)
