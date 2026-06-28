from utils.enums import ChoiceSet


class IPFamily(ChoiceSet):
    ALL = 0
    IPV4 = 4
    IPV6 = 6

    CHOICES = ((ALL, "All"), (IPV4, "IPv4"), (IPV6, "IPv6"))
