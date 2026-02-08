from json import dumps as json_dumps
from json import loads as json_loads

from django import forms
from django.conf import settings

__all__ = ("APISelect", "APISelectMultiple")


class APISelect(forms.Select):
    """
    Select widget using API calls to populate its choices.
    """

    def __init__(self, api_url=None, full=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs["class"] = "custom-tomselect-api"

        if api_url:
            self.attrs["data-url"] = f"/{settings.BASE_PATH}{api_url.lstrip('/')}"
        if full:
            self.attrs["data-full"] = full

    def add_query_param(self, name, value):
        key = f"data-query-param-{name}"

        values = json_loads(self.attrs.get(key, "[]"))
        if isinstance(value, list):
            values.extend([str(v) for v in value])
        else:
            values.append(str(value))

        self.attrs[key] = json_dumps(values)


class APISelectMultiple(APISelect, forms.SelectMultiple):
    """
    Same API select widget using TomSelect but allowing multiple choices.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs["data-multiple"] = 1
        self.attrs["data-close-on-select"] = 0
