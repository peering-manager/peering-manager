from django.db import models


class BGPRelationship(models.TextChoices):
    PRIVATE_PEERING = "private-peering"
    TRANSIT_PROVIDER = "transit-provider"
    CUSTOMER = "customer"


class BGPState(models.TextChoices):
    IDLE = "idle"
    CONNECT = "connect"
    ACTIVE = "active"
    OPENSENT = "opensent", "OpenSent"
    OPENCONFIRM = "openconfirm", "OpenConfirm"
    ESTABLISHED = "established"


class CommunityType(models.TextChoices):
    EGRESS = "egress"
    INGRESS = "ingress"


class DeviceState(models.TextChoices):
    ENABLED = "enabled", "Enabled"
    DISABLED = "disabled", "Disabled"
    MAINTENANCE = "maintenance", "Maintenance"


class IPFamily(models.IntegerChoices):
    ALL = 0, "All"
    IPV4 = 4, "IPv4"
    IPV6 = 6, "IPv6"


class RoutingPolicyType(models.TextChoices):
    EXPORT = "export-policy", "Export"
    IMPORT = "import-policy", "Import"
    IMPORT_EXPORT = "import-export-policy", "Import+Export"
