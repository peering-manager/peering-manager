from django.db.models import Q
from django.utils.deconstruct import deconstructible

from peering_manager.registry import MODEL_FEATURES_KEY, registry


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
        for app_label, models in registry[MODEL_FEATURES_KEY][self.feature].items():
            query |= Q(app_label=app_label, model__in=models)

        return query
