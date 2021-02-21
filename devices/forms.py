from django import forms

from utils.fields import SlugField
from utils.forms import BootstrapMixin, SmallTextarea, StaticSelect, add_blank_choice

from .enums import PasswordAlgorithm
from .models import Platform


class PlatformForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField(max_length=255)
    password_algorithm = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(PasswordAlgorithm.choices),
        widget=StaticSelect,
    )

    class Meta:
        model = Platform
        fields = [
            "name",
            "slug",
            "napalm_driver",
            "napalm_args",
            "password_algorithm",
            "description",
        ]
        widgets = {"napalm_args": SmallTextarea()}
