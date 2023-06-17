from django import forms
from django.contrib.auth.models import User
from django.db.models import Count
from taggit.forms import TagField

from utils.enums import ObjectChangeAction
from utils.models import ObjectChange

from .fields import DynamicModelMultipleChoiceField
from .widgets import APISelectMultiple, StaticSelectMultiple


def add_blank_choice(choices):
    """
    Add a blank choice to the beginning of a choices list.
    """
    return ((None, "---------"),) + tuple(choices)


class BulkEditForm(forms.Form):
    """
    Base form for editing several objects at the same time.
    """

    def __init__(self, model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
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
        required=False,
        choices=(),
        widget=forms.SelectMultiple(attrs={"size": 10}),
        help_text="Use the buttons below to arrange columns in the desired order, then select all columns to display.",
    )

    def __init__(self, table, *args, **kwargs):
        self.table = table

        super().__init__(*args, **kwargs)

        self.fields["columns"].choices = table.available_columns
        self.fields["columns"].initial = table.selected_columns

    @property
    def table_name(self):
        return self.table.__class__.__name__


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
        required=False, choices=ObjectChangeAction, widget=StaticSelectMultiple
    )
    user_id = DynamicModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        display_field="username",
        label="User",
        widget=APISelectMultiple(api_url="/api/users/users/"),
    )


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
            tags = model.tags.annotate(count=Count("extras_taggeditem_items")).order_by(
                "name"
            )
            return [(str(tag.slug), f"{tag.name} ({tag.count})") for tag in tags]

        # Choices are fetched each time the form is initialized
        super().__init__(
            label="Tags", choices=get_choices, required=False, *args, **kwargs
        )
