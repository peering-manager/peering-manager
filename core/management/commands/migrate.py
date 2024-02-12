from django.core.management.commands.migrate import Command  # noqa: F401
from django.db import models

from utils.migration import custom_deconstruct

models.Field.deconstruct = custom_deconstruct
