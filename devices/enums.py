from utils.enums import ChoiceSet


class PasswordAlgorithm(ChoiceSet):
    CISCO_TYPE7 = "cisco-type7"
    JUNIPER_TYPE9 = "juniper-type9"
    NOKIA_BCRYPT = "nokia-bcrypt"

    CHOICES = ((CISCO_TYPE7, "Cisco Type 7"), (JUNIPER_TYPE9, "Juniper Type 9"),
               (NOKIA_BCRYPT, "Nokia bcrypt"))
