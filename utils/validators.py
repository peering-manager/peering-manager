from django.core.validators import BaseValidator
from django.utils.deconstruct import deconstructible


@deconstructible
class AddressFamilyValidator(BaseValidator):
    compare = lambda self, value, version: value.version != version
    message = "Enter a valid IPv%(limit_value)s address."
    code = "address_version"
