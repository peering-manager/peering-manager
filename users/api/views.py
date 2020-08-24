from django.contrib.auth.models import Group, User
from django.db.models import Count
from rest_framework.routers import APIRootView

from .serializers import GroupSerializer, UserSerializer
from users.filters import GroupFilterSet, UserFilterSet
from utils.api import ModelViewSet


class GroupViewSet(ModelViewSet):
    queryset = Group.objects.all().annotate(user_count=Count("user")).order_by("name")
    serializer_class = GroupSerializer
    filterset_class = GroupFilterSet


class UserViewSet(ModelViewSet):
    queryset = User.objects.all().prefetch_related("groups").order_by("username")
    serializer_class = UserSerializer
    filterset_class = UserFilterSet
