import ipaddress
import logging

import napalm
from django.conf import settings
from django.core.cache import cache
from django.db import models, transaction
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from bgp.models import Community
from net.models import BFD, Connection
from peering.enums import BGPState
from peering.models import (
    AutonomousSystem,
    BGPGroup,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    RoutingPolicy,
)
from peering_manager.models import (
    JobsMixin,
    OrganisationalModel,
    PrimaryModel,
    PushedDataMixin,
    SynchronisedDataMixin,
    TemplateModel,
)

from .crypto import *
from .enums import DeviceStatus, PasswordAlgorithm

__all__ = ("Configuration", "Platform", "Router")


class Configuration(SynchronisedDataMixin, TemplateModel):
    def synchronise_data(self) -> None:
        self.template = self.data_file.data_as_string

    def render(self, context) -> str:
        """
        Render the template using Jinja2.
        """
        from peering_manager.jinja2 import render_jinja2

        return render_jinja2(
            self.template, context, trim=self.jinja2_trim, lstrip=self.jinja2_lstrip
        )


class Platform(OrganisationalModel):
    """
    Platform refers to the software or firmware running on a device.

    For example, "Juniper Junos", "Arista EOS" or "Cisco IOS-XR".

    Peering Manager uses platforms to determine how to interact with routers by
    specifying a NAPALM driver.
    """

    napalm_driver = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="NAPALM driver",
        help_text="The name of the NAPALM driver to use when interacting with devices",
    )
    napalm_args = models.JSONField(
        blank=True,
        null=True,
        verbose_name="NAPALM arguments",
        help_text="Additional arguments to pass when initiating the NAPALM driver (JSON format)",
    )
    password_algorithm = models.CharField(
        max_length=16,
        blank=True,
        choices=PasswordAlgorithm,
        help_text="Algorithm to cipher password in configuration",
    )

    def get_absolute_url(self) -> str:
        return f"{reverse('devices:router_list')}?platform_id={self.pk}"

    def encrypt_password(self, password) -> str:
        """
        Encrypts a password using the defined algorithm.

        If no algorithm is selected, the password will be returned as it is.
        If the password is already encrypted, it will be returned without performing
        a new encryption.
        """
        if not self.password_algorithm:
            return password

        return ENCRYPTERS[self.password_algorithm](password)

    def decrypt_password(self, password) -> str:
        """
        Decrypts a password using the defined algorithm.

        If no algorithm is selected, the password will be returned as it is.
        If the password is not encrypted, it will be returned without performing a
        decryption.
        """
        if not self.password_algorithm:
            return password

        return DECRYPTERS[self.password_algorithm](password)


