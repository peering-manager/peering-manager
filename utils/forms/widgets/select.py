from django import forms

from ...enums import Colour
from ..utils import add_blank_choice

__all__ = (
    "BulkEditNullBooleanSelect",
    "ColourSelect",
    "StaticSelect",
    "StaticSelectMultiple",
)


class BulkEditNullBooleanSelect(forms.NullBooleanSelect):
    """
    Do not enforce True/False when not selecting an option.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.choices = (("1", "---------"), ("2", "Yes"), ("3", "No"))
        self.attrs["class"] = "custom-select2-static"


class ColourSelect(forms.Select):
    """
    Colourise each <option> inside a select widget.
    """

    option_template_name = "widgets/colourselect_option.html"

    def __init__(self, *args, **kwargs):
        kwargs["choices"] = add_blank_choice(Colour)
        super().__init__(*args, **kwargs)
        self.attrs["class"] = "custom-select2-colour-picker"


class StaticSelect(forms.Select):
    """
    Select widget for static choices leveraging the select2 component.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs["class"] = "custom-select2-static"


class StaticSelectMultiple(StaticSelect, forms.SelectMultiple):
    """
    Same static select widget using select2 but allowing multiple choices.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs["data-multiple"] = 1
        self.attrs["data-close-on-select"] = 0
