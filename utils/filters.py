import django_filters
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django_filters.constants import EMPTY_VALUES
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field

__all__ = (
    "ContentTypeFilter",
    "MACAddressFilter",
    "MultiValueCharFilter",
    "MultiValueDateFilter",
    "MultiValueDateTimeFilter",
    "MultiValueDecimalFilter",
    "MultiValueMACAddressFilter",
    "MultiValueNumberFilter",
    "MultiValueTimeFilter",
    "NullableCharFieldFilter",
)


def multivalue_field_factory(field_class):
    """
    Transforms a form field into one that accepts multiple values.

    This is used to apply `or` logic when multiple filter values are given while
    maintaining the field's built-in validation.

    Example: /api/peering/autonomous-systems/?asn=64500&asn=64501
    """

    class NewField(field_class):
        widget = forms.SelectMultiple

        def to_python(self, value):
            if not value:
                return []
            field = field_class()
            # Only append non-empty values (this avoids e.g. trying to cast '' as an
            # integer)
            return [field.to_python(v) for v in value if v not in [""]]

        def run_validators(self, value):
            for v in value:
                super().run_validators(v)

        def validate(self, value):
            for v in value:
                super().validate(v)

    return type(f"MultiValue{field_class.__name__}", (NewField,), dict())


@extend_schema_field(OpenApiTypes.STR)
class MultiValueCharFilter(django_filters.MultipleChoiceFilter):
    field_class = multivalue_field_factory(forms.CharField)


@extend_schema_field(OpenApiTypes.DATE)
class MultiValueDateFilter(django_filters.MultipleChoiceFilter):
    field_class = multivalue_field_factory(forms.DateField)


@extend_schema_field(OpenApiTypes.DATETIME)
class MultiValueDateTimeFilter(django_filters.MultipleChoiceFilter):
    field_class = multivalue_field_factory(forms.DateTimeField)


@extend_schema_field(OpenApiTypes.INT32)
class MultiValueNumberFilter(django_filters.MultipleChoiceFilter):
    field_class = multivalue_field_factory(forms.IntegerField)


@extend_schema_field(OpenApiTypes.DECIMAL)
class MultiValueDecimalFilter(django_filters.MultipleChoiceFilter):
    field_class = multivalue_field_factory(forms.DecimalField)


@extend_schema_field(OpenApiTypes.TIME)
class MultiValueTimeFilter(django_filters.MultipleChoiceFilter):
    field_class = multivalue_field_factory(forms.TimeField)


class MACAddressFilter(django_filters.CharFilter):
    pass


@extend_schema_field(OpenApiTypes.STR)
class MultiValueMACAddressFilter(django_filters.MultipleChoiceFilter):
    field_class = multivalue_field_factory(forms.CharField)

    def filter(self, qs, value):
        try:
            return super().filter(qs, value)
        except ValidationError:
            return qs.none()


class NullableCharFieldFilter(django_filters.CharFilter):
    """
    Allow matching on null field values by passing a special string meaning NULL.
    """

    def filter(self, qs, value):
        if value != settings.FILTERS_NULL_CHOICE_VALUE:
            return super().filter(qs, value)
        qs = self.get_method(qs)(**{f"{self.field_name}__isnull": True})
        return qs.distinct() if self.distinct else qs


class ContentTypeFilter(django_filters.CharFilter):
    """
    Allows giving a ContentType by <app_label>.<model> like "peering.router".
    """

    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs

        try:
            app_label, model = value.lower().split(".")
        except ValueError:
            return qs.none()
        return qs.filter(
            **{
                f"{self.field_name}__app_label": app_label,
                f"{self.field_name}__model": model,
            }
        )
