from collections import defaultdict

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.validators import ValidationError
from django.db import models
from django.db.models.signals import class_prepared
from django.dispatch import receiver
from django.utils import timezone
from taggit.managers import TaggableManager

from core.enums import JobStatus, ObjectChangeAction
from extras.utils import register_features
from utils.functions import merge_hash, serialize_object

from ..registry import registry

__all__ = (
    "ChangeLoggingMixin",
    "ConfigContextMixin",
    "ExportTemplatesMixin",
    "JobsMixin",
    "JournalingMixin",
    "PushedDataMixin",
    "SynchronisedDataMixin",
    "TagsMixin",
    "WebhooksMixin",
)


class ChangeLoggingMixin(models.Model):
    """
    Abstract class providing fields and functions to log changes made to a model.
    """

    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        abstract = True

    @property
    def excluded_fields(self):
        return ["updated", *getattr(self, "changelog_excluded_fields", [])]

    def snapshot(self):
        """
        Save a snapshot of the object's current state in preparation for modification.
        """
        self._prechange_snapshot = serialize_object(self, exclude=self.excluded_fields)

    def to_objectchange(self, action, related_object=None):
        """
        Return a new `ObjectChange` representing a change made to this object.
        """
        from core.models import ObjectChange

        object_change = ObjectChange(
            changed_object=self,
            related_object=related_object,
            object_repr=str(self),
            action=action,
        )

        if hasattr(self, "_prechange_snapshot"):
            object_change.prechange_data = self._prechange_snapshot
        if action in (ObjectChangeAction.CREATE, ObjectChangeAction.UPDATE):
            object_change.postchange_data = serialize_object(
                self, exclude=self.excluded_fields
            )

        return object_change


class ConfigContextMixin(models.Model):
    config_contexts = GenericRelation(to="extras.ConfigContextAssignment")
    local_context_data = models.JSONField(blank=True, null=True)

    class Meta:
        abstract = True

    @property
    def config_context(self):
        """
        Property mostly exposed for templating purposes.
        """
        return self.get_config_context()

    def clean(self):
        super().clean()

        # Verify that JSON data is provided as an object
        if self.local_context_data and not isinstance(self.local_context_data, dict):
            raise ValidationError(
                {
                    "local_context_data": 'JSON data must be in object form. Example: {"foo": 123}'
                }
            )

    def get_config_context(self):
        """
        Merge the config contexts and the local context data all together according to
        the pre-defined merge strategy.
        """
        rendered = {}
        for assignment in self.config_contexts.all():
            rendered = merge_hash(
                rendered,
                assignment.config_context.data,
                **settings.CONFIG_CONTEXT_MERGE_STRATEGY,
            )

        if not self.local_context_data and not rendered:
            # Always return a null value instead of empty dict
            return None
        if not self.local_context_data:
            return rendered
        if not rendered:
            return self.local_context_data

        return merge_hash(
            rendered, self.local_context_data, **settings.CONFIG_CONTEXT_MERGE_STRATEGY
        )


class ExportTemplatesMixin(models.Model):
    """
    Enables support for export templates.
    """

    class Meta:
        abstract = True


class JobsMixin(models.Model):
    """
    Enables support for jobs.
    """

    jobs = GenericRelation(
        to="core.Job",
        content_type_field="object_type",
        object_id_field="object_id",
        for_concrete_model=False,
    )

    class Meta:
        abstract = True

    def get_latest_jobs(self):
        """
        Return a dictionary mapping of the most recent jobs for this instance.
        """
        return {
            job.name: job
            for job in self.jobs.filter(status__in=JobStatus.TERMINAL_STATE_CHOICES)
            .order_by("name", "-created")
            .distinct("name")
            .defer("data")
        }


class JournalingMixin(models.Model):
    """
    Enables support for object journaling. Adds a generic relation
    `journal_entries` pointing to `JournalEntry` model.
    """

    journal_entries = GenericRelation(
        to="extras.JournalEntry",
        object_id_field="assigned_object_id",
        content_type_field="assigned_object_type",
    )

    class Meta:
        abstract = True


