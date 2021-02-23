from django.db import models


class PasswordAlgorithm(models.TextChoices):
    CISCO_TYPE7 = "cisco-type7", "Cisco Type 7"
    JUNIPER_TYPE9 = "juniper-type9", "Juniper Type 9"
