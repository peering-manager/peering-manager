from django import forms
from django.conf import settings
from django.contrib.auth.models import User
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
        # Only preload the selected option(s); new options are dynamically displayed
        # and added via the API
        template_name = "widgets/select_api.html"

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
        self.choices = (("unknown", "---------"), ("true", "Yes"), ("false", "No"))


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
