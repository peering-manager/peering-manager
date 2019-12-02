NET_AS65536 = {
    "meta": {},
    "data": [
        {
            "id": 1,
            "org_id": 1,
            "name": "Mocked",
            "aka": "mocked",
            "website": "https://example.net",
            "asn": 65536,
            "looking_glass": "https://lg.example.net",
            "route_server": "",
            "irr_as_set": "MOCKED::AS-MOCKED",
            "info_type": "Non-Profit",
            "info_prefixes4": 5,
            "info_prefixes6": 5,
            "info_traffic": "20-100Mbps",
            "info_ratio": "Balanced",
            "info_scope": "Europe",
            "info_unicast": True,
            "info_multicast": False,
            "info_ipv6": True,
            "notes": "",
            "policy_url": "https://example.net",
            "policy_general": "Open",
            "policy_locations": "Not Required",
            "policy_ratio": False,
            "policy_contracts": "Not Required",
            "created": "2018-07-16T17:14:59Z",
            "updated": "2019-09-16T21:12:34Z",
            "status": "ok",
        }
    ],
}

NETIXLAN = {
    "meta": {},
    "data": [
        {
            "id": 1,
            "net_id": 1,
            "ix_id": 1,
            "name": "Mocked",
            "ixlan_id": 1,
            "notes": "",
            "speed": 100000,
            "asn": 65536,
            "ipaddr4": "203.0.113.1",
            "ipaddr6": "2001:db8:1337::1",
            "is_rs_peer": True,
            "created": "2016-06-15T13:23:35Z",
            "updated": "2019-08-13T13:38:52Z",
            "status": "ok",
        }
    ],
}

NETIXLANS_FOR_AS65536 = {
    "meta": {},
    "data": [
        {
            "id": 1,
            "net_id": 1,
            "ix_id": 1,
            "name": "LU-CIX",
            "ixlan_id": 1,
            "notes": "",
            "speed": 100000,
            "asn": 65536,
            "ipaddr4": "203.0.113.1",
            "ipaddr6": "2001:db8:1337::1",
            "is_rs_peer": True,
            "created": "2013-07-14T00:00:00Z",
            "updated": "2018-05-07T07:08:03Z",
            "status": "ok",
        },
        {
            "id": 2,
            "net_id": 1,
            "ix_id": 2,
            "name": "France-IX Paris",
            "ixlan_id": 2,
            "notes": "",
            "speed": 100000,
            "asn": 65536,
            "ipaddr4": "203.0.114.1",
            "ipaddr6": "2001:db8:1338::1",
            "is_rs_peer": True,
            "created": "2013-07-14T00:00:00Z",
            "updated": "2018-04-13T09:58:14Z",
            "status": "ok",
        },
    ],
}

NETIXLANS_FOR_AS65537 = {
    "meta": {},
    "data": [
        {
            "id": 3,
            "net_id": 2,
            "ix_id": 1,
            "name": "LU-CIX",
            "ixlan_id": 1,
            "notes": "",
            "speed": 100000,
            "asn": 65537,
            "ipaddr4": "203.0.113.2",
            "ipaddr6": "2001:db8:1337::2",
            "is_rs_peer": True,
            "created": "2013-07-14T00:00:00Z",
            "updated": "2018-05-07T07:08:03Z",
            "status": "ok",
        }
    ],
}

IXPFX = {
    "meta": {},
    "data": [
        {
            "id": 1,
            "ixlan_id": 1,
            "protocol": "IPv6",
            "prefix": "2001:db8:1337::/64",
            "created": "2011-04-19T00:00:00Z",
            "updated": "2016-03-14T21:55:43Z",
            "status": "ok",
        },
        {
            "id": 2,
            "ixlan_id": 1,
            "protocol": "IPv4",
            "prefix": "203.0.113.0/24",
            "created": "2014-10-16T00:00:00Z",
            "updated": "2016-03-14T21:33:56Z",
            "status": "ok",
        },
    ],
}

NETIXLAN_FOR_ID = {
    "meta": {},
    "data": [
        {
            "id": 1,
            "net_id": 1,
            "ix_id": 1,
            "name": "Mocked",
            "ixlan_id": 1,
            "notes": "",
            "speed": 100000,
            "asn": 65536,
            "ipaddr4": "203.0.113.1",
            "ipaddr6": "2001:db8:1337::1",
            "is_rs_peer": True,
            "created": "2016-02-10T00:00:00Z",
            "updated": "2017-11-21T10:38:33Z",
            "status": "ok",
        },
        {
            "id": 2,
            "net_id": 2,
            "ix_id": 1,
            "name": "Mocked",
            "ixlan_id": 1,
            "notes": "",
            "speed": 100000,
            "asn": 65537,
            "ipaddr4": "203.0.113.2",
            "ipaddr6": "2001:db8:1337::2",
            "is_rs_peer": True,
            "created": "2016-02-14T00:00:00Z",
            "updated": "2016-04-15T18:58:44Z",
            "status": "ok",
        },
    ],
}


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, status_code, json_data):
            self.status_code = status_code
            self.json_data = json_data

        def json(self):
            return self.json_data

    # Mock net records
    if args[0] == "https://peeringdb.com/api/net":
        if kwargs["params"]["asn"] == 65536:
            return MockResponse(200, NET_AS65536)
    # Mock netixlan records
    if args[0] == "https://peeringdb.com/api/netixlan":
        if (
            ("id" in kwargs["params"] and kwargs["params"]["id"] == 1)
            or (
                "ipaddr6" in kwargs["params"]
                and kwargs["params"]["ipaddr6"] == "2001:db8:1337::1"
            )
            or (
                "ipaddr4" in kwargs["params"]
                and kwargs["params"]["ipaddr4"] == "203.0.113.1"
            )
        ):
            return MockResponse(200, NETIXLAN)

        if "asn" in kwargs["params"]:
            if kwargs["params"]["asn"] == 65536:
                return MockResponse(200, NETIXLANS_FOR_AS65536)
            if kwargs["params"]["asn"] == 65537:
                return MockResponse(200, NETIXLANS_FOR_AS65537)

        if "ix_id" in kwargs["params"] and kwargs["params"]["ix_id"] == 1:
            return MockResponse(200, NETIXLAN_FOR_ID)
    # Mock ixpfx records
    if args[0] == "https://peeringdb.com/api/ixpfx":
        if kwargs["params"]["ixlan_id"] == 1:
            return MockResponse(200, IXPFX)

    return MockResponse(404, None)
