from django import forms
from taggit.forms import TagField

from devices.enums import PasswordAlgorithm
from devices.models import Configuration, Platform
from utils.forms import BootstrapMixin, TagFilterField, add_blank_choice
from utils.forms.fields import CommentField, JSONField, SlugField, TemplateField
from utils.forms.widgets import SmallTextarea, StaticSelect


class ConfigurationForm(BootstrapMixin, forms.ModelForm):
    template = TemplateField()
    comments = CommentField()
    tags = TagField(required=False)

    class Meta:
        model = Configuration
        fields = (
            "name",
            "template",
            "jinja2_trim",
            "jinja2_lstrip",
            "comments",
            "tags",
        )


class ConfigurationFilterForm(BootstrapMixin, forms.Form):
    model = Configuration
    q = forms.CharField(required=False, label="Search")
    tag = TagFilterField(model)


class PlatformForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField(max_length=255)
    napalm_args = JSONField(
        required=False,
        label="Optional arguments",
        help_text="See NAPALM's <a href='http://napalm.readthedocs.io/en/latest/support/#optional-arguments'>documentation</a> for a complete list of optional arguments",
        widget=SmallTextarea,
    )
    password_algorithm = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(PasswordAlgorithm.choices),
        widget=StaticSelect,
    )

    class Meta:
        model = Platform
        fields = (
            "name",
            "slug",
            "napalm_driver",
            "napalm_args",
            "password_algorithm",
            "description",
        )
