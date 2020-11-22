import json

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.serializers import serialize
from django.db import models
from django.db.models.fields.related import ForeignKey, ManyToManyField
from django.urls import reverse
from django.utils.safestring import mark_safe
from taggit.managers import TaggableManager
from taggit.models import GenericTaggedItemBase, TagBase

from .enums import ObjectChangeAction
from .fields import ColorField
from .functions import serialize_object
from .templatetags.helpers import title_with_uppers


class ChangeLoggedModel(models.Model):
    """
    Abstract class providing fields and functions to log changes made to a model.
    """

    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        abstract = True

    def get_change(self, action):
        """
        Returns a new ObjectChange representing a change made to this object.
        """
        return ObjectChange(
            changed_object=self,
            action=action,
            object_repr=str(self),
            object_data=serialize_object(self),
        )


class ObjectChange(models.Model):
    """
    Records a change done to an object and the user who did it.
    """

    time = models.DateTimeField(auto_now_add=True, editable=False)
    user = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        related_name="changes",
        blank=True,
        null=True,
    )
    user_name = models.CharField(max_length=150, editable=False)
    request_id = models.UUIDField(editable=False)
    action = models.PositiveSmallIntegerField(choices=ObjectChangeAction.choices)
    changed_object_type = models.ForeignKey(
        to=ContentType, on_delete=models.PROTECT, related_name="+"
    )
    changed_object_id = models.PositiveIntegerField()
    changed_object = GenericForeignKey(
        ct_field="changed_object_type", fk_field="changed_object_id"
    )
    related_object_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.PROTECT,
        related_name="+",
        blank=True,
        null=True,
    )
    related_object_id = models.PositiveIntegerField(blank=True, null=True)
    related_object = GenericForeignKey(
        ct_field="related_object_type", fk_field="related_object_id"
    )
    object_repr = models.CharField(max_length=256, editable=False)
    object_data = models.JSONField(editable=False)

    class Meta:
        ordering = ["-time"]

    def save(self, *args, **kwargs):
        self.user_name = self.user.username
        self.object_repr = str(self.changed_object)

        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("utils:objectchange_details", kwargs={"pk": self.pk})

    def get_html_icon(self):
        if self.action == ObjectChangeAction.CREATE:
            return mark_safe('<i class="fas fa-plus-square text-success"></i>')
        if self.action == ObjectChangeAction.UPDATE:
            return mark_safe('<i class="fas fa-pen-square text-warning"></i>')
        if self.action == ObjectChangeAction.DELETE:
            return mark_safe('<i class="fas fa-minus-square text-danger"></i>')
        return mark_safe('<i class="fas fa-question-circle text-secondary"></i>')

    def __str__(self):
        return "{} {} {} by {}".format(
            title_with_uppers(self.changed_object_type),
            self.object_repr,
            self.get_action_display().lower(),
            self.user_name,
        )


class Tag(TagBase, ChangeLoggedModel):
    color = ColorField(default="9e9e9e")
    comments = models.TextField(blank=True, default="")

    def get_absolute_url(self):
        return reverse("utils:tag_details", kwargs={"slug": self.slug})


class TaggedItem(GenericTaggedItemBase):
    tag = models.ForeignKey(
        to=Tag, related_name="%(app_label)s_%(class)s_items", on_delete=models.CASCADE
    )

    class Meta:
        index_together = ("content_type", "object_id")


class TaggableModel(models.Model):
    """
    Abstract class that just provides tags to its subclasses.
    """

    tags = TaggableManager(through=TaggedItem)

    class Meta:
        abstract = True


class TemplateModel(models.Model):
    """
    Abstract class providing functions to be used in templates.
    """

    class Meta:
        abstract = True

    def to_dict(self):
        data = {}

        # Iterate over croncrete and many-to-many fields
        for field in self._meta.concrete_fields + self._meta.many_to_many:
            value = None

            # If the value of the field is another model, fetch an instance of it
            # Exception made of tags for which we just retrieve the list of them for later
            # conversion to simple strings
            if isinstance(field, ForeignKey):
                value = self.__getattribute__(field.name)
            elif isinstance(field, ManyToManyField):
                value = list(self.__getattribute__(field.name).all())
            elif isinstance(field, TaggableManager):
                value = list(self.__getattribute__(field.name).all())
            else:
                value = self.__getattribute__(field.name)

            # If the instance of a model as a to_dict() function, call it
            if isinstance(value, TemplateModel):
                data[field.name] = value.to_dict()
            elif isinstance(value, list):
                data[field.name] = []
                for element in value:
                    if isinstance(element, TemplateModel):
                        data[field.name].append(element.to_dict())
                    else:
                        data[field.name].append(str(element))
            else:
                data[field.name] = value

        return data
