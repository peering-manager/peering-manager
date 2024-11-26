from django import forms
from taggit.forms import TagField

from peering_manager.forms import (
    PeeringManagerModelBulkEditForm,
    PeeringManagerModelFilterSetForm,
    PeeringManagerModelForm,
)
from utils.forms.fields import JSONField, SlugField, TagFilterField

from ..models import BFD

__all__ = ("BFDBulkEditForm", "BFDFilterForm", "BFDForm")


class BFDForm(PeeringManagerModelForm):
    slug = SlugField(max_length=255)
    tags = TagField(required=False)
    fieldsets = (
        (
            "Bidirectional Forwarding Detection",
            ("name", "slug", "description"),
        ),
        (
            "Timing Values",
            (
                "minimum_transmit_interval",
                "minimum_receive_interval",
                "detection_multiplier",
                "hold_time",
            ),
        ),
        ("Config Context", ("local_context_data",)),
    )

    class Meta:
        model = BFD
        fields = (
            "name",
            "slug",
            "description",
            "minimum_transmit_interval",
            "minimum_receive_interval",
            "detection_multiplier",
            "hold_time",
            "local_context_data",
            "tags",
        )


class BFDBulkEditForm(PeeringManagerModelBulkEditForm):
    model = BFD
    minimum_transmit_interval = forms.IntegerField(required=False)
    minimum_receive_interval = forms.IntegerField(required=False)
    detection_multiplier = forms.IntegerField(required=False)
    hold_time = forms.IntegerField(required=False)
    local_context_data = JSONField(required=False)


class BFDFilterForm(PeeringManagerModelFilterSetForm):
    model = BFD
    minimum_transmit_interval = forms.IntegerField(required=False)
    minimum_receive_interval = forms.IntegerField(required=False)
    detection_multiplier = forms.IntegerField(required=False)
    hold_time = forms.IntegerField(required=False)
    tag = TagFilterField(model)
