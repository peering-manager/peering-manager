from django import forms

from utils.forms import widgets
from utils.functions import content_type_name

__all__ = ("ContentTypeChoiceField", "ContentTypeMultipleChoiceField")


class ContentTypeChoiceMixin(object):
    def __init__(self, queryset, *args, **kwargs):
        # Order ContentTypes by app_label
        queryset = queryset.order_by("app_label", "model")
        super().__init__(queryset, *args, **kwargs)

    def label_from_instance(self, obj):
        try:
            return content_type_name(obj)
        except AttributeError:
            return super().label_from_instance(obj)


class ContentTypeChoiceField(ContentTypeChoiceMixin, forms.ModelChoiceField):
    """
    Selection field for a single content type.
    """

    widget = widgets.StaticSelect


class ContentTypeMultipleChoiceField(
    ContentTypeChoiceMixin, forms.ModelMultipleChoiceField
):
    """
    Selection field for one or more content types.
    """

    widget = widgets.StaticSelectMultiple
