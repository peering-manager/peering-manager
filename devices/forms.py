from django import forms

from utils.fields import SlugField
from utils.forms import BootstrapMixin, SmallTextarea

from .models import Platform


class PlatformFilterForm(BootstrapMixin, forms.Form):
    model = Platform
    q = forms.CharField(required=False, label="Search")


class PlatformForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField(max_length=255)

    class Meta:
        model = Platform
        fields = ["name", "slug", "napalm_driver", "napalm_args", "description"]
        widgets = {"napalm_args": SmallTextarea()}