class Router(JobsMixin, PushedDataMixin, PrimaryModel):
    local_autonomous_system = models.ForeignKey(
        to="peering.AutonomousSystem", on_delete=models.CASCADE, null=True
    )
    name = models.CharField(max_length=128, unique=True)
    hostname = models.CharField(max_length=256)
    platform = models.ForeignKey(
        to="devices.Platform",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        help_text="The router platform, used to interact with it",
    )
    status = models.CharField(
        max_length=50, choices=DeviceStatus, default=DeviceStatus.ENABLED
    )
    encrypt_passwords = models.BooleanField(
        blank=True,
        default=False,
        help_text="Try to encrypt passwords for peering sessions",
    )
    poll_bgp_sessions_state = models.BooleanField(
        blank=True,
        default=False,
        help_text="Enable polling of BGP sessions state",
        verbose_name="Poll BGP sessions state",
    )
    poll_bgp_sessions_last_updated = models.DateTimeField(blank=True, null=True)
    configuration_template = models.ForeignKey(
        "devices.Configuration", blank=True, null=True, on_delete=models.SET_NULL
    )
    communities = models.ManyToManyField(to="bgp.Community", blank=True)
    netbox_device_id = models.PositiveIntegerField(
        blank=True, default=0, verbose_name="NetBox device"
    )
    napalm_username = models.CharField(blank=True, null=True, max_length=256)
    napalm_password = models.CharField(blank=True, null=True, max_length=256)
    napalm_timeout = models.PositiveIntegerField(blank=True, default=0)
    napalm_args = models.JSONField(blank=True, null=True)

    logger = logging.getLogger("peering.manager.napalm")

    class Meta:
        ordering = ["local_autonomous_system", "name"]
        permissions = [
            ("view_router_configuration", "Can view router's configuration"),
            ("deploy_router_configuration", "Can deploy router's configuration"),
            (
                "push_router_configuration_to_data_source",
                "Can push router's configuration on a data source",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def get_direct_peering_sessions_list_url(self) -> str:
        return reverse("devices:router_direct_peering_sessions", args=[self.pk])

    def get_status_colour(self):
        return DeviceStatus.colours.get(self.status)

    def is_netbox_device(self):
        return self.netbox_device_id != 0

    def is_usable_for_task(self, job=None, logger=None):
        """
        Performs pre-flight checks to understand if a router is suited for background
        task processing.
        """
        if logger is None:
            logger = self.logger

        # Ensure device is not in disabled state
        if self.status == DeviceStatus.DISABLED:
            if job:
                job.log_warning("Router is disabled.", object=self, logger=logger)
            return False

        # Check if the router runs on a supported platform
        if not self.platform:
            if job:
                job.log_warning(
                    "Router has no assigned platform.", object=self, logger=logger
                )
            return False
        if not self.platform.napalm_driver:
            if job:
                job.log_warning(
                    "Router's platform has no NAPALM driver.",
                    object=self,
                    logger=logger,
                )
            return False

        return True

    def get_bgp_groups(self):
        """
        Returns BGP groups that can be deployed on this router.

        A group is considered as deployable on a router if direct peering sessions in
        the group are also attached to the router.
        """
        return BGPGroup.objects.filter(
            pk__in=DirectPeeringSession.objects.filter(router=self).values_list(
                "bgp_group", flat=True
            )
        )

    def get_connections(self, internet_exchange_point=None):
        """
        Returns connections attached to this router.
        """
        if internet_exchange_point:
            return Connection.objects.filter(
                internet_exchange_point=internet_exchange_point, router=self
            )
        return Connection.objects.filter(router=self)

    def get_internet_exchange_points(self):
        """
        Returns IXPs that this router is connected to.
        """
        return InternetExchange.objects.filter(
            pk__in=self.get_connections().values_list(
                "internet_exchange_point", flat=True
            )
        )

    def get_direct_autonomous_systems(self, bgp_group=None):
        """
        Returns autonomous systems that are directly peered with this router.
        """
        if bgp_group:
            sessions = DirectPeeringSession.objects.filter(
                bgp_group=bgp_group, router=self
            ).values_list("autonomous_system", flat=True)
        else:
            sessions = DirectPeeringSession.objects.filter(router=self).values_list(
                "autonomous_system", flat=True
            )
        return AutonomousSystem.objects.filter(pk__in=sessions)

    def get_ixp_autonomous_systems(self, internet_exchange_point=None):
        """
        Returns autonomous systems with which this router peers over IXPs.
        """
        return AutonomousSystem.objects.filter(
            pk__in=InternetExchangePeeringSession.objects.filter(
                ixp_connection__in=self.get_connections(
                    internet_exchange_point=internet_exchange_point
                )
            ).values_list("autonomous_system", flat=True)
        )

    def get_autonomous_systems(self):
        """
        Returns all autonomous systems with which this router peers.
        """
        return self.get_direct_autonomous_systems().union(
            self.get_ixp_autonomous_systems()
        )

    def get_direct_peering_sessions(self, bgp_group=None):
        """
        Returns all direct peering sessions setup on this router.
        """
        if bgp_group:
            return DirectPeeringSession.objects.filter(bgp_group=bgp_group, router=self)
        return DirectPeeringSession.objects.filter(router=self)

    def get_ixp_peering_sessions(self, internet_exchange_point=None):
        """
        Returns all IXP peering sessions setup on this router.
        """
        return InternetExchangePeeringSession.objects.filter(
            ixp_connection__in=self.get_connections(
                internet_exchange_point=internet_exchange_point
            )
        )

    def get_bfd_configs(self):
        """
        Returns all the BFDs that have at least one session configured on the router.
        """
        return BFD.objects.filter(
            Q(directpeeringsession__router=self)
            | Q(internetexchangepeeringsession__ixp_connection__router=self)
        ).distinct()

    def get_routing_policies(self):
        """
        Returns all routing policies that this router should have.
        """
        q = Q()

        if direct_sessions := list(
            self.get_direct_peering_sessions().values_list("pk", flat=True)
        ):
            q |= Q(
                directpeeringsession_import_routing_policies__in=direct_sessions
            ) | Q(directpeeringsession_export_routing_policies__in=direct_sessions)

            direct_as = (
                DirectPeeringSession.objects.filter(pk__in=direct_sessions)
                .values_list("autonomous_system", flat=True)
                .distinct()
            )
            q |= Q(autonomoussystem_import_routing_policies__in=direct_as) | Q(
                autonomoussystem_export_routing_policies__in=direct_as
            )

            if bgp_groups := (
                DirectPeeringSession.objects.filter(
                    pk__in=direct_sessions, bgp_group__isnull=False
                )
                .values_list("bgp_group", flat=True)
                .distinct()
            ):
                q |= Q(bgpgroup_import_routing_policies__in=bgp_groups) | Q(
                    bgpgroup_export_routing_policies__in=bgp_groups
                )

        if ixp_sessions := list(
            self.get_ixp_peering_sessions().values_list("pk", flat=True)
        ):
            q |= Q(
                internetexchangepeeringsession_import_routing_policies__in=ixp_sessions
            ) | Q(
                internetexchangepeeringsession_export_routing_policies__in=ixp_sessions
            )

            ixp_as = (
                InternetExchangePeeringSession.objects.filter(pk__in=ixp_sessions)
                .values_list("autonomous_system", flat=True)
                .distinct()
            )
            q |= Q(autonomoussystem_import_routing_policies__in=ixp_as) | Q(
                autonomoussystem_export_routing_policies__in=ixp_as
            )

            ixps = (
                InternetExchangePeeringSession.objects.filter(pk__in=ixp_sessions)
                .values_list("ixp_connection__internet_exchange_point", flat=True)
                .distinct()
            )
            q |= Q(internetexchange_import_routing_policies__in=ixps) | Q(
                internetexchange_export_routing_policies__in=ixps
            )

        return RoutingPolicy.objects.filter(q).distinct().order_by("name")

    def get_configuration_context(self):
        """
        Returns a dict, to be used in a Jinja2 environment, that holds enough data to
        help in creating a configuration from a template.
        """
        return {
            "router": self,
            "local_as": self.local_autonomous_system,
            "autonomous_systems": self.get_autonomous_systems(),
            "bgp_groups": self.get_bgp_groups(),
            "internet_exchange_points": self.get_internet_exchange_points(),
            "communities": Community.objects.all(),
            "routing_policies": self.get_routing_policies(),
        }

    def render_configuration(self):
        """
        Returns the configuration of a router according to the template in use.

        If no template is used, an empty string is returned.
        """
        from .signals import post_configuration_rendering, pre_configuration_rendering

        pre_configuration_rendering.send(sender=self.__class__, instance=self)

        if self.configuration_template:
            context = self.get_configuration_context()
            rendered = self.configuration_template.render(context)
        else:
            rendered = ""

        post_configuration_rendering.send(
            sender=self.__class__, instance=self, configuration=rendered
        )

        return rendered

    def get_napalm_device(self):
        """
        Returns an instance of the NAPALM driver to connect to a router.
        """
        if not self.platform or not self.platform.napalm_driver:
            self.logger.debug("no napalm driver defined")
            return None

        self.logger.debug(f"looking for napalm driver '{self.platform.napalm_driver}'")
        try:
            # Driver found, instanciate it
            driver = napalm.get_network_driver(self.platform.napalm_driver)
            self.logger.debug(f"found napalm driver '{self.platform.napalm_driver}'")

            # Merge NAPALM args: first global, then platform's, finish with router's
            args = settings.NAPALM_ARGS
            if self.platform.napalm_args:
                args.update(self.platform.napalm_args)
            if self.napalm_args:
                args.update(self.napalm_args)

            return driver(
                hostname=self.hostname,
                username=self.napalm_username or settings.NAPALM_USERNAME,
                password=self.napalm_password or settings.NAPALM_PASSWORD,
                timeout=self.napalm_timeout or settings.NAPALM_TIMEOUT,
                optional_args=args,
            )
        except napalm.base.exceptions.ModuleImportError:
            # Unable to import proper driver from napalm
            # Most probably due to a broken install
            self.logger.error(
                f"no napalm driver: '{self.platform.napalm_driver}' for platform: '{self.platform}' found (not installed or does not exist)"
            )
            return None

    def open_napalm_device(self, device):
        """
        Opens a connection with a device using NAPALM.

        This method returns `True` if the connection is properly opened or `False` in
        any other cases. It handles exceptions that can occur during the connection
        opening process by itself.

        It is a wrapper method mostly used for logging purpose.
        """
        success = False

        if not device:
            return success

        try:
            self.logger.debug(f"connecting to {self.hostname}")
            device.open()
        except napalm.base.exceptions.ConnectionException as e:
            self.logger.error(
                f'error while trying to connect to {self.hostname} reason "{e}"'
            )
        except Exception:
            self.logger.error(f"error while trying to connect to {self.hostname}")
        else:
            self.logger.debug(f"successfully connected to {self.hostname}")
            success = True

        return success

    def close_napalm_device(self, device):
        """
        Closes a connection with a device using NAPALM.

        This method returns True if the connection is properly closed or False
        if the device is not valid.

        It is a wrapper method mostly used for logging purpose.
        """
        if not device:
            return False

        try:
            device.close()
            self.logger.debug(f"closed connection with {self.hostname}")
        except Exception as e:
            self.logger.debug(f"failed to close connection with {self.hostname}: {e}")
            return False

        return True

    def test_napalm_connection(self):
        """
        Opens and closes a connection with a device using NAPALM to see if it
        is possible to interact with it.

        This method returns `True` only if the connection opening and closing are
        both successful.
        """
        opened, alive, closed = False, False, False
        device = self.get_napalm_device()

        # Open and close the test_napalm_connection
        self.logger.debug(f"testing connection with {self.hostname}")
        opened = self.open_napalm_device(device)
        if opened:
            alive = device.is_alive()
            if alive:
                closed = self.close_napalm_device(device)

        # Issue while opening or closing the connection
        if not opened or not closed or not alive:
            self.logger.error(
                f"cannot connect to {self.hostname}, napalm functions won't work"
            )

        return opened and closed and alive

    def set_napalm_configuration(self, config, commit=False):
        """
        Tries to merge a given configuration on a device using NAPALM.

        This methods returns the changes applied to the configuration if the merge was
        successful. It will return None in any other cases.

        The optional named argument 'commit' is a boolean which is used to know if the
        changes must be commited or discarded. The default value is `False` which
        means that the changes will be discarded.
        """
        from .signals import post_device_configuration, pre_device_configuration

        error, changes = None, None

        # Ensure device is enabled, we allow maintenance mode to force a config push
        if not self.is_usable_for_task():
            self.logger.debug(
                f"{self.hostname}: unusable (due to disabled state or platform), exiting config push"
            )
            return (
                "device is unusable (check state or platform), cannot deploy config",
                changes,
            )

        # Make sure there actually a configuration to merge
        if config is None or not isinstance(config, str) or not config.strip():
            self.logger.debug(f"{self.hostname}: no configuration to merge: {config}")
            return "no configuration found to be merged", changes

        device = self.get_napalm_device()
        opened = self.open_napalm_device(device)

        if opened:
            try:
                # Load the config
                self.logger.debug(f"merging configuration on {self.hostname}")
                device.load_merge_candidate(config=config)
                self.logger.debug(f"merged configuration\n{config}")

                # Get the config diff
                self.logger.debug(
                    f"checking for configuration changes on {self.hostname}"
                )
                changes = device.compare_config()
                if not changes:
                    self.logger.debug("no configuration changes detected")
                else:
                    self.logger.debug(f"raw napalm output\n{changes}")

                    # Commit the config if required
                    if commit:
                        pre_device_configuration.send(
                            sender=self.__class__, instance=self
                        )
                        self.logger.debug(f"commiting configuration on {self.hostname}")
                        device.commit_config()
                        post_device_configuration.send(
                            sender=self.__class__, instance=self, configuration=config
                        )
                    else:
                        self.logger.debug(
                            f"discarding configuration on {self.hostname}"
                        )
                        device.discard_config()
            except Exception as e:
                try:
                    # Try to restore initial config
                    device.discard_config()
                except Exception as f:
                    self.logger.debug(
                        f'unable to discard configuration on {self.hostname} reason "{f}"'
                    )
                changes = None
                error = str(e)
                self.logger.debug(
                    f'unable to merge configuration on {self.hostname} reason "{e}"'
                )
            else:
                self.logger.debug(
                    f"successfully merged configuration on {self.hostname}"
                )
            finally:
                closed = self.close_napalm_device(device)
                if not closed:
                    self.logger.debug(
                        f"error while closing connection with {self.hostname}"
                    )
        else:
            error = f"unable to connect to {self.hostname}"

        return error, changes

    def _napalm_bgp_neighbors_to_peer_list(self, napalm_dict):
        bgp_peers = []

        if not napalm_dict:
            return bgp_peers

        # For each VRF
        for vrf in napalm_dict:
            # Get peers inside it
            peers = napalm_dict[vrf]["peers"]
            self.logger.debug(
                f"found {len(peers)} bgp neighbors in {vrf} vrf on {self.hostname}"
            )

            # For each peer handle its IP address and the needed details
            for ip, details in peers.items():
                if "remote_as" not in details:
                    self.logger.debug(
                        f"ignored bgp neighbor {ip} in {vrf} vrf on {self.hostname}",
                    )
                elif ip in [str(i["ip_address"]) for i in bgp_peers]:
                    self.logger.debug(f"duplicate bgp neighbor {ip} on {self.hostname}")
                else:
                    try:
                        # Save the BGP session (IP and remote ASN)
                        bgp_peers.append(
                            {
                                "ip_address": ipaddress.ip_address(ip),
                                "remote_asn": details["remote_as"],
                            }
                        )
                    except ValueError as e:
                        # Error while parsing the IP address
                        self.logger.error(
                            f'ignored bgp neighbor {ip} in {vrf} vrf on {self.hostname} reason "{e}"',
                        )
                        # Force next iteration
                        continue

        return bgp_peers

    def get_napalm_bgp_neighbors(self):
        """
        Returns a list of dictionaries listing all BGP neighbors found on the
        router using NAPALM.

        Each dictionary contains two keys 'ip_address' and 'remote_asn'.

        If an error occurs or no BGP neighbors can be found, the returned list
        will be empty.
        """
        bgp_sessions = []

        device = self.get_napalm_device()
        opened = self.open_napalm_device(device)

        if opened:
            # Get all BGP neighbors on the router
            self.logger.debug(f"getting bgp neighbors on {self.hostname}")
            bgp_neighbors = device.get_bgp_neighbors()
            self.logger.debug(f"raw napalm output {bgp_neighbors}")
            self.logger.debug(
                f"found {len(bgp_neighbors)} vrfs with bgp neighbors on {self.hostname}"
            )

            bgp_sessions = self._napalm_bgp_neighbors_to_peer_list(bgp_neighbors)
            self.logger.debug(
                f"found {len(bgp_sessions)} bgp neighbors on {self.hostname}"
            )

            # Close connection to the device
            closed = self.close_napalm_device(device)
            if not closed:
                self.logger.debug(
                    f"error while closing connection with {self.hostname}"
                )

        return bgp_sessions

    def get_bgp_neighbors(self):
        """
        Returns a list of dictionaries listing all BGP neighbors found on the router
        using NAPALM.

        Each dictionary contains two keys 'ip_address' and 'remote_asn'.

        If an error occurs or no BGP neighbors can be found, the returned list will be
        empty.
        """
        return self.get_napalm_bgp_neighbors()

    def find_bgp_neighbor_detail(self, bgp_neighbors, ip_address):
        """
        Finds and returns a single BGP neighbor amongst others.
        """
        # NAPALM dict expected
        if not isinstance(bgp_neighbors, dict):
            return None

        # Make sure to use an IP object
        if type(ip_address) in (str, ipaddress.IPv4Address, ipaddress.IPv6Address):
            ip_address = ipaddress.ip_interface(ip_address)

        for _, asn in bgp_neighbors.items():
            for _, neighbors in asn.items():
                for neighbor in neighbors:
                    neighbor_ip_address = ipaddress.ip_address(
                        neighbor["remote_address"]
                    )
                    if ip_address.ip == neighbor_ip_address:
                        return neighbor

        return None

    def get_napalm_bgp_neighbors_detail(self, ip_address=None):
        """
        Returns a list of dictionaries listing all BGP neighbors found on the router
        using NAPALM and there respective detail.

        If an error occurs or no BGP neighbors can be found, the returned list will be
        empty.
        """
        bgp_neighbors_detail = []

        device = self.get_napalm_device()
        opened = self.open_napalm_device(device)

        if opened:
            # Get all BGP neighbors on the router
            self.logger.debug(f"getting bgp neighbors detail on {self.hostname}")
            bgp_neighbors_detail = device.get_bgp_neighbors_detail()
            self.logger.debug(f"raw napalm output {bgp_neighbors_detail}")
            self.logger.debug(
                f"found {len(bgp_neighbors_detail)} vrfs with bgp neighbors on {self.hostname}"
            )

            # Close connection to the device
            closed = self.close_napalm_device(device)
            if not closed:
                self.logger.debug(
                    f"error while closing connection with {self.hostname}"
                )

        return (
            bgp_neighbors_detail
            if not ip_address
            else self.find_bgp_neighbor_detail(bgp_neighbors_detail, ip_address)
        )

    def get_bgp_neighbors_detail(self, ip_address=None):
        """
        Returns a list of dictionaries listing all BGP neighbors found on the router
        using NAPALM and their respective detail.

        If the `ip_address` named parameter is not `None`, only the neighbor with this
        IP address will be returned

        If an error occurs or no BGP neighbors can be found, the returned list
        will be empty.
        """
        cache_key = f"bgp_neighbors_detail_{ip_address or ''}_{self.pk}"
        cached_value = cache.get(cache_key)

        if cached_value:
            return cached_value

        r = dict(self.get_napalm_bgp_neighbors_detail(ip_address=ip_address))

        cache.set(cache_key, r, timeout=settings.CACHE_BGP_DETAIL_TIMEOUT)
        return r

    def bgp_neighbors_detail_as_list(self, bgp_neighbors_detail):
        """
        Returns a list based on the dict returned by calling
        `get_napalm_bgp_neighbors_detail`.
        """
        flattened = []

        if not bgp_neighbors_detail:
            return flattened

        for vrf in bgp_neighbors_detail:
            for asn in bgp_neighbors_detail[vrf]:
                flattened.extend(bgp_neighbors_detail[vrf][asn])

        return flattened

    def poll_bgp_session(self, ip_address):
        """
        Polls the state of a single session given its IP address.
        """
        if not self.is_usable_for_task():
            self.logger.debug(
                f"cannot poll bgp sessions state for {self.hostname}, disabled or platform unusable"
            )
            return False
        if not self.poll_bgp_sessions_state:
            self.logger.debug(
                f"bgp sessions state polling disabled for {self.hostname}"
            )
            return False

        # Get BGP session detail
        bgp_neighbor_detail = self.get_bgp_neighbors_detail(ip_address=ip_address)
        if bgp_neighbor_detail:
            return {
                "bgp_state": bgp_neighbor_detail["connection_state"].lower(),
                "received_prefix_count": max(
                    0, bgp_neighbor_detail["received_prefix_count"]
                ),
                "accepted_prefix_count": max(
                    0, bgp_neighbor_detail["accepted_prefix_count"]
                ),
                "advertised_prefix_count": max(
                    0, bgp_neighbor_detail["advertised_prefix_count"]
                ),
            }

        return {}

    @transaction.atomic
    def poll_bgp_sessions(self):
        """
        Polls the state of all BGP sessions on this router and update the
        corresponding IXP or direct sessions found in records.
        """
        if not self.is_usable_for_task():
            self.logger.debug(
                f"cannot poll bgp sessions state for {self.hostname}, disabled or platform unusable"
            )
            return False, 0
        if not self.poll_bgp_sessions_state:
            self.logger.debug(
                f"bgp sessions state polling disabled for {self.hostname}"
            )
            return False, 0

        directs = self.get_direct_peering_sessions()
        ixps = self.get_ixp_peering_sessions()

        if not directs and not ixps:
            self.logger.debug(f"no bgp sessions attached to {self.hostname}")
            return True, 0

        # Get BGP neighbors details from router, but only get them once
        bgp_neighbors_detail = self.bgp_neighbors_detail_as_list(
            self.get_bgp_neighbors_detail()
        )
        if not bgp_neighbors_detail:
            self.logger.debug(f"no bgp sessions found on {self.hostname}")
            return True, 0

        count = 0
        for neighbor_detail in bgp_neighbors_detail:
            ip_address = neighbor_detail["remote_address"]
            self.logger.debug(f"looking for session {ip_address} in {self.hostname}")

            # Check if the session is in our database, skip it if not
            # NAPALM ignores prefix length, so __host is used to lookup the actual IP
            match = directs.filter(ip_address__host=ip_address) or ixps.filter(
                ip_address__host=ip_address
            )
            if not match:
                self.logger.debug(f"session {ip_address} not found for {self.hostname}")
                continue
            if match.count() > 1:
                self.logger.debug(
                    f"multiple sessions found for {ip_address} and {self.hostname}, ignoring"
                )
                continue

            # Get info that we are actually looking for
            state = neighbor_detail["connection_state"].lower()
            self.logger.debug(
                f"found session {ip_address} on {self.hostname} in {state} state"
            )

            # Update fields
            session = match.first()
            session.bgp_state = state
            session.received_prefix_count = max(
                0, neighbor_detail["received_prefix_count"]
            )
            session.accepted_prefix_count = max(
                0, neighbor_detail["accepted_prefix_count"]
            )
            session.advertised_prefix_count = max(
                0, neighbor_detail["advertised_prefix_count"]
            )
            # Update the BGP state of the session
            if session.bgp_state == BGPState.ESTABLISHED:
                session.last_established_state = timezone.now()
            session.save()
            self.logger.debug(
                f"session {ip_address} on {self.hostname} saved as {state}"
            )
            count += 1

        # Save last session states update
        self.poll_bgp_sessions_last_updated = timezone.now()
        self.save()

        return True, count

    def push_data(self):
        if self.data_source and self.data_path:
            self.data_source.push(self.data_path, self.render_configuration())
