from django.db import models

from utils.enums import ChoiceSet


class ConnectionStatus(ChoiceSet):
    ENABLED = "enabled"
    MAINTENANCE = "maintenance"
    DISABLED = "disabled"

    CHOICES = (
        (ENABLED, "Enabled", "success"),
        (MAINTENANCE, "Maintenance", "warning"),
        (DISABLED, "Disabled", "danger"),
    )
