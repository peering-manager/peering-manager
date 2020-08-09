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


class IPFamily(models.IntegerChoices):
    ALL = 0, "All"
    IPV4 = 4, "IPv4"
    IPV6 = 6, "IPv6"


class Platform(models.TextChoices):
    JUNOS = "junos", "Juniper JUNOS"
    IOSXR = "iosxr", "Cisco IOS-XR"
    IOS = "ios", "Cisco IOS"
    NXOS = "nxos", "Cisco NX-OS"
    EOS = "eos", "Arista EOS"
    NONE = "", "Other"


class RoutingPolicyType(models.TextChoices):
    EXPORT = "export-policy", "Export"
    IMPORT = "import-policy", "Import"
    IMPORT_EXPORT = "import-export-policy", "Import+Export"
