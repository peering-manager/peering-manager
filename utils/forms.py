import django_filters
import json

from django import forms
from django.db.models import Count
from django.conf import settings
from django.contrib.auth.models import User
from django.forms import BoundField
from django.urls import reverse
from taggit.forms import TagField

from .constants import *
from .fields import ColorSelect, CommentField, SlugField
from .models import ObjectChange, Tag


def add_blank_choice(choices):
    """
    Add a blank choice to the beginning of a choices list.
    """
    return ((None, "---------"),) + tuple(choices)


class BulkEditForm(forms.Form):
    """
    Base form for editing several objects at the same time.
    """

    def __init__(self, model, parent_object=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
        self.parent_object = parent_object
        self.nullable_fields = []

        if hasattr(self.Meta, "nullable_fields"):
            self.nullable_fields = self.Meta.nullable_fields


class BootstrapMixin(forms.BaseForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        custom_widgets = [forms.CheckboxInput, forms.RadioSelect]

        for field_name, field in self.fields.items():
            if field.widget.__class__ in custom_widgets:
                css = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = " ".join(
                    [css, "custom-control-input"]
                ).strip()
            else:
                css = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = " ".join([css, "form-control"]).strip()

            if field.required:
                field.widget.attrs["required"] = "required"
            if "placeholder" not in field.widget.attrs:
                field.widget.attrs["placeholder"] = field.label


class ConfirmationForm(BootstrapMixin, forms.Form):
    """
    A generic confirmation form. The form is not valid unless the confirm field
    is checked.
    """

    confirm = forms.BooleanField(
        required=True, widget=forms.HiddenInput(), initial=True
    )


class TableConfigurationForm(BootstrapMixin, forms.Form):
    """
    Form used to configure table and store the result in user's preferences.
    """

    columns = forms.MultipleChoiceField(
        choices=[],
        widget=forms.SelectMultiple(attrs={"size": 10}),
        help_text="Use the buttons below to arrange columns in the desired order, then select all columns to display.",
    )

    def __init__(self, table, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["columns"].choices = table.configurable_columns
        self.fields["columns"].initial = table.visible_columns


class SmallTextarea(forms.Textarea):
    """
    Just to be used as small text area.
    """

    pass


class APISelect(forms.Select):
    """
    Select widget using API calls to populate its choices.
    """

    def __init__(
        self,
        api_url=None,
        display_field=None,
        value_field=None,
        disabled_indicator=None,
        filter_for=None,
        conditional_query_params=None,
        additional_query_params=None,
        null_option=False,
        full=False,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.attrs["class"] = "custom-select2-api"

        if api_url:
            self.attrs["data-url"] = f"/{settings.BASE_PATH}{api_url.lstrip('/')}"
        if full:
            self.attrs["data-full"] = full
        if display_field:
            self.attrs["display-field"] = display_field
        if value_field:
            self.attrs["value-field"] = value_field
        if disabled_indicator:
            self.attrs["disabled-indicator"] = disabled_indicator
        if filter_for:
            for key, value in filter_for.items():
                self.add_filter_for(key, value)
        if conditional_query_params:
            for key, value in conditional_query_params.items():
                self.add_conditional_query_param(key, value)
        if additional_query_params:
            for key, value in additional_query_params.items():
                self.add_additional_query_param(key, value)
        if null_option:
            self.attrs["data-null-option"] = 1

    def add_filter_for(self, name, value):
        """
        Add details for an additional query param in the form of a data-filter-for-*
        attribute.
        """
        self.attrs[f"data-filter-for-{name}"] = value

    def add_additional_query_param(self, name, value):
        """
        Add details for an additional query param in the form of a data-* JSON-encoded
        list attribute.
        """
        key = f"data-additional-query-param-{name}"

        values = json.loads(self.attrs.get(key, "[]"))
        values.append(value)

        self.attrs[key] = json.dumps(values)

    def add_conditional_query_param(self, condition, value):
        """
        Add details for a URL query strings to append to the URL if the condition is
        met. The condition is specified in the form `<field_name>__<field_value>`.
        """
        self.attrs[f"data-conditional-query-param-{condition}"] = value


class APISelectMultiple(APISelect, forms.SelectMultiple):
    """
    Same API select widget using select2 but allowing multiple choices.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs["data-multiple"] = 1
        self.attrs["data-close-on-select"] = 0


class StaticSelect(forms.Select):
    """
    Select widget for static choices leveraging the select2 component.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs["class"] = "custom-select2-static"


class StaticSelectMultiple(StaticSelect, forms.SelectMultiple):
    """
    Same static select widget using select2 but allowing multiple choices.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs["data-multiple"] = 1
        self.attrs["data-close-on-select"] = 0


class CustomNullBooleanSelect(StaticSelect):
    """
    Do not enforce True/False when not selecting an option.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.choices = (("unknown", "---------"), ("true", "Yes"), ("false", "No"))


class DynamicModelChoiceMixin(object):
    filter = django_filters.ModelChoiceFilter
    widget = APISelect

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_bound_field(self, form, field_name):
        bound_field = BoundField(form, self, field_name)

        # Modify the QuerySet of the field before we return it. Limit choices to any
        # data already bound: Options will be populated on-demand via the APISelect
        # widget
        data = self.prepare_value(bound_field.data or bound_field.initial)
        if data:
            filter = self.filter(
                field_name=self.to_field_name or "pk", queryset=self.queryset
            )
            self.queryset = filter.filter(self.queryset, data)
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


class DynamicModelChoiceField(DynamicModelChoiceMixin, forms.ModelChoiceField):
    """
    Override get_bound_field() to avoid pre-populating field choices with a SQL query.
    The field will be rendered only with choices set via bound data.
    Choices are populated on-demand via the APISelect widget.
    """

    pass


class DynamicModelMultipleChoiceField(
    DynamicModelChoiceMixin, forms.ModelMultipleChoiceField
):
    """
    A multiple-choice version of DynamicModelChoiceField.
    """

    filter = django_filters.ModelMultipleChoiceFilter
    widget = APISelectMultiple


class ObjectChangeFilterForm(BootstrapMixin, forms.Form):
    model = ObjectChange
    q = forms.CharField(required=False, label="Search")
    time_after = forms.DateTimeField(
        label="After",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "YYYY-MM-DD hh:mm:ss"}),
    )
    time_before = forms.DateTimeField(
        label="Before",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "YYYY-MM-DD hh:mm:ss"}),
    )
    action = forms.ChoiceField(
        required=False,
        choices=OBJECT_CHANGE_ACTION_CHOICES,
        widget=StaticSelectMultiple,
    )
    user = forms.ModelChoiceField(
        required=False,
        queryset=User.objects.order_by("username"),
        widget=StaticSelectMultiple,
    )


class TagBulkEditForm(BootstrapMixin, BulkEditForm):
    pk = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(), widget=forms.MultipleHiddenInput
    )
    color = forms.CharField(max_length=6, required=False, widget=ColorSelect())

    class Meta:
        nullable_fields = ["comments"]


class TagFilterForm(BootstrapMixin, forms.Form):
    model = Tag
    q = forms.CharField(required=False, label="Search")


class TagForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField()
    comments = CommentField()

    class Meta:
        model = Tag
        fields = ["name", "slug", "color", "comments"]


class AddRemoveTagsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["add_tags"] = TagField(required=False)
        self.fields["remove_tags"] = TagField(required=False)


class TagFilterField(forms.MultipleChoiceField):
    """
    A filter field for the tags of a model.
    Only the tags used by a model are displayed.
    """

    widget = StaticSelectMultiple

    def __init__(self, model, *args, **kwargs):
        def get_choices():
            tags = model.tags.annotate(count=Count("utils_taggeditem_items")).order_by(
                "name"
            )
            return [(str(tag.slug), f"{tag.name} ({tag.count})") for tag in tags]

        # Choices are fetched each time the form is initialized
        super().__init__(
            label="Tags", choices=get_choices, required=False, *args, **kwargs
        )
