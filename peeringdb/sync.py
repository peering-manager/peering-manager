import logging

import requests
from cacheops import invalidate_model
from django.conf import settings
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import transaction
from django.db.utils import DEFAULT_DB_ALIAS
from django.utils import timezone

from net.models import Connection
from peering.models import InternetExchange as IXP
from utils.enums import ObjectChangeAction

from .models import (
    Facility,
    InternetExchange,
    InternetExchangeFacility,
    IXLan,
    IXLanPrefix,
    Network,
    NetworkContact,
    NetworkFacility,
    NetworkIXLan,
    Organization,
    Synchronization,
)

# Order matters for caching data locally
NAMESPACES = {
    "org": Organization,
    "fac": Facility,
    "net": Network,
    "ix": InternetExchange,
    "ixfac": InternetExchangeFacility,
    "ixlan": IXLan,
    "ixpfx": IXLanPrefix,
    "netfac": NetworkFacility,
    "netixlan": NetworkIXLan,
    "poc": NetworkContact,
}

logger = logging.getLogger("peering.manager.peeringdb")


class PeeringDB(object):
    """
    Class used to interact with the PeeringDB API.
    """

    def lookup(self, namespace, search):
        """
        Sends a get request to the API given a namespace and some parameters.
        """
        # Enforce trailing slash and add namespace
        api_url = f"{settings.PEERINGDB_API.strip('/')}/{namespace}"

        # Check if the depth param is provided, add it if not
        if "depth" not in search:
            search["depth"] = 1

        # Authenticate with API Key if present
        q = {"params": search}

        if settings.PEERINGDB_API_KEY:
            q["headers"] = {"AUTHORIZATION": f"Api-Key {settings.PEERINGDB_API_KEY}"}
        # To be removed in v2.0
        elif settings.PEERINGDB_USERNAME:
            logger.warning(
                "PeeringDB authentication with username/password is deprecated and will be removed in v2.0. Please use an API key instead."
            )
            q["auth"] = (settings.PEERINGDB_USERNAME, settings.PEERINGDB_PASSWORD)

        # Make the request
        logger.debug(f"calling api: {api_url} | {search}")
        response = requests.get(api_url, **q)

        return response.json() if response.status_code == 200 else None

    def record_last_sync(self, time, changes):
        """
        Saves the last synchronization details (number of objects and time) for later
        use (and logs).
        """
        last_sync = None
        changes_number = changes["created"] + changes["updated"] + changes["deleted"]

        # Save the last sync time only if objects were retrieved
        if changes_number > 0:
            values = {
                "time": time,
                "created": changes["created"],
                "updated": changes["updated"],
                "deleted": changes["deleted"],
            }

            last_sync = Synchronization(**values)
            last_sync.save()

            logger.debug(f"synchronized {changes_number} objects at {last_sync.time}")

        return last_sync

    def get_last_synchronization(self):
        """
        Returns the last recorded synchronization.
        """
        try:
            return Synchronization.objects.latest("time")
        except Synchronization.DoesNotExist:
            pass

        return None

    def get_last_sync_time(self):
        """
        Returns the last synchronization time based on the latest record.
        The time is returned as a UNIX timestamp.
        """
        # Assume first sync
        last_sync_time = 0
        last_sync = self.get_last_synchronization()

        if last_sync:
            last_sync_time = last_sync.time.timestamp()

        return int(last_sync_time)

    def _process_field(self, model, foreign_keys, obj, name, value):
        """
        Sets the value for a single field of an object.
        """
        # Fields not to process
        if name in ["created", "updated", "status"] or (
            hasattr(obj, "ignored_fields") and name in model.ignored_fields
        ):
            return

        stop_processing = False
        # If the field looks like one of the FK
        for f in foreign_keys:
            if f in name:
                # The field is the FK ID so set it
                if name == f"{f}_id":
                    setattr(obj, name, value)
                # If the field starts with a foreign key name but is not
                # suffixed by _id, just ignore it (it can be its name or
                # something else)
                stop_processing = True

        if stop_processing:
            return

        try:
            # Latitude and longitude are special decimal values that must be
            # casted to string before using them
            if name in ["latitude", "longitude"] and value is not None:
                value = str(value)

            setattr(obj, name, value)
        except FieldDoesNotExist:
            logger.error(
                f"field: {name} not in model: {model._meta.verbose_name.lower()}"
            )

    def _process_object(self, model, data):
        """
        Synchronizes a single object.
        """
        action = (
            ObjectChangeAction.DELETE
            if "deleted" == data["status"]
            else ObjectChangeAction.UPDATE
        )

        try:
            # Get the local object by its ID
            local_object = model.objects.get(pk=data["id"])

            # Object marked as deleted so remove it locally too
            if action == ObjectChangeAction.DELETE:
                logger.debug(
                    f"deleted {model._meta.verbose_name.lower()} #{local_object.pk} from local database"
                )
                local_object.delete()
                return None, action
        except model.DoesNotExist:
            action = ObjectChangeAction.CREATE
            local_object = model()

        # Make a list of foreign key field names
        fk = [
            f.name
            for f in model._meta.get_fields()
            if f.get_internal_type() == "ForeignKey"
        ]

        # Set the value for each field
        for field_name, field_value in data.items():
            self._process_field(model, fk, local_object, field_name, field_value)

        return local_object, action

    def _fix_related_objects(self):
        """
        Fixes main connections and IXPs objects linking them with PeeringDB's if
        possible.
        """
        for c in Connection.objects.all():
            c.link_to_peeringdb()
        for i in IXP.objects.all():
            i.link_to_peeringdb()

    def synchronize_objects(self, last_sync, namespace, model):
        """
        Synchronizes all the objects of a namespace of the PeeringDB to the
        local database. This function is meant to be run regularly to update
        the local database with the latest changes.

        If the object already exists locally it will be updated and no new
        entry will be created.

        If the object is marked as deleted in the PeeringDB, it will be deleted
        locally as well.

        This function returns the number of objects that have been successfully
        synchronized to the local database.
        """
        created, updated, deleted = 0, 0, 0

        # Get all network changes since the last sync
        search = {"since": last_sync, "depth": 0}
        result = self.lookup(namespace, search)

        if not result:
            return (created, updated, deleted)

        for data in result["data"]:
            try:
                local_object, action = self._process_object(model, data)

                if action != ObjectChangeAction.DELETE:
                    # Save the local object
                    local_object.full_clean()
                    local_object.save()
            except ValidationError as e:
                logger.error(
                    f"error validating id: {local_object.id} for model: {model._meta.verbose_name.lower()}\n{e}"
                )
                continue

            # Update counters
            if action == ObjectChangeAction.CREATE:
                created += 1
                logger.debug(
                    f"created {model._meta.verbose_name.lower()} #{local_object.pk} from peeringdb"
                )
            elif action == ObjectChangeAction.UPDATE:
                updated += 1
                logger.debug(
                    f"updated {model._meta.verbose_name.lower()} #{local_object.pk} from peeringdb"
                )
            else:
                deleted += 1

        self._fix_related_objects()

        return (created, updated, deleted)

    def update_local_database(self, last_sync):
        """
        Updates the local database by synchronizing all PeeringDB API's namespaces
        that we are caring about.
        """
        # Set time of sync
        time_of_sync = timezone.now()
        list_of_changes = []

        # Make a single transaction, avoid too much database commits (poor
        # speed) and fail the whole synchronization if something goes wrong
        with transaction.atomic():
            # Try to sync objects
            for namespace, object_type in NAMESPACES.items():
                changes = self.synchronize_objects(last_sync, namespace, object_type)
                list_of_changes.append(changes)

        objects_changes = {
            "created": sum(created for created, _, _ in list_of_changes),
            "updated": sum(updated for _, updated, _ in list_of_changes),
            "deleted": sum(deleted for _, _, deleted in list_of_changes),
        }

        # Save the last sync time
        return self.record_last_sync(time_of_sync, objects_changes)

    def clear_local_database(self):
        """
        Deletes all data related to the local database. This can be used to get a
        fresh start.
        """
        # Unlink main objects from PeeringDB's before emptying the local database
        Connection.objects.filter(peeringdb_netixlan__isnull=False).update(
            peeringdb_netixlan=None
        )
        IXP.objects.filter(peeringdb_ixlan__isnull=False).update(peeringdb_ixlan=None)

        # The use of reversed is important to avoid fk issues
        for model in reversed(list(NAMESPACES.values())):
            model.objects.all()._raw_delete(using=DEFAULT_DB_ALIAS)
            invalidate_model(model)
        Synchronization.objects.all()._raw_delete(using=DEFAULT_DB_ALIAS)
        invalidate_model(Synchronization)
