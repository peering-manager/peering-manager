from django import forms

from bgp.models import Relationship
from utils.fields import SlugField
from utils.forms import BootstrapMixin


class RelationshipForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField()

    class Meta:
        model = Relationship
        fields = [
            "name",
            "slug",
            "description",
            "color",
        ]


class RelationshipFilterForm(BootstrapMixin, forms.Form):
    model = Relationship
    q = forms.CharField(required=False, label="Search")
