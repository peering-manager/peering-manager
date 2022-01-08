from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from jinja2 import Environment, TemplateSyntaxError

from peering.models import Template
from peering.models.jinja2 import FILTER_DICT
from utils.models import ChangeLoggedModel, TaggableModel

__all__ = ("ContactRole", "Contact", "ContactAssignment", "Email")


class ContactRole(ChangeLoggedModel, TaggableModel):
    """
    Functional role for a `Contact` assigned to an object.
    """

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("messaging:contactrole_details", args=[self.pk])


class Contact(ChangeLoggedModel, TaggableModel):
    name = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=200, blank=True)
    comments = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("messaging:contact_details", args=[self.pk])


class ContactAssignment(ChangeLoggedModel):
    content_type = models.ForeignKey(to=ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    object = GenericForeignKey(ct_field="content_type", fk_field="object_id")
    contact = models.ForeignKey(
        to="messaging.Contact", on_delete=models.PROTECT, related_name="assignments"
    )
    role = models.ForeignKey(
        to="messaging.ContactRole", on_delete=models.PROTECT, related_name="assignments"
    )

    class Meta:
        ordering = ["contact"]
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_id", "contact", "role"],
                name="contact_per_object",
            )
        ]

    def __str__(self):
        return str(self.contact)


class Email(Template):
    # While a line length should not exceed 78 characters (as per RFC2822), we allow
    # user more characters for templating and let the user to decide what he wants to
    # with this recommended limit, including not respecting it
    subject = models.CharField(max_length=512)

    def get_absolute_url(self):
        return reverse("messaging:email_details", args=[self.pk])

    def render(self, variables):
        """
        Render the template using Jinja2.
        """
        subject, body = "", ""
        environment = Environment(
            trim_blocks=self.jinja2_trim, lstrip_blocks=self.jinja2_lstrip
        )

        # Add custom filters to our environment
        environment.filters.update(FILTER_DICT)

        try:
            jinja2_template = environment.from_string(self.subject)
            subject = jinja2_template.render(variables)
        except TemplateSyntaxError as e:
            subject = (
                f"Syntax error in subject template at line {e.lineno}: {e.message}"
            )
        except Exception as e:
            subject = str(e)

        try:
            jinja2_template = environment.from_string(self.template)
            body = jinja2_template.render(variables)
        except TemplateSyntaxError as e:
            body = f"Syntax error in body template at line {e.lineno}: {e.message}"
        except Exception as e:
            body = str(e)

        return subject, body
