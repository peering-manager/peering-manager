import peering.models

from django.db.models import Count
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from utils.models import SoftDeleteModel

from . import ModelViewSet
from .serializers import TagSerializer
from utils.filters import TagFilterSet
from utils.models import Tag


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.annotate(
        tagged_items=Count("utils_taggeditem_items", distinct=True)
    )
    serializer_class = TagSerializer
    filterset_class = TagFilterSet


class SoftDeleteViewSet(ViewSet):
    permission_classes = [IsAdminUser]

    def get_view_name(self):
        return "Soft Delete Management"

    @action(detail=False, methods=["get"], url_path="statistics")
    def statistics(self, request):
        return Response(SoftDeleteModel.get_deleted_counts(peering.models))

    @action(detail=False, methods=["post"], url_path="purge")
    def purge(self, request):
        SoftDeleteModel.purge_deleted(peering.models, age=request.POST.get("age", 0))
        return Response({"status": "success"})
