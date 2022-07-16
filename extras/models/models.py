import json
import logging
import traceback
import uuid
from collections import OrderedDict

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.urls import reverse
from django.utils import timezone
from jinja2 import Environment, TemplateSyntaxError
from rest_framework.utils.encoders import JSONEncoder

from extras.enums import (
    WEBHOOK_HTTP_CONTENT_TYPE_JSON,
    HttpMethod,
    JobResultStatus,
    LogLevel,
)
from extras.utils import FeatureQuery
from peering_manager.jinja2 import (
    FILTER_DICT,
    IncludeTemplateExtension,
    PeeringManagerLoader,
)
from utils.models import ChangeLoggedMixin


class ExportTemplate(ChangeLoggedMixin):
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

    def __str__(self):
        return f"{self.content_type}: {self.name}"

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


class JobResult(models.Model):
    """
    This model stores the results for a job that has been run in background.
    """

    name = models.CharField(max_length=255)
    obj_type = models.ForeignKey(
        to=ContentType,
        related_name="job_results",
        verbose_name="Object type",
        help_text="The object type to which this job result applies",
        on_delete=models.CASCADE,
    )
    created = models.DateTimeField(auto_now_add=True)
    completed = models.DateTimeField(blank=True, null=True)
    user = models.ForeignKey(
        to=User, on_delete=models.SET_NULL, related_name="+", null=True, blank=True
    )
    status = models.CharField(
        max_length=30, choices=JobResultStatus.choices, default=JobResultStatus.PENDING
    )
    data = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    job_id = models.UUIDField(unique=True)

    class Meta:
        ordering = ["-created"]

    @classmethod
    def enqueue_job(cls, func, name, obj_type, user, *args, **kwargs):
        """
        Creates a JobResult instance and enqueue a job using the given callable.
        """
        job_result = cls.objects.create(
            name=name,
            obj_type=ContentType.objects.get_for_model(obj_type),
            user=user,
            job_id=uuid.uuid4(),
        )

        func.delay(
            *args, job_id=str(job_result.job_id), job_result=job_result, **kwargs
        )

        return job_result

    @staticmethod
    def _data_grouping_struct():
        return OrderedDict(
            [("success", 0), ("info", 0), ("warning", 0), ("failure", 0), ("log", [])]
        )

    @property
    def output(self):
        if not self.data or "output" not in self.data or not self.data["output"]:
            return ""

        lines = []
        for line in self.data["output"]["log"]:
            lines.append(line[-1])

        return "\n".join(lines)

    @property
    def duration(self):
        if not self.completed:
            return ""

        duration = self.completed - self.created
        minutes, seconds = divmod(duration.total_seconds(), 60)

        return f"{int(minutes)} minutes, {seconds:.2f} seconds"

    @property
    def is_over(self):
        return self.status in [
            JobResultStatus.COMPLETED,
            JobResultStatus.ERRORED,
            JobResultStatus.FAILED,
        ]

    def __str__(self):
        return f"Result for job {self.job_id}"

    def get_absolute_url(self):
        return reverse("extras:jobresult_view", args=[self.pk])

    def set_status(self, status):
        """
        Helper method to change the status of the job result. If the target status is
        terminal, the completion time is also set.
        """
        self.status = status
        if status in [
            JobResultStatus.COMPLETED,
            JobResultStatus.ERRORED,
            JobResultStatus.FAILED,
        ]:
            self.completed = timezone.now()

    def log(
        self,
        message,
        obj=None,
        level_choice=LogLevel.DEFAULT,
        grouping="main",
        logger=None,
        save=True,
    ):
        """
        Stores log messages in a JobResult's `data` field.
        """
        if level_choice not in LogLevel.values:
            raise Exception(f"Unknown logging level: {level_choice}")

        if not self.data:
            self.data = {}

        data = self.data
        data.setdefault(grouping, self._data_grouping_struct())
        # Just in case it got initialized by something else:
        if "log" not in data[grouping]:
            data[grouping]["log"] = []
        log = data[grouping]["log"]

        # Record the log message
        log.append(
            [
                timezone.now().isoformat(),
                level_choice,
                str(obj) if obj else None,
                obj.get_absolute_url() if hasattr(obj, "get_absolute_url") else None,
                str(message),
            ]
        )

        # Default log messages have no status and do not get counted
        if level_choice != LogLevel.DEFAULT:
            # Update per-grouping and total results counters
            data[grouping].setdefault(level_choice, 0)
            data[grouping][level_choice] += 1
            if "total" not in data:
                data["total"] = self._data_grouping_struct()
                del data["total"]["log"]
            data["total"].setdefault(level_choice, 0)
            data["total"][level_choice] += 1

        if logger:
            if level_choice == LogLevel.FAILURE:
                log_level = logging.ERROR
            elif level_choice == LogLevel.WARNING:
                log_level = logging.WARNING
            else:
                log_level = logging.INFO
            logger.log(log_level, str(message))

        if save:
            self.save()

    def mark_completed(self, log_message, obj=None, logger=None):
        self.set_status(JobResultStatus.COMPLETED)
        self.log(log_message, obj=obj, level_choice=LogLevel.SUCCESS, logger=logger)

    def mark_errored(self, log_message, obj=None, logger=None):
        self.set_status(JobResultStatus.ERRORED)
        self.log(log_message, obj=obj, level_choice=LogLevel.FAILURE, logger=logger)

    def mark_failed(self, log_message, obj=None, logger=None):
        self.set_status(JobResultStatus.FAILED)
        self.log(log_message, obj=obj, level_choice=LogLevel.FAILURE, logger=logger)

    def mark_running(self, log_message, obj=None, logger=None):
        self.set_status(JobResultStatus.RUNNING)
        self.log(log_message, obj=obj, level_choice=LogLevel.INFO, logger=logger)

    def set_output(self, output, obj=None):
        self.log(
            output,
            obj=obj,
            level_choice=LogLevel.DEFAULT,
            grouping="output",
            save=False,
        )


class Webhook(models.Model):
    """
    A Webhook defines a request that will be sent to a remote HTTP server when an
    object is created, updated, and/or delete. The request will contain a
    representation of the object.
    """

    name = models.CharField(max_length=128, unique=True)
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
        choices=HttpMethod.choices,
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
