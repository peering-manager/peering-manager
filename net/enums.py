from utils.enums import ChoiceSet


class ConnectionStatus(ChoiceSet):
    ENABLED = "enabled"
    PRE_MAINTENANCE = "pre-maintenance"
    MAINTENANCE = "maintenance"
    POST_MAINTENANCE = "post-maintenance"
    DISABLED = "disabled"

    CHOICES = (
        (ENABLED, "Enabled", "success"),
        (PRE_MAINTENANCE, "Pre-maintenance", "warning"),
        (MAINTENANCE, "Maintenance", "warning"),
        (POST_MAINTENANCE, "Post-maintenance", "warning"),
        (DISABLED, "Disabled", "danger"),
    )
