from django.db.models import Count

from utils.filters import ObjectChangeFilterSet, TagFilterSet
from utils.models import ObjectChange, Tag

from . import ModelViewSet
from .serializers import ObjectChangeSerializer, TagSerializer


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
