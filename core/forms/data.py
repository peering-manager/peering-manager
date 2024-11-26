import copy

from django import forms

from core.enums import DataSourceStatus
from peering_manager.forms import (
    PeeringManagerModelBulkEditForm,
    PeeringManagerModelFilterSetForm,
    PeeringManagerModelForm,
)
from peering_manager.registry import DATA_BACKENDS_KEY, registry
from utils.forms import get_field_value
from utils.forms.constants import BOOLEAN_WITH_BLANK_CHOICES
from utils.forms.fields import DynamicModelChoiceField, DynamicModelMultipleChoiceField
from utils.forms.fields.fields import CommentField
from utils.forms.widgets import (
    BulkEditNullBooleanSelect,
    StaticSelect,
    StaticSelectMultiple,
)

from ..models import DataFile, DataSource
from ..utils import get_data_backend_choices

__all__ = (
    "DataFileFilterForm",
    "DataSourceBulkEditForm",
    "DataSourceFilterForm",
    "DataSourceForm",
    "PushedDataMixin",
    "SynchronisedDataMixin",
)


class DataFileFilterForm(PeeringManagerModelFilterSetForm):
    model = DataFile
    source_id = DynamicModelMultipleChoiceField(
        required=False, queryset=DataSource.objects.all(), label="Data source"
    )


class DataSourceForm(PeeringManagerModelForm):
    type = forms.ChoiceField(choices=get_data_backend_choices, widget=StaticSelect)
    comments = CommentField()

    class Meta:
        model = DataSource
        fields = (
            "name",
            "type",
            "source_url",
            "enabled",
            "description",
            "comments",
            "ignore_rules",
            "tags",
        )
        widgets = {
            "ignore_rules": forms.Textarea(
                attrs={
                    "rows": 5,
                    "class": "text-monospace",
                    "placeholder": ".cache\n*.txt",
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        backend_type = get_field_value(self, "type")
        backend = registry[DATA_BACKENDS_KEY].get(backend_type)

        self.backend_fields = []
        if backend:
            for name, form_field in backend.parameters.items():
                field_name = f"backend_{name}"
                self.backend_fields.append(field_name)
                self.fields[field_name] = copy.copy(form_field)
                if self.instance and self.instance.parameters:
                    self.fields[field_name].initial = self.instance.parameters.get(name)

    def save(self, *args, **kwargs):
        parameters = {}
        for name in self.fields:
            if name.startswith("backend_"):
                parameters[name[8:]] = self.cleaned_data[name]
        self.instance.parameters = parameters

        return super().save(*args, **kwargs)

    @property
    def fieldsets(self):
        fieldsets = [
            (
                "Source",
                (
                    "name",
                    "type",
                    "source_url",
                    "enabled",
                    "description",
                    "tags",
                    "ignore_rules",
                ),
            )
        ]

        if self.backend_fields:
            fieldsets.append(("Backend Parameters", self.backend_fields))

        return fieldsets


class DataSourceBulkEditForm(PeeringManagerModelBulkEditForm):
    type = forms.ChoiceField(required=False, choices=get_data_backend_choices)
    enabled = forms.NullBooleanField(required=False, widget=BulkEditNullBooleanSelect())
    description = forms.CharField(required=False, max_length=200)
    comments = CommentField()
    parameters = forms.JSONField(required=False)
    ignore_rules = forms.CharField(required=False, widget=forms.Textarea())

    model = DataSource
    fieldsets = (
        None,
        ("type", "enabled", "description", "comments", "parameters", "ignore_rules"),
    )
    nullable_fields = ("description", "parameters", "comments", "ignore_rules")


class DataSourceFilterForm(PeeringManagerModelFilterSetForm):
    model = DataSource
    type = forms.MultipleChoiceField(
        required=False, choices=get_data_backend_choices, widget=StaticSelectMultiple
    )
    status = forms.MultipleChoiceField(
        required=False, choices=DataSourceStatus, widget=StaticSelectMultiple
    )
    enabled = forms.NullBooleanField(
        required=False, widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES)
    )


class PushedDataMixin(forms.Form):
    data_source = DynamicModelChoiceField(
        required=False, queryset=DataSource.objects.all()
    )
    data_path = forms.CharField(
        required=False,
        max_length=200,
        help_text="Relative path of the file (filename included) to create or update",
    )


class SynchronisedDataMixin(forms.Form):
    data_source = DynamicModelChoiceField(
        required=False, queryset=DataSource.objects.all()
    )
    data_file = DynamicModelChoiceField(
        required=False,
        queryset=DataFile.objects.all(),
        label="File",
        query_params={"source_id": "$data_source"},
    )