class PushedDataMixin(models.Model):
    data_source = models.ForeignKey(
        to="core.DataSource",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="+",
        help_text="Remote data source",
    )
    data_file = models.ForeignKey(
        to="core.DataFile",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
        editable=False,
    )
    data_path = models.CharField(
        max_length=1000,
        blank=True,
        null=True,
        help_text="Path to the remote file, relative to its data source root",
    )
    data_pushed = models.DateTimeField(blank=True, null=True, editable=False)

    class Meta:
        abstract = True

    @property
    def is_pushed(self):
        return self.data_file and self.data_pushed >= self.data_file.updated

    def clean(self, *args, **kwargs):
        if not self.data_source:
            self.data_source = None
            self.data_path = ""
            self.data_pushed = None

        super().clean()

    def resolve_data_file(self):
        """
        Determine the designated `DataFile` object identified by its parent
        `DataSource` and its path, create it if it does not exist. Return `None` if
        either attribute is unset.
        """
        from core.models import DataFile

        if self.data_source and self.data_path:
            try:
                return DataFile.objects.get(
                    source=self.data_source, path=self.data_path
                )
            except DataFile.DoesNotExist:
                pass
        return None

    def push_data(self):
        """
        Inheriting models must override this method with specific logic to copy data
        from the assigned `DataFile` to the local instance. This method should *NOT*
        call `save()` on the instance.
        """
        raise NotImplementedError()

    def push(self, save=False):
        """
        Push the object from it's assigned `DataFile` (if any). This wraps
        `push_data()` and updates the `data_pushed` timestamp.
        """
        self.push_data()
        self.data_pushed = timezone.now()

        data_file = self.resolve_data_file()
        if self.data_file != data_file:
            self.data_file = data_file

        if save:
            self.save()


class SynchronisedDataMixin(models.Model):
    data_source = models.ForeignKey(
        to="core.DataSource",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="+",
        help_text="Remote data source",
    )
    data_file = models.ForeignKey(
        to="core.DataFile",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
    )
    data_path = models.CharField(
        max_length=1000,
        blank=True,
        editable=False,
        help_text="Path to the remote file, relative to its data source root",
    )
    auto_synchronisation_enabled = models.BooleanField(
        default=True,
        help_text="Enable automatic synchronisation of data when the data file is updated",
    )
    data_synchronised = models.DateTimeField(blank=True, null=True, editable=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        from core.models import AutoSynchronisationRecord

        r = super().save(*args, **kwargs)

        content_type = ContentType.objects.get_for_model(self)
        if self.auto_synchronisation_enabled and self.data_file:
            AutoSynchronisationRecord.objects.update_or_create(
                object_type=content_type,
                object_id=self.pk,
                defaults={"data_file": self.data_file},
            )
        else:
            AutoSynchronisationRecord.objects.filter(
                data_file=self.data_file, object_type=content_type, object_id=self.pk
            ).delete()

        return r

    @property
    def is_synchronised(self):
        return self.data_file and self.data_synchronised >= self.data_file.updated

    def clean(self, *args, **kwargs):
        if self.data_file:
            self.data_source = self.data_file.source
            self.data_path = self.data_file.path
            self.synchronise()
        else:
            self.data_source = None
            self.data_path = ""
            self.auto_synchronisation_enabled = False
            self.data_synchronised = None

        super().clean()

    def delete(self, *args, **kwargs):
        from core.models import AutoSynchronisationRecord

        content_type = ContentType.objects.get_for_model(self)
        AutoSynchronisationRecord.objects.filter(
            data_file=self.data_file, object_type=content_type, object_id=self.pk
        ).delete()

        return super().delete(*args, **kwargs)

    def resolve_data_file(self):
        """
        Determine the designated `DataFile` object identified by its parent
        `DataSource` and its path. Returns `None` if either attribute is unset, or if
        no matching `DataFile` is found.
        """
        from core.models import DataFile

        if self.data_source and self.data_path:
            try:
                return DataFile.objects.get(
                    source=self.data_source, path=self.data_path
                )
            except DataFile.DoesNotExist:
                pass

        return None

    def synchronise_data(self):
        """
        Inheriting models must override this method with specific logic to copy data
        from the assigned `DataFile` to the local instance. This method should *NOT*
        call `save()` on the instance.
        """
        raise NotImplementedError()

    def synchronise(self, save=False):
        """
        Synchronize the object from it's assigned `DataFile` (if any). This wraps
        `synchronise_data()` and updates the `data_synchronised` timestamp.
        """
        self.synchronise_data()
        self.data_synchronised = timezone.now()
        if save:
            self.save()


class TagsMixin(models.Model):
    """
    Abstract class that just provides tags to its subclasses.
    """

    tags = TaggableManager(through="extras.TaggedItem")

    class Meta:
        abstract = True


class WebhooksMixin(models.Model):
    """
    Enable support for webhooks.
    """

    class Meta:
        abstract = True


FEATURES_MAP = {
    "config-contexts": ConfigContextMixin,
    "export-templates": ExportTemplatesMixin,
    "jobs": JobsMixin,
    "journaling": JournalingMixin,
    "tags": TagsMixin,
    "synchronised_data": SynchronisedDataMixin,
    "webhooks": WebhooksMixin,
}
registry["model_features"].update(
    {feature: defaultdict(set) for feature in FEATURES_MAP}
)


@receiver(class_prepared)
def _register_features(sender, **kwargs):
    features = {
        feature for feature, cls in FEATURES_MAP.items() if issubclass(sender, cls)
    }
    register_features(sender, features)
