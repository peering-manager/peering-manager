from django import forms

from .mixins import BootstrapMixin

__all__ = (
    "BulkEditForm",
    "ConfirmationForm",
    "FilterForm",
    "TableConfigForm",
)


class BulkEditForm(BootstrapMixin, forms.Form):
    """
    Provide bulk edit support for objects.
    """

    nullable_fields = ()


class ConfirmationForm(BootstrapMixin, forms.Form):
    """
    A generic confirmation form.

    The form is not valid unless the `confirm` field is checked.
    """

    return_url = forms.CharField(required=False, widget=forms.HiddenInput())
    confirm = forms.BooleanField(
        required=True, widget=forms.HiddenInput(), initial=True
    )


class FilterForm(BootstrapMixin, forms.Form):
    """
    Base form class for `FilterSet` forms.
    """

    q = forms.CharField(required=False, label="Search")


class TableConfigForm(BootstrapMixin, forms.Form):
    """
    Form used to configure table and store the result in user's preferences.
    """

    columns = forms.MultipleChoiceField(
        choices=[],
        required=False,
        widget=forms.SelectMultiple(attrs={"size": 10, "class": "form-select"}),
        help_text="Use the buttons below to arrange columns in the desired order, then select all columns to display.",
    )

    def __init__(self, table, *args, **kwargs):
        self.table = table

        super().__init__(*args, **kwargs)

        # Initialize columns field based on table attributes
        self.fields["columns"].choices = table.available_columns
        self.fields["columns"].initial = [c[0] for c in table.selected_columns]

    @property
    def table_name(self):
        return self.table.__class__.__name__
