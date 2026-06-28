from utils.enums import ChoiceSet


class CommunityKind(ChoiceSet):
    STANDARD = "standard"
    EXTENDED = "extended"
    LARGE = "large"

    CHOICES = (
        (STANDARD, "Community"),
        (EXTENDED, "Extended Community"),
        (LARGE, "Large Community"),
    )


class CommunityCategory(ChoiceSet):
    INFORMATIONAL = "informational"
    ACTION = "action"

    CHOICES = ((INFORMATIONAL, "Informational"), (ACTION, "Action"))


class CommunityType(ChoiceSet):
    EGRESS = "egress"
    INGRESS = "ingress"
    INGRESS_EGRESS = "ingress-egress"

    CHOICES = (
        (EGRESS, "Egress"),
        (INGRESS, "Ingress"),
        (INGRESS_EGRESS, "Ingress+Egress"),
    )


class RoutingPolicyType(ChoiceSet):
    EXPORT = "export-policy"
    IMPORT = "import-policy"
    IMPORT_EXPORT = "import-export-policy"

    CHOICES = ((EXPORT, "Export"), (IMPORT, "Import"), (IMPORT_EXPORT, "Import+Export"))
