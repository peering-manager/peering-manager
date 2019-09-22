from django.db.models import Count

from rest_framework.viewsets import ViewSet

from . import ModelViewSet
from .serializers import TagSerializer
from utils.filters import TagFilter
from utils.models import Tag


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.annotate(
        tagged_items=Count("utils_taggeditem_items", distinct=True)
    )
    serializer_class = TagSerializer
    filterset_class = TagFilter
