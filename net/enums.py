from django.db import models


class ConnectionState(models.TextChoices):
    ENABLED = "enabled", "Enabled"
    DISABLED = "disabled", "Disabled"
