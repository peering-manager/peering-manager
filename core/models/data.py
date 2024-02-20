import logging
import os
from fnmatch import fnmatchcase
from pathlib import Path
from urllib.parse import urlparse

import yaml
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.module_loading import import_string

from peering_manager.models import JobsMixin, PrimaryModel
from peering_manager.registry import DATA_BACKENDS_KEY, registry
from utils.functions import sha256_hash

from ..enums import DataSourceStatus
from ..exceptions import SynchronisationError
from ..signals import post_synchronisation, pre_synchronisation
from .jobs import Job

logger = logging.getLogger("peering.manager.core.data")

__all__ = ("DataSource", "DataFile")

CENSORSHIP_STRING = "*************"
CENSORSHIP_STRING_CHANGED = "***CHANGED***"


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
            path = path.split(root)[1].lstrip("/")
            if path.startswith("."):
                continue
            for file_name in file_names:
                if not self._ignore(file_name):
                    paths.add(os.path.join(path, file_name))

        logger.debug(f"found {len(paths)} files")
        return paths

    def get_absolute_url(self):
        return reverse("core:datasource_view", args=[self.pk])

    def clean(self):
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

    def to_objectchange(self, action):
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
        else:
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
        if self.status == DataSourceStatus.SYNCHRONISING:
            raise SynchronisationError(
                "Synchronisation already in progress, not starting a new one."
            )

        pre_synchronisation.send(sender=self.__class__, instance=self)

        self.status = DataSourceStatus.SYNCHRONISING
        self.save()

        try:
            backend = self.get_backend()
        except ModuleNotFoundError as e:
            raise SynchronisationError(
                f"Unable to initialise the backend. A dependency needs to be installed: {e}"
            )

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

    @property
    def data_as_string(self):
        if not self.data:
            return None

        try:
            return self.data.decode("utf-8")
        except UnicodeDecodeError:
            return None

    def __str__(self):
        return self.path

    def get_absolute_url(self):
        return reverse("core:datafile_view", args=[self.pk])

    def get_data(self):
        """
        Return a native Python object from either YAML or JSON.
        """
        return yaml.safe_load(self.data_as_string)

    def refresh_from_disk(self, source_root):
        """
        Update attributes of an instance based on the file on disk. If any attribute
        has changed, this function will return `True`.
        """
        file_path = Path(source_root) / self.path
        file_hash = sha256_hash(file_path).hexdigest()

        has_changed = file_path != self.hash
        if has_changed:
            self.updated = timezone.now()
            self.size = file_path.stat().st_size
            self.hash = file_hash
            self.data = file_path.read_bytes()

        return has_changed

    def write_to_disk(self, path, overwrite=False):
        """
        Write data stored in the database for this file into a corresponding file on
        disk.
        """
        file_path = Path(path)

        if file_path.is_file() and not overwrite:
            raise FileExistsError()

        file_path.write_bytes(self.data)
