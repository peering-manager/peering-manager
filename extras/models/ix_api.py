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

    def create_auth_token(self):
        """
        Creates a new set of tokens to start interacting with the API.
        """
        _, j = self.post(
            "auth/token",
            payload={
                "api_key": self.ix_api_endpoint.api_key,
                "api_secret": self.ix_api_endpoint.api_secret,
            },
        )
        logger.debug(f"api at {self.host} responded {j}")

        if "access_token" not in j or "refresh_token" not in j:
            logger.error(f"malformed response from api at {self.host}")
            return

        self.access_token = j["access_token"]
        self.refresh_token = j["refresh_token"]

    def refresh_auth_token(self):
        """
        Refreshes the current session to continue using the same token.
        """
        _, j = self.post("auth/refresh", payload={"refresh_token": self.refresh_token})
        logger.debug(f"api at {self.host} responded {j}")

        if "access_token" not in j or "refresh_token" not in j:
            logger.error(f"malformed response from api at {self.host}")
            return

        self.access_token = j["access_token"]
        self.refresh_token = j["refresh_token"]

    def get(self, resource, query=None):
        u = format_url(self.host, resource)
        logger.debug(f"sending get to api located at {u}")

        r = requests.get(u, query, headers=self.request_headers)
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


class Customer(object):
    def __init__(self, *args, **kwargs):
        self.id = kwargs.pop("id")
        self.parent = kwargs.pop("parent", 0)
        self.external_ref = kwargs.pop("external_ref", "")
        self.name = kwargs.pop("name")
        self.state = kwargs.pop("state")
        self.status = []

    def __str__(self):
        s = self.name

        if self.external_ref:
            s += f" {self.external_ref}"

        return s


class CustomerAllocated(object):
    def __init__(self, *args, **kwargs):
        self.managing_customer_id = kwargs.pop("managing_customer", 0)
        self.consuming_customer_id = kwargs.pop("consuming_customer", 0)


class Contact(CustomerAllocated):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.id = kwargs.pop("id")
        self.external_ref = kwargs.pop("external_ref", "")
        self.type = kwargs.pop("type", "")
        self.legal_company_name = kwargs.pop("legal_company_name", "")
        self.vat_number = kwargs.pop("vat_number", "")
        self.address_country = kwargs.pop("address_country", "")
        self.address_locality = kwargs.pop("address_locality", "")
        self.address_region = kwargs.pop("address_region", "")
        self.street_address = kwargs.pop("street_address", "")
        self.post_office_box_number = kwargs.pop("post_office_box_number", "")
        self.postal_code = kwargs.pop("postal_code", "")
        self.name = kwargs.pop("name", "")
        self.email = kwargs.pop("email", "")
        self.telephone = kwargs.pop("telephone", "")


class IP(CustomerAllocated):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.id = kwargs.pop("id")
        self.external_ref = kwargs.pop("external_ref", "")
        self.version = kwargs.pop("version")
        self.address = kwargs.pop("address")
        self.prefix_length = kwargs.pop("prefix_length")
        self.fqdn = kwargs.pop("fqdn", "")

    @property
    def ip_address(self):
        ip = f"{self.address}/{self.prefix_length}"
        if self.version == 6:
            return ipaddress.IPv6Interface(ip)
        else:
            return ipaddress.IPv4Interface(ip)


class MAC(CustomerAllocated):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.id = kwargs.pop("id")
        self.external_ref = kwargs.pop("external_ref", "")
        self.address = kwargs.pop("address")
        self.valid_not_before = kwargs.pop("valid_not_before", "")
        self.valid_not_after = kwargs.pop("valid_not_after", "")


class NetworkService(CustomerAllocated):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.id = kwargs.pop("id")
        self.external_ref = kwargs.pop("external_ref", "")
        self.type = kwargs.pop("type")
        self.contacts = kwargs.pop("contacts")
        self.purchase_order = kwargs.pop("purchase_order")
        self.contract_ref = kwargs.pop("contract_ref")
        self.product = kwargs.pop("product")
        self.required_contact_types = kwargs.pop("required_contact_types")
        self.network_features = kwargs.pop("network_features")
        self.name = kwargs.pop("name")
        self.metro_area = kwargs.pop("metro_area")
        self.peeringdb_ixid = kwargs.pop("peeringdb_ixid", 0)
        self.ixfdb_ixid = kwargs.pop("ixfdb_ixid", 0)
        self.ips = kwargs.pop("ips")


class IXAPI(ChangeLoggedModel):
    """
    An Endpoint holds the details to reach an IX-API given its URL, API key and
    secret.
    """

    name = models.CharField(max_length=128)
    url = models.CharField(max_length=2000, verbose_name="URL")
    api_key = models.CharField(max_length=2000, verbose_name="API key")
    api_secret = models.CharField(max_length=2000, verbose_name="API secret")
    identity = models.PositiveBigIntegerField(
        help_text="Identity used to interact with the IX-API"
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
        c.create_auth_token()

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

    def get_customer(self, id=0):
        """
        Returns our own customer.

        In theory the primary customer is us, that said we may be a reseller (thus
        having sub-customers), but we do not need to track this, at least yet.
        """
        endpoint = "customers"
        if id:
            endpoint += f"?id={id}"

        c = self.dial()
        _, data = c.get(endpoint)

        if id:
            return Customer(**data[0])

        return [Customer(**d) for d in data]

    def get_identity(self):
        """
        Returns our own customer instance.
        """
        return self.get_customer(id=self.identity)

    def get_something(self, something):
        client = self.dial()
        _, data = client.get(something)

        return data

    def get_contacts(self):
        d = self.get_something(f"contacts?consuming_customer={self.identity}")
        return [Contact(**data) for data in d]

    def get_demarcs(self):
        return self.get_something("demarcs")

    def get_connections(self):
        return self.get_something("connections")

    def get_ips(self):
        d = self.get_something(f"ips?consuming_customer={self.identity}")
        return [IP(**data) for data in d]

    def get_macs(self):
        d = self.get_something("macs?consuming_customer={self.identity}")
        return [MAC(**data) for data in d]

    def get_network_feature_configs(self):
        return self.get_something("network-feature-configs")

    def get_network_service_configs(self):
        return self.get_something("network-service-configs")

    def get_network_services(self):
        d = self.get_something(f"network-services?consuming_customer={self.identity}")
        for data in d:
            if data["peeringdb_ixid"]:
                print(data)
        return [NetworkService(**data) for data in d]

    # Figure out what can be achieved with IX-API in the context of an IXP
    # List all connections on an IXP, service IDs, demarcation points, characteristics
    # (speed, …); list all IPs; list all MAC address (create/destroy them); list all
    # services (order/cancel then)
