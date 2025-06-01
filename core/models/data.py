from __future__ import annotations

import logging
import os
from fnmatch import fnmatchcase
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import yaml
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.module_loading import import_string

from peering_manager.models import JobsMixin, PrimaryModel
from peering_manager.registry import DATA_BACKENDS_KEY, registry
from utils.functions import sha256_hash

from ..constants import CENSORSHIP_STRING, CENSORSHIP_STRING_CHANGED
from ..enums import DataSourceStatus
from ..exceptions import SynchronisationError
from ..signals import post_synchronisation, pre_synchronisation
from .jobs import Job

if TYPE_CHECKING:
    from core.models import ObjectChange

logger = logging.getLogger("peering.manager.core.data")

__all__ = ("AutoSynchronisationRecord", "DataFile", "DataSource")


class DataSource(PrimaryModel, JobsMixin):
    """
    A remote source of data, such as a git repository, which will synchronise
    `DataFile`s.
    """

    name = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=50)
    source_url = models.CharField(max_length=200, verbose_name="URL")
    status = models.CharField(
        max_length=50,
        choices=DataSourceStatus,
        default=DataSourceStatus.NEW,
        editable=False,
    )
    enabled = models.BooleanField(default=True)
    ignore_rules = models.TextField(
        blank=True,
        help_text="Patterns (one per line) matching files to ignore when synchronising",
    )
    parameters = models.JSONField(blank=True, null=True)
    last_synchronised = models.DateTimeField(blank=True, null=True, editable=False)

    class Meta:
        ordering = ["name"]
        permissions = [("synchronise_datasource", "Can synchronise data source")]

    @property
    def backend_class(self):
        return registry[DATA_BACKENDS_KEY].get(self.type)

    @property
    def url_scheme(self):
        return urlparse(self.source_url).scheme.lower()

    @property
    def ready_for_synchronisation(self):
        return self.enabled and self.status not in (
            DataSourceStatus.QUEUED,
            DataSourceStatus.SYNCHRONISING,
        )

    @property
    def ready_for_push(self):
        return self.enabled and self.status not in (
            DataSourceStatus.QUEUED,
            DataSourceStatus.PUSHING,
        )

    def __str__(self):
        return self.name

    def _ignore(self, filename):
        if filename.startswith("."):
            return True
        for rule in self.ignore_rules.splitlines():
            if fnmatchcase(filename, rule):
                return True
        return False

    def _walk(self, root):
        logger.debug(f"walking {root}...")

        paths = set()

        for path, _, file_names in os.walk(root):
            p = path.split(root)[1].lstrip("/")
            if p.startswith("."):
                continue
            for file_name in file_names:
                if not self._ignore(file_name):
                    paths.add(str(Path(p, file_name)))

        logger.debug(f"found {len(paths)} files")
        return paths

    def clean(self) -> None:
        super().clean()

        # Make sure the data backend type is supported
        if self.type and self.type not in registry[DATA_BACKENDS_KEY]:
            raise ValidationError({"type": f"Unknown backend type: {self.type}"})

        # Ensure URL scheme matches the selected backend type
        if self.backend_class.is_local and self.url_scheme not in ("file", ""):
            raise ValidationError(
                {
                    "source_url": "URLs for local sources must start with file:// (or should not have one)"
                }
            )

    def to_objectchange(self, action) -> ObjectChange:
        object_change = super().to_objectchange(action)

        pre_change_params = {}
        post_change_params = {}

        if object_change.prechange_data:
            pre_change_params = object_change.prechange_data.get("parameters") or {}
        if object_change.postchange_data:
            post_change_params = object_change.postchange_data.get("parameters") or {}
        for param in self.backend_class.sensitive_parameters:
            if post_change_params.get(param):
                if post_change_params[param] != pre_change_params.get(param):
                    post_change_params[param] = CENSORSHIP_STRING_CHANGED
                else:
                    post_change_params[param] = CENSORSHIP_STRING
            if pre_change_params.get(param):
                pre_change_params[param] = CENSORSHIP_STRING

        return object_change

    def get_type_display(self):
        backend = registry[DATA_BACKENDS_KEY].get(self.type)
        if backend:
            return backend.label
        return None

    def get_status_colour(self):
        return DataSourceStatus.colours.get(self.status)

    def enqueue_synchronisation_job(self, request):
        """
        Enqueue a background job to synchronise files for this source.

        The job will eventually end up calling `synchronise()`.
        """
        self.status = DataSourceStatus.QUEUED
        self.save()

        return Job.enqueue(
            import_string("core.jobs.synchronise_datasource"),
            self,
            name="core.datasource.synchronisation",
            object=self,
            user=request.user,
        )

    def get_backend(self):
        parameters = self.parameters or {}
        return self.backend_class(self.source_url, **parameters)

    def synchronise(self):
        """
        Perform `DataFile` creation/update/deletion according to the synchronisation
        process.
        """
        if not self.enabled:
            raise SynchronisationError(
                "Data source if disabled, synchronisation aborted."
            )
        if self.status == DataSourceStatus.SYNCHRONISING:
            raise SynchronisationError(
                "Synchronisation already in progress, not starting a new one."
            )
        if self.status == DataSourceStatus.PUSHING:
            raise SynchronisationError(
                "Push in progress, not starting a new synchronisation."
            )

        pre_synchronisation.send(sender=self.__class__, instance=self)

        self.status = DataSourceStatus.SYNCHRONISING
        self.save()

        try:
            backend = self.get_backend()
        except ModuleNotFoundError as e:
            raise SynchronisationError(
                f"Unable to initialise the backend. A dependency needs to be installed: {e}"
            ) from e

        with backend.fetch() as local_path:
            logger.debug(f"synchronising files from source root {local_path}")

            data_files = self.datafiles.all()
            known_paths = {df.path for df in data_files}
            logger.debug(f"source has already {len(known_paths)} files")

            changed_files = []
            deleted_file_ids = []

            # Update files and detect deleted ones
            for data_file in data_files:
                try:
                    if data_file.refresh_from_disk(source_root=local_path):
                        changed_files.append(data_file)
                except FileNotFoundError:
                    deleted_file_ids.append(data_file.pk)
                    continue

            # Update changed files
            changed_count = DataFile.objects.bulk_update(
                changed_files, ("updated", "size", "hash", "data")
            )
            logger.debug(f"changed {changed_count} files")
            # Delete files marked for deletion
            deleted_count = DataFile.objects.filter(pk__in=deleted_file_ids).delete()
            logger.debug(f"deleted {deleted_count} files")

            # Find new files locally
            new_paths = self._walk(local_path) - known_paths
            new_data_files = []
            for path in new_paths:
                data_file = DataFile(source=self, path=path)
                data_file.refresh_from_disk(source_root=local_path)
                data_file.full_clean()
                new_data_files.append(data_file)

            created_count = len(
                DataFile.objects.bulk_create(new_data_files, batch_size=100)
            )
            logger.debug(f"created {created_count} files")

        self.status = DataSourceStatus.COMPLETED
        self.last_synchronised = timezone.now()
        self.save()

        post_synchronisation.send(sender=self.__class__, instance=self)

    def push(self, file_path, content: str):
        """
        Push a file to a data source given its file path and content.
        """
        if not self.enabled:
            raise SynchronisationError("Data source if disabled, push aborted.")
        if self.status == DataSourceStatus.SYNCHRONISING:
            raise SynchronisationError(
                "Synchronisation in progress, not starting a new push."
            )
        if self.status == DataSourceStatus.PUSHING:
            raise SynchronisationError(
                "Pushing already in progress, not starting a new one."
            )

        self.status = DataSourceStatus.PUSHING
        self.save()

        try:
            backend = self.get_backend()
        except ModuleNotFoundError as e:
            raise SynchronisationError(
                f"Unable to initialise the backend. A dependency needs to be installed: {e}"
            ) from e

        with backend.push(file_path) as local_path:
            logger.debug(f"pushing {file_path} to {local_path}")

            try:
                data_file = self.datafiles.get(path=file_path)
            except DataFile.DoesNotExist:
                logger.debug(f"creating new file {file_path} to {local_path}")
                data_file = DataFile(source=self, path=file_path)

            data_file.data = content.encode()
            data_file.updated = timezone.now()
            data_file.write_to_disk(source_root=local_path, overwrite=True)
            data_file.refresh_from_disk(source_root=local_path)
            data_file.save()

            logger.debug(f"{file_path} written to {local_path}")

        self.status = DataSourceStatus.COMPLETED
        self.last_synchronised = timezone.now()
        self.save()


