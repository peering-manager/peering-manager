from django.db import models


class Media(models.TextChoices):
    ETHERNET = "Ethernet"
    ATM = "ATM"
    MULTIPLE = "Multiple"


class POCRole(models.TextChoices):
    ABUSE = "Abuse"
    MAINTENANCE = "Maintenance"
    POLICY = "Policy"
    TECHNICAL = "Technical"
    NOC = "NOC", "NOC"
    PUBLIC_RELATIONS = "Public Relations"
    SALES = "Sales"


class GeneralPolicy(models.TextChoices):
    OPEN = "Open"
    SELECTIVE = "Selective"
    RESTRICTIVE = "Restrictive"
    NO = "No"


class LocationsPolicy(models.TextChoices):
    NOT_REQUIRED = "Not Required"
    PREFERRED = "Preferred"
    REQUIRED_US = "Required - US"
    REQUIRED_EU = "Required - EU"
    REQUIRED_INT = "Required - International"


class ContractsPolicy(models.TextChoices):
    NOT_REQUIRED = "Not Required"
    PRIVATE_ONLY = "Private Only"
    REQUIRED = "Required"


class Protocol(models.TextChoices):
    IPV4 = "IPv4"
    IPV6 = "IPv6"


class Ratio(models.TextChoices):
    NOT_DISCLOSED = "", "Not Disclosed"
    NOT_DISCLOSED_BIS = "Not Disclosed"
    HEAVY_OUTBOUND = "Heavy Outbound"
    MOSTLY_OUTBOUND = "Mostly Outbound"
    BALANCED = "Balanced"
    MOSTLY_INBOUND = "Mostly Inbound"
    HEAVY_INBOUND = "Heavy Inbound"


class Region(models.TextChoices):
    NORTH_AMERICA = "North America"
    ASIA_PACIFIC = "Asia Pacific"
    EUROPE = "Europe"
    SOUTH_AMERICA = "South America"
    AFRICA = "Africa"
    AUSTRALIA = "Australia"
    MIDDLE_EAST = "Middle East"


class ServiceLevels(models.TextChoices):
    NOT_DISCLOSED = "", "Not Disclosed"
    NOT_DISCLOSED_BIS = "Not Disclosed"
    BEST_EFFORT = "Best Effort (no SLA)"
    NORMAL_BUSINESS_HOURS = "Normal Business Hours"
    SUPPORT_24_7 = "24/7 Support"


class Scope(models.TextChoices):
    NOT_DISCLOSED = "", "Not Disclosed"
    NOT_DISCLOSED_BIS = "Not Disclosed"
    REGIONAL = "Regional"
    NORTH_AMERICA = "North America"
    ASIA_PACIFIC = "Asia Pacific"
    EUROPE = "Europe"
    SOUTH_AMERICA = "South America"
    AFRICA = "Africa"
    AUSTRALIA = "Australia"
    MIDDLE_EAST = "Middle East"
    GLOBAL = "Global"


class Terms(models.TextChoices):
    NOT_DISCLOSED = "", "Not Disclosed"
    NOT_DISCLOSED_BIS = "Not Disclosed"
    NO_COMMERCIAL_TERMS = "No Commercial Terms"
    BUNDLED_WITH_OTHER_SERVICES = "Bundled With Other Services"
    NON_RECURRING_FEES_ONLY = "Non-recurring Fees Only"
    RECURRING_FEES = "Recurring Fees"


class Traffic(models.TextChoices):
    NOT_DISCLOSED = "", "Not Disclosed"
    MBPS_20 = "0-20Mbps", "0-20Mbps"
    MBPS_100 = "20-100Mbps", "20-100Mbps"
    GBPS_1 = "100-1000Mbps", "100-1000Mbps"
    GBPS_5 = "1-5Gbps", "1-5Gbps"
    GBPS_10 = "5-10Gbps", "5-10Gbps"
    GBPS_20 = "10-20Gbps", "10-20Gbps"
    GBPS_50 = "20-50Gbps", "20-50Gbps"
    GBPS_100 = "50-100Gbps", "50-100Gbps"
    GBPS_200 = "100-200Gbps", "100-200Gbps"
    GBPS_300 = "200-300Gbps", "200-300Gbps"
    GBPS_500 = "300-500Gbps", "300-500Gbps"
    TBPS_1 = "500-1000Gbps", "500-1000Gbps"
    TBPS_5 = "1-5Tbps", "1-5Tbps"
    TBPS_10 = "5-10Tbps", "5-10Tbps"
    TBPS_20 = "10-20Tbps", "10-20Tbps"
    TBPS_50 = "20-50Tbps", "20-50Tbps"
    TBPS_100 = "50-100Tbps", "50-100Tbps"
    TBPS_100_PLUS = "100+Tbps", "100+Tbps"


class NetType(models.TextChoices):
    NOT_DISCLOSED = "", "Not Disclosed"
    NOT_DISCLOSED_BIS = "Not Disclosed", "Not Disclosed"
    NSP = "NSP", "NSP"
    CONTENT = "Content", "Content"
    CABLE_DSL_ISP = "Cable/DSL/ISP", "Cable/DSL/ISP"
    ENTREPRISE = "Enterprise", "Enterprise"
    EDUCATIONAL_RESEARCH = "Educational/Research", "Educational/Research"
    NON_PROFIT = "Non-Profit", "Non-Profit"
    ROUTE_SERVER = "Route Server", "Route Server"
    NETWORK_SERVICES = "Network Services", "Network Services"
    ROUTE_COLLECTOR = "Route Collector", "Route Collector"
    GOVERNMENT = "Government", "Government"


class Visibility(models.TextChoices):
    PRIVATE = "Private"
    USERS = "Users"
    PUBLIC = "Public"


class Property(models.TextChoices):
    NOT_DISCLOSED = "", "Not Disclosed"
    OWNER = "Owner"
    LESSEE = "Lessee"


class AvailableVoltage(models.TextChoices):
    VDC_48 = "48 VDC", "48 VDC"
    VAC_120 = "120 VAC", "120 VAC"
    VAC_208 = "208 VAC", "208 VAC"
    VAC_240 = "240 VAC", "240 VAC"
    VAC_480 = "480 VAC", "480 VAC"


class MTU(models.IntegerChoices):
    MTU_1500 = 1500, "1500"
    MTU_9000 = 9000, "9000"
