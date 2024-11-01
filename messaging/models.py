from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse

from peering_manager.jinja2 import render_jinja2
from peering_manager.models import (
    ChangeLoggedModel,
    OrganisationalModel,
    PrimaryModel,
    SynchronisedDataMixin,
    TemplateModel,
)

__all__ = ("ContactRole", "Contact", "ContactAssignment", "Email")


class ContactRole(OrganisationalModel):
    """
    Functional role for a `Contact` assigned to an object.
    """

    def get_absolute_url(self):
        return reverse("messaging:contactrole_view", args=[self.pk])


class Contact(PrimaryModel):
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("messaging:contact_view", args=[self.pk])


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


class Email(SynchronisedDataMixin, TemplateModel):
    # While a line length should not exceed 78 characters (as per RFC2822), we allow
    # user more characters for templating and let the user to decide what he wants to
    # with this recommended limit, including not respecting it
    subject = models.CharField(max_length=512)

    def get_absolute_url(self):
        return reverse("messaging:email_view", args=[self.pk])

    def synchronise_data(self):
        self.template = self.data_file.data_as_string

    def render(self, variables):
        """
        Render the template using Jinja2.
        """
        subject = render_jinja2(
            self.subject, variables, trim=self.jinja2_trim, lstrip=self.jinja2_lstrip
        )
        body = render_jinja2(
            self.template, variables, trim=self.jinja2_trim, lstrip=self.jinja2_lstrip
        )

        return subject, body
