from collections import OrderedDict

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import ListField
from rest_framework.relations import PrimaryKeyRelatedField, RelatedField


class ChoiceField(serializers.Field):
    """
    Represents a `ChoiceField` as:

      {'value': <DB value>, 'label': <string>}.

    Accepts a single value on write.

    `choices` is an iterable of choices in the form(value, key).
    """

    def __init__(self, choices, allow_blank=False, **kwargs):
        self.choiceset = choices
        self.allow_blank = allow_blank
        self._choices = {}

        # Unpack grouped choices
        for k, v in choices:
            if type(v) in (list, tuple):
                for k2, v2 in v:
                    self._choices[k2] = v2
            else:
                self._choices[k] = v

        super().__init__(**kwargs)

    def validate_empty_values(self, data):
        # Convert null to an empty string unless allow_null == True
        if data is None:
            if self.allow_null:
                return True, None
            else:
                data = ""
        return super().validate_empty_values(data)

    def to_representation(self, o):
        return (
            None
            if o == ""
            else OrderedDict([("value", o), ("label", self._choices[o])])
        )

    def to_internal_value(self, data):
        if data == "":
            if self.allow_blank:
                return data
            raise ValidationError("This field may not be blank.")

        # Provide an explicit error message if the request is trying to write a dict or list
        if isinstance(data, (dict, list)):
            raise ValidationError(
                'Value must be passed directly (e.g. "foo": 123); do not use a dictionary or list.'
            )

        # Check for string representations of boolean/integer values
        if hasattr(data, "lower"):
            if data.lower() == "true":
                data = True
            elif data.lower() == "false":
                data = False
            else:
                try:
                    data = int(data)
                except ValueError:
                    pass

        try:
            if data in self._choices:
                return data
        except TypeError:
            pass

        raise ValidationError(f"{data} is not a valid choice.")

    @property
    def choices(self):
        return self._choices


class ContentTypeField(RelatedField):
    """
    Represent a ContentType as '<app_label>.<model>'
    """

    default_error_messages = {
        "does_not_exist": "Invalid content type: {content_type}",
        "invalid": "Invalid value. Specify a content type as '<app_label>.<model_name>'.",
    }

    def to_internal_value(self, data):
        try:
            app_label, model = data.split(".")
            return self.queryset.get(app_label=app_label, model=model)
        except ObjectDoesNotExist:
            self.fail("does_not_exist", content_type=data)
        except (AttributeError, TypeError, ValueError):
            self.fail("invalid")

    def to_representation(self, obj):
        return f"{obj.app_label}.{obj.model}"


class SerializedPKRelatedField(PrimaryKeyRelatedField):
    """
    Extends DRF's `PrimaryKeyRelatedField` to return a serialized object on read.
    This is used for representing related objects in a `ManyToManyField` while still
    allowing a set of primary keys to be written.
    """

    def __init__(self, serializer, **kwargs):
        self.serializer = serializer
        self.pk_field = kwargs.pop("pk_field", None)

        super().__init__(**kwargs)

    def to_representation(self, value):
        return self.serializer(value, context={"request": self.context["request"]}).data
