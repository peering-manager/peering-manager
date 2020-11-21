from django.db.models import Count

from utils.filters import TagFilterSet
from utils.models import Tag

from . import ModelViewSet
from .serializers import TagSerializer


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.annotate(
        tagged_items=Count("utils_taggeditem_items", distinct=True)
    )
    serializer_class = TagSerializer
    filterset_class = TagFilterSet
