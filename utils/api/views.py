from django.db.models import Count
from rest_framework.routers import APIRootView

from peering_manager.api.views import ModelViewSet
from utils.filters import ObjectChangeFilterSet, TagFilterSet
from utils.models import ObjectChange, Tag

from .serializers import ObjectChangeSerializer, TagSerializer


class UtilsRootView(APIRootView):
    def get_view_name(self):
        return "Utilities"


class ObjectChangeViewSet(ModelViewSet):
    queryset = ObjectChange.objects.all()
    serializer_class = ObjectChangeSerializer
    filterset_class = ObjectChangeFilterSet


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.annotate(
        tagged_items=Count("utils_taggeditem_items", distinct=True)
    )
    serializer_class = TagSerializer
    filterset_class = TagFilterSet
