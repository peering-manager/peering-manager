from utils.enums import ChoiceSet


class PasswordAlgorithm(ChoiceSet):
    CISCO_TYPE7 = "cisco-type7"
    JUNIPER_TYPE9 = "juniper-type9"

    CHOICES = ((CISCO_TYPE7, "Cisco Type 7"), (JUNIPER_TYPE9, "Juniper Type 9"))
