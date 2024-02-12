from collections import defaultdict

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.core.validators import ValidationError
from django.db import models
from django.db.models.signals import class_prepared
from django.dispatch import receiver
from taggit.managers import TaggableManager

from core.enums import JobStatus
from extras.enums import ObjectChangeAction
from extras.utils import register_features
from utils.functions import merge_hash, serialize_object

from ..registry import registry

__all__ = (
    "ChangeLoggingMixin",
    "ConfigContextMixin",
    "ExportTemplatesMixin",
    "JobsMixin",
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

    def snapshot(self):
        """
        Save a snapshot of the object's current state in preparation for modification.
        """
        self._prechange_snapshot = serialize_object(self)

    def to_objectchange(self, action, related_object=None):
        """
        Return a new `ObjectChange` representing a change made to this object.
        """
        from extras.models import ObjectChange

        object_change = ObjectChange(
            changed_object=self,
            related_object=related_object,
            object_repr=str(self),
            action=action,
        )

        if hasattr(self, "_prechange_snapshot"):
            object_change.prechange_data = self._prechange_snapshot
        if action in (ObjectChangeAction.CREATE, ObjectChangeAction.UPDATE):
            object_change.postchange_data = serialize_object(self)

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
    "tags": TagsMixin,
    "webhooks": WebhooksMixin,
}
registry["model_features"].update(
    {feature: defaultdict(set) for feature in FEATURES_MAP.keys()}
)


@receiver(class_prepared)
def _register_features(sender, **kwargs):
    features = {
        feature for feature, cls in FEATURES_MAP.items() if issubclass(sender, cls)
    }
    register_features(sender, features)
