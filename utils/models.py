import json
import inspect
import datetime
import pytz

from django.conf import settings
from django.db import models
from django.db.models.fields.related import ForeignKey, ManyToManyField
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.serializers import serialize
from django.urls import reverse
from django.utils.safestring import mark_safe

from taggit.managers import TaggableManager, _TaggableManager
from taggit.models import TagBase, GenericTaggedItemBase

from safedelete.queryset import SafeDeleteQueryset
from safedelete.models import (
    SafeDeleteModel,
    SOFT_DELETE,
    SOFT_DELETE_CASCADE,
    HARD_DELETE,
)

from .enums import ObjectChangeAction
from .fields import ColorField
from .templatetags.helpers import title_with_uppers


class ChangeLoggedModel(models.Model):
    """
    Abstract class providing fields and functions to log changes made to a model.
    """

    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        abstract = True

    def serialize(self):
        """
        Returns a JSON representation of an object using Django's built-in serializer.
        """
        return json.loads(serialize("json", [self]))[0]["fields"]

    def log_change(self, user, request_id, action):
        """
        Creates a new ObjectChange representing a change made to this object.
        """
        ObjectChange(
            user=user,
            request_id=request_id,
            changed_object=self,
            action=action,
            object_data=self.serialize(),
        ).save()


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
                # Hack to deal with Template Preview
                if not isinstance(self.__getattribute__(field.name), _TaggableManager):
                    value = list(self.__getattribute__(field.name))
                else:
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


class SoftDeleteModel(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE

    class Meta:
        abstract = True

    @classmethod
    def _get_models_from_module(cls, module):
        return [
            x[1]
            for x in inspect.getmembers(module, inspect.isclass)
            if issubclass(x[1], cls) and not x[1]._meta.abstract
        ]

    @classmethod
    def get_deleted_counts(cls, module):
        return {
            model._meta.verbose_name: model.deleted_objects.count()
            for model in cls._get_models_from_module(module)
        }

    @classmethod
    def purge_deleted(cls, module, age=0):
        now = datetime.datetime.now(tz=pytz.timezone(settings.TIME_ZONE))
        expiry_date = now - datetime.timedelta()

        deleted = {}
        total = 0
        for model in cls._get_models_from_module(module):
            count, deleted_count = model.deleted_objects.filter(
                deleted__lte=expiry_date
            ).delete(HARD_DELETE)
            total += count
            deleted.update(deleted_count)
        return total, deleted


class CascadingSoftDeleteModel(SoftDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    class Meta:
        abstract = True


# Patch safedelete's queryset delete so it returns the
# counts of objects deleted like the regular queryset delete.
def safedelete_queryset_delete(self, force_policy=None):
    """Overrides bulk delete behaviour.

    .. note::
        The current implementation loses performance on bulk deletes in order
        to safely delete objects according to the deletion policies set.

    .. seealso::
        :py:func:`safedelete.models.SafeDeleteModel.delete`
    """
    assert self.query.can_filter(), "Cannot use 'limit' or 'offset' with delete."
    # TODO: Replace this by bulk update if we can
    from collections import Counter

    deleted_counter = Counter()
    for obj in self.all():
        obj.delete(force_policy=force_policy)
        deleted_counter[self.model._meta.label] += 1
    self._result_cache = None

    return sum(deleted_counter.values()), dict(deleted_counter)


SafeDeleteQueryset.delete = safedelete_queryset_delete
SafeDeleteQueryset.delete.alters_data = True
