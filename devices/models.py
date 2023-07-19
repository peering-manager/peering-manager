import traceback

from django.conf import settings
from django.db import models
from django.urls import reverse
from jinja2 import Environment, TemplateSyntaxError

from peering.models import Template
from peering_manager.jinja2 import (
    FILTER_DICT,
    IncludeTemplateExtension,
    PeeringManagerLoader,
)
from peering_manager.models import OrganisationalModel

from .crypto import *
from .enums import PasswordAlgorithm

__all__ = ("Configuration", "Platform")


class Configuration(Template):
    def get_absolute_url(self):
        return reverse("devices:configuration_view", args=[self.pk])

    def render(self, variables):
        """
        Render the template using Jinja2.
        """
        environment = Environment(
            loader=PeeringManagerLoader(),
            trim_blocks=self.jinja2_trim,
            lstrip_blocks=self.jinja2_lstrip,
        )
        environment.add_extension(IncludeTemplateExtension)
        for extension in settings.JINJA2_TEMPLATE_EXTENSIONS:
            environment.add_extension(extension)

        # Add custom filters to our environment
        environment.filters.update(FILTER_DICT)

        # Try rendering the template, return a message about syntax issues if there
        # are any
        try:
            jinja2_template = environment.from_string(self.template)
            return jinja2_template.render(variables)
        except TemplateSyntaxError as e:
            return f"Syntax error in template at line {e.lineno}: {e.message}"
        except Exception:
            return traceback.format_exc()


class Platform(OrganisationalModel):
    """
    Platform refers to the software or firmware running on a device.

    For example, "Juniper Junos", "Arista EOS" or "Cisco IOS-XR".

    Peering Manager uses platforms to determine how to interact with routers by
    specifying a NAPALM driver.
    """

    napalm_driver = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="NAPALM driver",
        help_text="The name of the NAPALM driver to use when interacting with devices",
    )
    napalm_args = models.JSONField(
        blank=True,
        null=True,
        verbose_name="NAPALM arguments",
        help_text="Additional arguments to pass when initiating the NAPALM driver (JSON format)",
    )
    password_algorithm = models.CharField(
        max_length=16,
        blank=True,
        choices=PasswordAlgorithm,
        help_text="Algorithm to cipher password in configuration",
    )

    def get_absolute_url(self):
        return f"{reverse('peering:router_list')}?platform={self.pk}"

    def encrypt_password(self, password):
        """
        Encrypts a password using the defined algorithm.

        If no algorithm is selected, the password will be returned as it is.
        If the password is already encrypted, it will be returned without performing
        a new encryption.
        """
        if not self.password_algorithm:
            return password

        return ENCRYPTERS[self.password_algorithm](password)

    def decrypt_password(self, password):
        """
        Decrypts a password using the defined algorithm.

        If no algorithm is selected, the password will be returned as it is.
        If the password is not encrypted, it will be returned without performing a
        decryption.
        """
        if not self.password_algorithm:
            return password

        return DECRYPTERS[self.password_algorithm](password)
