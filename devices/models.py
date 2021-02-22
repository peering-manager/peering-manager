from django.db import models
from django.urls import reverse

from utils.models import ChangeLoggedModel

from .crypto import *
from .enums import PasswordAlgorithm


class Platform(ChangeLoggedModel):
    """
    Platform refers to the software or firmware running on a device.

    For example, "Juniper Junos", "Arista EOS" or "Cisco IOS-XR".

    Peering Manager uses platforms to determine how to interact with routers by
    specifying a NAPALM driver.
    """

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="Friendly unique shorthand used for URL and config",
    )
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
        choices=PasswordAlgorithm.choices,
        help_text="Algorithm to cipher password in configuration",
    )
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

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
