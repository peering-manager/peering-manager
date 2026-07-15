# ASN bounds
ASN_MIN = 1
ASN_MAX = 2**32 - 1
ASN_MAX_2_OCTETS = 2**16 - 1

# TTL bounds
TTL_MIN = 1
TTL_MAX = 2**8 - 1

# Follows draft-ramseyer-grow-peering-api
IX_LOCATION_PREFIX = "pdb:ix:"
FACILITY_LOCATION_PREFIX = "pdb:fac:"


def format_ix_location(ixlan_pk: int) -> str:
    """Returns the portal API location identifier of an IX LAN."""
    return f"{IX_LOCATION_PREFIX}{ixlan_pk}"


def format_facility_location(facility_pk: int) -> str:
    """Returns the portal API location identifier of a PeeringDB facility."""
    return f"{FACILITY_LOCATION_PREFIX}{facility_pk}"
