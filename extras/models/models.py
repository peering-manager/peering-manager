import json
import traceback

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from jinja2 import Environment, TemplateSyntaxError
from rest_framework.utils.encoders import JSONEncoder

from extras.enums import WEBHOOK_HTTP_CONTENT_TYPE_JSON, HttpMethod
from extras.utils import FeatureQuery
from peering_manager.jinja2 import (
    FILTER_DICT,
    IncludeTemplateExtension,
    PeeringManagerLoader,
)
from peering_manager.models import ChangeLoggedModel

__all__ = ("ExportTemplate", "Webhook")

__all__ = ("ExportTemplate", "Webhook")


class ExportTemplate(ChangeLoggedModel):
    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=FeatureQuery("export-templates"),
    )
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200, blank=True)
    template = models.TextField(
        help_text="Jinja2 template code. The list of objects being exported is passed as a context variable named <code>dataset</code>."
    )
    jinja2_trim = models.BooleanField(
        default=False, help_text="Removes new line after tag"
    )
    jinja2_lstrip = models.BooleanField(
        default=False, help_text="Strips whitespaces before block"
    )

    class Meta:
        ordering = ["content_type", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "name"], name="contenttype_per_name"
            )
        ]

    @property
    def rendered(self):
        return self.render()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("extras:exporttemplate_view", args=[self.pk])

    def clean(self):
        super().clean()

        if self.name.lower() == "table":
            raise ValidationError(
                {
                    "name": f'"{self.name}" is a reserved name. Please choose a different name.'
                }
            )

    def render(self):
        """
        Renders the content of the export template.
        """
        environment = Environment(
            loader=PeeringManagerLoader(),
            trim_blocks=self.jinja2_trim,
            lstrip_blocks=self.jinja2_lstrip,
        )
        environment.add_extension(IncludeTemplateExtension)
        for extension in settings.JINJA2_TEMPLATE_EXTENSIONS:
            environment.add_extension(extension)

        # Add custom filters to our environment
        environment.filters.update(FILTER_DICT)

        # Try rendering the template, return a message about syntax issues if there
        # are any
        try:
            jinja2_template = environment.from_string(self.template)
            return jinja2_template.render(
                dataset=self.content_type.model_class().objects.all()
            )
        except TemplateSyntaxError as e:
            return f"Syntax error in template at line {e.lineno}: {e.message}"
        except Exception:
            return traceback.format_exc()


class Webhook(models.Model):
    """
    A Webhook defines a request that will be sent to a remote HTTP server when an
    object is created, updated, and/or delete. The request will contain a
    representation of the object.
    """

    name = models.CharField(max_length=100, unique=True)
    type_create = models.BooleanField(
        default=False, help_text="Call this webhook when an object is created."
    )
    type_update = models.BooleanField(
        default=False, help_text="Call this webhook when an object is updated."
    )
    type_delete = models.BooleanField(
        default=False, help_text="Call this webhook when an object is deleted."
    )
    url = models.CharField(
        max_length=512,
        verbose_name="URL",
        help_text="A POST will be sent to this URL when the webhook is called.",
    )
    enabled = models.BooleanField(default=True)
    http_method = models.CharField(
        max_length=32,
        choices=HttpMethod,
        default=HttpMethod.POST,
        verbose_name="HTTP method",
    )
    http_content_type = models.CharField(
        max_length=128,
        default=WEBHOOK_HTTP_CONTENT_TYPE_JSON,
        verbose_name="HTTP content type",
        help_text='The complete list of official content types is available <a href="https://www.iana.org/assignments/media-types/media-types.xhtml">here</a>.',
    )
    secret = models.CharField(
        max_length=255,
        blank=True,
        help_text="When provided, the request will include a 'X-Hook-Signature' header containing a HMAC hex digest of the payload body using the secret as the key. The secret is not transmitted in the request.",
    )
    ssl_verification = models.BooleanField(
        default=True,
        verbose_name="SSL verification",
        help_text="Enable SSL certificate verification. Disable with caution!",
    )
    ca_file_path = models.CharField(
        max_length=4096,
        null=True,
        blank=True,
        verbose_name="CA File Path",
        help_text="CA certificate file to use for SSL verification. Leave blank to use the system defaults.",
    )

    class Meta:
        ordering = ["name"]
        unique_together = ["type_create", "type_update", "type_delete", "url"]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()

        if not self.type_create and not self.type_delete and not self.type_update:
            raise ValidationError(
                "You must select at least one type: create, update, and/or delete."
            )
        if not self.ssl_verification and self.ca_file_path:
            raise ValidationError(
                {
                    "ca_file_path": "Do not specify a CA certificate file if SSL verification is disabled."
                }
            )

    def render_body(self, data):
        """
        Renders the data as a JSON object.
        """
        return json.dumps(data, cls=JSONEncoder)
