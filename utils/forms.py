import django_filters
import json

from django import forms
from django.db.models import Count
from django.conf import settings
from django.contrib.auth.models import User
from django.forms import BoundField
from django.urls import reverse
from taggit.forms import TagField

from .enums import ObjectChangeAction
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

    def __init__(self, api_url=None, full=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs["class"] = "custom-select2-api"

        if api_url:
            self.attrs["data-url"] = f"/{settings.BASE_PATH}{api_url.lstrip('/')}"
        if full:
            self.attrs["data-full"] = full

    def add_query_param(self, name, value):
        key = f"data-query-param-{name}"

        values = json.loads(self.attrs.get(key, "[]"))
        if type(value) is list:
            values.extend([str(v) for v in value])
        else:
            values.append(str(value))

        self.attrs[key] = json.dumps(values)


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

    def __init__(
        self,
        *args,
        display_field="name",
        query_params=None,
        null_option=None,
        disabled_indicator=None,
        **kwargs,
    ):
        self.display_field = display_field
        self.to_field_name = kwargs.get("to_field_name")
        self.query_params = query_params or {}
        self.null_option = null_option
        self.disabled_indicator = disabled_indicator

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
        required=False, choices=ObjectChangeAction.choices, widget=StaticSelectMultiple,
    )
    user = DynamicModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        display_field="username",
        widget=APISelectMultiple(api_url="/api/users/users/"),
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
