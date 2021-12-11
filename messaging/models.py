from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse

from utils.models import ChangeLoggedModel, TaggableModel

__all__ = ("ContactRole", "Contact", "ContactAssignment")


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
