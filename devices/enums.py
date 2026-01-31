from utils.enums import ChoiceSet


class DeviceStatus(ChoiceSet):
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


class PasswordAlgorithm(ChoiceSet):
    ARISTA_TYPE7 = "arista-type7"
    CISCO_TYPE7 = "cisco-type7"
    JUNIPER_TYPE9 = "juniper-type9"

    CHOICES = (
        (ARISTA_TYPE7, "Arista Type 7"),
        (CISCO_TYPE7, "Cisco Type 7"),
        (JUNIPER_TYPE9, "Juniper Type 9"),
    )
