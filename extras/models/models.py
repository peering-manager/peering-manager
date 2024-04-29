import json

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from rest_framework.utils.encoders import JSONEncoder

from peering_manager.jinja2 import render_jinja2
from peering_manager.models import ChangeLoggedModel, SynchronisedDataMixin

from ..conditions import ConditionSet
from ..enums import WEBHOOK_HTTP_CONTENT_TYPE_JSON, HttpMethod
from ..utils import FeatureQuery

__all__ = ("ExportTemplate", "Webhook")


class ExportTemplate(SynchronisedDataMixin, ChangeLoggedModel):
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

    def synchronise_data(self):
        self.template = self.data_file.data_as_string

    def render(self):
        """
        Renders the content of the export template.
        """
        return render_jinja2(
            self.template, {"dataset": self.content_type.model_class().objects.all()}
        )


class Webhook(ChangeLoggedModel):
    """
    A Webhook defines a request that will be sent to a remote HTTP server when an
    object is created, updated, and/or delete. The request will contain a
    representation of the object.
    """

    content_types = models.ManyToManyField(
        to=ContentType,
        related_name="webhooks",
        verbose_name="Object types",
        limit_choices_to=FeatureQuery("webhooks"),
        help_text="The object(s) to which this webhook applies.",
    )
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
    payload_url = models.CharField(
        max_length=512,
        verbose_name="URL",
        help_text="This URL will be called using the HTTP method defined when the webhook is called. Jinja2 template processing is supported with the same context as the request body.",
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
    additional_headers = models.TextField(
        blank=True,
        help_text="User-supplied HTTP headers to be sent with the request in addition to the HTTP content type. Headers should be defined in the format <code>Name: Value</code>. Jinja2 template processing is supported with the same context as the request body (below).",
    )
    body_template = models.TextField(
        blank=True,
        help_text="Jinja2 template for a custom request body. If blank, a JSON object representing the change will be included. Available context data includes: <code>event</code>, <code>model</code>, <code>timestamp</code>, <code>username</code>, <code>request_id</code>, and <code>data</code>.",
    )
    secret = models.CharField(
        max_length=255,
        blank=True,
        help_text="When provided, the request will include a 'X-Hook-Signature' header containing a HMAC hex digest of the payload body using the secret as the key. The secret is not transmitted in the request.",
    )
    conditions = models.JSONField(
        blank=True,
        null=True,
        help_text="A set of conditions which determine whether the webhook will be generated.",
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
        unique_together = ["type_create", "type_update", "type_delete", "payload_url"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("extras:webhook_view", args=[self.pk])

    def clean(self):
        super().clean()

        if not any([self.type_create, self.type_update, self.type_delete]):
            raise ValidationError(
                "At least one event type must be selected: create, update, and/or delete."
            )
        if self.conditions:
            try:
                ConditionSet(self.conditions)
            except ValueError as e:
                raise ValidationError({"conditions": e})
        if not self.ssl_verification and self.ca_file_path:
            raise ValidationError(
                {
                    "ca_file_path": "Do not specify a CA certificate file if SSL verification is disabled."
                }
            )

    def render_headers(self, context):
        """
        Render `additional_headers` and return a dict of `Header: Value`
        pairs.
        """
        if not self.additional_headers:
            return {}

        r = {}
        data = render_jinja2(self.additional_headers, context)
        for line in data.splitlines():
            header, value = line.split(":", 1)
            r[header.strip()] = value.strip()
        return r

    def render_body(self, context):
        """
        Render the body template, if defined. Otherwise, jump the context as a JSON
        object.
        """
        if self.body_template:
            return render_jinja2(self.body_template, context)
        return json.dumps(context, cls=JSONEncoder)

    def render_payload_url(self, context):
        """
        Render the payload URL.
        """
        return render_jinja2(self.payload_url, context)
