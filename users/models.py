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

    def all(self):
        """
        Returns a dictionary of all defined keys and their values.
        """

        def flatten(d, prefix="", separator="."):
            r = {}
            for k, v in d.items():
                key = separator.join([prefix, k]) if prefix else k
                if type(v) == dict:
                    r.update(flatten(v, prefix=key))
                else:
                    r[key] = v
            return r

        return flatten(self.data)

    def get(self, path, default=None, separator="."):
        """
        Retrieves a value based on its path. Each category and value are separated by
        a separator (a dot by default). If the value is not found a provided default
        will be returned instead (None by default).
        """
        data = self.data
        keys = path.split(separator)

        for key in keys:
            if type(data) == dict and key in data:
                # Step by step down the dicts
                data = data.get(key)
            else:
                # Not found
                return default

        return data

    def set(self, path, value, separator=".", commit=False):
        """
        Sets a preference value based on its path. If the preference is nested inside
        categories and subcategories, these will be created in the process. If the
        preference already exists its value will be overwritten. Categories and
        subcategories cannot be overwriten with values, a TypeError exception will be
        raised in that case. This behavior is the same for preferences that cannot be
        changed to categories later on.

        This function does not commit changes to the database if True is not provided
        as value for the commit named parameter.
        """
        data = self.data
        keys = path.split(separator)

        # Look only for categories for now, excluding the name of the value
        for i, key in enumerate(keys[:-1]):
            if key in data and type(data[key]) == dict:
                # Step by step down the dicts
                data = data[key]
            elif key in data:
                wrong_path = separator.join(path.split(separator)[: i + 1])
                raise TypeError(f"Cannot convert category '{wrong_path}' to a value.")
            else:
                # Create a new category
                data = data.setdefault(key, {})

        # Now set the actual value of the preference
        key = keys[-1]
        if key in data and type(data[key]) == dict:
            raise TypeError(
                f"'{path}' is a category, it cannot be converted to a value."
            )
        else:
            data[key] = value

        if commit:
            self.save()

    def delete(self, path, separator=".", commit=False):
        """
        Deletes a preference specified by its path given a separator.
        The key and its children will be deleted. If the key is not valid it will be
        ignored.
        """
        data = self.data
        keys = path.split(separator)

        # Look only for categories for now, excluding the name of the value
        for i, key in enumerate(keys[:-1]):
            if key not in data:
                break
            if type(data[key]) == dict:
                # Step by step down the dicts
                data = data[key]

        # Now delete the preference
        key = keys[-1]
        data.pop(key, None)

        if commit:
            self.save()


@receiver(post_save, sender=User)
def create_userpreferences(instance, created, **kwargs):
    """
    Creates a new `UserPreferences` when a new `User` is created.
    """
    if created:
        UserPreferences(user=instance).save()
