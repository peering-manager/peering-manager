from taggit.forms import TagField

from peering_manager.forms import (
    PeeringManagerModelFilterSetForm,
    PeeringManagerModelForm,
)
from utils.forms.fields import SlugField, TagFilterField

from ..models import Relationship

__all__ = ("RelationshipFilterForm", "RelationshipForm")


class RelationshipForm(PeeringManagerModelForm):
    slug = SlugField()
    tags = TagField(required=False)
    fieldsets = (("Relationship", ("name", "slug", "description", "color")),)

    class Meta:
        model = Relationship
        fields = ("name", "slug", "description", "color")


class RelationshipFilterForm(PeeringManagerModelFilterSetForm):
    model = Relationship
    tag = TagFilterField(model)
