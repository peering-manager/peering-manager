from django.db.models import Q
from django.utils.deconstruct import deconstructible

from .enums import EXTRAS_FEATURES
from .registry import registry


@deconstructible
class FeatureQuery:
    """
    Helper class that delays evaluation of the registry contents for the functionality
    store until it has been populated.
    """

    def __init__(self, feature):
        self.feature = feature

    def __call__(self):
        return self.get_query()

    def get_query(self):
        """
        Given an extras feature, return a `Q` object for content type lookup.
        """
        query = Q()
        for app_label, models in registry["model_features"][self.feature].items():
            query |= Q(app_label=app_label, model__in=models)

        return query


def register_features(model, features):
    for feature in features:
        if feature not in EXTRAS_FEATURES:
            raise ValueError(f"{feature} is not a valid extras feature!")
        app_label, model_name = model._meta.label_lower.split(".")
        registry["model_features"][feature][app_label].add(model_name)
