from __future__ import unicode_literals

# BGP relationship between us and a peer
BGP_RELATIONSHIP_PRIVATE_PEERING = "private-peering"
BGP_RELATIONSHIP_TRANSIT_PROVIDER = "transit-provider"
BGP_RELATIONSHIP_CUSTOMER = "customer"
BGP_RELATIONSHIP_CHOICES = (
    (BGP_RELATIONSHIP_PRIVATE_PEERING, "Private Peering"),
    (BGP_RELATIONSHIP_TRANSIT_PROVIDER, "Transit Provider"),
    (BGP_RELATIONSHIP_CUSTOMER, "Customer"),
)

# BGP session state constants
BGP_STATE_IDLE = "idle"
BGP_STATE_CONNECT = "connect"
BGP_STATE_ACTIVE = "active"
BGP_STATE_OPENSENT = "opensent"
BGP_STATE_OPENCONFIRM = "openconfirm"
BGP_STATE_ESTABLISHED = "established"
BGP_STATE_CHOICES = (
    (BGP_STATE_IDLE, "Idle"),
    (BGP_STATE_CONNECT, "Connect"),
    (BGP_STATE_ACTIVE, "Active"),
    (BGP_STATE_OPENSENT, "OpenSent"),
    (BGP_STATE_OPENCONFIRM, "OpenConfirm"),
    (BGP_STATE_ESTABLISHED, "Established"),
)

# Community type constants
COMMUNITY_TYPE_EGRESS = "egress"
COMMUNITY_TYPE_INGRESS = "ingress"
COMMUNITY_TYPE_CHOICES = (
    (COMMUNITY_TYPE_EGRESS, "Egress"),
    (COMMUNITY_TYPE_INGRESS, "Ingress"),
)

# Platform constants, based on NAPALM drivers
PLATFORM_JUNOS = "junos"
PLATFORM_IOSXR = "iosxr"
PLATFORM_IOS = "ios"
PLATFORM_NXOS = "nxos"
PLATFORM_EOS = "eos"
PLATFORM_NONE = None
PLATFORM_CHOICES = (
    (PLATFORM_JUNOS, "Juniper JUNOS"),
    (PLATFORM_IOSXR, "Cisco IOS-XR"),
    (PLATFORM_IOS, "Cisco IOS"),
    (PLATFORM_NXOS, "Cisco NX-OS"),
    (PLATFORM_EOS, "Arista EOS"),
    (PLATFORM_NONE, "Other"),
)

# Routing policies constants
ROUTING_POLICY_TYPE_IMPORT = "import-policy"
ROUTING_POLICY_TYPE_EXPORT = "export-policy"
ROUTING_POLICY_TYPE_CHOICES = (
    (ROUTING_POLICY_TYPE_IMPORT, "Import"),
    (ROUTING_POLICY_TYPE_EXPORT, "Export"),
)
