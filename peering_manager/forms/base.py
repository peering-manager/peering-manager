from django import forms
from django.contrib.contenttypes.models import ContentType
from django.forms.formsets import BaseFormSet

from extras.models import Tag
from utils.forms import BootstrapMixin
from utils.forms.fields import DynamicModelMultipleChoiceField

__all__ = (
    "PeeringManagerModelForm",
    "PeeringManagerModelBulkEditForm",
    "PeeringManagerModelFilterSetForm",
    "HiddenControlFormSet",
)


class PeeringManagerModelForm(BootstrapMixin, forms.ModelForm):
    """
    Base form for creating and editing models.

    It adds support for adding/removing tags.

    The `fieldsets` property is an iterable of two-tuples which define a heading and
    field set to display per section of the rendered form (optional). If not defined,
    all fields will be rendered as a single section.
    """

    fieldsets = ()
    tags = DynamicModelMultipleChoiceField(queryset=Tag.objects.all(), required=False)

    def _get_content_type(self):
        return ContentType.objects.get_for_model(self._meta.model)


class PeeringManagerModelBulkEditForm(BootstrapMixin, forms.Form):
    """
    Base form for modifying multiple objects (of the same type) in bulk via the UI.

    It adds support for adding/removing tags.

    The `fieldsets` property is an iterable of two-tuples which define a heading and
    field set to display per section of the rendered form (optional). If not defined,
    all fields will be rendered as a single section.

    The `nullable_fields` property is an iterable of field names indicating which
    fields support being set to null/empty.
    """

    nullable_fields = ()

    pk = forms.ModelMultipleChoiceField(
        queryset=None, widget=forms.MultipleHiddenInput  # Set from self.model on init
    )
    add_tags = DynamicModelMultipleChoiceField(
        queryset=Tag.objects.all(), required=False
    )
    remove_tags = DynamicModelMultipleChoiceField(
        queryset=Tag.objects.all(), required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["pk"].queryset = self.model.objects.all()


class PeeringManagerModelFilterSetForm(BootstrapMixin, forms.Form):
    """
    Base form for FilerSet forms. These are used to filter object lists in the UI.

    The corresponding FilterSet must provide a `q` filter.

    The `model` property must be set to the model class associated with the form.

    The `fieldsets` property is an iterable of two-tuples which define a heading and
    field set to display per section of the rendered form (optional). If not defined,
    all fields will be rendered as a single section.
    """

    q = forms.CharField(required=False, label="Search")


class HiddenControlFormSet(BaseFormSet):
    deletion_widget = forms.widgets.HiddenInput
