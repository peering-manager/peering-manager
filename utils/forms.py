from django import forms
from django.conf import settings
from django.contrib.auth.models import User

from .constants import *
from .models import ObjectChange


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


class FilterChoiceIterator(forms.models.ModelChoiceIterator):
    def __iter__(self):
        # null for the first time if we asked for it
        if self.field.null_label:
            yield (
                settings.FILTERS_NULL_CHOICE_VALUE,
                settings.FILTERS_NULL_CHOICE_LABEL,
            )
        queryset = self.queryset.all()
        # Can't use iterator() when queryset uses prefetch_related()
        if not queryset._prefetch_related_lookups:
            queryset = queryset.iterator()
        for obj in queryset:
            yield self.choice(obj)


class FilterChoiceFieldMixin(object):
    iterator = FilterChoiceIterator

    def __init__(self, null_label=None, *args, **kwargs):
        self.null_label = null_label
        if "required" not in kwargs:
            kwargs["required"] = False
        if "widget" not in kwargs:
            kwargs["widget"] = forms.SelectMultiple(attrs={"size": 6})
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        label = super().label_from_instance(obj)
        if hasattr(obj, "filter_count"):
            return "{} ({})".format(label, obj.filter_count)
        return label


class FilterChoiceField(FilterChoiceFieldMixin, forms.ModelMultipleChoiceField):
    pass


class PasswordField(forms.CharField):
    """
    A field used to enter password. The field will hide the password unless the
    reveal button is clicked.
    """

    def __init__(self, password_source="password", render_value=False, *args, **kwargs):
        widget = kwargs.pop("widget", forms.PasswordInput(render_value=render_value))
        label = kwargs.pop("label", "Password")
        help_text = kwargs.pop(
            "help_text",
            "It can be a clear text password or an "
            "encrypted one. It really depends on how you "
            "want to use it. Be aware that it is stored "
            "without encryption in the database.",
        )
        super().__init__(
            widget=widget, label=label, help_text=help_text, *args, **kwargs
        )
        self.widget.attrs["password-source"] = password_source


class SlugField(forms.SlugField):
    """
    An improved SlugField that allows to be automatically generated based on a
    field used as source.
    """

    def __init__(self, slug_source="name", *args, **kwargs):
        label = kwargs.pop("label", "Slug")
        help_text = kwargs.pop(
            "help_text", "Friendly unique shorthand used for URL and config"
        )
        super().__init__(label=label, help_text=help_text, *args, **kwargs)
        self.widget.attrs["slug-source"] = slug_source


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
        api_url,
        display_field=None,
        value_field=None,
        query_filters=None,
        null_option=False,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.attrs["class"] = "custom-select2-api"
        self.attrs["data-url"] = "/{}{}".format(settings.BASE_PATH, api_url.lstrip("/"))

        if display_field:
            self.attrs["display-field"] = display_field
        if value_field:
            self.attrs["value-field"] = value_field
        if query_filters:
            for key, value in query_filters.items():
                self.add_query_filter(key, value)
        if null_option:
            self.attrs["data-null-option"] = 1

    def add_query_filter(self, condition, value):
        """
        Add a condition to filter the feedback from the API call.
        """
        self.attrs["data-query-filter-{}".format(condition)] = value


class APISelectMultiple(APISelect, forms.SelectMultiple):
    """
    Same API select widget using select2 but allowing multiple choices.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs["data-multiple"] = 1


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
        self.choices = (("1", "---------"), ("2", "Yes"), ("3", "No"))


class TextareaField(forms.CharField):
    """
    A textarea with support for GitHub-Flavored Markdown. Exists mostly just to
    add a standard help_text.
    """

    widget = forms.Textarea

    def __init__(self, *args, **kwargs):
        required = kwargs.pop("required", False)
        super().__init__(required=required, *args, **kwargs)


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
