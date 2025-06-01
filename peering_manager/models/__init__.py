from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.validators import ValidationError
from django.db import models
from django.urls import reverse

from .features import *

__all__ = (
    "ChangeLoggedModel",
    "OrganisationalModel",
    "PeeringManagerModel",
    "PrimaryModel",
    "TemplateModel",
)


class PeeringManagerFeatureSet(
    ChangeLoggingMixin,
    ConfigContextMixin,
    ExportTemplatesMixin,
    TagsMixin,
    WebhooksMixin,
):
    """
    Peering Manager feature set includes change logging and tags fields.
    """

    class Meta:
        abstract = True

    @property
    def docs_url(self) -> str:
        return f"{settings.STATIC_URL}docs/models/{self._meta.app_label}/{self._meta.model_name}/"

    def get_absolute_url(self) -> str:
        return reverse(
            f"{self._meta.app_label}:{self._meta.model_name}", kwargs={"pk": self.pk}
        )


class ChangeLoggedModel(ChangeLoggingMixin, models.Model):
    """
    Base model for simple models, it provides limited functionality for models which
    don't support Peering Manager's full feature set.
    """

    class Meta:
        abstract = True


class PeeringManagerModel(PeeringManagerFeatureSet, models.Model):
    """
    Base model for most object types.
    """

    class Meta:
        abstract = True

    def clean(self):
        """
        Validate the model for GenericForeignKey fields to ensure that the content type and object ID exist.
        """
        super().clean()

        for field in self._meta.get_fields():
            if isinstance(field, GenericForeignKey):
                ct_value = getattr(self, field.ct_field, None)
                fk_value = getattr(self, field.fk_field, None)

                if ct_value is None and fk_value is not None:
                    raise ValidationError(
                        {field.ct_field: "This field cannot be null."}
                    )
                if fk_value is None and ct_value is not None:
                    raise ValidationError(
                        {field.fk_field: "This field cannot be null."}
                    )

                if ct_value and fk_value:
                    klass = getattr(self, field.ct_field).model_class()
                    if not klass.objects.filter(pk=fk_value).exists():
                        raise ValidationError(
                            {
                                field.fk_field: f"Related object not found using the provided value: {fk_value}."
                            }
                        )


class PrimaryModel(PeeringManagerModel):
    """
    Primary models always have description and comments fields.
    """

    description = models.CharField(max_length=200, blank=True)
    comments = models.TextField(blank=True)

    class Meta:
        abstract = True


class OrganisationalModel(PeeringManagerFeatureSet, models.Model):
    """
    Organisational models provide the following standard attributes:
    - Unique name
    - Unique slug (automatically derived from name)
    - Optional description
    """

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        abstract = True
        ordering = ("name",)

    def __str__(self):
        return self.name


class TemplateModel(PrimaryModel):
    name = models.CharField(max_length=100)
    template = models.TextField()
    jinja2_trim = models.BooleanField(
        default=False, help_text="Removes new line after tag"
    )
    jinja2_lstrip = models.BooleanField(
        default=False, help_text="Strips whitespaces before block"
    )

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self):
        return self.name

    def render(self, variables):
        raise NotImplementedError()
