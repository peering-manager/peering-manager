from peeringdb.models import Network, Organization

PREFIXES6 = '{"prefix_list": [{"prefix": "2001:db8::/32", "exact": true}]}'
PREFIXES4 = '{"prefix_list": [{"prefix": "203.0.113.0/24", "exact": true}]}'
AS_LIST = '{"as_list": [65537, 65538, 65539]}'


def load_peeringdb_data():
    Organization.objects.create(
        id=20477,
        name="Guillaume Mazoyer",
        website="https://as201281.net/",
        notes="",
        address1="",
        address2="",
        city="Metz",
        country="FR",
        state="",
        zipcode="57070",
    )
    Network.objects.create(
        id=17293,
        org_id=20477,
        name="Guillaume Mazoyer",
        aka="mazoyer.eu",
        website="https://as201281.net",
        asn=201281,
        looking_glass="https://lg.as201281.net",
        route_server="",
        irr_as_set="RIPE::AS-MAZOYER-EU",
        info_type="Non-Profit",
        info_prefixes4=5,
        info_prefixes6=5,
        info_traffic="20-100Mbps",
        info_ratio="Balanced",
        info_scope="Europe",
        info_unicast=True,
        info_multicast=False,
        info_ipv6=True,
        info_never_via_route_servers=False,
        notes="",
        policy_url="https://as201281.net",
        policy_general="Open",
        policy_locations="Not Required",
        policy_ratio=False,
        policy_contracts="Not Required",
    )


def mocked_subprocess_popen(*args, **kwargs):
    class MockResponse:
        def __init__(self, returncode, out, err):
            self.returncode = returncode
            self.out = out
            self.err = err

        def communicate(self):
            return self.out, self.err

    if "AS-MOCKED" in args[0] or "AS65537" in args[0]:
        if "-6" in args[0]:
            return MockResponse(0, PREFIXES6.encode(), b"")
        if "-4" in args[0]:
            return MockResponse(0, PREFIXES4.encode(), b"")
    if "AS-NOPREFIXES" in args[0]:
        return MockResponse(0, b'{"prefix_list": []}', b"")
    if "AS-ERROR" in args[0]:
        return MockResponse(1, b"", b"Exit with error")

    return MockResponse(-1, b"", b"Something went wrong")


def mocked_subprocess_popen_as_list(*args, **kwargs):
    class MockResponse:
        def __init__(self, returncode, out, err):
            self.returncode = returncode
            self.out = out
            self.err = err

        def communicate(self):
            return self.out, self.err

    if "AS-MOCKED" in args[0]:
        return MockResponse(0, AS_LIST.encode(), b"")
    if "AS-ERROR" in args[0]:
        return MockResponse(1, b"", b"Exit with error")

    return MockResponse(-1, b"", b"Something went wrong")
