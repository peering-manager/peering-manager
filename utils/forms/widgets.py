from json import dumps as json_dumps
from json import loads as json_loads

from django import forms
from django.conf import settings

from utils.enums import Colour


class SmallTextarea(forms.Textarea):
    """
    Just to be used as small text area.
    """

    pass


class APISelect(forms.Select):
    """
    Select widget using API calls to populate its choices.
    """

    def __init__(self, api_url=None, full=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs["class"] = "custom-select2-api"

        if api_url:
            self.attrs["data-url"] = f"/{settings.BASE_PATH}{api_url.lstrip('/')}"
        if full:
            self.attrs["data-full"] = full

    def add_query_param(self, name, value):
        key = f"data-query-param-{name}"

        values = json_loads(self.attrs.get(key, "[]"))
        if type(value) is list:
            values.extend([str(v) for v in value])
        else:
            values.append(str(value))

        self.attrs[key] = json_dumps(values)


class APISelectMultiple(APISelect, forms.SelectMultiple):
    """
    Same API select widget using select2 but allowing multiple choices.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs["data-multiple"] = 1
        self.attrs["data-close-on-select"] = 0


class ColorSelect(forms.Select):
    """
    Colorize each <option> inside a select widget.
    """

    option_template_name = "widgets/colorselect_option.html"

    def __init__(self, *args, **kwargs):
        from . import add_blank_choice

        kwargs["choices"] = add_blank_choice(Colour)
        super().__init__(*args, **kwargs)
        self.attrs["class"] = "custom-select2-color-picker"


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


class CustomNullBooleanSelect(StaticSelect):
    """
    Do not enforce True/False when not selecting an option.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.choices = (("unknown", "---------"), ("true", "Yes"), ("false", "No"))
