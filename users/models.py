import binascii
import os

from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class Token(models.Model):
    """
    A token is an object allowing a user to work with the API. Without a token the
    user will not be able to authenticate.
    """

    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="tokens")
    created = models.DateTimeField(auto_now_add=True)
    expires = models.DateTimeField(blank=True, null=True)
    key = models.CharField(
        max_length=40, unique=True, validators=[MinLengthValidator(40)]
    )
    write_enabled = models.BooleanField(
        default=True, help_text="Permit create/update/delete operations using this key"
    )
    description = models.CharField(max_length=100, blank=True)

    class Meta:
        pass

    def __str__(self):
        # Prevent exposure of the complete key
        return "{} ({})".format(self.key[-6:], self.user)

    def __generate_key(self):
        # Random 160-bit key in hexadecimal
        return binascii.hexlify(os.urandom(20)).decode()

    @property
    def is_expired(self):
        """
        Says if this token is expired if it has an expiration date.
        """
        return (self.expires is not None) and (timezone.now() >= self.expires)

    def save(self, *args, **kwargs):
        if not self.key:
            # Generate a key if none is given
            self.key = self.__generate_key()
        return super().save(*args, **kwargs)


class UserPreferences(models.Model):
    """
    This model stores user-specific preferences as JSON.
    """

    user = models.OneToOneField(
        to=User, on_delete=models.CASCADE, related_name="preferences"
    )
    data = JSONField(default=dict)

    class Meta:
        ordering = ["user"]
        verbose_name = verbose_name_plural = "User Preferences"


@receiver(post_save, sender=User)
def create_userpreferences(instance, created, **kwargs):
    """
    Creates a new `UserPreferences` when a new `User` is created.
    """
    if created:
        UserPreferences(user=instance).save()
