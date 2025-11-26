from django import forms
from taggit.forms import TagField

from peering_manager.forms import (
    PeeringManagerModelFilterSetForm,
    PeeringManagerModelForm,
)
from peering_manager.forms.base import PeeringManagerModelBulkEditForm
from utils.forms import add_blank_choice
from utils.forms.fields import JSONField, SlugField, TagFilterField
from utils.forms.widgets import StaticSelect, StaticSelectMultiple

from ..enums import CommunityType
from ..models import Community

__all__ = ("CommunityBulkEditForm", "CommunityFilterForm", "CommunityForm")


class CommunityForm(PeeringManagerModelForm):
    slug = SlugField(max_length=255)
    type = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(CommunityType),
        widget=StaticSelect,
        help_text="Optional, Ingress for received routes, Egress for advertised routes",
    )
    local_context_data = JSONField(required=False)
    tags = TagField(required=False)
    fieldsets = (
        (
            "Community",
            (
                "name",
                "slug",
                "description",
                "type",
                "value",
            ),
        ),
        ("Config Context", ("local_context_data",)),
    )

    class Meta:
        model = Community

        fields = (
            "name",
            "slug",
            "description",
            "type",
            "value",
            "local_context_data",
            "tags",
        )
        help_texts = {
            "value": 'Community (<a target="_blank" href="https://tools.ietf.org/html/rfc1997">RFC1997</a>), Extended Community (<a target="_blank" href="https://tools.ietf.org/html/rfc4360">RFC4360</a>) or Large Community (<a target="_blank" href="https://tools.ietf.org/html/rfc8092">RFC8092</a>)'
        }


class CommunityBulkEditForm(PeeringManagerModelBulkEditForm):
    type = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(CommunityType),
        widget=StaticSelect,
    )
    local_context_data = JSONField(required=False)

    model = Community
    nullable_fields = ("type", "description", "local_context_data")


class CommunityFilterForm(PeeringManagerModelFilterSetForm):
    model = Community
    type = forms.MultipleChoiceField(
        required=False,
        choices=add_blank_choice(CommunityType),
        widget=StaticSelectMultiple,
    )
    tag = TagFilterField(model)
