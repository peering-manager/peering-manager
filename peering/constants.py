from __future__ import unicode_literals

# BGP session state constants
BGP_STATE_IDLE = 'idle'
BGP_STATE_CONNECT = 'connect'
BGP_STATE_ACTIVE = 'active'
BGP_STATE_OPENSENT = 'opensent'
BGP_STATE_OPENCONFIRM = 'openconfirm'
BGP_STATE_ESTABLISHED = 'established'
BGP_STATE_CHOICES = (
    (BGP_STATE_IDLE, 'Idle'),
    (BGP_STATE_CONNECT, 'Connect'),
    (BGP_STATE_ACTIVE, 'Active'),
    (BGP_STATE_OPENSENT, 'OpenSent'),
    (BGP_STATE_OPENCONFIRM, 'OpenConfirm'),
    (BGP_STATE_ESTABLISHED, 'Established'),
)

# Platform constants, based on NAPALM drivers
PLATFORM_JUNOS = 'junos'
PLATFORM_IOSXR = 'iosxr'
PLATFORM_IOS = 'ios'
PLATFORM_NXOS = 'nxos'
PLATFORM_EOS = 'eos'
PLATFORM_NONE = None
PLATFORM_CHOICES = (
    (PLATFORM_JUNOS, 'Juniper JUNOS'),
    (PLATFORM_IOSXR, 'Cisco IOS-XR'),
    (PLATFORM_IOS, 'Cisco IOS'),
    (PLATFORM_NXOS, 'Cisco NX-OS'),
    (PLATFORM_EOS, 'Arista EOS'),
    (PLATFORM_NONE, 'Other'),
)
