import ipaddress
import json
import logging
import requests

from django.db import transaction
from django.conf import settings
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.utils import timezone

from .models import Contact, Network, NetworkIXLAN, PeerRecord, Prefix, Synchronization


NAMESPACES = {
    "facility": "fac",
    "internet_exchange": "ix",
    "internet_exchange_facility": "ixfac",
    "internet_exchange_lan": "ixlan",
    "internet_exchange_prefix": "ixpfx",
    "network": "net",
    "network_facility": "netfac",
    "network_internet_exchange_lan": "netixlan",
    "organization": "org",
    "network_contact": "poc",
}


class Object(object):
    """
    This is a class used to load JSON data into class fields for easier use.
    """

    def __init__(self, data):
        self.__dict__ = json.loads(json.dumps(data))

    def __str__(self):
        return str(self.__dict__)


class PeeringDB(object):
    """
    Class used to interact with the PeeringDB API.
    """

    logger = logging.getLogger("peering.manager.peeringdb")

    def lookup(self, namespace, search):
        """
        Sends a get request to the API given a namespace and some parameters.
        """
        # Enforce trailing slash and add namespace
        api_url = settings.PEERINGDB_API.strip("/") + "/" + namespace

        # Check if the depth param is provided, add it if not
        if "depth" not in search:
            search["depth"] = 1

        # Make the request
        # Authenticate with a basic auth method if the user provided some credentials
        self.logger.debug("calling api: %s | %s", api_url, search)
        if settings.PEERINGDB_USERNAME:
            response = requests.get(
                api_url,
                params=search,
                auth=(settings.PEERINGDB_USERNAME, settings.PEERINGDB_PASSWORD),
            )
        else:
            response = requests.get(api_url, params=search)

        return response.json() if response.status_code == 200 else None

    def record_last_sync(self, time, objects_changes):
        """
        Save the last synchronization details (number of objects and time) for
        later use (and logs).
        """
        last_sync = None
        number_of_changes = (
            objects_changes["added"]
            + objects_changes["updated"]
            + objects_changes["deleted"]
        )

        # Save the last sync time only if objects were retrieved
        if number_of_changes > 0:
            values = {
                "time": time,
                "added": objects_changes["added"],
                "updated": objects_changes["updated"],
                "deleted": objects_changes["deleted"],
            }

            last_sync = Synchronization(**values)
            last_sync.save()

            self.logger.debug(
                "synchronizated %s objects at %s", number_of_changes, last_sync.time
            )

        return last_sync

    def get_last_synchronization(self):
        """
        Return the last synchronization.
        """
        try:
            return Synchronization.objects.latest("time")
        except Synchronization.DoesNotExist:
            pass

        return None

    def get_last_sync_time(self):
        """
        Return the last time of synchronization based on the latest record.
        The time is returned as an integer UNIX timestamp.
        """
        # Assume first sync
        last_sync_time = 0
        last_sync = self.get_last_synchronization()

        if last_sync:
            last_sync_time = last_sync.time.timestamp()

        return int(last_sync_time)

    def synchronize_objects(self, last_sync, namespace, model):
        """
        Synchronizes all the objects of a namespace of the PeeringDB to the
        local database. This function is meant to be run regularly to update
        the local database with the latest changes.

        If the object already exists locally it will be updated and no new
        entry will be created.

        If the object is marked as deleted in the PeeringDB, it will be locally
        deleted.

        This function returns the number of objects that have been successfully
        synchronized to the local database.
        """
        objects_added = 0
        objects_updated = 0
        objects_deleted = 0

        # Get all network changes since the last sync
        search = {"since": last_sync, "depth": 0}
        result = self.lookup(namespace, search)

        if not result:
            return None

        for data in result["data"]:
            peeringdb_object = Object(data)
            marked_as_deleted = peeringdb_object.status == "deleted"
            marked_as_new = False

            try:
                # Get the local object by its ID
                local_object = model.objects.get(pk=peeringdb_object.id)

                # Object marked as deleted so remove it locally too
                if marked_as_deleted:
                    local_object.delete()
                    objects_deleted += 1
                    self.logger.debug(
                        "deleted %s #%s from local database",
                        model._meta.verbose_name.lower(),
                        peeringdb_object.id,
                    )
                    continue
            except model.DoesNotExist:
                # Local object does not exist so create it
                local_object = model()
                marked_as_new = True

            # Set the value for each field
            for model_field in model._meta.get_fields():
                field_name = model_field.name

                # Do not try to follow foreign keys
                if model_field.get_internal_type() == "ForeignKey":
                    continue

                value = getattr(peeringdb_object, field_name)

                try:
                    field = local_object._meta.get_field(field_name)
                except FieldDoesNotExist:
                    field = None
                    self.logger.error(
                        "bug found? field: %s for model: %s",
                        field_name,
                        model._meta.verbose_name.lower(),
                    )

                if field:
                    setattr(local_object, field_name, value)

            try:
                local_object.full_clean()
            except ValidationError as e:
                self.logger.error(
                    "bug found? error while validating id: %s for model: %s",
                    peeringdb_object.id,
                    model._meta.verbose_name.lower(),
                )
                self.logger.error(e)
                continue

            # Save the local object
            local_object.save()

            # Update counters
            if marked_as_new:
                objects_added += 1
                self.logger.debug(
                    "created %s #%s from peeringdb",
                    model._meta.verbose_name.lower(),
                    local_object.id,
                )
            else:
                objects_updated += 1
                self.logger.debug(
                    "updated %s #%s from peeringdb",
                    model._meta.verbose_name.lower(),
                    local_object.id,
                )

        return (objects_added, objects_updated, objects_deleted)

    def update_local_database(self, last_sync):
        """
        Update the local database by synchronizing all PeeringDB API's
        namespaces that we are actually caring about.
        """
        # Set time of sync
        time_of_sync = timezone.now()
        objects_to_sync = [
            (NAMESPACES["network_contact"], Contact),
            (NAMESPACES["network"], Network),
            (NAMESPACES["network_internet_exchange_lan"], NetworkIXLAN),
            (NAMESPACES["internet_exchange_prefix"], Prefix),
        ]
        list_of_changes = []

        # Make a single transaction, avoid too much database commits (poor
        # speed) and fail the whole synchronization if something goes wrong
        with transaction.atomic():
            # Try to sync objects
            for (namespace, object_type) in objects_to_sync:
                changes = self.synchronize_objects(last_sync, namespace, object_type)
                list_of_changes.append(changes)

        objects_changes = {
            "added": sum(added for added, _, _ in list_of_changes),
            "updated": sum(updated for _, updated, _ in list_of_changes),
            "deleted": sum(deleted for _, _, deleted in list_of_changes),
        }

        # Save the last sync time
        return self.record_last_sync(time_of_sync, objects_changes)

    def clear_local_database(self):
        """
        Delete all data related to the local database. This can be used to get a
        fresh start.
        """
        for model in [Contact, Network, NetworkIXLAN, PeerRecord, Synchronization]:
            model.objects.all().delete()

    def force_peer_records_discovery(self):
        """
        Force the peer records cache to be [re]built. This function can be used
        if this cache appears to be out of sync or inconsistent.
        """
        indexed = 0

        with transaction.atomic():
            # First of all, delete all existing peer records
            PeerRecord.objects.all().delete()

            # Build the cache
            for network_ixlan in NetworkIXLAN.objects.all():
                # Ignore if we have no IPv6 and no IPv4 to peer with
                if not network_ixlan.ipaddr6 and not network_ixlan.ipaddr4:
                    self.logger.debug(
                        "network ixlan with as%s and ixlan id %s"
                        " ignored, no ipv6 and no ipv4",
                        network_ixlan.asn,
                        network_ixlan.ixlan_id,
                    )
                    continue

                network = None
                try:
                    network = Network.objects.get(asn=network_ixlan.asn)
                except Network.DoesNotExist:
                    self.logger.debug("unable to find network as%s", network_ixlan.asn)

                if network:
                    PeerRecord.objects.create(
                        network=network, network_ixlan=network_ixlan
                    )
                    self.logger.debug(
                        "peer record with network as%s and ixlan" "id %s created",
                        network_ixlan.asn,
                        network_ixlan.ixlan_id,
                    )
                    indexed += 1
                else:
                    self.logger.debug(
                        "network ixlan with as%s and ixlan id %s" " ignored",
                        network_ixlan.asn,
                        network_ixlan.ixlan_id,
                    )

            return indexed

    def get_autonomous_system(self, asn):
        """
        Return an AS (and its details) given its ASN. The result can come from
        the local database (cache built with the peeringdb_sync command). If
        the AS details are not found in the local database, they will be
        fetched online which will take more time.
        """
        try:
            # Try to get from cached data
            network = Network.objects.get(asn=asn)
        except Network.DoesNotExist:
            # If no cached data found, query the API
            search = {"asn": asn}
            result = self.lookup(NAMESPACES["network"], search)

            if not result or not result["data"]:
                return None

            network = Object(result["data"][0])

        return network

    def get_autonomous_system_contacts(self, asn):
        network = self.get_autonomous_system(asn)
        if network:
            return Contact.objects.filter(net_id=network.id)
        else:
            return Contact.objects.none()

    def get_ix_network(self, ix_network_id):
        """
        Return an IX network (and its details) given an IP address. The result
        can come from the local database (cache built with the peeringdb_sync
        command). If the IX network is not found in the local database, it will
        be fetched online which will take more time.
        """
        try:
            # Try to get from cached data
            network_ixlan = NetworkIXLAN.objects.get(id=ix_network_id)
        except NetworkIXLAN.DoesNotExist:
            # If no cached data found, query the API
            search = {"id": ix_network_id}
            result = self.lookup(NAMESPACES["network_internet_exchange_lan"], search)

            if not result or not result["data"]:
                return None

            network_ixlan = Object(result["data"][0])

        return network_ixlan

    def get_ix_network_by_ip_address(self, ipv6_address=None, ipv4_address=None):
        """
        Return an IX network (and its details) given its ID. The result can
        come from the local database (cache built with the peeringdb_sync
        command). If the IX network is not found in the local database, it will
        be fetched online which will take more time.
        """
        if not ipv6_address and not ipv4_address:
            return None

        search = {}
        if ipv6_address:
            search.update({"ipaddr6": ipv6_address})
        if ipv4_address:
            search.update({"ipaddr4": ipv4_address})

        try:
            # Try to get from cached data
            network_ixlan = NetworkIXLAN.objects.get(**search)
        except NetworkIXLAN.DoesNotExist:
            # If no cached data found, query the API
            result = self.lookup(NAMESPACES["network_internet_exchange_lan"], search)

            if not result or not result["data"]:
                return None

            network_ixlan = Object(result["data"][0])

        return network_ixlan

    def get_ix_networks_for_asn(self, asn):
        """
        Returns a list of all IX networks an AS is connected to.
        """
        # Try to get from cached data
        network_ixlans = NetworkIXLAN.objects.filter(asn=asn)

        # If nothing found in cache, try to fetch data online
        if not network_ixlans:
            search = {"asn": asn}
            result = self.lookup(NAMESPACES["network_internet_exchange_lan"], search)

            if not result or not result["data"]:
                return None

            network_ixlans = []
            for ix_network in result["data"]:
                network_ixlans.append(Object(ix_network))

        return network_ixlans

    def get_common_ix_networks_for_asns(self, asn1, asn2):
        """
        Returns a list of all common IX networks on which both ASNs are
        connected to. The list contains tuples of NetworkIXLAN objects. The
        first element of each tuple is the IX LAN network of asn1, the second
        element is the IX LAN network of asn2 matching the one of asn1.
        """
        common_network_ixlans = []

        # Grab IX LANs for both ASNs
        asn1_network_ixlans = self.get_ix_networks_for_asn(asn1)
        asn2_network_ixlans = self.get_ix_networks_for_asn(asn2)

        # If IX for one of the AS cannot be found, return the empty list
        if not asn1_network_ixlans or not asn2_network_ixlans:
            return common_network_ixlans

        # Find IX LAN networks matching
        for asn1_network_ixlan in asn1_network_ixlans:
            for asn2_network_ixlan in asn2_network_ixlans:
                if asn1_network_ixlan.ixlan_id == asn2_network_ixlan.ixlan_id:
                    # Keep track of the two IX LAN networks
                    common_network_ixlans.append(
                        (asn1_network_ixlan, asn2_network_ixlan)
                    )

        return common_network_ixlans

    def get_prefixes_for_ix_network(self, ix_network_id):
        """
        Returns a list of all prefixes used by an IX network.
        """
        prefixes = []

        # Get the NetworkIXLAN object using its ID
        network_ixlan = self.get_ix_network(ix_network_id)

        if network_ixlan:
            # Try to get prefixes from cache
            ix_prefixes = Prefix.objects.filter(ixlan_id=network_ixlan.ixlan_id)

            # If not cached data, try to fetch online
            if not ix_prefixes:
                search = {"ixlan_id": network_ixlan.ixlan_id}
                result = self.lookup(NAMESPACES["internet_exchange_prefix"], search)

                if not result or not result["data"]:
                    return prefixes

                ix_prefixes = []
                for ix_prefix in result["data"]:
                    ix_prefixes.append(Object(ix_prefix))

            # Build a list of prefixes
            for ix_prefix in ix_prefixes:
                prefixes.append(ipaddress.ip_network(ix_prefix.prefix))

        return prefixes
