from django import forms
from taggit.forms import TagField

from peering_manager.enums import IPFamily
from peering_manager.forms import (
    PeeringManagerModelFilterSetForm,
    PeeringManagerModelForm,
)
from peering_manager.forms.base import PeeringManagerModelBulkEditForm
from utils.forms import add_blank_choice
from utils.forms.fields import (
    DynamicModelMultipleChoiceField,
    JSONField,
    SlugField,
    TagFilterField,
)
from utils.forms.widgets import StaticSelect, StaticSelectMultiple

from ..enums import RoutingPolicyType
from ..models import Community, RoutingPolicy

__all__ = (
    "RoutingPolicyBulkEditForm",
    "RoutingPolicyFilterForm",
    "RoutingPolicyForm",
)


class RoutingPolicyForm(PeeringManagerModelForm):
    slug = SlugField(max_length=255)
    type = forms.ChoiceField(choices=RoutingPolicyType, widget=StaticSelect)
    address_family = forms.ChoiceField(choices=IPFamily, widget=StaticSelect)
    communities = DynamicModelMultipleChoiceField(
        required=False, queryset=Community.objects.all()
    )
    local_context_data = JSONField(required=False)
    tags = TagField(required=False)
    fieldsets = (
        (
            "Routing Policy",
            (
                "name",
                "slug",
                "description",
                "type",
                "weight",
                "address_family",
                "communities",
            ),
        ),
        ("Config Context", ("local_context_data",)),
    )

    class Meta:
        model = RoutingPolicy

        fields = (
            "name",
            "slug",
            "description",
            "type",
            "weight",
            "address_family",
            "communities",
            "local_context_data",
            "tags",
        )


class RoutingPolicyBulkEditForm(PeeringManagerModelBulkEditForm):
    type = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(RoutingPolicyType),
        widget=StaticSelect,
    )
    weight = forms.IntegerField(required=False, min_value=0, max_value=32767)
    address_family = forms.ChoiceField(
        required=False, choices=IPFamily, widget=StaticSelect
    )
    communities = DynamicModelMultipleChoiceField(
        required=False, queryset=Community.objects.all()
    )
    description = forms.CharField(max_length=200, required=False)
    local_context_data = JSONField(required=False)

    model = RoutingPolicy
    nullable_fields = ("description", "communities", "local_context_data")


class RoutingPolicyFilterForm(PeeringManagerModelFilterSetForm):
    model = RoutingPolicy
    type = forms.MultipleChoiceField(
        required=False,
        choices=add_blank_choice(RoutingPolicyType),
        widget=StaticSelectMultiple,
    )
    weight = forms.IntegerField(required=False, min_value=0, max_value=32767)
    address_family = forms.ChoiceField(
        required=False, choices=add_blank_choice(IPFamily), widget=StaticSelect
    )
    tag = TagFilterField(model)
