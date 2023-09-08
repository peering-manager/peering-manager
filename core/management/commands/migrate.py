from django.core.management.commands.migrate import Command
from django.db import models

from utils.migration import custom_deconstruct

models.Field.deconstruct = custom_deconstruct
