from django import forms
from taggit.forms import TagField

from peering_manager.forms import (
    PeeringManagerModelFilterSetForm,
    PeeringManagerModelForm,
)
from utils.forms import add_blank_choice
from utils.forms.fields import (
    CommentField,
    JSONField,
    SlugField,
    TagFilterField,
    TemplateField,
)
from utils.forms.widgets import StaticSelect

from .enums import PasswordAlgorithm
from .models import Configuration, Platform

__all__ = ("ConfigurationForm", "ConfigurationFilterForm", "PlatformForm")


class ConfigurationForm(PeeringManagerModelForm):
    template = TemplateField()
    comments = CommentField()
    tags = TagField(required=False)
    fieldsets = (
        (
            "Configuration",
            ("name", "description", "jinja2_trim", "jinja2_lstrip", "template"),
        ),
    )

    class Meta:
        model = Configuration
        fields = (
            "name",
            "description",
            "template",
            "jinja2_trim",
            "jinja2_lstrip",
            "comments",
            "tags",
        )


class ConfigurationFilterForm(PeeringManagerModelFilterSetForm):
    model = Configuration
    tag = TagFilterField(model)


class PlatformForm(PeeringManagerModelForm):
    slug = SlugField(max_length=255)
    password_algorithm = forms.ChoiceField(
        required=False, choices=add_blank_choice(PasswordAlgorithm), widget=StaticSelect
    )
    napalm_args = JSONField(
        required=False,
        label="Optional arguments",
        help_text="See NAPALM's <a href='http://napalm.readthedocs.io/en/latest/support/#optional-arguments'>documentation</a> for a complete list of optional arguments",
    )
    tags = TagField(required=False)
    fieldsets = (
        (
            "Platform",
            (
                "name",
                "slug",
                "description",
                "password_algorithm",
                "napalm_driver",
                "napalm_args",
            ),
        ),
    )

    class Meta:
        model = Platform
        fields = (
            "name",
            "slug",
            "description",
            "password_algorithm",
            "napalm_driver",
            "napalm_args",
            "tags",
        )
