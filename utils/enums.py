from django.db import models


class Color(models.TextChoices):
    DARK_RED = "aa1409", "Dark red"
    RED = "f44336", "Red"
    PINK = "e91e63", "Pink"
    ROSE = "ffe4e1", "Rose"
    FUSCHIA = "ff66ff", "Fuschia"
    PURPLE = "9c27b0", "Purple"
    DARK_PURPLE = "673ab7", "Dark purple"
    INDIGO = "3f51b5", "Indigo"
    BLUE = "2196f3", "Blue"
    LIGHT_BLUE = "03a9f4", "Light blue"
    CYAN = "00bcd4", "Cyan"
    TEAL = "009688", "Teal"
    AQUA = "00ffff", "Aqua"
    DARK_GREEN = "2f6a31", "Dark green"
    GREEN = "4caf50", "Green"
    LIGHT_GREEN = "8bc34a", "Light green"
    LIME = "cddc39", "Lime"
    YELLOW = "ffeb3b", "Yellow"
    AMBER = "ffc107", "Amber"
    ORANGE = "ff9800", "Orange"
    DARK_ORANGE = "ff5722", "Dark orange"
    BROWN = "795548", "Brown"
    LIGHT_GREY = "c0c0c0", "Light grey"
    GREY = "9e9e9e", "Grey"
    DARK_GREY = "607d8b", "Dark grey"
    BLACK = "111111", "Black"
    WHITE = "ffffff", "White"


class ObjectChangeAction(models.IntegerChoices):
    CREATE = 1, "Created"
    UPDATE = 2, "Updated"
    DELETE = 3, "Deleted"
