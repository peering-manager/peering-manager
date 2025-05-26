class ChoiceSetMeta(type):
    """
    Metaclass for `ChoiceSet`.
    """

    def __new__(mcs, name, bases, attrs):
        # Define choice tuples and colour maps
        attrs["_choices"] = []
        attrs["colours"] = {}
        for choice in attrs["CHOICES"]:
            if isinstance(choice[1], list | tuple):
                grouped_choices = []
                for c in choice[1]:
                    grouped_choices.append((c[0], c[1]))
                    if len(c) == 3:
                        attrs["colours"][c[0]] = c[2]
                attrs["_choices"].append((choice[0], grouped_choices))
            else:
                attrs["_choices"].append((choice[0], choice[1]))
                if len(choice) == 3:
                    attrs["colours"][choice[0]] = choice[2]

        return super().__new__(mcs, name, bases, attrs)

    def __call__(cls, *args, **kwargs):
        # django-filters will check if a 'choices' value is callable, and if so assume
        # that it returns an iterable
        return getattr(cls, "_choices", ())

    def __iter__(cls):
        return iter(getattr(cls, "_choices", ()))


class ChoiceSet(metaclass=ChoiceSetMeta):
    """
    Holds an iterable of choice tuples suitable for passing to a Django model or form
    field.
    """

    CHOICES = []

    @classmethod
    def values(cls):
        return [c[0] for c in cls._choices]


class Colour(ChoiceSet):
    DARK_RED = "aa1409"
    RED = "f44336"
    PINK = "e91e63"
    ROSE = "ffe4e1"
    FUCHSIA = "ff66ff"
    PURPLE = "9c27b0"
    DARK_PURPLE = "673ab7"
    INDIGO = "3f51b5"
    BLUE = "2196f3"
    LIGHT_BLUE = "03a9f4"
    CYAN = "00bcd4"
    TEAL = "009688"
    AQUA = "00ffff"
    DARK_GREEN = "2f6a31"
    GREEN = "4caf50"
    LIGHT_GREEN = "8bc34a"
    LIME = "cddc39"
    YELLOW = "ffeb3b"
    AMBER = "ffc107"
    ORANGE = "ff9800"
    DARK_ORANGE = "ff5722"
    BROWN = "795548"
    LIGHT_GREY = "c0c0c0"
    GREY = "9e9e9e"
    DARK_GREY = "607d8b"
    BLACK = "111111"
    WHITE = "ffffff"

    CHOICES = (
        (DARK_RED, "Dark Red"),
        (RED, "Red"),
        (PINK, "Pink"),
        (ROSE, "Rose"),
        (FUCHSIA, "Fuchsia"),
        (PURPLE, "Purple"),
        (DARK_PURPLE, "Dark Purple"),
        (INDIGO, "Indigo"),
        (BLUE, "Blue"),
        (LIGHT_BLUE, "Light Blue"),
        (CYAN, "Cyan"),
        (TEAL, "Teal"),
        (AQUA, "Aqua"),
        (DARK_GREEN, "Dark Green"),
        (GREEN, "Green"),
        (LIGHT_GREEN, "Light Green"),
        (LIME, "Lime"),
        (YELLOW, "Yellow"),
        (AMBER, "Amber"),
        (ORANGE, "Orange"),
        (DARK_ORANGE, "Dark Orange"),
        (BROWN, "Brown"),
        (LIGHT_GREY, "Light Grey"),
        (GREY, "Grey"),
        (DARK_GREY, "Dark Grey"),
        (BLACK, "Black"),
        (WHITE, "White"),
    )