class DataFile(models.Model):
    """
    A database representation of a file fetched from a `DataSource`. Instances of this
    class should only be managed by the `DataSource.synchronise()` function.
    """

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(editable=False)
    source = models.ForeignKey(
        to="core.DataSource",
        on_delete=models.CASCADE,
        related_name="datafiles",
        editable=False,
    )
    path = models.CharField(
        max_length=1000,
        editable=False,
        help_text="File path relative to the data source's root",
    )
    size = models.PositiveIntegerField(editable=False)
    hash = models.CharField(
        max_length=64,
        editable=False,
        validators=[
            RegexValidator(
                regex=r"^[0-9a-f]{64}$",
                message="It must be composed of 64 hexadecimal characters.",
            )
        ],
        help_text="SHA256 hash of the file data",
    )
    data = models.BinaryField()

    class Meta:
        ordering = ["source", "path"]
        constraints = [
            models.UniqueConstraint(
                fields=("source", "path"),
                name="%(app_label)s_%(class)s_unique_source_path",
            )
        ]

    def __str__(self) -> str:
        return self.path

    def get_absolute_url(self) -> str:
        return reverse("core:datafile", args=[self.pk])

    @property
    def data_as_string(self) -> str | None:
        if not self.data:
            return None

        try:
            return self.data.decode("utf-8")
        except UnicodeDecodeError:
            return None

    def get_data(self) -> Any:
        """
        Return a native Python object from either YAML or JSON.
        """
        return yaml.safe_load(self.data_as_string)

    def refresh_from_disk(self, source_root) -> bool:
        """
        Update attributes of an instance based on the file on disk. If any attribute
        has changed, this function will return `True`.
        """
        file_path = Path(source_root) / self.path
        file_hash = sha256_hash(file_path).hexdigest()

        has_changed = file_hash != self.hash
        if has_changed:
            self.updated = timezone.now()
            self.size = file_path.stat().st_size
            self.hash = file_hash
            self.data = file_path.read_bytes()

        return has_changed

    def write_to_disk(self, source_root, overwrite=False) -> None:
        """
        Write data stored in the database for this file into a corresponding file on
        disk.
        """
        file_path = Path(source_root) / self.path

        if file_path.is_file() and not overwrite:
            raise FileExistsError()

        file_path.write_bytes(self.data)


class AutoSynchronisationRecord(models.Model):
    """
    Map a `DataFile` to a synchronised object to update it automatically.
    """

    data_file = models.ForeignKey(
        to="DataFile", on_delete=models.CASCADE, related_name="+"
    )
    object_type = models.ForeignKey(
        to="contenttypes.ContentType", on_delete=models.CASCADE, related_name="+"
    )
    object_id = models.PositiveBigIntegerField()
    object = GenericForeignKey(ct_field="object_type", fk_field="object_id")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("object_type", "object_id"),
                name="%(app_label)s_%(class)s_object",
            ),
        ]

    def __str__(self) -> str:
        return f"Auto synchronisation of {self.data_file!s} for {self.object!s}"
