import django_filters
from django import forms
from django.forms import BoundField
from django.urls import reverse

from utils.forms.widgets import APISelect, APISelectMultiple

__all__ = ("DynamicModelChoiceField", "DynamicModelMultipleChoiceField")


class DynamicModelChoiceMixin(object):
    filter = django_filters.ModelChoiceFilter
    widget = APISelect

    def __init__(
        self,
        *args,
        display_field="display",
        query_params=None,
        initial_params=None,
        null_option=None,
        disabled_indicator=None,
        **kwargs,
    ):
        self.display_field = display_field
        self.to_field_name = kwargs.get("to_field_name")
        self.query_params = query_params or {}
        self.initial_params = initial_params or {}
        self.null_option = null_option
        self.disabled_indicator = disabled_indicator

        super().__init__(*args, **kwargs)

    def widget_attrs(self, widget):
        attrs = {"display-field": self.display_field}

        # Set value-field attribute if the field specifies to_field_name
        if self.to_field_name:
            attrs["value-field"] = self.to_field_name

        # Set the string used to represent a null option
        if self.null_option is not None:
            attrs["data-null-option"] = self.null_option

        # Set the disabled indicator, if any
        if self.disabled_indicator is not None:
            attrs["disabled-indicator"] = self.disabled_indicator

        # Attach any static query parameters
        for key, value in self.query_params.items():
            widget.add_query_param(key, value)

        return attrs

    def get_bound_field(self, form, field_name):
        bound_field = BoundField(form, self, field_name)

        # Set the initial value based on prescribed child fields (if not set)
        if not self.initial and self.initial_params:
            filter_kwargs = {}
            for kwarg, child_field in self.initial_params.items():
                value = form.initial.get(child_field.lstrip("$"))
                if value:
                    filter_kwargs[kwarg] = value
            if filter_kwargs:
                self.initial = self.queryset.filter(**filter_kwargs).first()

        # Modify the QuerySet of the field before we return it. Limit choices to any
        # data already bound: Options will be populated on-demand via the APISelect
        # widget
        data = bound_field.value()
        if data:
            field_name = getattr(self, "to_field_name") or "pk"
            filter = self.filter(field_name=field_name)
            try:
                self.queryset = filter.filter(self.queryset, data)
            except (TypeError, ValueError):
                # Catch errors caused by invalid initial data
                self.queryset = self.queryset.none()
        else:
            self.queryset = self.queryset.none()

        # Set the data URL on the APISelect widget (if not already set)
        widget = bound_field.field.widget
        if not widget.attrs.get("data-url"):
            data_url = reverse(
                f"{self.queryset.model._meta.app_label}-api:{self.queryset.model._meta.model_name}-list"
            )
            widget.attrs["data-url"] = data_url

        return bound_field

    def widget_attrs(self, widget):
        attrs = {"display-field": self.display_field}

        # Set value-field attribute if the field specifies to_field_name
        if self.to_field_name:
            attrs["value-field"] = self.to_field_name

        # Attach any static query parameters
        for key, value in self.query_params.items():
            widget.add_query_param(key, value)

        # Set the string used to represent a null option
        if self.null_option is not None:
            attrs["data-null-option"] = self.null_option

        # Set the disabled indicator
        if self.disabled_indicator is not None:
            attrs["disabled-indicator"] = self.disabled_indicator

        return attrs


class DynamicModelChoiceField(DynamicModelChoiceMixin, forms.ModelChoiceField):
    """
    Override get_bound_field() to avoid pre-populating field choices with a SQL query.
    The field will be rendered only with choices set via bound data.
    Choices are populated on-demand via the APISelect widget.
    """

    def clean(self, value):
        if self.null_option is not None and value == "null":
            return None
        return super().clean(value)


class DynamicModelMultipleChoiceField(
    DynamicModelChoiceMixin, forms.ModelMultipleChoiceField
):
    """
    A multiple-choice version of DynamicModelChoiceField.
    """

    filter = django_filters.ModelMultipleChoiceFilter
    widget = APISelectMultiple
