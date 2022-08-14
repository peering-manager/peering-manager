from utils.enums import ChoiceSet


class BGPGroupStatus(ChoiceSet):
    ENABLED = "enabled"
    MAINTENANCE = "maintenance"
    DISABLED = "disabled"

    CHOICES = (
        (ENABLED, "Enabled", "success"),
        (MAINTENANCE, "Maintenance", "warning"),
        (DISABLED, "Disabled", "danger"),
    )


class BGPSessionStatus(ChoiceSet):
    ENABLED = "enabled"
    MAINTENANCE = "maintenance"
    DISABLED = "disabled"

    CHOICES = (
        (ENABLED, "Enabled", "success"),
        (MAINTENANCE, "Maintenance", "warning"),
        (DISABLED, "Disabled", "danger"),
    )


class BGPState(ChoiceSet):
    IDLE = "idle"
    CONNECT = "connect"
    ACTIVE = "active"
    OPENSENT = "opensent"
    OPENCONFIRM = "openconfirm"
    ESTABLISHED = "established"

    CHOICES = (
        (IDLE, "Idle"),
        (CONNECT, "Connect"),
        (ACTIVE, "Active"),
        (OPENSENT, "OpenSent"),
        (OPENCONFIRM, "OpenConfirm"),
        (ESTABLISHED, "Established"),
    )


class CommunityType(ChoiceSet):
    EGRESS = "egress"
    INGRESS = "ingress"

    CHOICES = ((EGRESS, "Egress"), (INGRESS, "Ingress"))


class DeviceStatus(ChoiceSet):
    ENABLED = "enabled"
    MAINTENANCE = "maintenance"
    DISABLED = "disabled"

    CHOICES = (
        (ENABLED, "Enabled", "success"),
        (MAINTENANCE, "Maintenance", "warning"),
        (DISABLED, "Disabled", "danger"),
    )


class IPFamily(ChoiceSet):
    ALL = 0
    IPV4 = 4
    IPV6 = 6

    CHOICES = ((ALL, "All"), (IPV4, "IPv4"), (IPV6, "IPv6"))


class RoutingPolicyType(ChoiceSet):
    EXPORT = "export-policy"
    IMPORT = "import-policy"
    IMPORT_EXPORT = "import-export-policy"

    CHOICES = ((EXPORT, "Export"), (IMPORT, "Import"), (IMPORT_EXPORT, "Import+Export"))
