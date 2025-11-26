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


class CommunityType(ChoiceSet):
    EGRESS = "egress"
    INGRESS = "ingress"

    CHOICES = ((EGRESS, "Egress"), (INGRESS, "Ingress"))
